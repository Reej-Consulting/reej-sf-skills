# reej-sf-skills — Marketplace Reej des skills Salesforce & Agentforce

Miroir de [forcedotcom/sf-skills](https://github.com/forcedotcom/sf-skills) (skills officiels Salesforce, licence Apache-2.0), **repackagé en 7 plugins par domaine** et **synchronisé chaque nuit**. Rien n'est écrit à la main dans `plugins/` : tout est régénéré par `scripts/sync.py`.

Pourquoi ce repo plutôt que le marketplace officiel ? Celui de Salesforce ne packageait que ~107 skills sur 227 au moment de la création, sans les skills Agentforce ni Data 360. Ici, les 230 skills autonomes sont couverts, et l'on maîtrise le découpage et le rythme de mise à jour.

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

La liste exacte des skills de chaque plugin est dans `plugins/<plugin>/README.md`. Les skills se référencent entre eux : quand un skill renvoie vers un skill d'un autre plugin, le lien est remplacé par `<skill:nom — plugin sf-xxx>`, ce qui indique quel plugin installer en plus.

> Conseil : n'installez que les plugins dont vous avez besoin. Chaque plugin ajoute les descriptions de ses skills au contexte de chaque session ; `sf-agentforce` + `sf-platform` couvrent l'essentiel d'une mission Agentforce.

## Installation

### Claude Code (VS Code / terminal)

```bash
claude plugin marketplace add <ORG_GITHUB>/reej-sf-skills
claude plugin install sf-agentforce@reej-salesforce
claude plugin install sf-platform@reej-salesforce
```

Mise à jour :

```bash
claude plugin marketplace update reej-salesforce
claude plugin update sf-agentforce@reej-salesforce
```

Si le repo est privé, remplacez `<ORG_GITHUB>/reej-sf-skills` par l'URL git complète (SSH ou HTTPS avec vos identifiants).

### Claude Cowork (app desktop)

Paramètres → Plugins → ajouter un marketplace avec l'URL du repo, puis installer les plugins voulus depuis la liste. Les mises à jour se récupèrent depuis le même écran.

Limite à connaître : ces skills sont conçus pour un poste de développement avec le **Salesforce CLI (`sf`) et une org authentifiée**. Dans Cowork (et sur claude.ai), ces prérequis sont absents par défaut : les skills servent alors surtout de base de connaissance (syntaxe Agent Script, specs de test, patterns d'architecture) plutôt que de workflows exécutables de bout en bout.

### claude.ai (web)

Pas de mécanisme de marketplace à ce jour. Les skills s'ajoutent individuellement (zip d'un dossier `plugins/<plugin>/skills/<skill>/`) ou via les skills d'organisation par un administrateur. Pas de mise à jour automatique sur cette surface.

## Synchronisation

- **Automatique** : le workflow `.github/workflows/sync-upstream.yml` tourne chaque jour à 05:00 UTC. S'il y a des changements upstream, il ouvre une PR `sync/upstream` dont le corps liste les skills ajoutés, retirés ou déplacés. Merger la PR publie la nouvelle version ; les utilisateurs la récupèrent avec `marketplace update`.
- **Manuelle** : onglet Actions → *Sync sf-skills upstream* → *Run workflow*. Cocher `auto_merge` pour pousser directement sur `main` sans PR.
- **Locale** : `python3 scripts/sync.py` (ou `--dry-run` pour voir sans écrire), puis `python3 scripts/validate.py`.

La version des plugins suit la date du commit upstream (`2026.9.10`), ce qui garantit qu'elle croît à chaque synchro.

### Ajouter un domaine ou déplacer un skill

Modifier le dictionnaire `DOMAINS` dans `scripts/sync.py` (regex sur le nom du skill, première règle gagnante). Un skill qu'aucune règle ne couvre tombe dans `sf-platform` et est signalé dans le résumé de la PR — c'est le signal pour compléter la règle.

## Points de vigilance

- **Instabilité upstream assumée** : Salesforce prévient que les skills peuvent être renommés ou supprimés sans préavis. La PR quotidienne rend ces changements visibles avant qu'ils n'arrivent chez les utilisateurs — relire la section « Retirés » avant de merger.
- **Ce qui n'est pas repris** : les plugins officiels `salesforce-development` et `salesforce-test-drive` embarquent aussi des hooks (gate de déploiement production, télémétrie envoyée à Salesforce), un agent, un serveur MCP (LSP Apex/SOQL) et 7 skills qui dépendent de cet outillage (`platform-destructive-deploy`, `platform-lsp-integrate`, `platform-capability-search`, `platform-environment-validate`, `platform-deploy-validate`, `platform-quick-deploy`, `dx-project-create`). Ce miroir ne reprend **que les skills autonomes** ; pour ces extras, ajouter en plus le marketplace officiel `forcedotcom/sf-skills`.
- **Règle Reej** : aucune suppression d'enregistrements dans une org de production, quoi que suggère un skill (`platform-data-manage`, `platform-trust-archive-manage`, `platform-dsar-policy-manage` notamment). Les skills restent des instructions tierces : garder l'œil sur ce qu'ils déclenchent.

## Licence

Les skills sont © Salesforce, sous licence Apache-2.0 (voir `LICENSE` et `NOTICE`). Les scripts de ce repo sont sous la même licence.
