// OCR Multi-Model Interface - Main JavaScript

const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const loadingOverlay = document.getElementById('loadingOverlay');
const resultsContainer = document.getElementById('resultsContainer');
const languageInfo = document.getElementById('languageInfo');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const fileIcon = document.getElementById('fileIcon');
const removeFileBtn = document.getElementById('removeFileBtn');

let currentFile = null;
let selectedModelIndex = null;

// Single click handler on uploadZone that triggers fileInput.click()
uploadZone.addEventListener('click', function(e) {
    if (e.target !== fileInput) {
        fileInput.click();
    }
});

fileInput.addEventListener('click', function(e) {
    e.stopPropagation();
});

// Handle drag and drop
uploadZone.addEventListener('dragenter', function(e) {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragover', function(e) {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', function(e) {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', function(e) {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        handleFileSelection(e.dataTransfer.files[0]);
    }
});

// Handle file input change
fileInput.addEventListener('change', function(e) {
    if (e.target.files.length > 0) {
        handleFileSelection(e.target.files[0]);
    }
    // Reset input so same file can be selected again
    fileInput.value = '';
});

removeFileBtn.addEventListener('click', () => {
    currentFile = null;
    fileInfo.style.display = 'none';
    resultsContainer.innerHTML = '';
    languageInfo.innerHTML = '';
    uploadZone.style.display = 'block';
    // Cacher la prévisualisation
    const previewWrap = document.getElementById('filePreviewWrap');
    if (previewWrap) previewWrap.style.display = 'none';
});


