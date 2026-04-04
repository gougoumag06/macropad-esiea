# ==============================================================================
# boot.py — CE FICHIER S'EXÉCUTE EN PREMIER, AVANT TOUT LE RESTE
# il vérifie que le fichier de config n'est pas corrompu.
# Si c'est le cas, il essaie de le réparer automatiquement depuis une sauvegarde.
# ==============================================================================

import storage        #pour gérer les droits de lecture/écriture du stockage
import os             #pour naviguer dans les fichiers et dossiers
import json           #pour lire et écrire des fichiers au format JSON
import microcontroller  # Outil pour contrôler la RP2040zero

# adresse du fichier de sauvegarde (backup) 
BACKUP_PATH = "/backup/config.json"

# adresse du fichier principal
MAIN_PATH = "/config.json"


def check_integrity(path):
    """
    Vérifie si un fichier JSON existe ET est lisible (non corrompu).
    - path : le chemin du fichier à vérifier (ex: "/config.json")
    - Retourne True si tout va bien, False si le fichier est absent ou cassé.
    """

    try:
        parts = path.split("/")        
        filename = parts[-1]           
        directory = "/".join(parts[:-1]) if "/" in path else "/"

        # Vérifier que le fichier existe dans le dossier 
        # os.listdir() liste tous les fichiers d'un dossier
        if filename not in os.listdir(directory):
            return False  
        
        #Essayer d'ouvrir ET de lire le fichier JSON 
        with open(path, "r") as f:  
            json.load(f)           
        return True  
    except Exception:
        return False  # Le fichier est corrompu ou illisible


def perform_recovery():
    """
    Restaure le fichier principal config.json à partir de la sauvegarde.
    """
    try:
        # droit d'ecriture temporaire pour réparer le fichier
        storage.remount("/", readonly=False) 

        if "backup" not in os.listdir("/"):   
            os.mkdir("/backup")               

        #Lire le contenu du fichier de sauvegarde 
        with open(BACKUP_PATH, "r") as src:   
            data = src.read()                

        # Écrire ce contenu dans le fichier principal
        with open(MAIN_PATH, "w") as dest:   
            dest.write(data)                  # Écrase l'ancien contenu 

        # redemarage
        print("Restauration reussie. Redemarrage...")
        microcontroller.reset() 

    except Exception as e:
        print(f"Erreur fatale : {e}")



if not check_integrity(MAIN_PATH):

    if check_integrity(BACKUP_PATH):
        perform_recovery()  

storage.remount("/", readonly=True) 