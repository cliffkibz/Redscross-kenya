from flask import Flask, render_template, g, request, flash, redirect, url_for, session, get_flashed_messages
from flask_jwt_extended import JWTManager,decode_token, verify_jwt_in_request, get_jwt_identity, exceptions as jwt_exceptions
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
from backend.api.chatbot import chatbot_bp
from backend.models.user import User # Import User model

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(incidents_bp, url_prefix='/api/incidents')
app.register_blueprint(resources_bp, url_prefix='/api/resources')
app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
app.register_blueprint(chatbot_bp)  # Register chatbot blueprint

# Before request: Load current user from JWT if available
@app.before_request
def load_user_from_jwt():
    g.current_user = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            g.current_user = User.get_by_id(user_id)
            return
    except Exception:
        pass
    # Try cookie (browser navigation)
    token = request.cookies.get('access_token')
    if token:
        try:
            decoded = decode_token(token)
            user_id = decoded.get('sub')
            if user_id:
                g.current_user = User.get_by_id(user_id)
        except Exception:
            pass

# Context processor to make variables available to all templates
@app.context_processor
def inject_globals():
    class AnonymousUser:
        is_authenticated = False
        username = ''
        role = ''
    user = g.current_user if g.current_user else AnonymousUser()
    if user and hasattr(user, 'is_active') and user.is_active:
        user.is_authenticated = True
    else:
        user.is_authenticated = False
    return dict(
        current_user=user,
        get_flashed_messages=get_flashed_messages,
        now=datetime.utcnow()
    )

@app.route('/')
def index():
    from backend.utils.db import get_db
    db = get_db()
    stats = {
        'incident_count': db.incidents.count_documents({}),
        'responder_count': db.users.count_documents({'role': 'responder', 'is_active': True}),
        'resource_count': db.resources.count_documents({'status': 'available'})
    }
    return render_template('index.html', stats=stats)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login_page'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

from werkzeug.utils import secure_filename
from bson import ObjectId

@app.route('/report_incident', methods=['GET', 'POST'])
def report_incident():
    from backend.models.incident import Incident
    from backend.models.user import User
    import os
    from flask import current_app
    user = getattr(g, 'current_user', None)
    if not user:
        return redirect(url_for('auth.login_page'))
    if request.method == 'POST':
        data = request.form.to_dict()
        files = request.files.getlist('photos') if 'photos' in request.files else []
        # Accept the fields as provided by the form
        required_fields = ['name', 'email', 'location', 'description']
        if not all(field in data and data[field] for field in required_fields):
            flash('Please fill in all required fields.', 'danger')
            return render_template('report_incident.html')
        photo_paths = []
        for file in files:
            if file and '.' in file.filename:
                filename = secure_filename(file.filename)
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join('frontend/static/uploads', filename)
                file.save(file_path)
                photo_paths.append(filename)
        # Use name as title, set incident_type to 'other' by default
        location_dict = {
            'address': data['location'],
            'name': data.get('name', ''),
            'email': data.get('email', ''),
            'phone': data.get('phone', '')
        }
        incident = Incident(
            title=data.get('name', 'Incident Report'),
            description=data['description'],
            incident_type='other',
            location=location_dict,
            reporter_id=user._id,
            severity='medium',
            photos=photo_paths
        )
        incident.save()
        flash('Incident reported successfully!', 'success')
        return redirect(url_for('user_dashboard'))
    return render_template('report_incident.html')

