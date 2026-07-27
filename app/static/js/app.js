

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
    sessionStorage.removeItem('ocrKeepOnNextLoad');
    localStorage.removeItem('ocrExtractionState');
    localStorage.removeItem('ocrAppNotifications');
    localStorage.removeItem('ocrActiveJob');
    localStorage.removeItem('ocrNotifiedJobs');
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

/* ═══════════════════════════════════════════════════════════
   Centre de notifications (lié aux extractions OCR)
   ═══════════════════════════════════════════════════════════ */
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

/**
 * Ajoute une notification (centre + toast + option navigateur).
 * @param {{title:string, message:string, type?:string, link?:string, browser?:boolean, toast?:boolean}} opts
 */
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

/** Notification dédiée à la fin d'une extraction OCR */
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

/* ═══════════════════════════════════════════════════════════
   Jobs OCR asynchrones (SharedWorker — survit au changement de page)
   ═══════════════════════════════════════════════════════════ */
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
    if (jobId && _wasJobNotified(jobId)) {
        persistCompletedOcrResult(result);
        setActiveOcrJob(null);
        window.dispatchEvent(new CustomEvent('ocr-job-completed', { detail: result }));
        return;
    }
    if (jobId) _markJobNotified(jobId);
    stopOcrJobPolling();
    setActiveOcrJob(null);
    persistCompletedOcrResult(result);
    if (typeof notifyExtractionComplete === 'function') {
        notifyExtractionComplete(result);
    }
    window.dispatchEvent(new CustomEvent('ocr-job-completed', { detail: result }));
}

function _onOcrFailed(error, filename, jobId) {
    if (jobId && _wasJobNotified(jobId)) {
        setActiveOcrJob(null);
        return;
    }
    if (jobId) _markJobNotified(jobId);
    stopOcrJobPolling();
    setActiveOcrJob(null);
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
    setActiveOcrJob({
        ...active,
        jobId: job.job_id || job.jobId,
        filename: job.filename || active.filename,
        status: job.status,
        progress: job.progress,
        message: job.message,
    });

    const jobId = job.job_id || job.jobId;
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
    setActiveOcrJob({
        jobId,
        filename,
        status: 'queued',
        progress: 0,
        startedAt: new Date().toISOString(),
    });

    const tick = async () => {
        try {
            const job = await pollOcrJobOnce(jobId);
            if (job) handleOcrJobUpdate(job);
        } catch (e) {
            console.warn('OCR job poll error:', e);
        }
    };

    tick();
    _ocrJobPollTimer = setInterval(tick, 2000);
}

function _handleWorkerMessage(msg) {
    if (!msg || !msg.type) return;

    if (msg.type === 'job' && msg.job) {
        const j = msg.job;
        setActiveOcrJob({
            jobId: j.jobId,
            filename: j.filename,
            status: j.status,
            progress: j.progress,
            message: j.message,
        });
        window.dispatchEvent(new CustomEvent('ocr-job-progress', { detail: j }));
        return;
    }

    if (msg.type === 'completed' && msg.result) {
        const active = getActiveOcrJob();
        _onOcrCompleted(msg.result, active && active.jobId);
        return;
    }

    if (msg.type === 'failed') {
        const active = getActiveOcrJob();
        // Ne pas traiter "Failed to fetch" du worker comme échec définitif :
        // on tente une récupération serveur.
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
        _ocrSharedWorker = new SharedWorker('/static/js/ocr-job-worker.js?v=20260727h', {
            name: 'ocr-extraction-worker',
        });
        _ocrWorkerPort = _ocrSharedWorker.port;
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

/**
 * Démarre une extraction asynchrone via SharedWorker (survit à la navigation).
 */
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

    setActiveOcrJob({
        jobId: null,
        filename: file.name,
        status: 'uploading',
        progress: 5,
        message: 'Préparation…',
        startedAt: new Date().toISOString(),
    });

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

    // Fallback sans SharedWorker
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
        throw err;
    }
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
