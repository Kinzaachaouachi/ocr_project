

const API_BASE = "/api";
const AUTH_COOKIE = "ocr_auth";

function _setAuthCookie() {
    document.cookie = `${AUTH_COOKIE}=1; path=/; SameSite=Lax; Max-Age=86400`;
}

function _clearAuthCookie() {
    document.cookie = `${AUTH_COOKIE}=; path=/; SameSite=Lax; Max-Age=0`;
}

function clearAuthSession() {
    try {
        if (typeof stopOcrJobPolling === 'function') stopOcrJobPolling();
    } catch (e) {}
    try {
        if (typeof hideOcrProgressFab === 'function') hideOcrProgressFab();
    } catch (e) {}
    try {
        if (window.__ocrWorkerPort) {
            window.__ocrWorkerPort.postMessage({ type: 'stop' });
        }
    } catch (e) {}

    const keys = [
        'access_token', 'token_type', 'user_data', 'user', 'user_info', 'token',
        'otp_token', 'otp_email_hint',
        'ocrExtractionState', 'ocrActiveJob', 'ocrNotifiedJobs', 'ocrAppNotifications',
    ];
    keys.forEach((k) => {
        try { localStorage.removeItem(k); } catch (e) {}
    });
    try {
        sessionStorage.removeItem('ocrExtractionState');
        sessionStorage.removeItem('ocrKeepOnNextLoad');
        sessionStorage.setItem('auth_logged_out', '1');
    } catch (e) {}
    _clearAuthCookie();
}

function isProtectedAppPath(pathname) {
    return String(pathname || window.location.pathname).startsWith('/app');
}

function hasValidAuthToken() {
    try {
        const token = localStorage.getItem('access_token');
        return !!(token && String(token).trim());
    } catch (e) {
        return false;
    }
}

function redirectToLogin() {
    const target = '/';
    if (window.location.pathname === '/' || window.location.pathname === '') return;
    window.location.replace(target);
}

function enforceAuthGuard() {
    if (!isProtectedAppPath()) return true;
    if (hasValidAuthToken()) {
        try { sessionStorage.removeItem('auth_logged_out'); } catch (e) {}
        _setAuthCookie();
        return true;
    }
    // Masquer immédiatement le contenu (historique / bfcache)
    try {
        document.documentElement.style.visibility = 'hidden';
        if (document.body) document.body.innerHTML = '';
    } catch (e) {}
    clearAuthSession();
    redirectToLogin();
    return false;
}

