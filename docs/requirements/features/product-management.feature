# language: en
@product-management
Feature: Product Management
  As an owner
  I want to define products with variants and recipes
  So that the system can calculate sales from ingredient usage

  Background:
    Given I am logged in as the owner
    And the following ingredients exist:
      | name        | unit_type | unit_label |
      | Meat        | weight    | kg         |
      | Tortilla    | count     | szt        |
      | Onion       | weight    | kg         |
      | Sauce       | weight    | kg         |
      | Hot dog bun | count     | szt        |
      | Sausage     | count     | szt        |

  @happy-path @variants
  Scenario: Create a product with multiple variants
    When I navigate to "Products"
    And I click "Add Product"
    And I enter name "Kebab"
    And I enable "Has Variants"
    And I add variant "Small" with price 22.00 PLN
    And I add variant "Medium" with price 25.00 PLN
    And I add variant "Large" with price 28.00 PLN
    And I click "Save Product"
    Then the product should be created with 3 variants
    And I should see "Kebab" in the product list

  @happy-path @recipe
  Scenario: Define recipe for a product variant
    Given product "Kebab" exists with variant "Large"
    When I navigate to edit "Kebab Large"
    And I add ingredient "Tortilla" amount "1" and mark as primary
    And I add ingredient "Meat" amount "0.15" (150g)
    And I add ingredient "Onion" amount "0.05" (50g)
    And I add ingredient "Sauce" amount "0.03" (30g)
    And I click "Save Recipe"
    Then the recipe should be saved
    And Tortilla should be marked as the primary ingredient
    And the recipe should show 4 ingredients

  @happy-path @single-size
  Scenario: Create single-size product (no variants)
    When I navigate to "Products"
    And I click "Add Product"
    And I enter name "Hot Dog"
    And I leave "Has Variants" disabled
    And I enter price 12.00 PLN
    And I click "Save Product"
    Then the product should be created without explicit variants
    And it should have a single implicit variant with the product name
    When I navigate to edit "Hot Dog"
    And I add ingredient "Hot dog bun" amount "1" and mark as primary
    And I add ingredient "Sausage" amount "1"
    And I click "Save Recipe"
    Then the recipe should be saved

  @validation @primary-ingredient
  Scenario: Each variant must have a primary ingredient
    Given product "Kebab" exists with variant "Large" and no recipe
    When I navigate to edit "Kebab Large"
    And I add ingredient "Meat" amount "0.15" without marking as primary
    And I add ingredient "Tortilla" amount "1" without marking as primary
    And I click "Save Recipe"
    Then I should see error "Wybierz skladnik glowny do obliczania sprzedazy"
    And the recipe should not be saved

  @validation @negative
  Scenario: Product price must be positive
    When I navigate to "Products"
    And I click "Add Product"
    And I enter name "Test Product"
    And I enter price "0"
    And I click "Save Product"
    Then I should see error "Cena produktu musi byc wieksza od zera"
    And the product should not be saved

  @validation @negative
  Scenario: Recipe ingredient amount must be positive
    Given product "Kebab" exists with variant "Large"
    When I navigate to edit "Kebab Large"
    And I add ingredient "Meat" amount "0"
    And I click "Save Recipe"
    Then I should see error "Ilosc skladnika musi byc wieksza od zera"

  @soft-delete
  Scenario: Deactivate a product
    Given product "Old Special" exists and is active
    When I navigate to "Products"
    And I click "Deactivate" for "Old Special"
    Then the product should be marked as inactive
    And it should not appear in active products list
    And it should still be visible in historical reports
    And it should not be included in new sales calculations

  @soft-delete
  Scenario: Reactivate a deactivated product
    Given product "Old Special" exists and is inactive
    When I navigate to "Products"
    And I filter by "Show inactive"
    And I click "Activate" for "Old Special"
    Then the product should be marked as active
    And it should appear in active products list

  @edit
  Scenario: Edit product variant price
    Given product "Kebab" exists with variant "Large" at price 28.00 PLN
    When I navigate to edit "Kebab Large"
    And I change the price to 30.00 PLN
    And I click "Save"
    Then the price should be updated
    And new sales should use the updated price
    And historical sales should retain the old price

  @edit @recipe
  Scenario: Modify recipe ingredients
    Given product "Kebab Large" has recipe with Meat 0.15 kg
    When I navigate to edit "Kebab Large" recipe
    And I change Meat amount from 0.15 to 0.18 kg
    And I click "Save Recipe"
    Then the recipe should be updated
    And future calculations should use 0.18 kg per kebab

  @validation @unique-name
  Scenario: Product name must be unique
    Given product "Kebab" already exists
    When I navigate to "Products"
    And I click "Add Product"
    And I enter name "Kebab"
    And I click "Save Product"
    Then I should see error "Produkt o tej nazwie juz istnieje"
    And the product should not be created

  @ux
  Scenario: View all products with their variants
    Given the following products exist:
      | name    | variants              |
      | Kebab   | Small, Medium, Large  |
      | Hot Dog | (single size)         |
      | Burger  | Regular, Double       |
    When I navigate to "Products"
    Then I should see all products listed
    And I should see variant counts for each product
    And I should be able to expand to see variant details

  @calculation-integration
  Scenario: Product with recipe is used in sales calculation
    Given product "Kebab Large" exists with recipe:
      | ingredient | amount | is_primary |
      | Tortilla   | 1      | true       |
      | Meat       | 0.15   | false      |
    And today is open
    And 23 tortillas were used today (derived from inventory)
    When I close the day
    Then the system should calculate 23 "Kebab Large" sold
    And revenue should be 23 x 28.00 = 644 PLN
