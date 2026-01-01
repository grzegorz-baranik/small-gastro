# language: en
@storage-inventory
Feature: Storage Inventory Count
  As an owner
  I want to perform weekly storage inventory counts
  So that I know what ingredients are in my storage room

  Background:
    Given I am logged in as the owner
    And the following ingredients exist:
      | name     | unit_type | unit_label |
      | Meat     | weight    | kg         |
      | Tortilla | count     | szt        |
      | Onion    | weight    | kg         |

  @happy-path
  Scenario: Perform weekly storage count
    Given last storage count was 7 days ago:
      | ingredient | quantity |
      | Meat       | 30.0     |
      | Tortilla   | 250      |
      | Onion      | 15.0     |
    And transfers from storage this week totaled:
      | ingredient | quantity |
      | Meat       | 10.0     |
      | Tortilla   | 100      |
      | Onion      | 5.0      |
    When I navigate to "Storage Inventory"
    Then I should see last count values and expected current values:
      | ingredient | last_count | transfers | expected |
      | Meat       | 30.0       | -10.0     | 20.0     |
      | Tortilla   | 250        | -100      | 150      |
      | Onion      | 15.0       | -5.0      | 10.0     |
    When I enter current counts:
      | ingredient | quantity |
      | Meat       | 19.0     |
      | Tortilla   | 148      |
      | Onion      | 10.0     |
    And I click "Save Storage Count"
    Then the storage inventory should be updated
    And I should see a success message "Stan magazynowy zapisany"

  @discrepancy
  Scenario: Storage count shows discrepancy
    Given last storage count was 7 days ago:
      | ingredient | quantity |
      | Meat       | 30.0     |
    And transfers from storage this week totaled:
      | ingredient | quantity |
      | Meat       | 10.0     |
    When I navigate to "Storage Inventory"
    And I enter current count for Meat: 15.0
    And I click "Save Storage Count"
    Then I should see discrepancy for Meat: expected 20.0, actual 15.0, difference -5.0 kg

  @first-count
  Scenario: First storage count ever
    Given no storage inventory has ever been recorded
    When I navigate to "Storage Inventory"
    Then I should see empty count fields for all ingredients
    And I should not see "Expected" column
    When I enter current counts:
      | ingredient | quantity |
      | Meat       | 50.0     |
      | Tortilla   | 300      |
      | Onion      | 20.0     |
    And I click "Save Storage Count"
    Then the initial storage inventory should be created

  @validation @negative
  Scenario: Cannot submit with negative counts
    When I navigate to "Storage Inventory"
    And I enter "-5" for "Meat"
    And I click "Save Storage Count"
    Then I should see error "Ilosc nie moze byc ujemna"
    And the count should not be saved

  @validation
  Scenario: Can submit with zero counts (empty storage)
    When I navigate to "Storage Inventory"
    And I enter "0" for all ingredients
    And I click "Save Storage Count"
    Then the storage count should be saved successfully

  @history
  Scenario: View storage count history
    Given multiple storage counts have been recorded over time
    When I navigate to "Storage Inventory"
    And I click "View History"
    Then I should see a list of past storage counts
    And each entry should show date and ingredient quantities

  @ux @timing
  Scenario: Reminder for weekly storage count
    Given last storage count was 8 days ago
    When I navigate to "Dashboard"
    Then I should see a reminder "Ostatni stan magazynowy sprawdzony 8 dni temu"
    And I should see a quick link to "Storage Inventory"

  @integration
  Scenario: Storage count affects transfer warnings
    Given storage count shows Meat at 5.0 kg
    When I try to transfer 10.0 kg of Meat from storage
    Then I should see warning referencing the storage count
