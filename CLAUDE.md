# reej-sf-skills — contexte projet pour Claude Code

## Ce qu'est ce repo

Marketplace de plugins Claude (`reej-salesforce`) pour la practice Salesforce de Reej Consulting. Il sert deux familles de plugins, installables dans Claude Code (`/plugin`) et Cowork :

- `plugins/sf-*` — **miroir** des skills officiels Salesforce (https://github.com/forcedotcom/sf-skills, Apache-2.0), repackagés en un socle `sf-core` (~20 skills choisis d'après l'usage réel, liste `CORE_SKILLS` de `sync.py`) et 7 plugins par domaine : `sf-agentforce`, `sf-platform`, `sf-devops`, `sf-service`, `sf-experience`, `sf-integration`, `sf-industries`, qui déclarent chacun une dépendance à `sf-core` (installé automatiquement avec eux). ~250 skills. **Généré automatiquement, ne jamais éditer à la main.**
- `reej-plugins/reej-*` — skills **maison Reej**, écrits par l'équipe. Premier plugin : `reej-design` (skill `reej-slds-mockup-generate`).

Pourquoi un miroir plutôt que le marketplace officiel : au démarrage (sept. 2026) celui-ci ne packageait qu'une partie des skills (aucun Agentforce/Data 360). On garde le miroir pour la couverture complète, le découpage par domaine, l'absence des hooks de télémétrie Salesforce, et un point d'entrée unique pour l'équipe. Salesforce a depuis ajouté un plugin officiel `agentforce-adlc` ; si leur marketplace devient complet, rebasculer dessus est une option à réévaluer.

## Fichiers clés

| Fichier | Rôle |
|---|---|
| `scripts/sync.py` | Clone l'upstream, range chaque skill dans un plugin via les regex de `DOMAINS`, réécrit les liens inter-plugins (`[x](../x/SKILL.md)` → ``skill `sf-y:x` ``), génère `plugins/`, `marketplace.json`, `SYNC_STATE.json`, et imprime un résumé Markdown (ajouts, retraits, déplacements, scripts et `allowed-tools` modifiés, non-mappés, chemins longs) réutilisé comme corps de PR. `--dry-run` n'écrit rien ; `--marketplace-only` régénère seulement `marketplace.json` sans cloner. |
| `scripts/validate.py` | Contrôle de cohérence : marketplace ↔ plugin.json, préfixes `sf-`/`reej-`, frontmatter des SKILL.md, doublons de noms, `SYNC_STATE.json`, refuse tout `TODO` dans un fichier d'un skill maison. Avec `--base <ref>` (activé en CI sur les PR) : exige un incrément de version pour tout plugin maison modifié. |
| `.github/workflows/sync-upstream.yml` | Cron quotidien 05:00 UTC + déclenchement manuel. Ouvre une PR `sync/upstream` s'il y a des changements (option `auto_merge` pour pousser direct sur `main`). |
| `.github/workflows/validate.yml` | Sur toute PR/push touchant `reej-plugins/`, `scripts/` ou `marketplace.json` : vérifie que `marketplace.json` est à jour puis lance `validate.py`. |
| `.claude-plugin/marketplace.json` | Catalogue : entrées `reej-*` d'abord, puis `sf-*`. Généré, ne pas éditer. |
| `SYNC_STATE.json` | Commit upstream synchronisé + placement de chaque skill. Sans horodatage (sinon PR vide à chaque run). |
| `CONTRIBUTING.md` | Procédure complète pour ajouter un skill ou un plugin maison. |
| `README.md` | Installation par surface (Claude Code VS Code, CLI, Cowork, web) et mise à jour. |

## Règles de travail dans ce repo

1. **Ne jamais modifier `plugins/`, `marketplace.json` ni `SYNC_STATE.json` à la main.** Tout passe par `scripts/sync.py`.
2. Pour changer le rangement d'un skill : éditer `DOMAINS` dans `sync.py` (regex sur le nom, première règle gagnante ; non-mappé → `sf-platform` + alerte dans la PR). Pour le socle : `CORE_SKILLS` (noms exacts), à garder sobre car chaque description pèse dans toutes les sessions. Un skill n'est jamais copié dans deux plugins : deux skills de même nom se feraient concurrence. `EXTRA_SKILLS` liste les skills qui n'existent que dans les plugins officiels et sont autonomes (actuellement 3, dont `platform-architecture-analyze` depuis `plugins/builder/salesforce-code-quality`).
3. Toute modification de `sync.py` doit être **poussée sur `main` avant** de relancer le workflow : il exécute la version de `main` au moment du clic.
4. Vérifier l'idempotence après toute modification des scripts : deux exécutions consécutives doivent donner `git status` vide.
5. Skills maison : préfixe `reej-` sur plugin et skill, `name` = nom du dossier, description avec « TRIGGER when / DO NOT TRIGGER when » qui cite le skill Salesforce voisin le cas échéant, pas de données client ni d'URL interne (repo public), incrémenter `version` du `plugin.json` à chaque changement, puis `python scripts/sync.py --marketplace-only` et `python scripts/validate.py`.
6. Un merge sur `main` ne met **pas** à jour les postes : chaque utilisateur fait *Update* du marketplace puis du plugin. Annoncer les nouveautés à l'équipe.

## Rituel des PR de synchro

Lire le corps de la PR : « Scripts ajoutés ou modifiés » et « `allowed-tools` modifiés » en premier (c'est ce qui s'exécute sur les postes : ouvrir le diff de chaque fichier listé), « Retirés » (vérifier s'il s'agit d'un renommage — un skill retiré + un ajouté au nom proche — ou d'une vraie suppression), « Non mappés » (ajouter une regex dans `DOMAINS`), « EXTRA_SKILLS introuvables » (le skill a bougé upstream, mettre à jour le chemin). Le bloc « chemins > 170 caractères » est informatif (limite Windows ; `git config --global core.longpaths true` côté poste). Merger, puis mettre à jour les plugins sur son poste.

## Pièges rencontrés

- Windows : `Filename too long` au clone du marketplace → `core.longpaths true`. Modes de fichiers 644/755 : un commit depuis Windows peut produire une PR de 150 « file mode changed » ; `git config core.fileMode false` dans le clone.
- Les skills upstream s'appellent entre eux par liens relatifs ; quand la cible est dans un autre plugin, `sync.py` remplace le lien par le nom appelable `sf-<plugin>:<skill>`, qui dit aussi quel plugin installer.
- Version des plugins `sf-*` = date du commit upstream. Changer `DOMAINS` ou `CORE_SKILLS` sans publication upstream modifie le contenu à version constante : Claude Code répond « already at the latest version » et ne met rien à jour. Les postes concernés désinstallent puis réinstallent les plugins.
- Les skills Salesforce supposent le CLI `sf` et une org authentifiée : pleinement exploitables dans Claude Code sur un projet SFDX ; dans Cowork/web ils servent surtout de base de connaissance.
- Règle Reej : aucune suppression d'enregistrements dans une org de production, quoi que suggère un skill (`platform-data-manage`, `platform-trust-archive-manage`, `platform-dsar-policy-manage`).