// Utility Functions
function getFileIcon(filename) {
    const ext = filename.toLowerCase().split('.').pop();
    const icons = {
        'png': '🖼️', 'jpg': '🖼️', 'jpeg': '🖼️', 'bmp': '🖼️', 'tiff': '🖼️', 'webp': '🖼️',
        'pdf': '📕', 'txt': '📄', 'docx': '📘', 'doc': '📘', 'xlsx': '📗', 'xls': '📗'
    };
    return icons[ext] || '📄';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getTextDirection(languageCode) {
    return ['ar', 'he', 'fa', 'ur'].includes(languageCode) ? 'rtl' : 'ltr';
}

function getLanguageName(languageCode) {
    const names = {
        fr: 'Français',
        en: 'English',
        de: 'Deutsch',
        es: 'Español',
        it: 'Italiano',
        pt: 'Português',
        ar: 'العربية',
        zh: '中文',
        ja: '日本語',
        ko: '한국어',
        ru: 'Русский',
        tr: 'Türkçe',
        nl: 'Nederlands',
        pl: 'Polski',
        vi: 'Tiếng Việt',
        th: 'ไทย',
        he: 'עברית',
        hi: 'हिन्दी'
    };
    return names[languageCode] || (languageCode || 'und').toUpperCase();
}

function getLanguageFontFamily(languageCode) {
    return ['ar', 'he', 'fa', 'ur'].includes(languageCode)
        ? '"Segoe UI", "Noto Sans Arabic", "Tahoma", sans-serif'
        : '"Segoe UI", system-ui, sans-serif';
}

function detectLanguageFromTextClient(text) {
    if (!text || text.length < 10) return null;
    const sample = text.slice(0, 500);

    if(/[\u0600-\u06FF]/.test(sample)) return { code: 'ar', name: 'العربية', confidence: 0.9 };
    if(/[\u0590-\u05FF]/.test(sample)) return { code: 'he', name: 'עברית', confidence: 0.9 };
    if(/[\u0400-\u04FF]/.test(sample)) return { code: 'ru', name: 'Русский', confidence: 0.85 };
    if(/[\u4E00-\u9FFF]/.test(sample)) return { code: 'zh', name: '中文', confidence: 0.9 };
    if(/[\u3040-\u309F\u30A0-\u30FF]/.test(sample)) return { code: 'ja', name: '日本語', confidence: 0.85 };
    if(/[\uAC00-\uD7AF]/.test(sample)) return { code: 'ko', name: '한국어', confidence: 0.9 };
    if(/[\u0E00-\u0E7F]/.test(sample)) return { code: 'th', name: 'ไทย', confidence: 0.9 };

    return null;
}

function resolveDetectedLanguage(data) {
    if (data?.detected_language?.code) {
        return {
            code: data.detected_language.code,
            name: data.detected_language.name || getLanguageName(data.detected_language.code),
            confidence: data.detected_language.confidence || 0.5
        };
    }

    const firstTextResult = (data?.results || []).find(result => result?.status === 'success' && result?.text);
    if (firstTextResult?.text) {
        return detectLanguageFromTextClient(firstTextResult.text);
    }

    return null;
}

function renderLanguageInfo(language) {
    if (!language || !language.code) {
        languageInfo.innerHTML = '';
        return;
    }

    const direction = getTextDirection(language.code);
    const confidence = language.confidence != null ? `${Math.round(language.confidence * 100)}%` : 'n/d';

    languageInfo.innerHTML = `
        <div class="language-badge" style="direction:${direction}; text-align:${direction === 'rtl' ? 'right' : 'left'};">
            🌍 Langue détectée : <strong>${language.name || getLanguageName(language.code)}</strong>
            (${language.code.toUpperCase()}) · Confiance : <strong>${confidence}</strong>
        </div>
    `;
}

function applyDocumentLanguage(language) {
    const code = language?.code || 'und';
    const direction = getTextDirection(code);
    document.documentElement.lang = code;
    document.documentElement.dir = direction;
    document.body.style.direction = direction;
}

// File Handling
function handleFileSelection(file) {
    currentFile = file;

    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    fileIcon.textContent = getFileIcon(file.name);

    // ── Prévisualisation du fichier ──
    const previewWrap = document.getElementById('filePreviewWrap');
    const previewImg  = document.getElementById('filePreviewImg');
    const ext = file.name.toLowerCase().split('.').pop();
    const isImage = ['png','jpg','jpeg','bmp','tiff','webp'].includes(ext);

    if (isImage) {
        const url = URL.createObjectURL(file);
        previewImg.src = url;
        previewImg.onload = () => URL.revokeObjectURL(url); // libérer mémoire
        previewWrap.style.display = 'block';
    } else {
        previewWrap.style.display = 'none';
    }

    uploadZone.style.display = 'none';
    fileInfo.style.display = 'flex';
    resultsContainer.innerHTML = '';
    languageInfo.innerHTML = '';

    performExtraction(file);
}

// OCR Extraction
async function performExtraction(file) {
    loadingOverlay.classList.add('show');
    resultsContainer.innerHTML = '';
    languageInfo.innerHTML = '';

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/extract-all', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur lors de l\extraction');
        }

        const data = await response.json();
        displayResults(data);
        loadingOverlay.classList.remove('show');

    } catch (error) {
        loadingOverlay.classList.remove('show');
        resultsContainer.innerHTML = `<div class="error-message">❌ ${error.message}</div>`;
    }
}

// Display Results
function displayResults(data) {
    const detectedLanguage = resolveDetectedLanguage(data);
    renderLanguageInfo(detectedLanguage);
    applyDocumentLanguage(detectedLanguage);

    resultsContainer.innerHTML = `
        <div class="confidence-legend">
            <strong>Légende de confiance:</strong>
            <div class="legend-item">
                <div class="legend-dot" style="background: #0F172A;"></div>
                <span>Haute confiance (≥85%)</span>
            </div>
            <div class="legend-item">
                <div class="legend-dot" style="background: #F59E0B;"></div>
                <span>Confiance moyenne (60-84%)</span>
            </div>
            <div class="legend-item">
                <div class="legend-dot" style="background: #DC2626;"></div>
                <span>Faible confiance (<60%)</span>
            </div>
        </div>
        <div class="results-grid" id="resultsGrid"></div>
    `;

    const grid = document.getElementById('resultsGrid');
    const results = data.results || [];
    const bestModelId = data.best_model;

    results.forEach((result, index) => {
        if (result.status !== 'success') {
            grid.innerHTML += createErrorCard(result);
            return;
        }

        const isBest = result.model_id === bestModelId;
        const card = createResultCard(result, isBest, index, detectedLanguage);
        grid.innerHTML += card;
    });

    setTimeout(activateButtons, 100);
    setTimeout(setupTextObserver, 200);
}

