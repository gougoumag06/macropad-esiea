# ==============================================================================
# code.py — cerveau du macropad
# C'est ce fichier tourne tout le temps 
# Il surveille les boutons et envoie les actions au PC quand on appuie.
# ==============================================================================

import board        # Accès aux broches 
import digitalio    #lit l'état des boutons (appuyé / relâché)
import time       
import json       
import os         
import usb_hid      # Active le mode "périphérique USB HID" (clavier/souris)
from adafruit_hid.keyboard import Keyboard  # Simule un clavier USB
from adafruit_hid.keycode import Keycode    # Contient les codes de toutes les touches


# dictionnaire qui mappe les numéros de boutons (3, 4, 5...) à leurs broches GPIO correspondantes
PIN_MAPPING = {
    3: board.GP3,
    4: board.GP4,
    5: board.GP5,
    6: board.GP6,
    7: board.GP7,
    8: board.GP8,
}

buttons = {}            
last_state = {}          
last_debounce_time = {}  

# On initialise chaque bouton défini dans PIN_MAPPING
for pin, gp in PIN_MAPPING.items():
    btn = digitalio.DigitalInOut(gp)          
    btn.direction = digitalio.Direction.INPUT 
    btn.pull = digitalio.Pull.UP             
    buttons[pin] = btn          
    last_state[pin] = False     
    last_debounce_time[pin] = 0

kbd = Keyboard(usb_hid.devices)

# Configuration par défaut si aucun fichier JSON n'est trouvé
config = {
    "layout": "AZERTY",  # Disposition du clavier (AZERTY ou QWERTY)
    "os": "windows",     # Système d'exploitation cible
    "keys": {},          # Actions associées à chaque bouton (vide par défaut)
    "mapping": {},       # Correspondance bouton → numéro de broche GPIO
}


def load_config():
    """Lit le fichier /config.json et met à jour la variable 'config'."""
    global config  
    try:
        with open("/config.json", "r") as f:  # Ouvre le fichier en lecture
            config = json.load(f)             
            print("Configuration chargee.")
    except Exception:
        print("Fichier illisible...")

load_config()

# On mémorise la taille du fichier. Si elle change, c'est que le fichier a été modifié
try:
    last_file_size = os.stat("/config.json")[6]  
except Exception:
    last_file_size = 0  

last_check = time.monotonic()  



# Correspondance entre nom lisible et code HID réel des touches. Ex: "CTRL" → Keycode.CONTROL
KEYMAP = {
    "A": Keycode.A,         "B": Keycode.B,         "C": Keycode.C,
    "D": Keycode.D,         "E": Keycode.E,         "F": Keycode.F,
    "G": Keycode.G,         "H": Keycode.H,         "I": Keycode.I,
    "J": Keycode.J,         "K": Keycode.K,         "L": Keycode.L,
    "M": Keycode.M,         "N": Keycode.N,         "O": Keycode.O,
    "P": Keycode.P,         "Q": Keycode.Q,         "R": Keycode.R,
    "S": Keycode.S,         "T": Keycode.T,         "U": Keycode.U,
    "V": Keycode.V,         "W": Keycode.W,         "X": Keycode.X,
    "Y": Keycode.Y,         "Z": Keycode.Z,
    "1": Keycode.ONE,       "2": Keycode.TWO,       "3": Keycode.THREE,
    "4": Keycode.FOUR,      "5": Keycode.FIVE,      "6": Keycode.SIX,
    "7": Keycode.SEVEN,     "8": Keycode.EIGHT,     "9": Keycode.NINE,
    "0": Keycode.ZERO,
    "CTRL":      Keycode.CONTROL,   # Touche Contrôle
    "SHIFT":     Keycode.SHIFT,     # Touche Majuscule
    "ALT":       Keycode.ALT,       # Touche Alt
    "GUI":       Keycode.GUI,       # Touche Windows (ou Cmd sur Mac)
    "ENTER":     Keycode.ENTER,     # Touche Entrée
    "SPACE":     Keycode.SPACE,     # Barre espace
    "ESC":       Keycode.ESCAPE,    # Touche Échap
    "BACKSPACE": Keycode.BACKSPACE, # Touche Retour arrière
    "TAB":       Keycode.TAB,       # Touche Tabulation
    "UP":        Keycode.UP_ARROW,  # Flèche haut
    "DOWN":      Keycode.DOWN_ARROW,# Flèche bas
    "LEFT":      Keycode.LEFT_ARROW,# Flèche gauche
    "RIGHT":     Keycode.RIGHT_ARROW,# Flèche droite
}

