# Salesforce — Platform & Apex

Compléments plateforme au socle sf-core : sharing et OWD, rapports et list views, Code Analyzer et ApexGuru, chiffrement, gestion de données, métadonnées avancées, widgets, validation et migration SLDS.

39 skills, copie de [forcedotcom/sf-skills](https://github.com/forcedotcom/sf-skills) au commit `e5164d94` (2026-10-07). Ne pas éditer à la main : régénéré par `scripts/sync.py`.

Dépend de `sf-core` (socle), installé automatiquement avec ce plugin.

| Skill | Description |
|---|---|
| `design-systems-slds-validate` | Audit Lightning Web Components for SLDS design-system compliance and produce a scored quality report. Runs the SLDS linter and analyzes CSS for theming hook usage and pairing, scor… |
| `design-systems-slds2-migrate` | Migrate Lightning Web Components from SLDS 1 to SLDS 2 by running the SLDS linter and fixing violations. Use this skill whenever users mention SLDS 2, SLDS uplift, linter violation… |
| `dx-apexguru-scan` | Run an ApexGuru performance scan on a Salesforce Apex project via the ApexGuru SFAP Scan API. Zips the project's Apex (any layout), submits it, polls to completion, decodes the bas… |
| `dx-code-analyzer-configure` | Set up, configure, and troubleshoot Salesforce Code Analyzer for any project. Handles installation, prerequisite checks, diagnosing broken setups, creating and editing code-analyze… |
| `dx-code-analyzer-custom-rule-create` | Create custom Code Analyzer rules for Regex (pattern matching), PMD (XPath/AST for Apex and metadata XML), and ESLint (LWC/JavaScript/TypeScript). Use when users want to enforce co… |
| `dx-code-analyzer-run` | Run Salesforce Code Analyzer to scan code for security, performance, best practice, and code style violations. Supports all engines (PMD, ESLint, CPD, RetireJS, Flow, SFGE, ApexGur… |
| `external-diagram-mermaid-generate` | Salesforce architecture diagrams using Mermaid with ASCII fallback. Use this skill when generating text-based diagrams for Salesforce architecture, OAuth flows, ERDs, integration s… |
| `marketing-message-test` | Salesforce Marketing Cloud / Engagement 360 message preview and test-send. Use this skill when the user wants to render a personalized or unpersonalized preview of an E360 message … |
| `platform-agentexchange-partner-offers-configure` | Enable or disable the org preference that controls whether a Salesforce org can receive partner offers from the Transactable Marketplace. Use this skill when the user wants to turn… |
| `platform-custom-application-generate` | Use this skill when users need to create or configure tab-based Salesforce Custom Applications with navigation, branding, and action overrides. Trigger when users mention custom ap… |
| `platform-custom-metadata-type-generate` | Use to create, generate, or validate Salesforce Custom Metadata Type metadata — the __mdt object, fields, and deployable records. Trigger on custom metadata types, CMDT, __mdt obje… |
| `platform-custom-report-type-generate` | Use to create, generate, or validate Salesforce Custom Report Type metadata. Trigger on custom report types, CRTs, cross-object reports, report builder data sources, exposing field… |
| `platform-custom-setting-generate` | Use to create, generate, or validate Salesforce Custom Setting metadata. Trigger on custom settings (hierarchy/list), customSettingsType, SetupOwnerId, per-profile/per-user config … |
| `platform-custom-tab-generate` | Use this skill when users need to create or configure Salesforce Custom Tabs. Trigger when users mention tabs, navigation tabs, object tabs, web tabs, Visualforce tabs, Lightning c… |
| `platform-data-manage` | Salesforce data operations with 130-point scoring. Use to create, update, delete, bulk import/export, generate test data, and clean up org records via sf CLI and anonymous Apex. TR… |
| `platform-datamask-run` | Data Mask end-to-end operation on a sandbox: configure a masking policy over PII, run the masking job, poll it to completion, report masked-record results, and abort an in-progress… |
| `platform-dataspace-access-configure` | Use this skill to configure or inspect Salesforce Data Cloud DataSpace access for permission sets. Grants dataspace-level access via MDAPI PermissionSet XML with dataspaceScopes el… |
| `platform-dsar-policy-manage` | Configure, run, and audit DsarPolicy Right-to-Portability exports end to end: author the data map over a subject's related records, resolve a request's subject (email/name/id) to a… |
| `platform-encryption-configure` | Configure Salesforce Shield Platform Encryption — generate deployable encryption settings and encrypted-field metadata, and answer key-model and lifecycle questions. TRIGGER when: … |
| `platform-flexipage-generate` | Use when users create, generate, modify, or validate Salesforce Lightning pages (FlexiPages). Trigger on RecordPage, AppPage, HomePage, Lightning pages, adding components to a page… |
| `platform-lightning-app-coordinate` | Build complete Salesforce Lightning Experience applications from natural language descriptions. Use this skill when a user requests a \"complete app\", \"Lightning app\", \"busines… |
| `platform-lightning-type-widget-coordinate` | Orchestrate Apex-backed Lightning Type + HXL widget generation. TRIGGER only when the prompt EXPLICITLY invokes Lightning Types: user says 'Lightning Type', 'CLT', 'Custom Lightnin… |
| `platform-list-view-generate` | Use this skill when users need to create, generate, or validate Salesforce List View metadata. Trigger when users mention list views, filtered record lists, creating views, setting… |
| `platform-manifest-generate` | Use to generate a package.xml (and optionally destructiveChanges.xml / Pre / Post) from a source dir, a component list, or org introspection. Trigger on 'generate a package.xml fro… |
| `platform-mcp-tool-widget-coordinate` | Orchestrate object-based Lightning Type + HXL widget generation to render the output of a custom MCP server tool backed by an Apex Invocable Action. TRIGGER only when the prompt EX… |
| `platform-policy-rule-generate` | Use this skill when authoring PolicyRuleDefinition and PolicyRuleDefinitionSet metadata XML for Salesforce Data Cloud governance policies, or when editing *.policyRuleDefinition / … |
| `platform-report-generate` | Use when users create, generate, or validate Salesforce Lightning Report metadata (.report-meta.xml) — tabular, summary, matrix, or joined reports with columns, groupings, filters,… |
| `platform-salesforce-connect-adapter-generate` | Custom Apex adapter generation for Salesforce Connect — connects any external REST API to Salesforce as live, queryable External Objects without ETL or copying. TRIGGER when: conne… |
| `platform-sandbox-configure` | MUST USE this skill for ANY sandbox request — including simply getting a sandbox's details, status, license type, or pending-activation state by name or ID. TRIGGER when the user: … |
| `platform-sharing-owd-configure` | Use when the user wants to retrieve or update Organization-Wide Default (OWD) sharing settings for Salesforce objects. TRIGGER on org-wide defaults, checking/viewing sharing defaul… |
| `platform-sharing-rules-generate` | Use when users get, create, edit, delete, or retrieve Salesforce Sharing Rules metadata for record-level access. TRIGGER on sharing rules, record/criteria-based/role-based/guest-us… |
| `platform-tracing-configure` | Generate EventSettings metadata to enable or disable Platform Tracing (TraceSpanEvent publishing) in Event Monitoring. Use this skill for any EventSettings enablePlatformTracing me… |
| `platform-trial-org-create` | Use this skill to create a Salesforce trial, developer, or Trialforce org against an already-authenticated host org, the same way a developer/Trialforce web signup form provisions … |
| `platform-trust-archive-manage` | ALWAYS USE THIS SKILL for anything involving Salesforce Archive (also called Trusted Services Archive) — search, view, unarchive, analyze, mask, and erase (RTBF) archived records v… |
| `platform-validation-rule-generate` | Use this skill when users need to create, modify, or validate Salesforce Validation Rules. Trigger when users mention validation rules, field validation, data quality rules, formul… |
| `platform-value-set-generate` | Use to create, generate, or validate a Salesforce GlobalValueSet (reusable picklist shared across fields) or customize a StandardValueSet (built-in picklists like Industry, Lead So… |
| `platform-widget-generate` | Use this skill to author a complete HXL WidgetBundle (UEM body + schema.json + -meta.xml). TRIGGER when: user asks for a widget, mosaic, fragment, card, or rich UI surface for any … |
| `sales-call-scoring-configure` | Configure, set up, or repair AI Call Scoring (a.k.a. Call Coaching / Coaching Competencies) on an ECI-enabled Salesforce org. Flips ECICallScoringEnabled via SOAP Metadata API, ena… |
| `tableau-next-asset-create` | Build and edit Tableau Next semantic models (SDMs), vizzes, and dashboards via MCP. TRIGGER when: building a semantic model or dashboard from CSV/Excel files; ingesting a flat file… |
