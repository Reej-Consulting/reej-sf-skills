# Revenue Cloud — Pricing recipes, procedures and expression sets
> Adapted from [SalesforceLabs/revenue-cloud-foundations](https://github.com/SalesforceLabs/revenue-cloud-foundations) (Apache-2.0), `.cursor/skills/pricing-wiring` and `.cursor/skills/expression-sets`, commit `c850652` — Release 264 / API v68.0. Modified by Reej Consulting: repo-specific tooling removed, content condensed.

Decision table authoring and refresh mechanics live in `decision-tables.md`. This file covers only how pricing references and depends on them.

## Contents

1. Layers and objects
2. Dependency order
3. Expression set structure
4. Metadata API vs Connect API
5. Modifying a standard pricing procedure safely
6. Procedure plans and overlays
7. Price Revision element and compound ramp uplift
8. Debugging checklist
9. Error reference

---

## 1. Layers and objects

A procedure can deploy cleanly and still misprice when a lower layer is missing.

| Layer | Role | Objects / types |
|---|---|---|
| Lookup data | Tables read by pricing steps (list price, adjustments, tiers) | `DecisionTable`, `DecisionTableSourceCriteria` |
| Recipe-table mappings | Bind a pricing recipe to the table each pricing component uses | `PricingRecipe`, `PricingRecipeTableMapping` (Tooling API: `PricingRecipeId`, `LookupTableId`, `PricingComponentType`, e.g. `ListPrice`) |
| Pricing procedure | Expression set with `interfaceSourceType = PricingProcedure` | Metadata type `ExpressionSetDefinition`; see §3.2 |
| Context definition | Attributes/tags the procedure reads and persists | `ContextDefinition`, `ContextAttributeMapping`, `ContextAttrHydrationDetail` |
| Procedure plan | Sections, options and criteria that route to expression sets | `ProcedurePlanDefinitionVersion` |
| Overlays | Data/plan adjustments applied after metadata deploy (plan sections/options, context extensions, procedure step changes) | — |

Split every customization into three layers, each rerunnable as a no-op:

1. **Core**: global defaults most features need (e.g. the recipe mapping for cost book list pricing).
2. **Feature**: additive prerequisites and procedures for one feature. Do not push them into core unless truly global.
3. **Overlay**: post-deploy data and plan adjustments.

Rules:

- An Active decision table does not imply recipe compatibility. The mapping row can still be missing.
- Recipe-table mappings and context attributes are prerequisites the expression set engine does not check. Satisfy them before deploying or activating the procedure.
- Keep metadata org-agnostic. Never commit record IDs.

## 2. Dependency order

1. Activate or refresh lookup artifacts (decision tables).
2. Ensure **core** recipe-table mappings.
3. Deploy core pricing procedures.
4. Ensure **feature** recipe-table mappings.
5. Deploy feature pricing procedures.
6. Apply context-definition updates the pricing features need.
7. Apply procedure-plan and data overlays.
8. Verify (mapping rows, plan invariants, a test reprice), then rerun the chain to prove idempotency.

Validate on a clean org first. Context updates must land before end-to-end pricing tests. A feature deploy failing *before* its mapping step usually hides another missing metadata or field dependency.

Mapping check (Tooling API):

```bash
sf data query --use-tooling-api --target-org <alias> -q "SELECT Id, PricingComponentType FROM PricingRecipeTableMapping WHERE PricingRecipeId IN (SELECT Id FROM PricingRecipe WHERE DeveloperName = '<Recipe>') AND LookupTableId IN (SELECT Id FROM DecisionTable WHERE DeveloperName = '<Table>')"
```

Fast parse signal for one procedure (sandbox):

```bash
sf project deploy start --metadata ExpressionSetDefinition:<Procedure> --dry-run --test-level NoTestRun --json --target-org <alias>
```

## 3. Expression set structure

### 3.1 Types

Each expression set carries an `interfaceSourceType` (on runtime `ExpressionSet`) and a `usageType`. Revenue Cloud uses six of the eleven enum values:

| `interfaceSourceType` | Computes | `usageType` |
|---|---|---|
| `PricingProcedure` | Pricing waterfall: list price, discounts, derived/rounded net price. Runs on quote/order repricing | `DefaultPricing` |
| `DiscoveryProcedure` | Prices shown in Product Discovery, pre-quote | `PricingDiscovery` |
| `RatingProcedure` | Usage rating | `DefaultRating` |
| `RatingDiscoveryProcedure` | Discovery-phase rating | `RatingDiscovery` |
| `QualificationProcedure` | Product qualification/disqualification in Product Discovery | `ProductQualification` |
| `Constraint` | Product Configurator constraint rules, authored in CML | `Constraint` |

Not Revenue Cloud: `EventOrchestration`, `GpaCalculationProcedure`, `IntelligentDecisionStudio`, `ItServiceManagement`. `Sample` is a documentation placeholder: never use it (`usageType: sample` also hides the set from pricing UIs).

Inventory: `SELECT InterfaceSourceType, UsageType, COUNT(Id) FROM ExpressionSet GROUP BY InterfaceSourceType, UsageType`.

**Constraint sets are not step graphs.** CML is stored as a plain-text `.ffxblob`; the step rules below do not apply. Writing the CML (`ExpressionSetDefinitionVersion.ConstraintModel`) on an **active** version succeeds silently and does not redeploy the running model. Reading the field back only confirms the upload. Activation is `ExpressionSetVersion.IsActive`, the same flag the Constraint Builder UI toggles. Verify by exercising the configurator.

### 3.2 Records and identifiers

| Item | Access | Key fields / notes |
|---|---|---|
| `ExpressionSetDefinition` | Metadata API; SFDX `expressionSetDefinition/<Name>.expressionSetDefinition-meta.xml` | Full step graph with `<label>` per step |
| `ExpressionSetDefinition` record (prefix 9QA) | Definition | — |
| `ExpressionSetDefinitionVersion` (prefix 9QB) | Tooling API | `Metadata` (full JSON incl. `steps[].label`), `DeveloperName`, `ExpressionSetDefinitionId`, `VersionNumber`, `ConstraintModel` |
| `ExpressionSet` | Runtime | `InterfaceSourceType`, `UsageType` |
| `ExpressionSetVersion` | Runtime | `IsActive`, `ApiName`. Source of truth for version identity |

At rest, 9QB `DeveloperName` equals the runtime version `ApiName` (9QM). That join breaks after a Connect PATCH (§4.4).

Definition-level fields: `usageType`, `resourceInitializationType` (immutable once set; `Default` is common), `contextDefinitions[]` (bound context, with `id`), version `variables[]` and `steps[]`.

### 3.3 Step graph

- `steps[]` is **flat**. Hierarchy is `parentStep` = the parent's step **name**.
- `sequenceNumber` is execution order, **scoped per parent**: children restart at 1.
- `name` is a spaceless API name (the `parentStep` key). `label` is UI text. Names derive from labels, de-spaced, sometimes with a uniqueness suffix.
- References: `customElement.parameters[]` with `type: Parameter` (name in `value`) or `type: Formula` (field names inside the expression string), and `advancedCondition.criteria[].sourceFieldName`.
- Element kinds in pricing procedures: `ListGroup` (first child must be a list filter such as `AdvancedListFilter`; cannot be empty), `AssignmentElement`, `FormulaBasedPricing`, `GroupingAndAggregatePricing`, `DiscountDistributionService` (DDS), `PriceRevision`, `BreakdownLineMapping` (Map Line Item), the `ListPrice` lookup step, `GetOutputsFromDecisionTable`. BKM steps use `stepType: BusinessKnowledgeModel`.

### 3.4 Variables, context and dependency scopes

- Version `variables[]` have `type` `Constant`, `Variable`, `LocalListVariable`, etc.
- A step's **output** variable is created implicitly from its output param (`section-N-output` on aggregates, `formula-section-N-output` on formulas). Never declare it again as a variable.
- Inside a list group that uses a business element, use a list variable, not a local variable.

Every name a step references falls into one scope:

| Scope | Recognize by | Target org needs |
|---|---|---|
| Version variable | Listed in the source version `variables[]` | Add it if missing (inputs only) |
| Custom dependency | `__c` / `__r` field, or custom context node | Must already exist and be mapped into the bound context definition |
| Standard context | `__std` suffix or no suffix (`NetUnitPrice`, `ItemDetailListPrice__std`) | Nothing; supplied by the standard context |

A step copied from another org looks self-contained because the source org has its variables and fields. Classify every reference first. Custom fields can hide inside `Formula` strings: scan the formula text.

Context rules:

- Every attribute/tag the procedure reads must exist in the target context definition. A missing key deploys fine and fails at quote save or pricing (`Invalid tag attribute name key`).
- Transient attribute (computed at runtime, not read from a record): node-level `ContextAttributeMapping` with an sObject but no source field, hence no `ContextAttrHydrationDetail`. Add a source field only when the attribute must hydrate.

### 3.5 How pricing steps reference decision tables

- `LookUpApiName` = target `DecisionTable.DeveloperName`. Default choice, org-agnostic.
- `LookUpId` = record ID. Use only for a known org/runtime issue. Resolve it per target org before deploy: placeholder tokens are not valid record IDs and the Metadata API rejects them. **At most one** `LookUpId` parameter per step; a duplicate gives a generic "unexpected error" at deploy.
- `GetOutputsFromDecisionTable` consumes a table's output through a `DecisionTable` parameter.
- **Multicurrency:** pass `CurrencyIsoCode` on **every** lookup step returning a currency amount (list price, adjustment schedule, adjustment tier). Without it, the step matches the first row for the product in any currency: plausible wrong price, no error.
- A lookup reads a point-in-time snapshot of the table's source object. Rows written after the last refresh are invisible, silently (§8.1).

## 4. Metadata API vs Connect API

| | Metadata API | Connect API |
|---|---|---|
| Artifact | `ExpressionSetDefinition` XML | JSON on `/connect/business-rules/expression-set` (GET, POST, PATCH, DELETE) |
| Use for | Source-controlled, diffable, build changes | Runtime CRUD, exploration, org-to-org capture |
| Shapes | Identical step/param/variable shapes. XML adds `<label>`, keeps the misspelled `<shouldExposExecPathMsgOnly>`, omits empty `*MessageTokenMappings` | Same, no `label` field |
| Parent/child steps | Full nested graphs deploy | Flat `steps[]`, hierarchy via `parentStep` |
| Escaping | XML parser decodes entities | GET output is HTML-escaped; unescape before sending |
| Errors | Specific and actionable | Often opaque |
| Labels | Preserved | Every full-graph PATCH resets labels to `name` |
| Activation | No deactivate/reactivate cycle described for the set itself (see note) | Enabled version cannot be modified or deleted |

**Note, sources disagree.** The expression-set material says the Metadata path needs no activation lifecycle. The pricing troubleshooting says an active `ProcedurePlanDefinitionVersion` referencing the set blocks a Metadata deploy (generic "unexpected error"), and lists ES-version deactivation as a check for active-version update failures. Safe practice: on such a failure, deactivate the referencing plan version (then the ES version if needed), deploy, reactivate.

### 4.1 Connect mutation lifecycle

1. Validate the full payload while the version is still active: target and parent steps exist, no duplicate variables. A typo then fails before anything is deactivated.
2. If an active `ProcedurePlanDefinitionVersion` references the procedure, deactivate it first. It locks the ES version.
3. Deactivate the `ExpressionSetVersion`.
4. Strip output-only top-level `id`/`error`. HTML-unescape every string leaf.
5. POST (create) or PATCH (replace). PATCH replaces the full graph: GET, merge, send everything.
6. On success, reactivate the ES version (`enabled: true` in the PATCH body already does it), then the plan version.
7. On failure, leave the ES version **deactivated**. PATCH is not atomic; a half-applied graph must not be re-enabled. Inspect, restore, then reactivate both.

### 4.2 Verb rules

| Concern | POST (create) | PATCH (replace) |
|---|---|---|
| Version-level `id` | Omit | Keep |
| Top-level `id`, `error` | Strip | Strip |
| `contextDefinitions[].id` | Keep | n/a |
| `resourceInitializationType` | Set correctly; immutable afterwards | Must equal stored value |
| `usageType` | `DefaultPricing` for pricing, `Bre` for BRE | Unchanged |

To clone, change top-level `apiName`, top-level `name` **and** version `apiName`, and omit the version `id`. A PATCH cannot rename a version.

### 4.3 Reading GET output

- Top-level steps come back **alphabetically by name**. Sort by per-parent `sequenceNumber`.
- JSON-in-string values (`customElement.parameters[].value`, `advancedCondition.criteria[].value`, formula text) are HTML-escaped (`&quot;`, `&#39;`).
- GET can transiently serve a stale version apiName. Read version identity from `ExpressionSetVersion`.

### 4.4 Tooling path: labels and new versions

- Labels live in `ExpressionSetDefinitionVersion.Metadata.steps[].label`: `GET` / `PATCH tooling/sobjects/ExpressionSetDefinitionVersion/{9QB}`. PATCH sends the whole `Metadata` (drop read-only `urls`). Join to Connect steps by `name`.
- A Tooling `Metadata` PATCH on an **active** version is rejected and not persisted. Deactivate (`ExpressionSetVersion.IsActive`), PATCH, reactivate; labels survive.
- Appending a step through a Tooling `Metadata` PATCH fails. For new-version semantics, Tooling-create a new `ExpressionSetDefinitionVersion` from the prior version's `Metadata` (create-with-content), or deploy via Metadata API.
- Connect writes and Tooling labels are mutually exclusive on one version. Relabel **last**; redo it after any later Connect write.
- A Connect PATCH can rewrite the 9QB `DeveloperName` in place (observed 262 / v67.0). After one, resolve the 9QB by `ExpressionSetDefinitionId` (+ `VersionNumber`), not by `DeveloperName`.
- Steps that must ship with readable labels: author `<label>` in the Metadata XML.

## 5. Modifying a standard pricing procedure safely

1. Identify the procedure actually in use: `PricingProcedure` sets and their active `ExpressionSetVersion`. Never assume the template default name.
2. Retrieve it (`ExpressionSetDefinition`) and/or export it via Connect GET.
3. Experiment on a **disposable clone** (§4.2), never on the shipped procedure, except for an intentional, approved change. The 264 Help path for features like compound uplift is also "clone the template".
4. Make minimal additive deltas on the stable baseline structure.
5. Classify each new step's references (§3.4). Add only input variables. Confirm custom fields exist and are mapped in the bound context.
6. Check placement (§5.1) and removals (§5.2).
7. Satisfy prerequisites in order (§2).
8. Deactivate plan version, then ES version; apply; reactivate (§4.1). On the Metadata path, dry-run first.
9. If Connect was used, relabel last.
10. Verify **functionally**: test reprice of each affected scenario, re-export and diff the graph. Reactivation proves structure only.
11. Apply to the real target only after the clone passes. Rerun to confirm idempotency.

### 5.1 Placement and ordering

- Adding a top-level step: set its slot among siblings and renumber them. Child steps keep `parentStep` and their per-parent `sequenceNumber`. List the parent before its children.
- The procedure ends with a fixed **tail**: DDS, `GroupingAndAggregatePricing` aggregates, Rounding Rules. A `FormulaBasedPricing` step after the tail is rejected with an error that names DDS, not your step.
- Aggregates are pinned after DDS by a data dependency: DDS rewrites per-line `NetUnitPrice` / `ItemNetTotalPrice` that `TotalAmount` sums. Moving aggregates up drags the barrier with them.
- A top-level header formula placed *before* the tail is accepted, but its operands hold values hydrated from the record at reprice start: it lags one reprice. For a header value derived from aggregates, use a record formula field or an earlier derivation step.
- New SUM aggregates: place them right after the last existing aggregation.
- If line cost/margin are computed before DDS, a header margin % built from `SUM(line margin) / TotalAmount` mixes pre- and post-header-discount bases. Cost totals are unaffected.
- Map Line Item (`BreakdownLineMapping`): the documented path is the UI paste. Programmatically, place it right after Pricing Setting and author `sectionJsonStringN` values unescaped. A Metadata `<steps>` block also works.

### 5.2 Removing steps

1. Engine validation is **structural, not functional**. A removal that reactivates can still leave a `ListGroup`/filter with nothing computing its subset: silent mispricing.
2. Before removing a producer, list every consumer of its outputs and every filter selecting its target lines. Rewire or remove them.
3. A context mapping that persisted the removed step's output does not error. The field stays null on every reprice. Remove the mapping or accept it as inert.
4. Remove on a clone, then run a functional test.

## 6. Procedure plans and overlays

- An active `ProcedurePlanDefinitionVersion` that references a procedure blocks ES-version deactivation and Metadata deploys of that set. Its "unexpected error" differs from the ES-version lock. Pair every procedure change with a plan-version deactivate/reactivate.
- Never edit an active plan version without that cycle.
- Never insert a section into an occupied sequence before moving the existing one out.

Overlay procedure:

1. Deactivate the plan version.
2. Create or patch the declared sections (one row per `subSectionType`).
3. Compute the final order from the org's current state. Declare placement by anchor ("after section X"), not by a hard-coded number.
4. Resequence through a temporary high range to avoid collisions.
5. Resolve parent IDs by SOQL. Avoid data-loader relationship-traversal upserts unless proven idempotent on the target.
6. Create or patch options (per section: `priority`, expected expression set), then criteria if any (per option: `sequence`, `fieldPath`, `operator`).
7. Verify: exactly one row per section, option and criterion; anchored sections sit immediately after their anchor.
8. Reactivate the plan version in a guarded `finally`.

Independent overlays on the same anchor need an explicit ordering convention; otherwise run order decides. An overlay that only succeeds on rerun usually relies on fixed numbers or separate manual moves.

## 7. Price Revision element and compound ramp uplift (264)

Compound uplift applies each ramp segment's uplift on the prior segment's factor, not on list price. Help: *Compound Uplift in Ramp Deals*, *Create Ramp Deals with Standard or Compound Price Uplifts*, *Use the Price Revision Element in a Pricing Procedure*.

Prerequisites:

1. **Revenue Settings → Advanced Detail Line Pricing ON.** Off, Compound is hidden from the Ramp Uplift Type picklist. Turning it off after compound quotes/orders/assets exist corrupts pricing, amendments and renewals.
2. **Group ramp.** Line-level `createRampDeal` yields segments with `QuoteLineGroupId = null`: nothing holds the uplift mode. The legacy `/commerce/…/ramp-deals` API does not produce the group either.
3. **`RampUpliftType = 'Compound'` on the ramp group**: the top-level `RampScheduleGroup` when Multiple Ramp Schedules Per Transaction is on, else the single ramp segment group. Read-only on `QuoteLineItem`, `OrderItem` and segment groups; it cascades to ramped lines.
4. **Ramp-path `PriceRevision` element** with `IsCompoundUpliftEnabled = true` ("Enable Compound Uplift") and all bindings set:

| Binding | Rule |
|---|---|
| Ramp Identifier | Groups segments; lines without one price independently |
| Base Price Multiplier | Blank ⇒ 1 on new sale; amend/renew use the prior compounded multiplier |
| Uplift Method | Blank ⇒ silently **standard** uplift |
| Effective From / To | Each segment needs a **unique** Effective From; missing or duplicate fails pricing for the whole ramp group |

5. **`UnitPriceUplift` per segment** (writeable). The first segment is the baseline; a 0% segment carries the prior multiplier over.

Gotchas:

- The checkbox appears only once a lookup table is selected. Changing or removing that table clears it.
- Help says compound "requires a newly-created procedure". That is a UI builder limitation; deploying full expression-set metadata bypasses it.
- Help path: clone the template, add a map line item mapping `ItemApplUnitPriceUpliftPct__std` → `itemDetailApplUnitPriceUpliftPct__std`, sync the context. The source observed these ramp attributes as standard in base `SalesTransactionContext` (264).
- Math, in percent: `applied%(n) = [(1 + applied%(n-1)/100) × (1 + UnitPriceUplift%(n)/100) − 1] × 100`; `NetUnitPrice(n) = base × (1 + applied%(n)/100)`. 5% then 3% gives 8.15.
- Unsupported: CPI renewal uplift, usage-based pricing, derived pricing. Compound resets on renewal. Pre-Winter '27 records use standard uplift.
- Check: `SELECT RampUpliftType, COUNT(Id) FROM QuoteLineGroup GROUP BY RampUpliftType`; per quote, compare `UnitPriceUplift`, `ApplUnitPriceUpliftPct`, `NetUnitPrice` on `QuoteLineItem` ordered by `StartDate`.

## 8. Debugging checklist

### 8.1 Price wrong or not applied

1. Lookup step error: see §9.
2. **Stale decision table.** Compare each table's `DecisionTable.LastSyncDate` with `MAX(LastModifiedDate)` of **its own** source object, filtered by **its own** `DecisionTableSourceCriteria` (`SourceFieldName`, `Operator`, `Value`). Use `LastModifiedDate`: edited rows invalidate too. `LastSyncDate` earlier than newest = stale. Null newest = cannot be stale. `RefreshStatus` / `RefreshFailureReason` only exist once a refresh was accepted.
3. **Contract prices** (`ContractItemPrice`, `ContractItemPriceAdjTier`). If a table filters on activated contracts, refresh on activation, not creation: a refresh at Draft stamps `LastSyncDate` while excluding the rows. Bulk loads that end without activation need a manual refresh. Criteria path `ContractItemPriceId.ContractId` becomes `ContractItemPrice.Contract` in SOQL.
4. **`refreshDecisionTable` in a Flow.** An invalid or inactive `DecisionTableApiName` raises a Flow fault and leaves no trace on any table; an accepted refresh returns `Queued`. Add a `faultConnector`, mandatory in after-save flows: an unhandled fault rolls back the triggering save.
5. **Currency.** `CurrencyIsoCode` on every lookup step (§3.5). Records created by quick actions and flows take the running user's currency, not the account's: wire inheritance explicitly. `AssetRateCardEntry` does not inherit its Asset's currency (262, no config remedy): use a before-save flow.
6. **Orphaned subset** after a step removal (§5.2).
7. **Header value one reprice behind**: formula before the tail (§5.1).
8. **Field stays null**: producing step removed, or transient mapping expected to hydrate (§3.4).
9. **No compounding**: Uplift Method blank, lookup table changed, Advanced Detail Line Pricing off, line-level ramp (§7).

### 8.2 Procedure not invoked

1. `usageType` is not `DefaultPricing`: the set does not surface in pricing UIs or run.
2. No active `ExpressionSetVersion`. A failed Connect PATCH leaves it deactivated by design.
3. Plan version left inactive, or sections/options/criteria missing, duplicated, misordered, or pointing at another expression set (§6 step 7).
4. Recipe-table mapping missing or wrong `PricingComponentType`.
5. Context key missing (`Invalid tag attribute name key`).

### 8.3 Wrong version active / change not visible

1. Check `ExpressionSetVersion.IsActive`, not the Connect GET body.
2. A new version was created (create-with-content) but the old one is still active.
3. Labels back to run-on names: a Connect PATCH ran after the relabel.
4. 9QB lookup by `DeveloperName` returns 0 rows right after a Connect PATCH (§4.4).
5. Constraint model unchanged: CML written on an active version (§3.1).
6. Deploy rejected with a generic error: active plan-version lock (§6).

## 9. Error reference

| Error | Cause | Fix |
|---|---|---|
| `Ensure that the lookup table in the ListPrice step is valid and try again.` | Unresolved lookup ID, missing table, or missing recipe-table mapping | Check in order: ID resolution, table exists, mapping row exists, `PricingComponentType` correct |
| `ExpressionSetDefinition … unexpected error occurred` (deploy) | Active plan version references the set; duplicate `LookUpId` in a step | Deactivate plan version, deploy, reactivate; targeted dry-run; diff against last good version; one `LookUpId` per step |
| Deploy rejects lookup IDs | Placeholder or foreign-org ID | Resolve per org, or use `LookUpApiName` |
| `Invalid tag attribute name key: [<Attr>]` | Attribute missing from target context, or wrong context/mapping | Add attribute to the bound context definition before pricing tests |
| `Syntax error. Found '&'` / `INVALID_INPUT: Error processing JSON` | HTML-escaped GET output resent | Unescape string leaves |
| `Specify a valid data type for the … variable` | POST without `contextDefinitions[].id` | Keep it on create |
| `You can't modify the apiName of an expression set version.` | Rename attempted via PATCH | Clone: new top-level `apiName`, `name`, version `apiName`; omit version `id` |
| `JSON_PARSER_ERROR: Unrecognized field "label"` | `label` sent to Connect | Labels via Tooling or XML only |
| `INVALID_INPUT` on step name | Spaces in `name` | API-name style |
| `INVALID_INPUT: A context variable with the name '<Name>' already exists.` | Step output also declared as variable | Declare inputs only |
| `INVALID_INPUT: You can add the Discount Distribution Service element only before the Rounding Rules and Aggregate elements …` | A `FormulaBasedPricing` step after the tail | Move it before the tail or compute elsewhere (§5.1) |
| `FIELD_INTEGRITY_EXCEPTION` | Step appended via Tooling `Metadata` PATCH | Create-with-content or Metadata deploy |
| `INVALID_ID_FIELD: LatestVersionSnapshotId not found …` | Tooling `Metadata` PATCH on active version | Deactivate, PATCH, reactivate |
| `ListGroup can not be empty` / `Select list filter as the first element in list group` | Malformed list group | Add children; list filter first |
| `Local variables aren't supported when a business element is used in a list group; specify a list variable` | Local variable in list group | Use a list variable |
| `The decision table API Name is invalid…` (Flow fault) | Bad or inactive `DecisionTableApiName` on refresh | Fix the name; add a fault connector |
| Change of `resourceInitializationType` rejected | Immutable after creation | Set it right at POST |
