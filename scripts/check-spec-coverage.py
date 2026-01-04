#!/usr/bin/env python3
"""
Script for checking specification coverage in the project.
Analyzes code directories and checks if corresponding specifications exist.

Usage:
    python scripts/check-spec-coverage.py
    python scripts/check-spec-coverage.py --verbose
    python scripts/check-spec-coverage.py --json

Features:
- Checking specification completeness
- Detecting undocumented modules
- Reporting documentation status
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
    """Specification status for a feature."""
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
        """Calculate specification completeness percentage."""
        checks = [
            self.has_readme,
            self.has_technical,
            self.has_testing,
            self.has_bdd,
        ]
        return sum(checks) / len(checks) * 100

    @property
    def is_complete(self) -> bool:
        """Check if specification is complete."""
        return all([
            self.has_readme,
            self.has_technical,
            self.has_testing,
            self.has_bdd,
        ])


@dataclass
class CoverageReport:
    """Specification coverage report."""
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
    """Find the project root directory."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".clinerules").exists() or (current / "CLAUDE.md").exists():
            return current
        current = current.parent
    return Path.cwd()


def check_spec_approval(readme_path: Path) -> bool:
    """Check if specification has been approved."""
    if not readme_path.exists():
        return False

    content = readme_path.read_text(encoding="utf-8")
    # Search for "Approved" status (English or Polish "Zatwierdzony")
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
    """Get list of sections from README."""
    if not readme_path.exists():
        return []

    content = readme_path.read_text(encoding="utf-8")
    # Find all ## headings
    sections = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)
    return sections


def analyze_spec_directory(spec_dir: Path) -> SpecStatus:
    """Analyze a specification directory."""
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
    """Find backend modules in the project."""
    modules = set()

    # Check API routers
    api_dir = project_root / "backend" / "app" / "api" / "v1"
    if api_dir.exists():
        for file in api_dir.glob("*.py"):
            if file.name not in ("__init__.py", "deps.py"):
                module_name = file.stem
                # Convert snake_case to kebab-case
                modules.add(module_name.replace("_", "-"))

    # Check services
    services_dir = project_root / "backend" / "app" / "services"
    if services_dir.exists():
        for file in services_dir.glob("*.py"):
            if file.name not in ("__init__.py",):
                module_name = file.stem.replace("_service", "")
                modules.add(module_name.replace("_", "-"))

    return modules


def find_frontend_modules(project_root: Path) -> Set[str]:
    """Find frontend modules in the project."""
    modules = set()

    # Check pages
    pages_dir = project_root / "frontend" / "src" / "pages"
    if pages_dir.exists():
        for file in pages_dir.glob("*.tsx"):
            if file.name not in ("index.tsx",):
                # Remove "Page" from name
                page_name = file.stem.replace("Page", "")
                # Convert PascalCase to kebab-case
                kebab = re.sub(r"(?<!^)(?=[A-Z])", "-", page_name).lower()
                modules.add(kebab)

    return modules


def generate_report(project_root: Path) -> CoverageReport:
    """Generate specification coverage report."""
    report = CoverageReport()

    specs_dir = project_root / "docs" / "specs"

    # Analyze existing specifications
    if specs_dir.exists():
        for spec_dir in specs_dir.iterdir():
            if spec_dir.is_dir():
                status = analyze_spec_directory(spec_dir)
                report.specs.append(status)

    # Find modules in code
    backend_modules = find_backend_modules(project_root)
    frontend_modules = find_frontend_modules(project_root)
    all_modules = backend_modules | frontend_modules

    # Get specification names
    spec_names = {s.name for s in report.specs}

    # Find undocumented modules
    report.undocumented_modules = sorted(all_modules - spec_names)

    # Find orphaned specifications (without code)
    # (Skipping - specs can be written before code)

    return report


def print_report(report: CoverageReport, verbose: bool = False) -> None:
    """Print report in text format."""
    print()
    print("=" * 70)
    print("SPECIFICATION COVERAGE REPORT")
    print("=" * 70)
    print()

    # Summary
    print("SUMMARY:")
    print(f"   Total specifications:    {report.total_specs}")
    print(f"   Complete specifications: {report.complete_specs}")
    print(f"   Approved specifications: {report.approved_specs}")
    print(f"   Average coverage:        {report.coverage_percentage:.1f}%")
    print()

    # Specification status
    if report.specs:
        print("SPECIFICATION STATUS:")
        print()
        print(f"{'Feature':<30} {'README':<8} {'TECH':<8} {'TEST':<8} {'BDD':<8} {'Status':<15}")
        print("-" * 85)

        for spec in sorted(report.specs, key=lambda s: s.name):
            readme = "[OK]" if spec.has_readme else "[X]"
            tech = "[OK]" if spec.has_technical else "[X]"
            test = "[OK]" if spec.has_testing else "[X]"
            bdd = "[OK]" if spec.has_bdd else "[X]"

            if spec.is_complete and spec.is_approved:
                status = "Ready"
            elif spec.is_complete:
                status = "Pending approval"
            else:
                status = f"{spec.completeness:.0f}% complete"

            print(f"{spec.name:<30} {readme:<8} {tech:<8} {test:<8} {bdd:<8} {status:<15}")

        print()

    # Undocumented modules
    if report.undocumented_modules:
        print("UNDOCUMENTED MODULES:")
        print("   The following modules have no specifications:")
        print()
        for module in report.undocumented_modules:
            print(f"   - {module}")
        print()
        print("   Use: python scripts/new-feature.py <name>")
        print()

    # Details (verbose)
    if verbose and report.specs:
        print("SPECIFICATION DETAILS:")
        print()
        for spec in sorted(report.specs, key=lambda s: s.name):
            print(f"   {spec.name}:")
            print(f"      Path: {spec.path}")
            print(f"      Completeness: {spec.completeness:.0f}%")
            if spec.readme_sections:
                print(f"      README sections: {', '.join(spec.readme_sections[:5])}")
                if len(spec.readme_sections) > 5:
                    print(f"                       ... and {len(spec.readme_sections) - 5} more")
            print()

    # Recommendations
    print("RECOMMENDATIONS:")
    print()

    incomplete = [s for s in report.specs if not s.is_complete]
    if incomplete:
        print(f"   1. Complete missing documents for {len(incomplete)} specifications")

    unapproved = [s for s in report.specs if s.is_complete and not s.is_approved]
    if unapproved:
        print(f"   2. Approve {len(unapproved)} complete specifications")

    if report.undocumented_modules:
        print(f"   3. Create specifications for {len(report.undocumented_modules)} undocumented modules")

    if not incomplete and not unapproved and not report.undocumented_modules:
        print("   All good! Documentation is complete.")

    print()
    print("=" * 70)


def print_json_report(report: CoverageReport) -> None:
    """Print report in JSON format."""
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
        description="Check specification coverage in the project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Display detailed report",
    )

    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Display report in JSON format",
    )

    parser.add_argument(
        "--fail-incomplete",
        action="store_true",
        help="Return error code if there are incomplete specifications",
    )

    args = parser.parse_args()

    project_root = get_project_root()
    report = generate_report(project_root)

    if args.json:
        print_json_report(report)
    else:
        print_report(report, verbose=args.verbose)

    # Return error code if required
    if args.fail_incomplete:
        if report.complete_specs < report.total_specs:
            sys.exit(1)
        if report.undocumented_modules:
            sys.exit(1)


if __name__ == "__main__":
    main()
