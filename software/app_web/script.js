let port, writer, reader;
let keepReading = true;
let isConfigLoaded = false;
let isConnected = false; // Flag pour checker si le serial est up

// Config en RAM par défaut (au cas où on n'arrive pas à lire celle du Pico)
let currentConfig = { layout: "AZERTY", os: "windows", keys: {}, mapping: {} };
let learningKeyId = null;

// Cache des éléments du DOM
const connectBtn = document.getElementById('connectBtn');
const applyBtn = document.getElementById('applyBtn');
const inputField = document.getElementById('actionValue');
const actionTypeSelect = document.getElementById('actionType');
const osSelect = document.getElementById('osSelect');
const layoutSelect = document.getElementById('layoutSelect');
const targetName = document.getElementById('targetName');
const editorPanel = document.getElementById('editorPanel');
const logDiv = document.getElementById('log');
const keys = document.querySelectorAll('.key');

// --- UI & DOM ---

// Affiche/masque les presets selon l'OS (les raccourcis Gnome vs Windows...)
function updateOSPresets() {
    if (osSelect.value === 'linux') {
        document.getElementById('presets-windows').style.display = 'none';
        document.getElementById('presets-linux').style.display = 'grid';
    } else {
        document.getElementById('presets-windows').style.display = 'grid';
        document.getElementById('presets-linux').style.display = 'none';
    }
}

osSelect.addEventListener('change', () => { currentConfig.os = osSelect.value; updateOSPresets(); });
layoutSelect.addEventListener('change', () => { currentConfig.layout = layoutSelect.value; });

// Rafraîchit les 6 touches visuelles du macropad
function refreshAllVisualKeys() {
    for(let id=0; id<6; id++) {
        const keyDiv = document.getElementById('key_' + id);
        const macroSpan = document.getElementById('macro_' + id);
        const pinDisplay = document.getElementById('pinDisplay_' + id);

        let pin = currentConfig.mapping[id];
        
        if (pin) {
            pinDisplay.textContent = "(GP" + pin + ")";
            if (currentConfig.keys[pin] && currentConfig.keys[pin].value) {
                macroSpan.textContent = currentConfig.keys[pin].value;
                keyDiv.classList.add('configured');
            } else {
                macroSpan.textContent = "--";
                keyDiv.classList.remove('configured');
            }
        } else {
            pinDisplay.textContent = "(Non linké)";
            macroSpan.textContent = "--";
            keyDiv.classList.remove('configured');
        }
    }
}

// Focus sur une touche pour l'éditer
function selectKeyForLearning(id) {
    keys.forEach(k => k.classList.remove('active'));
    learningKeyId = id; 
    document.getElementById('key_' + id).classList.add('active');
    editorPanel.classList.remove('disabled');

    if (currentConfig.mapping[id]) {
        let pin = currentConfig.mapping[id];
        targetName.innerText = "GPIO " + pin;
        if (currentConfig.keys[pin]) {
            actionTypeSelect.value = currentConfig.keys[pin].type || 'shortcut';
            inputField.value = currentConfig.keys[pin].value || '';
        } else {
            actionTypeSelect.value = 'shortcut';
            inputField.value = '';
        }
    } else {
        targetName.innerText = "APPUYEZ SUR LE MACROPAD...";
        actionTypeSelect.value = 'shortcut';
        inputField.value = '';
    }
    updateUIForActionType();
}

// Bind des events de clic sur les div des touches
keys.forEach(key => {
    key.addEventListener('click', () => {
        if(writer) selectKeyForLearning(key.dataset.id);
        else alert("Veuillez d'abord connecter le Macropad.");
    });
});

// Switch l'affichage de l'input selon l'action voulue
function updateUIForActionType() {
    const type = actionTypeSelect.value;
    document.getElementById('recordBtn').style.display = (type === 'shortcut') ? 'block' : 'none';
    document.getElementById('valueLabel').innerText = (type === 'launch') ? "Application ou URL" : "Valeur / Macro";
    inputField.placeholder = (type === 'launch') ? "ex: https://youtube.com ou calc" : "ex: CTRL+C ou Bonjour";
}

actionTypeSelect.addEventListener('change', () => { updateUIForActionType(); updateLocalConfig(); });
inputField.addEventListener('input', updateLocalConfig);

