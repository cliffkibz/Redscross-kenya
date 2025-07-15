from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from bson import ObjectId
from backend.models.incident import Incident
from backend.models.user import User
from backend.models.resource import Resource
from backend.utils.db import db
from backend.services.sms import send_incident_alert

incidents_bp = Blueprint('incidents', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@incidents_bp.route('/', methods=['POST'])
@jwt_required()
def create_incident():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.form.to_dict()
    files = request.files.getlist('photos')
    
    # Validate required fields
    required_fields = ['title', 'description', 'incident_type', 'location']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Handle photo uploads
        photo_paths = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                photo_paths.append(filename)
        
        # Create incident
        incident = Incident(
            title=data['title'],
            description=data['description'],
            incident_type=data['incident_type'],
            location=eval(data['location']),  # Convert string to dict
            reporter_id=current_user_id,
            severity=data.get('severity', 'medium'),
            photos=photo_paths
        )
        incident.save()
        
        # Send SMS alerts to responders
        if incident.severity in ['high', 'critical']:
            responders = User.get_by_role('responder')
            for responder in responders:
                if responder.phone:
                    send_incident_alert(responder.phone, incident)
        
        return jsonify({
            'message': 'Incident reported successfully',
            'incident': incident.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@incidents_bp.route('/', methods=['GET'])
@jwt_required(optional=True)
def get_incidents():
    # Allow public access to incidents list
    # If user is authenticated, can add user-specific logic if needed
    # Otherwise, show all incidents
    status = request.args.get('status')
    incident_type = request.args.get('type')
    severity = request.args.get('severity')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Build query
    query = {}
    if status:
        query['status'] = status
    if incident_type:
        query['incident_type'] = incident_type
    if severity:
        query['severity'] = severity
    
    # Get incidents
    skip = (page - 1) * per_page
    incidents = list(db.incidents.find(query).skip(skip).limit(per_page))
    total = db.incidents.count_documents(query)
    
    # Convert ObjectId to string
    for incident in incidents:
        incident['_id'] = str(incident['_id'])
        incident['reporter_id'] = str(incident['reporter_id'])
    
    return jsonify({
        'incidents': incidents,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }), 200

@incidents_bp.route('/<incident_id>', methods=['GET'])
@jwt_required()
def get_incident(incident_id):
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    incident = Incident.get_by_id(incident_id)
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    return jsonify(incident.to_dict()), 200

@incidents_bp.route('/<incident_id>', methods=['PUT'])
@jwt_required()
def update_incident(incident_id):
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Only responders and admins can update incidents
    if user.role not in ['responder', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    incident = Incident.get_by_id(incident_id)
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    data = request.get_json()
    allowed_fields = ['status', 'severity', 'description']
    
    for field in allowed_fields:
        if field in data:
            setattr(incident, field, data[field])
    
    incident.updated_at = datetime.utcnow()
    incident.save()
    
    return jsonify({
        'message': 'Incident updated successfully',
        'incident': incident.to_dict()
    }), 200

@incidents_bp.route('/<incident_id>/resources', methods=['POST'])
@jwt_required()
def assign_resource(incident_id):
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Only responders and admins can assign resources
    if user.role not in ['responder', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    incident = Incident.get_by_id(incident_id)
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    data = request.get_json()
    if not data or 'resource_id' not in data:
        return jsonify({'error': 'Missing resource_id'}), 400
    
    resource = Resource.get_by_id(data['resource_id'])
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    
    if resource.assign_to_incident(incident_id):
        incident.assign_resource(resource._id)
        return jsonify({
            'message': 'Resource assigned successfully',
            'incident': incident.to_dict()
        }), 200
    else:
        return jsonify({'error': 'Resource is not available'}), 400

@incidents_bp.route('/<incident_id>/responders', methods=['POST'])
@jwt_required()
def assign_responder(incident_id):
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Only admins can assign responders
    if user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    incident = Incident.get_by_id(incident_id)
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    data = request.get_json()
    if not data or 'responder_id' not in data:
        return jsonify({'error': 'Missing responder_id'}), 400
    
    responder = User.get_by_id(data['responder_id'])
    if not responder or responder.role != 'responder':
        return jsonify({'error': 'Invalid responder'}), 400
    
    incident.assign_responder(responder._id)
    return jsonify({
        'message': 'Responder assigned successfully',
        'incident': incident.to_dict()
    }), 200

@incidents_bp.route('/<incident_id>/notes', methods=['POST'])
@jwt_required()
def add_note(incident_id):
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Only responders and admins can add notes
    if user.role not in ['responder', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    incident = Incident.get_by_id(incident_id)
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Missing note content'}), 400
    
    incident.add_note(current_user_id, data['content'])
    return jsonify({
        'message': 'Note added successfully',
        'incident': incident.to_dict()
    }), 200  

@incidents_bp.route('/locations', methods=['GET'])
@jwt_required()
def get_incident_locations():
    """
    Returns a list of incidents with latitude and longitude for map display.
    """
    # Only return incidents with valid coordinates
    incidents = db.incidents.find({
        "latitude": {"$ne": None},
        "longitude": {"$ne": None}
    })
    data = []
    for incident in incidents:
        data.append({
            "title": incident.get("title", ""),
            "latitude": incident.get("latitude"),
            "longitude": incident.get("longitude"),
            "location": incident.get("location", "")
        })
    return jsonify(data), 200 