(function authGuard() {
    enforceAuthGuard();

    // Retour / avant navigateur (bfcache) : re-vérifier le token
    window.addEventListener('pageshow', function (event) {
        if (event.persisted || isProtectedAppPath()) {
            enforceAuthGuard();
        }
    });

    // Onglet revenu au premier plan
    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'visible' && isProtectedAppPath()) {
            enforceAuthGuard();
        }
    });

    // Déconnexion depuis un autre onglet
    window.addEventListener('storage', function (event) {
        if (event.key === 'access_token' && !event.newValue && isProtectedAppPath()) {
            enforceAuthGuard();
        }
    });

    // Réduit le risque de restauration bfcache après départ
    window.addEventListener('pagehide', function () {
        if (!hasValidAuthToken() && isProtectedAppPath()) {
            try { document.body.innerHTML = ''; } catch (e) {}
        }
    });
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
        clearAuthSession();
        redirectToLogin();
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
    
    if (isProtectedAppPath() && !enforceAuthGuard()) return;

    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user_data');
    
    if (token && userData) {
        try {
            const user = JSON.parse(userData);
            _setAuthCookie();
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

    clearAuthSession();
    console.log('✅ Déconnexion — session effacée');

    // replace : la page protégée ne reste pas dans l'historique "avant"
    window.location.replace('/');
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

const APP_NOTIF_KEY = 'ocrAppNotifications';
const APP_NOTIF_MAX = 30;

function _readAppNotifications() {
    try {
        return JSON.parse(localStorage.getItem(APP_NOTIF_KEY) || '[]');
    } catch (e) {
        return [];
    }
}

function _writeAppNotifications(list) {
    localStorage.setItem(APP_NOTIF_KEY, JSON.stringify(list.slice(0, APP_NOTIF_MAX)));
}

function _formatNotifTime(iso) {
    try {
        const d = new Date(iso);
        return d.toLocaleString('fr-FR', {
            day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
        });
    } catch (e) {
        return '';
    }
}

function getUnreadNotificationCount() {
    return _readAppNotifications().filter((n) => !n.read).length;
}

function updateNotificationBadge() {
    const badge = document.getElementById('app-notif-badge');
    if (!badge) return;
    const count = getUnreadNotificationCount();
    if (count > 0) {
        badge.textContent = count > 9 ? '9+' : String(count);
        badge.classList.add('show');
    } else {
        badge.classList.remove('show');
        badge.textContent = '';
    }
}

function renderNotificationPanel() {
    const listEl = document.getElementById('app-notif-list');
    if (!listEl) return;
    const items = _readAppNotifications();
    if (!items.length) {
        listEl.innerHTML = '<div class="app-notif-empty">Aucune notification pour le moment</div>';
        return;
    }
    listEl.innerHTML = items.map((n) => `
        <div class="app-notif-item type-${n.type || 'info'} ${n.read ? '' : 'unread'}" data-id="${n.id}" onclick="openAppNotification('${n.id}')">
            <div class="app-notif-item-title">${n.title || 'Notification'}</div>
            <div class="app-notif-item-msg">${n.message || ''}</div>
            <div class="app-notif-item-time">${_formatNotifTime(n.createdAt)}</div>
        </div>
    `).join('');
}

function openAppNotification(id) {
    const items = _readAppNotifications();
    const idx = items.findIndex((n) => n.id === id);
    if (idx >= 0) {
        items[idx].read = true;
        _writeAppNotifications(items);
        updateNotificationBadge();
        renderNotificationPanel();
        const link = items[idx].link;
        if (link && window.location.pathname !== link) {
            window.location.href = link;
        }
    }
}

function markAllNotificationsRead() {
    const items = _readAppNotifications().map((n) => ({ ...n, read: true }));
    _writeAppNotifications(items);
    updateNotificationBadge();
    renderNotificationPanel();
}

function clearAllNotifications() {
    _writeAppNotifications([]);
    updateNotificationBadge();
    renderNotificationPanel();
}

function ensureBrowserNotificationPermission() {
    if (!('Notification' in window)) return Promise.resolve('denied');
    if (Notification.permission === 'granted' || Notification.permission === 'denied') {
        return Promise.resolve(Notification.permission);
    }
    return Notification.requestPermission();
}

function showBrowserNotification(title, body) {
    if (!('Notification' in window) || Notification.permission !== 'granted') return;
    try {
        const n = new Notification(title, {
            body,
            tag: 'ocr-extraction',
        });
        n.onclick = () => {
            window.focus();
            if (!window.location.pathname.includes('/app/ocr')) {
                window.location.href = '/app/ocr';
            }
            n.close();
        };
    } catch (e) {
        console.warn('Notification navigateur impossible:', e);
    }
}

function pushAppNotification(opts = {}) {
    const item = {
        id: `n_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
        title: opts.title || 'Notification',
        message: opts.message || '',
        type: opts.type || 'info',
        link: opts.link || null,
        read: false,
        createdAt: new Date().toISOString(),
    };

    const list = _readAppNotifications();
    list.unshift(item);
    _writeAppNotifications(list);
    updateNotificationBadge();
    renderNotificationPanel();

    if (opts.toast !== false) {
        const toastFn = item.type === 'success' ? showSuccess
            : item.type === 'error' ? showError
            : item.type === 'warning' ? showWarning
            : showInfo;
        toastFn(`${item.title} — ${item.message}`, opts.toastDuration || 6000);
    }

    if (opts.browser !== false) {
        showBrowserNotification(item.title, item.message);
    }

    return item;
}

function notifyExtractionComplete(data = {}) {
    const ok = data.successful_extractions ?? 0;
    const total = data.total_models_tested ?? 0;
    const file = data.file || 'document';
    const time = data.total_processing_time_s != null ? `${data.total_processing_time_s}s` : '';
    const best = data.best_model_name ? ` Meilleur modèle : ${data.best_model_name}.` : '';

    return pushAppNotification({
        title: '✅ Extraction terminée',
        message: `${file} — ${ok}/${total} modèles réussis.${best}${time ? ` Durée : ${time}.` : ''}`.trim(),
        type: 'success',
        link: '/app/ocr',
        browser: true,
        toast: true,
        toastDuration: 7000,
    });
}

function notifyExtractionStarted(filename) {
    return pushAppNotification({
        title: '⏳ Extraction en cours',
        message: `Traitement de « ${filename || 'document'} » avec les 4 modèles OCR…`,
        type: 'info',
        link: '/app/ocr',
        browser: false,
        toast: true,
        toastDuration: 3500,
    });
}

function notifyExtractionFailed(errorMessage, filename) {
    return pushAppNotification({
        title: '❌ Extraction échouée',
        message: `${filename ? filename + ' — ' : ''}${errorMessage || 'Une erreur est survenue.'}`,
        type: 'error',
        link: '/app/ocr',
        browser: true,
        toast: true,
    });
}


const OCR_ACTIVE_JOB_KEY = 'ocrActiveJob';
const OCR_NOTIFIED_JOBS_KEY = 'ocrNotifiedJobs';
let _ocrJobPollTimer = null;
let _ocrSharedWorker = null;
let _ocrWorkerPort = null;
let _ocrWorkerReady = false;

function getActiveOcrJob() {
    try {
        return JSON.parse(localStorage.getItem(OCR_ACTIVE_JOB_KEY) || 'null');
    } catch (e) {
        return null;
    }
}

function setActiveOcrJob(job) {
    if (!job) localStorage.removeItem(OCR_ACTIVE_JOB_KEY);
    else localStorage.setItem(OCR_ACTIVE_JOB_KEY, JSON.stringify(job));
}

function _wasJobNotified(jobId) {
    try {
        const ids = JSON.parse(localStorage.getItem(OCR_NOTIFIED_JOBS_KEY) || '[]');
        return ids.includes(jobId);
    } catch (e) {
        return false;
    }
}

function _markJobNotified(jobId) {
    if (!jobId) return;
    try {
        const ids = JSON.parse(localStorage.getItem(OCR_NOTIFIED_JOBS_KEY) || '[]');
        if (!ids.includes(jobId)) {
            ids.unshift(jobId);
            localStorage.setItem(OCR_NOTIFIED_JOBS_KEY, JSON.stringify(ids.slice(0, 40)));
        }
    } catch (e) {}
}

function _slimOcrResultForStorage(data) {
    if (!data) return null;
    return {
        ...data,
        results: (data.results || []).map((r) => ({
            model_id: r.model_id,
            model_name: r.model_name,
            status: r.status,
            text: r.text,
            error: r.error,
            char_count: r.char_count,
            word_count: r.word_count,
            quality_score: r.quality_score,
            timing: r.timing,
            word_confidence: r.word_confidence,
        })),
    };
}

function persistCompletedOcrResult(data) {
    const token = localStorage.getItem('access_token');
    if (!data || !token) return;
    try {
        localStorage.setItem('ocrExtractionState', JSON.stringify({
            data: _slimOcrResultForStorage(data),
            edits: {},
            baselines: {},
            token,
        }));
        sessionStorage.setItem('ocrKeepOnNextLoad', '1');
    } catch (e) {
        console.warn('Persist OCR result failed:', e);
    }
}

function _onOcrCompleted(result, jobId) {
    const active = getActiveOcrJob() || {};
    updateOcrProgressFab({
        ...active,
        status: 'completed',
        progress: 100,
        message: 'Extraction terminée',
        filename: (result && (result.filename || result.file)) || active.filename,
    });

    if (jobId && _wasJobNotified(jobId)) {
        persistCompletedOcrResult(result);
        setActiveOcrJob(null);
        hideOcrProgressFab(2200);
        window.dispatchEvent(new CustomEvent('ocr-job-completed', { detail: result }));
        return;
    }
    if (jobId) _markJobNotified(jobId);
    stopOcrJobPolling();
    setActiveOcrJob(null);
    hideOcrProgressFab(2800);
    persistCompletedOcrResult(result);
    if (typeof notifyExtractionComplete === 'function') {
        notifyExtractionComplete(result);
    }
    window.dispatchEvent(new CustomEvent('ocr-job-completed', { detail: result }));
}

function _onOcrFailed(error, filename, jobId) {
    const active = getActiveOcrJob() || {};
    updateOcrProgressFab({
        ...active,
        status: 'failed',
        progress: Number(active.progress) || 0,
        message: error || 'Échec de l\'extraction',
        filename: filename || active.filename,
    });

    if (jobId && _wasJobNotified(jobId)) {
        setActiveOcrJob(null);
        hideOcrProgressFab(2500);
        return;
    }
    if (jobId) _markJobNotified(jobId);
    stopOcrJobPolling();
    setActiveOcrJob(null);
    hideOcrProgressFab(3200);
    if (typeof notifyExtractionFailed === 'function') {
        notifyExtractionFailed(error || 'Erreur', filename);
    }
    window.dispatchEvent(new CustomEvent('ocr-job-failed', { detail: { error, filename } }));
}

async function pollOcrJobOnce(jobId) {
    const response = await authenticatedFetch(`/api/extract-all/jobs/${jobId}`);
    if (!response || !response.ok) {
        if (response && response.status === 404) {
            setActiveOcrJob(null);
            stopOcrJobPolling();
            hideOcrProgressFab();
        }
        return null;
    }
    return response.json();
}

function stopOcrJobPolling() {
    if (_ocrJobPollTimer) {
        clearInterval(_ocrJobPollTimer);
        _ocrJobPollTimer = null;
    }
}

function handleOcrJobUpdate(job) {
    if (!job) return;

    const active = getActiveOcrJob() || {};
    const status = job.status || active.status;
    const merged = {
        ...active,
        jobId: job.job_id || job.jobId || active.jobId,
        filename: job.filename || active.filename,
        status,
        progress: _mergeOcrProgress(active.progress, job.progress, status),
        message: job.message || active.message,
        startedAt: active.startedAt || job.created_at || new Date().toISOString(),
        created_at: job.created_at || active.created_at,
    };
    setActiveOcrJob(merged);
    window.dispatchEvent(new CustomEvent('ocr-job-progress', { detail: merged }));
    updateOcrProgressFab(merged);

    const jobId = merged.jobId;
    if (job.status === 'completed' && job.result) {
        _onOcrCompleted(job.result, jobId);
        return;
    }
    if (job.status === 'failed') {
        _onOcrFailed(job.error || job.message || 'Erreur', job.filename, jobId);
    }
}

function startOcrJobPolling(jobId, filename) {
    stopOcrJobPolling();
    const active = getActiveOcrJob() || {};
    const started = {
        jobId,
        filename: filename || active.filename,
        status: active.status === 'uploading' ? 'queued' : (active.status || 'queued'),
        progress: Math.max(Number(active.progress) || 0, 0),
        message: active.message || 'En file d\'attente…',
        startedAt: active.startedAt || new Date().toISOString(),
    };
    setActiveOcrJob(started);
    updateOcrProgressFab(started);

    const tick = async () => {
        try {
            const job = await pollOcrJobOnce(jobId);
            if (job) handleOcrJobUpdate(job);
        } catch (e) {
            console.warn('OCR job poll error:', e);
        }
    };

    tick();
    _ocrJobPollTimer = setInterval(tick, 1000);
}

function _handleWorkerMessage(msg) {
    if (!msg || !msg.type) return;

    if (msg.type === 'job' && msg.job) {
        const j = msg.job;
        const active = getActiveOcrJob() || {};
        const status = j.status || active.status;
        const merged = {
            ...active,
            jobId: j.jobId || j.job_id || active.jobId,
            filename: j.filename || active.filename,
            status,
            progress: _mergeOcrProgress(active.progress, j.progress, status),
            message: j.message || active.message,
            startedAt: active.startedAt || j.startedAt || j.created_at || new Date().toISOString(),
            created_at: j.created_at || active.created_at,
        };
        setActiveOcrJob(merged);
        window.dispatchEvent(new CustomEvent('ocr-job-progress', { detail: merged }));
        updateOcrProgressFab(merged);
        return;
    }

    if (msg.type === 'completed' && msg.result) {
        const active = getActiveOcrJob();
        _onOcrCompleted(msg.result, active && active.jobId);
        return;
    }

    if (msg.type === 'failed') {
        const active = getActiveOcrJob();
        const err = String(msg.error || '');
        if (/failed to fetch|networkerror|load failed|aborted/i.test(err)) {
            console.warn('Worker fetch interrompu — récupération serveur…');
            recoverOcrJobFromServer(msg.filename);
            return;
        }
        _onOcrFailed(msg.error, msg.filename, active && active.jobId);
    }
}

function getOcrSharedWorker() {
    if (_ocrWorkerPort) return _ocrWorkerPort;
    if (typeof SharedWorker === 'undefined') return null;

    try {
        _ocrSharedWorker = new SharedWorker('/static/js/ocr-job-worker.js?v=20260727r', {
            name: 'ocr-extraction-worker',
        });
        _ocrWorkerPort = _ocrSharedWorker.port;
        window.__ocrWorkerPort = _ocrWorkerPort;
        _ocrWorkerPort.onmessage = (e) => {
            if (e.data && e.data.type === 'ready') _ocrWorkerReady = true;
            _handleWorkerMessage(e.data);
        };
        _ocrWorkerPort.start();
        _ocrWorkerPort.postMessage({ type: 'hello' });
        return _ocrWorkerPort;
    } catch (e) {
        console.warn('SharedWorker indisponible:', e);
        _ocrWorkerPort = null;
        window.__ocrWorkerPort = null;
        return null;
    }
}

async function recoverOcrJobFromServer(preferredFilename) {
    try {
        const res = await authenticatedFetch('/api/extract-all/jobs/active');
        if (!res || !res.ok) return false;
        const data = await res.json();
        const job = data.job;
        if (!job) return false;

        if (job.status === 'completed' && job.result) {
            _onOcrCompleted(job.result, job.job_id);
            return true;
        }
        if (job.status === 'failed') {
            _onOcrFailed(job.error || job.message, job.filename || preferredFilename, job.job_id);
            return true;
        }
        if (job.status === 'queued' || job.status === 'running') {
            if (typeof notifyExtractionStarted === 'function' && preferredFilename) {
                // déjà notifié au lancement — skip
            }
            startOcrJobPolling(job.job_id, job.filename || preferredFilename);
            const port = getOcrSharedWorker();
            if (port) {
                port.postMessage({
                    type: 'resume',
                    jobId: job.job_id,
                    filename: job.filename || preferredFilename,
                    token: localStorage.getItem('access_token'),
                    tokenType: localStorage.getItem('token_type') || 'Bearer',
                });
            }
            showInfo('Extraction toujours en cours en arrière-plan…', 4000);
            return true;
        }
    } catch (e) {
        console.warn('recoverOcrJobFromServer:', e);
    }
    return false;
}

async function resumeActiveOcrJobPolling() {
    const port = getOcrSharedWorker();
    if (port) {
        port.postMessage({ type: 'subscribe' });
    }

    const active = getActiveOcrJob();
    if (active && active.jobId && active.status !== 'completed' && active.status !== 'failed') {
        console.log('🔁 Reprise du suivi extraction:', active.jobId);
        if (port) {
            port.postMessage({
                type: 'resume',
                jobId: active.jobId,
                filename: active.filename,
                token: localStorage.getItem('access_token'),
                tokenType: localStorage.getItem('token_type') || 'Bearer',
            });
        } else {
            startOcrJobPolling(active.jobId, active.filename);
        }
        return;
    }

    // Pas de job local → demander au serveur
    await recoverOcrJobFromServer();
}

async function startAsyncExtraction(file) {
    const token = localStorage.getItem('access_token');
    const tokenType = localStorage.getItem('token_type') || 'Bearer';
    if (!token) throw new Error('Non authentifié');

    if (typeof ensureBrowserNotificationPermission === 'function') {
        ensureBrowserNotificationPermission();
    }
    if (typeof notifyExtractionStarted === 'function') {
        notifyExtractionStarted(file.name);
    }

    const uploadingJob = {
        jobId: null,
        filename: file.name,
        status: 'uploading',
        progress: 5,
        message: 'Envoi du fichier…',
        startedAt: new Date().toISOString(),
    };
    setActiveOcrJob(uploadingJob);
    updateOcrProgressFab(uploadingJob);

    const port = getOcrSharedWorker();
    if (port) {
        const buffer = await file.arrayBuffer();
        port.postMessage(
            {
                type: 'start',
                token,
                tokenType,
                filename: file.name,
                mime: file.type || 'application/octet-stream',
                fileBuffer: buffer,
            },
            [buffer]
        );
        return { async: true, file: file.name, via: 'shared-worker' };
    }

    // Sans SharedWorker
    try {
        const headers = getAuthHeaders();
        delete headers['Content-Type'];
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/extract-all', {
            method: 'POST',
            headers,
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Erreur HTTP: ${response.status}`);
        }

        const data = await response.json();
        if (!data.job_id) throw new Error('job_id manquant');
        startOcrJobPolling(data.job_id, data.file || file.name);
        return data;
    } catch (err) {
        const msg = String(err && err.message || err);
        if (/failed to fetch|networkerror|aborted|load failed/i.test(msg)) {
            // Navigation pendant l'upload : le serveur a peut-être quand même reçu le fichier
            await new Promise((r) => setTimeout(r, 800));
            const recovered = await recoverOcrJobFromServer(file.name);
            if (recovered) {
                return { async: true, file: file.name, via: 'recover' };
            }
        }
        setActiveOcrJob(null);
        hideOcrProgressFab();
        throw err;
    }
}