// Met à jour l'objet config local dès qu'on tape un truc
function updateLocalConfig() {
    if(learningKeyId !== null && currentConfig.mapping[learningKeyId]) {
        let pin = currentConfig.mapping[learningKeyId];
        currentConfig.keys[pin] = { 
            type: actionTypeSelect.value, 
            value: inputField.value 
        };
        refreshAllVisualKeys();
    }
}

// Helpers exposés sur window pour les onclick du HTML
window.setPreset = function(val) { actionTypeSelect.value = 'shortcut'; inputField.value = val; updateUIForActionType(); updateLocalConfig(); }
window.setLaunch = function(val) { actionTypeSelect.value = 'launch'; inputField.value = val; updateUIForActionType(); updateLocalConfig(); }
window.setApp = function(windowsApp, linuxApp) { const appToLaunch = (osSelect.value === 'linux') ? linuxApp : windowsApp; setLaunch(appToLaunch); }

// Gestion de l'enregistrement de combos de touches (le truc chiant avec les listeners)
let isRecording = false; let activeKeys = new Set(); let finalCombo = [];
document.getElementById('recordBtn').addEventListener('click', toggleRecording);

function toggleRecording() {
    const btn = document.getElementById('recordBtn');
    if (!isRecording) {
        isRecording = true; activeKeys.clear(); finalCombo = [];
        btn.innerHTML = "🛑 En cours"; btn.classList.add('recording');
        inputField.value = "Maintenez vos touches..."; inputField.disabled = true;
        // On bind en capture pour choper l'event avant tout le monde
        document.addEventListener('keydown', captureKeyDown, { capture: true });
        document.addEventListener('keyup', captureKeyUp, { capture: true });
        window.addEventListener('blur', stopRecording);
    } else { stopRecording(); }
}

// Formate les noms de touches renvoyés par l'event js pour que le python du Pico comprenne
function formatKeyName(key) {
    key = key.toUpperCase();
    if (key === 'CONTROL') return 'CTRL'; if (key === 'META' || key === 'OS') return 'GUI';
    if (key === 'ESCAPE') return 'ESC'; if (key === ' ') return 'SPACE';
    if (key.startsWith('ARROW')) return key.replace('ARROW', '');
    // Mapping manuel dégueu mais nécessaire pour l'AZERTY français
    const azertyMap = {'&':'1','É':'2','"':'3',"'":'4','(':'5','-':'6','È':'7','_':'8','Ç':'9','À':'0'};
    return azertyMap[key] || key;
}

// On chope l'event quand on enfonce la touche
function captureKeyDown(e) {
    e.preventDefault(); e.stopPropagation();
    let key = formatKeyName(e.key);
    activeKeys.add(key);
    if (!finalCombo.includes(key)) finalCombo.push(key);
    inputField.value = finalCombo.join('+');
    updateLocalConfig();
}

// Check quand on relâche
function captureKeyUp(e) {
    e.preventDefault(); e.stopPropagation();
    activeKeys.delete(formatKeyName(e.key));
    if (activeKeys.size === 0) stopRecording();
}

// Nettoyage des listeners (super important sinon ça leak)
function stopRecording() {
    if (!isRecording) return;
    isRecording = false;
    const btn = document.getElementById('recordBtn');
    btn.innerHTML = "⏺️ Capturer"; btn.classList.remove('recording');
    inputField.disabled = false;
    document.removeEventListener('keydown', captureKeyDown, { capture: true });
    document.removeEventListener('keyup', captureKeyUp, { capture: true });
    window.removeEventListener('blur', stopRecording);
    updateLocalConfig();
}

// --- COMMUNICATION SÉRIE (Web Serial API) ---

