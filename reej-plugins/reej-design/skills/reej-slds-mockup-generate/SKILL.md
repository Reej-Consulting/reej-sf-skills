---
name: reej-slds-mockup-generate
description: "Génère une maquette HTML statique et autonome (un seul fichier, SLDS chargé depuis le CDN, aucune dépendance LWC/Apex) d'un écran Salesforce Lightning — page d'enregistrement, liste, console, écran de flow ou composant — à partir d'une description fonctionnelle, pour l'avant-vente, les ateliers de conception et les revues de design Reej. TRIGGER when: l'utilisateur demande une maquette, un mockup, un wireframe haute fidélité, une « capture » ou un rendu visuel d'un écran Salesforce ; veut montrer à un client à quoi ressemblerait une page, un onglet, un composant ou un parcours ; mentionne 'maquette SLDS', 'mockup Lightning', 'écran de démo HTML'. DO NOT TRIGGER when: l'utilisateur développe un vrai composant LWC, Aura ou une page Experience Cloud déployable (utiliser experience-lwc-generate et design-systems-slds-apply) ; veut auditer ou migrer du SLDS existant (design-systems-slds-validate / slds2-migrate) ; demande un schéma d'architecture ou un diagramme (external-diagram-mermaid-generate)."
metadata:
  version: "0.1"
  owner: "Reej Consulting"
  domains: ["Design", "Avant-vente"]
  relatedSkills:
    - "design-systems-slds-apply"
    - "experience-lwc-generate"
---

<!-- TODO (auteur du skill) : remplacer chaque TODO par le contenu réel, puis supprimer ce commentaire.
     Rappels : ce fichier est une instruction POUR Claude, pas une doc pour l'utilisateur.
     Style impératif, concret, pas de généralités. Le corps doit rester < 3 000 mots ;
     tout ce qui est long (catalogue de composants, règles détaillées) va dans references/. -->

# Maquette HTML SLDS — Reej

## Objectif

Produire une maquette HTML **d'un seul fichier**, ouvrable dans un navigateur sans serveur ni build, qui ressemble fidèlement à Salesforce Lightning Experience, pour illustrer une proposition fonctionnelle. La maquette n'est pas du code livrable : elle sert à faire réagir un client ou un atelier.

## Entrées à collecter avant de produire

Vérifier que l'on dispose de ces éléments ; sinon, poser **une seule question groupée** à l'utilisateur :

1. Type d'écran : page d'enregistrement (record page), liste (list view), page d'accueil, console Service, écran de flow, composant isolé, parcours multi-écrans.
2. Objet(s) et champs à montrer, avec des **valeurs d'exemple réalistes** dans le contexte du client (pas de « Lorem ipsum », pas de « Test 1 »).
3. Éléments spécifiques à mettre en avant (le composant ou la fonctionnalité qui fait l'objet de la proposition).
4. Langue de l'interface (français par défaut) et éventuel nom / logo client à afficher.

## Procédure

1. Charger `references/slds-components.md` pour choisir les blueprints SLDS adaptés à chaque zone de l'écran.
2. Partir du gabarit `assets/template.html` (shell Lightning : barre d'app, navigation, zone de contenu) et ne modifier que la zone de contenu, sauf demande contraire.
3. Construire l'écran avec les classes SLDS officielles (`slds-page-header`, `slds-card`, `slds-form-element`, `slds-table`, `slds-tabs_default`, etc.) — TODO : lister ici les 5-10 blueprints les plus utilisés chez Reej et les pièges connus.
4. Mettre en évidence l'élément proposé : TODO — convention Reej (bandeau, pastille « Nouveau », encadré de couleur ?).
5. Vérifier avant de livrer : un seul fichier `.html`, SLDS chargé depuis le CDN (TODO : URL et version retenues), aucune ressource locale, rendu correct à 1366 px de large, textes en français sans faute, aucune donnée client réelle (valeurs inventées mais plausibles).
6. Livrer le fichier et résumer en 3 lignes ce que montre la maquette et ce qui est volontairement simplifié.

## Règles

- Ne jamais présenter la maquette comme un composant déployable ; le dire explicitement si l'utilisateur semble le croire.
- Rester dans le vocabulaire Lightning Experience (pas de Classic), SLDS 2 si disponible — TODO : préciser la version SLDS de référence Reej.
- Si la demande porte en réalité sur un composant LWC réel, rediriger vers `experience-lwc-generate` et `design-systems-slds-apply` plutôt que de produire une maquette.

## Références

- `references/slds-components.md` — catalogue des blueprints utilisés et exemples de markup (TODO : à fournir).
- `assets/template.html` — shell Lightning de base (TODO : à fournir).
- `assets/exemples/` — une ou deux maquettes livrées comme référence de niveau de qualité attendu (TODO).
