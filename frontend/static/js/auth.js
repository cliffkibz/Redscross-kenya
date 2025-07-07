// Authentication and User Management
const API_BASE_URL = '/api';

// Token Management
const TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function setTokens(accessToken, refreshToken) {
    localStorage.setItem(TOKEN_KEY, accessToken);
    if (refreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    }
}

function clearTokens() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
}

// API Request Helper
async function apiRequest(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers
    };

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers
        });

        if (response.status === 401) {
            // Token expired, try to refresh
            const refreshToken = getRefreshToken();
            if (refreshToken) {
                const refreshResponse = await fetch(`${API_BASE_URL}/auth/refresh`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${refreshToken}`
                    }
                });

                if (refreshResponse.ok) {
                    const { access_token } = await refreshResponse.json();
                    setTokens(access_token);
                    // Retry the original request with new token
                    return apiRequest(endpoint, options);
                }
            }
            // If refresh failed, redirect to login
            clearTokens();
            window.location.href = '/login';
            return;
        }

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'An error occurred');
        }

        return data;
    } catch (error) {
        showToast('error', error.message);
        throw error;
    }
}

// Authentication Functions
async function login(username, password) {
    try {
        const data = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });

        setTokens(data.access_token, data.refresh_token);
        document.cookie = `access_token=${data.access_token}; path=/; SameSite=Lax`;
        showToast('success', 'Login successful');
        if (data.user && data.user.role === 'admin') {
            window.location.href = '/admin/dashboard';
        } else {
            window.location.href = '/dashboard';
        }
    } catch (error) {
        showToast('error', error.message);
        throw error;
    }
}

async function register(userData) {
    try {
        const data = await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });

        setTokens(data.access_token, data.refresh_token);
        showToast('success', 'Registration successful');
        window.location.href = '/dashboard';
    } catch (error) {
        showToast('error', error.message);
        throw error;
    }
}

async function logout() {
    try {
        await apiRequest('/auth/logout', { method: 'POST' });
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        clearTokens();
        window.location.href = '/login';
    }
}

async function getCurrentUser() {
    try {
        return await apiRequest('/auth/me');
    } catch (error) {
        console.error('Get current user error:', error);
        return null;
    }
}

// Form Handling
function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    showLoading();
    login(username, password)
        .catch(error => console.error('Login error:', error))
        .finally(hideLoading);
}

function handleRegister(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const userData = {
        username: formData.get('username'),
        email: formData.get('email'),
        password: formData.get('password'),
        phone: formData.get('phone')
    };
    
    showLoading();
    register(userData)
        .catch(error => console.error('Registration error:', error))
        .finally(hideLoading);
}

// UI Helpers
function showLoading() {
    document.getElementById('loading-spinner').classList.remove('d-none');
}

function hideLoading() {
    document.getElementById('loading-spinner').classList.add('d-none');
}

function showToast(type, message) {
    const toastContainer = document.querySelector('.toast-container');
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
    
    const logoutButton = document.querySelector('[onclick="logout()"]');
    if (logoutButton) {
        logoutButton.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }
    
    // Check authentication status
    const token = getToken();
    if (token) {
        getCurrentUser().then(user => {
            if (user) {
                // Update UI for authenticated user
                const userDropdown = document.getElementById('userDropdown');
                if (userDropdown) {
                    userDropdown.textContent = user.username;
                }
            } else {
                // Invalid token, redirect to login
                clearTokens();
                window.location.href = '/login';
            }
        });
    }
});