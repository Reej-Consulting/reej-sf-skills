# Contribuer un skill Reej

Ce repo contient deux familles de plugins qui ne se gèrent pas pareil :

- `plugins/sf-*` — **miroir de Salesforce**, régénéré chaque nuit par `scripts/sync.py`. **Ne jamais y éditer quoi que ce soit** : toute modification serait écrasée à la synchro suivante. Un problème dans un skill Salesforce se remonte sur [forcedotcom/sf-skills](https://github.com/forcedotcom/sf-skills).
- `reej-plugins/reej-*` — **skills maison Reej**, écrits et maintenus par nous. C'est ici que l'on contribue.

## Ce qu'est un skill

Un dossier avec un `SKILL.md` (instructions que Claude suit quand le sujet s'y prête) et, au besoin, `references/` (doc longue chargée à la demande), `assets/` (gabarits, exemples) et `scripts/`. Le `SKILL.md` s'adresse **à Claude, pas à l'utilisateur** : impératif, concret, pas de généralités. Les skills Salesforce dans `plugins/` sont de bons modèles de structure.

La partie la plus importante est la `description` du frontmatter : c'est elle qui décide si le skill se déclenche. Elle doit dire **quand l'utiliser** (phrases typiques, mots-clés) **et quand ne pas l'utiliser**, en nommant le skill à utiliser à la place. Toujours vérifier qu'un skill Salesforce voisin n'existe pas déjà : s'il existe, le skill Reej doit se distinguer nettement ou se contenter de le compléter.

## Règles

1. Préfixe `reej-` sur le nom du plugin **et** de chaque skill (`reej-design`, `reej-slds-mockup-generate`) — garantit qu'on n'entrera jamais en collision avec un futur skill Salesforce.
2. Noms en kebab-case, `name` du frontmatter identique au nom du dossier.
3. Pas de données client réelles, pas de secrets, pas d'URL interne dans un skill : le repo est public.
4. Corps du `SKILL.md` sous ~3 000 mots ; le reste dans `references/`.
5. Un skill = un usage. Deux usages distincts = deux skills.

## Procédure

1. Créer une branche depuis `main`.
2. Ajouter le skill sous `reej-plugins/<plugin>/skills/<reej-nom-du-skill>/`. Pour un nouveau plugin, copier la structure de `reej-plugins/reej-design/` (le `plugin.json` est obligatoire).
3. Incrémenter `version` dans `reej-plugins/<plugin>/.claude-plugin/plugin.json` (semver : correctif → patch, nouveau skill → minor). **Sans ça, les postes déjà installés ne verront pas la mise à jour.**
4. Régénérer le marketplace : `python3 scripts/sync.py --marketplace-only` puis `python3 scripts/validate.py` (les deux doivent passer).
5. Tester localement avant la PR : dans Claude Code, `/plugin` → Marketplaces → ajouter le **chemin local** du repo comme marketplace, installer le plugin, vérifier que le skill se déclenche sur 2-3 prompts attendus et **ne se déclenche pas** sur 2 prompts voisins.
6. Ouvrir une PR vers `main` avec, dans la description : à quoi sert le skill, les prompts testés, et si un skill Salesforce voisin existe, pourquoi celui-ci s'en distingue. Le workflow *Validate marketplace* doit être vert.
7. Après merge, prévenir l'équipe (canal Slack de la practice) : nom du plugin à mettre à jour.

## Après le merge, côté utilisateurs

Rien n'est automatique : chacun doit faire *Update* du marketplace `reej-salesforce` puis *Update* du plugin `reej-…` (dans `/plugin` pour Claude Code, dans Paramètres → Plugins pour Cowork). D'où l'importance du message d'annonce.
