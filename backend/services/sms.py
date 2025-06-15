from twilio.rest import Client
from flask import current_app
from backend.models.incident import Incident

def get_twilio_client():
    """Get a Twilio client instance"""
    return Client(
        current_app.config['TWILIO_ACCOUNT_SID'],
        current_app.config['TWILIO_AUTH_TOKEN']
    )

def send_sms(to_number, message):
    """Send an SMS message using Twilio"""
    try:
        client = get_twilio_client()
        message = client.messages.create(
            body=message,
            from_=current_app.config['TWILIO_PHONE_NUMBER'],
            to=to_number
        )
        return message.sid
    except Exception as e:
        current_app.logger.error(f"Failed to send SMS: {str(e)}")
        return None

def send_incident_alert(phone_number, incident):
    """Send an incident alert SMS"""
    message = f"""
🚨 RED CROSS KENYA ALERT 🚨
New {incident.severity.upper()} severity incident reported:
Type: {incident.incident_type}
Location: {incident.location.get('address', 'Location not specified')}
Description: {incident.description[:100]}...
Please respond immediately if you are in the area.
    """.strip()
    
    return send_sms(phone_number, message)

def send_resource_assignment(phone_number, incident, resource):
    """Send a resource assignment notification"""
    message = f"""
🔧 RED CROSS KENYA RESOURCE ASSIGNMENT
Resource: {resource.name} ({resource.resource_type})
Assigned to incident: {incident.title}
Location: {incident.location.get('address', 'Location not specified')}
Please proceed to the incident location.
    """.strip()
    
    return send_sms(phone_number, message)

def send_responder_assignment(phone_number, incident):
    """Send a responder assignment notification"""
    message = f"""
👥 RED CROSS KENYA RESPONDER ASSIGNMENT
You have been assigned to incident: {incident.title}
Type: {incident.incident_type}
Severity: {incident.severity}
Location: {incident.location.get('address', 'Location not specified')}
Please proceed to the incident location.
    """.strip()
    
    return send_sms(phone_number, message)

def send_incident_update(phone_number, incident, update_type, details=None):
    """Send an incident update notification"""
    base_message = f"""
📢 RED CROSS KENYA INCIDENT UPDATE
Incident: {incident.title}
Status: {incident.status}
    """
    
    if update_type == 'status_change':
        message = f"{base_message}\nStatus has been updated to: {incident.status}"
    elif update_type == 'severity_change':
        message = f"{base_message}\nSeverity has been updated to: {incident.severity}"
    elif update_type == 'note_added':
        message = f"{base_message}\nNew note added: {details}"
    else:
        message = f"{base_message}\nUpdate: {details}"
    
    return send_sms(phone_number, message) 