# language: en
@mid-day-operations @delivery
Feature: Record Delivery
  As an owner
  I want to record ingredient deliveries
  So that my inventory calculations include new stock

  Background:
    Given I am logged in as the owner
    And today is open
    And the following ingredients exist:
      | name     | unit_type | unit_label |
      | Meat     | weight    | kg         |
      | Tortilla | count     | szt        |
      | Onion    | weight    | kg         |

  @happy-path
  Scenario: Record a single ingredient delivery
    When I navigate to "Record Delivery"
    And I select ingredient "Meat"
    And I enter quantity "5.0"
    And I enter price "100"
    And I click "Save Delivery"
    Then I should see a success message "Dostawa zapisana"
    And the delivery should be recorded for today
    And today's delivery total should include 100 PLN

  @happy-path @batch
  Scenario: Record multiple ingredients in one session
    When I navigate to "Record Delivery"
    And I add delivery for "Meat" quantity "5.0" price "100"
    And I click "Add Another"
    And I add delivery for "Tortilla" quantity "50" price "75"
    And I click "Save All"
    Then both deliveries should be recorded
    And today's delivery total should be 175 PLN

  @validation @negative
  Scenario: Validation - quantity must be positive
    When I navigate to "Record Delivery"
    And I select ingredient "Meat"
    And I enter quantity "0"
    And I click "Save Delivery"
    Then I should see error "Ilosc dostawy musi byc wieksza od zera"
    And the delivery should not be saved

  @validation @negative
  Scenario: Validation - negative quantity rejected
    When I navigate to "Record Delivery"
    And I select ingredient "Meat"
    And I enter quantity "-5"
    And I click "Save Delivery"
    Then I should see error "Ilosc dostawy musi byc wieksza od zera"
    And the delivery should not be saved

  @edge-case
  Scenario: Validation - price can be zero (free sample/promo)
    When I navigate to "Record Delivery"
    And I select ingredient "Meat"
    And I enter quantity "1.0"
    And I enter price "0"
    And I click "Save Delivery"
    Then the delivery should be saved successfully
    And today's delivery cost should not increase

  @edge-case
  Scenario: Record delivery for a past open day
    Given yesterday is open (not closed yet)
    When I navigate to "Record Delivery"
    And I change the date to yesterday
    And I select ingredient "Meat"
    And I enter quantity "5.0"
    And I enter price "100"
    And I click "Save Delivery"
    Then the delivery should be recorded for yesterday

  @ux
  Scenario: Unit label displayed correctly for weight-based ingredient
    When I navigate to "Record Delivery"
    And I select ingredient "Meat"
    Then I should see the unit label "kg" next to the quantity field

  @ux
  Scenario: Unit label displayed correctly for count-based ingredient
    When I navigate to "Record Delivery"
    And I select ingredient "Tortilla"
    Then I should see the unit label "szt" next to the quantity field

  @calculation
  Scenario: Delivery affects day closing calculation
    When I record a delivery:
      | ingredient | quantity | price |
      | Meat       | 5.0      | 100   |
    And I navigate to "Close Day"
    Then the expected Meat value should include the delivered 5.0 kg