// Create Result Card
function createResultCard(result, isBest, index, detectedLanguage) {
    const coloredText = colorizeText(result.text, result.word_confidence || []);
    const textDirection = getTextDirection(detectedLanguage?.code || 'und');
    const textAlignment = textDirection === 'rtl' ? 'right' : 'left';
    const fontFamily = getLanguageFontFamily(detectedLanguage?.code || 'und');
    
    return `
        <div class="result-card ${isBest ? 'best' : ''}" id="card-${index}">
            <div class="result-header">
                <div class="result-title">
                    ${result.model_name}
                    ${isBest ? '<span class="best-badge">🏆 Meilleur</span>' : ''}
                </div>
                <div class="score-badge">Score: ${result.quality_score}</div>
            </div>
            <div class="result-body">
                <div class="text-display" id="text-${index}" data-model="${result.model_id}" style="direction:${textDirection}; text-align:${textAlignment}; font-family:${fontFamily};">
                    ${coloredText}
                </div>
                <div class="result-meta">
                    <div class="meta-item">
                        <div class="meta-label">Caractères</div>
                        <div class="meta-value">${result.char_count}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Mots</div>
                        <div class="meta-value">${result.word_count}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Temps</div>
                        <div class="meta-value">${result.timing.ocr_time_s.toFixed(2)}s</div>
                    </div>
                </div>
                <div class="action-row">
                    <div class="result-actions">
                        <button class="action-btn copy-btn" data-index="${index}" title="Copier">📋</button>
                        <button class="action-btn edit-btn" data-index="${index}" title="Éditer">✏️</button>
                        <button class="action-btn save-btn" data-index="${index}" title="Sauvegarder">💾</button>
                    </div>
                    <div class="translate-row">
                    <select class="translate-select" id="translate-select-${index}" aria-label="Choisir la langue de traduction">
                        <option value="en">English</option>
                        <option value="fr">Français</option>
                        <option value="es">Español</option>
                        <option value="de">Deutsch</option>
                        <option value="it">Italiano</option>
                        <option value="pt">Português</option>
                        <option value="ar">العربية</option>
                        <option value="zh">中文</option>
                        <option value="ru">Русский</option>
                        <option value="ko">한국어</option>
                        <option value="ja">日本語</option>
                        <option value="tr">Türkçe</option>
                        <option value="nl">Nederlands</option>
                        <option value="pl">Polski</option>
                        <option value="vi">Tiếng Việt</option>
                    </select>
                    <button class="action-btn translate-btn" data-index="${index}" title="Traduire">🌐</button>
                </div>
                <div class="translation-panel" id="translation-panel-${index}" style="display:none; margin-top: 1rem; padding: 1rem; background: #f8fafc; border-radius: 10px; border: 1px solid #e2e8f0;">
                    <div class="translation-title" style="font-weight:600; margin-bottom:0.5rem;">Traduction :</div>
                    <div class="translation-text" id="translation-text-${index}" style="white-space: pre-wrap; color: #0f172a;"></div>
                </div>
            </div>
        </div>
    `;
}

function createErrorCard(result) {
    return `
        <div class="result-card">
            <div class="result-header">
                <div class="result-title">${result.model_name}</div>
                <div class="score-badge" style="background: rgba(220, 38, 38, 0.1); color: #DC2626;">Erreur</div>
            </div>
            <div class="result-body">
                <div class="error-message">❌ ${result.error || 'Erreur inconnue'}</div>
            </div>
        </div>
    `;
}

// Text Colorization
function colorizeText(text, wordConfidence) {
    if (!wordConfidence || wordConfidence.length === 0) {
        return escapeHtml(text);
    }

    const words = text.split(/(\s+)/);
    let confIndex = 0;
    
    return words.map(word => {
        if (!word.trim()) return word;
        
        const conf = wordConfidence[confIndex];
        confIndex++;
        
        if (!conf) return escapeHtml(word);
        
        const confidence = conf.confidence;
        let colorClass = 'word-high';
        if (confidence < 0.60) colorClass = 'word-low';
        else if (confidence < 0.85) colorClass = 'word-medium';
        
        return `<span class="${colorClass}" data-original="${escapeHtml(word)}" title="Confiance: ${(confidence * 100).toFixed(0)}%">${escapeHtml(word)}</span>`;
    }).join('');
}

