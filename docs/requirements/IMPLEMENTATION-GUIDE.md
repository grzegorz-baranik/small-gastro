# Daily Inventory Management - Implementation Guide

**Quick Reference for Implementation Agents**

---

## Document Overview

| Document | Location | Purpose |
|----------|----------|---------|
| Full Requirements | `docs/requirements/daily-inventory-management-requirements.md` | Complete specification with all details |
| Feature Files | `docs/requirements/features/*.feature` | Cucumber BDD scenarios for TDD |
| This Guide | `docs/requirements/IMPLEMENTATION-GUIDE.md` | Quick reference and priorities |

---

## Implementation Priority Order

### Phase 1: Foundation (Must complete first)
1. **Database Schema** - Create/update migrations for new entities
2. **Ingredient Management** - CRUD with unit_type (weight/count)
3. **Product Management** - Products, variants, recipes with primary ingredient

### Phase 2: Core Daily Operations
4. **Day Opening** - Open day with inventory counts, pre-fill from previous
5. **Day Closing** - Close day with calculations, discrepancy alerts
6. **Dashboard** - Central hub showing status and quick actions

### Phase 3: Mid-Day Events
7. **Record Delivery** - Add deliveries with quantity and price
8. **Storage Transfer** - Transfer between storage and shop
9. **Record Spoilage** - Track waste with reasons

### Phase 4: Supporting Features
10. **Storage Inventory** - Weekly storage counts
11. **Reports** - Daily summary, monthly trends, usage, spoilage
12. **Excel Export** - Export functionality for all reports

---

## Key Technical Decisions

### Data Model Changes

**New Tables:**
- `product_variants` - Separate from products, each has price and recipe
- `product_ingredients` - Junction table with `is_primary` flag
- `deliveries` - Track quantity and price per ingredient
- `storage_transfers` - Track movement from storage to shop
- `spoilage` - Track waste with reason enum
- `storage_inventory` - Current storage levels
- `calculated_sales` - Derived sales per day

**Modified Tables:**
- `daily_records` - Add `total_income_pln`, `total_delivery_cost_pln`
- `inventory_snapshots` - Add `location` enum (shop/storage)

### API Endpoints Needed

```
# Day Operations
POST   /api/v1/daily-records/open          # Open a day
POST   /api/v1/daily-records/{id}/close    # Close a day
GET    /api/v1/daily-records/current       # Get current open day
PATCH  /api/v1/daily-records/{id}          # Edit closed day

# Mid-Day Events
POST   /api/v1/deliveries                  # Record delivery
POST   /api/v1/storage-transfers           # Record transfer
POST   /api/v1/spoilage                    # Record spoilage

# Products & Recipes
GET    /api/v1/products                    # List with variants
POST   /api/v1/products                    # Create product
POST   /api/v1/product-variants/{id}/recipe  # Set recipe

# Storage
GET    /api/v1/storage-inventory           # Current storage levels
POST   /api/v1/storage-inventory/count     # Submit storage count

# Reports
GET    /api/v1/reports/daily/{date}        # Daily summary
GET    /api/v1/reports/monthly/{year}/{month}  # Monthly trends
GET    /api/v1/reports/ingredients         # Ingredient usage
GET    /api/v1/reports/spoilage            # Spoilage analysis
GET    /api/v1/reports/export              # Excel export
```

### Core Calculation (Python pseudo-code)

```python
def calculate_day_results(daily_record):
    for ingredient in active_ingredients:
        # Get all events for the day
        opening = get_opening_snapshot(daily_record, ingredient)
        deliveries = sum(get_deliveries(daily_record, ingredient))
        transfers = sum(get_transfers(daily_record, ingredient))
        spoilage = sum(get_spoilage(daily_record, ingredient))
        closing = get_closing_snapshot(daily_record, ingredient)

        # Calculate usage
        usage = opening + deliveries + transfers - spoilage - closing

        # Store for later
        usages[ingredient] = usage

    # Derive products sold from primary ingredients
    for variant in active_product_variants:
        primary = get_primary_ingredient(variant)
        recipe_amount = get_recipe_amount(variant, primary)
        quantity_sold = usages[primary] / recipe_amount
        revenue = quantity_sold * variant.price

        save_calculated_sale(daily_record, variant, quantity_sold, revenue)

    # Calculate discrepancies
    for ingredient in usages:
        expected = calculate_expected_usage(ingredient, calculated_sales)
        actual = usages[ingredient]
        discrepancy_pct = abs((actual - expected) / expected) * 100

        if discrepancy_pct > 10:
            add_alert(ingredient, discrepancy_pct, 'critical')
        elif discrepancy_pct > 5:
            add_alert(ingredient, discrepancy_pct, 'concerning')
```

