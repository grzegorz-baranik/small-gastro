# language: en
@reports
Feature: Reports
  As an owner
  I want to view various reports
  So that I can analyze my business performance

  Background:
    Given I am logged in as the owner
    And historical data exists for the past 30 days

  @daily-summary
  Scenario: View daily summary report
    When I navigate to "Reports" > "Daily Summary"
    And I select date "2026-01-01"
    Then I should see:
      | metric                | label              |
      | Total Income          | Przychod           |
      | Delivery Costs        | Koszty dostaw      |
      | Spoilage Count        | Straty             |
      | Net Profit            | Zysk netto         |
    And I should see products sold breakdown:
      | product      | quantity | revenue  |
      | Kebab Large  | 23       | 644 PLN  |
      | Kebab Small  | 15       | 330 PLN  |
      | Hot Dog      | 8        | 96 PLN   |
    And I should see ingredient usage table:
      | ingredient | opening | used | closing |
      | Meat       | 12.5    | 7.5  | 5.0     |
      | Tortilla   | 45      | 23   | 22      |
    And I should see any discrepancy alerts for that day

  @daily-summary @navigation
  Scenario: Navigate between days in daily summary
    Given I am viewing daily summary for "2026-01-01"
    When I click "Previous Day"
    Then I should see summary for "2025-12-31"
    When I click "Next Day"
    Then I should see summary for "2026-01-01"

  @monthly-trends
  Scenario: View monthly trends report
    When I navigate to "Reports" > "Monthly Trends"
    And I select month "December 2025"
    Then I should see a line chart of daily income
    And I should see a line chart of daily costs
    And I should see summary statistics:
      | metric         | label               |
      | Total Income   | Laczny przychod     |
      | Total Costs    | Laczne koszty       |
      | Average Daily  | Srednia dzienna     |
      | Best Day       | Najlepszy dzien     |
      | Worst Day      | Najgorszy dzien     |
    And I should see a table with daily breakdown

  @monthly-trends @filter
  Scenario: Filter monthly trends by date range
    When I navigate to "Reports" > "Monthly Trends"
    And I select custom range "2025-12-15" to "2025-12-31"
    Then I should see data only for the selected 17 days

  @ingredient-usage
  Scenario: View ingredient usage report
    When I navigate to "Reports" > "Ingredient Usage"
    And I select date range "2025-12-01" to "2025-12-31"
    And I select ingredients "Meat, Tortilla"
    Then I should see usage table for each day:
      | date       | ingredient | opening | used  | closing |
      | 2025-12-01 | Meat       | 15.0    | 8.0   | 7.0     |
      | 2025-12-01 | Tortilla   | 50      | 25    | 25      |
    And I should see total usage for the period:
      | ingredient | total_used |
      | Meat       | 240.0 kg   |
      | Tortilla   | 750 szt    |
    And I should see average daily usage

  @ingredient-usage @filter
  Scenario: Filter ingredient usage by single ingredient
    When I navigate to "Reports" > "Ingredient Usage"
    And I select date range "2025-12-01" to "2025-12-31"
    And I select only ingredient "Meat"
    Then I should see usage data only for Meat

  @spoilage
  Scenario: View spoilage report grouped by reason
    When I navigate to "Reports" > "Spoilage"
    And I select date range "2025-12-01" to "2025-12-31"
    And I group by "Reason"
    Then I should see spoilage totals by reason:
      | reason        | count | polish_label        |
      | expired       | 15    | Przeterminowane     |
      | over_prepared | 8     | Nadmierna produkcja |
      | contaminated  | 2     | Zanieczyszczone     |
    And I should see a pie chart of reasons

  @spoilage @group-by-ingredient
  Scenario: View spoilage report grouped by ingredient
    When I navigate to "Reports" > "Spoilage"
    And I select date range "2025-12-01" to "2025-12-31"
    And I group by "Ingredient"
    Then I should see spoilage totals by ingredient:
      | ingredient | total_quantity | unit |
      | Meat       | 3.5            | kg   |
      | Tortilla   | 12             | szt  |
    And I should see a bar chart of ingredients

  @spoilage @details
  Scenario: View detailed spoilage entries
    When I navigate to "Reports" > "Spoilage"
    And I click "Show Details"
    Then I should see individual entries:
      | date       | ingredient | quantity | reason       | notes                  |
      | 2025-12-15 | Meat       | 0.5      | expired      |                        |
      | 2025-12-16 | Tortilla   | 3        | over_prepared| Too many for lunch     |

  @export @excel
  Scenario: Export daily summary to Excel
    Given I am viewing daily summary for "2026-01-01"
    When I click "Export to Excel"
    Then an .xlsx file should be downloaded
    And the filename should contain "daily-summary-2026-01-01"
    And it should contain all visible data in tabular format

  @export @excel
  Scenario: Export monthly trends to Excel
    Given I am viewing monthly trends for "December 2025"
    When I click "Export to Excel"
    Then an .xlsx file should be downloaded
    And the filename should contain "monthly-trends-2025-12"
    And it should contain daily breakdown and summary statistics

  @export @excel
  Scenario: Export ingredient usage to Excel
    Given I am viewing ingredient usage report
    When I click "Export to Excel"
    Then an .xlsx file should be downloaded
    And it should contain the filtered data

  @export @excel
  Scenario: Export spoilage report to Excel
    Given I am viewing spoilage report
    When I click "Export to Excel"
    Then an .xlsx file should be downloaded
    And it should contain spoilage details with all columns

  @data-retention
  Scenario: Reports show data up to 1 year back
    When I navigate to "Reports" > "Monthly Trends"
    And I try to select a month from 13 months ago
    Then the month should not be selectable
    And I should see message "Dane dostepne do 12 miesiecy wstecz"

  @empty-state
  Scenario: Report shows empty state when no data
    Given no daily records exist for January 2026
    When I navigate to "Reports" > "Monthly Trends"
    And I select month "January 2026"
    Then I should see message "Brak danych dla wybranego okresu"
    And charts should show empty state