// Setup Text Observer (détecte les modifications et change la couleur)
function setupTextObserver() {
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'characterData' || mutation.type === 'childList') {
                const target = mutation.target;
                let span = target.nodeType === Node.TEXT_NODE ? target.parentElement : target;
                
                if (span && span.classList && (span.classList.contains('word-medium') || span.classList.contains('word-low'))) {
                    const originalText = span.dataset.original || '';
                    const currentText = span.textContent || '';
                    
                    // Si le texte a été modifié, changer la couleur en noir
                    if (originalText !== currentText) {
                        span.classList.remove('word-medium', 'word-low');
                        span.classList.add('word-high');
                        span.style.color = '#0F172A';
                        span.title = 'Confiance: 100% (corrigé manuellement)';
                    }
                }
            }
        });
    });
    
    document.querySelectorAll('.text-display').forEach(textDiv => {
        observer.observe(textDiv, {
            characterData: true,
            childList: true,
            subtree: true
        });
    });
}

// Activate Buttons
function activateButtons() {

    // Bouton Copier
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const index = e.target.closest('.action-btn').dataset.index;
            const textDiv = document.getElementById(`text-${index}`);
            const text = textDiv.innerText;
            
            navigator.clipboard.writeText(text).then(() => {
                btn.textContent = '✓';
                setTimeout(() => { btn.textContent = '📋'; }, 1500);
            });
        });
    });

    // Bouton Éditer
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const index = e.target.closest('.action-btn').dataset.index;
            const textDiv = document.getElementById(`text-${index}`);
            const isEditing = textDiv.contentEditable === 'true';
            
            if (isEditing) {
                textDiv.contentEditable = 'false';
                btn.classList.remove('edit-active');
                btn.textContent = '✏️';
            } else {
                textDiv.contentEditable = 'true';
                textDiv.focus();
                btn.classList.add('edit-active');
                btn.textContent = '✓';
            }
        });
    });

    // Bouton Sauvegarder
    document.querySelectorAll('.save-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const index = e.target.closest('.action-btn').dataset.index;
            const textDiv = document.getElementById(`text-${index}`);
            const text = textDiv.innerText;
            const modelId = textDiv.dataset.model;
            
            const blob = new Blob([text], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `extraction_${modelId}_${Date.now()}.txt`;
            a.click();
            URL.revokeObjectURL(url);
            
            btn.textContent = '✓';
            setTimeout(() => { btn.textContent = '💾'; }, 1500);
        });
    });

    // Boutons Traduire
    document.querySelectorAll('.translate-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const index = e.target.closest('.action-btn').dataset.index;
            const textDiv = document.getElementById(`text-${index}`);
            const targetLang = document.getElementById(`translate-select-${index}`).value;
            const translatePanel = document.getElementById(`translation-panel-${index}`);
            const translationText = document.getElementById(`translation-text-${index}`);

            const originalText = textDiv.innerText.trim();
            if (!originalText) {
                translationText.textContent = 'Aucun texte à traduire.';
                translatePanel.style.display = 'block';
                return;
            }

            btn.textContent = '⏳';
            btn.disabled = true;
            translationText.textContent = 'Traduction en cours...';
            translatePanel.style.display = 'block';

            try {
                const formData = new FormData();
                formData.append('text', originalText);
                formData.append('target_lang', targetLang);
                formData.append('source_lang', 'auto');

                const response = await fetch('/translate', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Erreur de traduction');
                }

                const data = await response.json();
                translationText.textContent = data.translated_text || 'Aucune traduction disponible.';
            } catch (err) {
                translationText.textContent = `Erreur traduction: ${err.message}`;
            } finally {
                btn.textContent = '🌐';
                btn.disabled = false;
            }
        });
    });
}
