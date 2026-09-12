# Salesforce — DevOps & Orgs

DevOps Center, pipelines, gestion des orgs (scratch, sandbox, Dev Hub, trials), packaging, post-copy sandbox.

20 skills, copie de [forcedotcom/sf-skills](https://github.com/forcedotcom/sf-skills) au commit `80e068df` (2026-09-11). Ne pas éditer à la main : régénéré par `scripts/sync.py`.

| Skill | Description |
|---|---|
| `automation-sandbox-post-copy-config-generate` | Generate the JSON config file that the Salesforce sandbox post-copy automation tool consumes, from a customer SOP in any format (PDF, xlsx, csv, JSON, docx, Markdown, plain text, o… |
| `automation-sandbox-post-copy-configure` | Apply a Salesforce sandbox post-copy automation JSON config against a target org. For each entry, the skill derives the correct Tooling API sobject from the entry's `ConfigurationN… |
| `dx-app-analytics-query` | ISV App Analytics metadata types — AppAnalyticsQueryRequest and AppAnalyticsSettings. Use this skill when the user asks about retrieving managed package usage data, configuring App… |
| `dx-devops-conflict-resolve` | Use this skill to diagnose and resolve what blocks a DevOps Center promotion of a work item's feature branch: Git merge conflicts and deployment failures. DevOps Center is Git-back… |
| `dx-devops-pipeline-manage` | Use this skill to manage the full lifecycle of a DevOps Center pipeline — list all pipelines, get a single pipeline's details, create a new pipeline linked to a Git repository, add… |
| `dx-devops-project-manage` | Use this skill to list, view, or manage DevOps Center projects in a Salesforce org — show all projects, create a new project, or update an existing project's name, description, or … |
| `dx-devops-promote` | Use this skill to drive the full DevOps Center promotion workflow for work items and pipeline stages — validate preconditions, prepare work items, optionally combine work items tha… |
| `dx-devops-request-status` | Use this skill to poll the status of an asynchronous DevOps Center request — a promotion or deploy operation. Provide the request token returned by dx-devops-promote (the promote r… |
| `dx-devops-test-failures-analyze` | Analyzes DevOps Center test failures and Code Analyzer violations in plain language — failure category, offending file/class/method/line, rule violated, fix direction, and prioriti… |
| `dx-devops-test-pipeline-configure` | Configures DevOps Center pipeline testing infrastructure: enables a test provider so its suites become available, re-syncs a configured provider to pull in new suites, or creates a… |
| `dx-devops-test-suite-assignments-configure` | Recommends and manages DevOps Center test suite assignments for pipeline stages. Mode A analyzes a commit diff against assigned suite metadata to recommend relevant existing suites… |
| `dx-devops-test-suite-run` | Runs DevOps Center test suites on a pipeline stage (Pre-Promote, Post-Promote, or Review event) end to end: triggers async execution via the Connect API after an explicit confirmat… |
| `dx-devops-work-item-manage` | Use this skill to manage the full lifecycle of DevOps Center work items — list, create, update, commit changes, perform status transitions, and create pull requests. Update fields … |
| `dx-org-devhub-configure` | Enable Dev Hub on a Salesforce org and view its scratch org allocation, using the Salesforce CLI (sf). Use when someone wants to turn on or enable Dev Hub, set up an org to create … |
| `dx-org-manage` | INVOKE this skill to execute Salesforce org operations: create scratch orgs, list/display/resume/delete scratch orgs, create org snapshots, open orgs in browser. This skill EXECUTE… |
| `dx-org-permission-set-assign` | ALWAYS USE THIS SKILL to assign permission sets to org users. Assign one or more permission sets to org users using the sf org assign permset command. TRIGGER when the user asks to… |
| `dx-org-shape-manage` | ALWAYS USE THIS SKILL to create, list, or delete org shapes. An org shape is a captured baseline configuration (features, limits, edition, and Metadata API settings) of a source or… |
| `dx-org-switch` | Switches the active Salesforce org (default target-org) using the Salesforce CLI. Use whenever someone wants to change which org CLI commands run against — whether they say \"switc… |
| `dx-org-trial-expiration-check` | Check when Salesforce orgs expire (or already expired) and what to do about it, for one org, the default org, or across all authenticated orgs, using the Salesforce CLI (sf). Use w… |
| `dx-pkg-post-install-configure` | Use this skill to automate managed package post-install configuration. Package-agnostic — works with any managed package (LMA, FMA, work.com, Certinia, etc.). TRIGGER when: user in… |
