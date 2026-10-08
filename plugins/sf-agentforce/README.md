# Salesforce — Agentforce & Data 360

Agentforce avancé (tests, observabilité, persona, migration Einstein Bots, canaux), Data 360 / Data Cloud, Models API. L'écriture d'Agent Script est dans sf-core.

14 skills, copie de [forcedotcom/sf-skills](https://github.com/forcedotcom/sf-skills) au commit `e5164d94` (2026-10-07). Ne pas éditer à la main : régénéré par `scripts/sync.py`.

Dépend de `sf-core` (socle), installé automatiquement avec ce plugin.

| Skill | Description |
|---|---|
| `agentforce-bot-upgrade` | Use this skill to Upgrade Einstein Bots into Agentforce agents end-to-end in a single pass, orchestrating per-bot Agent Spec generation, planner reconciliation across bots, agentfo… |
| `agentforce-d360-analyze` | Data Cloud 360° view of a single Agentforce session. TRIGGER when user asks to trace, inspect, summarize, or describe a specific Agentforce session by session id (Agent Session UUI… |
| `agentforce-observe` | Analyze production Agentforce agent behavior using session traces and Data Cloud, and manage Agent Health Monitoring (AHM) alerts. TRIGGER when: user queries STDM session data or D… |
| `agentforce-persona-generate` | Use to design an AI agent persona — identity, voice, tone, behavioral style, guardrails — and encode it into Agent Script (.agent files) or Agentforce Builder field values. Runs fo… |
| `agentforce-test` | Write, run, and analyze structured test suites for Agentforce agents — functional AND security. TRIGGER when: user writes or modifies test spec YAML (AiEvaluationDefinition); runs … |
| `data360-code-extension-generate` | Develop and deploy Data Cloud Code Extensions using SF CLI plugin. Use this skill when creating custom Python transformations for Data Cloud, deploying code extensions, or testing … |
| `data360-schema-get` | Retrieve Data Lake Object (DLO) and Data Model Object (DMO) schema information from Salesforce Data Cloud using REST APIs. Use this skill when you need to inspect DLO or DMO field … |
| `platform-agenticsetup-categories-get` | Get agentic setup prompt categories from a connected Salesforce org using the Connect API via sf api request rest. Use this skill to call GET /services/data/vXX.0/agenticsetup/cate… |
| `platform-models-api-configure` | Configure (or troubleshoot) an AI coding agent or CLI to route through the Salesforce Models API using a signed OrgJWT. Use this skill when pointing an agent at the Salesforce mode… |
| `platform-tracing-agentforce-configure` | Generate AgentforcePlatformTracingSettings metadata to enable or disable Agentforce agent execution trace spans flowing to Data Cloud. Use this skill for any AgentforcePlatformTrac… |
| `sales-agentforce-pipeline-management-configure` | Use to configure, set up, or repair the Sales Management agent and Agentforce Pipeline Management in a Salesforce org. Automates metadata creation for flows, prompt templates, perm… |
| `service-agentforce-channel-configure` | Wires an existing, active Agentforce agent to a channel by resolving a fallback queue, setting up inbound routing (either PATCH SessionHandlerId on the MessagingChannel, or an inbo… |
| `service-agentforce-contact-center-coordinate` | Coordinates end-to-end setup of an Agentforce Contact Center voice channel: gathers country and phone-number-type selections, procures a chosen number, resolves its CommunicationCh… |
| `service-agentforce-human-escalation-configure` | Use to configure and verify Agentforce agent-to-human escalation, including human handoff, a staffed fallback queue, and failure-threshold directives. Triggers: configure agent esc… |
