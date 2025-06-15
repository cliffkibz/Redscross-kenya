from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from backend.models.user import User
from backend.models.incident import Incident
from backend.services.sms import (
    send_incident_alert, send_resource_assignment,
    send_responder_assignment, send_incident_update
)
from backend.utils.db import db

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/test', methods=['POST'])
@jwt_required()
def test_alert():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Only admins can send test alerts
    if user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data or 'phone_number' not in data:
        return jsonify({'error': 'Missing phone number'}), 400
    
    try:
        message = """
🔔 RED CROSS KENYA TEST ALERT
This is a test alert from the Red Cross Kenya Disaster Management System.
If you received this message, the alert system is working correctly.
        """.strip()
        
        from backend.services.sms import send_sms
        result = send_sms(data['phone_number'], message)
        
        if result:
            return jsonify({
                'message': 'Test alert sent successfully',
                'message_id': result
            }), 200
        else:
            return jsonify({'error': 'Failed to send test alert'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/incidents/<incident_id>/notify', methods=['POST'])
@jwt_required()
def notify_incident(incident_id):
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Only responders and admins can send notifications
    if user.role not in ['responder', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    incident = Incident.get_by_id(incident_id)
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    data = request.get_json()
    if not data or 'notification_type' not in data:
        return jsonify({'error': 'Missing notification type'}), 400
    
    try:
        notification_type = data['notification_type']
        details = data.get('details')
        
        # Get all responders
        responders = User.get_by_role('responder')
        sent_count = 0
        
        for responder in responders:
            if not responder.phone:
                continue
                
            if notification_type == 'status_update':
                send_incident_update(
                    responder.phone,
                    incident,
                    'status_change',
                    details
                )
            elif notification_type == 'severity_update':
                send_incident_update(
                    responder.phone,
                    incident,
                    'severity_change',
                    details
                )
            elif notification_type == 'note_added':
                send_incident_update(
                    responder.phone,
                    incident,
                    'note_added',
                    details
                )
            else:
                send_incident_update(
                    responder.phone,
                    incident,
                    'custom',
                    details
                )
            sent_count += 1
        
        return jsonify({
            'message': f'Notifications sent to {sent_count} responders',
            'incident_id': incident_id,
            'notification_type': notification_type
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/incidents/<incident_id>/responders', methods=['POST'])
@jwt_required()
def notify_responders(incident_id):
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Only admins can notify all responders
    if user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    incident = Incident.get_by_id(incident_id)
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    try:
        # Get all responders
        responders = User.get_by_role('responder')
        sent_count = 0
        
        for responder in responders:
            if responder.phone:
                send_responder_assignment(responder.phone, incident)
                sent_count += 1
        
        return jsonify({
            'message': f'Notifications sent to {sent_count} responders',
            'incident_id': incident_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/resources/<resource_id>/notify', methods=['POST'])
@jwt_required()
def notify_resource_assignment(resource_id):
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Only admins and responders can notify resource assignments
    if user.role not in ['admin', 'responder']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data or 'incident_id' not in data:
        return jsonify({'error': 'Missing incident_id'}), 400
    
    resource = Resource.get_by_id(resource_id)
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    
    incident = Incident.get_by_id(data['incident_id'])
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    try:
        # Notify all responders about the resource assignment
        responders = User.get_by_role('responder')
        sent_count = 0
        
        for responder in responders:
            if responder.phone:
                send_resource_assignment(responder.phone, incident, resource)
                sent_count += 1
        
        return jsonify({
            'message': f'Resource assignment notifications sent to {sent_count} responders',
            'resource_id': resource_id,
            'incident_id': incident._id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_alert_settings():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Only admins can view alert settings
    if user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get alert settings from database or return defaults
    settings = db.alert_settings.find_one({'_id': 'global'}) or {
        'incident_severity_threshold': 'high',
        'notification_channels': ['sms'],
        'auto_notify_responders': True,
        'auto_notify_resources': True,
        'notification_cooldown': 300,  # 5 minutes in seconds
        'last_notification_time': None
    }
    
    if '_id' in settings:
        settings['_id'] = str(settings['_id'])
    
    return jsonify(settings), 200

@alerts_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_alert_settings():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Only admins can update alert settings
    if user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No settings provided'}), 400
    
    allowed_fields = [
        'incident_severity_threshold',
        'notification_channels',
        'auto_notify_responders',
        'auto_notify_resources',
        'notification_cooldown'
    ]
    
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    update_data['updated_at'] = datetime.utcnow()
    
    try:
        result = db.alert_settings.update_one(
            {'_id': 'global'},
            {'$set': update_data},
            upsert=True
        )
        
        return jsonify({
            'message': 'Alert settings updated successfully',
            'modified_count': result.modified_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 