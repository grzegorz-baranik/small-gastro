# language: en
# encoding: utf-8

# BDD Scenario Template for the small-gastro project
# Use this template as a basis for new features
# Note: English Gherkin keywords are used (Polish is ONLY for UI labels)

@sales_tracking_hybrid
Feature: Sales Tracking Hybrid
  As a {user role}
  I want to {action/capability}
  So that {benefit/business goal}

  Background:
    # Common steps for all scenarios in this feature
    Given the database is empty
    And I am logged in as "{role}"

  # ============================================
  # POSITIVE SCENARIOS (Happy Path)
  # ============================================

  @happy-path @smoke
  Scenario: {Basic success scenario}
    Given {precondition}
    When {user action}
    Then {expected result}
    And {additional verification}

  @happy-path
  Scenario: {Second success scenario}
    Given {precondition}
    When {user action}
    Then {expected result}

  # ============================================
  # DATA-DRIVEN SCENARIOS (Scenario Outline)
  # ============================================

  @parametrized
  Scenario Outline: {Name with parameters}
    Given there exists a {object} named "<name>"
    When I change {field} to "<new_value>"
    Then {field} should have value "<new_value>"

    Examples:
      | name      | new_value |
      | Example1  | Value1    |
      | Example2  | Value2    |
      | Example3  | Value3    |

  # ============================================
  # ERROR SCENARIOS
  # ============================================

  @error-handling
  Scenario: Validation error - {error description}
    Given I am on the {page name} page
    When I try to create {object} with an empty "{field}" field
    Then I should see error message "{Field is required}"
    And {object} should not be created

  @error-handling
  Scenario: Validation error - invalid format
    Given I am on the {page name} page
    When I enter "{invalid_value}" in the "{field}" field
    Then I should see error message "{Invalid format}"

  @error-handling @404
  Scenario: Attempt to access non-existent resource
    When I try to view {object} with ID 99999
    Then I should see message "Not found"
    And I am redirected to {main page/list}

  # ============================================
  # EDGE CASES
  # ============================================

  @edge-case
  Scenario: {Edge case name}
    Given {special condition}
    When {action}
    Then {expected behavior in this case}

  @edge-case @concurrent
  Scenario: Concurrent modification of the same resource
    Given two users are editing the same {object}
    When the first user saves changes
    And the second user tries to save their changes
    Then the second user should see a conflict message

  # ============================================
  # PERFORMANCE
  # ============================================

  @performance
  Scenario: List loading performance
    Given the database contains 1000 {objects}
    When I open the {objects} list page
    Then the page should load in less than 2 seconds
    And I should see pagination

  # ============================================
  # SECURITY
  # ============================================

  @security
  Scenario: Access attempt without permissions
    Given I am logged in as a user without permissions
    When I try to access {protected function}
    Then I should see message "Access denied"
    And I should not see {protected data}

# ============================================
# EXAMPLES FOR SMALL-GASTRO PROJECT
# ============================================

# Below are example scenarios specific to small-gastro

@ingredients
Feature: Ingredient Management
  As a food establishment owner
  I want to manage the list of ingredients
  So that I can control inventory levels

  @happy-path @smoke
  Scenario: Adding a new weight-based ingredient
    Given I am on the "Ingredients" page
    When I click the "Add ingredient" button
    And I enter name "Iceberg lettuce"
    And I select unit "kg"
    And I click "Save"
    Then ingredient "Iceberg lettuce" should appear on the list
    And it should have unit "kg"

  @happy-path
  Scenario: Adding a new count-based ingredient
    Given I am on the "Ingredients" page
    When I click the "Add ingredient" button
    And I enter name "Burger bun"
    And I select unit "pcs"
    And I click "Save"
    Then ingredient "Burger bun" should appear on the list
    And it should have unit "pcs"

  @error-handling
  Scenario: Error - attempt to add ingredient with existing name
    Given ingredient "Tomato" exists
    When I try to add ingredient with name "Tomato"
    Then I should see message "Ingredient with this name already exists"
    And new ingredient should not be created

@products
Feature: Product Management
  As a food establishment owner
  I want to create products with assigned ingredients
  So that I can track ingredient usage during sales

  @happy-path
  Scenario: Creating a product with assigned ingredients
    Given the following ingredients exist:
      | name        | unit |
      | Burger bun  | pcs  |
      | Meat        | kg   |
      | Lettuce     | kg   |
    When I create product "Burger Classic" priced at 25.00 PLN
    And I assign ingredients:
      | ingredient  | quantity |
      | Burger bun  | 1        |
      | Meat        | 0.15     |
      | Lettuce     | 0.02     |
    Then product "Burger Classic" should be created
    And it should have 3 assigned ingredients

@daily-report
Feature: Day Open and Close
  As a restaurant employee
  I want to open and close the work day
  So that I can track inventory levels at the beginning and end of the day

  @happy-path @smoke
  Scenario: Opening a new day
    Given the previous day has been closed
    When I open a new day
    And I enter initial ingredient quantities
    Then a new day record should be created
    And initial quantities should be saved

  @edge-case
  Scenario: Attempt to open day when previous is not closed
    Given the previous day has not been closed
    When I try to open a new day
    Then I should see message "Close the previous day first"
    And new day should not be opened
