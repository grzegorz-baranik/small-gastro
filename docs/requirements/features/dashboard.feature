# language: en
@dashboard
Feature: Daily Operations Dashboard
  As an owner
  I want a central dashboard for daily operations
  So that I can quickly see status and take actions

  Background:
    Given I am logged in as the owner

  @happy-path @day-open
  Scenario: Dashboard when day is open
    Given today is open
    And today has the following events:
      | type     | count | total_cost |
      | delivery | 2     | 150 PLN    |
      | transfer | 1     | n/a        |
      | spoilage | 0     | 0 PLN      |
    When I navigate to "Dashboard"
    Then I should see today's date and "OPEN" status badge
    And I should see "Open Day" button disabled
    And I should see "Close Day" button enabled
    And I should see today's events summary:
      | event type | details                     |
      | Deliveries | 2 items (150 PLN)           |
      | Transfers  | 1 item                      |
      | Spoilage   | 0 items                     |
    And I should see quick action buttons:
      | action               |
      | Record Delivery      |
      | Transfer from Storage|
      | Record Spoilage      |

  @happy-path @day-closed
  Scenario: Dashboard when no day is open
    Given no day is currently open
    And yesterday was closed with income 1,250 PLN
    When I navigate to "Dashboard"
    Then I should see "No open day" status
    And I should see "Open Day" button enabled
    And I should see "Close Day" button disabled
    And I should see recent days summary:
      | date       | status | income    | alerts        |
      | Yesterday  | CLOSED | 1,250 PLN | 1 warning     |
      | 2 days ago | CLOSED | 980 PLN   | none          |
      | 3 days ago | CLOSED | 1,100 PLN | 2 warnings    |

  @alerts
  Scenario: Dashboard shows discrepancy alerts
    Given yesterday was closed with discrepancy alerts:
      | ingredient | variance | level      |
      | Meat       | 8%       | concerning |
      | Onion      | 12%      | critical   |
    When I navigate to "Dashboard"
    Then I should see alert indicators for yesterday
    And clicking on alerts should show details:
      | ingredient | variance | level      | color  |
      | Meat       | 8%       | Concerning | yellow |
      | Onion      | 12%      | Critical   | red    |

  @quick-actions
  Scenario: Quick action opens correct form
    Given today is open
    When I navigate to "Dashboard"
    And I click "Record Delivery"
    Then I should be taken to the Record Delivery form
    And the date should be pre-filled with today

  @navigation
  Scenario: Navigate to detailed day view
    Given yesterday is closed
    When I navigate to "Dashboard"
    And I click on yesterday's row
    Then I should be taken to the daily summary for yesterday

  @edge-case @unclosed-previous
  Scenario: Warning when previous day not closed
    Given yesterday is still open (not closed)
    When I navigate to "Dashboard"
    Then I should see prominent warning "Poprzedni dzien nie zamkniety!"
    And I should see "Close Yesterday" quick action button

  @storage-reminder
  Scenario: Storage count reminder on dashboard
    Given last storage count was 8 days ago
    When I navigate to "Dashboard"
    Then I should see reminder section:
      | reminder                                    |
      | Storage inventory last counted 8 days ago  |
    And I should see "Count Storage" quick link

  @empty-state
  Scenario: Dashboard first time (no data)
    Given no daily records exist in the system
    When I navigate to "Dashboard"
    Then I should see welcome message "Witaj! Zacznij od otwarcia pierwszego dnia."
    And I should see "Open First Day" button prominently
    And recent days section should show "No history yet"

  @time-display
  Scenario: Dashboard shows operation times
    Given today is open since 09:15
    When I navigate to "Dashboard"
    Then I should see "Opened at: 09:15"
    And I should see current time elapsed since opening

  @responsive
  Scenario: Dashboard works on mobile
    Given I am using a mobile device
    When I navigate to "Dashboard"
    Then all elements should be visible and usable
    And quick action buttons should be easily tappable
    And status should be clearly visible