@app.route('/request_help', methods=['GET', 'POST'])
def request_help():
    from backend.utils.db import get_db
    if request.method == 'POST':
        data = request.form.to_dict()
        db = get_db()
        help_request = {
            'name': data.get('name', ''),
            'email': data.get('email', ''),
            'phone': data.get('phone', ''),
            'location': data.get('location', ''),
            'help_type': data.get('help_type', ''),
            'details': data.get('details', ''),
            'created_at': datetime.utcnow()
        }
        db.help_requests.insert_one(help_request)
        flash('Help request submitted successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('request_help.html')

# Duplicate removed: handled by the POST+GET route above

@app.route('/view_resources', methods=['GET'])
def view_resources():
    return render_template('view_resources.html')

@app.route('/add_resource', methods=['GET'])
def add_resource():
    user = getattr(g, 'current_user', None)
    if not user or not hasattr(user, 'role') or user.role != 'admin':
        return "<h3 class='text-danger text-center mt-5'>Admin access required.</h3>", 403
    return render_template('add_resource.html')

@app.route('/dashboard', endpoint='user_dashboard')
def user_dashboard():
    user = getattr(g, 'current_user', None)
    if not user:
        return redirect(url_for('auth.login_page'))
    from backend.models.incident import Incident
    report_count = Incident.count_by_user(user._id)
    recent_reports = Incident.recent_by_user(user._id, limit=5)
    return render_template('user_dashboard.html', current_user=user, report_count=report_count, recent_reports=recent_reports)

# Admin Dashboard
@app.route('/admin/dashboard', endpoint='admin_dashboard')
def admin_dashboard():
    user = getattr(g, 'current_user', None)
    if not user or user.role != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('auth.login_page'))

    # Import models
    from backend.models.incident import Incident
    from backend.models.resource import Resource
    from backend.models.user import User
    from backend.utils.db import get_db
    db = get_db()

    # Stats
    stats = {
        'incident_count': db.incidents.count_documents({}),
        'responder_count': db.users.count_documents({'role': 'responder', 'is_active': True}),
        'resource_count': db.resources.count_documents({'status': 'available'})
    }

    # Recent incidents (limit 10)
    incidents = list(db.incidents.find().sort('created_at', -1).limit(10))
    for inc in incidents:
        inc['id'] = str(inc['_id'])
        inc['reporter_name'] = db.users.find_one({'_id': inc['reporter_id']})['username'] if db.users.find_one({'_id': inc['reporter_id']}) else 'Unknown'

    # Resources (limit 10)
    resources = list(db.resources.find().sort('created_at', -1).limit(10))
    for res in resources:
        res['id'] = str(res['_id'])

    # Users (limit 10)
    users = list(db.users.find().sort('created_at', -1).limit(10))
    for u in users:
        u['id'] = str(u['_id'])

    # Help requests (limit 10)
    help_requests = list(db.help_requests.find().sort('created_at', -1).limit(10))
    for req in help_requests:
        req['id'] = str(req['_id'])

    return render_template(
        'admin_dashboard.html',
        stats=stats,
        incidents=incidents,
        resources=resources,
        users=users,
        help_requests=help_requests
    )

# Admin: View Incident Details
@app.route('/admin/incidents/<incident_id>', methods=['GET'])
def admin_view_incident(incident_id):
    from backend.models.incident import Incident
    from backend.models.user import User
    from backend.utils.db import get_db
    db = get_db()
    incident = db.incidents.find_one({'_id': ObjectId(incident_id)})
    if not incident:
        flash('Incident not found.', 'danger')
        return redirect(url_for('admin_dashboard'))
    reporter = db.users.find_one({'_id': incident['reporter_id']})
    return render_template('admin_incident_detail.html', incident=incident, reporter=reporter)

# Admin: Update Incident
@app.route('/admin/incidents/<incident_id>/update', methods=['GET', 'POST'])
def admin_update_incident(incident_id):
    from backend.models.incident import Incident
    from backend.utils.db import get_db
    db = get_db()
    incident = db.incidents.find_one({'_id': ObjectId(incident_id)})
    if not incident:
        flash('Incident not found.', 'danger')
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        update_fields = {}
        for field in ['status', 'severity', 'description']:
            if field in request.form:
                update_fields[field] = request.form[field]
        if update_fields:
            db.incidents.update_one({'_id': ObjectId(incident_id)}, {'$set': update_fields})
            flash('Incident updated successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
    return render_template('admin_incident_update.html', incident=incident)

# Admin: Delete Incident
@app.route('/admin/incidents/<incident_id>/delete', methods=['POST'])
def admin_delete_incident(incident_id):
    from backend.utils.db import get_db
    db = get_db()
    db.incidents.delete_one({'_id': ObjectId(incident_id)})
    flash('Incident deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

# Incidents page (public)
@app.route('/incidents')
def incidents_page():
    return render_template('incidents.html')

import requests

# News API endpoint for disaster news
@app.route('/api/disaster_news')
def disaster_news():
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')
    keywords = 'flood OR fire OR earthquake OR landslide OR storm OR disaster'
    url = f'https://newsapi.org/v2/everything?q={keywords}&sortBy=publishedAt&language=en&pageSize=10&apiKey={NEWS_API_KEY}'
    try:
        resp = requests.get(url)
        data = resp.json()
        articles = [
            {
                'title': a['title'],
                'description': a['description'],
                'url': a['url']
            }
            for a in data.get('articles', []) if a.get('description')
        ]
        return {'articles': articles}
    except Exception as e:
        return {'articles': [], 'error': str(e)}, 500

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