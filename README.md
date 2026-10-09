# reej-sf-skills — Marketplace Reej des skills Salesforce & Agentforce

Miroir de [forcedotcom/sf-skills](https://github.com/forcedotcom/sf-skills) (skills officiels Salesforce, licence Apache-2.0), **repackagé en un socle (`sf-core`) et 7 plugins par domaine** et **synchronisé chaque nuit**, auquel s'ajoutent les **skills maison Reej** (`reej-*`). Rien n'est écrit à la main dans `plugins/` : tout y est régénéré par `scripts/sync.py` ; les skills Reej vivent dans `reej-plugins/`.

Pourquoi ce repo plutôt que le marketplace officiel ? Celui de Salesforce ne packageait que ~107 skills sur 227 au moment de la création, sans les skills Agentforce ni Data 360. Ici, tous les skills autonomes sont couverts, et l'on maîtrise le découpage et le rythme de mise à jour.

## Plugins

| Plugin | Contenu |
|---|---|
| `sf-core` | **Socle, à installer partout** — les ~20 skills du quotidien : SOQL, retrieve/deploy, Apex et tests, Flow, génération de métadonnées, LWC, Lightning Types, Agent Script, doc Salesforce |
| `sf-agentforce` | Agentforce avancé (tests, observabilité, persona, migration Einstein Bots, canaux), Data 360, Models API |
| `sf-platform` | Compléments plateforme : sharing, rapports, Code Analyzer, chiffrement, données, métadonnées avancées, widgets, SLDS avancé |
| `sf-devops` | DevOps Center, scratch orgs, sandboxes, Dev Hub, packaging |
| `sf-service` | Omni-Channel, Digital Engagement, ITSM, Email-to-Case, Help Agent |
| `sf-experience` | Experience Cloud, LWC avancé, UI bundles React, CMS, Commerce B2B, Mobile |
| `sf-integration` | Connected Apps, CDC, Platform Events, OmniStudio |
| `sf-industries` | Field Service, Consumer Goods, Education, Life Sciences |
| `reej-design` | **Maison Reej** — maquettes HTML SLDS pour l'avant-vente et les ateliers (voir `reej-plugins/`) |

Les plugins `sf-*` sont le miroir Salesforce, régénérés automatiquement ; les plugins `reej-*` sont écrits par Reej, dans `reej-plugins/`, et se contribuent par PR — voir [CONTRIBUTING.md](CONTRIBUTING.md).

La liste exacte des skills de chaque plugin est dans `plugins/<plugin>/README.md`. Les skills se référencent entre eux : quand un skill renvoie vers un skill d'un autre plugin, le lien est remplacé par son nom appelable `sf-xxx:nom` : Claude l'invoque directement si le plugin `sf-xxx` est installé, sinon le nom indique quel plugin installer en plus.

Chaque plugin de domaine dépend de `sf-core` : l'installer installe aussi le socle automatiquement. Un skill n'existe que dans un seul plugin (jamais de doublon).

> Conseil : installez `sf-core` partout, et un plugin de domaine seulement sur les projets qui en ont besoin — voir « Combien de plugins installer ? » plus bas.

## Installation

Le marketplace s'appelle `reej-salesforce` ; son adresse est `Reej-Consulting/reej-sf-skills` (ou `https://github.com/Reej-Consulting/reej-sf-skills`). Le repo est public : aucune authentification n'est demandée.

Quel que soit l'outil, le parcours est le même en trois temps : **ajouter le marketplace** (une fois), **installer les plugins** voulus, **mettre à jour** de temps en temps. Commencez par `sf-core` ; ajoutez les plugins de domaine selon vos missions.

### 0. Prérequis Windows (une fois par poste)

Certains skills (exemples OmniStudio) ont des chemins qui dépassent la limite Windows de 260 caractères une fois clonés sous `C:\Users\<vous>\.claude\plugins\…`. Sans ce réglage, l'ajout du marketplace échoue avec `Filename too long`. Dans un terminal :

```powershell
git config --global core.longpaths true
```

Si l'erreur persiste malgré tout, activer les chemins longs au niveau de Windows (PowerShell **en administrateur**, puis redémarrer le terminal) :

```powershell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

### A. Claude Code dans VS Code (extension)

Tout se fait depuis la conversation Claude Code, avec la commande `/plugin` qui ouvre le gestionnaire de plugins.

1. **Ajouter le marketplace** : `/plugin` → onglet *Marketplaces* → *Add* → saisir `Reej-Consulting/reej-sf-skills` → valider. Le clone prend quelques secondes (≈ 60 Mo).
2. **Installer les plugins** : `/plugin` → onglet *Discover* → repérer les plugins `sf-…` du marketplace `reej-salesforce` → *Install* sur `sf-core`. Portée « utilisateur » par défaut : le plugin est disponible dans tous vos projets. Pour un plugin de domaine (ex. `sf-agentforce`), choisir la portée « locale » (pour vous seul, dans ce projet), depuis le projet concerné. Éviter la portée « projet » : elle écrit `.claude/settings.json`, un fichier fait pour être commité, qui imposerait le plugin à tous ceux qui clonent le dépôt, y compris l'équipe d'un client.
3. **Vérifier** : dans une nouvelle conversation, taper `/sf-` — l'autocomplétion doit proposer `/sf-core:agentforce-generate`, `/sf-core:platform-soql-query`, etc.
4. **Mettre à jour** : `/plugin` → onglet *Marketplaces* → *Update* sur `reej-salesforce`, puis onglet *Installed* → *Update* sur chaque plugin `sf-…`, puis `/reload-plugins` (installe un socle ou une dépendance ajoutés entre-temps). À faire quand une PR de synchro a été mergée, ou une fois par mois.

### B. Claude Code en ligne de commande (CLI `claude`)

Si la commande `claude` est disponible dans votre terminal (installation native ou `npm install -g @anthropic-ai/claude-code`), les mêmes opérations en commandes :

```bash
# 1. Ajouter le marketplace (une fois)
claude plugin marketplace add Reej-Consulting/reej-sf-skills

# 2. Installer le socle (partout), puis un plugin de domaine pour un projet donné
claude plugin install sf-core@reej-salesforce
claude plugin install sf-agentforce@reej-salesforce --scope local   # depuis le dossier du projet

# 3. Vérifier
claude plugin list

# 4. Mettre à jour
claude plugin marketplace update reej-salesforce
claude plugin update sf-core@reej-salesforce
claude plugin update sf-agentforce@reej-salesforce
```

Pour limiter un plugin à un seul projet, lancer `claude plugin install … --scope local` depuis le dossier du projet : le réglage reste personnel (`.claude/settings.local.json`). Ne pas utiliser `--scope project`, qui écrit dans `.claude/settings.json`, fichier destiné à être commité et partagé avec tous ceux qui clonent le dépôt.

### C. Application Claude sur le poste (Cowork)

1. **Ajouter le marketplace** : Paramètres → *Plugins* → ajouter un marketplace / une source → coller `https://github.com/Reej-Consulting/reej-sf-skills` → valider.
2. **Installer les plugins** : dans la liste du marketplace `reej-salesforce`, installer `sf-core` (et les plugins de domaine au besoin). Contrairement à VS Code, Claude Desktop n'installe pas les dépendances : installer `sf-core` explicitement.
3. **Vérifier** : ouvrir une **nouvelle** session (les plugins sont chargés au démarrage) et demander par exemple « selon le skill agentforce-generate, comment structurer un sous-agent en Agent Script ? ».
4. **Mettre à jour** : même écran Paramètres → *Plugins* → mise à jour du marketplace puis des plugins.

Limite à connaître : ces skills sont conçus pour un poste de développement avec le **Salesforce CLI (`sf`) et une org authentifiée**. Dans Cowork (et sur claude.ai), ces prérequis sont absents par défaut : les skills servent alors surtout de base de connaissance (syntaxe Agent Script, specs de test, patterns d'architecture) plutôt que de workflows exécutables de bout en bout.

### Desktop et VS Code sur le même poste

Un plugin installé dans Claude Desktop est enregistré sur votre compte claude.ai, puis recopié automatiquement dans Claude Code (VS Code, CLI) sous le nom `<plugin>@synced`. Cette copie n'est pas mise à jour en même temps que le marketplace : elle peut être périmée et faire doublon avec les plugins installés dans VS Code (même skill présent deux fois, descriptions qui disparaissent faute de place). Dans `/plugin`, elle apparaît avec le suffixe `@synced`.

Si vous installez les plugins dans VS Code via le marketplace, coupez cette recopie en ajoutant dans `~/.claude/settings.json` :

```json
"syncClaudeAiPlugins": false
```

Au démarrage suivant, les copies `@synced` sont déplacées dans `~/.claude/plugins/.trash/` et ne se chargent plus. Contrepartie : un plugin activé dans Desktop n'arrive plus dans VS Code, il faut l'y installer aussi. Pour ne couper qu'un seul plugin, désactivez sa ligne `@synced` dans `/plugin`.

### D. claude.ai (web)

Pas de mécanisme de marketplace à ce jour. Un skill s'ajoute individuellement : zipper le dossier `plugins/<plugin>/skills/<skill>/` et l'importer dans Paramètres → Capacités → Skills (ou via les skills d'organisation, par un administrateur). Pas de mise à jour automatique : à réserver à 2 ou 3 skills réellement utilisés hors VS Code.

### Combien de plugins installer ?

Chaque plugin ajoute les descriptions de ses skills au contexte de chaque session, et au-delà d'un certain volume Claude ne voit plus que le nom des skills, sans leur description : il ne pense alors plus à les utiliser. D'où le socle `sf-core`, volontairement limité à ~20 skills choisis d'après l'usage réel : l'installer partout (portée utilisateur). Les plugins de domaine (`sf-agentforce`, `sf-platform`, `sf-service`, `sf-experience`, `sf-devops`, `sf-integration`, `sf-industries`) s'installent en portée **locale** (pour vous seul, dans le projet concerné), seulement là où la mission le justifie. Dans Claude Code, `/context` montre ce que les skills consomment.

## Synchronisation

- **Automatique** : le workflow `.github/workflows/sync-upstream.yml` tourne chaque jour à 05:00 UTC. S'il y a des changements upstream, il ouvre une PR `sync/upstream` dont le corps liste les skills ajoutés, retirés ou déplacés, ainsi que les scripts et `allowed-tools` modifiés (ce qui s'exécute sur les postes : à relire en priorité). Merger la PR publie la nouvelle version ; les utilisateurs la récupèrent avec `marketplace update`.
- **Manuelle** : onglet Actions → *Sync sf-skills upstream* → *Run workflow*. Cocher `auto_merge` pour pousser directement sur `main` sans PR.
- **Locale** : `python3 scripts/sync.py` (ou `--dry-run` pour voir sans écrire), puis `python3 scripts/validate.py`. Après ajout d'un plugin maison : `python3 scripts/sync.py --marketplace-only` (régénère `marketplace.json` sans cloner Salesforce).
- **Validation des PR humaines** : le workflow `validate.yml` vérifie `marketplace.json` et la structure des plugins sur toute PR touchant `reej-plugins/` ou `scripts/`.

La version des plugins suit la date du commit upstream (`2026.9.10`), ce qui garantit qu'elle croît à chaque synchro.

### Ajouter un domaine ou déplacer un skill

Modifier le dictionnaire `DOMAINS` dans `scripts/sync.py` (regex sur le nom du skill, première règle gagnante). Un skill qu'aucune règle ne couvre tombe dans `sf-platform` et est signalé dans le résumé de la PR — c'est le signal pour compléter la règle.

Pour faire entrer ou sortir un skill du socle, modifier la liste `CORE_SKILLS` (noms exacts). Rester sobre : chaque skill ajouté au socle pèse dans toutes les sessions. Si Salesforce renomme ou supprime un skill du socle, le résumé de la PR le signale (« CORE_SKILLS introuvables »).

Attention : un changement de découpage (`DOMAINS`, `CORE_SKILLS`) ne change pas le numéro de version des plugins tant que Salesforce n'a rien publié. Claude Code ne met à jour un plugin que si son numéro change : les postes déjà à jour doivent alors désinstaller puis réinstaller les plugins concernés.

## Points de vigilance

- **Instabilité upstream assumée** : Salesforce prévient que les skills peuvent être renommés ou supprimés sans préavis. La PR quotidienne rend ces changements visibles avant qu'ils n'arrivent chez les utilisateurs — relire la section « Retirés » avant de merger.
- **Ce qui n'est pas repris** : les plugins officiels `salesforce-development` et `salesforce-test-drive` embarquent aussi des hooks (gate de déploiement production, télémétrie envoyée à Salesforce), un agent, un serveur MCP (LSP Apex/SOQL) et 7 skills qui dépendent de cet outillage (`platform-destructive-deploy`, `platform-lsp-integrate`, `platform-capability-search`, `platform-environment-validate`, `platform-deploy-validate`, `platform-quick-deploy`, `dx-project-create`). Ce miroir ne reprend **que les skills autonomes** ; pour ces extras, ajouter en plus le marketplace officiel `forcedotcom/sf-skills`.
- **Règle Reej** : aucune suppression d'enregistrements dans une org de production, quoi que suggère un skill (`platform-data-manage`, `platform-trust-archive-manage`, `platform-dsar-policy-manage` notamment). Les skills restent des instructions tierces : garder l'œil sur ce qu'ils déclenchent.
- **Avis et avertissements dans Claude Desktop** (Paramètres → Plugins → Gérer les marketplaces) : les « avis » signalent qu'un plugin a changé depuis la dernière synchro, ce qui est normal après chaque mise à jour. Les « avertissements » portent sur quelques skills Salesforce dont la description contient un mot entre chevrons (`<description>`, `<suffix>`…) : claude.ai retire les chevrons, le skill reste disponible. Sans conséquence, rien à faire.

## Licence

Les skills `sf-*` sont © Salesforce, sous licence Apache-2.0 (voir `LICENSE` et `NOTICE`) ; les scripts de ce repo sont sous la même licence. Les skills `reej-*` sont © Reej Consulting.
