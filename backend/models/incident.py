from datetime import datetime
from bson import ObjectId
from backend.utils.db import get_db

class Incident:
    STATUSES = ['reported', 'verified', 'in_progress', 'resolved', 'closed']
    SEVERITY_LEVELS = ['low', 'medium', 'high', 'critical']
    TYPES = ['flood', 'fire', 'earthquake', 'landslide', 'storm', 'other']
    
    def __init__(self, title, description, incident_type, location, reporter_id,
                 severity='medium', status='reported', photos=None):
        self.title = title
        self.description = description
        self.incident_type = incident_type if incident_type in self.TYPES else 'other'
        self.location = location  # {lat: float, lng: float, address: str}
        self.reporter_id = reporter_id
        self.severity = severity if severity in self.SEVERITY_LEVELS else 'medium'
        self.status = status if status in self.STATUSES else 'reported'
        self.photos = photos or []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.resolved_at = None
        self.assigned_resources = []
        self.responders = []
        self.notes = []
        
    @staticmethod
    def get_by_id(incident_id):
        db = get_db()
        incident_data = db.incidents.find_one({'_id': ObjectId(incident_id)})
        if incident_data:
            incident = Incident(
                title=incident_data['title'],
                description=incident_data['description'],
                incident_type=incident_data['incident_type'],
                location=incident_data['location'],
                reporter_id=incident_data['reporter_id'],
                severity=incident_data['severity'],
                status=incident_data['status'],
                photos=incident_data.get('photos', [])
            )
            incident._id = incident_data['_id']
            incident.created_at = incident_data['created_at']
            incident.updated_at = incident_data['updated_at']
            incident.resolved_at = incident_data.get('resolved_at')
            incident.assigned_resources = incident_data.get('assigned_resources', [])
            incident.responders = incident_data.get('responders', [])
            incident.notes = incident_data.get('notes', [])
            return incident
        return None
    
    def save(self):
        db = get_db()
        incident_data = {
            'title': self.title,
            'description': self.description,
            'incident_type': self.incident_type,
            'location': self.location,
            'reporter_id': self.reporter_id,
            'severity': self.severity,
            'status': self.status,
            'photos': self.photos,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'resolved_at': self.resolved_at,
            'assigned_resources': self.assigned_resources,
            'responders': self.responders,
            'notes': self.notes
        }
        
        if hasattr(self, '_id'):
            db.incidents.update_one(
                {'_id': self._id},
                {'$set': incident_data}
            )
        else:
            result = db.incidents.insert_one(incident_data)
            self._id = result.inserted_id
            
    def add_note(self, user_id, content):
        note = {
            'user_id': user_id,
            'content': content,
            'created_at': datetime.utcnow()
        }
        self.notes.append(note)
        self.updated_at = datetime.utcnow()
        self.save()
        
    def assign_resource(self, resource_id):
        if resource_id not in self.assigned_resources:
            self.assigned_resources.append(resource_id)
            self.updated_at = datetime.utcnow()
            self.save()
            
    def assign_responder(self, responder_id):
        if responder_id not in self.responders:
            self.responders.append(responder_id)
            self.updated_at = datetime.utcnow()
            self.save()
            
    def update_status(self, new_status):
        if new_status in self.STATUSES:
            self.status = new_status
            self.updated_at = datetime.utcnow()
            if new_status == 'resolved':
                self.resolved_at = datetime.utcnow()
            self.save()
            
    def to_dict(self):
        return {
            'id': str(self._id),
            'title': self.title,
            'description': self.description,
            'incident_type': self.incident_type,
            'location': self.location,
            'reporter_id': str(self.reporter_id),
            'severity': self.severity,
            'status': self.status,
            'photos': self.photos,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'assigned_resources': [str(r) for r in self.assigned_resources],
            'responders': [str(r) for r in self.responders],
            'notes': self.notes
        } 