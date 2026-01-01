#!/usr/bin/env python3
"""
Skrypt do sprawdzania pokrycia specyfikacji w projekcie.
Analizuje katalogi z kodem i sprawdza czy istnieją odpowiednie specyfikacje.

Użycie:
    python scripts/check-spec-coverage.py
    python scripts/check-spec-coverage.py --verbose
    python scripts/check-spec-coverage.py --json

Funkcjonalności:
- Sprawdzanie kompletności specyfikacji
- Wykrywanie nieudokumentowanych modułów
- Raportowanie statusu dokumentacji
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class SpecStatus:
    """Status specyfikacji dla funkcjonalności."""
    name: str
    path: Path
    has_readme: bool = False
    has_technical: bool = False
    has_testing: bool = False
    has_bdd: bool = False
    readme_sections: List[str] = field(default_factory=list)
    is_approved: bool = False

    @property
    def completeness(self) -> float:
        """Oblicza procent kompletności specyfikacji."""
        checks = [
            self.has_readme,
            self.has_technical,
            self.has_testing,
            self.has_bdd,
        ]
        return sum(checks) / len(checks) * 100

    @property
    def is_complete(self) -> bool:
        """Sprawdza czy specyfikacja jest kompletna."""
        return all([
            self.has_readme,
            self.has_technical,
            self.has_testing,
            self.has_bdd,
        ])


@dataclass
class CoverageReport:
    """Raport pokrycia specyfikacji."""
    specs: List[SpecStatus] = field(default_factory=list)
    undocumented_modules: List[str] = field(default_factory=list)
    orphaned_specs: List[str] = field(default_factory=list)

    @property
    def total_specs(self) -> int:
        return len(self.specs)

    @property
    def complete_specs(self) -> int:
        return sum(1 for s in self.specs if s.is_complete)

    @property
    def approved_specs(self) -> int:
        return sum(1 for s in self.specs if s.is_approved)

    @property
    def coverage_percentage(self) -> float:
        if not self.specs:
            return 0.0
        return sum(s.completeness for s in self.specs) / len(self.specs)


def get_project_root() -> Path:
    """Znajdź katalog główny projektu."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".clinerules").exists() or (current / "CLAUDE.md").exists():
            return current
        current = current.parent
    return Path.cwd()


def check_spec_approval(readme_path: Path) -> bool:
    """Sprawdza czy specyfikacja została zatwierdzona."""
    if not readme_path.exists():
        return False

    content = readme_path.read_text(encoding="utf-8")
    # Szukaj statusu "Zatwierdzony" lub "Approved"
    patterns = [
        r"\*\*Status\*\*.*?Zatwierdzony",
        r"\*\*Status\*\*.*?Approved",
        r"\| Status \|.*?Zatwierdzony",
        r"\| Status \|.*?Approved",
    ]
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def get_readme_sections(readme_path: Path) -> List[str]:
    """Pobiera listę sekcji z README."""
    if not readme_path.exists():
        return []

    content = readme_path.read_text(encoding="utf-8")
    # Znajdź wszystkie nagłówki ##
    sections = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)
    return sections


def analyze_spec_directory(spec_dir: Path) -> SpecStatus:
    """Analizuje katalog specyfikacji."""
    status = SpecStatus(
        name=spec_dir.name,
        path=spec_dir
    )

    readme_path = spec_dir / "README.md"
    status.has_readme = readme_path.exists()
    status.has_technical = (spec_dir / "TECHNICAL.md").exists()
    status.has_testing = (spec_dir / "TESTING.md").exists()
    status.has_bdd = (spec_dir / "scenarios.feature").exists()

    if status.has_readme:
        status.readme_sections = get_readme_sections(readme_path)
        status.is_approved = check_spec_approval(readme_path)

    return status


def find_backend_modules(project_root: Path) -> Set[str]:
    """Znajduje moduły backendowe w projekcie."""
    modules = set()

    # Sprawdź routery API
    api_dir = project_root / "backend" / "app" / "api" / "v1"
    if api_dir.exists():
        for file in api_dir.glob("*.py"):
            if file.name not in ("__init__.py", "deps.py"):
                module_name = file.stem
                # Konwertuj snake_case na kebab-case
                modules.add(module_name.replace("_", "-"))

    # Sprawdź serwisy
    services_dir = project_root / "backend" / "app" / "services"
    if services_dir.exists():
        for file in services_dir.glob("*.py"):
            if file.name not in ("__init__.py",):
                module_name = file.stem.replace("_service", "")
                modules.add(module_name.replace("_", "-"))

    return modules


def find_frontend_modules(project_root: Path) -> Set[str]:
    """Znajduje moduły frontendowe w projekcie."""
    modules = set()

    # Sprawdź strony
    pages_dir = project_root / "frontend" / "src" / "pages"
    if pages_dir.exists():
        for file in pages_dir.glob("*.tsx"):
            if file.name not in ("index.tsx",):
                # Usuń "Page" z nazwy
                page_name = file.stem.replace("Page", "")
                # Konwertuj PascalCase na kebab-case
                kebab = re.sub(r"(?<!^)(?=[A-Z])", "-", page_name).lower()
                modules.add(kebab)

    return modules


