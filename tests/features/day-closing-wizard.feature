# language: en
# encoding: utf-8

@day-closing-wizard
Feature: Day Closing Wizard
  As a food establishment owner
  I want to have a clear step-by-step day closing wizard
  So that I clearly understand inventory calculations and make informed decisions

  Background:
    Given I have an open day record for today
    And the following ingredients exist:
      | name            | unit |
      | Kebab meat      | kg   |
      | Buns            | pcs  |
      | Mixed vegetables| kg   |
      | Garlic sauce    | kg   |
    And opening quantities were:
      | ingredient      | quantity |
      | Kebab meat      | 10.5     |
      | Buns            | 50       |
      | Mixed vegetables| 5.0      |
      | Garlic sauce    | 2.0      |

  # ===========================================
  # STEP 1: OPENING INVENTORY REVIEW
  # ===========================================

  @happy-path @smoke @step-1
  Scenario: Display opening inventory in step 1
    When I open the day closing wizard
    Then I should see a stepper with 4 steps
    And I should be on step 1 "Opening"
    And I should see the opening date and time
    And I should see the opening inventory table with:
      | ingredient       | quantity   |
      | Kebab meat       | 10.50 kg   |
      | Buns             | 50 pcs     |
      | Mixed vegetables | 5.00 kg    |
      | Garlic sauce     | 2.00 kg    |
    And opening values should be read-only

  @happy-path @navigation
  Scenario: Navigate from step 1 to step 2
    Given I am on step 1 of the day closing wizard
    When I click the "Next" button
    Then I should be on step 2 "Events"
    And step 1 should show a completion checkmark

  # ===========================================
  # STEP 2: DAY EVENTS REVIEW
  # ===========================================

  @happy-path @step-2
  Scenario: Display day events with deliveries, transfers, and spoilage
    Given the following events occurred today:
      | type     | ingredient       | quantity | price  | reason  |
      | delivery | Kebab meat       | 5.0      | 250.00 |         |
      | delivery | Buns             | 30       | 50.00  |         |
      | transfer | Garlic sauce     | 1.0      |        |         |
      | spoilage | Kebab meat       | 0.5      |        | expired |
      | spoilage | Buns             | 5        |        | damaged |
    When I am on step 2 of the day closing wizard
    Then I should see the deliveries section with:
      | ingredient  | quantity | price      |
      | Kebab meat  | +5.00 kg | 250.00 PLN |
      | Buns        | +30 pcs  | 50.00 PLN  |
    And I should see total delivery cost "300.00 PLN"
    And I should see the transfers section with:
      | ingredient   | quantity |
      | Garlic sauce | +1.00 kg |
    And I should see the spoilage section with:
      | ingredient  | quantity  | reason  |
      | Kebab meat  | -0.50 kg  | expired |
      | Buns        | -5 pcs    | damaged |
    And I should see the impact summary table

  @edge-case @step-2
  Scenario: Display events when there were no events
    Given no events occurred today
    When I am on step 2 of the day closing wizard
    Then I should see message "No events during the day"

  @navigation @step-2
  Scenario: Navigate between step 1 and step 2
    Given I am on step 2 of the day closing wizard
    When I click the "Back" button
    Then I should be on step 1 "Opening"
    When I click the "Next" button
    Then I should be on step 2 "Events"

  # ===========================================
  # STEP 3: ENTERING CLOSING QUANTITIES
  # ===========================================

  @happy-path @step-3 @live-calculations
  Scenario: Enter closing quantities with real-time calculations
    Given the following events occurred today:
      | type     | ingredient  | quantity | price  |
      | delivery | Kebab meat  | 5.0      | 250.00 |
    And expected closing quantity for "Kebab meat" is 15.5 kg
    When I am on step 3 of the day closing wizard
    And I enter "12.0" as closing quantity for "Kebab meat"
    Then I should see usage for "Kebab meat" as "3.50 kg"
    And calculations should update immediately without clicking a button

  @happy-path @step-3 @discrepancy-ok
  Scenario: Discrepancy status indicator - OK level
    Given expected closing quantity for "Kebab meat" is 15.0 kg
    And expected usage for "Kebab meat" is 3.0 kg
    When I am on step 3 of the day closing wizard
    And I enter "12.0" as closing quantity for "Kebab meat"
    Then usage should be "3.00 kg"
    And discrepancy status should show "OK" with green color

  @warning @step-3 @discrepancy-warning
  Scenario: Discrepancy level warning (5-10%)
    Given expected closing quantity for "Buns" is 75 pcs
    And expected usage for "Buns" is 20 pcs
    When I am on step 3 of the day closing wizard
    And I enter "53" as closing quantity for "Buns"
    Then usage should be "22 pcs"
    And discrepancy should be approximately 10%
    And discrepancy status should show "Warning" with yellow color

  @critical @step-3 @discrepancy-critical
  Scenario: Discrepancy level critical (>10%)
    Given expected closing quantity for "Garlic sauce" is 3.0 kg
    And expected usage for "Garlic sauce" is 1.0 kg
    When I am on step 3 of the day closing wizard
    And I enter "1.5" as closing quantity for "Garlic sauce"
    Then usage should be "1.50 kg"
    And discrepancy should be 50%
    And discrepancy status should show "Critical" with red color
    And I should see an alert for "Garlic sauce" in the discrepancy section

  @happy-path @step-3 @copy-expected
  Scenario: Copy expected values to closing fields
    Given I am on step 3 of the day closing wizard
    And all input fields are empty
    When I click the "Copy expected" button
    Then all closing fields should be filled with expected values
    And all usage values should show "0"
    And all discrepancy statuses should show "OK"

  @happy-path @step-3 @formula
  Scenario: Display calculation formula
    When I am on step 3 of the day closing wizard
    Then I should see the formula "Opening + Deliveries + Transfers - Spoilage - Closing = Usage"

  @error-handling @step-3 @validation
  Scenario: Validation prevents proceeding with empty fields
    Given I am on step 3 of the day closing wizard
    And I have not entered any closing quantities
    When I try to click the "Next" button
    Then I should remain on step 3
    And the "Next" button should be disabled

  @error-handling @step-3 @validation
  Scenario: Validation of invalid values
    Given I am on step 3 of the day closing wizard
    When I enter "abc" as closing quantity for "Kebab meat"
    Then I should see a validation error for "Kebab meat"

  @error-handling @step-3 @validation
  Scenario: Reject negative values
    Given I am on step 3 of the day closing wizard
    When I enter "-5" as closing quantity for "Buns"
    Then I should see error "Value cannot be negative"

  @error-handling @step-3 @validation
  Scenario: Reject decimal values for count-based ingredients
    Given I am on step 3 of the day closing wizard
    When I enter "5.5" as closing quantity for "Buns"
    Then I should see error "Quantity must be an integer"

  # ===========================================
  # STEP 4: CONFIRMATION
  # ===========================================

  @happy-path @step-4
  Scenario: Review summary before closing
    Given I have entered valid closing quantities in step 3
    When I proceed to step 4
    Then I should see the confirmation summary with:
      | field   | value          |
      | Date    | Today's date   |
      | Opening | Opening time   |
      | Closing | "now"          |
    And I should see discrepancy warnings
    And I should see calculated sales table
    And I should see financial summary with revenue, costs, and profit
    And I should see a notes field

  @happy-path @step-4 @notes
  Scenario: Add notes before closing
    Given I am on step 4 of the day closing wizard
    When I enter "Day was quiet" in the notes field
    And I click "Close day"
    And I confirm the closure
    Then notes should be saved with the day record

  @happy-path @smoke @step-4 @close
  Scenario: Confirm and close the day
    Given I have entered valid closing quantities
    And I am on step 4 of the day closing wizard
    When I click "Close day"
    Then I should see a confirmation dialog
    When I confirm the closure
    Then the day should be marked as closed
    And I should see a success message
    And the wizard should close

  @cancel @step-4
  Scenario: Cancel closure from confirmation dialog
    Given I am on step 4 of the day closing wizard
    When I click "Close day"
    And I cancel the confirmation dialog
    Then I should remain on step 4
    And the day should still be open

  # ===========================================
  # STEPPER NAVIGATION
  # ===========================================

  @navigation @stepper
  Scenario: Click on completed step to go back
    Given I am on step 3 of the day closing wizard
    When I click on step 1 in the stepper
    Then I should be on step 1

  @navigation @stepper
  Scenario: Cannot click on future steps
    Given I am on step 1 of the day closing wizard
    When I try to click on step 3 in the stepper
    Then I should remain on step 1

  @cancel
  Scenario: Cancel wizard on any step
    Given I am on step 2 of the day closing wizard
    When I click the "Cancel" button
    Then the wizard should close
    And the day should remain open

  # ===========================================
  # EDGE CASES
  # ===========================================

  @edge-case @negative-usage
  Scenario: Negative usage (more stock than expected)
    Given expected closing quantity for "Mixed vegetables" is 8.0 kg
    When I am on step 3 of the day closing wizard
    And I enter "10.0" as closing quantity for "Mixed vegetables"
    Then usage should be "-2.00 kg"
    And it should be highlighted as unusual

  @edge-case @zero-expected
  Scenario: Zero expected closing quantity
    Given expected closing quantity for "Garlic sauce" is 0 kg (all used)
    When I am on step 3 of the day closing wizard
    And I enter "0" as closing quantity for "Garlic sauce"
    Then discrepancy status should show "N/A" or "OK"

  @edge-case @large-discrepancy
  Scenario: Very large discrepancy (>50%)
    Given expected usage for "Kebab meat" is 2.0 kg
    When I am on step 3 of the day closing wizard
    And I enter "5.0" as closing quantity for "Kebab meat" (usage = 10 kg)
    Then discrepancy status should show "Critical"
    And I should see a clear warning for this ingredient

  # ===========================================
  # PERFORMANCE
  # ===========================================

  @performance
  Scenario: Real-time calculations execute quickly
    Given I have 20 ingredients in the system
    And I am on step 3 of the day closing wizard
    When I enter a value in a closing field
    Then calculations should complete in less than 50ms
    And there should be no noticeable delay

  @performance
  Scenario: Wizard loads quickly
    When I click the "Close day" button
    Then the wizard should load in less than 500ms
