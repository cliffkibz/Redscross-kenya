from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.resource import Resource
from backend.models.user import User
from backend.services.sms import send_resource_assignment
from datetime import datetime

resources_bp = Blueprint('resources', __name__)

@resources_bp.route('/', methods=['POST'])
@jwt_required()
def create_resource():
    """Create a new resource (admin only)"""
    current_user = User.get_by_id(get_jwt_identity())
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    required_fields = ['name', 'type', 'description', 'location', 'capacity', 'specifications']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        resource = Resource(
            name=data['name'],
            type=data['type'],
            description=data['description'],
            status='available',
            location=data['location'],
            capacity=data['capacity'],
            specifications=data['specifications']
        )
        resource.save()
        return jsonify(resource.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@resources_bp.route('/', methods=['GET'])
@jwt_required()
def get_resources():
    """Get a list of resources with optional filtering"""
    current_user = User.get_by_id(get_jwt_identity())
    if not current_user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get query parameters
    resource_type = request.args.get('type')
    status = request.args.get('status')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Build query
    query = {}
    if resource_type:
        query['type'] = resource_type
    if status:
        query['status'] = status
    
    # Get resources with pagination
    resources = Resource.objects(**query).skip((page - 1) * per_page).limit(per_page)
    total = Resource.objects(**query).count()
    
    return jsonify({
        'resources': [resource.to_dict() for resource in resources],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })

@resources_bp.route('/<resource_id>', methods=['GET'])
@jwt_required()
def get_resource(resource_id):
    """Get a specific resource by ID"""
    current_user = User.get_by_id(get_jwt_identity())
    if not current_user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    resource = Resource.get_by_id(resource_id)
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    
    return jsonify(resource.to_dict())

@resources_bp.route('/<resource_id>', methods=['PUT'])
@jwt_required()
def update_resource(resource_id):
    """Update a resource (admin only)"""
    current_user = User.get_by_id(get_jwt_identity())
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    resource = Resource.get_by_id(resource_id)
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    
    data = request.get_json()
    allowed_fields = ['name', 'type', 'description', 'status', 'location', 'capacity', 'specifications']
    
    for field in allowed_fields:
        if field in data:
            setattr(resource, field, data[field])
    
    try:
        resource.save()
        return jsonify(resource.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@resources_bp.route('/<resource_id>/maintenance', methods=['POST'])
@jwt_required()
def add_maintenance_record(resource_id):
    """Add a maintenance record for a resource (admin and responders)"""
    current_user = User.get_by_id(get_jwt_identity())
    if not current_user or current_user.role not in ['admin', 'responder']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    resource = Resource.get_by_id(resource_id)
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    
    data = request.get_json()
    if not data.get('type') or not data.get('description'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    maintenance_record = {
        'type': data['type'],
        'description': data['description'],
        'reported_by': current_user.id,
        'reported_at': datetime.utcnow(),
        'status': 'pending',
        'notes': data.get('notes')
    }
    
    resource.maintenance_records.append(maintenance_record)
    resource.status = 'maintenance'
    
    try:
        resource.save()
        return jsonify(resource.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@resources_bp.route('/<resource_id>/maintenance/<maintenance_id>/complete', methods=['POST'])
@jwt_required()
def complete_maintenance(resource_id, maintenance_id):
    """Mark a maintenance record as complete (admin and responders)"""
    current_user = User.get_by_id(get_jwt_identity())
    if not current_user or current_user.role not in ['admin', 'responder']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    resource = Resource.get_by_id(resource_id)
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    
    # Find the maintenance record
    maintenance_record = None
    for record in resource.maintenance_records:
        if str(record['_id']) == maintenance_id:
            maintenance_record = record
            break
    
    if not maintenance_record:
        return jsonify({'error': 'Maintenance record not found'}), 404
    
    data = request.get_json()
    maintenance_record['status'] = 'completed'
    maintenance_record['completed_by'] = current_user.id
    maintenance_record['completed_at'] = datetime.utcnow()
    maintenance_record['completion_notes'] = data.get('completion_notes')
    
    # Update resource status if no other pending maintenance
    has_pending = any(record['status'] == 'pending' for record in resource.maintenance_records)
    if not has_pending:
        resource.status = 'available'
    
    try:
        resource.save()
        return jsonify(resource.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@resources_bp.route('/<resource_id>/release', methods=['POST'])
@jwt_required()
def release_resource(resource_id):
    """Release a resource from an incident (admin and responders)"""
    current_user = User.get_by_id(get_jwt_identity())
    if not current_user or current_user.role not in ['admin', 'responder']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    resource = Resource.get_by_id(resource_id)
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    
    if resource.status != 'in_use':
        return jsonify({'error': 'Resource is not currently in use'}), 400
    
    resource.status = 'available'
    resource.current_incident = None
    
    try:
        resource.save()
        return jsonify(resource.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@resources_bp.route('/available/<incident_type>', methods=['GET'])
@jwt_required()
def get_available_resources(incident_type):
    """Get available resources for a specific incident type (responders and admins)"""
    current_user = User.get_by_id(get_jwt_identity())
    if not current_user or current_user.role not in ['admin', 'responder']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get available resources that match the incident type
    resources = Resource.objects(
        status='available',
        type__in=[incident_type, 'general']  # Include general-purpose resources
    )
    
    return jsonify({
        'resources': [resource.to_dict() for resource in resources]
    }) 