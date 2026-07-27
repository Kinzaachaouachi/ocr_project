

function initializeBenchmarkMenu() {
    
    const localMenu = document.getElementById('benchmarkMenu');
    const localSubmenu = document.getElementById('benchmarkSubmenu');

    if (localMenu && localSubmenu) {
        localMenu.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            localSubmenu.classList.toggle('show');
            localMenu.classList.toggle('active');
            
            const olmSubmenu = document.getElementById('olmSubmenu');
            const olmMenu = document.getElementById('olmMenu');
            if (olmSubmenu) olmSubmenu.classList.remove('show');
            if (olmMenu) olmMenu.classList.remove('active');
        });
    }

    
    const olmMenu = document.getElementById('olmMenu');
    const olmSubmenu = document.getElementById('olmSubmenu');

    if (olmMenu && olmSubmenu) {
        olmMenu.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            olmSubmenu.classList.toggle('show');
            olmMenu.classList.toggle('active');
            
            if (localSubmenu) localSubmenu.classList.remove('show');
            if (localMenu) localMenu.classList.remove('active');
        });
    }

    
    document.addEventListener('click', (e) => {
        if (localMenu && localSubmenu && !localMenu.contains(e.target) && !localSubmenu.contains(e.target)) {
            localSubmenu.classList.remove('show');
            localMenu.classList.remove('active');
        }
        if (olmMenu && olmSubmenu && !olmMenu.contains(e.target) && !olmSubmenu.contains(e.target)) {
            olmSubmenu.classList.remove('show');
            olmMenu.classList.remove('active');
        }
    });
}

async function downloadBenchmark(event, format) {
    event.preventDefault();
    event.stopPropagation();

    const formatNames = {
        'pdf': 'PDF',
        'docx': 'Word',
        'excel': 'Excel',
        'csv': 'CSV'
    };

    try {
        showInfo(`⏳ Génération du rapport local ${formatNames[format]}...`);

        const token = localStorage.getItem('token');
        if (!token) {
            showError('❌ Vous devez être connecté pour télécharger un rapport.');
            return;
        }

        const response = await fetch(`/api/local-benchmark/download/${format}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Erreur lors du téléchargement ${formatNames[format]}`);
        }

        
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `benchmark_local.${format === 'docx' ? 'docx' : format === 'excel' ? 'xlsx' : format}`;
        if (contentDisposition) {
            const match = contentDisposition.match(/filename="(.+)"/);
            if (match) filename = match[1];
        }

        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showSuccess(`✅ Rapport local ${formatNames[format]} téléchargé avec succès!`);

        
        closeAllSubmenus();

    } catch (error) {
        console.error('Erreur téléchargement local:', error);
        showError(`❌ ${error.message}`);
    }
}

async function downloadOlmReport(event, format) {
    event.preventDefault();
    event.stopPropagation();

    const formatNames = {
        'pdf': 'PDF',
        'docx': 'Word',
        'excel': 'Excel',
        'csv': 'CSV'
    };

    try {
        showInfo(`⏳ Génération du rapport OLM Global ${formatNames[format]}...`);

        const token = localStorage.getItem('token');
        if (!token) {
            showError('❌ Vous devez être connecté pour télécharger un rapport.');
            return;
        }

        const response = await fetch(`/api/olm-report/download/${format}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Erreur lors du téléchargement OLM ${formatNames[format]}`);
        }

        
        const contentDisposition = response.headers.get('Content-Disposition');
        const extMap = { 'pdf': 'pdf', 'docx': 'docx', 'excel': 'xlsx', 'csv': 'csv' };
        let filename = `rapport_olm_benchmark.${extMap[format] || format}`;
        if (contentDisposition) {
            const match = contentDisposition.match(/filename="(.+)"/);
            if (match) filename = match[1];
        }

        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showSuccess(`✅ Rapport OLM Global ${formatNames[format]} téléchargé avec succès!`);

        
        closeAllSubmenus();

    } catch (error) {
        console.error('Erreur téléchargement OLM:', error);
        showError(`❌ ${error.message}`);
    }
}

function closeAllSubmenus() {
    const submenus = document.querySelectorAll('.submenu');
    const menuItems = document.querySelectorAll('.benchmark-menu');
    submenus.forEach(s => s.classList.remove('show'));
    menuItems.forEach(m => m.classList.remove('active'));
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeBenchmarkMenu);
} else {
    initializeBenchmarkMenu();
}
