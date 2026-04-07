// Variables globales
let myFiles = [];
let sharedFiles = [];

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    initNavigation();
    initSearch();
    initFileUpload();
    initXmlGeneration();
    
    loadMyFiles();
    loadSharedFiles();
    loadUserStats();
    
    document.getElementById('refreshData')?.addEventListener('click', function() {
        loadMyFiles();
        loadSharedFiles();
        showMessage('Données actualisées', 'success');
    });
});

// Navigation
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const tabs = document.querySelectorAll('.tab-content');
    const pageTitle = document.getElementById('pageTitle');
    const pageSubtitle = document.getElementById('pageSubtitle');
    
    const titles = {
        dashboard: { title: 'Tableau de bord', subtitle: 'Vue d\'ensemble de vos fichiers' },
        myfiles: { title: 'Mes fichiers', subtitle: 'Gérez vos documents personnels' },
        shared: { title: 'Fichiers partagés', subtitle: 'Fichiers partagés avec vous' },
        xml: { title: 'Générer XML', subtitle: 'Exportez vos données au format XML' }
    };
    
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = item.getAttribute('data-tab');
            
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            tabs.forEach(tab => tab.classList.remove('active'));
            document.getElementById(`${tabId}Tab`).classList.add('active');
            
            if (titles[tabId]) {
                pageTitle.textContent = titles[tabId].title;
                pageSubtitle.textContent = titles[tabId].subtitle;
            }
        });
    });
}

// Recherche
function initSearch() {
    const searchInput = document.getElementById('globalSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const activeTab = document.querySelector('.tab-content.active');
            const fileCards = activeTab.querySelectorAll('.file-card');
            
            fileCards.forEach(card => {
                const fileName = card.querySelector('h4')?.textContent.toLowerCase() || '';
                const fileDesc = card.querySelector('.file-description')?.textContent.toLowerCase() || '';
                card.style.display = (fileName.includes(searchTerm) || fileDesc.includes(searchTerm)) ? 'block' : 'none';
            });
        });
    }
}

// Charger mes fichiers
async function loadMyFiles() {
    const filesGrid = document.getElementById('myFilesGrid');
    if (!filesGrid) return;
    
    try {
        const response = await fetch('/api/my-files/');
        const files = await response.json();
        myFiles = files;
        
        if (!files || files.length === 0) {
            filesGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-folder-open"></i>
                    <h3>Aucun fichier</h3>
                    <p>Vous n'avez pas encore de fichiers.</p>
                    <button class="btn-primary" onclick="document.getElementById('uploadFileBtn').click()" style="margin-top: 15px;">
                        <i class="fas fa-upload"></i> Uploader un fichier
                    </button>
                </div>
            `;
            return;
        }
        
        filesGrid.innerHTML = files.map(file => `
            <div class="file-card">
                <div class="file-icon ${getFileIconClass(file.name)}">
                    <i class="${getFileIcon(file.name)}"></i>
                </div>
                <h4>${escapeHtml(file.name)}</h4>
                <div class="file-description">${escapeHtml(file.description || 'Aucune description')}</div>
                <div class="file-meta">
                    <span><i class="fas fa-calendar"></i> ${formatDate(file.created_at)}</span>
                    <span><i class="fas fa-database"></i> ${file.size || 'N/A'}</span>
                </div>
                <div class="file-actions">
                    <button onclick="downloadFile(${file.id})" class="btn-secondary">
                        <i class="fas fa-download"></i> Télécharger
                    </button>
                    <button onclick="deleteFile(${file.id})" class="btn-danger">
                        <i class="fas fa-trash"></i> Supprimer
                    </button>
                </div>
            </div>
        `).join('');
        
        updateUserStats();
        
    } catch (error) {
        console.error('Erreur:', error);
        filesGrid.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><h3>Erreur de chargement</h3></div>';
    }
}

// Charger fichiers partagés
async function loadSharedFiles() {
    const filesGrid = document.getElementById('sharedFilesGrid');
    if (!filesGrid) return;
    
    try {
        const response = await fetch('/api/shared-files/');
        const files = await response.json();
        sharedFiles = files;
        
        if (!files || files.length === 0) {
            filesGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-share-alt"></i>
                    <h3>Aucun fichier partagé</h3>
                    <p>Aucun fichier n'a été partagé avec vous.</p>
                </div>
            `;
            return;
        }
        
        filesGrid.innerHTML = files.map(file => `
            <div class="file-card">
                <div class="file-icon ${getFileIconClass(file.name)}">
                    <i class="${getFileIcon(file.name)}"></i>
                </div>
                <h4>${escapeHtml(file.name)}</h4>
                <div class="file-description">${escapeHtml(file.description || 'Aucune description')}</div>
                <div class="file-meta">
                    <span><i class="fas fa-user"></i> ${escapeHtml(file.owner_name)}</span>
                    <span><i class="fas fa-calendar"></i> ${formatDate(file.created_at)}</span>
                </div>
                <div class="file-actions">
                    <button onclick="downloadFile(${file.id})" class="btn-primary">
                        <i class="fas fa-download"></i> Télécharger
                    </button>
                </div>
            </div>
        `).join('');
        
        document.getElementById('sharedFilesCount').textContent = files.length;
        
    } catch (error) {
        console.error('Erreur:', error);
        filesGrid.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><h3>Erreur de chargement</h3></div>';
    }
}

