

const API_BASE = "/api";

(function authGuard() {
    const publicPaths = ['/', '/register'];
    const path = window.location.pathname;
    if (!publicPaths.includes(path) && path.startsWith('/app')) {
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/';
            return;
        }
    }
})();

function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    const tokenType = localStorage.getItem('token_type') || 'Bearer';
    return token ? { 'Authorization': `${tokenType} ${token}` } : {};
}

async function authenticatedFetch(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
        ...options.headers
    };
    
    const response = await fetch(url, {
        ...options,
        headers
    });
    
    
    if (response.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('token_type');
        localStorage.removeItem('user_data');
        window.location.href = '/';
        return;
    }
    
    return response;
}

function getProfileImageUrl(profileImage) {
    if (!profileImage) return null;
    let value = String(profileImage).trim();
    if (!value) return null;

    
    value = value.replace(/^\/?uploads\/avatars\/+(\/static\/)/i, '$1');
    value = value.replace(/^\/?uploads\/avatars\/+(\/uploads\/)/i, '$1');

    if (value.startsWith('http://') || value.startsWith('https://') || value.startsWith('data:')) {
        return value;
    }
    if (value.startsWith('/')) {
        return value;
    }
    
    if (value.startsWith('static/uploads/') || value.startsWith('uploads/')) {
        return `/${value}`;
    }
    
    return `/uploads/avatars/${value}`;
}

function _avatarPlaceholderDataUri(initials) {
    const letter = encodeURIComponent((initials || 'U').toUpperCase().slice(0, 2));
    return `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect fill="%234F6EF7" width="40" height="40" rx="20"/><text x="20" y="26" text-anchor="middle" fill="white" font-size="16" font-family="Inter,sans-serif">${letter}</text></svg>`;
}

function applyAvatarToElement(el, profileImage, initials) {
    if (!el) return;
    const url = getProfileImageUrl(profileImage);
    const fallback = _avatarPlaceholderDataUri(initials);

    if (el.tagName === 'IMG') {
        el.src = url || fallback;
        el.onerror = () => {
            el.onerror = null;
            el.src = fallback;
        };
        return;
    }

    
    let img = el.querySelector('img.avatar-photo');
    if (!img) {
        el.textContent = '';
        el.style.backgroundImage = '';
        img = document.createElement('img');
        img.className = 'avatar-photo';
        img.alt = 'Avatar';
        el.appendChild(img);
    }
    img.src = url || fallback;
    img.onerror = () => {
        img.onerror = null;
        img.src = fallback;
    };
}

function initializeAuth() {
    
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user_data');
    
    if (token && userData) {
        try {
            const user = JSON.parse(userData);
            updateUserDisplay(user);
            updateSidebarUserInfo(user);
        } catch (e) {
            console.error('Error parsing user data:', e);
        }
    }

    
    if (token) {
        refreshUserProfile();
    }
}

async function refreshUserProfile() {
    try {
        const response = await authenticatedFetch('/api/me');
        if (!response || !response.ok) return;
        const user = await response.json();
        if (!user) return;
        localStorage.setItem('user_data', JSON.stringify(user));
        updateUserDisplay(user);
        updateSidebarUserInfo(user);
    } catch (e) {
        console.warn('Impossible de rafraîchir le profil:', e);
    }
}

function updateSidebarUserInfo(user) {
    
    const sidebarAvatar = document.getElementById('sidebarAvatar');
    const sidebarUsername = document.getElementById('sidebarUsername');
    
    if (sidebarUsername) {
        const name = (user.first_name && user.last_name)
            ? `${user.first_name} ${user.last_name}`
            : user.first_name || user.email?.split('@')[0] || 'Utilisateur';
        sidebarUsername.textContent = name;
    }
    
    if (sidebarAvatar) {
        const initials = (user.first_name?.[0] || user.email?.[0] || 'U').toUpperCase();
        applyAvatarToElement(sidebarAvatar, user.profile_image, initials);
    }
}

function updateUserDisplay(user) {
    
    const nameElements = document.querySelectorAll('#userName, #topbarUsername');
    nameElements.forEach(el => {
        if (el) {
            const name = (user.first_name && user.last_name)
                ? `${user.first_name} ${user.last_name}`
                : user.first_name || user.email?.split('@')[0] || 'Utilisateur';
            el.textContent = name;
        }
    });

    
    const initials = (user.first_name?.[0] || user.email?.[0] || 'U').toUpperCase();
    document.querySelectorAll('#userAvatar').forEach(avatarEl => {
        applyAvatarToElement(avatarEl, user.profile_image, initials);
    });
}