let _ocrFabHideTimer = null;
let _ocrFabEtaTimer = null;
let _ocrFabAnimRaf = null;
let _ocrFabDisplayProgress = 0;
let _ocrFabTargetProgress = 0;
let _ocrFabJobMeta = null;
const OCR_FAB_RING = 157; // 2 * π * 25

function _mergeOcrProgress(prev, next, status) {
    const a = Number(prev != null ? prev : 0);
    const b = Number(next != null ? next : 0);
    if (status === 'completed') return 100;
    if (!Number.isFinite(b)) return Number.isFinite(a) ? a : 0;
    if (!Number.isFinite(a)) return b;
    // Ne jamais reculer pendant un job en cours
    return Math.max(a, b);
}

function estimateOcrEtaSeconds(job, displayProgress) {
    if (!job) return null;
    const progress = Math.max(0, Math.min(100, Number(displayProgress != null ? displayProgress : job.progress) || 0));
    const startRaw = job.startedAt || job.created_at;
    if (!startRaw || progress < 8) return null;
    const startedMs = new Date(startRaw).getTime();
    if (!Number.isFinite(startedMs)) return null;
    const elapsed = (Date.now() - startedMs) / 1000;
    if (elapsed < 2) return null;
    return Math.max(0, Math.round((elapsed * (100 - progress)) / progress));
}

