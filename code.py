import board
import digitalio
import usb_hid
import time
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

kbd = Keyboard(usb_hid.devices)

# Dictionnaire de correspondance pour les caractères AZERTY
AZ_PHYSICAL = {
    'a': (Keycode.Q, False), 'A': (Keycode.Q, True),
    'q': (Keycode.A, False), 'Q': (Keycode.A, True),
    'z': (Keycode.W, False), 'Z': (Keycode.W, True),
    'w': (Keycode.Z, False), 'W': (Keycode.Z, True),
    'm': (Keycode.SEMICOLON, False), 'M': (Keycode.SEMICOLON, True),
    ',': (Keycode.M, False), '?': (Keycode.M, True),
    ';': (Keycode.COMMA, False), '.': (Keycode.COMMA, True),
    ':': (Keycode.PERIOD, False), '/': (Keycode.PERIOD, True),
    '!': (Keycode.FORWARD_SLASH, False), '§': (Keycode.FORWARD_SLASH, True),
    '-': (Keycode.SIX, False), '_' : (Keycode.EIGHT, False),
    '1': (Keycode.ONE, True), '2': (Keycode.TWO, True), '3': (Keycode.THREE, True), 
    '4': (Keycode.FOUR, True), '5': (Keycode.FIVE, True), '6': (Keycode.SIX, True), 
    '7': (Keycode.SEVEN, True), '8': (Keycode.EIGHT, True), '9': (Keycode.NINE, True), 
    '0': (Keycode.ZERO, True), ' ': (Keycode.SPACE, False),
    '&': (Keycode.ONE, False), 'é': (Keycode.TWO, False), '"': (Keycode.THREE, False), 
    "'": (Keycode.FOUR, False), '(': (Keycode.FIVE, False), 'è': (Keycode.SEVEN, False), 
    'ç': (Keycode.NINE, False), 'à': (Keycode.ZERO, False), ')': (Keycode.MINUS, False), 
    '=': (Keycode.EQUALS, False)
}

# on definit les pins des boutons, ici GP3 à GP8 pour 6 boutons
pin_numbers = [board.GP3, board.GP4, board.GP5, board.GP6, board.GP7, board.GP8]

buttons = []
for pin in pin_numbers:
    btn = digitalio.DigitalInOut(pin)
    btn.direction = digitalio.Direction.INPUT
    btn.pull = digitalio.Pull.UP
    buttons.append(btn)

# On définit ici ce que chaque bouton doit écrire (caractères AZERTY)
keymap_chars = ['4', '5', '6', '1', '2', '3']

def send_azerty_char(char):
    """Envoie un caractère AZERTY en utilisant le mapping défini.
    """
    if char in AZ_PHYSICAL:
        keycode, shift_required = AZ_PHYSICAL[char]
        if shift_required:
            kbd.press(Keycode.SHIFT)
        kbd.press(keycode)
        kbd.release_all() 
    else:
        # Si le caractère n'est pas dans le dico, on peut tenter de l'envoyer brut
        # ou ne rien faire pour éviter les erreurs.
        pass
#
last_states = [True] * len(buttons)

while True:
    for i, button in enumerate(buttons):
        current_state = button.value
        if current_state != last_states[i]:
            if not current_state: # Appui
                send_azerty_char(keymap_chars[i])
            last_states[i] = current_state
            
    time.sleep(0.01)