def generate_report(project_root: Path) -> CoverageReport:
    """Generuje raport pokrycia specyfikacji."""
    report = CoverageReport()

    specs_dir = project_root / "docs" / "specs"

    # Analizuj istniejące specyfikacje
    if specs_dir.exists():
        for spec_dir in specs_dir.iterdir():
            if spec_dir.is_dir():
                status = analyze_spec_directory(spec_dir)
                report.specs.append(status)

    # Znajdź moduły w kodzie
    backend_modules = find_backend_modules(project_root)
    frontend_modules = find_frontend_modules(project_root)
    all_modules = backend_modules | frontend_modules

    # Znajdź nazwy specyfikacji
    spec_names = {s.name for s in report.specs}

    # Znajdź nieudokumentowane moduły
    report.undocumented_modules = sorted(all_modules - spec_names)

    # Znajdź osierocone specyfikacje (bez kodu)
    # (Pomijamy - specyfikacje mogą być napisane przed kodem)

    return report


def print_report(report: CoverageReport, verbose: bool = False) -> None:
    """Wyświetla raport w formacie tekstowym."""
    print()
    print("=" * 70)
    print("📊 RAPORT POKRYCIA SPECYFIKACJI")
    print("=" * 70)
    print()

    # Podsumowanie
    print("📈 PODSUMOWANIE:")
    print(f"   Łączna liczba specyfikacji: {report.total_specs}")
    print(f"   Kompletne specyfikacje:     {report.complete_specs}")
    print(f"   Zatwierdzone specyfikacje:  {report.approved_specs}")
    print(f"   Średnie pokrycie:           {report.coverage_percentage:.1f}%")
    print()

    # Status specyfikacji
    if report.specs:
        print("📋 STATUS SPECYFIKACJI:")
        print()
        print(f"{'Funkcjonalność':<30} {'README':<8} {'TECH':<8} {'TEST':<8} {'BDD':<8} {'Status':<12}")
        print("-" * 82)

        for spec in sorted(report.specs, key=lambda s: s.name):
            readme = "✅" if spec.has_readme else "❌"
            tech = "✅" if spec.has_technical else "❌"
            test = "✅" if spec.has_testing else "❌"
            bdd = "✅" if spec.has_bdd else "❌"

            if spec.is_complete and spec.is_approved:
                status = "🟢 Gotowe"
            elif spec.is_complete:
                status = "🟡 Do zatwierdzenia"
            else:
                status = f"🔴 {spec.completeness:.0f}%"

            print(f"{spec.name:<30} {readme:<8} {tech:<8} {test:<8} {bdd:<8} {status:<12}")

        print()

    # Nieudokumentowane moduły
    if report.undocumented_modules:
        print("⚠️ NIEUDOKUMENTOWANE MODUŁY:")
        print("   Następujące moduły nie mają specyfikacji:")
        print()
        for module in report.undocumented_modules:
            print(f"   • {module}")
        print()
        print("   Użyj: python scripts/new-feature.py <nazwa>")
        print()

    # Szczegóły (verbose)
    if verbose and report.specs:
        print("📝 SZCZEGÓŁY SPECYFIKACJI:")
        print()
        for spec in sorted(report.specs, key=lambda s: s.name):
            print(f"   {spec.name}:")
            print(f"      Ścieżka: {spec.path}")
            print(f"      Kompletność: {spec.completeness:.0f}%")
            if spec.readme_sections:
                print(f"      Sekcje README: {', '.join(spec.readme_sections[:5])}")
                if len(spec.readme_sections) > 5:
                    print(f"                     ... i {len(spec.readme_sections) - 5} więcej")
            print()

    # Rekomendacje
    print("💡 REKOMENDACJE:")
    print()

    incomplete = [s for s in report.specs if not s.is_complete]
    if incomplete:
        print(f"   1. Uzupełnij brakujące dokumenty dla {len(incomplete)} specyfikacji")

    unapproved = [s for s in report.specs if s.is_complete and not s.is_approved]
    if unapproved:
        print(f"   2. Zatwierdź {len(unapproved)} kompletnych specyfikacji")

    if report.undocumented_modules:
        print(f"   3. Utwórz specyfikacje dla {len(report.undocumented_modules)} nieudokumentowanych modułów")

    if not incomplete and not unapproved and not report.undocumented_modules:
        print("   ✨ Wszystko w porządku! Dokumentacja jest kompletna.")

    print()
    print("=" * 70)


def print_json_report(report: CoverageReport) -> None:
    """Wyświetla raport w formacie JSON."""
    output = {
        "summary": {
            "total_specs": report.total_specs,
            "complete_specs": report.complete_specs,
            "approved_specs": report.approved_specs,
            "coverage_percentage": round(report.coverage_percentage, 2),
        },
        "specs": [
            {
                "name": s.name,
                "path": str(s.path),
                "has_readme": s.has_readme,
                "has_technical": s.has_technical,
                "has_testing": s.has_testing,
                "has_bdd": s.has_bdd,
                "completeness": round(s.completeness, 2),
                "is_approved": s.is_approved,
            }
            for s in report.specs
        ],
        "undocumented_modules": report.undocumented_modules,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(
        description="Sprawdzanie pokrycia specyfikacji w projekcie",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Wyświetl szczegółowy raport",
    )

    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Wyświetl raport w formacie JSON",
    )

    parser.add_argument(
        "--fail-incomplete",
        action="store_true",
        help="Zwróć kod błędu jeśli są niekompletne specyfikacje",
    )

    args = parser.parse_args()

    project_root = get_project_root()
    report = generate_report(project_root)

    if args.json:
        print_json_report(report)
    else:
        print_report(report, verbose=args.verbose)

    # Zwróć kod błędu jeśli wymagane
    if args.fail_incomplete:
        if report.complete_specs < report.total_specs:
            sys.exit(1)
        if report.undocumented_modules:
            sys.exit(1)


if __name__ == "__main__":
    main()
