# Reej — Design & maquettes

Plugin maison Reej (pas un miroir Salesforce) : skills de design d'interfaces Salesforce.

Dépend de `sf-core` (ses skills renvoient vers `design-systems-slds-apply` et `experience-lwc-generate`) : installé automatiquement dans VS Code, à installer à la main dans Claude Desktop.

| Skill | Usage |
|---|---|
| `reej-slds-mockup-generate` | Maquette HTML statique SLDS d'un écran Lightning pour l'avant-vente et les ateliers |

Contribution : voir [CONTRIBUTING.md](../../CONTRIBUTING.md) à la racine du repo. Après tout changement, incrémenter `version` dans `.claude-plugin/plugin.json`, sinon les postes installés ne verront pas la mise à jour.
