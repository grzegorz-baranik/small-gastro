# language: en
# encoding: utf-8

# Unified Day Operations - BDD Scenarios
# Language: English (code), Polish (UI labels)

@unified_day_operations
Feature: Unified Day Operations
  As a shop manager
  I want to manage all daily operations through a unified wizard
  So that I can efficiently handle shifts, inventory, and day lifecycle

  Background:
    Given the database is empty
    And the following employees exist:
      | name           | position | hourly_rate | is_active |
      | Anna Kowalska  | Cook     | 25.00       | true      |
      | Jan Nowak      | Helper   | 20.00       | true      |
      | Maria Wiśniak  | Cook     | 25.00       | true      |
    And the following ingredients exist:
      | name        | unit_type | unit |
      | Mięso kebab | weight    | kg   |
      | Chleb pita  | count     | szt  |
      | Warzywa     | weight    | kg   |

  # ===========================================
  # SHIFT TEMPLATE MANAGEMENT
  # ===========================================

  @shift-templates @happy-path @smoke
  Scenario: Create recurring shift template for employee
    Given I am on the Settings page
    And I navigate to the "Harmonogram zmian" section
    When I click "Dodaj szablon zmiany"
    And I select employee "Anna Kowalska"
    And I select day "Poniedziałek"
    And I set start time to "08:00"
    And I set end time to "16:00"
    And I click "Zapisz"
    Then I should see a success message
    And I should see a template for "Anna Kowalska" on "Poniedziałek" from "08:00" to "16:00"

  @shift-templates @happy-path
  Scenario: Create multiple templates for same employee
    Given Anna Kowalska has no shift templates
    When I create the following shift templates for "Anna Kowalska":
      | day_of_week  | start_time | end_time |
      | Poniedziałek | 08:00      | 16:00    |
      | Wtorek       | 08:00      | 16:00    |
      | Środa        | 08:00      | 16:00    |
      | Czwartek     | 08:00      | 16:00    |
      | Piątek       | 08:00      | 16:00    |
    Then Anna Kowalska should have 5 shift templates

  @shift-templates @error-handling
  Scenario: Cannot create duplicate template for same day
    Given Anna Kowalska has a shift template for "Poniedziałek"
    When I try to create another template for "Anna Kowalska" on "Poniedziałek"
    Then I should see an error message "Pracownik ma już zaplanowaną zmianę na ten dzień"

  @shift-templates @error-handling
  Scenario: Cannot create template with invalid time range
    When I try to create a template with start time "16:00" and end time "08:00"
    Then I should see an error message "Czas zakończenia musi być późniejszy niż czas rozpoczęcia"

  @shift-templates
  Scenario: Delete shift template
    Given Anna Kowalska has a shift template for "Poniedziałek"
    When I delete the template for "Anna Kowalska" on "Poniedziałek"
    Then Anna Kowalska should have no template for "Poniedziałek"

  # ===========================================
  # SHIFT SCHEDULE CALENDAR
  # ===========================================

  @shift-calendar @happy-path
  Scenario: View weekly schedule with templates
    Given the following shift templates exist:
      | employee      | day_of_week  | start_time | end_time |
      | Anna Kowalska | Poniedziałek | 08:00      | 16:00    |
      | Jan Nowak     | Poniedziałek | 10:00      | 18:00    |
      | Anna Kowalska | Wtorek       | 08:00      | 16:00    |
    When I view the weekly schedule starting from "2026-01-05"
    Then I should see:
      | date       | day_name     | employee      | start_time | end_time | source   |
      | 2026-01-05 | Poniedziałek | Anna Kowalska | 08:00      | 16:00    | template |
      | 2026-01-05 | Poniedziałek | Jan Nowak     | 10:00      | 18:00    | template |
      | 2026-01-06 | Wtorek       | Anna Kowalska | 08:00      | 16:00    | template |

  @shift-calendar @happy-path
  Scenario: Override shift for specific date
    Given Anna Kowalska has a template for "Poniedziałek" from "08:00" to "16:00"
    When I create an override for "Anna Kowalska" on "2026-01-05" from "09:00" to "17:00"
    Then the schedule for "2026-01-05" should show "Anna Kowalska" from "09:00" to "17:00"
    And the override should be marked as "override"
    And the template for "Poniedziałek" should remain unchanged

  @shift-calendar @happy-path
  Scenario: Mark employee day off
    Given Anna Kowalska has a template for "Poniedziałek"
    When I mark "Anna Kowalska" as day off on "2026-01-05"
    Then the schedule for "2026-01-05" should not show "Anna Kowalska"
    And the template for "Poniedziałek" should remain unchanged

  @shift-calendar
  Scenario: Add extra shift without template
    Given Jan Nowak has no template for "Środa"
    When I create an override for "Jan Nowak" on "2026-01-07" from "12:00" to "20:00"
    Then the schedule for "2026-01-07" should show "Jan Nowak" from "12:00" to "20:00"
    And the shift should be marked as "override"

  # ===========================================
  # DAY OPERATIONS WIZARD - OPENING
  # ===========================================

  @wizard @opening @happy-path @smoke
  Scenario: Open day with auto-populated shifts
    Given the following shift templates exist:
      | employee      | day_of_week  | start_time | end_time |
      | Anna Kowalska | Poniedziałek | 08:00      | 16:00    |
      | Jan Nowak     | Poniedziałek | 10:00      | 18:00    |
    And today is "2026-01-05" (Poniedziałek)
    And no day is currently open
    When I click on day "2026-01-05" in the day list
    And I click "Otwórz dzień"
    Then I should see the Day Operations Wizard
    And I should be on Step 1 "Otwarcie"
    And I should see suggested shifts:
      | employee      | start_time | end_time |
      | Anna Kowalska | 08:00      | 16:00    |
      | Jan Nowak     | 10:00      | 18:00    |

  @wizard @opening @happy-path
  Scenario: Confirm shifts and enter opening inventory
    Given the Day Operations Wizard is open for "2026-01-05"
    And I am on Step 1 "Otwarcie"
    And I see suggested shifts for Anna Kowalska and Jan Nowak
    When I confirm all suggested shifts
    And I enter opening inventory:
      | ingredient  | quantity | unit |
      | Mięso kebab | 50.0     | kg   |
      | Chleb pita  | 100      | szt  |
      | Warzywa     | 20.0     | kg   |
    And I click "Kontynuuj"
    Then I should move to Step 2 "Operacje"
    And the opening step should be marked as completed

  @wizard @opening
  Scenario: Modify suggested shift times before confirming
    Given the Day Operations Wizard is open for "2026-01-05"
    And Anna Kowalska has suggested shift from "08:00" to "16:00"
    When I modify Anna Kowalska's shift to start at "09:00" and end at "17:00"
    And I confirm all shifts
    And I complete the opening step
    Then Anna Kowalska's confirmed shift should be from "09:00" to "17:00"

  @wizard @opening
  Scenario: Add manual shift during opening
    Given the Day Operations Wizard is open for "2026-01-05"
    And Maria Wiśniak has no suggested shift
    When I click "Dodaj zmianę"
    And I select "Maria Wiśniak"
    And I set shift from "12:00" to "20:00"
    And I confirm all shifts
    Then Maria Wiśniak should have a confirmed shift from "12:00" to "20:00"

  @wizard @opening
  Scenario: Remove suggested shift
    Given the Day Operations Wizard is open for "2026-01-05"
    And Jan Nowak has a suggested shift
    When I remove Jan Nowak from the shift list
    And I confirm remaining shifts
    And I complete the opening step
    Then Jan Nowak should not have a shift for "2026-01-05"

  @wizard @opening @error-handling
  Scenario: Cannot proceed without opening inventory
    Given the Day Operations Wizard is open for "2026-01-05"
    And I have confirmed shifts
    But I have not entered any opening inventory
    When I click "Kontynuuj"
    Then I should see an error "Wprowadź stan początkowy magazynu"
    And I should remain on Step 1

  @wizard @opening
  Scenario: Show previous day's closing inventory as reference
    Given "2026-01-04" was closed with closing inventory:
      | ingredient  | quantity |
      | Mięso kebab | 45.0     |
      | Chleb pita  | 80       |
      | Warzywa     | 15.0     |
    And I open the Day Operations Wizard for "2026-01-05"
    Then I should see reference values from previous day:
      | ingredient  | previous_closing |
      | Mięso kebab | 45.0             |
      | Chleb pita  | 80               |
      | Warzywa     | 15.0             |

  # ===========================================
  # DAY OPERATIONS WIZARD - MID-DAY
  # ===========================================

  @wizard @mid-day @happy-path
  Scenario: Record warehouse to kitchen transfer
    Given day "2026-01-05" is open and on Step 2 "Operacje"
    And warehouse has:
      | ingredient  | quantity |
      | Mięso kebab | 100.0    |
    When I click "Dodaj transfer"
    And I select "Mięso kebab"
    And I enter quantity "20.0"
    And I click "Zapisz transfer"
    Then I should see a transfer record for "Mięso kebab" with quantity "20.0"
    And warehouse stock of "Mięso kebab" should be "80.0"
    And the transfer should increase kitchen available stock

  @wizard @mid-day @error-handling
  Scenario: Cannot transfer more than warehouse stock
    Given day "2026-01-05" is open
    And warehouse has "Mięso kebab" with quantity "10.0"
    When I try to transfer "15.0" kg of "Mięso kebab"
    Then I should see error "Niewystarczająca ilość w magazynie (10.0 dostępne)"

  @wizard @mid-day @happy-path
  Scenario: Record spoilage
    Given day "2026-01-05" is open and on Step 2 "Operacje"
    When I click "Dodaj stratę"
    And I select "Warzywa"
    And I enter quantity "2.0"
    And I select reason "Przeterminowane"
    And I click "Zapisz"
    Then I should see a spoilage record for "Warzywa" with quantity "2.0"
    And reason should be "Przeterminowane"

  @wizard @mid-day @happy-path
  Scenario: Record delivery
    Given day "2026-01-05" is open and on Step 2 "Operacje"
    When I click "Dodaj dostawę"
    And I enter supplier "Hurtownia ABC"
    And I add delivery item:
      | ingredient  | quantity | unit_price |
      | Mięso kebab | 50.0     | 25.00      |
      | Chleb pita  | 200      | 0.50       |
    And I click "Zapisz dostawę"
    Then I should see a delivery from "Hurtownia ABC"
    And total delivery cost should be "1350.00" PLN
    And warehouse stock should be updated

  @wizard @mid-day
  Scenario: View mid-day operations summary
    Given day "2026-01-05" has:
      | operation  | count |
      | transfers  | 3     |
      | spoilages  | 1     |
      | deliveries | 2     |
    When I view the mid-day operations panel
    Then I should see summary:
      | operation  | count |
      | Transfery  | 3     |
      | Straty     | 1     |
      | Dostawy    | 2     |

  @wizard @mid-day
  Scenario: Proceed to closing step
    Given day "2026-01-05" is open and on Step 2 "Operacje"
    When I click "Przejdź do zamknięcia"
    Then I should move to Step 3 "Zamknięcie"

  # ===========================================
  # DAY OPERATIONS WIZARD - CLOSING
  # ===========================================

  @wizard @closing @happy-path
  Scenario: Enter closing inventory and see calculated sales
    Given day "2026-01-05" has:
      | type      | ingredient  | quantity |
      | opening   | Mięso kebab | 50.0     |
      | opening   | Chleb pita  | 100      |
      | transfer  | Mięso kebab | 20.0     |
      | delivery  | Chleb pita  | 50       |
      | spoilage  | Mięso kebab | 2.0      |
    And I am on Step 3 "Zamknięcie"
    When I enter closing inventory:
      | ingredient  | quantity |
      | Mięso kebab | 38.0     |
      | Chleb pita  | 50       |
    Then I should see calculated usage:
      | ingredient  | opening | transfers | deliveries | spoilage | closing | used |
      | Mięso kebab | 50.0    | 20.0      | 0          | 2.0      | 38.0    | 30.0 |
      | Chleb pita  | 100     | 0         | 50         | 0        | 50      | 100  |

  @wizard @closing @happy-path
  Scenario: View calculated sales from ingredient usage
    Given ingredient usage has been calculated:
      | ingredient  | used |
      | Mięso kebab | 30.0 |
      | Chleb pita  | 100  |
    And products have recipes:
      | product     | ingredient  | amount_per_unit |
      | Kebab duży  | Mięso kebab | 0.3             |
      | Kebab duży  | Chleb pita  | 1               |
    Then I should see estimated sales:
      | product    | quantity | unit_price | total_revenue |
      | Kebab duży | 100      | 25.00      | 2500.00       |

  @wizard @closing @happy-path @smoke
  Scenario: Close day successfully
    Given I have entered all closing inventory
    And calculated sales are displayed
    When I click "Zamknij dzień"
    Then the day "2026-01-05" should be marked as closed
    And I should see the day summary
    And all inventory snapshots should be saved

  @wizard @closing @edge-case
  Scenario: Closing inventory higher than expected (discrepancy)
    Given opening inventory of "Mięso kebab" was 50.0 kg
    And no transfers, deliveries, or spoilage for "Mięso kebab"
    When I enter closing inventory of "55.0" kg for "Mięso kebab"
    Then I should see a warning "Wykryto rozbieżność - stan końcowy większy niż oczekiwany"
    And I should be able to proceed with confirmation

  @wizard @closing @error-handling
  Scenario: Cannot close without all closing inventory
    Given I am on Step 3 "Zamknięcie"
    And I have entered closing inventory for some but not all ingredients
    When I click "Zamknij dzień"
    Then I should see error "Wprowadź stan końcowy dla wszystkich składników"

  # ===========================================
  # DAY LIFECYCLE
  # ===========================================

  @day-lifecycle @happy-path
  Scenario: Complete day lifecycle
    Given today is "2026-01-05"
    And shift templates exist for employees
    When I open day "2026-01-05"
    And I complete the opening step with shifts and inventory
    And I record mid-day operations (transfers, deliveries, spoilage)
    And I enter closing inventory
    And I close the day
    Then day "2026-01-05" should be "closed"
    And all operations should be saved
    And day summary should be accurate

  @day-lifecycle
  Scenario: Open past day
    Given today is "2026-01-10"
    And day "2026-01-08" has no record
    When I select day "2026-01-08" from the calendar
    And I click "Otwórz dzień"
    Then day "2026-01-08" should be opened
    And I should see suggested shifts for "2026-01-08" (Czwartek)

  @day-lifecycle
  Scenario: Reopen closed day
    Given day "2026-01-05" is closed
    When I click on day "2026-01-05"
    And I click "Otwórz ponownie"
    And I confirm with reason "Korekta błędnych danych"
    Then day "2026-01-05" should be reopened
    And a reopen audit log should be created
    And I should see the wizard in edit mode

  @day-lifecycle
  Scenario: Multiple days open simultaneously
    Given day "2026-01-05" is open
    When I open day "2026-01-06"
    Then both days should be open
    And I should see both in the "open days" list

  @day-lifecycle
  Scenario: View closed day summary
    Given day "2026-01-05" is closed
    When I click on day "2026-01-05"
    Then I should see the day summary view
    And summary should show:
      | section       | data                        |
      | Zmiany        | List of worked shifts       |
      | Inwentarz     | Opening and closing values  |
      | Operacje      | Transfers, spoilage, deliveries |
      | Sprzedaż      | Calculated sales and revenue |
      | Podsumowanie  | Total revenue, costs, profit |

  # ===========================================
  # INVENTORY LOCATIONS
  # ===========================================

  @inventory @warehouse
  Scenario: View warehouse inventory
    Given warehouse has:
      | ingredient  | quantity |
      | Mięso kebab | 100.0    |
      | Chleb pita  | 500      |
    When I navigate to warehouse inventory in Settings
    Then I should see:
      | ingredient  | quantity | unit |
      | Mięso kebab | 100.0    | kg   |
      | Chleb pita  | 500      | szt  |

  @inventory @warehouse
  Scenario: Initial warehouse stock setup
    Given I am in Settings
    And "Mięso kebab" has no warehouse stock
    When I set initial warehouse stock for "Mięso kebab" to "200.0" kg
    Then warehouse should show "Mięso kebab" with "200.0" kg

  @inventory @kitchen
  Scenario: Kitchen inventory tracked daily
    Given day "2026-01-05" opening inventory:
      | ingredient  | quantity |
      | Mięso kebab | 50.0     |
    And transfers to kitchen:
      | ingredient  | quantity |
      | Mięso kebab | 20.0     |
    Then available kitchen stock should be "70.0" kg before closing

  # ===========================================
  # ERROR HANDLING
  # ===========================================

  @error-handling
  Scenario: Handle network error during save
    Given I am completing the opening step
    And the network is unavailable
    When I click "Kontynuuj"
    Then I should see error "Błąd połączenia. Spróbuj ponownie."
    And my entered data should not be lost

  @error-handling @concurrent
  Scenario: Concurrent modification warning
    Given two users are editing day "2026-01-05"
    And User A saves changes
    When User B tries to save
    Then User B should see "Dane zostały zmienione przez innego użytkownika"
    And User B should be prompted to refresh

  # ===========================================
  # REPORTING
  # ===========================================

  @reports
  Scenario: Day summary shows all metrics
    Given day "2026-01-05" is closed with:
      | metric               | value    |
      | shifts_worked        | 3        |
      | total_hours          | 24       |
      | deliveries_cost      | 500.00   |
      | spoilage_cost        | 25.00    |
      | calculated_revenue   | 2500.00  |
    When I view the day summary for "2026-01-05"
    Then I should see:
      | label             | value       |
      | Pracownicy        | 3 osoby     |
      | Godziny pracy     | 24 godz.    |
      | Koszt dostaw      | 500,00 PLN  |
      | Straty            | 25,00 PLN   |
      | Przychód          | 2500,00 PLN |
      | Zysk brutto       | 1975,00 PLN |

  # ===========================================
  # PERFORMANCE
  # ===========================================

  @performance
  Scenario: Wizard loading performance
    Given the database contains 100 ingredients
    And the database contains 50 employees
    When I open the Day Operations Wizard
    Then the wizard should load in less than 2 seconds

  @performance
  Scenario: Sales calculation performance
    Given the day has 50 different ingredients tracked
    And complex recipe mappings exist
    When I enter closing inventory
    Then sales calculation should complete in less than 500ms
