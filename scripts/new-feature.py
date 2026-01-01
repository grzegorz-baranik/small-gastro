#!/usr/bin/env python3
"""
Skrypt do tworzenia struktury nowej funkcjonalności.
Tworzy katalogi i pliki szablonowe dla specyfikacji.

Użycie:
    python scripts/new-feature.py <nazwa-funkcjonalnosci>

Przykład:
    python scripts/new-feature.py user-authentication
"""

import argparse
import os
import shutil
import sys
from datetime import date
from pathlib import Path


def get_project_root() -> Path:
    """Znajdź katalog główny projektu."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".clinerules").exists() or (current / "CLAUDE.md").exists():
            return current
        current = current.parent
    return Path.cwd()


def create_feature_structure(feature_name: str, author: str = "AI Assistant") -> None:
    """
    Tworzy pełną strukturę katalogów i plików dla nowej funkcjonalności.

    Args:
        feature_name: Nazwa funkcjonalności (np. 'user-authentication')
        author: Imię autora specyfikacji
    """
    project_root = get_project_root()
    feature_dir = project_root / "docs" / "specs" / feature_name
    templates_dir = project_root / "docs" / "templates"
    bdd_dir = project_root / "tests" / "features"

    # Sprawdź czy funkcjonalność już istnieje
    if feature_dir.exists():
        print(f"❌ Błąd: Funkcjonalność '{feature_name}' już istnieje w {feature_dir}")
        sys.exit(1)

    # Sprawdź czy szablony istnieją
    if not templates_dir.exists():
        print(f"❌ Błąd: Katalog szablonów nie istnieje: {templates_dir}")
        print("Upewnij się, że projekt jest poprawnie skonfigurowany.")
        sys.exit(1)

    print(f"📁 Tworzenie struktury dla funkcjonalności: {feature_name}")
    print(f"   Lokalizacja: {feature_dir}")
    print()

    # Utwórz katalog funkcjonalności
    feature_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Utworzono katalog: {feature_dir}")

    # Utwórz katalog dla testów BDD
    bdd_dir.mkdir(parents=True, exist_ok=True)

    # Data utworzenia
    today = date.today().isoformat()

    # Skopiuj i dostosuj szablony
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
            # Zamień placeholdery
            content = content.replace("{Nazwa Funkcjonalności}", feature_name.replace("-", " ").title())
            content = content.replace("{imię i nazwisko}", author)
            content = content.replace("{YYYY-MM-DD}", today)
            content = content.replace("{data}", today)
            content = content.replace("{autor}", author)

            output_path.write_text(content, encoding="utf-8")
            print(f"✅ Utworzono: {output_path.name}")
        else:
            print(f"⚠️ Pominięto (brak szablonu): {template_name}")

    # Skopiuj szablon BDD
    bdd_template = templates_dir / "bdd-scenarios.feature"
    bdd_output = feature_dir / "scenarios.feature"
    bdd_tests_output = bdd_dir / f"{feature_name}.feature"

    if bdd_template.exists():
        content = bdd_template.read_text(encoding="utf-8")
        # Zamień placeholdery
        content = content.replace("{Nazwa funkcjonalności}", feature_name.replace("-", " ").title())
        content = content.replace("{tag-funkcjonalności}", feature_name.replace("-", "_"))

        # Zapisz w katalogu specyfikacji
        bdd_output.write_text(content, encoding="utf-8")
        print(f"✅ Utworzono: scenarios.feature")

        # Zapisz też w katalogu testów
        bdd_tests_output.write_text(content, encoding="utf-8")
        print(f"✅ Utworzono: tests/features/{feature_name}.feature")

    print()
    print("=" * 60)
    print("🎉 Struktura funkcjonalności została utworzona!")
    print("=" * 60)
    print()
    print("📋 Następne kroki:")
    print()
    print(f"1. Uzupełnij specyfikację funkcjonalną:")
    print(f"   {feature_dir / 'README.md'}")
    print()
    print(f"2. Uzupełnij specyfikację techniczną:")
    print(f"   {feature_dir / 'TECHNICAL.md'}")
    print()
    print(f"3. Napisz scenariusze BDD:")
    print(f"   {feature_dir / 'scenarios.feature'}")
    print()
    print(f"4. Uzupełnij plan testów:")
    print(f"   {feature_dir / 'TESTING.md'}")
    print()
    print("⚠️ PAMIĘTAJ: Nie rozpoczynaj implementacji przed zatwierdzeniem specyfikacji!")
    print()


def list_features() -> None:
    """Wyświetla listę istniejących funkcjonalności."""
    project_root = get_project_root()
    specs_dir = project_root / "docs" / "specs"

    if not specs_dir.exists():
        print("Brak katalogu specs. Utwórz pierwszą funkcjonalność.")
        return

    features = [d.name for d in specs_dir.iterdir() if d.is_dir()]

    if not features:
        print("Brak zdefiniowanych funkcjonalności.")
        return

    print("📚 Istniejące funkcjonalności:")
    print()
    for feature in sorted(features):
        feature_path = specs_dir / feature
        readme = feature_path / "README.md"
        status = "✅" if readme.exists() else "⚠️"
        print(f"  {status} {feature}")


def main():
    parser = argparse.ArgumentParser(
        description="Tworzenie struktury nowej funkcjonalności",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Przykłady:
  python scripts/new-feature.py user-authentication
  python scripts/new-feature.py inventory-management --author "Jan Kowalski"
  python scripts/new-feature.py --list
        """,
    )

    parser.add_argument(
        "feature_name",
        nargs="?",
        help="Nazwa funkcjonalności (np. 'user-authentication')",
    )

    parser.add_argument(
        "--author",
        "-a",
        default="AI Assistant",
        help="Autor specyfikacji (domyślnie: AI Assistant)",
    )

    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="Wyświetl listę istniejących funkcjonalności",
    )

    args = parser.parse_args()

    if args.list:
        list_features()
        return

    if not args.feature_name:
        parser.print_help()
        print()
        print("❌ Błąd: Podaj nazwę funkcjonalności lub użyj --list")
        sys.exit(1)

    # Walidacja nazwy
    feature_name = args.feature_name.lower().strip()
    if not feature_name.replace("-", "").replace("_", "").isalnum():
        print("❌ Błąd: Nazwa funkcjonalności może zawierać tylko litery, cyfry i myślniki")
        sys.exit(1)

    create_feature_structure(feature_name, args.author)


if __name__ == "__main__":
    main()
