# Revenue Cloud — data model
> Adapted from [SalesforceLabs/revenue-cloud-foundations](https://github.com/SalesforceLabs/revenue-cloud-foundations) (Apache-2.0), `.cursor/skills/revenue-cloud-data-model`, commit `c850652` — Release 264 / API v68.0. Modified by Reej Consulting: repo-specific tooling removed, content condensed.

## Contents

1. [Scope and abbreviations](#1-scope-and-abbreviations)
2. [Release changes and misconceptions](#2-release-changes-and-misconceptions)
3. [Cross-domain hubs](#3-cross-domain-hubs)
4. [Domains](#4-domains): PCM, Pricing, Rates, Configurator, Transactions, DRO, Usage, Billing, Approvals
5. [Lifecycles and status flows](#5-lifecycles-and-status-flows)
6. [Load order and teardown](#6-load-order-and-teardown)
7. [Gotchas](#7-gotchas)

## 1. Scope and abbreviations

Platform (standard) schema only: standard RLM fields carry no `__c` suffix. Custom and managed-package `__c` fields are out of scope; check them with `sf sobject describe` on the org. `Product2` is the hub that nearly every domain references.

| Abbr. | Meaning | Abbr. | Meaning |
|---|---|---|---|
| PCM | Product Catalog Management | PUR | `ProductUsageResource` |
| PSM | `ProductSellingModel` | PURP | `ProductUsageResourcePolicy` |
| PSMO | `ProductSellingModelOption` | PUG | `ProductUsageGrant` |
| PBE | `PricebookEntry` | TUE | `TransactionUsageEntitlement` |
| PAS | `PriceAdjustmentSchedule` | RABT | `RateAdjustmentByTier` |
| PAT | `PriceAdjustmentTier` | BSG | `BillingScheduleGroup` |
| DRO | Dynamic Revenue Orchestration | CLM | Contract Lifecycle Management |
| CML | Constraint Markup Language | | |

## 2. Release changes and misconceptions

### 262 → 264

70 fields added, 8 removed (all in Usage), no type changes. Seven of the eight removals are one change: usage policy bindings moved off definition and runtime objects onto `ProductUsageResourcePolicy` (product-and-resource binding).

| Removed in 264 | Where the binding lives now |
|---|---|
| `TransactionUsageEntitlement.ChargeForOverage`, `.RatingFrequencyPolicyId`, `.UsageAggregationPolicyId` | PURP → `UsageOveragePolicy` / `RatingFrequencyPolicy` / `UsageResourceBillingPolicy` |
| `TransactionUsageEntitlement.DrawdownOrder` | **Not on PURP** (PURP has no drawdown field). Design time: `ProductUsageGrant.DrawdownOrder`. Runtime: `QuotLineItmUsageRsrcPlcy`, `OrderItemUsageRsrcPlcy`, `BindingObjUsageRsrcPlcy` |
| `UsageResource.UsageResourceBillingPolicyId` | `ProductUsageResourcePolicy.UsageAggregationPolicyId` |
| `RatingFrequencyPolicy.ProductId`, `.UsageResourceId` | `ProductUsageResourcePolicy.RatingFrequencyPolicyId` (the policy no longer knows its product/resource) |
| `ProductUsageGrant.OverageChargeable` | `UsageOveragePolicy.OverageChargeable`, via PURP |

PURP is the new binding site, not the only one: `UsageResourcePolicy` still carries the same four lookups (`RatingFrequencyPolicyId`, `UsageAggregationPolicyId`, `UsageCommitmentPolicyId`, `UsageOveragePolicyId`) at **resource** level. Read PURP for a specific product's use of a resource; `UsageResourcePolicy` is the resource-wide default.

### 260 → 262 (history)

Field-additive (45 added, 0 removed). Polymorphic targets expanded: `Invoice.ReferenceEntityId` now also accepts `Opportunity` and `Quote`. Picklist values removed: IANA time-zone renames on datetime-zone fields, and unused `UsageType` values `InsuranceRuleAction` / `StageManagement` on fulfillment objects.

### Misconceptions

1. "PUG" is `ProductUsageGrant`. `ProductUsageGroup` does not exist.
2. `RateCard.Status` does not exist in any release; `Status` is on `RateCardEntry` (unchanged across 260, 262, 264).
3. `UsageAggregationPolicy` is a **relationship name only**. The object behind `UsageAggregationPolicyId` is `UsageResourceBillingPolicy`; `Schema.UsageAggregationPolicy` does not compile.
4. TUE never carried `UsageCommitmentPolicyId` or `UsageOveragePolicyId` (neither 262 nor 264): do not describe them as removed in 264. TUE went from 40 to 36 fields in 264 (the four removals above, none added). Its only policy lookups ever: `UsageGrantRefreshPolicyId`, `UsageGrantRolloverPolicyId`.
5. The 262 `RateCardEntry` SOAP DML failure is a runtime platform regression, not a schema change. The 262 PUR overlap validation is runtime-gated, not a schema change.

## 3. Cross-domain hubs

| Parent | Referenced by (child.field) |
|---|---|
| `Product2` | `PricebookEntry.Product2Id`, `PriceAdjustmentTier.Product2Id`, `PriceBookEntryDerivedPrice.ProductId`/`ContributingProductId`, `AttributeAdjustmentCondition.ProductId`, `BundleBasedAdjustment.ProductId`/`ParentProductId`/`RootBundleId`, `RateCardEntry.ProductId`, `ProductConfigurationFlow.ReferenceObjectId`, `ProductConfigurationRule.ProductId`, `QuoteLineItem`/`OrderItem`/`Asset`/`FulfillmentOrderLineItem`/`InvoiceLine.Product2Id`, `ProductUsageResource.ProductId`, `UsageResource.UsageDefinitionProductId`, `ProductFulfillmentDecompRule.SourceProductId`/`DestinationProductId`, `ProductFulfillmentScenario.ProductId` |
| `ProductSellingModel` | `.ProductSellingModelId` on `PricebookEntry`, `PriceAdjustmentTier`, `PriceBookEntryDerivedPrice`, `ContractItemPrice`, `QuoteLineItem`, `OrderItem`, `RateCardEntry`, `ProductUsageGrant`, `ProductSellingModelOption`, `AttributeBasedAdjustment`, `ProductRampSegment` |
| `Account` | `.AccountId` on `Contact`, `Quote`, `Order`, `Contract`, `Asset`, `FulfillmentOrder`, `BillingAccount`, `BillingSchedule`, `Invoice`, `CreditMemo`, `Payment`; `Account.ParentId` |
| `Pricebook2` | `PricebookEntry.Pricebook2Id`, `Quote.Pricebook2Id`, `Order.Pricebook2Id`, `PriceBookRateCard.PriceBookId`, `PriceAdjustmentSchedule.Pricebook2Id` |
| `UsageResource` | `.UsageResourceId` on `ProductUsageResource`, `ProductUsageGrant`, `TransactionJournal`, `UsageSummary`, `RateCard`, `RateCardEntry` |
| `LegalEntity` | `.LegalEntityId` on `TaxTreatment`, `TaxRate`, `TaxPolicy`, `BillingTreatment`, `BillingScheduleGroup`, `GeneralLedgerAccount`, `GeneralLedgerAcctAsgntRule`, `LegalEntyAccountingPeriod`, `Invoice`, `InvoiceLine`, `CreditMemo`, `CreditMemoLineTax`, `CreditMemoLineInvoiceLine`, `DebitMemoLine`, `PaymentLineInvoice` |
| `Order` | `OrderItem.OrderId`, `FulfillmentOrder.OrderId`, `.ReferenceEntityId` on `BillingSchedule`, `Invoice`, `CreditMemo` |
| `Quote` | `QuoteLineItem.QuoteId`, `Order.QuoteId` |
| `OrderItem` | `FulfillmentOrderLineItem.OrderItemId`, `AssetActionSource.OrderItemId`, `OrderItem.OriginalOrderItemId` (amendments), `TransactionUsageEntitlement.OrderItemId`; also `OrderItemDetail`, `OrderItemAttribute` |
| `Asset` | `.AssetId` on `AssetAction`, `AssetStatePeriod`, `AssetRelationship`, `TransactionUsageEntitlement`; `Asset.ParentId`/`RootAssetId`; `ProductUsageGrant` |
| `BillingSchedule` | `InvoiceLine.BillingScheduleId`, `BillingPeriodItem`, `BillingMilestonePlanItem.ReferenceItemId`, `BillingSchedule.OriginalBillingScheduleId` |
| `PaymentTerm` | `.PaymentTermId` on `Invoice`, `BillingAccount`, `BillingScheduleGroup`, `PaymentTermItem` |
| `TaxTreatment` | `.TaxTreatmentId` on `BillingSchedule`, `BillingScheduleGroup`, `InvoiceLine`, `CreditMemoLineInvoiceLine`, `DebitMemoLine` |

`Product2` also points outward: `Product2.BillingPolicyId` → `BillingPolicy`, `Product2.TaxPolicyId` → `TaxPolicy`.

## 4. Domains

### 4.1 PCM — product catalog

| Object | Role | Key fields |
|---|---|---|
| `Product2` | Product | `StockKeepingUnit` (unique), `Name`, `ProductCode`, `Family`, `IsActive`, `UsageModelType`, `BillingPolicyId`, `TaxPolicyId` |
| `AttributePicklist` / `AttributePicklistValue` | Attribute value lists | `Name`, `UnitOfMeasureId` / `Code`, `AttributePicklistId` |
| `AttributeDefinition` | Attribute (size, color…) | `Code`, `DataType`, `PicklistId`, `UnitOfMeasureId` |
| `AttributeCategory` / `AttributeCategoryAttribute` | Attribute grouping / junction | `Code`, `Name` / `AttributeCategoryId`, `AttributeDefinitionId` |
| `ProductAttributeDefinition` | Attribute bound to a product | `Product2Id`, `AttributeDefinitionId`, `AttributeCategoryId` |
| `ProductClassification` | Hierarchical taxonomy | `Code`, `ParentProductClassificationId` (self) |
| `ProductClassificationAttr` | Attribute at classification level | `ProductClassificationId`, `AttributeDefinitionId` |
| `ProductCatalog` | Top-level catalog | `Code` |
| `ProductCategory` | Hierarchical category | `Code`, `CatalogId`, `ParentCategoryId` (self) |
| `ProductCategoryProduct` | Junction category ↔ product | `ProductCategoryId`, `ProductId`, `CatalogId` |
| `ProductRelationshipType` | Bundle, Add-On… | `Name` |
| `ProductComponentGroup` | Component group in a bundle | `Code`, `ParentProductId`, `ParentGroupId` (self) |
| `ProductRelatedComponent` | Bundle component | `ParentProductId`, `ChildProductId`, `ProductComponentGroupId`, `ProductRelationshipTypeId` |
| `ProductSellingModel` | One-Time, Evergreen, Term-Defined | `Name`, `SellingModelType` |
| `ProductSellingModelOption` | PSM allowed for a product | `Product2Id`, `ProductSellingModelId`, `ProrationPolicyId` |
| `ProrationPolicy` | Partial-period rules | `Name` |
| `ProductRampSegment` | Ramp segments | `ProductId`, `ProductSellingModelId`, `SegmentType` |
| `ProductQualification`, `ProductDisqualification`, `ProductCategoryQualification`, `ProductCategoryDisqual` | Qualification rules (product / category) | |

### 4.2 Pricing

| Object | Role | Key fields |
|---|---|---|
| `Pricebook2` | Price book | `Name`, `IsStandard`, `CostBookId` |
| `PricebookEntry` | Price of a product + PSM in a book | `Pricebook2Id`, `Product2Id`, `ProductSellingModelId`, `UnitPrice`, `CurrencyIsoCode` |
| `PriceAdjustmentSchedule` | Discount/surcharge schedule | `Name`, `Pricebook2Id`, `CurrencyIsoCode`, `AdjustmentType` |
| `PriceAdjustmentTier` | Tier | `PriceAdjustmentScheduleId`, `Product2Id`, `ProductSellingModelId`, `LowerBound`, `UpperBound` |
| `AttributeBasedAdjRule` | Attribute-pricing rule | `Name` |
| `AttributeAdjustmentCondition` | Condition of a rule | `AttributeBasedAdjRuleId`, `AttributeDefinitionId`, `ProductId` |
| `AttributeBasedAdjustment` | Adjustment for a rule | `AttributeBasedAdjRuleId`, `PriceAdjustmentScheduleId`, `ProductId`, `ProductSellingModelId` |
| `BundleBasedAdjustment` | Bundle-context adjustment | `PriceAdjustmentScheduleId`, `ProductId`, `ParentProductId`, `RootBundleId` |
| `PriceBookEntryDerivedPrice` | Derived price | `PricebookId`, `PricebookEntryId`, `ProductId`, `ContributingProductId`, `ProductSellingModelId` |
| `CostBook` / `CostBookEntry` | Costs | `Name`, `IsDefault` / `CostBookId`, `ProductId` |
| `CurrencyType` | Active currencies | `IsoCode` |

Supporting/runtime: `ContractItemPrice`, `IndexRate`, `PriceRevisionPolicy`, `PricingAPIExecution`, `PricingAdjBatchJob`(`Log`), `PricingProcedureResolution`, `PricingProcessExecution`, `ProcedurePlanCriterion` (`ProrationPolicyId`), `ProductPriceHistoryLog`, `ProductPriceRange`, `ProductSellingModelDataTranslation`.

### 4.3 Rates (usage-based pricing)

| Object | Role | Key fields |
|---|---|---|
| `RateCard` | Rate container (**no `Status`**) | `Name`, `Type`, `UsageResourceId` |
| `RateCardEntry` | Rate for product + resource | `RateCardId`, `ProductId`, `UsageResourceId`, `ProductSellingModelId`, `RateUnitOfMeasureClassId`, `RateUnitOfMeasureId`, `Status` |
| `RateAdjustmentByTier` | Tiered adjustment | `RateCardEntryId`, `RateCardId`, `ProductId`, `ProductSellingModelId`, `LowerBound`, `UpperBound` |
| `RateAdjustmentByAttribute` | Attribute adjustment | `RateCardEntryId`, `RateCardId` |
| `PriceBookRateCard` | Junction price book ↔ rate card | `PriceBookId`, `RateCardId`, `RateCardType` |
| `RatingFrequencyPolicy` | Rating frequency | `RatingPeriod` (bound through PURP since 264) |

Runtime/support: `RatingRequest`, `RatingRequestBatchJob`, `BindingObjectRateCardEntry` (`BindingObjectId` → `BindingObjectCustomExt`), `BindingObjectRateAdjustment`, `BindingObjectCustomExt`. Rate cards use the same `UsageResource` records as PURs; rates depend on PURs, `Product2`, PSM, `UnitOfMeasure(Class)` and `Pricebook2`.

### 4.4 Configurator

| Object | Key fields |
|---|---|
| `ProductConfigurationFlow` (configuration UX flow) | `ReferenceObjectId` → `Product2` |
| `ProductConfigurationRule` (validation/constraint rule) | `ProductId` |
| `ProductConfigFlowAssignment` (flow ↔ context) | |
| `ExpressionSetConstraintObj` (expression-set constraint link) | |

Rules are built with Expression Sets and CML. `TransactionProcessingType` records define which constraint types are active. Configuration flows are typically assigned per product or per classification.

### 4.5 Transactions (quote → order → asset)

| Object | Key fields |
|---|---|
| `Quote` | `AccountId`, `ContactId`, `Pricebook2Id`, `Status`, `ExpirationDate` |
| `QuoteLineItem` | `QuoteId` (master-detail), `Product2Id`, `PricebookEntryId`, `ProductSellingModelId`, `Quantity`, `UnitPrice` |
| `Order` | `AccountId`, `QuoteId`, `ContractId`, `Pricebook2Id`, `SalesTransactionTypeId`, `Status` |
| `OrderItem` | `OrderId` (master-detail), `Product2Id`, `PricebookEntryId`, `ProductSellingModelId`, `QuoteLineItemId`, `OriginalOrderItemId` (self, amendments) |
| `Contract` | `AccountId` |
| `Asset` | `AccountId`, `Product2Id`, `ContactId`, `ParentId`, `RootAssetId` (bundle hierarchy) |
| `AssetStatePeriod` | `AssetId`, `StartDate`, `EndDate`, `Quantity`, `Amount` (time-sliced state) |
| `AssetAction` | `AssetId`, `ActionType` (New, Amend, Renew, Cancel) |
| `AssetActionSource` | `AssetActionId`, `OrderItemId` |
| `AssetRelationship` / `AssetContractRelationship` | `AssetId`, `RelatedAssetId` / `AssetId` |
| `FulfillmentOrder` / `FulfillmentOrderLineItem` | `AccountId`, `OrderId` / `FulfillmentOrderId` (master-detail), `OrderItemId`, `Product2Id` |

Also `SalesTransactionType`, `AssetTokenEvent`, `OrderDeliveryMethod`, `QuoteAction` (quote actions sourced from assets), CLM objects (`ObjectStateDefinition` and its transitions).

| Line detail | Quote side | Order side |
|---|---|---|
| Group (bundles) | `QuoteLineGroup` | `OrderItemGroup` |
| Extended detail | `QuoteLineDetail` | `OrderItemDetail` |
| Attribute values | `QuoteLineItemAttribute` | `OrderItemAttribute` |
| Rate adjustments | `QuoteLineRateAdjustment` | `OrderItemRateAdjustment` |
| Rate card entries | `QuoteLineRateCardEntry` | `OrderItemRateCardEntry` |
| Usage resource policy | `QuotLineItmUsageRsrcPlcy` | `OrderItemUsageRsrcPlcy` |
| Usage resource grant | `QuotLineItmUseRsrcGrant` | `OrderItemUsageRsrcGrant` |

Quote, Order and Asset records are created at runtime through the business APIs, not loaded as reference data.

### 4.6 DRO — Dynamic Revenue Orchestration

| Design-time object | Key fields |
|---|---|
| `FulfillmentStepDefinitionGroup` | `Name` |
| `FulfillmentStepDefinition` | `Name`, `StepDefinitionGroupId`, `AssignedToId` (User/Group), `IntegrationDefinitionNameId` |
| `FulfillmentStepDependencyDef` | `FulfillmentStepDefinitionId`, `DependsOnStepDefinitionId` |
| `ProductFulfillmentDecompRule` | `Name`, `SourceProductId`, `DestinationProductId`, `SourceProductClassificationId` |
| `ProductDecompEnrichmentRule` | `DecompositionRuleId`, `SourceAttributeDefinitionId`, `DestinationAttributeDefinitionId`, `ListMappingGroupId` → `ValTfrmGrp` |
| `ProductFulfillmentScenario` | `ProductId`, `ProductClassificationId`, `FulfillmentStepDefnGroupId` |
| `FulfillmentFalloutRule` | `FalloutQueueId` → Group, `IntegrationDefinitionId` |
| `FulfillmentStepJeopardyRule` | `IntegrationDefinition.DeveloperName` |
| `FulfillmentTaskAssignmentRule` | `ConditionId`, `DestinationId`, `SourceId` (polymorphic) |
| `FulfillmentWorkspace` / `FulfillmentWorkspaceItem` | `Name` / `FulfillmentWorkspaceId`, `FulfillmentStepDefinitionGroupId` |
| `ValTfrmGrp` / `ValTfrm` | `Name` / `ValueTransformGroupId`, `InputPicklistValueId`, `OutputPicklistValueId` |

| Runtime object | Key fields |
|---|---|
| `FulfillmentPlan` | Plan instance for an order |
| `FulfillmentStep` | `FulfillmentPlanId`, `FulfillmentStepDefinitionId`, `AssignedToId` |
| `FulfillmentStepDependency` | `FulfillmentStepId`, `DependsOnStepId`, `DependencyDefinitionId` |
| `SalesTransactionFulfillReq` | `PlanId`, `PreviousRequestId` (self) |
| `AssetFulfillmentDecomp` | `FulfillmentSourceAssetId`, `FulfillmentTargetAssetId` → `FulfillmentAsset` |
| `FulfillmentAssetRelationship` | `AssociatedFulfillmentAssetId` |

Also runtime: `FulfillmentStepSource`, `SalesTrxnDeleteEvent`, `FulfillmentAsset`, `FulfillmentAssetAttribute`, `FulfillmentLineAttribute`, `FulfillmentLineRel`, `FulfillmentLineSourceRel`, `ProdtDecompEnrchVarMap`. Design-time objects are configuration data; runtime objects are created during order processing. `User` and `Group` are only referenced (assignees, fallout queues).

### 4.7 Usage

| Design-time object | Key fields |
|---|---|
| `UsageResource` | `Code` (unique), `UsageDefinitionProductId` → `Product2`, `TokenResourceId` (self), `UnitOfMeasureClassId` |
| `ProductUsageResource` (PUR) | `ProductId`, `UsageResourceId`, `TokenResourceId`, `Status`, `EffectiveStartDate`, `EffectiveEndDate` |
| `ProductUsageResourcePolicy` (PURP) | `ProductUsageResourceId`, `RatingFrequencyPolicyId`, `UsageAggregationPolicyId` (→ `UsageResourceBillingPolicy`), `UsageCommitmentPolicyId`, `UsageOveragePolicyId`; **no `Status`** |
| `ProductUsageGrant` (PUG) | `ProductUsageResourceId`, `UsageResourceId`, `ProductSellingModelId`, `RenewalPolicyId` → `UsageGrantRenewalPolicy`, `RolloverPolicyId` → `UsageGrantRolloverPolicy`, `UnitOfMeasureClassId`, `UnitOfMeasureId`, `DrawdownOrder` |
| `UsageResourceBillingPolicy` | `Code` |
| `UsageCommitmentPolicy` | `Name`, `CommitmentRate` |
| `UsageOveragePolicy` | `Name`, `OverageChargeable` |
| `UsageGrantRenewalPolicy` / `UsageGrantRolloverPolicy` | `Code`, `UsageSummaryId` / `Code` |
| `UsagePrdGrantBindingPolicy` | `Name`, `Product2Id` |
| `UsageResourcePolicy` | Resource-level defaults (four policy lookups, section 2) |
| `UnitOfMeasure` / `UnitOfMeasureClass` | `UnitCode` (unique) / `Code` (unique), `BaseUnitOfMeasureId`, `DefaultUnitOfMeasureId` |

| Runtime object | Key fields / meaning |
|---|---|
| `TransactionJournal` | One usage event; `UsageResourceId`, `Status` (`Pending` until a summary absorbs it) |
| `UsageSummary` | Aggregated usage per resource; `UsageResourceId`, `Status` |
| `UsageRatableSummary` | `TierQuantity`, `OverageQuantity` |
| `TransactionUsageEntitlement` (TUE) | Written by the platform at order activation / assetization. `AssetId`, `ProductId` (`createable: false`), `UsageResourceId`, `OrderItemId`, `EntitlementUomId`, `UsageGrantRefreshPolicyId`, `UsageGrantRolloverPolicyId`, `EffectiveStartDateTime`/`EffectiveEndDateTime`, `EntitlementProcessingStatus` (`PENDING`/`PROCESSED`; **no `Status` field**) |
| `UsageEntitlementBucket` / `UsageEntitlementEntry` | Balances / entries: `BucketBalanceUomId`, `ParentId` / `ParentEntitlementBucketId`, `TransactionUsageEntitlementId`, `TransactionalBucketId` |
| `UsageCmtAssetRelatedObj` | Commitment → anchor junction: `AssetId` = commitment asset, `RelatedObjectId` = anchor asset, `UsageResourceId` |
| `UsageRatableSumCmtAssetRt` | `UsageResourceId` |

Also runtime: `UsageEntitlementAccount`, `UsageBillingPeriodItem`, `AssetRateAdjustment` (created when a commitment is sold).

### 4.8 Billing

| Area | Object | Key fields |
|---|---|---|
| Policy | `BillingPolicy` | `Name`, `DefaultBillingTreatmentId` |
| | `BillingTreatment` / `BillingTreatmentItem` | `BillingPolicyId`, `LegalEntityId` / `BillingTreatmentId` |
| Schedule | `BillingSchedule` | `ReferenceEntityId` → Order, `AccountId`, `BillingTreatmentItemId`, `TaxTreatmentId`, `OriginalBillingScheduleId` |
| | `BillingScheduleGroup` | `BillingArrangementId`, `BillingTreatmentId`, `LegalEntityId`, `PaymentTermId`, `TaxTreatmentId` |
| | `BillingPeriodItem` | `BillingScheduleGroupId`, `InvoiceBatchRunId`, `InvoiceId`, `InvoiceLineId` |
| | `BillingMilestonePlan` / `BillingMilestonePlanItem` | `BillingTreatmentId` / `BillingScheduleGroupId`, `ReferenceItemId` → BillingSchedule |
| | `BsgRelationship` | `AssociatedBsgId` |
| Invoice | `Invoice` | `AccountId`, `BillingAccountId`, `LegalEntityId`, `PaymentTermId`, `InvoiceBatchRunId`, `ReferenceEntityId` (Order; also Opportunity/Quote since 262) |
| | `InvoiceLine` | `InvoiceId`, `Product2Id`, `BillingScheduleId`, `BillingScheduleGroupId`, `LegalEntityId`, `TaxTreatmentId` |
| | `InvoiceLineRelationship` | `AssociatedInvoiceLineId`, `UsageProductBillSchdGrpId` |
| | `InvoiceBatchRun` | `BillingBatchSchedulerId` |
| Credit/debit | `CreditMemo` | `AccountId`, `LegalEntityId`, `ReferenceEntityId` → Order |
| | `CreditMemoInvApplication` | `CreditMemoId`, `CreditMemoLineId` |
| | `CreditMemoLineInvoiceLine` | `CreditMemoLineId`, `TaxTreatmentId`, `LegalEntityId` |
| | `DebitMemoLine` | `LegalEntityId`, `TaxTreatmentId`, `BillingAddressId` |
| Payment | `Payment` | `AccountId` |
| | `PaymentSchedule` / `PaymentScheduleItem` | `CollectionPlanItemId`, `ReferenceEntityId` / `PaymentBatchRunId`, `PaymentId` |
| | `PaymentSchedulePolicy` | `DefaultTreatmentId` |
| | `PaymentTerm` / `PaymentTermItem` | `Name` / `PaymentTermId`, `Type` |
| Tax | `TaxPolicy` | `DefaultTaxTreatmentId`, `LegalEntityId`, `GeneralLedgerAcctAsgntRuleId` |
| | `TaxTreatment` | `LegalEntityId`, `TaxEngineId`, `TaxPolicyId` |
| | `TaxEngine` / `TaxEngineProvider` | `TaxEngineName`, `TaxEngineProviderId`, `MerchantCredentialId`, `Status` / `DeveloperName` |
| GL | `LegalEntyAccountingPeriod` | `LegalEntityId`, `AccountingPeriodId` (`AccountingPeriod`: `Name`, `FinancialYear`) |
| | `GeneralLedgerAccount` | `AccountingCode`, `LegalEntityId` |
| | `GeneralLedgerAcctAsgntRule` | `CreditGeneralLedgerAccountId`, `DebitGeneralLedgerAccountId`, `LegalEntityId` |
| | `GeneralLedgerJrnlEntryRule` | `CreditGeneralLedgerAccountId`, `DebitGeneralLedgerAccountId`, `GeneralLedgerAcctAsgntRuleId` |
| | `GeneralLdgrAcctPrdSummary` | `LegalEntityAccountingPeriodId` |
| Batch | `BillingBatchScheduler` / `BillingBatchFilterCriteria` | `RunCriteriaId` / `BatchCriteriaId` |
| Accounts | `BillingAccount` (distinct from Account) | `AccountId`, `PaymentTermId`; junction `AccountBillingAccount` |

Without key fields in the source: `BillingArrangement`(`Line`), `InvoiceLineTax`, `InvoiceAddressGroup`, `InvoiceDocument`, `InvoiceBatchRunCriteria`, `InvoiceBatchRunRecovery`, `InvBatchDraftToPostedRun`, `CreditMemoLine`, `CreditMemoLineTax`, `CreditMemoAddressGroup`, `DebitMemo`, `DebitMemoLineTax`, `DebitMemoAddress`, `PaymentLineInvoice`(`Line`), `PaymentBatchRun`, `PaymentScheduleTreatment`(`Dtl`), `PymtSchdDistributionMethod`, `PaymentRetryRule`(`Set`), `Refund`, `RefundLinePayment`, `TaxRate`, `TaxEngineInteractionLog`, `CollectionPlan`(`Item`), `RevenueTransactionErrorLog`. License-gated: `Dispute`/`DisputeItem`, `SequencePolicy`/`SeqPolicySelectionCondition`/`SequenceGapReconciliation`.

### 4.9 Approvals

| Object | Key fields / notes |
|---|---|
| `ApprovalSubmission` | `RelatedRecordId`: polymorphic, can point to the approved record or another `ApprovalSubmission` |
| `ApprovalAlertContentDef` | `Name`, `EmailTemplateId` |
| `EmailTemplate` | Referenced only |

Approval email templates are `EmailTemplatePage` flexipages: they **cannot be deployed with the Metadata API** and are created at runtime through the REST API. `ApprovalAlertContentDef` rows can only be loaded once those templates exist.

## 5. Lifecycles and status flows

### Quote to cash

```
Product2 + PricebookEntry
  → Quote → QuoteLineItem
  → (place order) Order → OrderItem            Order.QuoteId, OrderItem.QuoteLineItemId
  → (assetize) Asset → AssetStatePeriod, AssetAction → AssetActionSource (OrderItemId)
  → (fulfill) FulfillmentOrder → FulfillmentOrderLineItem; FulfillmentPlan → FulfillmentStep
  → (bill) BillingSchedule → BillingScheduleGroup
  → (invoice) Invoice → InvoiceLine → InvoiceLineTax
  → (pay) Payment → PaymentLineInvoice
```

Amendments chain through `OrderItem.OriginalOrderItemId`; asset changes are recorded as `AssetAction` (New/Amend/Renew/Cancel).

### Status and activation

| Object(s) | Flow stated in source |
|---|---|
| `BillingTreatmentItem`, `BillingTreatment`, `BillingPolicy` | Created Draft → activate treatment items → activate treatments and policies |
| `UnitOfMeasureClass`, `UsageResource` | Loaded, then activated in a second pass |
| PUR, PUG | Loaded, then activated (PUR: Draft → Active). PURP has no status; its parent PUR gates it |
| TUE | Written by the platform at order activation; `EntitlementProcessingStatus` `PENDING` → `PROCESSED` |
| `TransactionJournal` | `Pending` until a `UsageSummary` absorbs it |
| `UsageSummary` | Open period → `RatableSummaryComplete` / `LiableSummaryComplete`; a closed summary **never reopens** |

### Usage recording and rating (live-verified behaviour)

1. **Record usage against the anchor asset.** A commitment is a rate modifier, not a consumption target: journals uploaded against a commitment asset stay `Pending` forever.
2. **Selling a commitment takes three steps:** sell the anchor asset; sell the commitment asset (its own product); create `UsageCmtAssetRelatedObj` (`AssetId` = commitment, `RelatedObjectId` = anchor). Without step 3 the commitment exists, activates, and does nothing.
3. **Drawdown order:** commitment first, then grant, then overage. The commitment bucket decrements by the **discounted** quantity (raw 27,777.78 at 10% off draws 25,000); the anchor grant by the **raw** quantity (an included allowance is never discounted); overage is rated per `UsageCommitmentPolicy.CommitmentRate`.
4. **`CommitmentRate`:** `Lowest Commitment Rate` keeps the commitment discount into overage; `Bounded Object Rate` reverts to the standard anchor rate. Identical up to the boundary. It is a design-time switch that no runtime object snapshots: read the policy to know which applied.
5. **Entitlement bucket tree:** 3 levels deep, and **no bucket has a null `ParentId`**: the wallet's parent is a grant-binding target (`1Gv` prefix), not a bucket. Identify roots by set membership, never by `ParentId = null`.
6. **Orchestration needs several passes** to settle; stopping after one looks like zero.

## 6. Load order and teardown

Parent before child. Business transactions (Quote, Order, Asset), DRO runtime and usage runtime objects are produced by the platform, not loaded.

1. `Account`, `Contact`.
2. **PCM, the root of all other loads:** attributes (`AttributePicklist` → values → `AttributeDefinition` → categories) → classifications → `Product2` → selling models (`ProrationPolicy`, PSM → PSMO) → bundles (`ProductRelationshipType` → `ProductComponentGroup` → `ProductRelatedComponent`) → catalogs/categories → qualifications. `UnitOfMeasure` / `UnitOfMeasureClass` must exist before attributes and usage objects reference them.
3. Then, each depending only on PCM unless noted:

| Branch | Order | Extra prerequisites |
|---|---|---|
| Pricing | `Pricebook2` → `PricebookEntry` → `PriceAdjustmentSchedule` → tiers / attribute / bundle adjustments, derived prices | `Product2`, PSM, `ProrationPolicy`, `AttributeDefinition` |
| Billing | `LegalEntity`, `PaymentTerm`, `BillingPolicy` / `BillingTreatment` / `BillingTreatmentItem` (Draft, then activate items → treatments/policies), `UsageResourceBillingPolicy` | |
| Accounting | `GeneralLedgerAccount` → `GeneralLedgerAcctAsgntRule` → `GeneralLedgerJrnlEntryRule` | `LegalEntity` |
| Tax | `TaxEngine` → `TaxPolicy` / `TaxTreatment` | Tax engine adapter metadata deployed first; `LegalEntity` |
| Usage | UoM/UoM class → `UsageResource` + policies → PUR → PURP → PUG → activate UoM class and `UsageResource` → activate PUR/PUG | `UsageResourceBillingPolicy` (billing) |
| Rates | `RateCard` → `RateCardEntry` → `RateAdjustmentByTier` / `ByAttribute` → `PriceBookRateCard` | **Must follow Usage** (PURs, `UsageResource`); `Pricebook2` |
| DRO design time | step definition groups → step definitions → dependency defs; decomposition rules → enrichment rules; scenarios; workspaces | `User` / `Group` for assignees and queues |
| CLM | `ObjectStateDefinition` and transitions | |
| Approvals | `ApprovalAlertContentDef` | `EmailTemplate` created via REST first |
| Configurator | `TransactionProcessingType` | standalone |

4. Back-fill `Product2.BillingPolicyId` / `TaxPolicyId` once those policies exist.

Policies and treatments reference each other (`BillingPolicy.DefaultBillingTreatmentId` ↔ `BillingTreatment.BillingPolicyId`, `TaxPolicy.DefaultTaxTreatmentId` ↔ `TaxTreatment.TaxPolicyId`), hence multi-pass loads: set the default treatment once the treatment exists. `TaxPolicy.GeneralLedgerAcctAsgntRuleId` needs the GL rule first.

**Natural keys for upsert:** `Product2.StockKeepingUnit`, `UsageResource.Code`, `UnitOfMeasure.UnitCode`, `UnitOfMeasureClass.Code` are unique. A PUG key must include `ProductUsageResourceId`: the same grant values recur under different PURs.

**Teardown:**

1. Reverse the load order; delete rates before PURs (rates reference them).
2. Design-time rating/rates records that live entitlements reference cannot be deleted, so delete-and-reload fails on an org with live usage assets. Add new products incrementally instead.
3. The usage runtime graph has **circular delete constraints** (`UsageSummary` ↔ `UsageRatableSummary` reference each other, entries and journals hold summaries, buckets self-nest). No fixed order works: loop over every object each round and stop when a full round deletes nothing.
4. Deleting usage records does **not** reopen a closed period: period state on `UsageEntitlementAccount` and the buckets survives. Re-testing the same period needs the account's usage state and assets rebuilt; deleting usage only frees a different period.

## 7. Gotchas

1. **Commitment PURP takes only a `UsageCommitmentPolicy` (platform-enforced).** When the product's `UsageModelType` is `Commit`, `CommitmentQuantity` or `CommitmentSpend`, setting `RatingFrequencyPolicyId` or `UsageAggregationPolicyId` fails with `INVALID_INPUT: "This field must be empty when the product associated with the product usage resource is one of the commitment usage model types.: [RatingFrequencyPolicyId]"` (same message for `[UsageAggregationPolicyId]`).
2. **Only an Anchor product's PURP may carry a `UsageOveragePolicy`.** On a Pack product it fails with *"We can't save the pack usage model type record. Change the product usage model type from Pack to another valid option and try again."*; a Commit product's PURP rejects it too (gotcha 1). Verified on 264.
3. **Overage lookup by product + resource returns nothing for Pack/Commit products** (they have no overage row), and resources are shared across products. Safe resolution: exact product+resource row; else the resource-level policy only if every row for that resource agrees; else null.
4. **Filter PURP through `ProductUsageResource.Status = 'Active'`.** PURP has no status; after a reload, Draft PURs can carry PURP children that overlap the Active row and create false conflicts.
5. **`Status = 'Active'` gives one *effective* PUR, not one row.** Several Active PURs can exist per product+resource when `EffectiveStartDate`/`EffectiveEndDate` do not overlap. Match the PUR period against the TUE's `EffectiveStartDateTime`/`EffectiveEndDateTime`, not today's date.
6. **`UsageRatableSummary.OverageQuantity` mirrors `TierQuantity` on ordinary rows.** It means beyond the included allowance, not beyond the commitment.
7. **Silent zeros (no error, rated summary reads 0):**
   1. Usage recorded *after* its period was orchestrated stays `Pending` forever (closed summaries never reopen). Record before orchestrating.
   2. The first orchestration of an account closes every past period empty, and there is one attempt per account. Consume first, then orchestrate.
   3. Usage booked into the *current* period stays `InProgress` with buckets untouched (looks like full discount, no drawdown). Book into a past, completed period.
   4. Re-recording into a period after deleting usage reproduces case 1 (section 6, teardown 4).
   5. Where commitment rates resolve through a decision table, a commitment sold after the table's last refresh can rate at the undiscounted anchor rate. Selling a commitment creates `AssetRateAdjustment` rows; check `DecisionTable.LastSyncDate` is later than the newest `AssetRateAdjustment.CreatedDate`, refresh otherwise.
8. **TUE is transactional:** the platform writes it; `ProductId` is not createable; use `EntitlementProcessingStatus`, not `Status`.
9. **`DrawdownOrder` is not on PURP** in 264: `ProductUsageGrant` at design time, the `*UsageRsrcPlcy` line objects at runtime.
10. **`UsageAggregationPolicyId` points to `UsageResourceBillingPolicy`**; there is no `UsageAggregationPolicy` SObject.
11. **`RateCard` has no `Status`**; filter on `RateCardEntry.Status`.
12. **Approval email templates** (`EmailTemplatePage`) cannot go through the Metadata API; create them via REST before loading `ApprovalAlertContentDef`.
13. **Schema introspection:** `EntityDefinition` does not support `queryMore()`; querying every object at once fails with `EXCEEDED_ID_LIMIT`. Query an explicit object list.
14. **Feature/license gating:** some RLM objects are absent from orgs without the matching feature; `Dispute`/`DisputeItem` and the `SequencePolicy` family require a specific license.