---

## UI Components Needed

### React Components

```
src/
  components/
    daily-operations/
      DayStatusBadge.tsx       # Shows OPEN/CLOSED status
      OpenDayForm.tsx          # Form with ingredient counts
      CloseDayForm.tsx         # Form with closing counts + calculations
      DiscrepancyAlert.tsx     # Yellow/red warning display
      QuickActionButton.tsx    # Dashboard action buttons

    mid-day/
      DeliveryForm.tsx         # Multi-item delivery entry
      StorageTransferForm.tsx  # Transfer entry
      SpoilageForm.tsx         # Spoilage with reason dropdown

    products/
      ProductList.tsx          # List with variants
      ProductForm.tsx          # Create/edit product
      VariantForm.tsx          # Create/edit variant
      RecipeEditor.tsx         # Assign ingredients to variant

    reports/
      DailySummary.tsx         # Single day view
      MonthlyTrends.tsx        # Charts and tables
      IngredientUsage.tsx      # Usage over time
      SpoilageReport.tsx       # Waste analysis
      ExportButton.tsx         # Excel download

    common/
      IngredientInput.tsx      # Number input with unit label
      DatePicker.tsx           # Date selection
      DataTable.tsx            # Reusable table component

  pages/
    DashboardPage.tsx          # Central hub
    DayOperationsPage.tsx      # Open/Close day
    ProductsPage.tsx           # Product management
    ReportsPage.tsx            # Report selection
```

---

## Feature File Summary

| Feature File | Scenarios | Focus |
|--------------|-----------|-------|
| `day-opening.feature` | 8 | Opening workflow, validation, pre-fill |
| `day-closing.feature` | 10 | Closing, calculations, discrepancies |
| `delivery.feature` | 9 | Delivery recording, validation |
| `storage-transfer.feature` | 8 | Transfer workflow, warnings |
| `spoilage.feature` | 9 | Spoilage with reasons |
| `product-management.feature` | 13 | Products, variants, recipes |
| `storage-inventory.feature` | 8 | Weekly storage counts |
| `reports.feature` | 16 | All report types, export |
| `dashboard.feature` | 10 | Dashboard states, navigation |

**Total: 91 scenarios**

---

## Key Constraints

1. **Polish Language** - All UI text must be in Polish
2. **PLN Currency** - All money values in Polish Zloty
3. **Owner Only** - No employee access to system
4. **Desktop Primary** - Optimize for desktop, mobile secondary
5. **5-10 Min Target** - Daily entry must be fast
6. **1 Year History** - Keep data for 12 months

---

## Open Questions Requiring Decision

| # | Question | Suggested Answer | Impact |
|---|----------|------------------|--------|
| 1 | Fractional product sales (e.g., 23.5)? | Round to integer | Display |
| 2 | Negative storage after transfer? | Allow with warning | Data integrity |
| 3 | Which ingredient drives sales calculation? | Primary only | Calculation accuracy |
| 4 | Deleted ingredients in history? | Soft delete only | Data integrity |
| 5 | No primary ingredient assigned? | Block day closing | System stability |

---

## Testing Approach

1. **Unit Tests** - For all calculation functions
2. **Integration Tests** - For API endpoints
3. **E2E Tests** - Based on Cucumber feature files
4. **Manual Testing** - UI/UX validation with real workflow

---

## Definition of Done

A feature is complete when:
- [ ] All related Cucumber scenarios pass
- [ ] API endpoints return correct data
- [ ] UI matches wireframe specifications
- [ ] Polish translations are complete
- [ ] Performance targets are met (< 2s page load)
- [ ] Works on Chrome, Firefox, Edge
- [ ] Code reviewed and merged

---

**Ready for implementation. Start with Phase 1: Foundation.**
