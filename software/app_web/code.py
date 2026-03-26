import board
import digitalio
import time
import sys
import supervisor
import json
import os
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# Init des pins du RPi Pico (GP3 à GP8)
PIN_MAPPING = {3: board.GP3, 4: board.GP4, 5: board.GP5, 6: board.GP6, 7: board.GP7, 8: board.GP8}
buttons = {}
last_state = {}
last_debounce_time = {}

# Setup des boutons en input avec pull-up (appui = False/0V)
for pin, gp in PIN_MAPPING.items():
    btn = digitalio.DigitalInOut(gp)
    btn.direction = digitalio.Direction.INPUT
    btn.pull = digitalio.Pull.UP
    buttons[pin] = btn
    last_state[pin] = False
    last_debounce_time[pin] = 0

kbd = Keyboard(usb_hid.devices)
current_mode = "MACRO" # Mode par defaut
# Config de base au cas ou le fichier json n'existe pas
config = {"layout": "AZERTY", "os": "windows", "keys": {}, "mapping": {}}

# On tente de charger la config depuis la flash
try:
    with open("/config.json", "r") as f:
        saved = json.load(f)
        # Petite verif crade pour override la config par defaut
        if "layout" in saved: config["layout"] = saved["layout"]
        if "os" in saved: config["os"] = saved["os"]
        if "keys" in saved: config["keys"] = saved["keys"]
        if "mapping" in saved: config["mapping"] = saved["mapping"]
except Exception:
    pass # Si ça pète (fichier absent ou corrompu), on s'en fout on garde les valeurs par défaut

# Map physique pour bypasser l'OS en AZERTY (toujours un enfer ça)
AZ_PHYSICAL = {
    'a': (Keycode.Q, False), 'A': (Keycode.Q, True), 'q': (Keycode.A, False), 'Q': (Keycode.A, True),
    'z': (Keycode.W, False), 'Z': (Keycode.W, True), 'w': (Keycode.Z, False), 'W': (Keycode.Z, True),
    'm': (Keycode.SEMICOLON, False), 'M': (Keycode.SEMICOLON, True), ',': (Keycode.M, False), '?': (Keycode.M, True),
    ';': (Keycode.COMMA, False), '.': (Keycode.COMMA, True), ':': (Keycode.PERIOD, False), '/': (Keycode.PERIOD, True),
    '!': (Keycode.FORWARD_SLASH, False), '§': (Keycode.FORWARD_SLASH, True), '-': (Keycode.SIX, False), '_' : (Keycode.EIGHT, False),
    '1': (Keycode.ONE, True), '2': (Keycode.TWO, True), '3': (Keycode.THREE, True), '4': (Keycode.FOUR, True),
    '5': (Keycode.FIVE, True), '6': (Keycode.SIX, True), '7': (Keycode.SEVEN, True), '8': (Keycode.EIGHT, True),
    '9': (Keycode.NINE, True), '0': (Keycode.ZERO, True), ' ': (Keycode.SPACE, False),
    '&': (Keycode.ONE, False), 'é': (Keycode.TWO, False), '"': (Keycode.THREE, False), "'": (Keycode.FOUR, False),
    '(': (Keycode.FIVE, False), 'è': (Keycode.SEVEN, False), 'ç': (Keycode.NINE, False), 'à': (Keycode.ZERO, False),
    ')': (Keycode.MINUS, False), '=': (Keycode.EQUALS, False)
}

