// Alerts and Notifications Management

// SendTest
async function sendTestAlert(phoneNumber) {
    try {
        showLoading();
        await apiRequest('/alerts/test', {
            method: 'POST',
            body: JSON.stringify({ phone_number: phoneNumber })
        });
        
        showToast('success', 'Test alert sent successfully');
    } catch (error) {
        showToast('error', 'Failed to send test alert');
        console.error('Send test alert error:', error);
    } finally {
        hideLoading();
    }
}

// Notify
async function notifyIncidentUpdate(incidentId, notificationType, details = null) {
    try {
        showLoading();
        await apiRequest(`/alerts/incidents/${incidentId}/notify`, {
            method: 'POST',
            body: JSON.stringify({
                notification_type: notificationType,
                details: details
            })
        });
        
        showToast('success', 'Notification sent successfully');
    } catch (error) {
        showToast('error', 'Failed to send notification');
        console.error('Notify incident update error:', error);
    } finally {
        hideLoading();
    }
}

// NotifyResponders
async function notifyResponders(incidentId) {
    try {
        showLoading();
        await apiRequest(`/alerts/incidents/${incidentId}/responders`, {
            method: 'POST'
        });
        
        showToast('success', 'Responders notified successfully');
    } catch (error) {
        showToast('error', 'Failed to notify responders');
        console.error('Notify responders error:', error);
    } finally {
        hideLoading();
    }
}

// NotifyResource
async function notifyResourceAssignment(resourceId) {
    try {
        showLoading();
        await apiRequest(`/alerts/resources/${resourceId}/notify`, {
            method: 'POST'
        });
        
        showToast('success', 'Resource assignment notification sent successfully');
    } catch (error) {
        showToast('error', 'Failed to send resource assignment notification');
        console.error('Notify resource assignment error:', error);
    } finally {
        hideLoading();
    }
}


async function getAlertSettings() {
    try {
        showLoading();
        const data = await apiRequest('/alerts/settings');
        return data;
    } catch (error) {
        showToast('error', 'Failed to get alert settings');
        console.error('Get alert settings error:', error);
        throw error;
    } finally {
        hideLoading();
    }
}


async function updateAlertSettings(settings) {
    try {
        showLoading();
        const data = await apiRequest('/alerts/settings', {
            method: 'PUT',
            body: JSON.stringify(settings)
        });
        
        showToast('success', 'Alert settings updated successfully');
        return data;
    } catch (error) {
        showToast('error', 'Failed to update alert settings');
        console.error('Update alert settings error:', error);
        throw error;
    } finally {
        hideLoading();
    }
}


function createAlertSettingsForm(settings) {
    return `
        <form id="alert-settings-form" class="alert-settings-form">
            <div class="mb-3">
                <label class="form-label">Notification Types</label>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="notify-status" 
                        ${settings.notify_status ? 'checked' : ''}>
                    <label class="form-check-label" for="notify-status">
                        Status Updates
                    </label>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="notify-severity" 
                        ${settings.notify_severity ? 'checked' : ''}>
                    <label class="form-check-label" for="notify-severity">
                        Severity Changes
                    </label>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="notify-notes" 
                        ${settings.notify_notes ? 'checked' : ''}>
                    <label class="form-check-label" for="notify-notes">
                        New Notes
                    </label>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="notify-resources" 
                        ${settings.notify_resources ? 'checked' : ''}>
                    <label class="form-check-label" for="notify-resources">
                        Resource Assignments
                    </label>
                </div>
            </div>
            
            <div class="mb-3">
                <label class="form-label">Severity Thresholds</label>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="notify-low" 
                        ${settings.notify_low_severity ? 'checked' : ''}>
                    <label class="form-check-label" for="notify-low">
                        Low Severity
                    </label>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="notify-medium" 
                        ${settings.notify_medium_severity ? 'checked' : ''}>
                    <label class="form-check-label" for="notify-medium">
                        Medium Severity
                    </label>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="notify-high" 
                        ${settings.notify_high_severity ? 'checked' : ''}>
                    <label class="form-check-label" for="notify-high">
                        High Severity
                    </label>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="notify-critical" 
                        ${settings.notify_critical_severity ? 'checked' : ''}>
                    <label class="form-check-label" for="notify-critical">
                        Critical Severity
                    </label>
                </div>
            </div>
            
            <div class="mb-3">
                <label class="form-label">Notification Methods</label>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="notify-sms" 
                        ${settings.notify_sms ? 'checked' : ''}>
                    <label class="form-check-label" for="notify-sms">
                        SMS
                    </label>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="notify-email" 
                        ${settings.notify_email ? 'checked' : ''}>
                    <label class="form-check-label" for="notify-email">
                        Email
                    </label>
                </div>
            </div>
            
            <button type="submit" class="btn btn-primary">Save Settings</button>
        </form>
    `;
}


