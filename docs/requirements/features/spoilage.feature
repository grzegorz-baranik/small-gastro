# language: en
@mid-day-operations @spoilage
Feature: Record Spoilage
  As an owner
  I want to record spoiled ingredients with reasons
  So that I can track waste and identify patterns

  Background:
    Given I am logged in as the owner
    And today is open
    And the following ingredients exist:
      | name     | unit_type | unit_label |
      | Meat     | weight    | kg         |
      | Tortilla | count     | szt        |
      | Onion    | weight    | kg         |

  @happy-path
  Scenario: Record spoilage with reason
    When I navigate to "Record Spoilage"
    And I select ingredient "Meat"
    And I enter quantity "0.5"
    And I select reason "Expired"
    And I click "Save"
    Then I should see a success message "Strata zapisana"
    And the spoilage should be recorded for today
    And today's closing calculation should account for this spoilage

  @happy-path
  Scenario: Record spoilage with notes
    When I navigate to "Record Spoilage"
    And I select ingredient "Tortilla"
    And I enter quantity "5"
    And I select reason "Over-prepared"
    And I enter notes "Made too many wraps for lunch rush"
    And I click "Save"
    Then the spoilage should be saved with the notes
    And the notes should be visible in the spoilage report

  @ux @dropdown
  Scenario: Available spoilage reasons
    When I navigate to "Record Spoilage"
    And I click on the reason dropdown
    Then I should see the following options:
      | reason              | polish_label           |
      | expired             | Przeterminowane        |
      | over_prepared       | Nadmierna produkcja    |
      | contaminated        | Zanieczyszczone        |
      | equipment_failure   | Awaria sprzetu         |
      | other               | Inne                   |

  @validation @negative
  Scenario: Validation - quantity must be positive
    When I navigate to "Record Spoilage"
    And I select ingredient "Meat"
    And I enter quantity "0"
    And I select reason "Expired"
    And I click "Save"
    Then I should see error "Ilosc musi byc wieksza od zera"
    And the spoilage should not be saved

  @validation @negative
  Scenario: Validation - reason is required
    When I navigate to "Record Spoilage"
    And I select ingredient "Meat"
    And I enter quantity "0.5"
    And I do not select a reason
    And I click "Save"
    Then I should see error "Wybierz przyczyne straty"
    And the spoilage should not be saved

  @calculation
  Scenario: Spoilage affects day closing calculation
    When I record spoilage:
      | ingredient | quantity | reason  |
      | Meat       | 0.5      | expired |
    And I navigate to "Close Day"
    Then the expected Meat value should be reduced by spoilage 0.5 kg

  @batch
  Scenario: Record multiple spoilage entries
    When I navigate to "Record Spoilage"
    And I add spoilage for "Meat" quantity "0.3" reason "Expired"
    And I click "Add Another"
    And I add spoilage for "Tortilla" quantity "3" reason "Over-prepared"
    And I click "Save All"
    Then both spoilage entries should be recorded

  @edge-case
  Scenario: Record spoilage for "Other" reason requires notes
    When I navigate to "Record Spoilage"
    And I select ingredient "Onion"
    And I enter quantity "1.0"
    And I select reason "Other"
    And I leave notes empty
    And I click "Save"
    Then I should see error "Podaj opis dla 'Inne'"
    And the spoilage should not be saved

  @edge-case
  Scenario: Record spoilage for "Other" with notes succeeds
    When I navigate to "Record Spoilage"
    And I select ingredient "Onion"
    And I enter quantity "1.0"
    And I select reason "Other"
    And I enter notes "Customer complained, had to throw away"
    And I click "Save"
    Then the spoilage should be saved successfully