# Map QWERTY standard
QW_PHYSICAL = {
    'a': (Keycode.A, False), 'A': (Keycode.A, True), 'q': (Keycode.Q, False), 'Q': (Keycode.Q, True),
    'z': (Keycode.Z, False), 'Z': (Keycode.Z, True), 'w': (Keycode.W, False), 'W': (Keycode.W, True),
    'm': (Keycode.M, False), 'M': (Keycode.M, True), ',': (Keycode.COMMA, False), '<': (Keycode.COMMA, True),
    '.': (Keycode.PERIOD, False), '>': (Keycode.PERIOD, True), '/': (Keycode.FORWARD_SLASH, False), '?': (Keycode.FORWARD_SLASH, True),
    ';': (Keycode.SEMICOLON, False), ':': (Keycode.SEMICOLON, True), "'": (Keycode.QUOTE, False), '"': (Keycode.QUOTE, True),
    '[': (Keycode.LEFT_BRACKET, False), '{': (Keycode.LEFT_BRACKET, True), ']': (Keycode.RIGHT_BRACKET, False), '}': (Keycode.RIGHT_BRACKET, True),
    '\\': (Keycode.BACKSLASH, False), '|': (Keycode.BACKSLASH, True), '-': (Keycode.MINUS, False), '_': (Keycode.MINUS, True),
    '=': (Keycode.EQUALS, False), '+': (Keycode.EQUALS, True),
    '1': (Keycode.ONE, False), '!': (Keycode.ONE, True), '2': (Keycode.TWO, False), '@': (Keycode.TWO, True),
    '3': (Keycode.THREE, False), '#': (Keycode.THREE, True), '4': (Keycode.FOUR, False), '$': (Keycode.FOUR, True),
    '5': (Keycode.FIVE, False), '%': (Keycode.FIVE, True), '6': (Keycode.SIX, False), '^': (Keycode.SIX, True),
    '7': (Keycode.SEVEN, False), '&': (Keycode.SEVEN, True), '8': (Keycode.EIGHT, False), '*': (Keycode.EIGHT, True),
    '9': (Keycode.NINE, False), '(': (Keycode.NINE, True), '0': (Keycode.ZERO, False), ')': (Keycode.ZERO, True),
    ' ': (Keycode.SPACE, False)
}

# Fonction qui simule la frappe au clavier
def send_text(text):
    layout = config.get("layout", "AZERTY")
    mapping = AZ_PHYSICAL if layout == "AZERTY" else QW_PHYSICAL
    
    for char in text:
        if char in mapping:
            code, use_shift = mapping[char]
            if use_shift: kbd.press(Keycode.SHIFT)
            kbd.press(code)
            kbd.release_all()
        else:
            # Fallback si le char n'est pas dans le dico (genre des majuscules basiques)
            is_cap = 'A' <= char <= 'Z'
            if is_cap: kbd.press(Keycode.SHIFT)
            try:
                if 'a' <= char.lower() <= 'z': kbd.press(getattr(Keycode, char.upper()))
            except AttributeError: pass
            kbd.release_all()
        time.sleep(0.015) # Petit delay pour eviter que l'OS rate des touches

# Dico des modifieurs et touches speciales
KEYMAP = {
    "A": Keycode.A, "B": Keycode.B, "C": Keycode.C, "D": Keycode.D, "E": Keycode.E, "F": Keycode.F, "G": Keycode.G,
    "H": Keycode.H, "I": Keycode.I, "J": Keycode.J, "K": Keycode.K, "L": Keycode.L, "M": Keycode.M, "N": Keycode.N,
    "O": Keycode.O, "P": Keycode.P, "Q": Keycode.Q, "R": Keycode.R, "S": Keycode.S, "T": Keycode.T, "U": Keycode.U,
    "V": Keycode.V, "W": Keycode.W, "X": Keycode.X, "Y": Keycode.Y, "Z": Keycode.Z,
    "1": Keycode.ONE, "2": Keycode.TWO, "3": Keycode.THREE, "4": Keycode.FOUR, "5": Keycode.FIVE, "6": Keycode.SIX,
    "7": Keycode.SEVEN, "8": Keycode.EIGHT, "9": Keycode.NINE, "0": Keycode.ZERO,
    "CTRL": Keycode.CONTROL, "SHIFT": Keycode.SHIFT, "ALT": Keycode.ALT, "GUI": Keycode.GUI,
    "ENTER": Keycode.ENTER, "SPACE": Keycode.SPACE, "ESC": Keycode.ESCAPE, "BACKSPACE": Keycode.BACKSPACE, "TAB": Keycode.TAB,
    "UP": Keycode.UP_ARROW, "DOWN": Keycode.DOWN_ARROW, "LEFT": Keycode.LEFT_ARROW, "RIGHT": Keycode.RIGHT_ARROW
}