# --- Correspondances physiques AZERTY ---
AZ_PHYSICAL = {
    'a': (Keycode.Q, False),            
    'A': (Keycode.Q, True),            
    'q': (Keycode.A, False),           
    'Q': (Keycode.A, True),
    'z': (Keycode.W, False),
    'Z': (Keycode.W, True),
    'w': (Keycode.Z, False),
    'W': (Keycode.Z, True),
    'm': (Keycode.SEMICOLON, False),
    'M': (Keycode.SEMICOLON, True),
    ',': (Keycode.M, False),
    '?': (Keycode.M, True),
    ';': (Keycode.COMMA, False),
    '.': (Keycode.COMMA, True),
    ':': (Keycode.PERIOD, False),
    '/': (Keycode.PERIOD, True),
    '!': (Keycode.FORWARD_SLASH, False),
    '§': (Keycode.FORWARD_SLASH, True),
    '-': (Keycode.SIX, False),
    '_': (Keycode.EIGHT, False),
    '1': (Keycode.ONE, True),           
    '2': (Keycode.TWO, True),
    '3': (Keycode.THREE, True),
    '4': (Keycode.FOUR, True),
    '5': (Keycode.FIVE, True),
    '6': (Keycode.SIX, True),
    '7': (Keycode.SEVEN, True),
    '8': (Keycode.EIGHT, True),
    '9': (Keycode.NINE, True),
    '0': (Keycode.ZERO, True),
    ' ': (Keycode.SPACE, False),
    '&': (Keycode.ONE, False),          
    'é': (Keycode.TWO, False),
    '"': (Keycode.THREE, False),
    "'": (Keycode.FOUR, False),
    '(': (Keycode.FIVE, False),
    'è': (Keycode.SEVEN, False),
    'ç': (Keycode.NINE, False),
    'à': (Keycode.ZERO, False),
    ')': (Keycode.MINUS, False),
    '=': (Keycode.EQUALS, False),
}

# --- Correspondances physiques QWERTY ---
QW_PHYSICAL = {
    'a': (Keycode.A, False),            'A': (Keycode.A, True),
    'q': (Keycode.Q, False),            'Q': (Keycode.Q, True),
    'z': (Keycode.Z, False),            'Z': (Keycode.Z, True),
    'w': (Keycode.W, False),            'W': (Keycode.W, True),
    'm': (Keycode.M, False),            'M': (Keycode.M, True),
    ',': (Keycode.COMMA, False),        '<': (Keycode.COMMA, True),
    '.': (Keycode.PERIOD, False),       '>': (Keycode.PERIOD, True),
    '/': (Keycode.FORWARD_SLASH, False),'?': (Keycode.FORWARD_SLASH, True),
    ';': (Keycode.SEMICOLON, False),    ':': (Keycode.SEMICOLON, True),
    "'": (Keycode.QUOTE, False),        '"': (Keycode.QUOTE, True),
    '[': (Keycode.LEFT_BRACKET, False), '{': (Keycode.LEFT_BRACKET, True),
    ']': (Keycode.RIGHT_BRACKET, False),'}': (Keycode.RIGHT_BRACKET, True),
    '\\': (Keycode.BACKSLASH, False),   '|': (Keycode.BACKSLASH, True),
    '-': (Keycode.MINUS, False),        '_': (Keycode.MINUS, True),
    '=': (Keycode.EQUALS, False),       '+': (Keycode.EQUALS, True),
    '1': (Keycode.ONE, False),          '!': (Keycode.ONE, True),
    '2': (Keycode.TWO, False),          '@': (Keycode.TWO, True),
    '3': (Keycode.THREE, False),        '#': (Keycode.THREE, True),
    '4': (Keycode.FOUR, False),         '$': (Keycode.FOUR, True),
    '5': (Keycode.FIVE, False),         '%': (Keycode.FIVE, True),
    '6': (Keycode.SIX, False),          '^': (Keycode.SIX, True),
    '7': (Keycode.SEVEN, False),        '&': (Keycode.SEVEN, True),
    '8': (Keycode.EIGHT, False),        '*': (Keycode.EIGHT, True),
    '9': (Keycode.NINE, False),         '(': (Keycode.NINE, True),
    '0': (Keycode.ZERO, False),         ')': (Keycode.ZERO, True),
    ' ': (Keycode.SPACE, False),
}