function formatOcrEta(seconds) {
    if (seconds == null) return 'Calcul…';
    if (seconds < 5) return '< 5 s';
    if (seconds < 60) return `~${seconds} s`;
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return s ? `~${m} min ${s} s` : `~${m} min`;
}

function stopOcrFabEtaTicker() {
    if (_ocrFabEtaTimer) {
        clearInterval(_ocrFabEtaTimer);
        _ocrFabEtaTimer = null;
    }
}

function applyOcrFabVisual(progress, job) {
    const root = document.getElementById('ocr-progress-fab');
    if (!root || !job) return;

    const pct = Math.max(0, Math.min(100, Math.round(progress)));
    const status = job.status || 'running';
    const done = status === 'completed';
    const failed = status === 'failed';

    root.classList.toggle('done', done);
    root.classList.toggle('failed', failed);
    root.classList.add('visible');

    const ring = document.getElementById('ocr-progress-fab-ring');
    const pctEl = document.getElementById('ocr-progress-fab-pct');
    const pctLabel = document.getElementById('ocr-progress-fab-pct-label');
    const bar = document.getElementById('ocr-progress-fab-bar');
    const title = document.getElementById('ocr-progress-fab-title');
    const msg = document.getElementById('ocr-progress-fab-msg');
    const etaEl = document.getElementById('ocr-progress-fab-eta');

    if (ring) {
        ring.style.strokeDashoffset = String(OCR_FAB_RING * (1 - progress / 100));
    }
    if (pctEl) pctEl.textContent = `${pct}%`;
    if (pctLabel) pctLabel.textContent = `${pct} %`;
    if (bar) bar.style.width = `${Math.max(0, Math.min(100, progress))}%`;
    if (title) title.textContent = job.filename || 'Extraction en cours';
    if (msg) {
        if (done) msg.textContent = 'Extraction terminée';
        else if (failed) msg.textContent = job.message || 'Échec de l\'extraction';
        else msg.textContent = job.message || 'Extraction en cours…';
    }
    if (etaEl) {
        if (done) etaEl.textContent = 'Terminé';
        else if (failed) etaEl.textContent = '—';
        else etaEl.textContent = formatOcrEta(estimateOcrEtaSeconds(job, progress));
    }
}

