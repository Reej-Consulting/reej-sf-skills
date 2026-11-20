# Revenue Cloud — Decision tables

> Adapted from [SalesforceLabs/revenue-cloud-foundations](https://github.com/SalesforceLabs/revenue-cloud-foundations) (Apache-2.0), `.cursor/skills/decision-tables`, commit `c850652` — Release 264 / API v68.0. Modified by Reej Consulting: repo-specific tooling removed, content condensed.

**Contents**

1. [Role in RLM](#1-role-in-rlm)
2. [Two layers: definition and data](#2-two-layers-definition-and-data)
3. [Data model](#3-data-model)
4. [CSV-based tables](#4-csv-based-tables)
5. [Lifecycle: deploy, activate, edit](#5-lifecycle-deploy-activate-edit)
6. [Refresh](#6-refresh)
7. [Freshness and the timing rule](#7-freshness-and-the-timing-rule)
8. [Platform facts worth not re-discovering](#8-platform-facts-worth-not-re-discovering)
9. [Debugging checklist](#9-debugging-checklist)

---

## 1. Role in RLM

A decision table is a **materialized lookup** evaluated by the Business Rules Engine (BRE). A refresh **copies** source rows in; nothing re-reads the source afterwards: a cache with no invalidation. Pricing right in the data but wrong in the quote, a tier not applying, an ignored contracted price, a new SKU pricing as if absent: usually one bug, a stale table.

**Usages** (`usageType`): `DefaultPricing`, `DefaultRating`, `PricingDiscovery`, `RatingDiscovery`, `RevenueStandardTax`, `ProductCategoryQualification`, `ProductQualification`, `RecordAlert`, `Bre`, …

**Pricing consumption.** A recipe points to a table through a `PricingRecipeTableMapping` record (standard API, **not** Tooling): `PricingRecipeId`, `PricingComponentType` (`ListPrice`, `VolumeDiscount`, `VolumeTierDiscount`, `AttributeDiscount`, `BundleDiscount`, `PriceAdjustmentMatrix`, …), `LookupTableId`, `IsInternal`, `FileBasedDecisionTableName`. There is **no `DecisionTableId` field**: `LookupTableId` = `DecisionTable.Id` for sObject-backed tables; `FileBasedDecisionTableName` = `DeveloperName` for CSV-backed tables.

**Runtime.** INPUT columns are matched (`conditionType` / `conditionCriteria`), the hit policy (`filterResultBy`) picks the row(s), OUTPUT columns return to the calling expression set or pricing procedure. Direct invocation: Connect Decision Table Lookup / Invocation / Execution resources, or `ConnectApi` in Apex.

---

## 2. Two layers: definition and data

- **Definition**: columns (parameters), source binding, hit policy, row-filter criteria; no row values. Changed by Metadata deploy, Tooling API or Setup.
- **Data**: the rows the engine evaluates. Changed by refresh, and by CSV upload for CSV tables.

**Editing the definition does not synchronize rows**; a definition change is not live until a refresh completes. Where rows live, by `dataSourceType`:

| `dataSourceType` | Rows | How to sample |
|---|---|---|
| `SingleSobject` | Records of `sourceObject` | SOQL |
| `MultipleSobjects` | Dataset-link source objects, joined | One SOQL per dataset link |
| `CsvUpload` | Uploaded CSV held by the platform | Connect `…/{id}/data` (v62+) |
| `ContextDefinition` | Hydrated at runtime by a Context Definition | Nothing static |

---

## 3. Data model

### 3.1 The five Tooling setup objects

The definition is spread across five objects that are **Tooling API only** (`/tooling/query`, `/tooling/sobjects/<Object>`), not on the standard `/sobjects` surface.

| Object | Prefix | API | Role and key fields |
|---|---|---|---|
| `DecisionTable` | `0lD` | v51.0+ | Head: `DeveloperName`, `SetupName` (label), `Status`, `UsageType`, `DataSourceType`, `SourceObject`, `LastSyncDate`, `Metadata` |
| `DecisionTableParameter` | `0lP` | v51.0+ | Column: `DecisionTableId`, `FieldName`, `Usage`, `Operator`, `Sequence`, `DataType`, `FieldPath`, `IsRequired`, `DomainObject` |
| `DecisionTableDatasetLink` | `0lX` | v51.0+ | Source sObject for `MultipleSobjects`, **Standard tables only**: `SourceObject`, `IsDefault` |
| `DecisionTblDatasetParameter` | `0lZ` | v51.0+ | Maps a dataset field to a parameter: `DatasetFieldName`, `DatasetSourceObject` |
| `DecisionTableSourceCriteria` | `0VT` | v59.0+ | Source row filter: `SourceFieldName`, `Operator`, `Value`, `ValueType`, `SequenceNumber` |

Discover from the org (names and counts differ per org and release):

```bash
sf data query -t -q "SELECT DeveloperName, SetupName, DataSourceType, SourceObject, UsageType, Status, LastSyncDate FROM DecisionTable ORDER BY UsageType, SetupName" --target-org <alias>
sf data query -t -q "SELECT DecisionTableId, FieldPath, DomainObject FROM DecisionTableParameter" --target-org <alias>
sf data query -t -q "SELECT DecisionTableId, SourceFieldName, Operator, Value, ValueType FROM DecisionTableSourceCriteria" --target-org <alias>
```

Without `-t` (`--use-tooling-api`) the query fails: `sObject type 'DecisionTable' is not supported`.

Reading `DecisionTableParameter`:

1. **`DomainObject` can be the literal string `'null'`** for a column from the table's own object; `String.isBlank` does not catch it.
2. **`DomainObject` names only the object owning the final field of `FieldPath`.** For `AssetRateCardEntryId.RateCardEntryId.RateUnitOfMeasureName` it says `RateCardEntry`, never `AssetRateCardEntry`, yet re-pointing that intermediate lookup changes what a refresh materializes. Resolve every hop of `FieldPath`.

### 3.2 The `DecisionTable.Metadata` complexvalue

A Tooling GET of `DecisionTable/{id}` returns `Metadata`, inlining parameters, criteria (`decisionTableSourceCriterias[]`) and file-import versions with **Metadata API field names** (§3.3), plus `lastIncrementalSyncDate`, `refreshStatus`, `refreshFailureReason`, `uploadStatus`. POST/PATCH it to write the whole definition in one Tooling call.

### 3.3 Metadata API — `DecisionTable`

Folder `decisionTables/`, MDAPI suffix `.decisionTable`, source format `.decisionTable-meta.xml`. This is the source-controlled path (`sf project deploy start`). The file name is the `DeveloperName`; `setupName` is the human label.

Example: a `SingleSobject` table on `CostBookEntry`, INPUT `ProductId` (sequence 1) and `CurrencyIsoCode` (sequence 2, block omitted), OUTPUT `Cost`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DecisionTable xmlns="http://soap.sforce.com/2006/04/metadata">
    <collectOperator>None</collectOperator>
    <conditionCriteria>1 AND 2</conditionCriteria>   <!-- logic over INPUT sequences -->
    <conditionType>All</conditionType>
    <dataSourceType>SingleSobject</dataSourceType>
    <decisionTableParameters>
        <dataType>String</dataType>
        <fieldName>ProductId</fieldName>
        <fieldPath>ProductId</fieldPath>
        <isGroupByField>false</isGroupByField>
        <isRequired>true</isRequired>
        <operator>Equals</operator>                 <!-- INPUT only -->
        <sequence>1</sequence>                      <!-- INPUT only -->
        <usage>INPUT</usage>
    </decisionTableParameters>
    <decisionTableParameters>
        <dataType>String</dataType>
        <fieldName>Cost</fieldName>
        <fieldPath>Cost</fieldPath>
        <isGroupByField>false</isGroupByField>
        <isRequired>false</isRequired>
        <usage>OUTPUT</usage>                       <!-- no operator/sequence -->
    </decisionTableParameters>
    <doesConsiderNullValue>false</doesConsiderNullValue>
    <dtRowLevelOverrideType>None</dtRowLevelOverrideType>
    <executionType>HBASE</executionType>
    <filterResultBy>OutputOrder</filterResultBy>      <!-- hit policy -->
    <hasIncrementalSyncFailed>false</hasIncrementalSyncFailed>
    <isIncrementalSyncEnabled>false</isIncrementalSyncEnabled>
    <isVersioned>false</isVersioned>
    <setupName>Cost Book Entries</setupName>
    <sourceObject>CostBookEntry</sourceObject>
    <status>Active</status>                         <!-- deploy-time status -->
    <type>MediumVolume</type>
    <usageType>DefaultPricing</usageType>
</DecisionTable>
```

Authoring rules:

1. Column `usage`: **INPUT** = match condition (`operator` + `sequence`); **OUTPUT** = returned value; **ROWCRITERIA** = per-row filter (less common than `DecisionTableSourceCriteria`).
2. INPUT `sequence` values, not element order, drive `conditionCriteria`.
3. Spell `executionType` `HBASE`.
4. Connect definition resources use another vocabulary (`parameters`, `decisionResultPolicy`); write definitions through Metadata or Tooling.

### 3.4 Enum catalog

Captured on Release 262, not re-verified on 264. API v67 adds `isVersioned` and `decisionTableFileImportVersions[]`.

| Field | Values |
|---|---|
| `dataSourceType` | `ContextDefinition`, `CsvUpload`, `MultipleSobjects`, `SingleSobject` |
| `executionType` | `DLO` (v67.0+, replaces `DMO`), `HBASE`, `HBPO`, `SOLR`, `SOQL` |
| `conditionType` | `All`, `Any`, `Custom` |
| `filterResultBy` | `AnyValue`, `CollectOperator`, `FirstMatch`, `OutputOrder`, `Priority`, `RuleOrder`, `UniqueValues` |
| `type` | `Advanced`, `HighScaleExecution`, `HighVolume`, `LowVolume`, `MediumVolume`, `RealTime` |
| `status` | `ActivationInProgress`, `Active`, `Draft`, `Inactive` |
| parameter `usage` | `INPUT`, `OUTPUT`, `ROWCRITERIA` |
| parameter `dataType` | `Boolean`, `Currency`, `Date`, `DateTime`, `Number`, `Percent`, `String` |
| parameter `operator` | `Contains`, `DoesNotExistIn`, `DoesNotMatch`, `Equals`, `ExistsIn`, `GreaterOrEqual`, `GreaterThan`, `IsNotNull`, `IsNull`, `LessOrEqual`, `LessThan`, `Matches`, `NotEquals` |
| parameter `sortType` | `AscNullFirst`, `AscNullLast`, `DescNullFirst`, `DescNullLast`, `None` |
| criteria `valueType` | `Formula`, `Literal`, `Lookup`, `Parameter`, `Picklist` |
| `collectOperator` | `Count`, `Maximum`, `Minimum`, `None`, `Sum` |
| `dtRowLevelOverrideType` | `None`, `Both`, `Condition`, `Operator` |

---

## 4. CSV-based tables

A `CsvUpload` table has no backing sObject: `sourceObject` is the literal `"CSV"`, still **required** on create.

### 4.1 Upload (two phases, asynchronous, append-only)

1. Insert a `ContentVersion` with the CSV as base64 (`Title`, `PathOnClient`, `VersionData`). The first row must be the headers, matching the INPUT/OUTPUT `fieldName`s. Returns a `068…` id.
2. `POST connect/business-rules/decision-table/{0lD…}/file` with `{"fileId":"068…"}`. Response: *"We are uploading and processing the CSV file."*
3. Poll `uploadStatus`: `UploadInProgress` → `Completed` / `CompletedWithErrors` / `Failed`. Only `Completed` is a clean load.

Rules:

- Uploads **append** to the current file-import version (created with the table); no new version is created.
- **Bad rows drop silently**: only valid rows load, status `CompletedWithErrors`, no per-row error. Read rows back and compare counts.
- **Avoid `deleteAllRows:true`**: it can end `Failed` with existing rows intact (Release 262 / API v67.0, not re-tested on 264). To replace data, create a fresh table and upload.

### 4.2 Cell encoding per `dataType`

A cell that fails coercion drops its **row**.

| `dataType` | Accepted cell | Notes |
|---|---|---|
| String | any text, `"quoted, comma"`, UTF-8 | UTF-8 preserved |
| Number | `42`, `-3.5`, `0` | decimals, negatives OK |
| Currency | `1234.56` | stored verbatim, no rounding |
| Percent | `0.15`, `50` | **stored verbatim, no ×100 / ÷100** |
| Boolean | `true`, `false`, `TRUE` | **`1`/`0` rejected** |
| Date | `2020-01-02` | `YYYY-MM-DD` |
| DateTime | `2020-01-02T03:04:05.000Z` | **milliseconds and `Z` required** |

Generic BRE CSV tables accept all seven types, but **Salesforce Pricing** (per Help) limits CSV tables to DateTime/Text, Boolean and Number, and does not support Currency as an input rule variable.

### 4.3 Reading rows

`GET connect/business-rules/decision-table/{id}/data[?filter=Field:Value][&limit=N]` → `{"rows":[{"id":"1FI…","rowData":{…}}],"totalRows":N}`.

1. `filter` is an **exact, case-sensitive equality** (`Region:North` ≠ `Region:north`), no substring or prefix match.
2. An unknown field name returns **0 rows and no error**.
3. `filter` + `limit` throws `UNKNOWN_EXCEPTION` when `limit` is not strictly greater than the matched count. Use `filter` alone to narrow, `limit` alone to peek.
4. `totalRows` is the count **in the response**, not a grand total, and `offset` is unreliable: do not build an offset pager.

---

## 5. Lifecycle: deploy, activate, edit

```
deploy definition → activate → (deactivate → edit → reactivate) → refresh (async)
```

The definition is deployed and activated; the data becomes live only after a successful refresh.

### 5.1 Activation

- sObject-backed tables: state is `DecisionTable.Status` (`Active` ↔ `Inactive`/`Draft`; `ActivationInProgress` transient), changed in Setup or by a Tooling update of `Status`.
- A Tooling `Metadata` PATCH **requires `status`** (`FIELD_INTEGRITY_EXCEPTION: Required field is missing: status`): send the current status.

### 5.2 Active-edit restriction

An Active definition **cannot be modified in place** (`FIELD_NOT_UPDATABLE`, "Can't edit an active Decision Table"); deleting it can return `INVALID_OPERATION` + `DEPENDENCY_EXISTS`; a deploy over it fails. Procedure:

1. Deactivate the table.
2. Edit or redeploy the definition.
3. Reactivate.
4. Refresh.

Run each step separately so each platform error surfaces on its own.

### 5.3 CSV-based table lifecycle

1. **Create** the definition (`sourceObject` = `"CSV"`); version 1 is created.
2. **Upload** rows (§4.1).
3. **Activate**: PATCH the version's `versionStatus` via the table's Connect `/versions/{N}` sub-resource; table `Status` cascades to Active (async, past `ActivationInProgress`).
4. **Refresh** (§6), with `VersionNumber` if versioned.

Teardown: deactivate the **version** first (`{"versionStatus":"Inactive"}`), which cascades the table to Inactive, then delete. A table `Status` PATCH while a version is Active fails with `INVALID_INPUT`.

---

## 6. Refresh

The `refreshDecisionTable` **standard invocable action** syncs source rows into the BRE cache: how a data change or a redeployed definition goes live. Endpoint `POST /services/data/v68.0/actions/standard/refreshDecisionTable` (`GET` describes it). Inputs:

| Input | Type | Required |
|---|---|---|
| `DecisionTableApiName` | STRING | yes |
| `isDecisionTableIncremental` | BOOLEAN | no |
| `VersionNumber` | INTEGER | no, **but required for versioned CSV tables** (else `INVALID_API_INPUT`) |

Rules:

1. Input names match case-insensitively (verified v67.0), but a **wrong name is silently ignored**: `isIncremental` does nothing.
2. The action requires an **Active** table.
3. **Asynchronous**: the response is `outputValues.Status = "Queued"`, no tracker id. Poll the timestamps (`RefreshStatus=Completed`).
4. A full refresh advances `LastSyncDate`; an incremental one advances only `LastIncrementalSyncDate`.
5. Incremental needs `isIncrementalSyncEnabled = true`; otherwise the action returns `isSuccess=true` / `Queued` and **syncs nothing**. This is the common case: check the flag first.
6. **Limits**: full refreshes use separate hourly pools per org, **40 Standard and 60 Advanced**; CSV tables use Advanced. Do not loop refreshes.
7. Callable from **Flow and REST only**: Apex must start a flow (`Flow.Interview.createInterview(...).start()`).
8. One table by hand: Setup → Decision Tables.

**Refresh is required** after any catalog, pricing, rate or contract change to an object the table reads (source **or any `FieldPath` hop**), after a data load, a definition redeploy, or a deletion. Loading data after the refresh step leaves stale tables.

---

## 7. Freshness and the timing rule

### 7.1 Manual freshness check

1. Read the table's `LastSyncDate` (full sync).
2. List every object it reads: `SourceObject`, dataset links, **every hop** of each `FieldPath`, criteria fields.
3. Compare each object's newest `LastModifiedDate` with `LastSyncDate`. A change at or after the sync means stale; a **tie** proves no ordering: treat as stale.
4. Query the whole object, not only rows matching the criteria: a row edited **out of** the filter disappears from a filtered query while the table keeps its old copy.

Blind spots: a **deleted** row leaves no timestamp; rows hidden by sharing are invisible (run as a user with org-wide read; a zero count means "nothing *you* can see"); a parent edit does not touch the child's `LastModifiedDate`; `CsvUpload` and `ContextDefinition` tables have no record timestamps. A clean check is a readiness signal, not proof: refresh anyway after a known load or deletion.

### 7.2 The timing rule

**Fire a refresh when the table's source criteria become true, not when the triggering row is written.** If a table filters on `…ContractId.StatusCode = 'Activated'`, refreshing at contract creation excludes those rows and still advances `LastSyncDate`. Procedure before wiring automation:

1. Read the table's `DecisionTableSourceCriteria`.
2. Determine the state a source row must reach to satisfy them.
3. Trigger the refresh when a row **reaches** that state.
4. Handle faults: an unhandled fault in a record-triggered **after-save** flow rolls back the triggering DML, so a failed refresh must not take the record with it.

---

## 8. Platform facts worth not re-discovering

| Fact | Consequence |
|---|---|
| `DecisionTable` is a setup object | Apex DML is rejected **at compile time** (`DML operation Update not allowed on List<DecisionTable>`): the class will not deploy. Test fixtures need `JSON.deserialize`. |
| `MasterLabel` is the constant `"Decision Tables"` | Identify by `DeveloperName` or `SetupName`. |
| `SourceConditionLogic` is a non-filterable textarea | Not usable in `WHERE`. Auto-filled (`"1"`, `"1 AND 2"`) whenever criteria exist: non-blank ≠ custom logic. |
| `DecisionTableDataset` / `DecisionTableRecordset` reject aggregates and partial filters | A table's own row count is not queryable. |
| `CalculationMatrix.DecisionMatrixType` joins `Name` ↔ `SetupName` | The only way to tell a decision table from a decision matrix. |
| A Trialforce org inherits the template's `LastSyncDate` | A sync earlier than `Organization.CreatedDate` proves the table was never built in this org. |

---

## 9. Debugging checklist

**Pricing or rating is wrong while the data looks right:**

1. Confirm the table exists and is Active (§3.1); identify it by `DeveloperName`, and its recipe via `PricingRecipeTableMapping`.
2. Run the freshness check (§7.1). If stale, refresh and re-test before anything else.
3. Confirm the refresh completed: `LastSyncDate` advanced, not just `Queued`; read `refreshStatus` / `refreshFailureReason`.
4. Check the source criteria against the rows' current state (§7.2).
5. CSV tables: `uploadStatus` = `Completed`, row count matches the file, encodings per §4.2.
6. Check INPUT `operator`, `sequence` / `conditionCriteria`, and `filterResultBy`.

**Typical errors:**

| Error or symptom | Cause | Fix |
|---|---|---|
| `sObject type 'DecisionTable' is not supported` | Standard API | `--use-tooling-api` |
| `FIELD_NOT_UPDATABLE`, "Can't edit an active Decision Table" | Edit/deploy on Active table | Deactivate → edit → reactivate → refresh |
| `INVALID_OPERATION` + `DEPENDENCY_EXISTS` | Deleting an Active table | Deactivate first |
| `FIELD_INTEGRITY_EXCEPTION: Required field is missing: status` | Tooling PATCH without `status` | Send current `status` |
| `INVALID_INPUT` on table Status PATCH | CSV version still Active | Deactivate the version |
| `INVALID_API_INPUT: Enter a valid versionNumber…` | Versioned CSV table | Pass `VersionNumber` |
| Refresh `Queued`, nothing changes | Incremental disabled, or `isIncremental` misspelled | Full refresh |
| `CompletedWithErrors` | Cells failed coercion | Fix cells, reload into a fresh table |
| `UNKNOWN_EXCEPTION` on `/data` | `filter` + truncating `limit` | Drop `limit` |
| `/data` returns 0 rows | Unknown field or case mismatch | Check column and exact value |
| Rows missing after an automated refresh | Fired before criteria were true | Trigger on the state transition |
