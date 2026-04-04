// =============================================================================
// script.js — La logique de l application web pour configurer le macropad
// se que sa fait :
// - Afficher les touches et leur config
// - Ouvrir et sauvegarder le fichier config.json 
// - Capturer les raccourcis clavier
// - Gérer les clics sur les boutons de la bibliothèque
// =============================================================================


// =============================================================================
// Les variable globales de l'application — elles stockent l'état de l'application et la config en cours
// =============================================================================

let isConfigLoaded = false;   // le json est chargé?
let isConnected = false;      // l'utilisateur a-t-il lié un fichier config.json ? 
let learningKeyId = null;     // Quelle touche est actuellement sélectionnée pour l'édition ? (0 à 5, ou null si aucune)
let fileHandle = null;        // La référence au fichier ouvert (pour sauvegarder plus tard)

// La config actuelle en mémoire, qui sera modifiée au fur et à mesure que l'utilisateur édite les touches.
let currentConfig = {
    layout: "AZERTY",   
    os: "windows",      
    keys: {},           
    mapping: {},        
};

// Variables pour la capture de raccourcis clavier
let isRecording = false;   
let activeKeys = new Set(); 
let finalCombo = [];        


// =============================================================================
// 
// =============================================================================

const connectBtn       = document.getElementById('connectBtn');       // Bouton "Ouvrir config.json"
const applyBtn         = document.getElementById('applyBtn');         // Bouton "Sauvegarder"
const inputField       = document.getElementById('actionValue');      // Champ texte pour la valeur
const actionTypeSelect = document.getElementById('actionType');       // Menu déroulant du type d'action
const osSelect         = document.getElementById('osSelect');         // Menu déroulant Windows/Linux
const layoutSelect     = document.getElementById('layoutSelect');     // Menu déroulant AZERTY/QWERTY
const targetName       = document.getElementById('targetName');       // Affiche le nom de la touche ciblée
const editorPanel      = document.getElementById('editorPanel');      // Panneau d'édition (droite)
const logDiv           = document.getElementById('log');              // Barre de statut en bas
const keys             = document.querySelectorAll('.key');           // TOUTES les touches visuelles


// =============================================================================
// FONCTIONS DE MISE À JOUR DE L'INTERFACE ET DE LA CONFIG
// =============================================================================
function updateOSPresets() {
    /**
     * Affiche les boutons de raccourcis adaptés au bon OS.
     */
    const isLinux = osSelect.value === 'linux';  // true si Linux sélectionné, false si Windows
    document.getElementById('presets-windows').style.display = isLinux ? 'none' : 'grid';
    document.getElementById('presets-linux').style.display   = isLinux ? 'grid' : 'none';
}

function updateUIForActionType() {
    /**
     * Adapte l'interface selon le type d'action sélectionné.
     * - "shortcut" → affiche le bouton "Capturer", placeholder "CTRL+C"
     * - "text"     → cache le bouton capturer, placeholder "Bonjour !"
     * - "launch"   → cache le bouton capturer, label "Application ou URL"
     */
    const type = actionTypeSelect.value;      // Récupère la valeur du menu déroulant
    const isLaunch   = type === 'launch';     // Est-ce le type "lancer appli" ?
    const isShortcut = type === 'shortcut';   // Est-ce le type "raccourci" ?

    // Affiche ou cache le bouton "Capturer" 
    document.getElementById('recordBtn').style.display = isShortcut ? 'block' : 'none';

    //On change le label du champ texte selon le type 
    document.getElementById('valueLabel').innerText = isLaunch
        ? "Application ou URL"  // Si type = launch
        : "Valeur / Macro";     // Si type = text ou shortcut

    // Change le texte d'exemple dans le champ texte
    inputField.placeholder = isLaunch
        ? "ex: https://youtube.com ou calc"
        : "ex: CTRL+C ou Bonjour";
}

function updateLocalConfig() {
    /**
     * Met à jour la variable currentConfig avec les valeurs actuelles des champs.
     * Appelée à chaque fois que l'utilisateur modifie quelque chose dans le panneau.
     * Puis rafraîchit l'affichage des touches.
     */
    if (learningKeyId === null) return;  

    // Récupère le numéro de broche GPIO correspondant à la touche sélectionnée
    const pin = currentConfig.mapping[learningKeyId];
    if (!pin) return;  

    // Met à jour la config pour cette broche avec les valeurs des champs
    currentConfig.keys[pin] = {
        type: actionTypeSelect.value,  
        value: inputField.value,       
    };
    refreshAllVisualKeys();  // on rafraîchit l'affichage des touches pour montrer la nouvelle config assignée
}

