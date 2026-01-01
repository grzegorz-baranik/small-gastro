# language: en
@daily-operations @day-closing
Feature: Day Closing
  As an owner
  I want to record closing inventory counts and see calculated sales
  So that I know what was sold and my daily income

  Background:
    Given I am logged in as the owner
    And the following products exist:
      | name         | variant | price | primary_ingredient | amount |
      | Kebab        | Large   | 28.00 | Tortilla           | 1      |
      | Kebab        | Small   | 22.00 | Tortilla           | 1      |
      | Hot Dog      | null    | 12.00 | Hot dog bun        | 1      |
    And today is open with opening counts:
      | ingredient   | quantity |
      | Meat         | 12.5     |
      | Tortilla     | 45       |
      | Hot dog bun  | 20       |

  @happy-path @calculation
  Scenario: Close day and calculate sales
    Given no deliveries, transfers, or spoilage today
    When I navigate to "Close Day"
    Then I should see the opening counts for each ingredient
    And I should see expected closing equals opening (no events)
    When I enter the following closing counts:
      | ingredient   | quantity |
      | Meat         | 5.0      |
      | Tortilla     | 22       |
      | Hot dog bun  | 12       |
    And I click "Calculate Usage"
    Then I should see usage calculated:
      | ingredient   | usage |
      | Meat         | 7.5   |
      | Tortilla     | 23    |
      | Hot dog bun  | 8     |
    And I should see products sold:
      | product      | quantity | revenue  |
      | Kebab Large  | 23       | 644 PLN  |
      | Hot Dog      | 8        | 96 PLN   |
    And I should see total income "740 PLN"
    When I click "Close Day"
    Then the day should be marked as "closed"
    And I should see a success message

  @calculation @delivery
  Scenario: Close day with deliveries included in calculation
    Given today has a delivery:
      | ingredient | quantity | price |
      | Meat       | 5.0      | 100   |
    When I navigate to "Close Day"
    Then I should see expected for Meat: 12.5 + 5.0 = 17.5 kg
    When I enter closing count for Meat: 10.0
    And I click "Calculate Usage"
    Then I should see Meat usage: 7.5 kg

  @calculation @transfer
  Scenario: Close day with storage transfers included
    Given today has a storage transfer:
      | ingredient | quantity |
      | Tortilla   | 20       |
    When I navigate to "Close Day"
    Then I should see expected for Tortilla: 45 + 20 = 65 szt
    When I enter closing count for Tortilla: 40
    And I click "Calculate Usage"
    Then I should see Tortilla usage: 25 szt

  @calculation @spoilage
  Scenario: Close day with spoilage deducted
    Given today has spoilage:
      | ingredient | quantity | reason  |
      | Meat       | 0.5      | expired |
    When I navigate to "Close Day"
    Then I should see expected for Meat: 12.5 - 0.5 = 12.0 kg
    When I enter closing count for Meat: 5.0
    And I click "Calculate Usage"
    Then I should see Meat usage: 7.0 kg (not 7.5)

  @discrepancy @alert-green
  Scenario: Discrepancy alert - acceptable variance (under 5%)
    Given product recipes expect 7.0 kg meat for 23 kebabs
    When I navigate to "Close Day"
    And I enter closing counts showing 7.2 kg meat used
    And I click "Calculate Usage"
    Then I should see Meat discrepancy "3%" with green indicator
    And no warning message should appear

  @discrepancy @alert-yellow
  Scenario: Discrepancy alert - concerning variance (5-10%)
    Given product recipes expect 7.0 kg meat for calculated sales
    When I navigate to "Close Day"
    And I enter closing counts showing 7.6 kg meat used
    And I click "Calculate Usage"
    Then I should see Meat discrepancy "8%" with yellow indicator
    And I should see warning "Meat: 8% variance - Concerning"

  @discrepancy @alert-red
  Scenario: Discrepancy alert - critical variance (over 10%)
    Given product recipes expect 7.0 kg meat for calculated sales
    When I navigate to "Close Day"
    And I enter closing counts showing 8.0 kg meat used
    And I click "Calculate Usage"
    Then I should see Meat discrepancy "14%" with red indicator
    And I should see warning "Meat: 14% variance - Critical"

  @edit @closed-day
  Scenario: Edit a closed day
    Given yesterday is closed with income 1000 PLN
    When I navigate to yesterday's record
    And I click "Edit"
    Then I should be able to modify closing counts
    When I change Tortilla closing from 22 to 20
    And I click "Recalculate and Save"
    Then the sales and income should be recalculated
    And the record should remain closed with updated values

  @edge-case @all-events
  Scenario: Close day with all event types
    Given today has a delivery:
      | ingredient | quantity | price |
      | Meat       | 5.0      | 100   |
    And today has a storage transfer:
      | ingredient | quantity |
      | Tortilla   | 20       |
    And today has spoilage:
      | ingredient | quantity | reason       |
      | Meat       | 0.3      | over_prepared|
    When I navigate to "Close Day"
    Then I should see combined expected values:
      | ingredient   | opening | delivery | transfer | spoilage | expected |
      | Meat         | 12.5    | 5.0      | 0        | 0.3      | 17.2     |
      | Tortilla     | 45      | 0        | 20       | 0        | 65       |
      | Hot dog bun  | 20      | 0        | 0        | 0        | 20       |

  @validation
  Scenario: Warning when closing exceeds expected (allow override)
    Given no deliveries, transfers, or spoilage today
    And opening count for Meat was 12.5 kg
    When I navigate to "Close Day"
    And I enter closing count for Meat: 15.0 kg
    Then I should see warning "Ilosc koncowa przekracza dostepny stan"
    And I should be able to save anyway with acknowledgment
