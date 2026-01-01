# language: en
@mid-day-operations @storage-transfer
Feature: Record Storage Transfer
  As an owner
  I want to record items brought from storage to shop
  So that my inventory is accurate across locations

  Background:
    Given I am logged in as the owner
    And today is open
    And the following ingredients exist:
      | name     | unit_type | unit_label |
      | Meat     | weight    | kg         |
      | Tortilla | count     | szt        |
      | Onion    | weight    | kg         |
    And the following storage inventory exists:
      | ingredient | quantity |
      | Meat       | 25.0     |
      | Tortilla   | 200      |
      | Onion      | 10.0     |

  @happy-path
  Scenario: Transfer items from storage to shop
    When I navigate to "Transfer from Storage"
    And I select ingredient "Tortilla"
    And I enter quantity "50"
    And I click "Save Transfer"
    Then I should see a success message "Transfer zapisany"
    And storage inventory for Tortilla should be 150
    And today's shop inventory should include the transfer

  @happy-path @batch
  Scenario: Transfer multiple ingredients in one session
    When I navigate to "Transfer from Storage"
    And I add transfer for "Tortilla" quantity "50"
    And I click "Add Another"
    And I add transfer for "Meat" quantity "5.0"
    And I click "Save All"
    Then both transfers should be recorded
    And storage inventory should be updated for both

  @edge-case @warning
  Scenario: Warning when transfer exceeds storage (allow override)
    Given storage inventory for Meat is 5.0 kg
    When I navigate to "Transfer from Storage"
    And I select ingredient "Meat"
    And I enter quantity "10.0"
    And I click "Save Transfer"
    Then I should see warning "Ilosc przekracza stan magazynowy (5.0 kg)"
    And I should see option "Save Anyway" and "Cancel"
    When I click "Save Anyway"
    Then the transfer should be saved
    And storage inventory for Meat should be -5.0 kg

  @validation @negative
  Scenario: Validation - quantity must be positive
    When I navigate to "Transfer from Storage"
    And I select ingredient "Tortilla"
    And I enter quantity "0"
    And I click "Save Transfer"
    Then I should see error "Ilosc musi byc wieksza od zera"
    And the transfer should not be saved

  @validation @negative
  Scenario: Validation - negative quantity rejected
    When I navigate to "Transfer from Storage"
    And I select ingredient "Tortilla"
    And I enter quantity "-10"
    And I click "Save Transfer"
    Then I should see error "Ilosc musi byc wieksza od zera"
    And the transfer should not be saved

  @calculation
  Scenario: Transfer affects day closing calculation
    When I record a storage transfer:
      | ingredient | quantity |
      | Tortilla   | 20       |
    And I navigate to "Close Day"
    Then the expected Tortilla value should include the transferred 20 szt

  @ux
  Scenario: Shows current storage levels when selecting ingredient
    When I navigate to "Transfer from Storage"
    And I select ingredient "Meat"
    Then I should see "Available in storage: 25.0 kg"

  @edge-case
  Scenario: Transfer from storage with no prior storage count
    Given no storage inventory exists for "Onion"
    When I navigate to "Transfer from Storage"
    And I select ingredient "Onion"
    And I enter quantity "2.0"
    And I click "Save Transfer"
    Then I should see warning "Brak stanu magazynowego dla tego skladnika"
    And I should be able to save anyway
    And storage inventory for Onion should be -2.0 kg
