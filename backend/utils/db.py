from pymongo import MongoClient
from flask import current_app, g
from werkzeug.local import LocalProxy

def get_db():
    """
    Config method to return db instance
    """
    db_client = getattr(g, "_database", None)
    if db_client is None:
        db_client = g._database = MongoClient(current_app.config['MONGODB_URI'])
    return db_client.get_database()

# Use LocalProxy to read the global db instance with 'db'
db = LocalProxy(get_db)

def close_db(e=None):
    """
    Close the db connection
    """
    db_client = getattr(g, "_database", None)
    if db_client is not None:
        db_client.close()

def init_db(app):
    """
    Initialize the connection
    """
    # Register the close_db function to be called when the application context ends
    app.teardown_appcontext(close_db)
    
    # Create indexes
    with app.app_context():
        # Users collection indexes
        db.users.create_index("email", unique=True)
        db.users.create_index("username", unique=True)
        
        # Incidents collection indexes
        db.incidents.create_index("location", "2dsphere")  # For geospatial queries
        db.incidents.create_index("created_at")
        db.incidents.create_index("status")
        db.incidents.create_index("incident_type")
        
        # Resources collection indexes
        db.resources.create_index("location", "2dsphere")  # For geospatial queries
        db.resources.create_index("resource_type")
        db.resources.create_index("status")
        db.resources.create_index("current_incident") 