# Functional Specification: Menu Sorting

## Metadata

| Field | Value |
|-------|-------|
| **Author** | Claude AI |
| **Created** | 2026-01-02 |
| **Version** | 1.0 |
| **Status** | Approved |
| **Approved by** | - |

---

## 1. Overview

### 1.1 Purpose
Enable users to define the display order of products in the menu using drag-and-drop functionality. The defined order will be applied in all places in the application where the product list is displayed.

### 1.2 Business Context
In food service establishments, the order of products in the menu matters - popular/promoted products should be displayed first. Currently, products are displayed in the order of creation, which does not meet business needs.

### 1.3 Scope
**In scope:**
- Adding `sort_order` field to the Product model
- Implementing drag-and-drop on the product list in MenuPage
- Applying sorting in all views displaying products
- API endpoint for updating product order

**Out of scope:**
- Sorting ingredients
- Sorting product variants
- Grouping products into categories

---

## 2. User Stories

### US-001: Change Product Order
**As a** food establishment owner
**I want** to drag products on the menu list to change their order
**So that** the most popular products are displayed first

**Acceptance Criteria:**
- [ ] I can drag a product up or down the list
- [ ] The order is saved automatically after dragging
- [ ] The new order is preserved after page refresh
- [ ] I see visual indication during dragging

**Priority:** High

---

### US-002: Consistent Order Across Application
**As a** system user
**I want** to see products in the same order in all views
**So that** I can find products more easily

**Acceptance Criteria:**
- [ ] Product list in MenuPage is sorted by `sort_order`
- [ ] Product list in DailyOperationsPage is sorted by `sort_order`
- [ ] Each new product receives the highest `sort_order` (appears at the end of the list)

**Priority:** High

---

## 3. Functional Requirements

### 3.1 Drag-and-drop Sorting
**ID:** FR-001
**Description:** The product list in the "Products" tab on the Menu page allows changing the order using drag-and-drop. After dragging a product to a new position, the order is automatically saved to the database.
**Priority:** High

### 3.2 Order Persistence
**ID:** FR-002
**Description:** Product order is stored in the `sort_order` field (INTEGER) in the `products` table. Lower values mean higher position on the list.
**Priority:** High

### 3.3 Default Order for New Products
**ID:** FR-003
**Description:** A newly created product receives a `sort_order` value equal to MAX(sort_order) + 1, adding it to the end of the list.
**Priority:** Medium

### 3.4 Global Sort Order
**ID:** FR-004
**Description:** All API endpoints returning product lists sort by `sort_order` ascending by default.
**Priority:** High

---

## 4. User Interface

### 4.1 User Flow
```
[MenuPage - Products tab] -> [Click and hold product] -> [Drag to new position] -> [Drop] -> [Auto save]
```

### 4.2 UI Elements
| Element | Type | Description |
|---------|------|-------------|
| Drag handle | Icon (GripVertical) | Icon on the left side of product card indicating drag capability |
| Drop target indicator | Border/Shadow | Highlighting where product will be dropped |
| Product card | Draggable card | Entire product card is the draggable element |

### 4.3 Visual States
- **Normal**: Drag handle icon in gray
- **Hover on handle**: Cursor changes to "grab", icon highlighted
- **During drag**: Card with shadow, opacity 0.8
- **Drop target**: Blue line indicating target position

---

## 5. Edge Cases

### 5.1 Concurrent Editing
**Scenario:** Two users change the order at the same time
**Expected behavior:** Last save wins (optimistic update). No locking.

### 5.2 Product Deletion
**Scenario:** Product in the middle of the list is deleted
**Expected behavior:** Gap in `sort_order` does not affect sorting (ORDER BY still works correctly)

### 5.3 Product Filtering
**Scenario:** Product list is filtered (e.g., only active products)
**Expected behavior:** Drag-and-drop works only on visible products, order is updated correctly

---

## 6. Error Handling

| Error | Message (Polish) | Action |
|-------|------------------|--------|
| Order save error | "Nie udało się zapisać kolejności. Spróbuj ponownie." | Error toast, restore previous order |
| Network error | "Błąd połączenia. Sprawdź połączenie z internetem." | Error toast, restore previous order |

---

## 7. Non-Functional Requirements

### 7.1 Performance
- Order update should be executed in a single database query (bulk update)
- API response in < 500ms

### 7.2 UX
- Drag-and-drop animation should be smooth (60 FPS)
- Visual feedback immediately after starting to drag

---

## 8. Dependencies

### 8.1 Required Features
- Existing product list (MenuPage)
- Existing Product model

### 8.2 Related Data Models
- `Product` - adding `sort_order` field

---

## 9. Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Order save time | < 500ms | API monitoring |
| Animation smoothness | 60 FPS | Developer tools |

---

## 10. Open Questions

- [x] Should sorting also apply to ingredients? **Answer: No, only products**
- [ ] Do we want to show position number next to the product?

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-02 | Claude AI | Initial version |
