// Resource Management

// Load Resources
async function loadResources(filters = {}) {
    try {
        showLoading();
        const queryParams = new URLSearchParams(filters);
        const data = await apiRequest(`/resources?${queryParams}`);
        
        // Update resource list if it exists
        const resourceList = document.getElementById('resource-list');
        if (resourceList) {
            resourceList.innerHTML = data.resources.map(resource => 
                createResourceCard(resource)
            ).join('');
        }
        
        return data;
    } catch (error) {
        showToast('error', 'Failed to load resources');
        console.error('Load resources error:', error);
    } finally {
        hideLoading();
    }
}

// Create Resource
async function createResource(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const resourceData = {
        name: formData.get('name'),
        type: formData.get('type'),
        description: formData.get('description'),
        status: 'available',
        location: {
            latitude: parseFloat(formData.get('latitude')),
            longitude: parseFloat(formData.get('longitude')),
            address: formData.get('address')
        },
        capacity: parseInt(formData.get('capacity')),
        specifications: {
            model: formData.get('model'),
            manufacturer: formData.get('manufacturer'),
            year: formData.get('year'),
            condition: formData.get('condition')
        }
    };
    
    try {
        showLoading();
        const data = await apiRequest('/resources', {
            method: 'POST',
            body: JSON.stringify(resourceData)
        });
        
        showToast('success', 'Resource created successfully');
        window.location.href = `/resources/${data._id}`;
    } catch (error) {
        showToast('error', 'Failed to create resource');
        console.error('Create resource error:', error);
    } finally {
        hideLoading();
    }
}

