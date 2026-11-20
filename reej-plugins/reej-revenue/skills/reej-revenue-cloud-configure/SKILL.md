---
name: reej-revenue-cloud-configure
description: "Concevoir, configurer, requêter et déboguer Revenue Cloud (anciennement Revenue Lifecycle Management, RLM) dans l'org et le repo SFDX d'un client : modèle de données RLM (catalogue PCM, pricing, rates, configurator, devis/commandes, DRO, usage, billing, approvals), Business APIs (Connect REST), Context Definitions, recettes et procédures de prix (expression sets), decision tables, constraint models (CML). TRIGGER when: l'utilisateur travaille sur Revenue Cloud / RLM — objets ProductSellingModel, ProductRelatedComponent, RateCardEntry, AssetAction, BillingSchedule, UsageResource, DecisionTable… ; pricing procedure, expression set, decision table, context definition, CML, configurateur produit, DRO, place sales transaction ; demande pourquoi un prix, une règle de configuration ou un contexte ne s'applique pas. DO NOT TRIGGER when: Salesforce CPQ historique (package géré SBQQ__, autre modèle de données) ; catalogue Industries EPC / OmniStudio (omnistudio-epc-catalog-generate) ; facturation courtage Insurance (insurance-brokerage-agency-billing-configure) ; la session est ouverte dans un clone de SalesforceLabs/revenue-cloud-foundations (utiliser ses skills natifs) ; SOQL, Apex ou déploiement sans lien avec RLM (skills sf-core)."
metadata:
  version: "0.1"
  owner: "Reej Consulting"
  domains: ["Revenue Cloud"]
  sourceRelease: "264 (Winter '27), API v68.0"
  relatedSkills:
    - "platform-soql-query"
    - "platform-metadata-retrieve"
    - "platform-metadata-deploy"
    - "platform-docs-get"
---

# Revenue Cloud (RLM) — projet client

## Objectif

Aider un consultant Reej à concevoir, configurer et déboguer Revenue Cloud dans l'org d'un client, depuis le repo SFDX du client, avec des faits RLM fiables plutôt que des souvenirs approximatifs. Les fichiers de `references/` contiennent la connaissance ; ce fichier dit quand les lire et comment travailler.

## 1. Avant toute réponse ou modification

1. **Version de l'org.** Les références décrivent la **Release 264 (Winter '27, API v68.0)**. Lire `apiVersion` (`sf org display`) ou `sourceApiVersion` (`sfdx-project.json`). Si l'org est sur une autre release, signaler que les références peuvent différer et vérifier tout point critique dans la doc officielle (skill `platform-docs-get`).
2. **Type d'org.** Identifier l'org cible (`sf org display`). Production : lecture seule. Ne jamais y déployer, ne jamais y supprimer d'enregistrement, même si l'utilisateur le demande ; les changements passent par une sandbox et le processus de mise en production du client.
3. **Existant d'abord.** Avant de modifier une procédure de prix, une decision table, une context definition ou un modèle CML, récupérer la version actuelle (skill `platform-metadata-retrieve`, ou requête SOQL / appel GET) et la montrer. Ne jamais réécrire de mémoire un artefact qu'on n'a pas lu.
4. **Objet RLM ou CPQ ?** Un objet ou champ préfixé `SBQQ__` signale Salesforce CPQ (package géré), pas RLM : le dire et sortir de ce skill.

## 2. Quelle référence lire

Lire **uniquement** la ou les références utiles à la question, en entier, avant de répondre.

| La question porte sur… | Lire |
|---|---|
| Un objet, un champ, une relation, l'ordre de chargement des données, une requête SOQL sur des objets RLM | `references/data-model.md` |
| Un appel REST (Connect API) : pricing, configurateur, product discovery, création de devis/commande, billing, usage, rates | `references/business-apis.md` |
| Un contexte : context definition, mapping, tag, hydratation, persistance, extension d'une définition standard | `references/context-definitions.md` |
| Le calcul de prix : recette de prix, procédure de prix, expression set, procedure plan, overlay, prix non appliqué | `references/pricing-procedures.md` |
| Une table de décision : création, paramètres, activation, rafraîchissement, résultat de lookup inattendu | `references/decision-tables.md` |
| Une règle de configuration produit : modèle CML, bundle, règle sans effet après déploiement | `references/constraint-models.md` |

Un problème de prix touche souvent trois références à la fois : procédure (`pricing-procedures.md`), données de lookup (`decision-tables.md`) et contexte (`context-definitions.md`). Les lire dans cet ordre.

## 3. Règles de travail

1. **Ordre de dépendance.** Respecter l'ordre décrit dans la référence concernée (parent avant enfant pour les données ; pour le pricing : decision tables → mappings recette/table → procédures de prix → context definitions → procedure plans et overlays). Présenter tout plan de changement comme une liste numérotée dans cet ordre, avec pour chaque étape l'artefact touché et la façon de vérifier.
2. **Metadata API ou Connect API.** Choisir selon ce que dit la référence pour l'artefact concerné, et le dire. Ne pas mélanger les deux sur un même artefact sans raison.
3. **Versions et activation.** Ne jamais modifier en place une version active si la référence indique de créer une nouvelle version ; préciser ce qu'il faut activer ou rafraîchir après le déploiement (decision table, context definition, procédure).
4. **Aucune invention.** Ne jamais deviner un nom d'objet, de champ, d'endpoint ou une syntaxe CML. Si la référence ne le donne pas : vérifier dans l'org (`sf sobject describe --sobject <Objet>`, requête sur les métadonnées) ou dans la doc officielle, sinon écrire « à vérifier ».
5. **Données client.** Ne pas recopier de données client dans un fichier commité ni dans un exemple réutilisable.
6. **Diagnostic.** Pour « ça ne marche pas après déploiement », dérouler la checklist de diagnostic de la référence concernée avant de proposer une correction, et dire quelle étape a révélé la cause.

## 4. Org de démo ou de POC

Si l'utilisateur veut monter une org Revenue Cloud de démonstration de bout en bout (catalogue, prix, données de démo), ce skill n'est pas le bon outil : recommander le dépôt **SalesforceLabs/revenue-cloud-foundations**, à cloner et à ouvrir dans Claude Code à sa racine, où ses propres skills (orchestration CumulusCI, plans SFDMU, données de démo) prennent le relais. Sous Windows, ses skills sont des liens symboliques : travailler dans WSL, ou suivre la section « Revenue Cloud » du README du marketplace Reej.

## 5. Format de réponse

- Réponse en français, noms d'API Salesforce tels quels.
- Pour un plan de configuration : étapes numérotées dans l'ordre de dépendance, artefact, méthode (Metadata / Connect / données), vérification.
- Signaler toute affirmation issue des références qui dépend de la release (« Release 264 ») quand l'org est sur une autre version.
