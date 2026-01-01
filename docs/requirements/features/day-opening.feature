# language: en
@daily-operations @day-opening
Feature: Day Opening
  As an owner
  I want to record opening inventory counts for all ingredients
  So that I know my starting resources for the day

  Background:
    Given I am logged in as the owner
    And the following ingredients exist:
      | name     | unit_type | unit_label |
      | Meat     | weight    | kg         |
      | Tortilla | count     | szt        |
      | Onion    | weight    | kg         |

  @happy-path
  Scenario: Open a new day with manual counts
    Given no day is currently open
    And yesterday's closing counts were:
      | ingredient | quantity |
      | Meat       | 12.5     |
      | Tortilla   | 45       |
      | Onion      | 3.0      |
    When I navigate to "Open Day"
    Then I should see a form with today's date
    And I should see opening count fields for all active ingredients
    And the fields should be pre-filled with yesterday's closing values
    When I enter the following opening counts:
      | ingredient | quantity |
      | Meat       | 12.5     |
      | Tortilla   | 45       |
      | Onion      | 3.0      |
    And I click "Open Day"
    Then the day should be marked as "open"
    And I should see a success message "Dzien otwarty. Powodzenia!"
    And the opening inventory snapshot should be saved

  @happy-path
  Scenario: Open day with different counts than previous closing
    Given no day is currently open
    And yesterday's closing counts were:
      | ingredient | quantity |
      | Meat       | 12.5     |
      | Tortilla   | 45       |
    When I navigate to "Open Day"
    And I enter the following opening counts:
      | ingredient | quantity |
      | Meat       | 10.0     |
      | Tortilla   | 40       |
    And I click "Open Day"
    Then the day should be marked as "open"
    And the opening counts should be saved as entered

  @edge-case @warning
  Scenario: Cannot open a day when previous day is not closed
    Given there is an open day for yesterday
    When I navigate to "Open Day"
    Then I should see a warning "Poprzedni dzien nie zostal zamkniety"
    And I should see an option to "Close Yesterday First"
    And I should see an option to "Open Today Anyway"

  @ux @time-saving
  Scenario: Use "Copy from Last Closing" button
    Given no day is currently open
    And yesterday's closing counts were:
      | ingredient | quantity |
      | Meat       | 15.0     |
      | Tortilla   | 60       |
      | Onion      | 4.5      |
    When I navigate to "Open Day"
    And I click "Copy from Last Closing"
    Then all opening count fields should be filled with yesterday's closing values
    And I can modify individual values before saving

  @validation @negative
  Scenario: Validation - cannot submit with empty counts
    Given no day is currently open
    When I navigate to "Open Day"
    And I leave the "Meat" count empty
    And I click "Open Day"
    Then I should see an error "Wszystkie skladniki musza miec uzupelniona ilosc"
    And the day should not be opened

  @validation @negative
  Scenario: Validation - cannot submit with negative counts
    Given no day is currently open
    When I navigate to "Open Day"
    And I enter "-5" for "Meat"
    And I click "Open Day"
    Then I should see an error "Ilosc nie moze byc ujemna"
    And the day should not be opened

  @edge-case
  Scenario: First day ever - no previous closing exists
    Given no daily records exist in the system
    When I navigate to "Open Day"
    Then I should see empty opening count fields
    And I should not see "Copy from Last Closing" button
    When I enter the following opening counts:
      | ingredient | quantity |
      | Meat       | 20.0     |
      | Tortilla   | 100      |
      | Onion      | 5.0      |
    And I click "Open Day"
    Then the day should be marked as "open"

  @edge-case
  Scenario: Open a past date (catching up)
    Given no day is currently open
    And today is "2026-01-05"
    And the last closed day was "2026-01-02"
    When I navigate to "Open Day"
    And I change the date to "2026-01-03"
    And I enter opening counts for all ingredients
    And I click "Open Day"
    Then day "2026-01-03" should be marked as "open"