function refreshAllVisualKeys() {
    /**
     * Met à jour l'affichage visuel des 6 touches du macropad.
     * Pour chaque touche, on affiche :
     * - Son numéro GPIO entre parenthèses
     * - La valeur de l'action assignée (ou "--" si rien)
     * - Une bordure verte si elle est configurée
     */
    for (let id = 0; id < 6; id++) {  // On parcourt les 6 touches (id 0 à 5)
        const keyDiv     = document.getElementById('key_' + id);     
        const macroSpan  = document.getElementById('macro_' + id);  
        const pinDisplay = document.getElementById('pinDisplay_' + id);
        const pin        = currentConfig.mapping[id]; 

        if (pin) {
            // Cette touche a un GPIO assigné → on l'affiche
            pinDisplay.textContent = "(GP" + pin + ")"; 

            if (currentConfig.keys[pin] && currentConfig.keys[pin].value) {
                // Une action est configurée pour ce GPIO
                macroSpan.textContent = currentConfig.keys[pin].value;
                keyDiv.classList.add('configured');  
            } else {
                // Aucune action configurée 
                macroSpan.textContent = "--";
                keyDiv.classList.remove('configured');
            }
        } else {
            // Cette touche n'a pas de GPIO 
            pinDisplay.textContent = "(Non linké)";
            macroSpan.textContent  = "--";
            keyDiv.classList.remove('configured');
        }
    }
}

function selectKeyForLearning(id) {
    /**
     * Sélectionne une touche pour l'éditer.
     * Met en surbrillance la touche cliquée et affiche ses paramètres dans le panneau latéral.
     * - id : l'identifiant visuel de la touche (0 à 5)
     */
    // Retire la classe "active"  de toutes les touches
    keys.forEach(k => k.classList.remove('active'));

    learningKeyId = id;  
    document.getElementById('key_' + id).classList.add('active');  // Surligne la touche cliquée
    editorPanel.classList.remove('disabled');  // Rend le panneau d'édition actif 

    const pin = currentConfig.mapping[id];  // Trouve le GPIO de cette touche

    if (pin) {
        targetName.innerText = "Touche liée au GPIO " + pin;

        if (currentConfig.keys[pin]) {
            // si une config deja assigne on affiche les valeurs dans les champs
            actionTypeSelect.value = currentConfig.keys[pin].type  || 'shortcut';
            inputField.value       = currentConfig.keys[pin].value || '';
        } else {
            actionTypeSelect.value = 'shortcut';
            inputField.value       = '';
        }
    } else {
        // Pas de GPIO assigné
        targetName.innerText   = "ERREUR : Pin non définie dans le JSON";
        actionTypeSelect.value = 'shortcut';
        inputField.value       = '';
    }

    updateUIForActionType();  
}


// Quand on change le système d'exploitation dans le menu
osSelect.addEventListener('change', () => {
    currentConfig.os = osSelect.value;  
    updateOSPresets();         
});

// Quand on change le layout clavier
layoutSelect.addEventListener('change', () => {
    currentConfig.layout = layoutSelect.value;  
});

// Quand on change le type d'action (shortcut / text / launch)
actionTypeSelect.addEventListener('change', () => {
    updateUIForActionType();  
    updateLocalConfig();    
});


inputField.addEventListener('input', updateLocalConfig); 

// Quand on clique sur une touche visuelle
keys.forEach(key => {
    key.addEventListener('click', () => {
        if (isConnected) {
            // si un fichier est ouvert on edite la touche
            selectKeyForLearning(key.dataset.id);  
        } else {
            // Pas de fichier ouvert 
            alert("Veuillez d'abord ouvrir le fichier config.json du clavier.");
        }
    });
});


// --- Fonctions de preset (exposées globalement pour les boutons dans le HTML) ---
// "window.xxx = function" permet d'appeler ces fonctions depuis les onclick= du HTML

window.setPreset = function (val) {
    /**
     * Applique un preset de type "raccourci clavier" 
     */
    actionTypeSelect.value = 'shortcut';  // Force le type à "raccourci"
    inputField.value = val;               // Met la valeur dans le champ
    updateUIForActionType();              
    updateLocalConfig();                 
};