// Update Resource
async function updateResource(resourceId, updateData) {
    try {
        showLoading();
        const data = await apiRequest(`/resources/${resourceId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
        
        showToast('success', 'Resource updated successfully');
        return data;
    } catch (error) {
        showToast('error', 'Failed to update resource');
        console.error('Update resource error:', error);
        throw error;
    } finally {
        hideLoading();
    }
}

// Add Maintenance Record
async function addMaintenanceRecord(resourceId, recordData) {
    try {
        showLoading();
        const data = await apiRequest(`/resources/${resourceId}/maintenance`, {
            method: 'POST',
            body: JSON.stringify(recordData)
        });
        
        showToast('success', 'Maintenance record added successfully');
        return data;
    } catch (error) {
        showToast('error', 'Failed to add maintenance record');
        console.error('Add maintenance record error:', error);
        throw error;
    } finally {
        hideLoading();
    }
}

// Complete Maintenance
async function completeMaintenance(resourceId, maintenanceId, completionData) {
    try {
        showLoading();
        const data = await apiRequest(`/resources/${resourceId}/maintenance/${maintenanceId}/complete`, {
            method: 'POST',
            body: JSON.stringify(completionData)
        });
        
        showToast('success', 'Maintenance marked as complete');
        return data;
    } catch (error) {
        showToast('error', 'Failed to complete maintenance');
        console.error('Complete maintenance error:', error);
        throw error;
    } finally {
        hideLoading();
    }
}

// Release Resource
async function releaseResource(resourceId) {
    try {
        showLoading();
        const data = await apiRequest(`/resources/${resourceId}/release`, {
            method: 'POST'
        });
        
        showToast('success', 'Resource released successfully');
        return data;
    } catch (error) {
        showToast('error', 'Failed to release resource');
        console.error('Release resource error:', error);
        throw error;
    } finally {
        hideLoading();
    }
}

// Get Available Resources
async function getAvailableResources(incidentType) {
    try {
        showLoading();
        const data = await apiRequest(`/resources/available/${incidentType}`);
        return data;
    } catch (error) {
        showToast('error', 'Failed to get available resources');
        console.error('Get available resources error:', error);
        throw error;
    } finally {
        hideLoading();
    }
}

// UI Helpers
function createResourceCard(resource) {
    const statusColors = {
        'available': 'success',
        'in_use': 'primary',
        'maintenance': 'warning',
        'unavailable': 'danger'
    };
    
    return `
        <div class="card resource-card mb-3">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <h5 class="card-title">${resource.name}</h5>
                    <span class="badge bg-${statusColors[resource.status]}">${resource.status}</span>
                </div>
                <p class="card-text">${resource.description}</p>
                <div class="resource-details">
                    <p><strong>Type:</strong> ${resource.type}</p>
                    <p><strong>Location:</strong> ${resource.location.address}</p>
                    <p><strong>Capacity:</strong> ${resource.capacity}</p>
                    <p><strong>Specifications:</strong></p>
                    <ul>
                        <li>Model: ${resource.specifications.model}</li>
                        <li>Manufacturer: ${resource.specifications.manufacturer}</li>
                        <li>Year: ${resource.specifications.year}</li>
                        <li>Condition: ${resource.specifications.condition}</li>
                    </ul>
                </div>
                <div class="d-flex justify-content-between align-items-center">
                    <a href="/resources/${resource._id}" class="btn btn-primary">View Details</a>
                    <div class="resource-stats">
                        ${resource.current_incident ? 
                            `<span class="badge bg-info">Assigned to Incident</span>` :
                            `<span class="badge bg-success">Available</span>`
                        }
                        <span class="badge bg-secondary">${resource.maintenance_records.length} Maintenance Records</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function createMaintenanceRecordCard(record) {
    return `
        <div class="card maintenance-record-card mb-3">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <h6 class="card-title">${record.type}</h6>
                    <span class="badge bg-${record.status === 'completed' ? 'success' : 'warning'}">
                        ${record.status}
                    </span>
                </div>
                <p class="card-text">${record.description}</p>
                <div class="maintenance-details">
                    <p><strong>Reported:</strong> ${new Date(record.reported_at).toLocaleString()}</p>
                    ${record.completed_at ? 
                        `<p><strong>Completed:</strong> ${new Date(record.completed_at).toLocaleString()}</p>` :
                        ''
                    }
                    ${record.notes ? 
                        `<p><strong>Notes:</strong> ${record.notes}</p>` :
                        ''
                    }
                </div>
                ${record.status === 'pending' && isAdmin() ? 
                    `<button onclick="completeMaintenance('${record._id}')" class="btn btn-success btn-sm">
                        Mark as Complete
                    </button>` :
                    ''
                }
            </div>
        </div>
    `;
}

// Filter Handlers
function handleFilterSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const filters = {
        type: formData.get('type'),
        status: formData.get('status'),
        condition: formData.get('condition')
    };
    
    // Remove empty filters
    Object.keys(filters).forEach(key => {
        if (!filters[key]) delete filters[key];
    });
    
    loadResources(filters);
}

// Utility Functions
function isAdmin() {
    const userRole = document.body.dataset.userRole;
    return userRole === 'admin';
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Form handlers
    const createResourceForm = document.getElementById('create-resource-form');
    if (createResourceForm) {
        createResourceForm.addEventListener('submit', createResource);
    }
    
    const filterForm = document.getElementById('resource-filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', handleFilterSubmit);
    }
    
    // Maintenance form handler
    const maintenanceForm = document.getElementById('add-maintenance-form');
    if (maintenanceForm) {
        maintenanceForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const resourceId = maintenanceForm.dataset.resourceId;
            const formData = new FormData(event.target);
            const recordData = {
                type: formData.get('type'),
                description: formData.get('description'),
                notes: formData.get('notes')
            };
            
            await addMaintenanceRecord(resourceId, recordData);
            maintenanceForm.reset();
            // Reload resource details
            loadResourceDetails(resourceId);
        });
    }
    
    // Status update handler
    const statusSelect = document.getElementById('resource-status');
    if (statusSelect) {
        statusSelect.addEventListener('change', async (event) => {
            const resourceId = statusSelect.dataset.resourceId;
            const newStatus = event.target.value;
            await updateResource(resourceId, { status: newStatus });
            // Reload resource details
            loadResourceDetails(resourceId);
        });
    }
    
    // Initial load
    loadResources();
}); 