function handleAlertSettingsSubmit(event) {
    event.preventDefault();
    const settings = {
        notify_status: document.getElementById('notify-status').checked,
        notify_severity: document.getElementById('notify-severity').checked,
        notify_notes: document.getElementById('notify-notes').checked,
        notify_resources: document.getElementById('notify-resources').checked,
        notify_low_severity: document.getElementById('notify-low').checked,
        notify_medium_severity: document.getElementById('notify-medium').checked,
        notify_high_severity: document.getElementById('notify-high').checked,
        notify_critical_severity: document.getElementById('notify-critical').checked,
        notify_sms: document.getElementById('notify-sms').checked,
        notify_email: document.getElementById('notify-email').checked
    };
    
    updateAlertSettings(settings)
        .then(() => {
            // Reload settings
            loadAlertSettings();
        })
        .catch(error => console.error('Update settings error:', error));
}

function handleTestAlertSubmit(event) {
    event.preventDefault();
    const phoneNumber = document.getElementById('test-phone').value;
    sendTestAlert(phoneNumber);
}


async function loadAlertSettings() {
    try {
        const settings = await getAlertSettings();
        const settingsContainer = document.getElementById('alert-settings');
        if (settingsContainer) {
            settingsContainer.innerHTML = createAlertSettingsForm(settings);
            
            // Add event listener to the new form
            const form = document.getElementById('alert-settings-form');
            if (form) {
                form.addEventListener('submit', handleAlertSettingsSubmit);
            }
        }
    } catch (error) {
        console.error('Load settings error:', error);
    }
}


document.addEventListener('DOMContentLoaded', () => {
    // Load alert settings if on settings page
    const settingsContainer = document.getElementById('alert-settings');
    if (settingsContainer) {
        loadAlertSettings();
    }
    

    const testAlertForm = document.getElementById('test-alert-form');
    if (testAlertForm) {
        testAlertForm.addEventListener('submit', handleTestAlertSubmit);
    }
    

    const notifyStatusBtn = document.getElementById('notify-status-btn');
    if (notifyStatusBtn) {
        notifyStatusBtn.addEventListener('click', () => {
            const incidentId = notifyStatusBtn.dataset.incidentId;
            notifyIncidentUpdate(incidentId, 'status_update');
        });
    }
    
    const notifySeverityBtn = document.getElementById('notify-severity-btn');
    if (notifySeverityBtn) {
        notifySeverityBtn.addEventListener('click', () => {
            const incidentId = notifySeverityBtn.dataset.incidentId;
            notifyIncidentUpdate(incidentId, 'severity_update');
        });
    }
    
    const notifyRespondersBtn = document.getElementById('notify-responders-btn');
    if (notifyRespondersBtn) {
        notifyRespondersBtn.addEventListener('click', () => {
            const incidentId = notifyRespondersBtn.dataset.incidentId;
            notifyResponders(incidentId);
        });
    }
    

    const notifyResourceBtn = document.getElementById('notify-resource-btn');
    if (notifyResourceBtn) {
        notifyResourceBtn.addEventListener('click', () => {
            const resourceId = notifyResourceBtn.dataset.resourceId;
            notifyResourceAssignment(resourceId);
        });
    }
}); 