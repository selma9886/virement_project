// static/js/admin.js
// Ce fichier gère tout SAUF l'ajout d'utilisateur (qui est géré par le script inline dans le HTML)

document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin JS chargé - Gestion admin uniquement');
    
    // ========== GESTION DE LA NAVIGATION ==========
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        // Supprimer d'anciens écouteurs pour éviter les doublons
        const newItem = item.cloneNode(true);
        if (item.parentNode) {
            item.parentNode.replaceChild(newItem, item);
        }
        
        newItem.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            const tab = this.getAttribute('data-tab');
            
            console.log('Click sur nav-item:', { href: href, tab: tab });
            
            // Vérifier si c'est un lien vers une autre page (URL absolue ou relative complète)
            if (href && href !== '#' && href !== '' && !href.startsWith('#')) {
                console.log('Navigation vers:', href);
                // Laisser le navigateur naviguer normalement
                return true;
            }
            
            // Si c'est un lien avec data-tab (onglet interne)
            if (tab) {
                e.preventDefault();
                console.log('Changement d\'onglet:', tab);
                switchTab(tab);
                updateActiveNavItem(this);
                
                // Mettre à jour l'URL avec le hash
                window.location.hash = tab;
            }
        });
    });
    
    // ========== GESTION DES STATISTIQUES ==========
    function loadStats() {
        console.log('Chargement des statistiques...');
        fetch('/api/stats/')
            .then(response => response.json())
            .then(data => {
                const totalFiles = document.getElementById('totalFiles');
                const totalUsers = document.getElementById('totalUsers');
                const totalEmails = document.getElementById('totalEmails');
                const totalSize = document.getElementById('totalSize');
                
                if (totalFiles) totalFiles.innerText = data.total_files || 0;
                if (totalUsers) totalUsers.innerText = data.total_users || 0;
                if (totalEmails) totalEmails.innerText = data.total_emails || 0;
                if (totalSize) totalSize.innerText = data.total_size || '0 MB';
            })
            .catch(error => console.error('Erreur chargement stats:', error));
    }
    
    // ========== GESTION DES ACTIVITÉS RÉCENTES ==========
    function loadRecentActivities() {
        console.log('Chargement des activités récentes...');
        fetch('/api/recent-activities/')
            .then(response => response.json())
            .then(data => {
                const tbody = document.getElementById('recentActivities');
                if (tbody && data.activities && data.activities.length > 0) {
                    tbody.innerHTML = data.activities.map(activity => `
                        <tr>
                            <td>${escapeHtml(activity.date)}</td>
                            <td>${escapeHtml(activity.user)}</td>
                            <td>${escapeHtml(activity.action)}</td>
                            <td>${escapeHtml(activity.details)}</td>
                        </tr>
                    `).join('');
                } else if (tbody) {
                    tbody.innerHTML = '<tr><td colspan="4" class="text-center">Aucune activité récente</td></tr>';
                }
            })
            .catch(error => console.error('Erreur chargement activités:', error));
    }
    
    // ========== GESTION DES FICHIERS ==========
    function loadFiles() {
        console.log('Chargement des fichiers...');
        const filesGrid = document.getElementById('filesGrid');
        if (filesGrid) {
            filesGrid.innerHTML = '<div class="loading-text">Chargement des fichiers...</div>';
            fetch('/api/files/')
                .then(response => response.json())
                .then(data => {
                    if (data.files && data.files.length > 0) {
                        filesGrid.innerHTML = data.files.map(file => `
                            <div class="file-card">
                                <i class="fas fa-file-alt"></i>
                                <h4>${escapeHtml(file.name)}</h4>
                                <p>${escapeHtml(file.description || 'Aucune description')}</p>
                                <small>${escapeHtml(file.size)} - ${escapeHtml(file.date)}</small>
                                <div class="file-actions">
                                    <button onclick="downloadFile(${file.id})" class="btn-sm">
                                        <i class="fas fa-download"></i>
                                    </button>
                                </div>
                            </div>
                        `).join('');
                    } else {
                        filesGrid.innerHTML = '<div class="empty-message">Aucun fichier trouvé</div>';
                    }
                })
                .catch(error => {
                    console.error('Erreur chargement fichiers:', error);
                    filesGrid.innerHTML = '<div class="error-message">Erreur de chargement des fichiers</div>';
                });
        }
    }
    
    // ========== GESTION DES UTILISATEURS ==========
    function loadUsers() {
        console.log('Chargement des utilisateurs...');
        const usersTableBody = document.getElementById('usersTableBody');
        if (usersTableBody) {
            usersTableBody.innerHTML = '<tr><td colspan="8" class="loading-text">Chargement...</td></tr>';
            fetch('/api/users/')
                .then(response => response.json())
                .then(data => {
                    if (data.users && data.users.length > 0) {
                        usersTableBody.innerHTML = data.users.map(user => `
                            <tr>
                                <td>${escapeHtml(user.id)}</td>
                                <td>${escapeHtml(user.fullname)}</td>
                                <td>${escapeHtml(user.email)}</td>
                                <td><span class="badge badge-${user.role}">${escapeHtml(user.role)}</span></td>
                                <td>${user.is_verified ? '✅ Oui' : '❌ Non'}</td>
                                <td>${user.file_access ? '✅ Oui' : '❌ Non'}</td>
                                <td>${escapeHtml(user.date)}</td>
                                <td class="actions">
                                    <button onclick="editUser(${user.id})" class="btn-icon">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button onclick="deleteUser(${user.id})" class="btn-icon">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('');
                    } else {
                        usersTableBody.innerHTML = '<tr><td colspan="8" class="text-center">Aucun utilisateur trouvé</td></tr>';
                    }
                })
                .catch(error => {
                    console.error('Erreur chargement utilisateurs:', error);
                    usersTableBody.innerHTML = '<tr><td colspan="8" class="error-message">Erreur de chargement</td></tr>';
                });
        }
    }
    
    // ========== GESTION DE L'HISTORIQUE EMAILS ==========
    function loadEmailHistory() {
        console.log('Chargement de l\'historique des emails...');
        const historyTableBody = document.getElementById('historyTableBody');
        if (historyTableBody) {
            historyTableBody.innerHTML = '<tr><td colspan="5" class="loading-text">Chargement...</td></tr>';
            fetch('/api/email-history/')
                .then(response => response.json())
                .then(data => {
                    if (data.history && data.history.length > 0) {
                        historyTableBody.innerHTML = data.history.map(history => `
                            <tr>
                                <td>${escapeHtml(history.date)}</td>
                                <td>${escapeHtml(history.sender)}</td>
                                <td>${escapeHtml(history.recipient)}</td>
                                <td>${escapeHtml(history.subject)}</td>
                                <td><span class="badge badge-${history.status}">${escapeHtml(history.status)}</span></td>
                            </tr>
                        `).join('');
                    } else {
                        historyTableBody.innerHTML = '<tr><td colspan="5" class="text-center">Aucun historique trouvé</td></tr>';
                    }
                })
                .catch(error => {
                    console.error('Erreur chargement historique:', error);
                    historyTableBody.innerHTML = '<tr><td colspan="5" class="error-message">Erreur de chargement</td></tr>';
                });
        }
    }
    
    // ========== GESTION DES ONGLETS ==========
    function switchTab(tabName) {
        console.log('Changement vers onglet:', tabName);
        
        // Cacher tous les onglets
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Afficher l'onglet sélectionné
        const activeTab = document.getElementById(`${tabName}Tab`);
        if (activeTab) {
            activeTab.classList.add('active');
            console.log('Onglet activé:', `${tabName}Tab`);
        } else {
            console.error('Onglet non trouvé:', `${tabName}Tab`);
        }
        
        // Mettre à jour le titre de la page
        const pageTitle = document.getElementById('pageTitle');
        const pageSubtitle = document.getElementById('pageSubtitle');
        
        if (pageTitle && pageSubtitle) {
            switch(tabName) {
                case 'dashboard':
                    pageTitle.innerText = 'Tableau de bord';
                    pageSubtitle.innerText = 'Bienvenue dans l\'interface d\'administration';
                    break;
                case 'files':
                    pageTitle.innerText = 'Gestion des fichiers';
                    pageSubtitle.innerText = 'Téléchargez et gérez vos fichiers';
                    loadFiles();
                    break;
                case 'users':
                    pageTitle.innerText = 'Gestion des utilisateurs';
                    pageSubtitle.innerText = 'Ajouter, modifier ou supprimer des utilisateurs';
                    loadUsers();
                    break;
                case 'history':
                    pageTitle.innerText = 'Historique des emails';
                    pageSubtitle.innerText = 'Consultez l\'historique des emails envoyés';
                    loadEmailHistory();
                    break;
                case 'xml':
                    pageTitle.innerText = 'Génération XML';
                    pageSubtitle.innerText = 'Générez des rapports XML personnalisés';
                    break;
                default:
                    console.log('Onglet inconnu:', tabName);
            }
        }
    }
    
    function updateActiveNavItem(activeItem) {
        // Retirer la classe active de tous les éléments
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Ajouter la classe active à l'élément cliqué
        activeItem.classList.add('active');
    }
    
    // ========== GESTION DU HASH DANS L'URL ==========
    function handleHashChange() {
        const hash = window.location.hash;
        if (hash) {
            const tab = hash.substring(1); // Enlever le #
            if (['dashboard', 'files', 'users', 'history', 'xml'].includes(tab)) {
                switchTab(tab);
                
                // Mettre à jour l'élément actif dans la navigation
                document.querySelectorAll('.nav-item').forEach(item => {
                    const itemTab = item.getAttribute('data-tab');
                    if (itemTab === tab) {
                        item.classList.add('active');
                    } else {
                        item.classList.remove('active');
                    }
                });
            }
        }
    }
    
    // ========== GESTION DU BOUTON RAFRAÎCHIR ==========
    const refreshBtn = document.getElementById('refreshData');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            console.log('Rafraîchissement des données...');
            loadStats();
            loadRecentActivities();
            const activeTab = document.querySelector('.tab-content.active');
            if (activeTab) {
                if (activeTab.id === 'filesTab') loadFiles();
                if (activeTab.id === 'usersTab') loadUsers();
                if (activeTab.id === 'historyTab') loadEmailHistory();
            }
        });
    }
    
    // ========== GESTION DE LA RECHERCHE GLOBALE ==========
    const searchInput = document.getElementById('globalSearch');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const searchTerm = e.target.value;
                console.log('Recherche:', searchTerm);
                // Implémenter la recherche selon l'onglet actif
                const activeTab = document.querySelector('.tab-content.active');
                if (activeTab) {
                    if (activeTab.id === 'filesTab') {
                        searchFiles(searchTerm);
                    } else if (activeTab.id === 'usersTab') {
                        searchUsers(searchTerm);
                    }
                }
            }, 300);
        });
    }
    
    function searchFiles(term) {
        console.log('Recherche fichiers:', term);
        // Implémenter la recherche de fichiers
    }
    
    function searchUsers(term) {
        console.log('Recherche utilisateurs:', term);
        // Implémenter la recherche d'utilisateurs
    }
    
    // ========== GESTION DES MODALS (SAUF ADD USER) ==========
    // Modal Upload
    const uploadBtn = document.getElementById('uploadFileBtn');
    const uploadModal = document.getElementById('uploadModal');
    
    if (uploadBtn && uploadModal) {
        uploadBtn.addEventListener('click', function() {
            uploadModal.style.display = 'block';
            loadUsersForSharing();
        });
    }
    
    // Fermer les modals (ne pas fermer addUserModal ici car il est géré par le script inline)
    const closeBtns = document.querySelectorAll('.close:not(#addUserModal .close)');
    closeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            if (uploadModal) uploadModal.style.display = 'none';
        });
    });
    
    // Fermer en cliquant en dehors (ne pas fermer addUserModal ici car il est géré par le script inline)
    window.addEventListener('click', function(e) {
        if (uploadModal && e.target === uploadModal) uploadModal.style.display = 'none';
    });
    
    function loadUsersForSharing() {
        const shareWithSelect = document.getElementById('shareWith');
        if (shareWithSelect) {
            fetch('/api/users/')
                .then(response => response.json())
                .then(data => {
                    shareWithSelect.innerHTML = data.users.map(user => 
                        `<option value="${user.id}">${escapeHtml(user.fullname)} (${escapeHtml(user.email)})</option>`
                    ).join('');
                })
                .catch(error => console.error('Erreur chargement utilisateurs:', error));
        }
    }
    
    // ========== GESTION DU FORMULAIRE UPLOAD ==========
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            
            fetch('/api/upload/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Fichier uploadé avec succès !');
                    if (uploadModal) uploadModal.style.display = 'none';
                    loadFiles();
                } else {
                    alert('Erreur: ' + data.error);
                }
            })
            .catch(error => console.error('Erreur upload:', error));
        });
    }
    
    // ========== GESTION DE LA GÉNÉRATION XML ==========
    const generateXmlBtn = document.getElementById('generateXmlBtn');
    if (generateXmlBtn) {
        generateXmlBtn.addEventListener('click', function() {
            const xmlType = document.getElementById('xmlType')?.value;
            const xmlFilter = document.getElementById('xmlFilter')?.value;
            const xmlPreview = document.getElementById('xmlPreview');
            
            if (xmlPreview) {
                xmlPreview.innerText = 'Génération en cours...';
            }
            
            fetch(`/api/generate-xml/?type=${encodeURIComponent(xmlType)}&filter=${encodeURIComponent(xmlFilter)}`)
                .then(response => response.json())
                .then(data => {
                    if (xmlPreview) {
                        xmlPreview.innerText = data.xml_content || 'Aucune donnée à afficher';
                    }
                    if (data.download_url) {
                        window.location.href = data.download_url;
                    }
                })
                .catch(error => {
                    console.error('Erreur génération XML:', error);
                    if (xmlPreview) {
                        xmlPreview.innerText = 'Erreur lors de la génération du XML';
                    }
                });
        });
    }
    
    // Fonction utilitaire pour échapper le HTML
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // ========== CHARGEMENT INITIAL ==========
    console.log('Chargement initial des données...');
    loadStats();
    loadRecentActivities();
    
    // Gérer le hash au chargement
    handleHashChange();
    
    // Écouter les changements de hash
    window.addEventListener('hashchange', handleHashChange);
});

// ========== FONCTIONS GLOBALES ==========
function downloadFile(fileId) {
    console.log('Téléchargement du fichier:', fileId);
    window.location.href = `/api/download/${fileId}/`;
}

function editUser(userId) {
    console.log('Édition utilisateur:', userId);
    // Implémenter l'édition
}

function deleteUser(userId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cet utilisateur ?')) {
        console.log('Suppression utilisateur:', userId);
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        fetch(`/api/delete-user/${userId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Utilisateur supprimé avec succès');
                location.reload();
            } else {
                alert('Erreur: ' + data.error);
            }
        })
        .catch(error => console.error('Erreur suppression:', error));
    }
}