function startOcrFabAnim() {
    if (_ocrFabAnimRaf) return;

    const step = () => {
        const diff = _ocrFabTargetProgress - _ocrFabDisplayProgress;
        if (Math.abs(diff) < 0.25) {
            _ocrFabDisplayProgress = _ocrFabTargetProgress;
            if (_ocrFabJobMeta) applyOcrFabVisual(_ocrFabDisplayProgress, _ocrFabJobMeta);
            _ocrFabAnimRaf = null;
            return;
        }
        // Interpolation douce (plus rapide si écart grand)
        const speed = Math.abs(diff) > 20 ? 0.18 : 0.12;
        _ocrFabDisplayProgress += diff * speed + Math.sign(diff) * 0.08;
        if (_ocrFabJobMeta) applyOcrFabVisual(_ocrFabDisplayProgress, _ocrFabJobMeta);
        _ocrFabAnimRaf = requestAnimationFrame(step);
    };

    _ocrFabAnimRaf = requestAnimationFrame(step);
}

function startOcrFabEtaTicker() {
    if (_ocrFabEtaTimer) return;
    _ocrFabEtaTimer = setInterval(() => {
        const active = getActiveOcrJob();
        if (!active || active.status === 'completed' || active.status === 'failed') {
            stopOcrFabEtaTicker();
            return;
        }
        // Léger creep local si le serveur stagne un moment
        const target = Number(active.progress) || 0;
        if (_ocrFabDisplayProgress < Math.min(target + 4, 92) && active.status === 'running') {
            const soft = Math.min(_ocrFabTargetProgress + 0.6, Math.min(target + 4, 92));
            if (soft > _ocrFabTargetProgress) {
                _ocrFabTargetProgress = soft;
                startOcrFabAnim();
            }
        }
        if (_ocrFabJobMeta) {
            _ocrFabJobMeta = { ..._ocrFabJobMeta, ...active };
            applyOcrFabVisual(_ocrFabDisplayProgress, _ocrFabJobMeta);
        }
    }, 1000);
}

