## Détails d'installation pas à pas

Voici la procédure détaillée pour configurer les fichiers internes de votre clavier :

### 1. Flash du microcontrôleur (`piper_circuitpython.uf2`)
Cette étape est indispensable et doit être réalisée en premier. Elle sert à installer le système sur la carte **RP2040-Zero**.
* Glissez simplement le fichier `piper_circuitpython.uf2` à la racine de votre carte.
* *Note : La RP2040-Zero va redémarrer automatiquement et les fichiers de base apparaîtront*

### 2. Ajout des dépendances (`adafruit_hid.zip`)
Une fois le système installé (l'étape 1 terminée) et le lecteur `CIRCUITPY` apparu :
* Extrayez l'archive `adafruit_hid.zip`.
* Placez les fichiers obtenus dans le dossier `/lib` du lecteur `CIRCUITPY`. *(Créez le dossier s'il n'existe pas).*

### 3. Installation de l'application de paramétrage (`app`)
Il s'agit de l'application Web visuelle qui vous permettra de configurer facilement les touches de votre macropad.
* Récupérez l'intégralité du contenu présent dans le dossier `app`.
* Copiez tout ce contenu directement à la racine du lecteur `CIRCUITPY`.

###Une fois tout installé, vous devriez avoir ça :
[Aperçu des fichiers apres avoir tout installé](/assets/images/capture.png)
