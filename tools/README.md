# RUSH RIVALS — environnement Blender gratuit

Ce dossier contient un générateur procédural de décor 3D. Il utilise uniquement l'API intégrée de Blender : aucun plugin payant, aucune bibliothèque externe et aucun crédit IA.

## Générer la scène

1. Installer Blender 3.6 ou une version plus récente : https://www.blender.org/download/
2. Télécharger le dépôt GitHub ou cloner le projet.
3. Depuis le dossier du projet, lancer :

```bash
blender --background --python tools/build_rush_rivals_scene.py
```

Le script crée automatiquement le dossier `assets/` et produit :
- `assets/rush-rivals-world.blend` : scène Blender modifiable.
- `assets/rush-rivals-world.glb` : export glTF binaire destiné à Three.js.

## Contenu de la scène

- Piste fermée avec virages et variations d'altitude.
- Rubans d'asphalte, marquages, bordures et rails lumineux.
- Arche de départ, deux arches de checkpoint et entrée de tunnel.
- Skyline futuriste, reliefs lointains, lampadaires et panneaux de piste.
- Matériaux PBR avec accents cyan, magenta et ambre.

## Intégration au jeu

Le GLB est un nouvel asset de décor, pas encore branché automatiquement dans `index.html`. Pour l'intégrer, il faudra le placer dans `assets/`, charger le modèle avec `GLTFLoader`, puis aligner la voiture, la caméra, les collisions et les points de progression sur la géométrie exportée. Il faudra également tester les performances sur téléphone avant d'activer ce décor par défaut.
