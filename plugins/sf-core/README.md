# Salesforce — Socle

Socle commun : SOQL, retrieve/deploy, Apex et tests, Flow, génération de métadonnées, LWC, Lightning Types, Agent Script, documentation Salesforce. Installé automatiquement avec tout autre plugin sf-*.

21 skills, copie de [forcedotcom/sf-skills](https://github.com/forcedotcom/sf-skills) au commit `4bbae5c4` (2026-10-09). Ne pas éditer à la main : régénéré par `scripts/sync.py`.

| Skill | Description |
|---|---|
| `agentforce-architecture-analyze` | Declared architecture snapshot for one Agentforce agent: planner, topics, actions, flows, Apex, prompt templates, and NGA plugins. Renders a human-readable architecture document an… |
| `agentforce-generate` | Build, modify, audit, repair, optimize, debug, and deploy agents with Agentforce Agent Script. TRIGGER when: user creates, reviews, or changes .agent files or aiAuthoringBundle met… |
| `automation-flow-generate` | Generate Salesforce Flows using the MCP tool execute_metadata_action. Use when the user asks to create, build, or generate a flow — including Screen, Autolaunched, Record-Triggered… |
| `design-systems-slds-apply` | Apply SLDS-compliant UI using the correct blueprints, styling hooks, utility classes, and icons. Use when building any UI that needs SLDS, choosing between Lightning Base Component… |
| `experience-lwc-generate` | Lightning Web Components with PICKLES methodology and 165-point scoring. Use this skill when the user creates or edits LWC components, builds wire service patterns, or writes Jest … |
| `platform-apex-anonymous-run` | Runs anonymous Apex against the connected org (.apex file or pasted snippet), capturing the debug log, surfacing errors. Triggers on \"run this anonymous apex\", \"execute this scr… |
| `platform-apex-generate` | Primary Apex authoring skill for class generation, refactoring, and review. ALWAYS ACTIVATE when the user mentions Apex, .cls, triggers, or asks to create/refactor a class (service… |
| `platform-apex-logs-debug` | Salesforce debug log analysis and troubleshooting with 100-point scoring. TRIGGER when: user analyzes debug logs, hits governor limits, reads stack traces, or touches .log files fr… |
| `platform-apex-test-generate` | Use to generate and validate Apex test classes with TestDataFactory patterns, bulk testing (251+ records), mocking, assertions, and disciplined test-fix loops. Use when creating Ap… |
| `platform-apex-test-run` | Apex test execution, coverage analysis, and test-fix loops with 120-point scoring. Use when the user runs Apex tests, checks code coverage, fixes failing tests, or touches *Test.cl… |
| `platform-architecture-analyze` | Use when the developer asks to \"review the architecture\", \"run a Well-Architected check\", \"audit this project\", \"is this project well-architected?\", or wants to assess secu… |
| `platform-custom-field-generate` | Use when users create, generate, or validate Salesforce Custom Field metadata. Trigger on custom fields, field types, Roll-Up Summary, Master-Detail/Lookup relationships, formula f… |
| `platform-custom-lightning-type-generate` | Use this skill when users need to create Custom Lightning Types (CLTs) for Einstein Agent actions or structured input/output schemas. Trigger when users mention CLT, Custom Lightni… |
| `platform-custom-object-generate` | Use when users create, generate, or validate Salesforce Custom Object metadata. Trigger on custom objects, .object files, sharing models, name fields, or validation rules — e.g. \"… |
| `platform-data-and-tooling-api-context-get` | Authoritative field/schema reference for 2130 STANDARD Salesforce objects — sObject and Tooling field API names, types, properties (filterable/sortable/groupable/updateable), and r… |
| `platform-docs-get` | Official Salesforce documentation retrieval skill. Use when you need authoritative Salesforce docs from developer.salesforce.com, help.salesforce.com, architect.salesforce.com, adm… |
| `platform-metadata-api-context-get` | REQUIRED companion for Salesforce metadata generation — load this schema/API-context skill in the SAME turn as ANY metadata generator (if you load a generator, you ALSO load this).… |
| `platform-metadata-deploy` | Salesforce DevOps automation using sf CLI v2. TRIGGER when: user deploys metadata, creates/manages scratch orgs or sandboxes, sets up CI/CD pipelines, or troubleshoots deployment e… |
| `platform-metadata-retrieve` | ALWAYS USE THIS SKILL to retrieve metadata from an org to your local project with sf project retrieve start. Supports retrieval by all changes, source directory, metadata type (wil… |
| `platform-permission-set-generate` | Generates correct, deployable Salesforce permission set metadata (PermissionSet XML) with object, field, user, and app permissions. Use this skill when creating or editing permissi… |
| `platform-soql-query` | Use when the user needs SOQL/SOSL authoring or optimization: natural-language-to-query generation, relationship queries, aggregates, query-plan/selectivity analysis, and performanc… |
