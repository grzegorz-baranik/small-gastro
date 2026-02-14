# language: en
# encoding: utf-8

@sales_tracking_hybrid
Feature: Sales Tracking Hybrid
  As a kebab shop owner
  I want to record sales as they happen and compare them with inventory-derived calculations
  So that I can identify discrepancies, improve portion accuracy, and gain insights into my business

  Background:
    Given the database is empty
    And I am logged in as "staff"
    And the following product categories exist:
      | name     | sort_order |
      | Kebaby   | 1          |
      | Burgery  | 2          |
      | Napoje   | 3          |
    And the following products with variants exist:
      | product | category | variant | price_pln | primary_ingredient | quantity_per_unit |
      | Kebab   | Kebaby   | Maly    | 18.00     | Mieso wolowe       | 0.100             |
      | Kebab   | Kebaby   | Sredni  | 22.00     | Mieso wolowe       | 0.150             |
      | Kebab   | Kebaby   | Duzy    | 28.00     | Mieso wolowe       | 0.200             |
      | Burger  | Burgery  | Classic | 25.00     | Mieso mielone      | 0.150             |
      | Cola    | Napoje   | 0.5L    | 6.00      | Cola 0.5L          | 1                 |

  # ============================================
  # SALES RECORDING - HAPPY PATH
  # ============================================

  @happy-path @smoke
  Scenario: Record a single sale
    Given a day is open for today
    When I navigate to the sales entry page
    And I tap on "Kebab Duzy" product button
    Then a sale should be recorded for "Kebab Duzy"
    And the running total should show "28.00 PLN"
    And the recent sales list should show 1 item

  @happy-path
  Scenario: Record multiple sales
    Given a day is open for today
    When I navigate to the sales entry page
    And I tap on "Kebab Duzy" product button
    And I tap on "Kebab Duzy" product button
    And I tap on "Burger Classic" product button
    Then the running total should show "81.00 PLN"
    And the recent sales list should show 3 items
    And "Kebab Duzy" should show count "(2)" on its button

  @happy-path
  Scenario: Sales are attributed to current shift
    Given a day is open for today
    And employee "Jan Kowalski" has a shift from "10:00" to "18:00"
    And the current time is "14:00"
    When I record a sale for "Kebab Maly"
    Then the sale should be attributed to the shift of "Jan Kowalski"

  @happy-path
  Scenario: Switch between product categories
    Given a day is open for today
    When I navigate to the sales entry page
    And I tap on the "Burgery" category tab
    Then I should see "Burger Classic" product button
    And I should not see "Kebab" products
    When I tap on the "Napoje" category tab
    Then I should see "Cola 0.5L" product button

  # ============================================
  # VOIDING SALES
  # ============================================

  @happy-path
  Scenario: Void a recorded sale with reason
    Given a day is open for today
    And I have recorded a sale for "Kebab Duzy"
    When I tap on the sale in the recent sales list
    And I select void reason "Pomylka przy rejestracji"
    And I confirm the void
    Then the sale should be marked as voided
    And the running total should show "0.00 PLN"
    And the sale should still appear in history with strikethrough

  @happy-path
  Scenario: Void a sale with custom notes
    Given a day is open for today
    And I have recorded a sale for "Burger Classic"
    When I void the sale with reason "Zwrot klientowi" and notes "Burger byl zimny"
    Then the void reason should be "customer_refund"
    And the void notes should be "Burger byl zimny"

  @error-handling
  Scenario: Cannot void a sale from a closed day
    Given a day was opened and closed yesterday with 1 sale
    When I try to void a sale from yesterday
    Then I should see error message "Nie mozna anulowac sprzedazy z zamknietego dnia"
    And the sale should remain active

  @error-handling
  Scenario: Cannot void an already voided sale
    Given a day is open for today
    And I have recorded and voided a sale for "Kebab Maly"
    When I try to void the same sale again
    Then I should see error message "Sprzedaz nie istnieje lub zostala juz anulowana"

  # ============================================
  # RECONCILIATION
  # ============================================

  @happy-path @smoke
  Scenario: View reconciliation during day close
    Given a day is open for today
    And I have recorded the following sales:
      | product       | quantity |
      | Kebab Duzy    | 10       |
      | Burger Classic| 5        |
    And the calculated sales from inventory show:
      | product       | quantity |
      | Kebab Duzy    | 12       |
      | Burger Classic| 5        |
    When I start the day close wizard
    And I proceed to the reconciliation step
    Then I should see recorded total "405.00 PLN"
    And I should see calculated total "461.00 PLN"
    And I should see discrepancy "-56.00 PLN"
    And I should see discrepancy percentage "12.1%"

  @happy-path
  Scenario: Reconciliation shows missing sales suggestions
    Given a day is open for today
    And I have recorded 10 sales of "Kebab Duzy"
    And the inventory suggests 12 "Kebab Duzy" were made
    When I view the reconciliation report
    Then I should see suggestion "Mozliwe brakujace: 2x Kebab Duzy (56 PLN)"
    And the suggestion should mention ingredient usage

  @happy-path
  Scenario: Reconciliation with no discrepancy
    Given a day is open for today
    And I have recorded the following sales:
      | product       | quantity |
      | Kebab Sredni  | 7        |
    And the calculated sales from inventory match exactly
    When I view the reconciliation report
    Then I should see discrepancy "0.00 PLN"
    And I should see discrepancy percentage "0.0%"
    And I should not see any suggestions

  # ============================================
  # CLOSING DAY WITHOUT RECORDED SALES
  # ============================================

  @edge-case
  Scenario: Close day with no recorded sales - warning shown
    Given a day is open for today
    And no sales have been recorded
    And the calculated sales from inventory show revenue of "500.00 PLN"
    When I start the day close wizard
    And I proceed to the reconciliation step
    Then I should see warning "Nie zarejestrowano zadnej sprzedazy"
    And I should be able to continue to confirmation
    And the revenue source should be marked as "calculated"

  @edge-case
  Scenario: Close day with partial recorded sales
    Given a day is open for today
    And I have recorded sales totaling "200.00 PLN"
    And the calculated sales show revenue of "500.00 PLN"
    When I proceed through the close wizard
    Then I should see discrepancy of "-300.00 PLN (60%)"
    And I should be able to continue despite the large discrepancy

  # ============================================
  # CRITICAL DISCREPANCY WARNING
  # ============================================

  @edge-case
  Scenario: Critical discrepancy warning when difference exceeds 30%
    Given a day is open for today
    And I have recorded sales totaling "100.00 PLN"
    And the calculated sales show revenue of "200.00 PLN"
    When I view the reconciliation report
    Then I should see a critical warning indicator
    And I should see message about reviewing inventory counts
    And the warning should be displayed in red

  # ============================================
  # SALES RECORDING EDGE CASES
  # ============================================

  @edge-case
  Scenario: Record sale when no shift is active
    Given a day is open for today
    And no shifts are currently active
    When I record a sale for "Kebab Maly"
    Then the sale should be recorded successfully
    And the sale should have no shift attribution

  @edge-case
  Scenario: Record sale for inactive product
    Given a day is open for today
    And product variant "Kebab Duzy" is marked as inactive
    When I try to record a sale for "Kebab Duzy"
    Then I should see error message "Produkt nie istnieje lub jest nieaktywny"
    And no sale should be recorded

  @error-handling
  Scenario: Cannot record sale when day is closed
    Given a day was opened and closed today
    When I try to navigate to the sales entry page
    Then I should be redirected to the daily operations page
    And I should see message "Brak otwartego dnia"

  @error-handling
  Scenario: Cannot record sale when no day is open
    Given no day is currently open
    When I try to access the sales entry page
    Then I should see message "Brak otwartego dnia. Otworz dzien aby rejestrowac sprzedaz."
    And I should be redirected to open a new day

  # ============================================
  # RUNNING TOTAL AND REAL-TIME UPDATES
  # ============================================

  @happy-path
  Scenario: Running total updates immediately on sale
    Given a day is open for today
    And the running total shows "0.00 PLN"
    When I record a sale for "Cola 0.5L"
    Then the running total should update to "6.00 PLN" within 1 second

  @happy-path
  Scenario: Running total updates when sale is voided
    Given a day is open for today
    And I have recorded sales totaling "50.00 PLN"
    When I void a sale worth "18.00 PLN"
    Then the running total should update to "32.00 PLN"

  # ============================================
  # INSIGHTS - PRODUCT POPULARITY
  # ============================================

  @insights
  Scenario: View product popularity ranking
    Given the following sales have been recorded over the past week:
      | product       | total_quantity |
      | Kebab Duzy    | 150            |
      | Kebab Sredni  | 100            |
      | Burger Classic| 80             |
      | Cola 0.5L     | 200            |
    When I view the product popularity insights
    Then I should see products ranked by quantity sold
    And "Cola 0.5L" should be ranked first
    And "Kebab Duzy" should be ranked second

  # ============================================
  # INSIGHTS - PEAK HOURS
  # ============================================

  @insights
  Scenario: View peak hours analysis
    Given at least 50 sales have been recorded with timestamps
    And sales distribution is:
      | hour | sales_count |
      | 11   | 10          |
      | 12   | 25          |
      | 13   | 30          |
      | 14   | 20          |
    When I view the peak hours insights
    Then I should see 13:00 identified as peak hour
    And I should see an hourly breakdown chart
    And I should see 11:00 identified as slowest hour

  @insights @edge-case
  Scenario: Peak hours not available with insufficient data
    Given only 10 sales have been recorded
    When I view the peak hours insights
    Then I should see message "Niewystarczajaca ilosc danych"
    And I should see that at least 50 sales are required

  # ============================================
  # INSIGHTS - PORTION ACCURACY
  # ============================================

  @insights
  Scenario: View portion accuracy report
    Given the following sales and ingredient usage over the past week:
      | ingredient     | expected_usage_kg | actual_usage_kg |
      | Mieso wolowe   | 45.0              | 49.0            |
      | Mieso mielone  | 12.0              | 11.5            |
    When I view the portion accuracy insights
    Then I should see "Mieso wolowe" with accuracy "91.8%"
    And I should see warning about 8% over-usage
    And I should see "Mieso mielone" with accuracy "104.3%"

  # ============================================
  # PERFORMANCE
  # ============================================

  @performance
  Scenario: Sales recording responds quickly
    Given a day is open for today
    When I tap on a product button
    Then the sale should be recorded in less than 500ms
    And the UI should show immediate feedback

  @performance
  Scenario: Reconciliation calculates quickly
    Given a day is open with 200 recorded sales
    When I request the reconciliation report
    Then the report should be generated in less than 2 seconds

  # ============================================
  # MOBILE/TOUCH EXPERIENCE
  # ============================================

  @mobile
  Scenario: Product buttons are touch-friendly
    Given I am using a smartphone
    When I view the sales entry screen
    Then product buttons should be at least 48x48 pixels
    And there should be adequate spacing between buttons
    And the running total should be visible without scrolling

  @mobile
  Scenario: Category tabs are swipeable
    Given I am using a smartphone
    And there are more categories than fit on screen
    When I swipe left on the category tabs
    Then I should see additional categories
    And the selected category should remain highlighted
