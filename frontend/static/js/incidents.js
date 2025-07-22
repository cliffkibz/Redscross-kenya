
let map;
let incidentMarkers = {};
let currentIncident = null;

// Start Map
function initMap() {
    map = L.map('incident-map').setView([-0.0236, 37.9062], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    map.on('click', (e) => {
        if (document.getElementById('create-incident-form')) {
            document.getElementById('latitude').value = e.latlng.lat;
            document.getElementById('longitude').value = e.latlng.lng;
            if (currentIncident) {
                map.removeLayer(currentIncident);
            }
            currentIncident = L.marker(e.latlng).addTo(map);
        }
    });
}
async function loadIncidents(filters = {}) {
    try {
        showLoading();
        const queryParams = new URLSearchParams(filters);
        const data = await apiRequest(`/incidents?${queryParams}`);
        
        Object.values(incidentMarkers).forEach(marker => map.removeLayer(marker));
        incidentMarkers = {};
        
        data.incidents.forEach(incident => {
            const marker = L.marker([incident.location.latitude, incident.location.longitude])
                .bindPopup(createIncidentPopup(incident));
            
            const severityColors = {
                'low': 'green',
                'medium': 'orange',
                'high': 'red',
                'critical': 'purple'
            };
            
            marker.setIcon(L.divIcon({
                className: `incident-marker severity-${incident.severity}`,
                html: `<div class="marker-pin ${severityColors[incident.severity]}"></div>`,
                iconSize: [30, 42],
                iconAnchor: [15, 42]
            }));
            
            marker.addTo(map);
            incidentMarkers[incident._id] = marker;
        });
        
        const incidentList = document.getElementById('incident-list');
        if (incidentList) {
            incidentList.innerHTML = data.incidents.map(incident => 
                createIncidentCard(incident)
            ).join('');
        }
        
        return data;
    } catch (error) {
        showToast('error', 'Failed to load incidents');
        console.error('Load incidents error:', error);
    } finally {
        hideLoading();
    }
}

async function createIncident(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const incidentData = {
        title: formData.get('title'),
        description: formData.get('description'),
        type: formData.get('type'),
        severity: formData.get('severity'),
        location: {
            latitude: parseFloat(formData.get('latitude')),
            longitude: parseFloat(formData.get('longitude')),
            address: formData.get('address')
        },
        affected_areas: formData.get('affected_areas').split(',').map(area => area.trim()),
        resources_needed: formData.get('resources_needed').split(',').map(resource => resource.trim())
    };
    
    try {
        showLoading();
        const data = await apiRequest('/incidents', {
            method: 'POST',
            body: JSON.stringify(incidentData)
        });
        
        showToast('success', 'Incident created successfully');
        window.location.href = `/incidents/${data._id}`;
    } catch (error) {
        showToast('error', 'Failed to create incident');
        console.error('Create incident error:', error);
    } finally {
        hideLoading();
    }
}
async function updateIncident(incidentId, updateData) {
    try {
        showLoading();
        const data = await apiRequest(`/incidents/${incidentId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
        
        showToast('success', 'Incident updated successfully');
        return data;
    } catch (error) {
        showToast('error', 'Failed to update incident');
        console.error('Update incident error:', error);
        throw error;
    } finally {
        hideLoading();
    }
}

// Add Note to Incident
async function addIncidentNote(incidentId, note) {
    try {
        showLoading();
        const data = await apiRequest(`/incidents/${incidentId}/notes`, {
            method: 'POST',
            body: JSON.stringify({ note })
        });
        
        showToast('success', 'Note added successfully');
        return data;
    } catch (error) {
        showToast('error', 'Failed to add note');
        console.error('Add note error:', error);
        throw error;
    } finally {
        hideLoading();
    }
}
async function assignResponder(incidentId, responderId) {
    try {
        showLoading();
        const data = await apiRequest(`/incidents/${incidentId}/responders`, {
            method: 'POST',
            body: JSON.stringify({ responder_id: responderId })
        });
        
        showToast('success', 'Responder assigned successfully');
        return data;
    } catch (error) {
        showToast('error', 'Failed to assign responder');
        console.error('Assign responder error:', error);
        throw error;
    } finally {
        hideLoading();
    }
}
async function assignResource(incidentId, resourceId) {
    try {
        showLoading();
        const data = await apiRequest(`/incidents/${incidentId}/resources`, {
            method: 'POST',
            body: JSON.stringify({ resource_id: resourceId })
        });
        
        showToast('success', 'Resource assigned successfully');
        return data;
    } catch (error) {
        showToast('error', 'Failed to assign resource');
        console.error('Assign resource error:', error);
        throw error;
    } finally {
        hideLoading();
    }
}
function createIncidentPopup(incident) {
    return `
        <div class="incident-popup">
            <h5>${incident.title}</h5>
            <p class="severity-${incident.severity}">${incident.severity.toUpperCase()}</p>
            <p>${incident.description}</p>
            <p><strong>Type:</strong> ${incident.type}</p>
            <p><strong>Status:</strong> ${incident.status}</p>
            <p><strong>Reported:</strong> ${new Date(incident.created_at).toLocaleString()}</p>
            <a href="/incidents/${incident._id}" class="btn btn-primary btn-sm">View Details</a>
        </div>
    `;
}

function createIncidentCard(incident) {
    return `
        <div class="card incident-card mb-3">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <h5 class="card-title">${incident.title}</h5>
                    <span class="badge severity-${incident.severity}">${incident.severity}</span>
                </div>
                <p class="card-text">${incident.description}</p>
                <div class="incident-details">
                    <p><strong>Type:</strong> ${incident.type}</p>
                    <p><strong>Status:</strong> ${incident.status}</p>
                    <p><strong>Location:</strong> ${incident.location.address}</p>
                    <p><strong>Reported:</strong> ${new Date(incident.created_at).toLocaleString()}</p>
                </div>
                <div class="d-flex justify-content-between align-items-center">
                    <a href="/incidents/${incident._id}" class="btn btn-primary">View Details</a>
                    <div class="incident-stats">
                        <span class="badge bg-info">${incident.responders.length} Responders</span>
                        <span class="badge bg-secondary">${incident.resources.length} Resources</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}
function handleFilterSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const filters = {
        type: formData.get('type'),
        severity: formData.get('severity'),
        status: formData.get('status'),
        start_date: formData.get('start_date'),
        end_date: formData.get('end_date')
    };
    
    Object.keys(filters).forEach(key => {
        if (!filters[key]) delete filters[key];
    });
    
    loadIncidents(filters);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    const mapElement = document.getElementById('incident-map');
    if (mapElement) {
        initMap();
        loadIncidents();
    }
    
    const createIncidentForm = document.getElementById('create-incident-form');
    if (createIncidentForm) {
        createIncidentForm.addEventListener('submit', createIncident);
    }
    
    const filterForm = document.getElementById('incident-filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', handleFilterSubmit);
    }
    
    const noteForm = document.getElementById('add-note-form');
    if (noteForm) {
        noteForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const incidentId = noteForm.dataset.incidentId;
            const note = document.getElementById('note-text').value;
            await addIncidentNote(incidentId, note);
            noteForm.reset();
            // Reload incident details
            loadIncidentDetails(incidentId);
        });
    }
    
    const statusSelect = document.getElementById('incident-status');
    if (statusSelect) {
        statusSelect.addEventListener('change', async (event) => {
            const incidentId = statusSelect.dataset.incidentId;
            const newStatus = event.target.value;
            await updateIncident(incidentId, { status: newStatus });
            loadIncidentDetails(incidentId);
        });
    }
}); 