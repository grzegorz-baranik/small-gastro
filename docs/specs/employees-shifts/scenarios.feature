# language: en
# encoding: utf-8

@employees-shifts
Feature: Employees & Shifts Management
  As a gastro business owner
  I want to manage employees, their positions, and shift assignments
  So that I can track who works when and manage labor costs

  Background:
    Given I am logged in as owner
    And I am on the settings page

  # ============================================
  # POSITION MANAGEMENT
  # ============================================

  @positions @happy-path @smoke
  Scenario: Create a new position with default rate
    Given no positions exist in the system
    When I click the "Add position" button
    And I enter "Cook" as the position name
    And I enter "25.00" as the hourly rate
    And I click the "Save" button
    Then I should see "Cook" in the positions list
    And the hourly rate should show "25.00 PLN/h"

  @positions @happy-path
  Scenario: Edit an existing position
    Given a position "Cook" exists with rate "25.00"
    When I click the edit button for position "Cook"
    And I change the hourly rate to "27.00"
    And I click the "Save" button
    Then the hourly rate for "Cook" should show "27.00 PLN/h"

  @positions @validation
  Scenario: Cannot create position with duplicate name
    Given a position "Cook" exists with rate "25.00"
    When I click the "Add position" button
    And I enter "Cook" as the position name
    And I enter "30.00" as the hourly rate
    And I click the "Save" button
    Then I should see error message "Position with this name already exists"

  @positions @validation
  Scenario: Cannot delete position with assigned employees
    Given a position "Cook" exists with rate "25.00"
    And an employee "John Smith" exists with position "Cook"
    When I click the delete button for position "Cook"
    Then I should see error message "Cannot delete position with assigned employees"
    And position "Cook" should still exist in the list

  @positions @happy-path
  Scenario: Delete position without employees
    Given a position "Helper" exists with rate "20.00"
    And no employees are assigned to position "Helper"
    When I click the delete button for position "Helper"
    Then position "Helper" should not exist in the list

  # ============================================
  # EMPLOYEE MANAGEMENT
  # ============================================

  @employees @happy-path @smoke
  Scenario: Create employee with position's default rate
    Given a position "Cashier" exists with rate "22.00"
    When I click the "Add employee" button
    And I enter "Anna Smith" as the name
    And I select "Cashier" as the position
    And I leave the hourly rate field empty
    And I click the "Save" button
    Then I should see "Anna Smith" in the employees list
    And the employee's hourly rate should show "22.00 PLN/h"

  @employees @happy-path
  Scenario: Create employee with custom hourly rate
    Given a position "Cashier" exists with rate "22.00"
    When I click the "Add employee" button
    And I enter "Peter Smith" as the name
    And I select "Cashier" as the position
    And I enter "24.50" as the hourly rate
    And I click the "Save" button
    Then I should see "Peter Smith" in the employees list
    And the employee's hourly rate should show "24.50 PLN/h"

  @employees @happy-path
  Scenario: Deactivate an employee
    Given an active employee "John Smith" exists
    When I click the deactivate button for employee "John Smith"
    Then employee "John Smith" should be marked as inactive
    And employee "John Smith" should be hidden from the active employees list

  @employees @happy-path
  Scenario: Reactivate an inactive employee
    Given an inactive employee "John Smith" exists
    And I enable showing inactive employees
    When I click the activate button for employee "John Smith"
    Then employee "John Smith" should be marked as active

  @employees @filtering
  Scenario: Filter employees by active status
    Given an active employee "John Smith" exists
    And an inactive employee "Anna Smith" exists
    When I am on the settings page
    Then I should see "John Smith" in the employees list
    And I should not see "Anna Smith" in the employees list
    When I enable showing inactive employees
    Then I should see both "John Smith" and "Anna Smith" in the list

  @employees @validation
  Scenario: Cannot delete employee with wage history
    Given an employee "John Smith" exists
    And a wage transaction exists for employee "John Smith"
    When I try to delete employee "John Smith"
    Then I should see error message "Cannot delete employee with wage history. You can deactivate them."

  # ============================================
  # SHIFT ASSIGNMENTS
  # ============================================

  @shifts @daily-operations @happy-path @smoke
  Scenario: Add employee to current day's shift
    Given an open daily record exists for today
    And an active employee "John Smith" exists
    When I go to the daily operations page
    And I click the "Add employee to shift" button
    And I select "John Smith" from the employee dropdown
    And I set start time to "08:00"
    And I set end time to "16:00"
    And I click the "Add" button
    Then I should see "John Smith" in the shift assignments
    And the hours worked should show "8.0"

  @shifts @daily-operations @happy-path
  Scenario: Add multiple employees to the same shift
    Given an open daily record exists for today
    And active employees "John Smith" and "Anna Smith" exist
    When I go to the daily operations page
    And I add "John Smith" with times "08:00" to "16:00"
    And I add "Anna Smith" with times "10:00" to "18:00"
    Then I should see both employees in the shift assignments
    And "John Smith" should show 8.0 hours
    And "Anna Smith" should show 8.0 hours

  @shifts @validation
  Scenario: Cannot add shift with end time before start time
    Given an open daily record exists for today
    And an active employee "John Smith" exists
    When I go to the daily operations page
    And I click the "Add employee to shift" button
    And I select "John Smith" from the employee dropdown
    And I set start time to "16:00"
    And I set end time to "08:00"
    And I click the "Add" button
    Then I should see error message "End time must be after start time"

  @shifts @validation
  Scenario: Cannot close day without at least one employee
    Given an open daily record exists for today
    And no shift assignments exist for today
    When I go to the daily operations page
    And I try to close the day
    Then I should see warning message "You must add at least one employee to the shift"
    And the day should remain open

  @shifts @daily-operations @happy-path
  Scenario: Successfully close day with assigned employees
    Given an open daily record exists for today
    And "John Smith" is assigned to today's shift from "08:00" to "16:00"
    When I go to the daily operations page
    And I click the "Close day" button
    Then the day should be marked as closed
    And I should not be able to modify shift assignments

  @shifts @daily-operations
  Scenario: Cannot modify shifts after day is closed
    Given a closed daily record exists for today
    And "John Smith" is assigned to today's shift
    When I go to the daily operations page
    Then the shift assignment list should be read-only
    And I should not see the "Add employee to shift" button

  @shifts @daily-operations @happy-path
  Scenario: Edit shift times while day is open
    Given an open daily record exists for today
    And "John Smith" is assigned from "08:00" to "16:00"
    When I go to the daily operations page
    And I change "John Smith"'s end time to "17:00"
    And I click the "Save" button
    Then the hours worked for "John Smith" should show "9.0"

  @shifts @daily-operations @happy-path
  Scenario: Remove employee from shift while day is open
    Given an open daily record exists for today
    And "John Smith" is assigned to today's shift
    And "Anna Smith" is assigned to today's shift
    When I go to the daily operations page
    And I click the remove button for "John Smith"'s shift
    Then "John Smith" should not appear in shift assignments
    And "Anna Smith" should still appear in shift assignments

  # ============================================
  # WAGE TRANSACTIONS
  # ============================================

  @wages @finances @happy-path @smoke
  Scenario: Create wage transaction for an employee
    Given an employee "John Smith" exists
    And a "Wages" expense category exists
    When I go to the finances page
    And I click the "Add expense" button
    And I select "Wages" as the category
    Then I should see the employee dropdown appear
    When I select "John Smith" as the employee
    And I select "Monthly" as the period type
    And I enter "4500.00" as the amount
    And I click the "Save" button
    Then the wage transaction should be created
    And it should be linked to employee "John Smith"

  @wages @finances @happy-path
  Scenario: Calculate wages from recorded shift hours
    Given an employee "John Smith" exists with hourly rate "25.00"
    And "John Smith" has worked 40 hours in the current week
    When I go to the finances page
    And I create a wage transaction for "John Smith"
    And I select "Weekly" as the period type
    And I click the "Calculate from hours" button
    Then the amount field should show "1000.00"

  @wages @validation
  Scenario: Cannot create wage transaction without selecting employee
    Given a "Wages" expense category exists
    When I go to the finances page
    And I click the "Add expense" button
    And I select "Wages" as the category
    And I enter "4500.00" as the amount
    And I click "Save" without selecting an employee
    Then I should see error message "Select an employee for wage transaction"

  @wages @finances
  Scenario: Show message when no shifts recorded for calculation period
    Given an employee "John Smith" exists
    And "John Smith" has no recorded shifts in the current month
    When I create a wage transaction for "John Smith"
    And I select "Monthly" as the period type
    And I click the "Calculate from hours" button
    Then I should see message "No recorded hours in selected period"
    And the amount field should remain empty

  # ============================================
  # WAGE ANALYTICS
  # ============================================

  @analytics @reports @happy-path @smoke
  Scenario: View monthly wage analytics for all employees
    Given employees with wage transactions exist for the current month
    When I go to the reports page
    And I select the "Wages" tab
    And I select the current month
    Then I should see the total wages summary
    And I should see the total hours worked
    And I should see the average cost per hour
    And I should see a breakdown by employee

  @analytics @reports @happy-path
  Scenario: Filter wage analytics by specific employee
    Given employees "John Smith" and "Anna Smith" have wage data
    When I go to the wage analytics section
    And I select "John Smith" from the employee filter
    Then I should only see data for "John Smith"
    And the summary should reflect only "John Smith"'s totals

  @analytics @reports @happy-path
  Scenario: Compare current month to previous month
    Given wage data exists for current and previous month
    When I go to the wage analytics section
    And I select the current month
    Then I should see the previous month comparison
    And I should see percentage change for each employee

  @analytics @reports
  Scenario: View analytics with no data for selected period
    Given no wage transactions exist for December 2025
    When I go to the wage analytics section
    And I select December 2025
    Then I should see a message "No data for selected period"
    And the summary should show zeros

  # ============================================
  # EDGE CASES
  # ============================================

  @edge-cases
  Scenario: Deactivate employee currently on shift
    Given an open daily record exists for today
    And "John Smith" is assigned to today's shift
    When I go to settings and deactivate "John Smith"
    Then "John Smith" should remain in today's shift assignments
    But "John Smith" should not appear in the employee dropdown for new shifts

  @edge-cases
  Scenario: Change employee's position updates future rate calculations
    Given an employee "John Smith" exists with position "Helper" at "20.00/h"
    And a position "Cook" exists with hourly rate "25.00"
    When I change "John Smith"'s position to "Cook"
    And "John Smith" works a new shift
    Then the shift should calculate wages at "25.00/h"

  @edge-cases
  Scenario: Employee with custom rate keeps rate after position change
    Given an employee "John Smith" exists with custom rate "27.00"
    And "John Smith"'s current position is "Cook" at "25.00"
    When I change "John Smith"'s position to "Cashier" at "22.00"
    Then "John Smith"'s effective rate should still be "27.00"

  # ============================================
  # PARAMETERIZED SCENARIOS
  # ============================================

  @positions @parameterized
  Scenario Outline: Creating positions with different rates
    Given I am on the position management page
    When I create position "<name>" with rate "<rate>"
    Then the position should exist with rate "<rate> PLN/h"

    Examples:
      | name     | rate  |
      | Cook     | 25.00 |
      | Cashier  | 22.00 |
      | Helper   | 18.50 |
      | Manager  | 35.00 |

  @wages @parameterized
  Scenario Outline: Calculating wages for different periods
    Given employee "John Smith" has rate "25.00" per hour
    And worked "<hours>" hours in period "<period>"
    When I calculate wages for period "<period>"
    Then the calculated amount should be "<amount>" PLN

    Examples:
      | period    | hours | amount  |
      | Daily     | 8     | 200.00  |
      | Weekly    | 40    | 1000.00 |
      | Bi-weekly | 80    | 2000.00 |
      | Monthly   | 168   | 4200.00 |