function logout(event) {
    if (event) event.preventDefault();
    
    
    sessionStorage.removeItem('ocrExtractionState');
    
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
    localStorage.removeItem('user_data');
    localStorage.removeItem('otp_token');
    localStorage.removeItem('otp_email_hint');
    
    console.log('✅ Déconnexion - Extraction OCR effacée');
    
    window.location.href = '/';
}

function showNotification(message, type = 'info', duration = 5000) {
    
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            max-width: 400px;
        `;
        document.body.appendChild(container);
    }
    
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#22c55e' : type === 'warning' ? '#f59e0b' : '#3b82f6'};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideIn 0.3s ease-out;
        display: flex;
        align-items: center;
        justify-content: space-between;
    `;
    
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" style="background: none; border: none; color: white; cursor: pointer; margin-left: 10px; font-size: 18px;">×</button>
    `;
    
    container.appendChild(notification);
    
    
    if (duration > 0) {
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, duration);
    }
}

function showSuccess(message, duration) { showNotification(message, 'success', duration); }
function showError(message, duration) { showNotification(message, 'error', duration); }
function showWarning(message, duration) { showNotification(message, 'warning', duration); }
function showInfo(message, duration) { showNotification(message, 'info', duration); }

(function initUserUI() {
    try {
        const stored = localStorage.getItem('user_data') || localStorage.getItem('user') || localStorage.getItem('user_info');
        const user = stored ? JSON.parse(stored) : null;
        if (!user) return;

        updateUserDisplay(user);
    } catch (e) { 
        console.error('User UI init error:', e); 
    }
})();

(function initUserDropdown() {
    const userButton = document.getElementById('userButton');
    const userMenu = document.getElementById('userMenu');
    
    if (userButton && userMenu) {
        userButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            userMenu.classList.toggle('open');
        });
        
        
        document.addEventListener('click', function(e) {
            if (!userMenu.contains(e.target)) {
                userMenu.classList.remove('open');
            }
        });
        
        
        const dropdownMenu = userMenu.querySelector('.dropdown-menu');
        if (dropdownMenu) {
            dropdownMenu.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        }
    }
})();

(function initSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const mainWrapper = document.getElementById('mainWrapper');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');

    if (!sidebar) return;

    
    let overlay = document.querySelector('.sidebar-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 998;
            display: none;
        `;
        document.body.appendChild(overlay);
    }

    function closeMobileSidebar() {
        sidebar.classList.remove('open');
        overlay.style.display = 'none';
    }

    function openMobileSidebar() {
        sidebar.classList.add('open');
        overlay.style.display = 'block';
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                if (sidebar.classList.contains('open')) {
                    closeMobileSidebar();
                } else {
                    openMobileSidebar();
                }
            }
        });
    }

    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', () => {
            if (sidebar.classList.contains('open')) {
                closeMobileSidebar();
            } else {
                openMobileSidebar();
            }
        });
    }

    overlay.addEventListener('click', closeMobileSidebar);

    
    document.querySelectorAll('.menu-item').forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                closeMobileSidebar();
            }
        });
    });
})();

(function highlightActivePage() {
    const path = window.location.pathname;
    document.querySelectorAll('.menu-item').forEach(link => {
        link.classList.remove('active');
        const href = link.getAttribute('href');
        
        
        if (href === path || (path === '/app' && href === '/app')) {
            link.classList.add('active');
        }
        
        else if (path.startsWith(href) && href !== '/app' && href.length > 1) {
            link.classList.add('active');
        }
    });
})();

function validateEmail(email) {
    const emailRegex = /^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email);
}

function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const errorDiv = document.getElementById(fieldId + '-error');
    
    if (message && field && errorDiv) {
        field.classList.add('error');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    } else if (field && errorDiv) {
        field.classList.remove('error');
        errorDiv.style.display = 'none';
    }
}

const animationStyles = `
@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.notification {
    animation: slideIn 0.3s ease-out;
}

.sidebar-overlay {
    transition: opacity 0.3s ease;
}

.sidebar-overlay.show {
    opacity: 1;
}

@media (max-width: 768px) {
    .sidebar {
        transform: translateX(-100%);
        transition: transform 0.3s ease;
    }
    
    .sidebar.open {
        transform: translateX(0);
    }
}
`;

if (!document.getElementById('app-animations')) {
    const style = document.createElement('style');
    style.id = 'app-animations';
    style.textContent = animationStyles;
    document.head.appendChild(style);
}

document.addEventListener('DOMContentLoaded', function() {
    initializeAuth();
});