connectBtn.addEventListener('click', async () => {
    
    // Si on est déjà branché, un clic = reload de la page (fausse déconnexion)
    if (isConnected) {
        try {
            if (writer) await writer.write("MODE:MACRO\n");
        } catch(e){}
        window.location.reload(); 
        return;
    }

    try {
        // Demande d'accès au port COM
        port = await navigator.serial.requestPort();
        await port.open({ baudRate: 115200 });

        const textEncoder = new TextEncoderStream(); textEncoder.readable.pipeTo(port.writable);
        writer = textEncoder.writable.getWriter();

        const textDecoder = new TextDecoderStream(); port.readable.pipeTo(textDecoder.writable);
        reader = textDecoder.readable.getReader();

        keepReading = true;
        isConfigLoaded = false;
        isConnected = true;
        readLoop();

        // Update UI
        connectBtn.textContent = "Déconnecter & Réactiver";
        connectBtn.classList.add('connected');
        applyBtn.disabled = false;
        logDiv.innerText = "État : Réveil du clavier (Mode Édition, macros muettes)...";

        // Polling pour dire au Pico de passer en mode MAPPING
        const pingInterval = setInterval(async () => {
            if (isConfigLoaded || !writer) {
                clearInterval(pingInterval);
            } else {
                try { await writer.write("MODE:MAPPING\n"); } catch(e){}
            }
        }, 500);

    } catch (err) { console.error(err); } // L'user a annulé ou le port est pris
});

// Sécurité : si le gars ferme l'onglet on essaie de remettre le Pico en MACRO
window.addEventListener('beforeunload', () => {
    if (isConnected && writer) {
        writer.write("MODE:MACRO\n");
    }
});

// Boucle de lecture asynchrone pour lire ce que le Pico nous raconte
async function readLoop() {
    let buffer = "";
    while (port.readable && keepReading) {
        try {
            const { value, done } = await reader.read();
            if (done) break;
            if (value) {
                buffer += value;
                let lines = buffer.split('\n');
                buffer = lines.pop(); // Garde le bout de ligne pas fini dans le buffer

                for (let line of lines) {
                    line = line.trim();
                    
                    // Si le dev a appuyé sur un bouton du macropad
                    if (line.startsWith("PIN_PRESSED:")) {
                        let pin = line.split(":")[1];
                        if (learningKeyId !== null) {
                            currentConfig.mapping[learningKeyId] = pin;
                            // Init le pin dans les keys s'il existe pas
                            if (!currentConfig.keys[pin]) {
                                currentConfig.keys[pin] = { type: actionTypeSelect.value, value: inputField.value };
                            }
                            targetName.innerText = "GPIO " + pin;
                            refreshAllVisualKeys();
                            updateLocalConfig();
                        }
                    }
                    // Le Pico a répondu avec sa config actuelle
                    else if (line.startsWith("CURRENT_CONFIG:")) {
                        try {
                            const configJson = line.replace("CURRENT_CONFIG:", "");
                            const newConfig = JSON.parse(configJson);
                            
                            // On merge la config lue dans la variable locale
                            currentConfig.layout = newConfig.layout || "AZERTY";
                            currentConfig.os = newConfig.os || "windows";
                            currentConfig.keys = newConfig.keys || {};
                            currentConfig.mapping = newConfig.mapping || {};
                            
                            osSelect.value = currentConfig.os;
                            layoutSelect.value = currentConfig.layout;
                            updateOSPresets();
                            
                            refreshAllVisualKeys();
                            
                            isConfigLoaded = true; 
                            logDiv.innerText = "État : Configuration chargée avec succès (Macros inactives en édition).";
                        } catch (e) { console.error("Erreur JSON:", e); }
                    }
                }
            }
        } catch (error) { break; } // Port déconnecté sauvagement
    }
}

// Push de la nouvelle config vers le Pico
applyBtn.addEventListener('click', async () => {
    if (!writer) return;
    try {
        const jsonString = JSON.stringify(currentConfig);
        const fullMessage = "NEW_CONFIG:" + jsonString + "\n";
        
        // ASTUCE: On envoie par chunks (32 bytes) parce que le buffer du rp2040 peut saturer vite
        for (let i = 0; i < fullMessage.length; i += 32) {
            await writer.write(fullMessage.substring(i, i + 32));
            await new Promise(resolve => setTimeout(resolve, 10));
        }
        
        // Feedback UI
        applyBtn.textContent = "✓ APPLIQUÉ !";
        applyBtn.style.background = "#00ff88";
        
        setTimeout(() => {
            applyBtn.textContent = "APPLIQUER AU CLAVIER";
            applyBtn.style.background = "#00d2ff";
        }, 2000);

    } catch (err) { console.error(err); }
});

updateOSPresets();