window.setLaunch = function (val) {
    /**
     * Applique un preset de type "lancer une URL ou appli" 
     */
    actionTypeSelect.value = 'launch';   
    inputField.value = val;
    updateUIForActionType();
    updateLocalConfig();
};

window.setApp = function (windowsApp, linuxApp) {
    /**
     * Choisit l'application à lancer selon l'OS sélectionné.
     * Ex: setApp('calc', 'gnome-calculator') → lance calc sur Windows, gnome-calculator sur Linux
     */
    const appToLaunch = (osSelect.value === 'linux') ? linuxApp : windowsApp;
    window.setLaunch(appToLaunch);  // Utilise setLaunch avec le bon nom d'appli
};


// =============================================================================
// FONCTIONS DE CAPTURE DE RACCOURCIS CLAVIER
// =============================================================================

// AZERTY_KEY_MAP = Certains caractères sur un clavier AZERTY ne correspondent pas directement à des touches de raccourci standard.
const AZERTY_KEY_MAP = {
    '&': '1', 'É': '2', '"': '3', "'": '4',
    '(': '5', '-': '6', 'È': '7', '_': '8',
    'Ç': '9', 'À': '0',
};

function formatKeyName(key) {
    /**
     * Transforme le nom d'une touche JS en nom lisible et cohérent pour notre config.
     */
    key = key.toUpperCase();  // Met tout en majuscules

    if (key === 'CONTROL')              return 'CTRL';   
    if (key === 'META' || key === 'OS') return 'GUI';   
    if (key === 'ESCAPE')               return 'ESC';    
    if (key === ' ')                    return 'SPACE';  
    if (key.startsWith('ARROW'))        return key.replace('ARROW', ''); 

    return AZERTY_KEY_MAP[key] || key;  
}

function captureKeyDown(e) {
    /**
     * Appelée à chaque fois qu'une touche est ENFONCÉE pendant l'enregistrement.
     * Ajoute la touche à la combinaison en cours.
     */
    e.preventDefault();    
    e.stopPropagation();   

    const key = formatKeyName(e.key);  
    activeKeys.add(key);              

    if (!finalCombo.includes(key)) {
        finalCombo.push(key);
    }
    // Affiche la combinaison en cours dans le champ texte pendant l'enregistrement 
    inputField.value = finalCombo.join('+');
    updateLocalConfig();
}

function captureKeyUp(e) {
    /**
     * Appelée à chaque fois qu'une touche est RELÂCHÉE pendant l'enregistrement.
     * Quand toutes les touches sont relâchées, on arrête l'enregistrement.
     */
    e.preventDefault();
    e.stopPropagation();

    activeKeys.delete(formatKeyName(e.key));  // Retire la touche des touches enfoncées

    if (activeKeys.size === 0) {
        stopRecording();
    }
}

function stopRecording() {
    /**
     * Arrête le mode d'enregistrement de raccourci.
     * Remet l'interface dans son état normal.
     */
    if (!isRecording) return; 

    isRecording = false;

    const btn = document.getElementById('recordBtn');
    btn.innerHTML = "⏺️ Capturer";
    btn.classList.remove('recording');  // Retire l'animation rouge

    inputField.disabled = false;  // Réactive le champ texte


    document.removeEventListener('keydown', captureKeyDown, { capture: true });
    document.removeEventListener('keyup', captureKeyUp, { capture: true });
    window.removeEventListener('blur', stopRecording);  // Si la fenêtre perd le focus

    updateLocalConfig();
}

function toggleRecording() {
    /**
     * Active ou désactive le mode enregistrement de raccourci.
     * Appelée quand on clique sur le bouton "⏺️ Capturer".
     */
    const btn = document.getElementById('recordBtn');

    if (!isRecording) {

        isRecording = true;
        activeKeys.clear();   // Vide les touches actives
        finalCombo = [];      // Remet la combinaison à zéro

        btn.innerHTML = "🛑 En cours";   
        btn.classList.add('recording'); 

        inputField.value    = "Maintenez vos touches..."; 
        inputField.disabled = true;  

        document.addEventListener('keydown', captureKeyDown, { capture: true });
        document.addEventListener('keyup', captureKeyUp, { capture: true });
        window.addEventListener('blur', stopRecording);  // Si l'utilisateur change de fenêtre → stop
    } else {
  
        stopRecording();
    }
}