# Parser et executeur d'action selon le JSON
def execute_action(action):
    val = action["value"]
    if action["type"] == "text":
        send_text(val)
    elif action["type"] == "shortcut":
        keys = []
        # On split le combo (ex: CTRL+C)
        for k in val.split('+'):
            k = k.strip().upper()
            # Hack pour adapter le raccourci si on est en AZERTY
            if config.get("layout") == "AZERTY" and len(k) == 1:
                if k == 'M': keys.append(Keycode.SEMICOLON); continue
                swap = {'A': 'Q', 'Q': 'A', 'Z': 'W', 'W': 'Z'}
                k = swap.get(k, k)
            if k in KEYMAP: keys.append(KEYMAP[k])
        if keys:
            try: kbd.press(*keys)
            except Exception: pass
    elif action["type"] == "launch":
        # Lancement d'app ou URL selon l'OS
        target_os = config.get("os", "windows")
        if target_os == "windows":
            # Win+R puis on tape la commande
            kbd.press(Keycode.GUI, Keycode.R); kbd.release_all(); time.sleep(0.4)
            send_text(val); time.sleep(0.1); kbd.press(Keycode.ENTER); kbd.release_all()
        elif target_os == "linux":
            if val.startswith("http"):
                # Alt+F2 sous linux (gnome) pour xdg-open
                kbd.press(Keycode.ALT, Keycode.F2); kbd.release_all(); time.sleep(0.4)
                send_text(f"xdg-open {val}"); time.sleep(0.2); kbd.press(Keycode.ENTER); kbd.release_all()
            else:
                # Appui sur Super (GUI) pour ouvrir la barre de recherche
                kbd.press(Keycode.GUI); kbd.release_all(); time.sleep(0.6)
                send_text(val); time.sleep(0.8); kbd.press(Keycode.ENTER); kbd.release_all()


buffer = ""

# --- MAIN LOOP ---
while True:
    now = time.monotonic()
    
    # Check si l'interface web nous envoie des trucs sur le port serie
    bytes_avail = supervisor.runtime.serial_bytes_available
    if bytes_avail > 0:
        buffer += sys.stdin.read(bytes_avail)
        
        # On lit ligne par ligne
        if '\n' in buffer:
            lines = buffer.split('\n')
            for line in lines[:-1]:
                data = line.strip()
                if data == "MODE:MAPPING":
                    current_mode = "MAPPING"
                    print("CURRENT_CONFIG:" + json.dumps(config))
                elif data == "MODE:MACRO":
                    current_mode = "MACRO"
                elif data.startswith("NEW_CONFIG:"):
                    json_str = data.replace("NEW_CONFIG:", "")
                    try:
                        new_cfg = json.loads(json_str)
                        # Mise a jour de la config en RAM
                        config["layout"] = new_cfg.get("layout", "AZERTY")
                        config["os"] = new_cfg.get("os", "windows")
                        config["keys"] = new_cfg.get("keys", {})
                        config["mapping"] = new_cfg.get("mapping", {})
                        
                        # Save sur la flash (on supprime l'ancien avant pour etre sur)
                        try: os.remove("/config.json")
                        except: pass
                        
                        with open("/config.json", "w") as f:
                            f.write(json.dumps(config))
                            f.flush()
                            
                        # On ne remet PAS current_mode = "MACRO" ici !
                        # Le clavier reste docile en mode MAPPING tant que la page web est connectée.
                        print("CONFIG_SAVED")
                    except Exception as e:
                        print("ERROR_JSON:", e) # Toujours utile pour debug le front
            
            buffer = lines[-1]

    # Polling des boutons avec un anti-rebond basique (20ms)
    for pin, btn in buttons.items():
        state = not btn.value # pulled up, donc True quand on appuie (0V)
        if state != last_state[pin] and (now - last_debounce_time[pin] > 0.02):
            last_debounce_time[pin] = now
            last_state[pin] = state
            
            if state: # Front montant (appui)
                if current_mode == "MAPPING":
                    # On notifie le front-end de quel bouton a ete presse
                    print(f"PIN_PRESSED:{pin}")
                elif current_mode == "MACRO":
                    # On lance la sauce
                    action = config.get("keys", {}).get(str(pin))
                    if action and action.get("value"):
                        execute_action(action)
            else: 
                # Front descendant (relachement), on reset le clavier
                if current_mode == "MACRO":
                    kbd.release_all()