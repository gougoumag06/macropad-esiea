# Glyphie

**Qu'est ce que c'est ?**

Glyphie est un mini clavier de 6 touches créé par notre équipe.  
Il permet de vous faire gagner du temps au quotidien en assignant des actions spécifiques à chacune de ses touches (des raccourcis, des phrases automatiques ou l'ouverture de logiciels).

![kesiea](/assets/images/kesiea.jpg)

**Pourquoi ?**

Cette création s'inscrit dans un projet à impact RSE : [leHack Kids](https://lehack.org/fr/lehack-kids/), mené par notre équipe tout au long de notre deuxième année d'école d'ingénieur (ESIEA). 
LeHack Kids est un évènement qui se tient en même temps que le salon [leHack](https://lehack.org/fr/) à Paris et permet à des jeunes de découvrir l'univers des sciences, de la technologie et de l'informatique à travers plusieurs activités. 

Ce mini clavier est le fruit de notre travail pour le salon de 2026 qui regroupera plusieurs domaines. Adapté à toutes les tranches d'âge, l'objectif est de faire construire le mini clavier aux jeunes de A à Z, que ce soit l'assemblage, l'électronique, la programmation et son utilisation dans une activité type mini-jeu.

---

## 1. Montage et Installation

Si vous souhaitez fabriquer ce clavier vous-même, tous les fichiers nécessaires au projet sont fournis dans ce dépôt (la notice de montage étape par étape et les plans 3D pour l'impression du boîtier).

**Matériel requis :**
- 1 carte microcontrôleur **RP2040-Zero**
- 6 switchs (boutons) de clavier mécanique
- Des câbles ou fils électriques fins
- Un poste à souder et de l'étain
- Une imprimante 3D (pour le boîtier extérieur et les capuchons des touches)

**Câblage des touches :**
 
| Touche | Broche Pico |
|--------|-------------|
| Touche 1 | GP3 |
| Touche 2 | GP4 |
| Touche 3 | GP5 |
| Touche 4 | GP6 |
| Touche 5 | GP7 |
| Touche 6 | GP8 |

**Installation du code :**
Une fois le montage physique terminé, il faut installer le système sur la carte. Voici la marche à suivre :

1. **Installer le firmware (fichier UF2) :** Branchez la carte RP2040-Zero à votre ordinateur. Elle va apparaître comme une clé USB classique. Glissez à l'intérieur le fichier `.uf2` (CircuitPython) pour installer le système de base. La carte va redémarrer automatiquement et réapparaître sous le nom `CIRCUITPY`.
2. **Ajouter les bibliothèques :** Prenez le dossier `lib` fourni dans le projet et glissez-le directement à la racine de la carte `CIRCUITPY`.
3. **Ajouter le programme principal :** Récupérez tout le contenu du dossier `software` présent sur ce répertoire Git (les fichiers `.py`, `config.json`, etc.) et copiez-le également à la racine de la carte RP2040.

C'est prêt ! 

---

## 2. Utilisation et Configuration

Le clavier fonctionne tout de suite, sans avoir besoin d'installer de logiciel sur votre PC. Branchez-le et c'est parti (compatible Windows, Linux).
*Note : Par sécurité, quand vous branchez le clavier, les touches sont désactivées pendant les 3 premières secondes pour éviter de déclencher une action par erreur.*

### Que peuvent faire les touches ?
Chaque touche peut être programmée pour exécuter 3 types d'actions :
* **Un raccourci clavier (`shortcut`) :** Pratique pour faire un `CTRL + C`, ou verrouiller le PC (`Windows + L`).
* **Taper du texte (`text`) :** Le clavier écrit une phrase entière à votre place.
* **Lancer un programme (`launch`) :** Ouvre une application ou un site web (`https://youtube.com`).

### Comment paramétrer les touches ?

Il y a deux méthodes pour personnaliser votre clavier, selon votre système d'exploitation et vos préférences.

#### Méthode A : Avec l'application Web (Recommandé)
Nous avons créé une interface visuelle pour configurer le clavier très facilement. *(Une fois configuré sous Windows, le clavier fonctionnera parfaitement sur Linux).*

1. Branchez le clavier à votre ordinateur.
2. Ouvrez le fichier `index.html`  present sur le peripherique `CIRCUITPY` avec un navigateur basé sur Chromium (**Google Chrome, Edge, Brave ou Opera**). *Safari et Firefox ne sont pas compatibles
3. Cliquez sur le bouton **Ouvrir config.json** en haut à droite et sélectionnez le fichier `config.json` situé à la racine de votre clavier (le lecteur nommé `CIRCUITPY`).
4. Cliquez visuellement sur la touche que vous voulez modifier directement sur l'interface de la page web.
5. Choisissez l'action souhaitée (Raccourci, Texte ou Lancement d'application/URL) et configurez-la.
6. Cliquez sur **SAUVEGARDER SUR LE CLAVIER**. 
7. **⚠️ IMPORTANT :** Une fois la sauvegarde terminée, vous **devez éjecter proprement le périphérique** (`CIRCUITPY`) depuis Windows/Linux avant de débrancher le clavier. Sans cette étape, le système d'exploitation risque de corrompre votre configuration !

#### Méthode B : Directement via le fichier JSON (Pour les bidouilleurs)
Vous pouvez configurer vos touches en modifiant directement le fichier interne du clavier. Le clavier s'affiche en permanence sur votre PC comme une clé USB classique.

1. Branchez le câble USB sur l'ordinateur.
2. Ouvrez le lecteur `CIRCUITPY` (qui s'affiche comme une clé USB) et ouvrez le fichier `config.json` avec votre éditeur de texte ou de code préféré.
3. Modifiez vos macros dans la partie `"keys"` (des textes d'aide sont inclus dans le fichier pour vous guider).
4. Sauvegardez le fichier (`CTRL + S`).
5. **Éjectez proprement le lecteur** depuis votre système d'exploitation.
6. Le clavier lit sa configuration en continu : il détectera la mise à jour de la sauvegarde et rechargera automatiquement vos nouvelles touches sans même avoir besoin de le débrancher !

---

## Remarques et améliorations possibles

Ce projet va continuer d'évoluer. Voici nos pistes d'amélioration :
* **Utilisation d'un PCB :** Créer notre propre circuit imprimé pour simplifier le montage et éviter de souder les câbles un par un.
* **Développer un site web en ligne :** Héberger le fichier `index.html` sur internet pour que les utilisateurs n'aient plus besoin de le télécharger localement pour configurer leur clavier.
