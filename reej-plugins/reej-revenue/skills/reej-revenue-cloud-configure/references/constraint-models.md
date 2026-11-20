# Revenue Cloud — Constraint models (CML)

> Adapted from [SalesforceLabs/revenue-cloud-foundations](https://github.com/SalesforceLabs/revenue-cloud-foundations) (Apache-2.0), `.cursor/skills/constraint-models`, commit `c850652` — Release 264 / API v68.0. Modified by Reej Consulting: repo-specific tooling removed, content condensed.

**Contents**

1. [Role in the configurator](#1-role-in-the-configurator)
2. [Objects involved](#2-objects-involved)
3. [CML essentials shown by the source](#3-cml-essentials-shown-by-the-source)
4. [Binding a model to products and bundles](#4-binding-a-model-to-products-and-bundles)
5. [Lifecycle: store, cycle, activate](#5-lifecycle-store-cycle-activate)
6. [Proving a change is live](#6-proving-a-change-is-live)
7. [Checklist: configurator behavior did not change after deployment](#7-checklist-configurator-behavior-did-not-change-after-deployment)
8. [Not covered by the source](#8-not-covered-by-the-source)

---

## 1. Role in the configurator

A constraint model holds the Constraint Modeling Language (CML) rules that decide **what the Product Configurator lets a user select inside a bundle**.

- A constraint model **is an Expression Set** with `UsageType = 'Constraint'`. That field, not the name, identifies a constraint model.
- An org can run several models at once. Among **alternative models of the same bundle** (a "family"), keep **exactly one active**; unrelated models stay active alongside it. Read "active" per family, not per org.
- Do not count on activating one model to deactivate another: discover what is active and deactivate the model you replace explicitly.

Discover from the org, never from a document (the set differs per org and grows over time):

```sql
SELECT ExpressionSet.ApiName, ApiName, VersionNumber, IsActive
FROM ExpressionSetVersion
WHERE ExpressionSet.UsageType = 'Constraint'
ORDER BY ExpressionSet.ApiName
```

---

## 2. Objects involved

| Object | Prefix | Role |
|---|---|---|
| `ExpressionSet` | `9QL` | The **Constraint Model** record (`UsageType = Constraint`). Record page `/lightning/r/ExpressionSet/<9QL…>/view` |
| `ExpressionSetVersion` | | **Constraint Model Versions** related list. `ApiName`, `VersionNumber`, **`IsActive`** (the field Constraint Builder toggles) |
| `ExpressionSetDefinitionVersion` | | Holds **`ConstraintModel`**, the stored CML source. Query through the Tooling API by `DeveloperName` (the source names both the version and the definition version `<Model>_V1`) |
| `ExpressionSetDefinitionContextDefinition` | | Exported with each model alongside the records above |
| `ExpressionSetConstraintObj` (ESC) | | Associations binding model elements to records: `ExpressionSetId`, `ConstraintModelTag`, `ConstraintModelTagType` (`Type` or `Port`), reference to the target record (`ReferenceObjectId`) |
| `Product2` | `01t` | Target of `Type` associations |
| `ProductRelatedComponent` (PRC) | `0dS` | Bundle component row; target of `Port` associations |
| `ProductClassification` | | Used to match a PRC across orgs (§4.3) |

**The CML is plain text.** Model files exported as `.ffxblob` are ASCII CML source, not binary (`file` reports "c program text"). The stored model is whatever was uploaded into `ConstraintModel`; a reference copy elsewhere in a repo changes nothing in any org.

**Read the stored model back:**

1. Tooling query: `SELECT ConstraintModel FROM ExpressionSetDefinitionVersion WHERE DeveloperName = '<Version>'`.
2. The field returns a **relative URL**, not the text.
3. `GET <instanceUrl><that URL>` with header `Authorization: Bearer <access token>` returns the CML source; search it for your change.

This proves the model was **stored**, not that the runtime uses it (§6).

**Moving a model between orgs.** Record Ids in exported files belong to the authoring org. Remap `Type` associations to the target org's `Product2` (the source matches by `Name`) and `Port` associations to the target org's PRC (§4.3).

---

## 3. CML essentials shown by the source

The source documents only the elements below. It mentions editing **attributes and rules** but gives **no syntax** for them, nor for constraints: use the official Salesforce CML reference for those.

| Element | Syntax shown | Meaning |
|---|---|---|
| `type` | `type SupportPlan : LineItem;` | Declares a model type; the source's bundle-member example is declared `: LineItem` |
| `relation` | `relation supportplan : SupportPlan;` | Declares a relation to a type; a **bundle relation** is what gets a `Port` |
| Annotation | `@(virtual = "true")` on a `Quote` container type | A virtual-quote container; its `lineitems` relation is **cart-level**, not a bundle component |

(Names are neutral placeholders; the source's own example pairs a lowercase relation name with its PascalCase type.)

Adding a bundle member in CML = **one `relation` and one `type`**, placed next to their existing siblings. The model alone is not enough: see §4.

---

## 4. Binding a model to products and bundles

### 4.1 The four records a bundle member needs

| # | Record | Where | Symptom if missing |
|---|---|---|---|
| 1 | `ProductRelatedComponent` row | Product catalog | Product never appears in the bundle |
| 2 | `type` + `relation` | The CML | Model has no concept of the product |
| 3 | ESC association, `ConstraintModelTagType = Type` → `Product2` | `ExpressionSetConstraintObj` | **Product appears, then fails Product Validation** |
| 4 | ESC association, `ConstraintModelTagType = Port` → PRC | `ExpressionSetConstraintObj` | Relation not bound to the bundle component |

**#3 is the trap.** With the PRC row present and the `Type` association missing, the configurator offers the product (the bundle says it is a component), then rejects it (the model has no type for it). The error looks like a product problem; nothing points at the constraint model.

### 4.2 Ports are per bundle relation, not per type

- Only types reachable as **bundle members** get a `Port`. The `Port` count tracks bundle `relation`s, not `type`s.
- A **cart-level** relation (such as `lineitems` on a virtual `Quote`) has no `Port`.
- A **virtual-quote model**, whose types are cart line items rather than bundle components, has **zero** `Port`s and is correct that way.
- For cart-level or virtual-quote types, records #1 and #4 do not apply; #2 and #3 still do.

### 4.3 Matching a PRC: `Sequence` counts

To find a PRC across orgs, the source matches on **parent product + child product + child product classification + product relationship type + `Sequence`** (by names). A `Port` association must point at the PRC that exists **in the target org**:

1. Do not invent a `Sequence` for a new PRC row: reuse the one the product's existing PRC row carries.
2. When a `Port` fails to resolve, **query the target org's PRC records**; do not compare files. An org loaded from another data revision disagrees with the files on disk.

---

## 5. Lifecycle: store, cycle, activate

**Storing a new CML into an Active version does not redeploy the model.** The org keeps running the old model and the upload reports success. The version must be **deactivated and reactivated after the upload**. Salesforce documents the same for table data:

> "If the table data is deployed when the constraint model is activated, and you add records to the table after constraint model activation, to fetch the new table data at runtime you must deactivate and reactivate the constraint model."
> — Help, *Import Object Data* (262)

### 5.1 Procedure to ship a model change

1. **Discover** the model and the version actually active (§1 query).
2. **Edit the CML** that will be uploaded (not a reference copy).
3. **Check bindings** for each new bundle member: PRC row in the target org, `type` + `relation`, ESC `Type` and `Port` (§4).
4. **Deactivate** the target version: `ExpressionSetVersion.IsActive = false`.
5. **Store** the new CML in `ExpressionSetDefinitionVersion.ConstraintModel` and write the ESC rows.
6. **Reactivate**: `IsActive = true`.
7. **Prove** it with the configurator (§6).

Order rule: the **reactivation must come after the upload**. Deactivate → upload → activate and upload → deactivate → activate both work; an upload into a version left Active without a later cycle changes nothing.

### 5.2 Activation rules

1. Activation = PATCH `IsActive` on `ExpressionSetVersion` (by `ApiName`), the same record and field the UI toggles.
2. **Activating an already-active version is a no-op.** A pipeline that "activates" a list of versions must deactivate each of them first, or it reports success while the old model keeps running. Every version it activates must also be in its deactivate list.
3. Cycle **the version you uploaded into**. Cycling an unrelated model proves nothing and briefly deactivates a model something else may depend on.
4. Activation itself only flips `IsActive`; per the source, the model is compiled when configuration rules run, which is why only running them proves deployment (§6).

### 5.3 UI equivalent

1. Open the Constraint Model record (`ExpressionSet` record page).
2. **Constraint Model Versions** related list (`ExpressionSetVersion`) → open the version: this launches **Constraint Builder**.
3. Toolbar: **Sync**, **Deactivate**, **Save**.

The effect of **Sync** was not investigated by the source: do not assume it is a no-op, nor a substitute for the deactivate/reactivate cycle.

---

## 6. Proving a change is live

| Check | Proves | Does not prove |
|---|---|---|
| Upload succeeded | The call completed | That anything changed at runtime |
| `ConstraintModel` reads back with the change | The CML was **stored** | That the runtime **rebuilt** (same field the upload writes) |
| ESC query scoped to the model | Associations exist | Runtime behavior |
| Configurator exercised | **Deployment** | — |

There is **no passive status field** distinguishing "stored" from "deployed": make the engine run.

1. **Interactive**: select the product in the configurator.
2. **Headless**: POST the Product Configurator `configure` action with `executeConfigurationRules: true` against a quote line that uses the model. A valid model returns `success: true`, `solverStatus: "success"`, `errors: []`; an invalid one returns `Model '…' is invalid`.
3. **Associations**: query the expected set, **scoped to the model you changed**:

   ```sql
   SELECT ConstraintModelTag, ConstraintModelTagType
   FROM ExpressionSetConstraintObj
   WHERE ExpressionSet.ApiName = '<Model>'
   ```

   Assert every expected bundle member has **both** a `Type` and a `Port` row. Models can share most tags, so an unscoped query lets another model's row mask a missing one.
4. **Resolved Ids**: query the referenced `Product2` / PRC Ids back and confirm they are the records you meant, not merely that something resolved.

---

## 7. Checklist: configurator behavior did not change after deployment

Work in order; stop at the first failing check.

| # | Check | How | Fix |
|---|---|---|---|
| 1 | Right model and version? | §1 query: which version of which model is active for this bundle | Work on that version |
| 2 | Change actually stored? | Read `ConstraintModel` back (§2), search for the change | Upload the edited CML, not a reference copy |
| 3 | Version cycled **after** the upload? | Was it Active during the upload with no deactivate/reactivate since? | Deactivate → reactivate that version |
| 4 | "Activation" was a no-op? | Version was already Active when the pipeline activated it | Deactivate first, then activate |
| 5 | Wrong model active in the family? | Another alternative model of the same bundle is active | Deactivate it; keep exactly one |
| 6 | Table data added after activation? | Records loaded after the model was activated | Deactivate → reactivate (Help, 262) |
| 7 | Product never appears in the bundle | PRC row missing in the target org | Create the PRC row |
| 8 | Product appears, then fails Product Validation | ESC `Type` association missing | Add the `Type` row (→ `Product2`) |
| 9 | Relation not bound to the bundle component | ESC `Port` missing, or pointing at a PRC whose `Sequence` differs in the target org | Add/fix the `Port`; match the org's PRC including `Sequence` |
| 10 | ESC set inconsistent | Scoped ESC query (§6) shows leftovers or gaps from an earlier, partly failed load | Correct the set to match the expected one, then re-query |
| 11 | Model valid? | `configure` with `executeConfigurationRules: true` | `Model '…' is invalid` → fix the CML, then repeat from step 2 |
| 12 | Still unchanged | Exercise the product in the configurator after the cycle | Re-check steps 1–4 on the **exact** version you uploaded into |

---

## 8. Not covered by the source

- CML syntax for **attributes, constraints and rules** (only `type`, `relation`, `LineItem` and the `@(virtual = "true")` annotation appear).
- The exact REST path of the Product Configurator `configure` action.
- The effect of Constraint Builder **Sync**.
- A Metadata API path for constraint models: the source documents none and handles models as records (`ExpressionSet*`, ESC) plus the stored CML.
- How to write `ConstraintModel` through the API (the source uses a repo tool for the upload).