# Conversion des lettres pour les RACCOURCIS en AZERTY
AZERTY_TO_QWERTY = {
    'A': 'Q',   # La touche physique "A" (AZERTY) = emplacement "Q" en QWERTY
    'Q': 'A',   # La touche physique "Q" (AZERTY) = emplacement "A" en QWERTY
    'Z': 'W',   # La touche physique "Z" (AZERTY) = emplacement "W" en QWERTY
    'W': 'Z',   # La touche physique "W" (AZERTY) = emplacement "Z" en QWERTY
}


def send_text(text):
    """
    Tape une chaîne de caractères lettre par lettre via le clavier virtuel HID.
    Gère automatiquement les différences AZERTY/QWERTY.
    """
    mapping = AZ_PHYSICAL if config.get("layout", "AZERTY") == "AZERTY" else QW_PHYSICAL

    for char in text:  
        if char in mapping:
            code, use_shift = mapping[char]  
            if use_shift:
                kbd.press(Keycode.SHIFT) 
            kbd.press(code)              
            kbd.release_all()            
        else:

            if 'A' <= char <= 'Z':     
                kbd.press(Keycode.SHIFT) 
            try:
                if 'a' <= char.lower() <= 'z':  
                    kbd.press(getattr(Keycode, char.upper()))
            except AttributeError:
                pass  
            kbd.release_all()

        time.sleep(0.015) 


def execute_action(action):
    """
    Exécute l'action assignée à une touche du macropad.
    Il existe 3 types d'actions : 'text', 'shortcut', 'launch'.
    - action : un dictionnaire avec les clés "type" et "value"
    """
    action_type = action["type"]   
    val = action["value"]        

    if action_type == "text":
        send_text(val)  

    # raccourci clavier
    elif action_type == "shortcut":
        keys = [] 

        for k in val.split('+'):
            k = k.strip().upper()  
            if config.get("layout") == "AZERTY" and len(k) == 1:
                if k == 'M':
                    keys.append(Keycode.SEMICOLON)
                    continue  
                k = AZERTY_TO_QWERTY.get(k, k)  

            if k in KEYMAP:
                keys.append(KEYMAP[k])  
        if keys:
            try:
                kbd.press(*keys)   #Appuie sur toutes les touches du raccourci en même temps
            except Exception:
                pass  

    # lancer une application ou une URL 
    elif action_type == "launch":
        if config.get("os", "windows") == "windows":
            # Sur Windows : on utilise Win+R pour lancer l'application
            kbd.press(Keycode.GUI, Keycode.R) 
            kbd.release_all()
            time.sleep(0.3)    
            send_text(val)     
            time.sleep(0.1)
            kbd.press(Keycode.ENTER)   
            kbd.release_all()
        else:
            # Sur Linux : deux cas selon si c'est une URL ou une application
            if val.startswith("http"):
                # URL → on utilise Alt+F2 (lanceur de commande) + xdg-open pour ouvrir dans le navigateur
                kbd.press(Keycode.ALT, Keycode.F2)
                kbd.release_all()
                time.sleep(0.4)
                send_text(f"xdg-open {val}") 
                time.sleep(0.2)
                kbd.press(Keycode.ENTER)
                kbd.release_all()
            else:
                # Application → on ouvre le lanceur et on tape le nom
                kbd.press(Keycode.GUI)
                kbd.release_all()
                time.sleep(0.6)    
                send_text(val)     
                time.sleep(0.8)    
                kbd.press(Keycode.ENTER)
                kbd.release_all()



start_time = time.monotonic()  

while True: 
    now = time.monotonic()  

    if now - last_check > 2.0:
        last_check = now  
        try:
            current_size = os.stat("/config.json")[6]  
            if current_size != last_file_size:
                time.sleep(1.0)    
                load_config()      
                last_file_size = current_size  
        except Exception:
            pass  

  
    for pin, btn in buttons.items(): 
        state = not btn.value 
        if state != last_state[pin]:  
            if now - last_debounce_time[pin] > 0.05: 
                last_debounce_time[pin] = now      
                last_state[pin] = state            

                if state:
                    # Ignore les appuis pendant les 3 premières secondes du démarrage
                    if now - start_time < 3.0:
                        continue 

                    action = config.get("keys", {}).get(str(pin))

                    if action and action.get("value"):
                        execute_action(action) 

                else:
                    kbd.release_all() 

