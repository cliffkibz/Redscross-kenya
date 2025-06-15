from flask import Flask, render_template, g, request, flash, redirect, url_for, session, get_flashed_messages
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt_identity, exceptions as jwt_exceptions
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import timedelta, datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, 
            static_folder='frontend/static',
            template_folder='frontend/templates')

# Configure app
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-here')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['MONGODB_URI'] = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/redcross_kenya')
app.config['TWILIO_ACCOUNT_SID'] = os.getenv('TWILIO_ACCOUNT_SID')
app.config['TWILIO_AUTH_TOKEN'] = os.getenv('TWILIO_AUTH_TOKEN')
app.config['TWILIO_PHONE_NUMBER'] = os.getenv('TWILIO_PHONE_NUMBER')

# Initialize extensions
jwt = JWTManager(app)
CORS(app)

# Import and register blueprints
from backend.api.auth import auth_bp
from backend.api.incidents import incidents_bp
from backend.api.resources import resources_bp
from backend.api.alerts import alerts_bp
from backend.models.user import User # Import User model

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(incidents_bp, url_prefix='/api/incidents')
app.register_blueprint(resources_bp, url_prefix='/api/resources')
app.register_blueprint(alerts_bp, url_prefix='/api/alerts')

# Before request: Load current user from JWT if available
@app.before_request
def load_user_from_jwt():
    g.current_user = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            g.current_user = User.get_by_id(user_id)
    except jwt_exceptions.NoAuthorizationError:
        # No JWT provided, g.current_user remains None
        pass
    except jwt_exceptions.InvalidHeaderError as e:
        # Handle invalid JWT headers, e.g., malformed token
        # For now, just set current_user to None and potentially log the error
        app.logger.warning(f"Invalid JWT header: {e}")
        pass
    except Exception as e:
        app.logger.error(f"Error loading user from JWT: {e}")
        pass

# Context processor to make variables available to all templates
@app.context_processor
def inject_globals():
    return dict(
        current_user=g.current_user,
        get_flashed_messages=get_flashed_messages,
        now=datetime.utcnow()
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logout')
def logout_web():
    session.clear()
    flash('you have been logged out.' , 'success')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    from flask import session, redirect, url_for, flash
    session.clear()  # Clear session data if using session-based auth
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return {'error': 'Not found'}, 404

@app.errorhandler(500)
def internal_error(error):
    return {'error': 'Internal server error'}, 500

if __name__ == '__main__':
    # Ensure the upload directory exists
    os.makedirs('frontend/static/uploads', exist_ok=True)
    
    # Run the app
    app.run(
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 5000)),
        debug=True
    )