function hideOcrProgressFab(delayMs) {
    const root = document.getElementById('ocr-progress-fab');
    if (!root) return;
    clearTimeout(_ocrFabHideTimer);
    const hide = () => {
        root.classList.remove('visible', 'open', 'done', 'failed');
        stopOcrFabEtaTicker();
        if (_ocrFabAnimRaf) {
            cancelAnimationFrame(_ocrFabAnimRaf);
            _ocrFabAnimRaf = null;
        }
        _ocrFabDisplayProgress = 0;
        _ocrFabTargetProgress = 0;
        _ocrFabJobMeta = null;
    };
    if (delayMs && delayMs > 0) {
        _ocrFabHideTimer = setTimeout(hide, delayMs);
    } else {
        hide();
    }
}

function ensureOcrProgressFab() {
    if (!window.location.pathname.startsWith('/app')) return null;
    let root = document.getElementById('ocr-progress-fab');
    if (root) return root;

    const active = getActiveOcrJob();
    const initial = active && active.status !== 'completed' && active.status !== 'failed'
        ? Math.max(0, Math.min(100, Number(active.progress) || 0))
        : 0;
    _ocrFabDisplayProgress = initial;
    _ocrFabTargetProgress = initial;
    if (active && initial > 0) _ocrFabJobMeta = active;

    const offset = OCR_FAB_RING * (1 - initial / 100);
    root = document.createElement('div');
    root.id = 'ocr-progress-fab';
    root.className = 'ocr-progress-fab' + (initial > 0 ? ' visible' : '');
    root.innerHTML = `
        <div class="ocr-progress-fab-panel" id="ocr-progress-fab-panel">
            <p class="ocr-progress-fab-title" id="ocr-progress-fab-title">${(active && active.filename) || 'Extraction'}</p>
            <p class="ocr-progress-fab-msg" id="ocr-progress-fab-msg">${(active && active.message) || 'En cours…'}</p>
            <div class="ocr-progress-fab-bar"><span id="ocr-progress-fab-bar" style="width:${initial}%"></span></div>
            <div class="ocr-progress-fab-meta">
                <span>Progression <strong id="ocr-progress-fab-pct-label">${Math.round(initial)} %</strong></span>
                <span>Restant <strong id="ocr-progress-fab-eta">Calcul…</strong></span>
            </div>
            <a class="ocr-progress-fab-link" href="/app/ocr">Voir l'extraction</a>
        </div>
        <button type="button" class="ocr-progress-fab-btn" id="ocr-progress-fab-btn" title="Progression de l'extraction" aria-label="Progression de l'extraction">
            <svg class="ring" viewBox="0 0 64 64" aria-hidden="true">
                <circle class="ring-bg" cx="32" cy="32" r="25"></circle>
                <circle class="ring-fg" id="ocr-progress-fab-ring" cx="32" cy="32" r="25" style="stroke-dashoffset:${offset}"></circle>
            </svg>
            <span class="ocr-progress-fab-pct" id="ocr-progress-fab-pct">${Math.round(initial)}%</span>
        </button>
    `;
    document.body.appendChild(root);

    const btn = document.getElementById('ocr-progress-fab-btn');
    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        root.classList.toggle('open');
    });
    document.addEventListener('click', (e) => {
        if (!root.contains(e.target)) root.classList.remove('open');
    });

    window.addEventListener('ocr-job-progress', (e) => {
        if (e && e.detail) updateOcrProgressFab(e.detail);
    });

    return root;
}

