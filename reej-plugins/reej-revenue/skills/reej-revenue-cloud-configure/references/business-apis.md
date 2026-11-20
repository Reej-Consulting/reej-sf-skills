# Revenue Cloud — Business APIs
> Adapted from [SalesforceLabs/revenue-cloud-foundations](https://github.com/SalesforceLabs/revenue-cloud-foundations) (Apache-2.0), `.cursor/skills/rlm-business-apis` and `postman/docs`, commit `c850652` — Release 264 / API v68.0. Modified by Reej Consulting: repo-specific tooling removed, content condensed.

1. [Conventions](#conventions)
2. [Transaction Management](#transaction-management)
3. [Pricing and procedure plans](#pricing-and-procedure-plans)
4. [Rate Management](#rate-management)
5. [Product Catalog Management (PCM)](#product-catalog-management-pcm)
6. [Product Discovery](#product-discovery)
7. [Product Configurator](#product-configurator)
8. [Usage Management](#usage-management)
9. [Billing](#billing)
10. [Context Service](#context-service)
11. [API vs DML and metadata](#api-vs-dml-and-metadata)
12. [Errors, limits and fixes](#errors-limits-and-fixes)

## Conventions

- Paths below are appended to `/services/data/v68.0`. They span several resource families — `/connect/`, `/revenue/`, `/commerce/`, `/industries/`, `/asset-management/`, `/global-promotions-management/` — so never assume a `/connect/` prefix.
- "Since" = first API version where the resource exists (Spring '26 = v66.0, Summer '26 = v67.0 / Release 262, Winter '27 = v68.0 / Release 264). Fields tagged `v65`, `v67`… appeared later than the resource.
- Auth: OAuth bearer token, JSON bodies, standard API limits. Optional `correlationId` on most calls for tracing.
- Many reads are `POST` because the body carries filters or buyer context (PCM lists, all Product Discovery).
- Sync/async, as documented: Place Sales Transaction returns a tracker ID whose errors are fetched separately (v66); invoice PDF batch `run`/`retry` are asynchronous; schedulers run batches on a cadence. Configurator and ramp-deal calls change a server-side context that must be persisted explicitly. No other async behavior is documented.
- Lifecycle: discover → configure → price → place quote → (approval) → place order → activate → assets → amend / renew / cancel / upgrade / downgrade / swap.

## Transaction Management

| Method | Path | Purpose | Since |
|---|---|---|---|
| POST | `/connect/rev/sales-transaction/actions/place` | Create/update a quote or order (header, lines, groups) with configuration, pricing and estimated tax | 63 |
| POST | `/connect/revenue/transaction-management/sales-transactions/actions/read` | Read a transaction snapshot from an initialized/hydrated context | 65 |
| POST | `/connect/rev/sales-transaction/actions/clone` | Clone a Quote, Order, line or group (a group clones its items) | 64 |
| POST | `/connect/rev/sales-transaction/actions/place-supplemental-transaction` | Supplemental/change order after submission (e.g. during fulfillment) | 64 |
| GET | `/connect/revenue/transaction-management/sales-transactions/actions/place/{trackerId}/errors` | Async errors of a Place call; `?includeRetryablePayload=true` | 66 |
| POST | `/industries/cpq/quotes/actions/get-instant-price` | Instant pricing for the line grid/summary; creates or updates a pricing context; line grouping | 60 |
| POST | `/revenue/transaction-management/sales-transactions/actions/get-eligible-promotions` | Eligible promotions for given lines | 66 |
| POST | `/connect/advanced-approvals/approval-submission/preview` | Preview approval levels, chains, approvers, conditions (Advanced Approvals domain) | 65 |
| POST | `/connect/revenue-management/assets/actions/amend` | Amendment quote/order from assets | 62 |
| POST | `/connect/revenue-management/assets/actions/cancel` | Cancellation quote/order | 62 |
| POST | `/connect/revenue-management/assets/actions/renew` | Renewal quote/order | 62 |
| POST | `/revenue/transaction-management/assets/actions/upgrade` | Upgrade to a higher-tier product | 66 |
| POST | `/revenue/transaction-management/assets/actions/downgrade` | Downgrade to a lower-tier product | 66 |
| POST | `/revenue/transaction-management/assets/actions/swap` | Swap one product for another | 66 |
| POST | `/connect/revenue-management/sales-transaction-contexts/{resourceId}/actions/ramp-deal-create` | Create line ramp segments | 62 |
| POST | `/connect/revenue-management/sales-transaction-contexts/{resourceId}/actions/ramp-deal-update` | Change segment quantity/discount/dates | 62 |
| POST | `/connect/revenue-management/sales-transaction-contexts/{resourceId}/actions/ramp-deal-delete` | Collapse a ramp back to one line | 62 |
| GET | `/connect/revenue-management/sales-transaction-contexts/{resourceId}/actions/ramp-deal-view` | View segments (`transactionId`, `transactionLineId` required) | 62 |
| GET, POST, PUT | `/global-promotions-management/promotions` | Unified Promotions (`promotionDetails`, `rules`); full schema in the Loyalty/Unified Promotions API | 66 |
| POST | `/commerce/quotes/actions/place` | Deprecated v63 — needs "Create on Quotes"; max 300 lines | 60 |
| POST | `/commerce/sales-orders/actions/place` | Deprecated v63 — needs PlaceOrder API permission set; max 300 lines | 60 |

**Place Sales Transaction** — `graph` (sObject graph: Quote, QuoteLineItem, Order, OrderItem, QuoteLineGroup, OrderItemGroup, extended-context custom objects; create/update/delete) **or** `contextDetails` (one is required); `pricingPref` `Force|Skip|System` (default System); `configurationPref`; `catalogRatesPref` `Fetch|Skip` (default Skip, Usage-Based Selling only); `taxPref` `Skip` (v65, tax runs otherwise); `groupRampAction` (v65) `AddProducts|DeleteProducts|EditGroup|EditRampSchedule|DeleteSegment|ConvertToNonRampedGroup`. Limits: 1,000 lines per quote or order, 3,000 line-item attributes.

**Read** — `contextId` (req), `queryTags` (e.g. `Quote`, `QuoteLineItem`), `sobjectFieldMap` (v67; empty list = all fields), `filters` (v67).

**Clone** — `recordIds` (only one honored), `salesTransactionId`, `options.recordTypeId`, `options.lineScope` `AllLines|RampedLinesOnly` (v65; only the last ramp segment can be cloned).

**Supplemental** — `relatedSalesTransactionId`, `pricingPref`, `supplementalGraph` (records use `attributes.method` = `PATCH` and the original order/order item IDs). Original order must not be assetized, not billed (if Billing configured), and not past the DRO point-of-no-return milestone (the fulfillment plan is then frozen).

**Instant pricing** — `contextId` (new context if omitted), `correlationId`, `records` (graph-style, `referenceId` + `record.attributes.type/method`).

**Eligible promotions** — `salesTransactionId`, `lineItemIds`. **Approval preview** — `flowApiName`, `objectApiName`, `recordId`, `inputParameters` (v67).

**Amend / cancel / renew** — common: `assetIds`, `outputRecordType` (req), `outputRecordId`, `contractId`, `opportunityId`. Amend adds `amendmentStartDate`, `quantityChange` (req); cancel adds `cancellationDate` (all assets in one price book); renew adds `renewalStartDate` (required for early renewal and expired assets: today or later), `renewalEndDate`. Permission sets: InitiateAmend, InitiateCancellation, InitiateRenewal.

**Upgrade / downgrade / swap** — `swapStartDate`, `outputRecordType`, `swapGroups[]` (`outGroup.swapAssets[{assetId, quantity}]`, `inGroup.graphId` + `records`), `contractId`, `opportunityId`. Each creates an amendment quote and order; on assetization the old and new assets get linked asset actions.

**Ramp deals** (line ramps only; group ramps go through `groupRampAction`) — create: `transactionId`, `transactionLineId`, `subscriptionTerm`, `subscriptionTermUnit` `MONTHS`, `segmentType` `FREE_TRIAL|CUSTOM|YEARLY`, `trialTerm` + `trialTermUnit` `DAYS`, `executionSettings` (`executePricing`, `executeConfigRules`). Update: `addedNodes` / `updatedNodes` / `deletedNodes` (`contextNodePath` + `contextNode`, e.g. `Discount`, `Quantity`, `StartDate`). Delete: `rampDealIds`. All three return an updated context: call Place Sales Transaction with that context ID to persist.

## Pricing and procedure plans

| Method | Path | Purpose | Since |
|---|---|---|---|
| POST | `/connect/core-pricing/pricing` | Create + hydrate a context and price it in one call | 60 |
| POST | `/connect/core-pricing/price-contexts/{contextId}` | Price an existing context instance | 60 |
| POST | `/connect/core-pricing/pbeDerivedPricingSourceProduct` | Source product for PBE derived pricing (`productId`, `pricebookEntryId`, `effectiveFrom`, `effectiveTo`) | 61 |
| GET | `/connect/core-pricing/apiexecutionlogs/{executionId}` | Log of a pricing API execution | 63 |
| GET | `/connect/core-pricing/pricing-process-execution/{executionId}` | Execution details; `?executionType=API_Execution\|Discovery\|Discovery_Line\|Pricing\|Pricing_Line` | 63 |
| GET | `/connect/core-pricing/pricing-process-execution/lineitems/{executionId}/{executionType}` | Line-level execution (`Pricing_Line` or `Discovery_Line`) | 63 |
| GET | `/connect/core-pricing/sync/{pricingSyncOrigin}` | Sync decision/lookup tables (e.g. `syncData`); `?pricingRecipeId=` (v67, default recipe otherwise) | 60 |
| GET | `/connect/core-pricing/recipe` | Recipe ↔ lookup table mappings | 60 |
| POST | `/connect/core-pricing/recipe/mapping` | Map a recipe to decision tables and a procedure | 60 |
| POST | `/connect/core-pricing/versioned-revise-details` | Versioned revisions of adjustment entities (e.g. AttributeBasedAdjustment, BundleBasedAdjustment) | 60 |
| GET | `/connect/core-pricing/waterfall/{lineItemId}/{executionId}` | Persisted waterfall; `?tagsToFilter=` (v61), `?usageType=Pricing\|Discovery\|Rating` (v62) | 60 |
| POST | `/connect/core-pricing/waterfall` | Write a waterfall log | 60 |
| GET | `/connect/core-pricing/simulationInputVariablesWithData` | Simulation inputs; `contextDefinitionId`, `contextMappingId`, `entityId` (quote/order), `expressionSetVersionId` (`9QM…`) all required | 64 |
| GET, POST | `/connect/procedure-plan-definitions` | List (`?isTemplate=true` = file-based templates) / create definitions | 62 |
| GET, PATCH, DELETE | `/connect/procedure-plan-definitions/{procedurePlanDefinitionId}` | Read/update/delete a definition | 62 |
| POST | `/connect/procedure-plan-definitions/evaluate` | Evaluate by primary object IDs | 62 |
| POST | `/connect/procedure-plan-definitions/evaluate/{procedurePlanDefinitionName}` | Evaluate by definition name | 62 |
| POST | `/connect/procedure-plan-definitions/{procedurePlanDefinitionId}/version` | Create a version | 62 |
| GET, PATCH, DELETE | `/connect/procedure-plan-definitions/versions/{procedurePlanVersionId}` | Read/update/delete a version | 62 |

**Pricing** — `contextDefinitionId`, `contextMappingId`, `jsonDataString` (all req; the JSON must be sent as a **string**, i.e. stringified), `pricingProcedureId` (ID or API name), `configurationOverrides` (`skipWaterfall`, `useSessionScopedContext`, `persistContext`, `referenceKey`, `displayContext`, `taggedData`, `isHighVolumeLineItems`). Price context: `procedureName`, `configurationOverrides`. The response carries per-line final prices and line errors.

**Procedure plans** — definition: `developerName`, `processType` (v63: `Billing`, `DRO`, `DeepClone`, `ProductDiscovery`, `Revenue Cloud`; default `Default`), `primaryObject` (needed for rule-based criteria; unique per definition), `procedurePlanDefinitionVersions[]` (`active`, `contextDefinition`, `readContextMapping`, `saveContextMapping`, `effectiveFrom`, `rank`). Version: `effectiveTo` (req), `procedurePlanSections[]` → `procedurePlanOptions[]` (`expressionSetApiName`, `logic`, `priority`, `procedurePlanCriterion`). A definition with an active version cannot be deleted; an active version cannot be edited or deleted. Evaluate: `idList`, `evaluationDate` (inside the effective range), `processType`, `sectionType` (`PricingProcedure`, `ProductDiscoveryProcedure`, `ProductQualificationProcedure`, `PricingDiscoveryProcedure`, `DiscountSpreadServiceProcedure`, `RatingProcedure`, `RatingDiscoveryProcedure`, `Custom`), `subSectionType` (sectionType + subSectionType unique per version).

## Rate Management

| Method | Path | Purpose | Since |
|---|---|---|---|
| GET | `/connect/core-rating/rate-plan` | Rate plan from the rating engine; `contextId`, `procedureApiName` required | 62 |
| GET | `/connect/core-pricing/waterfall/{lineItemId}/{executionId}?usageType=Rating` | Persisted rating waterfall (same resource as pricing waterfall) | 62 |

Rate plan: one price book and one sellable product per request, product ID required. Prerequisites: **Rate Management: Run Time User** permission set and a default usage rating discovery procedure in Revenue Settings. `lineItemId` can be a quote, order or billing line.

## Product Catalog Management (PCM)

Admin/integration catalog access, no buyer context.

| Method | Path | Purpose | Since |
|---|---|---|---|
| POST | `/connect/pcm/catalogs` | List/search catalogs (`filter` on `name`, `catalogType`; `pageSize` 1–100) | 60 |
| GET | `/connect/pcm/catalogs/{catalogId}` | Catalog details | 60 |
| GET | `/connect/pcm/catalogs/{catalogId}/categories` | Root categories or subtree (`parentCategoryId`, `depth` default 1) | 60 |
| GET | `/connect/pcm/categories/{categoryId}` | Category details | 60 |
| POST | `/connect/pcm/products` | List/search products | 60 |
| GET | `/connect/pcm/products/{productId}` | Product or bundle details; `catalogSystems` `epc\|pcm` (v66) | 60 |
| POST | `/connect/pcm/products/bulk` | Details for many products | 61 |
| POST | `/connect/pcm/relatedRecords/{entityName}` | `ProductRampSegment` / `ProductUsageGrant` records of `product2` | 62 |
| POST | `/connect/pcm/products/variants` | Variations of parent variant products (`parentVariantsIds`) | 67 |
| POST | `/revenue/product-catalog-management/product-classifications/details` | Classification metadata, attributes, attribute categories | 66 |
| POST | `/revenue/product-catalog-management/product-classifications/list` | Paginated classifications (`pageSize` 5/10/25/50/100) | 67 |
| POST | `/connect/pcm/deep-clone` | Clone a `Product2` with related records | 63 |
| GET | `/connect/pcm/index/configurations` | Index configurations (`fieldTypes`, `includeMetadata`) | 62 |
| PUT | `/connect/pcm/index/configurations` | Replace the full index configuration set | 62 |
| GET | `/connect/pcm/index/setting` | Index languages and grouping | 63 |
| PATCH | `/connect/pcm/index/setting?settingId=` | Update `setting.defaultLanguage`, `setting.supportedLanguages` | 63 |
| GET | `/connect/pcm/index/snapshots` | Index snapshots (`numberOfIndexLogs` 0–100, default 25) | 62 |
| POST | `/connect/pcm/index/deploy` | Build indexes for a snapshot | 62 |
| GET | `/connect/pcm/index/error` | Indexing errors (`indexId`, `snapshotIndexId`) | 63 |
| GET | `/connect/pcm/unit-of-measure/info` | UoM metadata (`ids` optional) | 63 |
| POST | `/connect/pcm/unit-of-measure/rounded-data` | Round values per UoM precision | 63 |

**List products** — scope with `catalogIds`, `categoryIds` or query `productClassificationId`; `filter` on `name`, `description`, `isActive` (only `name` with indexed search), operators `eq|in|contains` plus `gt|lt|gte|lte` (v63, number/date); `searchTerm` (v62); `additionalFields` (`Product2` fields, v61); `relatedObjectFilters` (`ProductSpecificationRecType.IsCommercial` `eq`); `pageSize` 1–200 (default 100). `language` (v64) returns translations on most PCM reads.

**Bulk** — `productIds` (invalid IDs skipped), `uptoLevel` (max 1; full bundle hierarchy if omitted), `additionalFields` (`Product2`, `ProductAttributeDefinition` — field must also exist on `ProductClassificationAttr`; with DRO, `AttributeDefinition` opt-out fields), `catalogSystems` (only one value honored).

**Related records** — `recordIds` (max 20), `relatedObjectNodes` (max 2, each with `relatedObjectAPIName`). **Deep clone** — `mainObjectApiName` = `Product2`, `mainRecordId`, `mainRecordFieldValues` (only `Name`). **Index deploy** — `buildType` `FULL|INCREMENTAL` (v63), `snapshot.id`, `snapshot.activationType` `IMMEDIATE`. **Index configurations** — `indexConfigurations[]` (`name`, `type`, `attributeDefinitionId` or `attributeFieldId`, `isSearchable`, `isFacetable` v63).

## Product Discovery

Buyer-context catalog: entitlements, qualification, pricing, promotions. All POST.

| Method | Path | Purpose | Since |
|---|---|---|---|
| POST | `/connect/cpq/catalogs` | Catalogs visible to the buyer (`limit`, `offset`, `orderBy`) | 60 |
| POST | `/connect/cpq/catalogs/{catalogId}` | Catalog in buyer context | 60 |
| POST | `/connect/cpq/categories` | Categories of `catalogId` (req); drops categories with no entitled products | 60 |
| POST | `/connect/cpq/categories/{categoryId}` | Category in buyer context | 60 |
| POST | `/connect/cpq/products` | Product grid for catalog/category, priced and qualified | 60 |
| POST | `/connect/cpq/products/{productId}` | One product: attributes, hierarchy, cardinality, price | 60 |
| POST | `/connect/cpq/products/search` | Keyword search (uses the PCM index when indexed data is on) | 60 |
| POST | `/connect/cpq/products/bulk` | Many products (`productData[{productId, productSellingModelId}]`) | 61 |
| POST | `/connect/cpq/products/guided-selection` | Products from a guided selling response or search terms | 62 |
| POST | `/connect/cpq/qualification` | Run the qualification procedure on `productIds` | 60 |
| POST | `/revenue/product-discovery/products/recommendations` | Recommendations for a quote/order from constraint rules | 67 |

Shared body fields: `userContext` (account ID, contact ID…), `priceBookId` (marked required on list/get product; standard price book used when omitted), `currencyCode` (required in multi-currency orgs), `catalogId`, `categoryId`, `enablePricing` / `enableQualification` (default `true`; the **Pricing Procedure** / **Qualification Procedure** Setup toggles override them), `pricingProcedure`, `qualificationProcedure`, `contextDefinition`, `contextMapping`, `additionalContextData` (max 10 nodes), `additionalFields` (v61; v66 adds proration policy per selling model option), `usePromotions` (v66; on categories defaults to true when Promotions is enabled; default false on recommendations), `transactionId` / `transactionContextId` (v67; v66 on search), `executeConfigurationRules` (v67), `limit` (default 10), `cursor`, `filter` (`name`).

Search: `query` (e.g. `{"textQuery":{"searchPhrase":"<term>"}}`) or `searchTerm` (v62). Guided selection: `catalogId`, `priceBookId`, and `guidedSelectionResponseId` or `searchTerms[{term, tags}]` (searchTerms wins); guided selling rules must exist in Revenue Cloud Setup. Recommendations `filter` is one object with a `criteria[]` array (`property`, `operator`, `value`); `enablePricing`/`enableQualification` cannot be forced to `true` when Pricing/Qualification is disabled in the org.

## Product Configurator

Stateful: a configuration session lives in a context (`contextId`) tied to `transactionId` / `transactionLineId` until saved.

| Method | Path | Purpose | Since |
|---|---|---|---|
| POST | `/connect/cpq/configurator/actions/configure` | Run rules, return violations and pricing; can apply node changes in the same call | 60 |
| POST | `/connect/cpq/configurator/actions/load-instance` | Open a session from `transactionId` | 60 |
| POST | `/connect/cpq/configurator/actions/get-instance` | JSON of the configuration (`contextId`) | 60 |
| POST | `/connect/cpq/configurator/actions/save-instance` | Persist the session to the transaction (`contextId`) | 60 |
| POST | `/connect/cpq/configurator/actions/set-instance` | Load a configuration stored outside Salesforce (`transaction` JSON string, `contextMappingId`) | 60 |
| POST | `/connect/cpq/configurator/actions/add-nodes` | Add components (`addedNodes[{path, addedObject}]`) | 60 |
| POST | `/connect/cpq/configurator/actions/update-nodes` | Change attributes (`updatedNodes[{path, updatedAttributes}]`) | 60 |
| POST | `/connect/cpq/configurator/actions/delete-nodes` | Remove components (`deletedNodes[{path}]`) | 60 |
| POST | `/connect/cpq/configurator/actions/set-product-quantity` | `contextId`, `quantity`, `transactionLinePath` | 60 |
| GET | `/connect/cpq/configurator/saved-configuration?referenceRecordId=` | List saved configurations of a record | 63 |
| POST | `/connect/cpq/configurator/saved-configuration` | Save (`referenceRecordId`, `data` JSON string, `name`, `description`) | 63 |
| PUT | `/connect/cpq/configurator/saved-configuration/{id}` | Update (`data`, `name`, `description` all required) | 63 |
| DELETE | `/connect/cpq/configurator/saved-configuration/{id}` | Delete (irreversible) | 63 |
| POST | `/revenue/product-configurator/rules/actions/execute` | Run configuration rules on `transactionId` or `transactionContextId`; `ruleOptions.isUpdateContextRequired` | 67 |

**Configure** — `transactionId` (req), `transactionLineId`, `transactionContextId`, `qualificationContext` (`accountId`, `contactId`, `contextId`), `configuratorOptions` (single object: `pricingProcedure` plus booleans `addDefaultConfiguration`, `executeConfigurationRules`, `executePricing`, `explainabilityEnabled` v66, `qualifyAllProductsInTransaction`, `returnProductCatalogData`, `validateAmendRenewCancel`, `validateProductCatalog`), `contextResponseType` (v65) `Delta|Full|None|Product` — required above 1,000 and below 15,000 lines — and `addedNodes` / `updatedNodes` / `deletedNodes`. Node operations accept the same `configuratorOptions` and `qualificationContext`; rules are re-evaluated after each change.

## Usage Management

| Method | Path | Purpose | Since |
|---|---|---|---|
| GET | `/asset-management/assets/{assetId}/usage-details` | Grants, resources and rates (incl. negotiated) of an asset; `effectiveDate` required | 63 |
| GET | `/commerce/sales-orders/line-items/{orderItemId}/usage-details` | Same for an order product | 63 |
| GET | `/commerce/quotes/line-items/{quoteLineItemId}/usage-details` | Same for a quote line | 62 |
| GET | `/revenue/usage-management/binding-objects/{bindingObjectId}/actions/usage-details` | Grants, resources, rates, policies of a binding object; `effectiveDate` `yyyy-MM-dd` required | 65 |
| POST | `/revenue/usage-management/consumption/actions/trace` | Overage and drawdown breakdown per invoice line (`liableSummaryIds`) | 66 |
| POST | `/revenue/usage-management/usage-products/actions/validate` | Validate usage product setup (`productIds` max 10, `startDate`, `endDate`) | 66 |
| POST | `/revenue/usage-management/usage-products/actions/activate` | Activate a usage product and its design-time records | 67 |

Asset/order/quote line details take `optionalFields` (custom fields on the matching `…RateCardEntry` / `…RateAdjustment` object) and do not return binding target rates. Binding objects: Account, Contract, BindingObjectCustomExt, or an anchor Asset not bound to a target.

**Activate** — `activationRequests` (exactly one `{productId, usageResourceIds}`; omit `usageResourceIds` to activate everything linked to the product), `shouldValidateProductSetup` (default `true`). Max 200 records per call (product + children: grants, policies, UoM, UoM classes, rate card entries). Records stay Draft until activated; activation follows dependency order; any failure rolls back the whole product.

## Billing

| Method | Path | Purpose | Since |
|---|---|---|---|
| POST | `/commerce/invoicing/invoices/collection/actions/generate` | Invoice for an account, order or billing schedules | 62 |
| POST | `/commerce/invoicing/invoices/collection/actions/post` | Draft → Posted (one invoice per call) | 62 |
| POST | `/commerce/invoicing/invoices/collection/actions/preview` | Preview invoices with estimated tax, next two billing periods | 63 |
| POST | `/commerce/invoicing/invoices/collection/actions/ingest` | Invoice from internal/external billing data (one per call) | 63 |
| POST | `/commerce/invoicing/invoices/actions/write-off` | Write off: credit memo for the total, invoice closed | 64 |
| POST | `/commerce/invoicing/invoices/{invoiceId}/actions/void` | Void a posted invoice (no body) | 62 |
| POST | `/commerce/invoicing/invoices/{invoiceId}/actions/credit` | Create and apply a credit memo (full or partial) | 62 |
| POST | `/commerce/invoicing/invoices/{invoiceId}/actions/convert-to-credit` | Negative invoice lines → posted credit memo | 62 |
| POST | `/commerce/invoicing/invoices/collection/actions/calculate-estimated-tax` | Estimated tax for lines in Pending/Estimated tax status (one invoice per call) | 63 |
| POST | `/commerce/invoicing/invoice-batch-runs/actions/send-email` | Email posted invoices of a batch run (`invoiceBatchRunId` in body) | 65 |
| POST | `/commerce/invoicing/invoice-batch-runs/{invoiceBatchRunId}/actions/draft-to-posted` | Post a batch of draft invoices | 62 |
| POST | `/commerce/invoicing/invoice-batch-runs/{invoiceBatchRunId}/actions/recover` | Recover a failed invoice run | 62 |
| POST | `/commerce/billing/invoices/invoice-batch-docgen/{invoiceBatchRunId}/actions/run` | Async PDF generation for a batch run | 63 |
| POST | `/commerce/billing/invoices/invoice-batch-docgen/{invoiceBatchRunId}/actions/retry` | Async retry of failed PDFs | 63 |
| POST | `/revenue/billing/document/actions/generate` | Generate an invoice document, update junction record | 66 |
| POST | `/revenue/billing/transactions/actions/apply` | Apply payments and credits to an account's invoices per Billing Settings rules | 66 |
| POST | `/commerce/invoicing/invoice-schedulers` | Create invoice scheduler | 62 |
| PUT | `/commerce/invoicing/invoice-schedulers/{billingBatchSchedulerId}` | Update scheduler (Draft/Inactive only) | 63 |
| POST | `/commerce/invoicing/credit-memos/actions/generate` | Standalone credit memo, applied later | 62 |
| POST | `/commerce/invoicing/credit-memos/{creditMemoId}/actions/apply` | Apply a credit memo to invoices | 62 |
| POST | `/commerce/invoicing/credit-memo-lines/{creditMemoLineId}/actions/apply` | Apply at line level | 62 |
| POST | `/commerce/invoicing/credit-memo-inv-applications/{creditMemoInvApplicationId}/actions/unapply` | Unapply from an invoice | 62 |
| POST | `/commerce/invoicing/credit-memo-line-invoice-line/{creditMemoLineInvoiceLineId}/actions/unapply` | Unapply at line level | 62 |
| POST | `/commerce/invoicing/credit/collection/actions/post` | Post a draft credit memo (`creditMemoIds`, one per call) | 65 |
| POST | `/commerce/billing/credit-memos/{creditMemoId}/actions/void` | Void a posted credit memo (no body) | 66 |
| POST | `/commerce/invoicing/billing-schedules/actions/create` | Billing schedules for orders via context service (`billingTransactionIds`) | 62 |
| POST | `/commerce/invoicing/standalone/billing-schedules/actions/create` | Billing schedules from any internal/external transaction | 64 |
| POST | `/commerce/invoicing/billing-schedules/collection/actions/recover` | Recover last invoice of schedules in Error/Processing (one per call) | 62 |
| POST | `/commerce/invoicing/actions/suspend-billing` | Suspend billing (account or schedule group) | 63 |
| POST | `/commerce/invoicing/actions/resume-billing` | Resume billing | 63 |
| POST | `/commerce/billing/payments/{paymentId}/actions/apply` | Apply a payment to an invoice | 64 |
| POST | `/commerce/billing/payments/{paymentId}/paymentlines/{paymentLineId}/actions/unapply` | Unapply a payment line | 64 |
| POST | `/commerce/billing/refunds/{refundId}/actions/apply` | Refund against a payment | 64 |
| POST | `/commerce/payments/payment-schedulers/` | Create payment scheduler | 64 |
| PATCH | `/commerce/payments/payment-schedulers/{billingBatchSchedulerId}` | Set status `Active\|Canceled\|Draft\|Inactive` | 64 |
| POST | `/commerce/taxes/actions/calculate` | Calculate tax for a transaction | 62 |
| POST | `/connect/sequences/policy` | Create invoice/credit memo numbering policy | 65 |
| PATCH | `/connect/sequences/policy/{sequencePolicyId}` | Update a sequence policy | 65 |
| POST | `/connect/sequences/actions/assign` | Assign sequence values (`targetObjectIds`, `sequencePolicyId`, `shouldPublishPlatformEvent`) | 65 |
| POST | `/connect/sequences/gap-reconciliation` | Restore missing values in gapless sequences | 65 |
| POST | `/revenue/billing/accounts/{accountId}/statement` | Account statement | 66 |
| GET | `/revenue/billing/billing-arrangement/{billingArrangementId}` | Billing arrangement and its lines | 66 |

Salesforce Payments (Commerce Payments API, outside the RLM guide), all POST: `/commerce/payments/payment-methods` (tokenize), `/commerce/payments/sales`, `/commerce/payments/authorizations`, `/commerce/payments/authorizations/{authorizationId}/captures`, `/commerce/payments/authorizations/{authorizationId}/reversals`, `/commerce/payments/payments/{paymentId}/refunds`.

**Generate invoice** — one of `accountId` (v63), `billingScheduleIds` (max 200) or `billingTransactionId`; `action` `Draft|Posted`, `invoiceDate`, `targetDate` (req). **Preview** — `billingTransactionId`, `numberOfBillingPeriods` (v64), `previewDate`. **Write-off** — `invoices[{invoiceId, reasonCode, description}]`.

**Credit and apply** — `invoiceLines[]` (req), `taxStrategy` `Ignore|ManualOverride|CopyFromInvoiceLine|Calculate` (req), `type` `Posted|Draft`, `effectiveDate`, `taxEffectiveDate`. **Standalone credit memo** — `billingAccountId`, `charges[]` (at least one), `taxStrategy` `Ignore|ManualOverride|Calculate`, `type`, `billToContactId`, `currencyIsoCode`, `externalReference`. **Apply credit memo** — `applications[{appliedToId, amount, description, effectiveDate}]`. **Convert to credit** — `effectiveDate` (req), `invoiceLines`.

**Standalone billing schedules** — `transactionContextDetails` (`contextDefinitionName`, `readContextMappingName`, `saveContextMappingName`, `intraContextCustomMappingName` v65) and `transactionDetails` (JSON string whose shape depends on `SellingModelType__std` `OneTime|TermDefined|Evergreen` and `BillingActionType__std`). **Suspend** — `referenceIds[{referenceId, suspendDate, resumeDate}]`; **resume** — `referenceIds[{referenceId, resumeDate}]`.

**Payment / refund apply** — `appliedToId`, `amount` (req), `comments`, `effectiveDate`; payment apply also `associatedAccountId`.

**Invoice scheduler** — `schedulerName`, `status` `Draft|Active|Inactive`, `invoiceStatus` `Draft|Posted`, `frequencyCadence` `Once|Daily|Weekly|Monthly`, `frequencyCadenceOptions`, `preferredTime`, `startDate` (all req), `endDate` and `isInvoiceDateFromRunDate` (v63), `timezone`, `filterCriteria[]`; `invoiceDate`/`targetDate` when `Once`, `invoiceDateOffset`/`targetDateOffset` otherwise. **Payment scheduler** — `schedulerName`, `startDate`, `preferredTime`, `frequencyCadence`, `status`; Monthly also needs `endDate`, `recursEveryMonthOnDay`, `criteriaMatchType` `MatchAny|MatchNone`, `filterCriteria`.

**Tax** — `lineItems[]`, `taxEngineId`, `taxType` `Actual|Estimated`, `transactionDate` (req); optional `addresses`, `customerDetails`, `sellerDetails`, `isCommit`, `taxTransactionType` `Debit|Credit|Void`.

**Sequence policy** — `name`, `targetObject` `Invoice|CreditMemo` (CreditMemo v66), `sequenceMode` `Basic|Gapless`, `sequencePattern`, `sequenceStartNumber`, `incrementNumber`, `dateStampFormat`, `effectiveFromDateTime`, `filterCriteria`, `isActive` (all req). Gap reconciliation: `sequencePolicyIds` **or** `targetObjects`, never both.

**Account statement** — `startDate` (`YYYY-MM-DD`, processes 90 days from it), `associatedAccountIds` (max 50), `transactionTypes` `All|CreditMemo|DebitMemo|Invoice|Payment|Refund`, `shouldShowOpenBalancesOnly`, `documentTemplateId`.

## Context Service

The v264 guide has no Context Service Business-API section; these are v59-era resources — verify on the target org.

| Method | Path | Purpose | Since |
|---|---|---|---|
| GET | `/connect/context-definitions` | List context definitions | 59 |
| POST | `/connect/context-definitions` | Create a context definition | 59 |
| GET | `/connect/context-definitions/{contextDefinitionId}` | Definition with nodes, attributes, mappings | 59 |

A context definition is the schema, a context mapping binds sObject fields to it, and a context instance is hydrated at run time. A context definition must be **activated** before use. Pricing takes `contextDefinitionId` + `contextMappingId`; Discovery accepts `contextDefinition` / `contextMapping`; configurator load/set-instance take `contextMappingId`.

## API vs DML and metadata

1. Quotes/orders whose lines must be configured, priced and taxed: Place Sales Transaction rather than raw DML.
2. Amendments, renewals, cancellations: asset lifecycle APIs or the equivalent invocable actions; Place Sales Transaction does not support them.
3. Full transaction snapshot: Read Sales Transaction instead of field-by-field SOQL.
4. Line ramps: ramp-deal APIs. Group ramps: Place Sales Transaction `groupRampAction`.
5. Computed prices come from the Pricing API and its procedures; do not write PricebookEntry records to emulate them.
6. Decision table refresh: full sync via `/connect/core-pricing/sync/...`; partial sync via the Decision Table Refresh Action in a Flow.
7. Catalog administration and integration reads: PCM. Anything buyer-specific (entitlements, qualification, price, promotions): Product Discovery.
8. Usage products: the activation API activates the product and its usage records in dependency order with rollback.
9. Configurations kept in an external system: `set-instance`. Transactions billed from outside RLM: standalone billing schedules or invoice ingestion.
10. Procedure plans: `GET /connect/procedure-plan-definitions?isTemplate=true` returns file-based templates; `false` (default) returns database records.

## Errors, limits and fixes

| Symptom | Cause → fix |
|---|---|
| Header saved, lines missing after Place | Place commits the header first and does not roll it back when line/group steps fail → `GET …/place/{trackerId}/errors?includeRetryablePayload=true`, read `rollbackedReferenceIds`, resend the corrected payload (config/tax warnings are not listed there) |
| Usage-product amendment order fails at activation | Direct-to-order amendment creates Order Products without Rate Card Entries → amend with `outputRecordType` = `Quote`, then create the order from that quote |
| `MAX_LIMIT_EXCEEDED` on usage activation | More than one `activationRequests` entry → one product per call, max 200 records |
| Array field takes a single value | Clone `recordIds`, invoice post `invoiceIds`, `creditMemoIds`, schedule recovery `billingScheduleIds`, ingest `invoices`, estimated-tax `invoiceIds`, PCM `catalogSystems` → one call per record |
| Ramp or configurator change not persisted | These APIs update the context only → Place Sales Transaction with the returned context ID, or `save-instance` |
| No waterfall in Price Context response | Price waterfall disabled in Salesforce Pricing Setup → enable it |
| Stale prices from lookup tables | Decision tables not synced → Pricing Data Sync or Decision Table Refresh Action |
| `contains` filter or non-name sort fails | Indexed search enabled → use `eq`/`in`, sort on `name` |
| Search misses products | Search relies on the PCM index → check `/connect/pcm/index/error`, redeploy the snapshot (`FULL`/`INCREMENTAL`) |
| Billing schedules stuck in Error/Processing/Void In Progress | Failed invoice run → `invoice-batch-runs/{invoiceBatchRunId}/actions/recover` or `billing-schedules/collection/actions/recover` |
