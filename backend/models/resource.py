from datetime import datetime
from bson import ObjectId
from backend.utils.db import get_db

class Resource:
    TYPES = [
        'ambulance', 'boat', 'truck', 'helicopter', 'medical_supplies',
        'food', 'water', 'shelter', 'rescue_equipment', 'communication_equipment'
    ]
    STATUSES = ['available', 'in_use', 'maintenance', 'reserved']
    
    def __init__(self, name, resource_type, location, status='available',
                 capacity=None, description=None, current_incident=None):
        self.name = name
        self.resource_type = resource_type if resource_type in self.TYPES else 'other'
        self.location = location  # {(lat: float), (lng: float), (address: str)}
        self.status = status if status in self.STATUSES else 'available'
        self.capacity = capacity
        self.description = description
        self.current_incident = current_incident
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.maintenance_history = []
        self.usage_history = []
        
    @staticmethod
    def get_by_id(resource_id):
        db = get_db()
        resource_data = db.resources.find_one({'_id': ObjectId(resource_id)})
        if resource_data:
            resource = Resource(
                name=resource_data['name'],
                resource_type=resource_data['resource_type'],
                location=resource_data['location'],
                status=resource_data['status'],
                capacity=resource_data.get('capacity'),
                description=resource_data.get('description'),
                current_incident=resource_data.get('current_incident')
            )
            resource._id = resource_data['_id']
            resource.created_at = resource_data['created_at']
            resource.updated_at = resource_data['updated_at']
            resource.maintenance_history = resource_data.get('maintenance_history', [])
            resource.usage_history = resource_data.get('usage_history', [])
            return resource
        return None
    
    @staticmethod
    def get_available_by_type(resource_type):
        db = get_db()
        resources = []
        cursor = db.resources.find({
            'resource_type': resource_type,
            'status': 'available'
        })
        for resource_data in cursor:
            resource = Resource(
                name=resource_data['name'],
                resource_type=resource_data['resource_type'],
                location=resource_data['location'],
                status=resource_data['status'],
                capacity=resource_data.get('capacity'),
                description=resource_data.get('description'),
                current_incident=resource_data.get('current_incident')
            )
            resource._id = resource_data['_id']
            resource.created_at = resource_data['created_at']
            resource.updated_at = resource_data['updated_at']
            resource.maintenance_history = resource_data.get('maintenance_history', [])
            resource.usage_history = resource_data.get('usage_history', [])
            resources.append(resource)
        return resources
    
    def save(self):
        db = get_db()
        resource_data = {
            'name': self.name,
            'resource_type': self.resource_type,
            'location': self.location,
            'status': self.status,
            'capacity': self.capacity,
            'description': self.description,
            'current_incident': self.current_incident,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'maintenance_history': self.maintenance_history,
            'usage_history': self.usage_history
        }
        
        if hasattr(self, '_id'):
            db.resources.update_one(
                {'_id': self._id},
                {'$set': resource_data}
            )
        else:
            result = db.resources.insert_one(resource_data)
            self._id = result.inserted_id
            
    def assign_to_incident(self, incident_id):
        if self.status == 'available':
            self.status = 'in_use'
            self.current_incident = incident_id
            self.usage_history.append({
                'incident_id': incident_id,
                'assigned_at': datetime.utcnow(),
                'status': 'assigned'
            })
            self.updated_at = datetime.utcnow()
            self.save()
            return True
        return False
    
    def release_from_incident(self):
        if self.status == 'in_use' and self.current_incident:
            last_usage = self.usage_history[-1]
            last_usage['released_at'] = datetime.utcnow()
            last_usage['status'] = 'completed'
            
            self.status = 'available'
            self.current_incident = None
            self.updated_at = datetime.utcnow()
            self.save()
            return True
        return False
    
    def add_maintenance_record(self, description, performed_by):
        record = {
            'description': description,
            'performed_by': performed_by,
            'performed_at': datetime.utcnow()
        }
        self.maintenance_history.append(record)
        self.status = 'maintenance'
        self.updated_at = datetime.utcnow()
        self.save()
        
    def complete_maintenance(self):
        if self.status == 'maintenance':
            self.status = 'available'
            self.updated_at = datetime.utcnow()
            self.save()
            return True
        return False
    
    def to_dict(self):
        return {
            'id': str(self._id),
            'name': self.name,
            'resource_type': self.resource_type,
            'location': self.location,
            'status': self.status,
            'capacity': self.capacity,
            'description': self.description,
            'current_incident': str(self.current_incident) if self.current_incident else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'maintenance_history': self.maintenance_history,
            'usage_history': self.usage_history
        } 