// Quand on clique sur le bouton "Capturer"
document.getElementById('recordBtn').addEventListener('click', toggleRecording);


// =============================================================================
// ouverture de fichier via File System Access API
// =============================================================================

connectBtn.addEventListener('click', async () => {
    /**
     * Ouvre une boîte de dialogue pour choisir le fichier config.json
     */
    try {
        const [handle] = await window.showOpenFilePicker({
            types: [{
                description: 'Fichier de configuration JSON',
                accept: { 'application/json': ['.json'] },  // Filtre pour n'afficher que les .json
            }],
            multiple: false,  
        });

        fileHandle = handle;  
        const file     = await fileHandle.getFile();  
        const contents = await file.text();          
        const newConfig = JSON.parse(contents);       

        // Copie les valeurs du JSON dans notre currentConfig
        currentConfig.layout  = newConfig.layout  || "AZERTY";   
        currentConfig.os      = newConfig.os       || "windows";
        currentConfig.keys    = newConfig.keys     || {};
        currentConfig.mapping = newConfig.mapping  || {};


        osSelect.value     = currentConfig.os;
        layoutSelect.value = currentConfig.layout;

        updateOSPresets();      
        refreshAllVisualKeys();  

        isConfigLoaded = true;  
        isConnected    = true;  

        connectBtn.textContent = "Fichier lié !";
        connectBtn.classList.add('connected'); 

        applyBtn.disabled = false;  // Active le bouton "Sauvegarder" 

        logDiv.innerText = "État : Configuration chargée depuis le fichier avec succès.";

    } catch (err) {
        console.error("Erreur d'ouverture ou annulation :", err);
        logDiv.innerText = "État : Erreur lors de la sélection du fichier.";
    }
});


// =============================================================================
// sauvegarde de la config dans le fichier ouvert
// =============================================================================

applyBtn.addEventListener('click', async () => {
    /**
     * Sauvegarde la configuration actuelle dans le fichier config.json 
     * IMPORTANT : il faut bien éjecter le Pico après pour que la sauvegarde soit complète.
     */

    // message d'avertissement
    const confirmation = confirm(
        "⚠️ ATTENTION : Ne débranchez pas le clavier à la volée après une nouvelle assignation.\n\n" +
        "Il est impératif d'éjecter le périphérique proprement depuis votre ordinateur pour que la " +
        "nouvelle configuration soit bien enregistrée et pour éviter de corrompre le fichier config.json.\n\n" +
        "Souhaitez-vous continuer la sauvegarde ?"
    );

    if (!confirmation) return;  

    if (!fileHandle) {
        alert("Veuillez d'abord lier le fichier config.json.");
        return;
    }

    try {
        logDiv.innerText = "État : Sauvegarde en cours...";

        const configToSave = {
            "_AIDE_1":       "Parametres globaux -> layout : AZERTY ou QWERTY | os : windows ou linux",
            "_AIDE_TYPES_1": "Il existe 3 types d'actions :",
            "_AIDE_TYPES_2": "1. 'shortcut' : Raccourci clavier (ex: 'CTRL+C', 'GUI+D', 'A').",
            "_AIDE_TYPES_3": "2. 'text'     : Tape une phrase entiere (ex: 'Bonjour !').",
            "_AIDE_TYPES_4": "3. 'launch'   : Ouvre une application ou une URL (ex: 'notepad', 'https://github.com').",
            ...currentConfig,  
        };

        const jsonString = JSON.stringify(configToSave, null, 2);

        const writable   = await fileHandle.createWritable();
        await writable.write(jsonString);  // Écrit le texte JSON dans le fichier
        await writable.close();           

        applyBtn.textContent      = "✓ SAUVEGARDÉ !";
        applyBtn.style.background = "#00ff88";  
        logDiv.innerText = "État : Fichier config.json mis à jour ! N'OUBLIEZ PAS D'ÉJECTER LE LECTEUR.";

        setTimeout(() => {
            applyBtn.textContent      = "SAUVEGARDER SUR LE CLAVIER";
            applyBtn.style.background = "#00d2ff"; 
        }, 3000);  

    } catch (err) {
        console.error("Erreur d'écriture :", err);
        logDiv.innerText = "État : Échec de la sauvegarde.";
        alert("Erreur lors de la sauvegarde. Avez-vous accordé les droits d'écriture ?");
    }
});

updateOSPresets(); 