// Charger statistiques utilisateur
async function loadUserStats() {
    try {
        const files = await fetch('/api/my-files/').then(r => r.json());
        let totalSize = 0;
        files.forEach(file => {
            if (file.size) totalSize += parseFloat(file.size);
        });
        
        document.getElementById('myFilesCount').textContent = files.length;
        document.getElementById('myFilesSize').textContent = formatFileSize(totalSize);
        
    } catch (error) {
        console.error('Erreur:', error);
    }
}

function updateUserStats() {
    let totalSize = 0;
    myFiles.forEach(file => {
        if (file.size) totalSize += parseFloat(file.size);
    });
    document.getElementById('myFilesCount').textContent = myFiles.length;
    document.getElementById('myFilesSize').textContent = formatFileSize(totalSize);
}

// Upload de fichiers
function initFileUpload() {
    const uploadBtn = document.getElementById('uploadFileBtn');
    const modal = document.getElementById('uploadModal');
    const closeBtn = document.querySelector('#uploadModal .close');
    const uploadForm = document.getElementById('uploadForm');
    
    if (uploadBtn) {
        uploadBtn.addEventListener('click', () => {
            loadUsersForSharing();
            modal.style.display = 'block';
        });
    }
    
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    window.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const fileInput = document.getElementById('fileInput');
            if (!fileInput.files[0]) {
                showMessage('Veuillez sélectionner un fichier', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('name', document.getElementById('fileName').value);
            formData.append('description', document.getElementById('fileDescription').value);
            formData.append('file', fileInput.files[0]);
            
            const shareWith = document.getElementById('shareWith');
            if (shareWith) {
                const selectedUsers = Array.from(shareWith.selectedOptions).map(opt => opt.value).filter(v => v);
                formData.append('shared_with', JSON.stringify(selectedUsers));
            }
            
            try {
                const response = await fetch('/api/upload-file/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCookie('csrftoken') },
                    body: formData
                });
                
                if (response.ok) {
                    showMessage('Fichier uploadé avec succès!', 'success');
                    modal.style.display = 'none';
                    uploadForm.reset();
                    loadMyFiles();
                } else {
                    throw new Error('Erreur lors de l\'upload');
                }
            } catch (error) {
                showMessage('Erreur: ' + error.message, 'error');
            }
        });
    }
}

// Génération XML
function initXmlGeneration() {
    const generateBtn = document.getElementById('generateXmlBtn');
    if (!generateBtn) return;
    
    generateBtn.addEventListener('click', async () => {
        const xmlType = document.getElementById('xmlType').value;
        const filter = document.getElementById('xmlFilter').value;
        const preview = document.getElementById('xmlPreview');
        
        preview.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Génération en cours...';
        
        try {
            const response = await fetch(`/api/generate-xml/?type=${xmlType}&filter=${encodeURIComponent(filter)}`);
            const xml = await response.text();
            
            preview.textContent = xml;
            
            const blob = new Blob([xml], { type: 'application/xml' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${xmlType}_export_${new Date().toISOString().slice(0,19).replace(/:/g, '-')}.xml`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showMessage('XML généré avec succès!', 'success');
        } catch (error) {
            console.error('Erreur:', error);
            preview.innerHTML = '<span style="color: #dc3545;">❌ Erreur lors de la génération</span>';
            showMessage('Erreur de génération XML', 'error');
        }
    });
}

async function loadUsersForSharing() {
    const shareSelect = document.getElementById('shareWith');
    if (!shareSelect) return;
    
    try {
        const response = await fetch('/api/users/');
        const users = await response.json();
        
        const currentUserId = document.querySelector('.user-info')?.getAttribute('data-user-id') || 0;
        shareSelect.innerHTML = users
            .filter(u => u.id != currentUserId)
            .map(user => `<option value="${user.id}">${escapeHtml(user.fullname)} (${escapeHtml(user.email)})</option>`)
            .join('');
            
        if (shareSelect.options.length === 0) {
            shareSelect.innerHTML = '<option value="">Aucun autre utilisateur</option>';
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

function downloadFile(fileId) {
    window.location.href = `/api/download-file/${fileId}/`;
}

async function deleteFile(fileId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce fichier ?')) return;
    
    try {
        const response = await fetch(`/api/delete-file/${fileId}/`, {
            method: 'DELETE',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        
        if (response.ok) {
            showMessage('Fichier supprimé avec succès', 'success');
            loadMyFiles();
        } else {
            throw new Error('Erreur de suppression');
        }
    } catch (error) {
        showMessage('Erreur: ' + error.message, 'error');
    }
}