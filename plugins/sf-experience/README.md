# Salesforce — Experience, LWC & Mobile

Experience Cloud, LWC, LDS/GraphQL, UI bundles React, CMS, Commerce B2B, Mobile SDK.

42 skills, copie de [forcedotcom/sf-skills](https://github.com/forcedotcom/sf-skills) au commit `bfca400c` (2026-09-08). Ne pas éditer à la main : régénéré par `scripts/sync.py`.

| Skill | Description |
|---|---|
| `commerce-b2b-open-code-components-integrate` | Integrate Salesforce B2B Commerce open source components from GitHub into B2B Commerce stores. Use when users mention \"integrate open code components\", \"open source B2B commerce… |
| `commerce-b2b-open-code-components-replace` | Replace OOTB (out-of-the-box) B2B Commerce components with open source equivalents in site metadata content.json files, or look up the equivalent open code `site:` component for OO… |
| `commerce-b2b-store-create` | Interactive workflow to create Commerce B2B Stores and retrieve storefront metadata. Use when users want to: create B2B Commerce stores, build Commerce storefronts, set up B2B stor… |
| `experience-accessibility-validate` | Use this skill to determine whether a Lightning Web Component (LWC) is accessible and meets WCAG accessibility guidelines. TRIGGER when the user asks \"is my component accessible?\… |
| `experience-aura-lwc-migrate` | Use this skill to analyze a Salesforce Aura component bundle (.cmp, .app, .evt, .intf, Controller.js, Helper.js, Renderer.js) and produce a framework-agnostic migration blueprint (… |
| `experience-cms-brand-apply` | Extracts, retrieves, and applies CMS brand guidelines (voice, tone, style, colors, typography) to generated content. Use this skill ANY TIME a user request involves branding, brand… |
| `experience-cms-brand-create` | Author a Salesforce Digital Experience brand (a \"brand.json\") so the VS Code Brand Toolkit can load, edit, and preview it. Use this skill whenever someone wants to: create a bran… |
| `experience-cms-content-generate` | Creates, edits, and publishes Salesforce CMS content of any kind — any domain, any topic. Single and bulk: create many in parallel, edit one or many, publish all or a subset. Use t… |
| `experience-cms-content-render` | Renders, embeds, or displays existing Salesforce CMS content in a React or Angular uiBundle app: installs the CMS toolkit package, registers a typed reference, generates a framewor… |
| `experience-cms-content-type-generate` | Salesforce CMS ContentTypeBundle creation skill. Use this skill ANY TIME a user request involves creating a ContentTypeBundle, and activate FIRST when CMS ContentTypeBundle creatio… |
| `experience-content-media-stock-image-search` | Searches for and downloads ethically-licensed stock images via the media-management MCP server. Use this skill whenever a user wants an image, photo, or picture — for BOTH requests… |
| `experience-lds-best-practices-apply` | Use when reviewing or implementing Lightning Data Service best practices in an LWC (.js, .html, .js-meta.xml) — UIAPI vs Apex, refreshApex / notifyRecordUpdateAvailable, @salesforc… |
| `experience-lds-data-requirements-generate` | Use when a Lightning Web Component data need is described in ambiguous natural language — turn \"get contact info\" or \"show account data\" into a clear, PRD-ready data-requiremen… |
| `experience-lds-graphql-generate` | Use ALWAYS when a prompt mentions GraphQL, lightning/uiGraphQLApi, @wire(graphql, ...), or gql template tags in an LWC context — even if the surface ask is \"build an LWC\". Owns t… |
| `experience-lwc-accessibility-jest-run` | Use ALWAYS when running Sa11y accessibility Jest tests for a Lightning Web Component — locally before pushing, producing the exact command(s), running one file vs a whole suite, se… |
| `experience-lwc-base-components-integrate` | Pick the right Lightning Base Component (`lightning-*`) for a given UI task, retrieve its full API (props, methods, events, slots) from the bundled per-component reference, and wir… |
| `experience-lwc-design-generate` | Use when you need to create a brand new Lightning Web Component from a Figma design, a Product Requirements Document, or another design artifact — orchestrating the five-phase work… |
| `experience-lwc-generate` | Lightning Web Components with PICKLES methodology and 165-point scoring. Use this skill when the user creates or edits LWC components, builds wire service patterns, or writes Jest … |
| `experience-lwc-rtl-validate` | Use this skill to review a Lightning Web Component (.html, .js, .css files) for right-to-left (RTL) internationalization correctness, producing a finding list with code-level fixes… |
| `experience-lwc-runtime-observe` | Use when running Salesforce Lightning Preview for an app or a single LWC component to extract the runtime DOM for inspection. TRIGGER when the user says \"preview an LWC locally\",… |
| `experience-lwc-security-validate` | Use this skill as THE specialized Lightning Web Security (LWS) validator for a Lightning Web Component bundle (`.js`, `.ts`, `.html`, `.css`, `.js-meta.xml`) — the canonical LWS/Pr… |
| `experience-lwc-typescript-migrate` | Use when converting an existing JavaScript Lightning Web Component (.js, .html, .css) to TypeScript with full type annotations and a matching `.d.ts` file that exposes only the com… |
| `experience-lwr-site-generate` | Creates, modifies, or manages Salesforce Experience Cloud LWR sites via DigitalExperience metadata. Always trigger when the tasks involve LWR sites configurations, e.g. creating/mo… |
| `experience-portal-create` | Create / provision / set up a NEW Digital Experience (Communities) / Experience Cloud site — employee service, IT support, help desk, HR, customer, and partner portals — via the he… |
| `experience-search-coordinate` | Searches for and retrieves existing content and media (articles, blogs, news, FAQs, events, products, images, logos, icons, photos, graphics, banners, hero images, audio clips, vid… |
| `experience-ui-bundle-2gp-deploy` | MUST activate when the user wants to package, distribute, or install/upgrade/uninstall/promote a UI Bundle as a Salesforce second-generation (2GP) package (project may contain uiBu… |
| `experience-ui-bundle-agentforce-client-generate` | Use this skill when the user asks to add, embed, integrate, configure, style, or remove an agent, chatbot, chat widget, conversation client, or AI assistant in a UI Bundle project … |
| `experience-ui-bundle-app-coordinate` | MUST activate when the user wants to build, create, or generate a React application, React app, web application, single-page application (SPA), or frontend application — even if no… |
| `experience-ui-bundle-custom-app-generate` | MUST activate when the project contains a uiBundles/*/src/ directory and the task involves creating or configuring a Custom Application for hosting a UI bundle in Lightning Experie… |
| `experience-ui-bundle-deploy` | MUST activate when the project has a uiBundles/*/src/ directory and the task involves deploying to an org or post-deploy org setup. Deploys a UI bundle app and runs ordered setup: … |
| `experience-ui-bundle-features-generate` | MUST activate when the project contains a uiBundles/*/src/ directory and the user wants to add a pre-built feature — such as authentication (login, logout, protected routes, sessio… |
| `experience-ui-bundle-file-upload-generate` | MUST activate when the project contains a uiBundles/*/src/ directory and the task involves uploading, attaching, or dropping files. Use this skill when adding file upload functiona… |
| `experience-ui-bundle-frontend-generate` | MUST activate before editing ANY file under uiBundles/*/src/ (or the bundle's index.html) for visual or UI changes to an EXISTING app — pages, components, sections, layout, styling… |
| `experience-ui-bundle-localize` | MUST activate to localize / internationalize a uiBundles/*/src/ project (React or Angular): extract hardcoded user-facing strings into Custom Labels, wire a runtime i18n library ov… |
| `experience-ui-bundle-metadata-generate` | Use this skill when adding a front-end React UI bundle to an existing project or configuring UI bundle metadata and config files. TRIGGER when: adding or scaffolding a new UI bundl… |
| `experience-ui-bundle-mfa-configure` | Configure Multi-Factor Authentication (MFA) for Salesforce Experience Site users. TRIGGER when: user wants to enable MFA on a community, enforce two-factor authentication for porta… |
| `experience-ui-bundle-project-generate` | Generates a minimal, ready-to-develop SFDX starter project from template instead of hand-scaffolding files. Use this skill when starting a brand-new Salesforce UI bundle app (React… |
| `experience-ui-bundle-salesforce-data-access` | MUST activate whenever a uiBundles/*/src/ project reads, writes, or displays Salesforce data — INCLUDING building a page, list, table, card grid, dashboard, or form that shows, fil… |
| `experience-ui-bundle-site-generate` | MUST activate when the project contains a uiBundles/*/src/ directory and the task involves creating or configuring site infrastructure. Use this skill when creating or configuring … |
| `mobile-apps-create` | The entry point for building any Salesforce native mobile app on iOS or Android. TRIGGER when the user says: \"build a Salesforce iOS app\", \"add Salesforce login to my Android ap… |
| `mobile-platform-native-capabilities-integrate` | Build a Salesforce LWC that uses native mobile device capabilities — barcode scanner, biometrics, location, NFC, calendar, contacts, document scanner, geofencing, AR space capture,… |
| `mobile-platform-offline-validate` | Review a Lightning Web Component for **mobile offline** compatibility — the Komaci offline static analyzer that pre-primes the data graph for Salesforce Mobile App Plus and Field S… |
