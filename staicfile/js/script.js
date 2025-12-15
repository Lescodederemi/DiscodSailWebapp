// Initialisation des événements au chargement du DOM
document.addEventListener('DOMContentLoaded', function() {

    // --- LOGIQUE COMMUNE A PLUSIEURS PAGES ---

    // Gestion des onglets (utilisé sur la page historique)
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            // Ajoutez ici la logique pour filtrer le contenu affiché
        });
    });

    
    // Animation de la barre de progression du niveau au chargement de la page
    const progressBar = document.querySelector('.level-progress-bar');
    if (progressBar) {
        const targetWidth = progressBar.style.width;
        progressBar.style.width = '0%';
        setTimeout(() => {
            progressBar.style.width = targetWidth;
        }, 300); // léger délai pour que l'animation soit visible
    }

    // --- LOGIQUE SPÉCIFIQUE A LA PAGE DE L'HISTORIQUE (HISTORY.HTML) ---

    // Gestion des filtres
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            // Ajoutez ici la logique pour filtrer la liste des tentatives
        });
    });

    // Gestion des boutons de certificats
    const certificateBtns = document.querySelectorAll('.certificate-btn');
    certificateBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            if(btn.textContent.includes('Créer')) {
                alert('Génération du certificat en cours...');
            } else if(btn.textContent.includes('Télécharger')) {
                alert('Téléchargement du modèle de certificat...');
            } else if(btn.textContent.includes('Partager')) {
                alert('Partage des certificats...');
            }
        });
    });


    // --- LOGIQUE SPÉCIFIQUE A LA PAGE DES PARAMETRES (ACCOUNT.HTML) ---
    
    // Gestion de la déconnexion Discord
    const disconnectBtn = document.getElementById('disconnectDiscordBtn');
    if(disconnectBtn) {
        disconnectBtn.addEventListener('click', function() {
            if (confirm('Êtes-vous sûr de vouloir déconnecter votre compte Discord ?')) {
                // Ici, vous feriez une redirection ou un appel AJAX pour déconnecter
                alert('Compte déconnecté (simulation).');
                window.location.href = '/'; // Rediriger vers l'accueil
            }
        });
    }
    
    // Gestion de l'annulation d'abonnement
    const cancelBtn = document.querySelector('.btn-cancel');
    if(cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            if (confirm('Votre abonnement restera actif jusqu\'à la fin de la période payée. Confirmez-vous l\'annulation ?')) {
                alert('Votre demande d\'annulation a été enregistrée.');
                this.textContent = "Annulation en cours";
                this.disabled = true;
            }
        });
    }
    
    // Gestion du changement d'abonnement (redirection)
    const upgradeBtn = document.querySelector('.btn-upgrade');
    if(upgradeBtn) {
        upgradeBtn.addEventListener('click', function() {
            window.location.href = '/board.html#subscription'; // Mettez l'URL Django correcte
        });
    }
});

   const userLevel = "{{ niveau_utilisateur|default:'' }}";
    const userLives = "{{ vies_utilisateur|default:'' }}";

    document.addEventListener('DOMContentLoaded', function() {
        if (userLevel) {
            document.getElementById('user-level').textContent = userLevel;
        }
        if (userLives) {
            document.getElementById('user-lives').textContent = userLives;
        }
    });