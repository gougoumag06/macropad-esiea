# Détails :

- piper_circuitpython.uf2  
A faire en premier, sert à flasher la RP2040zero, le déplacer à la racine. *(la RP2040zero redémarrera et les fichiers suivants vont apparaitre (voir image))* 
![capture](/assets/images/capture.png)

- adafruit_hid.zip  
Fichier à mettre dans le dossier /lib du RP2040zero, après avoir installé l'uf2.

- Code.py  
Programme qui contient la logique du clavier, l'attribution des actions des différentes touches et un dictionnaire de querty vers azerty *(la librairie utilisée est en querty)*.

