# reej-sf-skills — Marketplace Reej des skills Salesforce & Agentforce

Miroir de [forcedotcom/sf-skills](https://github.com/forcedotcom/sf-skills) (skills officiels Salesforce, licence Apache-2.0), **repackagé en 7 plugins par domaine** et **synchronisé chaque nuit**, auquel s'ajoutent les **skills maison Reej** (`reej-*`). Rien n'est écrit à la main dans `plugins/` : tout y est régénéré par `scripts/sync.py` ; les skills Reej vivent dans `reej-plugins/`.

Pourquoi ce repo plutôt que le marketplace officiel ? Celui de Salesforce ne packageait que ~107 skills sur 227 au moment de la création, sans les skills Agentforce ni Data 360. Ici, tous les skills autonomes sont couverts, et l'on maîtrise le découpage et le rythme de mise à jour.

## Plugins

| Plugin | Contenu |
|---|---|
| `sf-agentforce` | Agentforce (Agent Script, tests, observabilité, architecture, migration Einstein Bots), Data 360, Models API, canaux Agentforce |
| `sf-platform` | Métadonnées, Apex, Flow, SOQL, déploiement, Code Analyzer, SLDS, doc Salesforce — **socle à installer en premier** |
| `sf-devops` | DevOps Center, scratch orgs, sandboxes, Dev Hub, packaging |
| `sf-service` | Omni-Channel, Digital Engagement, ITSM, Email-to-Case, Help Agent |
| `sf-experience` | Experience Cloud, LWC, UI bundles React, CMS, Commerce B2B, Mobile |
| `sf-integration` | Connected Apps, CDC, Platform Events, OmniStudio |
| `sf-industries` | Field Service, Consumer Goods, Education, Life Sciences |
| `reej-design` | **Maison Reej** — maquettes HTML SLDS pour l'avant-vente et les ateliers (voir `reej-plugins/`) |

Les plugins `sf-*` sont le miroir Salesforce, régénérés automatiquement ; les plugins `reej-*` sont écrits par Reej, dans `reej-plugins/`, et se contribuent par PR — voir [CONTRIBUTING.md](CONTRIBUTING.md).

La liste exacte des skills de chaque plugin est dans `plugins/<plugin>/README.md`. Les skills se référencent entre eux : quand un skill renvoie vers un skill d'un autre plugin, le lien est remplacé par son nom appelable `sf-xxx:nom` : Claude l'invoque directement si le plugin `sf-xxx` est installé, sinon le nom indique quel plugin installer en plus.

> Conseil : commencez par `sf-agentforce` + `sf-platform` — voir « Combien de plugins installer ? » plus bas.

## Installation

Le marketplace s'appelle `reej-salesforce` ; son adresse est `Reej-Consulting/reej-sf-skills` (ou `https://github.com/Reej-Consulting/reej-sf-skills`). Le repo est public : aucune authentification n'est demandée.

Quel que soit l'outil, le parcours est le même en trois temps : **ajouter le marketplace** (une fois), **installer les plugins** voulus, **mettre à jour** de temps en temps. Commencez par `sf-agentforce` et `sf-platform` ; ajoutez les autres selon vos missions.

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
2. **Installer les plugins** : `/plugin` → onglet *Discover* → repérer les plugins `sf-…` du marketplace `reej-salesforce` → *Install* sur `sf-agentforce`, puis `sf-platform`. Portée « utilisateur » par défaut : les plugins sont disponibles dans tous vos projets.
3. **Vérifier** : dans une nouvelle conversation, taper `/sf-` — l'autocomplétion doit proposer `/sf-agentforce:agentforce-generate`, `/sf-platform:platform-soql-query`, etc.
4. **Mettre à jour** : `/plugin` → onglet *Marketplaces* → *Update* sur `reej-salesforce`, puis onglet *Installed* → *Update* sur chaque plugin `sf-…`. À faire quand une PR de synchro a été mergée, ou une fois par mois.

### B. Claude Code en ligne de commande (CLI `claude`)

Si la commande `claude` est disponible dans votre terminal (installation native ou `npm install -g @anthropic-ai/claude-code`), les mêmes opérations en commandes :

```bash
# 1. Ajouter le marketplace (une fois)
claude plugin marketplace add Reej-Consulting/reej-sf-skills

# 2. Installer les plugins
claude plugin install sf-agentforce@reej-salesforce
claude plugin install sf-platform@reej-salesforce

# 3. Vérifier
claude plugin list

# 4. Mettre à jour
claude plugin marketplace update reej-salesforce
claude plugin update sf-agentforce@reej-salesforce
claude plugin update sf-platform@reej-salesforce
```

Pour limiter un plugin à un seul projet, lancer `claude plugin install … --scope project` depuis le dossier du projet.

### C. Application Claude sur le poste (Cowork)

1. **Ajouter le marketplace** : Paramètres → *Plugins* → ajouter un marketplace / une source → coller `https://github.com/Reej-Consulting/reej-sf-skills` → valider.
2. **Installer les plugins** : dans la liste du marketplace `reej-salesforce`, installer `sf-agentforce` et `sf-platform` (et les autres au besoin).
3. **Vérifier** : ouvrir une **nouvelle** session (les plugins sont chargés au démarrage) et demander par exemple « selon le skill agentforce-test, quelles métriques choisir pour un agent de service ? ».
4. **Mettre à jour** : même écran Paramètres → *Plugins* → mise à jour du marketplace puis des plugins.

Limite à connaître : ces skills sont conçus pour un poste de développement avec le **Salesforce CLI (`sf`) et une org authentifiée**. Dans Cowork (et sur claude.ai), ces prérequis sont absents par défaut : les skills servent alors surtout de base de connaissance (syntaxe Agent Script, specs de test, patterns d'architecture) plutôt que de workflows exécutables de bout en bout.

### D. claude.ai (web)

Pas de mécanisme de marketplace à ce jour. Un skill s'ajoute individuellement : zipper le dossier `plugins/<plugin>/skills/<skill>/` et l'importer dans Paramètres → Capacités → Skills (ou via les skills d'organisation, par un administrateur). Pas de mise à jour automatique : à réserver à 2 ou 3 skills réellement utilisés hors VS Code.

### Combien de plugins installer ?

Chaque plugin ajoute les descriptions de ses skills au contexte de chaque session. Sept plugins partout, c'est lourd pour rien : installer `sf-agentforce` + `sf-platform` comme socle, puis `sf-service`, `sf-experience`, `sf-devops`, `sf-integration` ou `sf-industries` seulement là où la mission le justifie. Dans Claude Code, `/context` montre ce que les skills consomment.

## Synchronisation

- **Automatique** : le workflow `.github/workflows/sync-upstream.yml` tourne chaque jour à 05:00 UTC. S'il y a des changements upstream, il ouvre une PR `sync/upstream` dont le corps liste les skills ajoutés, retirés ou déplacés, ainsi que les scripts et `allowed-tools` modifiés (ce qui s'exécute sur les postes : à relire en priorité). Merger la PR publie la nouvelle version ; les utilisateurs la récupèrent avec `marketplace update`.
- **Manuelle** : onglet Actions → *Sync sf-skills upstream* → *Run workflow*. Cocher `auto_merge` pour pousser directement sur `main` sans PR.
- **Locale** : `python3 scripts/sync.py` (ou `--dry-run` pour voir sans écrire), puis `python3 scripts/validate.py`. Après ajout d'un plugin maison : `python3 scripts/sync.py --marketplace-only` (régénère `marketplace.json` sans cloner Salesforce).
- **Validation des PR humaines** : le workflow `validate.yml` vérifie `marketplace.json` et la structure des plugins sur toute PR touchant `reej-plugins/` ou `scripts/`.

La version des plugins suit la date du commit upstream (`2026.9.10`), ce qui garantit qu'elle croît à chaque synchro.

### Ajouter un domaine ou déplacer un skill

Modifier le dictionnaire `DOMAINS` dans `scripts/sync.py` (regex sur le nom du skill, première règle gagnante). Un skill qu'aucune règle ne couvre tombe dans `sf-platform` et est signalé dans le résumé de la PR — c'est le signal pour compléter la règle.

## Points de vigilance

- **Instabilité upstream assumée** : Salesforce prévient que les skills peuvent être renommés ou supprimés sans préavis. La PR quotidienne rend ces changements visibles avant qu'ils n'arrivent chez les utilisateurs — relire la section « Retirés » avant de merger.
- **Ce qui n'est pas repris** : les plugins officiels `salesforce-development` et `salesforce-test-drive` embarquent aussi des hooks (gate de déploiement production, télémétrie envoyée à Salesforce), un agent, un serveur MCP (LSP Apex/SOQL) et 7 skills qui dépendent de cet outillage (`platform-destructive-deploy`, `platform-lsp-integrate`, `platform-capability-search`, `platform-environment-validate`, `platform-deploy-validate`, `platform-quick-deploy`, `dx-project-create`). Ce miroir ne reprend **que les skills autonomes** ; pour ces extras, ajouter en plus le marketplace officiel `forcedotcom/sf-skills`.
- **Règle Reej** : aucune suppression d'enregistrements dans une org de production, quoi que suggère un skill (`platform-data-manage`, `platform-trust-archive-manage`, `platform-dsar-policy-manage` notamment). Les skills restent des instructions tierces : garder l'œil sur ce qu'ils déclenchent.

## Licence

Les skills `sf-*` sont © Salesforce, sous licence Apache-2.0 (voir `LICENSE` et `NOTICE`) ; les scripts de ce repo sont sous la même licence. Les skills `reej-*` sont © Reej Consulting.
