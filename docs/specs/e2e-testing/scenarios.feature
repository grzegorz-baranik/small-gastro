# E2E Testing Scenarios
# These scenarios define the end-to-end test cases for Playwright implementation
#
# SCOPE: To meet the <2 minute execution target, only 4 CRITICAL scenarios
#        are implemented initially (marked with @critical).
#        Other scenarios are documented for future expansion (marked with @future).

Feature: E2E Test Coverage
  As a QA engineer
  I want comprehensive E2E tests
  So that I can verify the system works correctly for real users

  # ===========================================================================
  # CRITICAL HAPPY PATHS (Initial Scope - 4 scenarios, ~90 sec total)
  # These are the ONLY scenarios implemented in Phase 1
  # ===========================================================================

  @e2e @day-closing @happy-path @critical
  Scenario: Complete day closing wizard from start to finish
    # Est. time: ~30 sec
    Given ingredients exist in the system:
      | name         | unit_type |
      | Mięso kebab  | weight    |
      | Bułki        | count     |
      | Sałata       | weight    |
    And a day is open with opening inventory:
      | ingredient   | quantity |
      | Mięso kebab  | 5.0      |
      | Bułki        | 50       |
      | Sałata       | 2.0      |
    When I navigate to "/operacje"
    And I click "Zamknij dzień" button
    Then I should see the close day wizard at step 1

    When I review the opening inventory table
    Then I should see "Mięso kebab" with quantity "5.0 kg"
    And I should see "Bułki" with quantity "50 szt"

    When I click "Dalej" button
    Then I should be at wizard step 2

    When I click "Dalej" button
    Then I should be at wizard step 3 (closing quantities)

    When I enter closing quantity "4.5" for "Mięso kebab"
    And I enter closing quantity "45" for "Bułki"
    And I enter closing quantity "1.8" for "Sałata"
    And I click "Dalej" button
    Then I should be at wizard step 4 (confirmation)

    When I enter notes "Dzień testowy"
    And I click "Zamknij dzień" button
    And I confirm the dialog
    Then the day should be marked as "Zamknięty"

  @e2e @menu @product-ingredients @critical
  Scenario: Create product with linked ingredients
    # Est. time: ~20 sec
    Given ingredients exist:
      | name         | unit_type |
      | Mięso kebab  | weight    |
      | Bułka        | count     |
      | Sos czosnkowy| weight    |
    When I navigate to "/menu"
    And I click "Dodaj produkt" button
    And I fill in product name "Kebab z sosem"
    And I fill in product price "22.00"
    And I add ingredient "Mięso kebab" with quantity "0.15"
    And I add ingredient "Bułka" with quantity "1"
    And I add ingredient "Sos czosnkowy" with quantity "0.03"
    And I click "Zapisz" button
    Then I should see "Kebab z sosem" in the products list

    When I click on product "Kebab z sosem"
    Then I should see ingredient "Mięso kebab" with "0.15 kg"
    And I should see ingredient "Bułka" with "1 szt"
    And I should see ingredient "Sos czosnkowy" with "0.03 kg"

  @e2e @employees @shifts @critical
  Scenario: Create employee and assign to shift
    # Est. time: ~20 sec
    Given positions exist:
      | name      | hourly_rate |
      | Kucharz   | 25.00       |
    And shift template "Zmiana poranna" exists (08:00-16:00)
    When I navigate to "/pracownicy"
    And I click "Dodaj pracownika" button
    And I fill in first name "Jan"
    And I fill in last name "Kowalski"
    And I assign position "Kucharz"
    And I click "Zapisz" button
    Then I should see "Jan Kowalski" in the employees list

    When I switch to "Grafik" tab
    And I select date "2026-01-10"
    And I click "Dodaj do zmiany" button
    And I select employee "Jan Kowalski"
    And I select shift "Zmiana poranna"
    And I click "Zapisz" button
    Then I should see "Jan Kowalski" assigned to "2026-01-10"

  @e2e @finances @category-expense @critical
  Scenario: Create expense category and add expense
    # Est. time: ~20 sec
    When I navigate to "/finanse"
    And I switch to "Kategorie" tab
    And I click "Dodaj kategorię" button
    And I fill in category name "Koszty operacyjne"
    And I click "Zapisz" button
    Then I should see "Koszty operacyjne" in categories

    When I click "Dodaj kategorię" button
    And I fill in category name "Media"
    And I select parent category "Koszty operacyjne"
    And I click "Zapisz" button
    Then "Media" should be a child of "Koszty operacyjne"

    When I switch to "Wydatki" tab
    And I click "Dodaj wydatek" button
    And I select category "Media"
    And I fill in amount "350.00"
    And I fill in description "Rachunek za prąd - styczeń"
    And I click "Zapisz" button
    Then I should see expense "350,00 zł" under "Media"

  # ===========================================================================
  # FUTURE SCOPE - Day Closing Additional Scenarios
  # ===========================================================================

  @e2e @day-closing @navigation @future
  Scenario: Navigate backwards in wizard preserves data
    Given a day is open with inventory
    And I am at step 3 of the close day wizard
    When I enter closing quantity "4.0" for "Mięso kebab"
    And I click "Wstecz" button
    Then I should be at wizard step 2

    When I click "Dalej" button
    Then I should be at wizard step 3
    And the closing quantity for "Mięso kebab" should be "4.0"

  @e2e @day-closing @copy-expected @future
  Scenario: Copy expected quantities to closing form
    Given a day is open with opening inventory:
      | ingredient   | quantity |
      | Mięso kebab  | 5.0      |
    And no events occurred during the day
    When I am at step 3 of the close day wizard
    And I click "Kopiuj oczekiwane" button
    Then the closing quantity for "Mięso kebab" should be "5.0"

  @e2e @day-closing @validation @future
  Scenario: Reject negative closing quantities
    Given a day is open with inventory
    When I am at step 3 of the close day wizard
    And I enter closing quantity "-1" for "Mięso kebab"
    Then I should see a validation error message
    And I should not be able to proceed to the next step

  @e2e @day-closing @discrepancy @future
  Scenario: Display discrepancy status based on difference
    Given a day is open with opening inventory:
      | ingredient   | quantity |
      | Mięso kebab  | 10.0     |
    When I am at step 3 of the close day wizard
    And I enter closing quantity "9.5" for "Mięso kebab"
    Then the discrepancy status for "Mięso kebab" should be "OK"

    When I change closing quantity to "8.5" for "Mięso kebab"
    Then the discrepancy status for "Mięso kebab" should be "Ostrzeżenie"

    When I change closing quantity to "7.0" for "Mięso kebab"
    Then the discrepancy status for "Mięso kebab" should be "Krytyczny"

  # ===========================================================================
  # FUTURE SCOPE - Menu & Ingredients Additional Scenarios
  # ===========================================================================

  @e2e @menu @create-product @future
  Scenario: Create a new product with price
    Given I navigate to "/menu"
    When I click "Dodaj produkt" button
    And I fill in product name "Kebab duży"
    And I fill in product price "25.00"
    And I click "Zapisz" button
    Then I should see "Kebab duży" in the products list
    And the price should display "25,00 zł"

  @e2e @menu @edit-product @future
  Scenario: Edit existing product price and ingredients
    Given a product "Burger" exists with price "18.00"
    When I navigate to "/menu"
    And I click edit on product "Burger"
    And I change the price to "20.00"
    And I click "Zapisz" button
    Then the product "Burger" should show price "20,00 zł"

  @e2e @menu @delete-product @future
  Scenario: Delete a product
    Given a product "Stary produkt" exists
    When I navigate to "/menu"
    And I click delete on product "Stary produkt"
    And I confirm the deletion
    Then "Stary produkt" should not appear in the products list

  @e2e @inventory @create-ingredient @future
  Scenario: Create new ingredient
    When I navigate to "/magazyn"
    And I click "Dodaj składnik" button
    And I fill in ingredient name "Ser żółty"
    And I select unit type "weight"
    And I click "Zapisz" button
    Then I should see "Ser żółty" in the ingredients list

  # ===========================================================================
  # FUTURE SCOPE - Employee & Shift Additional Scenarios
  # ===========================================================================

  @e2e @employees @create @future
  Scenario: Create a new employee
    When I navigate to "/pracownicy"
    And I click "Dodaj pracownika" button
    And I fill in first name "Jan"
    And I fill in last name "Kowalski"
    And I click "Zapisz" button
    Then I should see "Jan Kowalski" in the employees list

  @e2e @employees @assign-position @future
  Scenario: Assign position to employee
    Given positions exist:
      | name      | hourly_rate |
      | Kucharz   | 25.00       |
      | Kasjer    | 22.00       |
    And employee "Anna Nowak" exists
    When I navigate to "/pracownicy"
    And I click on employee "Anna Nowak"
    And I assign position "Kucharz"
    And I click "Zapisz" button
    Then employee "Anna Nowak" should have position "Kucharz"

  @e2e @shifts @create-template @future
  Scenario: Create shift template
    When I navigate to "/pracownicy"
    And I switch to "Szablony zmian" tab
    And I click "Dodaj szablon" button
    And I fill in shift name "Zmiana poranna"
    And I set start time "08:00"
    And I set end time "16:00"
    And I click "Zapisz" button
    Then I should see "Zmiana poranna" in shift templates

  @e2e @shifts @wage-calculation @future
  Scenario: View wage analytics for employee
    Given employee "Maria Zielińska" exists with position "Kasjer" at 22.00/hr
    And employee worked 40 hours in current week
    When I navigate to "/pracownicy"
    And I switch to "Analityka wynagrodzeń" tab
    And I select employee "Maria Zielińska"
    Then I should see total hours "40"
    And I should see calculated wage "880,00 zł"

  # ===========================================================================
  # FUTURE SCOPE - Finances Additional Scenarios
  # ===========================================================================

  @e2e @finances @create-revenue @future
  Scenario: Record revenue with payment method
    Given a day is open
    When I navigate to "/finanse"
    And I click "Dodaj przychód" button
    And I fill in amount "1250.00"
    And I select payment method "Gotówka"
    And I fill in description "Sprzedaż dzienna"
    And I click "Zapisz" button
    Then I should see revenue "1 250,00 zł" in today's transactions
    And the payment method should show "Gotówka"

  @e2e @finances @view-totals @future
  Scenario: View financial summary on dashboard
    Given expenses totaling 500 zł exist for today
    And revenue totaling 2000 zł exists for today
    When I navigate to "/pulpit"
    Then I should see today's revenue "2 000,00 zł"
    And I should see today's expenses "500,00 zł"
    And I should see today's profit "1 500,00 zł"

  # ===========================================================================
  # FUTURE SCOPE - Integration Scenarios
  # ===========================================================================

  @e2e @integration @day-with-sales @future
  Scenario: Complete day with sales affecting inventory
    Given ingredients exist with current stock:
      | name         | quantity |
      | Mięso kebab  | 10.0     |
      | Bułki        | 100      |
    And product "Kebab" exists with ingredients:
      | ingredient   | quantity |
      | Mięso kebab  | 0.15     |
      | Bułki        | 1        |
    And a day is open
    When 20 units of "Kebab" are sold
    And I close the day with actual inventory:
      | ingredient   | quantity |
      | Mięso kebab  | 6.8      |
      | Bułki        | 78       |
    Then the calculated usage for "Mięso kebab" should be "3.0 kg"
    And the calculated usage for "Bułki" should be "20 szt"
    And discrepancies should be flagged if actual differs from expected

  @e2e @integration @delivery-affects-closing @future
  Scenario: Delivery during day affects closing calculation
    Given ingredients exist
    And a day is open with 5.0 kg of "Mięso kebab"
    When a delivery of 3.0 kg "Mięso kebab" is recorded
    And I navigate to the close day wizard step 3
    Then the expected quantity for "Mięso kebab" should account for delivery
    And expected should show "8.0 kg" minus usage

  # ===========================================================================
  # FUTURE SCOPE - Error Handling Scenarios
  # ===========================================================================

  @e2e @error @api-failure @future
  Scenario: Handle API error gracefully
    Given the backend is returning errors
    When I try to create a new product
    Then I should see an error toast message
    And the form should remain open for retry

  @e2e @error @validation @future
  Scenario: Form validation prevents invalid data
    When I navigate to "/menu"
    And I click "Dodaj produkt" button
    And I leave product name empty
    And I enter negative price "-10"
    And I click "Zapisz" button
    Then I should see validation error for name field
    And I should see validation error for price field
    And the product should not be created
