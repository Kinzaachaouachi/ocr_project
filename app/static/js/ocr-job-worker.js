/* SharedWorker — garde l'upload + le polling OCR vivants entre les pages */
/* global self */

const ports = new Set();
let pollTimer = null;
let activeJob = null; // { jobId, filename, status, progress, message, startedAt }

function broadcast(msg) {
    ports.forEach((port) => {
        try {
            port.postMessage(msg);
        } catch (e) {
            ports.delete(port);
        }
    });
}

function stopPolling() {
    if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
    }
}

function mergeProgress(prev, next) {
    const a = Number(prev != null ? prev : 0);
    const b = Number(next != null ? next : 0);
    if (!Number.isFinite(b)) return a;
    if (!Number.isFinite(a)) return b;
    return Math.max(a, b);
}

async function pollOnce(jobId, token, tokenType) {
    const res = await fetch(`/api/extract-all/jobs/${jobId}`, {
        headers: { Authorization: `${tokenType} ${token}` },
    });
    if (!res.ok) {
        if (res.status === 404) {
            throw new Error('Job introuvable');
        }
        throw new Error(`HTTP ${res.status}`);
    }
    return res.json();
}

function startPolling(jobId, filename, token, tokenType) {
    stopPolling();
    const prev = activeJob && String(activeJob.jobId) === String(jobId) ? activeJob : null;
    activeJob = {
        jobId,
        filename: filename || (prev && prev.filename) || 'document',
        status: (prev && prev.status) || 'queued',
        progress: prev ? Number(prev.progress) || 0 : 0,
        message: (prev && prev.message) || 'Extraction démarrée…',
        startedAt: (prev && prev.startedAt) || new Date().toISOString(),
        created_at: prev && prev.created_at,
    };
    broadcast({ type: 'job', job: activeJob });

    const tick = async () => {
        try {
            const job = await pollOnce(jobId, token, tokenType);
            const prevProg = activeJob ? activeJob.progress : 0;
            activeJob = {
                jobId: job.job_id,
                filename: job.filename || filename,
                status: job.status,
                progress: mergeProgress(prevProg, job.progress),
                message: job.message || (activeJob && activeJob.message) || '',
                startedAt: (activeJob && activeJob.startedAt) || job.created_at,
                created_at: job.created_at,
            };
            broadcast({ type: 'job', job: activeJob });

            if (job.status === 'completed' && job.result) {
                stopPolling();
                activeJob = {
                    ...activeJob,
                    status: 'completed',
                    progress: 100,
                    message: 'Extraction terminée',
                };
                broadcast({ type: 'job', job: activeJob });
                activeJob = null;
                broadcast({ type: 'completed', result: job.result });
            } else if (job.status === 'failed') {
                stopPolling();
                const err = job.error || job.message || 'Échec extraction';
                activeJob = null;
                broadcast({ type: 'failed', error: err, filename });
            }
        } catch (e) {
            broadcast({
                type: 'job',
                job: {
                    ...(activeJob || { jobId, filename }),
                    message: 'Reconnexion au suivi…',
                },
            });
        }
    };

    tick();
    pollTimer = setInterval(tick, 1000);
}

self.onconnect = (e) => {
    const port = e.ports[0];
    ports.add(port);

    port.onmessage = async (ev) => {
        const msg = ev.data || {};

        if (msg.type === 'hello' || msg.type === 'subscribe') {
            if (activeJob) {
                port.postMessage({ type: 'job', job: activeJob });
            } else {
                port.postMessage({ type: 'idle' });
            }
            return;
        }

        if (msg.type === 'start') {
            const {
                token,
                tokenType = 'Bearer',
                filename,
                mime = 'application/octet-stream',
                fileBuffer,
            } = msg;

            if (!token || !fileBuffer) {
                port.postMessage({
                    type: 'failed',
                    error: 'Données manquantes pour démarrer l\'extraction',
                    filename,
                });
                return;
            }

            stopPolling();
            activeJob = {
                jobId: null,
                filename,
                status: 'uploading',
                progress: 5,
                message: 'Envoi du fichier au serveur…',
                startedAt: new Date().toISOString(),
            };
            broadcast({ type: 'job', job: activeJob });

            try {
                const blob = new Blob([fileBuffer], { type: mime });
                const formData = new FormData();
                formData.append('file', blob, filename || 'document');

                const res = await fetch('/api/extract-all', {
                    method: 'POST',
                    headers: { Authorization: `${tokenType} ${token}` },
                    body: formData,
                });

                if (!res.ok) {
                    const err = await res.json().catch(() => ({}));
                    throw new Error(err.detail || `Erreur HTTP ${res.status}`);
                }

                const data = await res.json();
                if (!data.job_id) {
                    throw new Error('job_id manquant dans la réponse serveur');
                }

                activeJob = {
                    jobId: data.job_id,
                    filename: data.file || filename,
                    status: 'queued',
                    progress: Math.max(8, Number(activeJob && activeJob.progress) || 8),
                    message: 'En file d\'attente…',
                    startedAt: (activeJob && activeJob.startedAt) || new Date().toISOString(),
                };
                broadcast({ type: 'job', job: activeJob });
                startPolling(data.job_id, data.file || filename, token, tokenType);
            } catch (err) {
                stopPolling();
                activeJob = null;
                broadcast({
                    type: 'failed',
                    error: err.message || String(err),
                    filename,
                });
            }
            return;
        }

        if (msg.type === 'resume') {
            const { jobId, filename, token, tokenType = 'Bearer' } = msg;
            if (jobId && token) {
                if (activeJob && String(activeJob.jobId) === String(jobId) && pollTimer) {
                    port.postMessage({ type: 'job', job: activeJob });
                    return;
                }
                startPolling(jobId, filename || 'document', token, tokenType);
            }
            return;
        }

        if (msg.type === 'stop') {
            stopPolling();
            activeJob = null;
            broadcast({ type: 'idle' });
        }
    };

    port.start();
    port.postMessage({ type: 'ready' });
};