function updateOcrProgressFab(job, options) {
    if (!job) return;
    const root = ensureOcrProgressFab();
    if (!root) return;

    clearTimeout(_ocrFabHideTimer);

    const status = job.status || 'running';
    const rawProgress = Math.max(0, Math.min(100, Number(job.progress) || 0));
    const progress = status === 'completed' ? 100 : rawProgress;
    const done = status === 'completed';
    const failed = status === 'failed';
    const active = status === 'uploading' || status === 'queued' || status === 'running';

    const prevJobId = _ocrFabJobMeta && (_ocrFabJobMeta.jobId || _ocrFabJobMeta.job_id);
    const newJobId = job.jobId || job.job_id;
    const isFreshUpload = status === 'uploading' && progress <= 10;
    const isNewJob = newJobId && prevJobId && String(newJobId) !== String(prevJobId) && progress < 20;

    _ocrFabJobMeta = { ...job, progress };

    if (isFreshUpload || isNewJob) {
        _ocrFabDisplayProgress = progress;
        _ocrFabTargetProgress = progress;
    } else if (done || failed) {
        _ocrFabTargetProgress = done ? 100 : Math.max(_ocrFabDisplayProgress, progress);
    } else if (progress + 0.5 >= _ocrFabTargetProgress || _ocrFabDisplayProgress < 1) {
        _ocrFabTargetProgress = Math.max(_ocrFabTargetProgress, progress);
    }

    // Au premier rendu d'une page, snap sans animation flash 0→N
    if (options && options.snap) {
        _ocrFabDisplayProgress = _ocrFabTargetProgress;
        applyOcrFabVisual(_ocrFabDisplayProgress, _ocrFabJobMeta);
    } else {
        startOcrFabAnim();
        applyOcrFabVisual(_ocrFabDisplayProgress, _ocrFabJobMeta);
    }

    if (active) startOcrFabEtaTicker();
    else if (!(options && options.quiet)) stopOcrFabEtaTicker();
}

