# Revenue Cloud — Context Definitions
> Adapted from [SalesforceLabs/revenue-cloud-foundations](https://github.com/SalesforceLabs/revenue-cloud-foundations) (Apache-2.0), `.cursor/skills/context-service`, commit `c850652` — Release 264 / API v68.0. Modified by Reej Consulting: repo-specific tooling removed, content condensed.

**Contents**

1. [Concepts and standard definitions](#1-concepts-and-standard-definitions)
2. [Data model](#2-data-model)
3. [Definition types and versioning](#3-definition-types-and-versioning)
4. [Extending a standard definition](#4-extending-a-standard-definition)
5. [Activation lifecycle](#5-activation-lifecycle)
6. [Deployment: Metadata API vs Connect API](#6-deployment-metadata-api-vs-connect-api)
7. [Upgrades between releases](#7-upgrades-between-releases)
8. [Runtime: hydrate, query, persist](#8-runtime-hydrate-query-persist)
9. [Debugging checklist and errors](#9-debugging-checklist-and-errors)

Behaviors were observed live on Release 262 / API v67.0 and pinned to 264 / v68.0 by the source: re-verify edge cases on the target release. Connect paths are relative to `/services/data/v68.0/`. With `sf api request rest`, pass the **fully versioned path**: a bare `connect/...` path returns an HTML "URL No Longer Exists" page (404, or 501 on PATCH), not a missing endpoint.

---

## 1. Concepts and standard definitions

A **Context Definition** is design-time schema for the data layer that pricing, BRE / expression sets, the configurator, DocGen, billing and DRO bind to at runtime. It declares **nodes** (an object hierarchy) and **attributes**, and **maps** attributes to SObject fields. At runtime an engine **hydrates** an instance via SOQL on the mapped SObjects (honoring FLS), reads and writes attributes **by tag**, and can **persist** values back.

Standard definitions are file-based, suffixed `__stdctx`, and not editable: you **extend** them.

| Standard context | Use / availability |
|---|---|
| Sales Transaction (`SalesTransactionContext__stdctx`) | Most-used; read by pricing and DocGen procedures; always provisioned. Its header node binds to Quote, Order or Sales Agreement depending on the mapping. Inherits a reference to `AssetContext__stdctx` so line pricing can reach the related Asset (renewals, amendments, asset-state lookups). |
| Product Discovery | Foundational, always provisioned. |
| Asset (`AssetContext__stdctx`) | Edition-dependent. |
| Cart, Billing, Fulfillment Asset, Collection Plan Segment, Rate Management, Rating Discovery, Contracts, Contracts Extraction | Edition-dependent; Cart and plain Contracts are the most often absent on lean editions. |

Check what the org provisioned: `GET connect/context-definitions?includeInactive=true&includeUpgrade=true`.

**Sales Transaction shape.** 4-level tree `SalesTransaction` → `SalesTransactionItem` → `SalesTransactionItemDetail` → `SalesTrxnItemRateCardEntry`, plus sibling nodes. Entity mappings (all four intents) include `QuoteEntitiesMapping` (→ Quote), `OrderEntitiesMapping` (→ Order), `SalesAgreementEntitiesMapping` (→ SalesAgreement), `QuoteToContractSlsTrxnMapping` (→ Quote, to-Contract lens). Link mappings (`ASSOCIATION` only): `SalesTransactionToAssetMapping`, `AssetToSalesTransactionMapping`, `ContractToSalesTxnMapping`, `SalesTxnItmToAssetStatePrdMap`, `AssetStatePrdToSalesTxnItmMap`, `ProductDiscoveryContextMapping`.

---

## 2. Data model

### 2.1 Version-centric, two layers

```
ContextDefinition                    (developerName, label; no IsActive)
└─ ContextDefinitionVersion          (IsActive here; exactly one per definition)
   ├─ Layer 1: abstract schema, no SObject
   │  └─ ContextNode                 (parentNodeId / childNodes)
   │     └─ ContextAttribute         (name, dataType, fieldType, isTransient, isKey/isValue)
   │        └─ ContextTag            (attributeTags)
   └─ Layer 2: SObject bindings, one "lens" per mapping
      └─ ContextMapping              (exactly one isDefault)
         └─ ContextNodeMapping       (contextNodeId → sObjectName)
            └─ ContextAttributeMapping       (contextAttributeId → field)
               └─ ContextAttrHydrationDetail (sObjectDomain + queryAttribute; ≤ 1 per attribute mapping)
```

1. Layer 2 **references** Layer 1 by id, so one node binds to a different SObject in each mapping. Binding an attribute is a separate step, repeated **per mapping**; an attribute may have no binding in a mapping.
2. The **default mapping** (`isDefault: true`) is the lens engines use unless told otherwise.
3. `ContextAttrHydrationDetail` is the **only** binding object, for read and write: persist runs it backward.
4. The source field is `contextAttrHydrationDetailList[].queryAttribute` (+ `sObjectDomain`); `mappedField` is empty on inherited mappings. Join field ↔ attribute ↔ tag on `contextAttributeId`.
5. The Connect GET nests nodes under `childNodes` (`{contextNodes: [...]}` wrapper or bare list) and attributes under `attributes` (`contextAttributes` wrapper or bare list): parse both.
6. Parent → child traversal is carried by relationship-typed attributes shipped with the base (e.g. `SalesTransactionItemParent`, `parentNodeMappingId`). A plain value attribute creates no relationship.
7. A version also holds `contextDefinitionFilters` (`connect/context-definitions/<id>/filters[/<filterId>]`), `contextDefinitionTransformations` and per-node-mapping `contextDictionaries` (empty on standard bases).

### 2.2 Key prefixes

A wrong-type id returns a misleading "The requested resource does not exist".

| Prefix | Object | Prefix | Object |
|---|---|---|---|
| `11O` | ContextDefinition | `11b` | ContextNodeMapping |
| `11o` | ContextNode | `11R` | ContextAttributeMapping |
| `11n` | ContextAttribute | `11P` | ContextAttrHydrationDetail |
| `11j` | ContextMapping | `11k` | ContextTag |

`11O` / `11o` / `11n` differ only by case. Attribute PATCH/DELETE is node-scoped: `connect/context-nodes/{11o…}/context-attributes/{11n…}`.

### 2.3 Attribute fields (Setup "Structure" tab)

| Column | API field | Notes |
|---|---|---|
| Name / Display Name | `name` / `displayName` | `displayName` is null on nearly all standard attributes. |
| Type | `fieldType` | Read/write direction (2.5). |
| Data Type | `dataType` | See 2.7. |
| Key / Value | `isKey` / `isValue` | Only on key-value "bag" nodes (`SalesTransactionItemAttribute`, `FulfillmentLineAttribute`, `ASPAttribute`). **Not** a primary key. |
| Transient | `isTransient` | Computed in cache, skipped on persist, not packaged. SObject REST only. |

Also: `isCustomMappingAllowed`, `isLocalizationDisabled` (opts out of the 262 locale-translation feature, unrelated to the `TRANSLATION` intent).

### 2.4 Tags: the expression-set contract

1. A tag `{contextTagId, name, contextAttributeId, dynamic}` hangs off an attribute. Expression sets and pricing procedures read and write **by tag name**, never by node path or field: renaming or dropping a tag breaks consumers. An **untagged** attribute is invisible to them and to DocGen.
2. **Tag names are unique per definition**, even across attributes (`DUPLICATE_VALUE` "Tag name already exists for this definition"), which is why a bare tag name is unambiguous.
3. **One attribute can carry several tags**, parallel aliases with no precedence (pricing takes the first match by name). Typical use: a `__c` alias next to an inherited tag.
4. Tag names differ from attribute names (attribute `Quantity` → tag `LineItemQuantity`; `Pricebook` → `PriceBooks`): read them off the definition.
5. A tag equal to a decision table's label or API name is rejected or collides.
6. `dynamic: true` marks a data-derived attribute populated via a context dictionary tied to an entity object.

### 2.5 Mappings, intents, fieldType

Rule types: **SOBJECT** (attribute ↔ `sObject.sObjectField`); **relationship traversal** (SOBJECT rule with `childSObject` / `childSObjectField`, hydration detail chained via `parentDetailId` / `childDetails`; **SObject REST only**); **CONTEXT** (`sourceContextNode` / `sourceContextAttribute`, `MappedContextDefinition` on the node mapping; **SObject REST only**). Create SOBJECT mappings **before** CONTEXT ones so referenced ids exist.

Intents (Connect `contextMappings[].intents`; Metadata API `contextMappingIntents[].mappingIntent`; since v61) gate data movement:

| Intent | Direction | Meaning |
|---|---|---|
| `HYDRATION` | record → cache | SOQL on mapped fields (FLS honored). |
| `PERSISTENCE` | cache → record | Write-back via Composite Graph API (`ALL_OR_NONE`). Without it the context is read-only. |
| `ASSOCIATION` | link | Links records/definitions without a DB relationship check and without hydrating. Only intent allowing many-node → one-SObject and cross-node shapes. |
| `TRANSLATION` | transform | Re-expresses a hydrated context through another mapping (`translate(contextId, mappingId)`); SObject mappings only. |

`PERSISTENCE` and `TRANSLATION` are one-to-one only. Intents can coexist on a mapping.

| `fieldType` | Hydration | Persistence |
|---|---|---|
| `INPUT` | read | never |
| `INPUTOUTPUT` | read | written |
| `OUTPUT` | — | written (computed) |
| `AGGREGATE` | — | computed / rollup |

`isTransient: true` is never persisted.

### 2.6 Referenced definitions

A definition can reference other definitions (Setup "Referenced Definitions"; GET `referenceContextDefinitions[]`), realized by `ASSOCIATION` mappings and usually inherited. `canBeReferenceDefinition` (Setup "Reference Definition") only says whether *this* definition may be referenced; it is `false` on Sales Transaction.

### 2.7 Enums and limits

1. `dataType`: `STRING`, `NUMBER`, `BOOLEAN`, `DATE`, `DATETIME`, `PERCENT`, `PICKLIST`, `CURRENCY`, `REFERENCE`, `DOUBLE`, `INT`, `MAP`, `SELFREFERENCE`, `LOOKUP`. `fieldType`: `INPUT`, `INPUTOUTPUT`, `OUTPUT`, `AGGREGATE`. `mappingType`: `SOBJECT`, `CONTEXT`.
2. The Metadata API file format differs slightly (`INTEGER` instead of `INT`, lower-case intents).
3. Limits (Salesforce Help): ≤ 50 nodes per definition, ≤ 1,000 attributes in total, depth ≤ 5, ≤ 1 hydration detail per attribute mapping. No per-node tag cap observed (20 tags on one node works).

---

## 3. Definition types and versioning

| Type | Marker | Sync upgrade | Editable |
|---|---|---|---|
| Standard | `__stdctx` | n/a (the base) | No: extend it |
| Extended | `inheritedFrom` set | Yes, keeps the base's mandatory mappings | Additively |
| Custom / cloned | from scratch, or `clonedFrom` set | No: frozen, reconcile by hand | Yes |

**Extend, don't clone** (documented best practice). Create a custom definition only when no base fits (e.g. a dedicated Quote → Line DocGen context).

1. Exactly **one** `ContextDefinitionVersion` per definition: a second insert fails with `MAX_LIMIT_EXCEEDED` "Version already exists for this Context Definition", despite the one-to-many Metadata API shape.
2. `IsActive` is on the version (`SELECT Id, ContextDefinition.DeveloperName, IsActive FROM ContextDefinitionVersion`). No `IsLatest` or `Status` field.
3. Additive edits and deactivate/reactivate cycles bump `VersionNumber` **in place**; the Id is stable.
4. `__stdctx` definitions expose no queryable version rows.
5. No "save as new version" verb: only Upgrade/Sync crosses versions (section 7).

---

## 4. Extending a standard definition

### 4.1 Pick the building block

| Need | Add |
|---|---|
| New value on a modeled entity (common case) | Attribute + tag + one mapping rule **per lens**: bind in `QuoteEntitiesMapping` → `QuoteLineItem.X__c` **and** `OrderEntitiesMapping` → `OrderItem.X__c`. Sales Transaction rarely needs a new node. |
| New entity / level | Node (parent-first, depth ≤ 5), then attributes, tags, node mapping, attribute mappings. |
| Expose an attribute to an engine | Tag. |

Partial combinations are why a change "does nothing":

| Declared | Result |
|---|---|
| Attribute only | Inert |
| Attribute + mapping, no tag | Hydrated, unreachable by expression sets |
| Attribute + tag, no mapping | Never populated (runtime input only) |
| Attribute + tag + mapping in each lens | Working: field surfaced to pricing / DocGen |
| Node + attributes + tags + node and attribute mappings | Working: new child entity |

### 4.2 Procedure: extend a standard base

1. Confirm the base is provisioned (section 1).
2. Extend it via `POST connect/context-definitions` (create, clone and extend). `name` alphanumeric only (label in DisplayName); `startDate` as xsd:dateTime (`"2020-01-01T00:00:00.000Z"`); never send `primaryDomainObject` / `primaryObject` (`JSON_PARSER_ERROR`).
3. While inactive, set the default mapping: `PATCH connect/context-definitions/{id}/context-mappings` with `{"contextMappings":[{"contextMappingId":"11j…","isDefault":"true","name":"…"}]}`.
4. Activate (`isActive: "true"`); without a default mapping: `DATA_MAPPING_NOT_FOUND`.
5. Leave inherited mappings (e.g. `TransactionType`) alone.
6. A failed create has **no full rollback**: clean up the orphan before retrying.

### 4.3 Procedure: surface a custom field to pricing / DocGen

1. Deploy the field on **every** bound SObject **first** and grant read FLS (permission set carrying the context's fields). Binding a missing field "succeeds" and stores nothing.
2. Add the attribute under the existing node (Connect POST, allowed on active). On an extended base, custom names **must** end in `__c` (`INVALID_API_INPUT`). Use `fieldType` `INPUTOUTPUT` if it must persist.
3. To exclude it from write-back, PATCH `IsTransient` on `ContextAttribute` via SObject REST (blocked on active: deactivate first).
4. Add a `__c` tag (Connect POST `context-tags`, allowed on active).
5. Bind it in **each** relevant mapping without touching siblings: SObject REST POST of a `ContextAttributeMapping` + `ContextAttrHydrationDetail` pair (allowed on active; the only clean way for a **root-node** attribute), or the granular `context-attribute-mappings` sub-resource one row at a time. Never PATCH `context-node-mappings` with a partial child list (section 5).
6. Clear the runtime schema cache: `DELETE connect/context-runtime-schema/clear?contextDefinitionName=…[&contextMappingNames=…]`.
7. Verify `queryAttribute` in the GET, then hydrate a real record and read the tag (section 8).
8. Reference the **tag name** in the expression set.

### 4.4 Procedure: model a new child entity

1. Create nodes parent-first, then attributes, tags, the node mapping and attribute mappings.
2. A child node creates a `ParentReference`: for hierarchical DocGen, map it **explicitly** to the child's lookup to its parent (e.g. `QuoteLineItem.QuoteId`).
3. For a Context Service document generation process, pass the root record id as plain `DocGenAdditionalInput`, never the runtime API's `inputData` JSON.

Custom (create-new) definitions need `developerName`, label and a default mapping; the `__c` rule applies only on extended bases; Sync never upgrades them.

---

## 5. Activation lifecycle

| Operation | Endpoint | On an active version |
|---|---|---|
| Insert node / attribute / tag / mapping shell | Connect POST | Allowed |
| Traversal hydration pair | SObject REST POST | Allowed |
| `MappedContextDefinition` | SObject REST PATCH `ContextNodeMapping` | Allowed |
| Delete one attribute mapping | SObject REST DELETE `ContextAttributeMapping/{id}` | Allowed |
| `IsTransient` | SObject REST PATCH `ContextAttribute` | Blocked: `RECORD_UPDATE_FAILED` |
| `isDefault` / mapping metadata | Connect PATCH `context-definitions/{id}/context-mappings` | Blocked |
| Delete an existing artifact | Connect DELETE | Blocked |
| Node mappings, partial children | Connect PATCH `context-mappings/{id}/context-node-mappings` | **Silently destructive**: `isSuccess:true`, wipes sibling `ContextAttributeMapping` rows not re-sent, active or not |

A Connect PATCH carrying hydration also defaults `isDeleteExistingHydrationDetail` to **true**: re-runs wipe hydration unless re-sent.

1. Additive edits need no deactivation; `IsTransient`, default mapping and deletions need deactivate → edit → reactivate.
2. **Deactivation is blocked** (`RECORD_UPDATE_FAILED`, blocker unnamed) while an **active** expression set, ContextRules, PricingActionParameters or decision table references the definition. Deactivating a definition used by a pricing procedure **breaks** it.
3. Expression-set consumers (data API; Tooling rejects it): `SELECT Id, ExpressionSetDefinitionId, ContextDefinitionId, ExecutableContextDefinition FROM ExpressionSetDefinitionContextDefinition WHERE ContextDefinitionId = '11O…'`. Other consumer types have no enumerating query.
4. Order: unlink / deactivate consumers, deactivate the definition, edit, reactivate, re-link.
5. Shortcut, **sandbox or scratch only** (it deletes records; Reej rule: never in production): back up the junction rows, delete them, edit, recreate each with `ExpressionSetDefinitionId` + `ContextDefinitionId`, then compare the sorted `ExpressionSetDefinitionId` sets (new rows get new Ids).
6. Don't test reversible edits on a definition wired to many expression sets: the undo strands behind the consumer block.

---

## 6. Deployment: Metadata API vs Connect API

| Channel | Covers | Limits |
|---|---|---|
| Metadata API: `ContextDefinition` (`contextDefinitions/` folder) | The whole definition as source | One **atomic** unit (`childXmlNames: []`). **Cannot** activate/deactivate or set the default mapping (not packageable): do it via API or Setup after deploy. |
| Connect API | List, read, create / clone / extend, PATCH / DELETE by id, granular sub-resources (`connect/context-definitions/<id>/<subresource>[/<subId>]`), filters, default mapping, activation, Upgrade | Rejects traversal, ignores `mappedContextDefinitionName`, ignores `IsTransient`; whole-body replace on node mappings; hydration wiped on re-PATCH. |
| SObject REST: `ContextAttribute`, `ContextNodeMapping`, `ContextAttributeMapping`, `ContextAttrHydrationDetail` | Traversal, `MappedContextDefinition`, `IsTransient`, sibling-safe bindings, leaf deletes | Active-version blocks still apply. |

Order on any org: custom fields + FLS, then definition changes, then default mapping and activation.

---

## 7. Upgrades between releases

1. `PATCH connect/context-definitions/upgrades`, one definition at a time, `upgradeMode`: `Preview` (delta only), `Sync` (merge platform changes, keep custom artifacts: **use this**), `Override` (**destructive**: deletes custom artifacts, resets to the base).
2. Only **extended** definitions follow the base; clones and custom definitions are reconciled by hand.
3. Sandbox first: Preview, Sync, confirm consumers (expression sets, pricing and DocGen procedures) still resolve, then promote through the client's release process.
4. Release 262: the Billing context needs a **duplicate-mapping cleanup** before Sync succeeds.

---

## 8. Runtime: hydrate, query, persist

Engines hydrate their own contexts in-process. Drive the runtime yourself to validate a definition, or from custom Apex / Flow.

### 8.1 Pick the path

| Org | Working path |
|---|---|
| Normal GA org | **Apex `Context.IndustriesContext`** or **one Flow**: whole lifecycle in one request. GA `IndustriesContext` permission only. |
| `ContextServicePilot` (user permission `SessionScopeContext`) and/or RLM Setup "Runtime Context Instance Reuse to Improve Response Times" (`ContextReuse`) | Multi-call REST also works. |

Why multi-call REST fails on GA:

1. `contextId` is an opaque **request-scoped** handle (UUID/hex: never prefix-validate). Default `metadata.contextScope` is `REQUEST` (~15 s TTL): a separate later call gets `RECORD_NOT_FOUND` (`GET connect/contexts/{id}`: 200 with `isSuccess:false`).
2. `contextScope: "SESSION"` is pilot-gated (`API_DISABLED_FOR_ORG`). REQUEST is the recommended customer scope.
3. `query-record` and `query-tags[-leaner]` are pilot-gated on scratch and production orgs alike. Create, attribute/tag PATCHes and `persist-records` are GA.

`contextTtl` is a **definition** property in minutes (default 10; org max 45 from R254 via `ContextMaxTtlInMinutes`), relevant to SESSION scope only. Never put a TTL in the runtime create body.

### 8.2 Apex: full lifecycle in one transaction

```apex
Context.IndustriesContext ctx = new Context.IndustriesContext();
Map<String,String> md = new Map<String,String>{
    'contextDefinitionId' => '<11O…>', 'mappingId' => '<11j… HYDRATION mapping>'};
// businessObjectType = MAPPED SObject ("Quote"), not the node name
Map<String,Object> bi = new Map<String,Object>{'metadata' => md,
    'data' => '{"SalesTransaction":[{"id":"<quoteId>","businessObjectType":"Quote"}]}'};
String cid = (String) ctx.buildContext(bi).get('contextId');   // lazy: 0 SOQL

Map<String,Object> q = ctx.leanerQueryTags(new Map<String,Object>{
    'contextId' => cid, 'tags' => new List<String>{'SalesTransactionName','LineItemQuantity'}});
System.debug(q.get('recordIds'));                               // [] = nothing hydrated

// dataPath = RECORD IDS ([rootId] or [parentId, childId]), not node names
Map<String,Object> np = new Map<String,Object>{
    'dataPath' => new List<String>{'<quoteId>', '<quoteLineId>'}};
List<Map<String,Object>> npa = new List<Map<String,Object>>{ new Map<String,Object>{
    'nodePath' => np,
    'attributes' => new List<Map<String,Object>>{
        new Map<String,Object>{'attributeName' => 'Quantity', 'attributeValue' => '5'}}}};
ctx.updateContextAttributes(new Map<String,Object>{
    'contextId' => cid, 'nodePathAndAttributes' => npa});
Object refId = ctx.persistContext(new Map<String,Object>{
    'contextId' => cid, 'contextMappingId' => '<11j… PERSISTENCE mapping>'});  // async (8.6)
```

1. `buildContext` hydrates lazily, server-side, outside the Apex SOQL governor count.
2. `leanerQueryTags` returns `{leanerQueryTagResult:{<tag>:[{isNodeLevelTag, recordIdIndexesForPath, tagValue}]}, recordIds[], recordsInfo[], isSuccess}` (`[0]` = root, `[0,n]` = nth child); `queryTags` returns `{queryResult:{tag:[…]}, isSuccess, isDone}`.
3. Unknown tag name: `ContextModificationException: Invalid tag attribute name key`.
4. `getContext` returns metadata only. `queryContextRecordsAndChildren` and `metadata.eagerHydration = 'true'` throw an uncatchable `System.UnexpectedException`.
5. Use key `nodePathAndAttributes` (native `List<Map>`); stringified `nodePathAndUpdatedValues` always throws in Apex. A node-name or empty `dataPath` silently no-ops.

### 8.3 Flow: invocable actions

Standard actions: `buildContext`, `updateContextAttributes`, `persistContextData`, `queryContextTags`, `deleteContextCache`, `addContextRecords`, `deleteContextRecords`, `getAgentContext`.

| Action | Required | Optional | Outputs |
|---|---|---|---|
| `buildContext` | `contextDefinitionId` | `contextMappingId`, `contextData` (stringified JSON), `isTaggedData` | `contextId`, `contextDefinitionId`, `contextMappingId` |
| `updateContextAttributes` | `contextId`, `nodePathAndUpdatedValues` (stringified JSON) | — | — |
| `persistContextData` | `contextId` | `contextMappingId`, `trackingId` | `referenceId` |
| `queryContextTags` | `contextId`, `tagsList` (real `String[]`) | — | `queryResult` (stringified JSON) |

Chain them inside **one Flow** (a reusable subflow); as separate REST invocations they hit `RECORD_NOT_FOUND`. A stringified `tagsList` fails with `INVALID_ARGUMENT_TYPE "expected String[]"`.

### 8.4 REST runtime endpoints

| Step | Endpoint | Notes |
|---|---|---|
| Create | `POST connect/contexts` | `{"metadata":{contextDefinitionId, mappingId[, contextScope]}, "data":"<stringified JSON>"}` |
| Update | `PATCH connect/contexts/attributes` | Flat `{contextId, nodePathAndAttributes}` |
| Write by tag | `PATCH connect/contexts/write-through-tags` | Flat `{contextId, nodePathAndTagValues}` |
| Read tree | `POST connect/contexts/query-record` | Pilot. `queryRecords[]` / `childQueryRecords`; compound values (e.g. Address) come as stringified JSON |
| Read by tag | `POST connect/contexts/query-tags[-leaner]` | Pilot. `{contextId, tags[]}`; leaner since API 66.0 |
| Persist | `POST connect/contexts/persist-records` | Flat `{contextId, targetMappingId}`; the documented `contextPersistInput` wrapper is rejected |
| Evict | `DELETE connect/contexts/{contextId}` | |
| Clear schema cache | `DELETE connect/context-runtime-schema/clear?contextDefinitionName=…` | Re-read mappings after a change |
| Interfaces | `GET connect/context-definition-interfaces[/…]` | Contracts engines use to find a compatible definition; not gated |

### 8.5 The `data` hydration payload

`data` is a JSON **string**: an object keyed by **node name**, records with `id`, `businessObjectType`, optional values, children as nested arrays named by child node:

```json
{"SalesTransaction":[{"id":"<quoteId>","businessObjectType":"Quote",
  "SalesTransactionItem":[{"id":"<lineId>","businessObjectType":"QuoteLineItem","Quantity":3}]}]}
```

1. **`businessObjectType` = the node's mapped SObject** under the chosen mapping (`contextNodeMappings`: `contextNodeName` → `sObjectName`). A node name hydrates **zero** records with `isSuccess:true`.
2. **Id-only is normal**: the root `id` alone makes the engine query mapped fields and **cascade to child nodes**. Inline values override org values (what-if tests).
3. **Hydration is sparse**: transient attributes never hydrate, only mappings with a `queryAttribute` read a field, and nodes without records stay empty.
4. **Querying a tag of a node with 0 records throws** an uncatchable `System.UnexpectedException`: check `recordIds` / `recordsInfo[].recordId` first.

### 8.6 Persistence

1. The target mapping needs `PERSISTENCE`; only non-transient `INPUTOUTPUT` / `OUTPUT` attributes are written.
2. **Asynchronous**: no synchronous DML. The `referenceId` (`16P…`) **is** the `AsyncOperationTracker.Id` (and the `RequestIdentifier` of the non-queryable `ContextPersistenceEvent` platform event, which only carries `HasErrors`).
3. Poll: `SELECT Id, Status, Response FROM AsyncOperationTracker WHERE Id = '<referenceId>'`. `Status`: `Submitted`, `InProgress` (keep polling), `Completed`, `CompletedWithFailures`, `Failure`. `Response` holds `savedNodes`, `skippedNodes`, `errorNodes` (`recordId` → DML error).
4. **Failure = `CompletedWithFailures` / `Failure` OR non-empty `errorNodes`**: `Completed` alone is not success.
5. Clean records are **skipped**: only records edited after hydration, new records with a synthetic id, or deleted ones persist. Values passed at create time do not make a record dirty.
6. A dirty record triggers an atomic UPDATE over the **node's full mapped fieldset**. FLS-hidden fields are dropped; `updateable=false` fields are not. The standard `QuoteEntitiesMapping` line node carries many (`TotalPrice`, `Subtotal`, `NetUnitPrice`, `ListPrice`, `Product2Id`, `PricebookEntryId`, …), so a dirty persist through it fails: "Unable to create/update fields: … Please check the security settings". No permission fixes it; use a custom PERSISTENCE mapping limited to updateable fields. Same via Apex, Flow, REST and write-through-tags.
7. Lookup / foreign-key changes are not reliably saved: persist scalars, re-query the target record.

---

## 9. Debugging checklist and errors

1. Base provisioned on this edition?
2. Id prefix matches the endpoint; REST path versioned?
3. Version active, default mapping set?
4. Mapped field exists (`FieldDefinition`); running user has FLS?
5. Attribute tagged **and** bound in the mapping the engine uses?
6. Runtime schema cache cleared after the change?
7. Apex hydration test returns non-empty `recordIds`?
8. Expression set uses the **tag** name?
9. Persist judged from `AsyncOperationTracker.Response`?

| Symptom / error | Cause | Fix |
|---|---|---|
| `JSON_PARSER_ERROR` on create | `primaryDomainObject` / `primaryObject`, bare-date `startDate`, unexpected key | Remove key; xsd:dateTime |
| `DATA_MAPPING_NOT_FOUND` | No default mapping | Set `isDefault` while inactive |
| `RECORD_UPDATE_FAILED` "Cannot modify/delete an active context definition" | Endpoint blocked on active | Deactivate, edit, reactivate |
| `RECORD_UPDATE_FAILED` on deactivate | Active consumer | Unlink consumers first (section 5) |
| `INVALID_API_INPUT` "…must have an '__c' suffix…" | Custom artifact on extended base | Add `__c` |
| `DUPLICATE_VALUE` "Tag name already exists…" | Name reused in definition | Distinct name |
| `MAX_LIMIT_EXCEEDED` "Version already exists…" | Second version | One version only |
| "The requested resource does not exist" | Wrong id type, or bare `connect/context-attributes/{id}` | Check prefix; node-scoped path |
| Binding `success:true`, then `hasHydrationDetail:false` | Field missing on org | Deploy field, rebind |
| GET / Setup shows no field bound, rows exist | Running user lacks FLS (GET filters by FLS) | Grant read FLS; no activation cycle needed |
| Sibling attribute mappings vanished | Partial node-mappings PATCH | Re-send full list; granular / SObject REST |
| `recordIds: []`, `isSuccess:true` | `businessObjectType` = node name | Mapped SObject name |
| `RECORD_NOT_FOUND` on later REST call | REQUEST scope expired | One Apex transaction / Flow |
| `API_DISABLED_FOR_ORG` | Pilot-gated query or SESSION scope | Apex / Flow |
| `ContextModificationException: Invalid tag attribute name key` | Attribute name used as tag | Tag name |
| `System.UnexpectedException` (uncatchable) | Unhydrated-node tag query, `eagerHydration`, `queryContextRecordsAndChildren`, `nodePathAndUpdatedValues` in Apex | See 8.2, 8.5 |
| Update `isSuccess:true`, value unchanged | `dataPath` not record ids | Record ids |
| Persist `Completed`, nothing written | Skipped clean records or `errorNodes` | Read `Response`; edit after hydration |
| "Unable to create/update fields … security settings" | Non-updateable fields in node fieldset | Updateable-only PERSISTENCE mapping |
