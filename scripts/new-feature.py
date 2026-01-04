#!/usr/bin/env python3
"""
Script for creating new feature structure.
Creates directories and template files for specifications.

Usage:
    python scripts/new-feature.py <feature-name>

Example:
    python scripts/new-feature.py user-authentication
"""

import argparse
import os
import shutil
import sys
from datetime import date
from pathlib import Path


def get_project_root() -> Path:
    """Find the project root directory."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".clinerules").exists() or (current / "CLAUDE.md").exists():
            return current
        current = current.parent
    return Path.cwd()


def create_feature_structure(feature_name: str, author: str = "AI Assistant") -> None:
    """
    Creates the full directory and file structure for a new feature.

    Args:
        feature_name: Name of the feature (e.g., 'user-authentication')
        author: Name of the specification author
    """
    project_root = get_project_root()
    feature_dir = project_root / "docs" / "specs" / feature_name
    templates_dir = project_root / "docs" / "templates"
    bdd_dir = project_root / "tests" / "features"

    # Check if feature already exists
    if feature_dir.exists():
        print(f"Error: Feature '{feature_name}' already exists at {feature_dir}")
        sys.exit(1)

    # Check if templates exist
    if not templates_dir.exists():
        print(f"Error: Templates directory does not exist: {templates_dir}")
        print("Make sure the project is properly configured.")
        sys.exit(1)

    print(f"Creating structure for feature: {feature_name}")
    print(f"   Location: {feature_dir}")
    print()

    # Create feature directory
    feature_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {feature_dir}")

    # Create BDD tests directory
    bdd_dir.mkdir(parents=True, exist_ok=True)

    # Creation date
    today = date.today().isoformat()

    # Copy and customize templates
    templates = [
        ("functional-spec.md", "README.md"),
        ("technical-spec.md", "TECHNICAL.md"),
        ("test-plan.md", "TESTING.md"),
    ]

    for template_name, output_name in templates:
        template_path = templates_dir / template_name
        output_path = feature_dir / output_name

        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            # Replace placeholders
            content = content.replace("{Feature Name}", feature_name.replace("-", " ").title())
            content = content.replace("{author}", author)
            content = content.replace("{YYYY-MM-DD}", today)
            content = content.replace("{date}", today)

            output_path.write_text(content, encoding="utf-8")
            print(f"Created: {output_path.name}")
        else:
            print(f"Skipped (no template): {template_name}")

    # Copy BDD template
    bdd_template = templates_dir / "bdd-scenarios.feature"
    bdd_output = feature_dir / "scenarios.feature"
    bdd_tests_output = bdd_dir / f"{feature_name}.feature"

    if bdd_template.exists():
        content = bdd_template.read_text(encoding="utf-8")
        # Replace placeholders
        content = content.replace("{Feature Name}", feature_name.replace("-", " ").title())
        content = content.replace("{feature-tag}", feature_name.replace("-", "_"))

        # Save in spec directory
        bdd_output.write_text(content, encoding="utf-8")
        print(f"Created: scenarios.feature")

        # Save in tests directory too
        bdd_tests_output.write_text(content, encoding="utf-8")
        print(f"Created: tests/features/{feature_name}.feature")

    print()
    print("=" * 60)
    print("Feature structure created successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print()
    print(f"1. Complete the functional specification:")
    print(f"   {feature_dir / 'README.md'}")
    print()
    print(f"2. Complete the technical specification:")
    print(f"   {feature_dir / 'TECHNICAL.md'}")
    print()
    print(f"3. Write BDD scenarios:")
    print(f"   {feature_dir / 'scenarios.feature'}")
    print()
    print(f"4. Complete the test plan:")
    print(f"   {feature_dir / 'TESTING.md'}")
    print()
    print("IMPORTANT: Do not start implementation before the specification is approved!")
    print()


def list_features() -> None:
    """Display list of existing features."""
    project_root = get_project_root()
    specs_dir = project_root / "docs" / "specs"

    if not specs_dir.exists():
        print("No specs directory. Create the first feature.")
        return

    features = [d.name for d in specs_dir.iterdir() if d.is_dir()]

    if not features:
        print("No features defined.")
        return

    print("Existing features:")
    print()
    for feature in sorted(features):
        feature_path = specs_dir / feature
        readme = feature_path / "README.md"
        status = "[OK]" if readme.exists() else "[!]"
        print(f"  {status} {feature}")


def main():
    parser = argparse.ArgumentParser(
        description="Create new feature structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/new-feature.py user-authentication
  python scripts/new-feature.py inventory-management --author "John Smith"
  python scripts/new-feature.py --list
        """,
    )

    parser.add_argument(
        "feature_name",
        nargs="?",
        help="Feature name (e.g., 'user-authentication')",
    )

    parser.add_argument(
        "--author",
        "-a",
        default="AI Assistant",
        help="Specification author (default: AI Assistant)",
    )

    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="Display list of existing features",
    )

    args = parser.parse_args()

    if args.list:
        list_features()
        return

    if not args.feature_name:
        parser.print_help()
        print()
        print("Error: Provide a feature name or use --list")
        sys.exit(1)

    # Validate name
    feature_name = args.feature_name.lower().strip()
    if not feature_name.replace("-", "").replace("_", "").isalnum():
        print("Error: Feature name can only contain letters, numbers, and hyphens")
        sys.exit(1)

    create_feature_structure(feature_name, args.author)


if __name__ == "__main__":
    main()