function ensureNotificationCenter() {
    if (!window.location.pathname.startsWith('/app')) return;
    if (document.getElementById('app-notif-root')) {
        updateNotificationBadge();
        return;
    }

    const root = document.createElement('div');
    root.id = 'app-notif-root';
    root.className = 'app-notif-root';
    root.innerHTML = `
        <button type="button" class="app-notif-bell" id="app-notif-bell" title="Notifications" aria-label="Notifications">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
            </svg>
            <span class="app-notif-badge" id="app-notif-badge"></span>
        </button>
        <div class="app-notif-panel" id="app-notif-panel">
            <div class="app-notif-panel-header">
                <h4>Notifications</h4>
                <div style="display:flex;gap:10px;">
                    <button type="button" onclick="markAllNotificationsRead()">Tout lu</button>
                    <button type="button" onclick="clearAllNotifications()">Vider</button>
                </div>
            </div>
            <div class="app-notif-list" id="app-notif-list"></div>
        </div>
    `;
    document.body.appendChild(root);

    const bell = document.getElementById('app-notif-bell');
    const panel = document.getElementById('app-notif-panel');
    bell.addEventListener('click', (e) => {
        e.stopPropagation();
        panel.classList.toggle('open');
        if (panel.classList.contains('open')) renderNotificationPanel();
    });
    document.addEventListener('click', (e) => {
        if (!root.contains(e.target)) panel.classList.remove('open');
    });

    updateNotificationBadge();
    renderNotificationPanel();
}

document.addEventListener('DOMContentLoaded', function() {
    initializeAuth();
    ensureNotificationCenter();
    ensureOcrProgressFab();
    const activeJob = getActiveOcrJob();
    if (activeJob && activeJob.status !== 'completed' && activeJob.status !== 'failed') {
        updateOcrProgressFab(activeJob, { snap: true });
    }
    resumeActiveOcrJobPolling();
});

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
