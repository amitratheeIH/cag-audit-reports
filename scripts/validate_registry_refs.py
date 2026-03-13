#!/usr/bin/env python3
"""
validate_registry_refs.py
-------------------------
Checks that every registry ID referenced in report files exists in the
corresponding registry / taxonomy file.

Checks:
  - state_ut.id                  → registry_states_uts.json
  - examination_coverage.state_ut_ids[] → registry_states_uts.json
  - main_audited_entities[]      → registry_entities.json
  - other_audited_entities[]     → registry_entities.json
  - primary_schemes[]            → registry_schemes.json
  - other_schemes[]              → registry_schemes.json
  - report_sector[]              → taxonomy_report_sector.json
  - audit_type[]                 → taxonomy_audit_type.json
  - product_type                 → taxonomy_product_types.json
  - audit_findings_categories[]  → taxonomy_audit_findings_{product_type}.json
                                   (product-type-specific; file looked up from manifest.product_type)

Usage:
    python scripts/validate_registry_refs.py
    python scripts/validate_registry_refs.py --product-id AR06-CAG-2023-STATE-MP
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_layout as rl


def load_registry_ids(filename: str, id_field: str = "id") -> set[str]:
    path = rl.TAXONOMIES_DIR / filename
    data = json.loads(path.read_text())
    entries = data.get("entries", data) if isinstance(data, dict) else data
    return {e[id_field] for e in entries if id_field in e}


FINDINGS_TAXONOMY_FILENAME = "taxonomy_audit_findings_{product_type}.json"


def audit_findings_taxonomy_filename(product_type: str) -> str:
    """
    Returns the findings taxonomy filename for a given product_type.
    Convention: taxonomy_audit_findings_{product_type}.json
    e.g. audit_report → taxonomy_audit_findings_audit_report.json
    """
    return FINDINGS_TAXONOMY_FILENAME.format(product_type=product_type)


def load_audit_findings_ids(product_type: str | None) -> set[str] | None:
    """
    Load audit findings category IDs for the given product_type.
    Returns None if product_type is unknown or the file does not exist yet.
    """
    if not product_type:
        return None
    fname = audit_findings_taxonomy_filename(product_type)
    path = rl.TAXONOMIES_DIR / fname
    if not path.exists():
        return None   # file not built yet for this product type — skip validation
    return load_registry_ids(fname)


def load_registries() -> dict[str, set[str]]:
    return {
        "states_uts":    load_registry_ids("registry_states_uts.json"),
        "entities":      load_registry_ids("registry_entities.json"),
        "schemes":       load_registry_ids("registry_schemes.json"),
        "report_sector": load_registry_ids("taxonomy_report_sector.json"),
        "audit_type":    load_registry_ids("taxonomy_audit_type.json"),
        "product_type":  load_registry_ids("taxonomy_product_types.json"),
    }


def check_ref(value: str, registry: set[str], label: str, source: str, errors: list[str]):
    if value and value not in registry:
        errors.append(f"  [{source}] Unknown {label}: '{value}'")


def check_refs(values: list, registry: set[str], label: str, source: str, errors: list[str]):
    for v in (values or []):
        check_ref(v, registry, label, source, errors)


def validate_inheritable(obj: dict, registries: dict, source: str,
                         audit_findings_ids: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    r = registries
    check_refs(obj.get("report_sector", []), r["report_sector"], "report_sector", source, errors)
    check_refs(obj.get("audit_type", []), r["audit_type"], "audit_type", source, errors)
    check_refs(obj.get("main_audited_entities", []), r["entities"], "main_audited_entities", source, errors)
    check_refs(obj.get("other_audited_entities", []), r["entities"], "other_audited_entities", source, errors)
    check_refs(obj.get("primary_schemes", []), r["schemes"], "primary_schemes", source, errors)
    check_refs(obj.get("other_schemes", []), r["schemes"], "other_schemes", source, errors)
    coverage = obj.get("examination_coverage", {})
    if isinstance(coverage, dict):
        check_refs(
            coverage.get("state_ut_ids", []),
            r["states_uts"],
            "examination_coverage.state_ut_ids",
            source,
            errors,
        )
    # audit_findings_categories — only at SECTION level; validated when ids available
    if audit_findings_ids is not None:
        check_refs(
            obj.get("audit_findings_categories", []),
            audit_findings_ids,
            "audit_findings_categories",
            source,
            errors,
        )
    return errors


def validate_metadata_file(report_dir: Path, registries: dict,
                            audit_findings_ids: set[str] | None) -> list[str]:
    errors: list[str] = []
    metadata = rl.load_metadata(report_dir)
    if not metadata:
        return errors

    # product_type (from common_metadata, embedded in metadata.json)
    check_ref(metadata.get("product_type"), registries["product_type"], "product_type", "metadata.json", errors)

    # state_ut
    rl_data = metadata.get("report_level", {})
    state_ut = rl_data.get("state_ut", {})
    if isinstance(state_ut, dict):
        check_ref(state_ut.get("id"), registries["states_uts"], "state_ut.id", "metadata.json", errors)

    # report-level inheritable (audit_findings_categories not set here — section-level only)
    inheritable = metadata.get("inheritable", {})
    if inheritable:
        errors.extend(validate_inheritable(inheritable, registries, "metadata.json/inheritable",
                                           audit_findings_ids=None))

    return errors


def validate_structure_node(node: dict, registries: dict, source: str, errors: list[str],
                             audit_findings_ids: set[str] | None = None):
    """Recursively validate inheritable metadata on structure units."""
    if "metadata" in node:
        node_id = node.get("unit_id", "?")
        errors.extend(validate_inheritable(node["metadata"], registries, f"{source}/{node_id}",
                                           audit_findings_ids=audit_findings_ids))
    for section in (node.get("content_units", []) + node.get("front_matter", [])
                    + node.get("back_matter", [])):
        validate_structure_node(section, registries, source, errors, audit_findings_ids)


def validate_structure_file(report_dir: Path, registries: dict,
                             audit_findings_ids: set[str] | None) -> list[str]:
    errors: list[str] = []
    structure = rl.load_structure(report_dir)
    if not structure:
        return errors

    for section_key in ("front_matter", "content_units", "back_matter"):
        for unit in structure.get(section_key, []):
            validate_structure_node(unit, registries, "structure.json", errors, audit_findings_ids)
    return errors


def validate_unit_files(report_dir: Path, registries: dict,
                         audit_findings_ids: set[str] | None) -> list[str]:
    """
    Validate inheritable metadata in individual unit JSON files.
    audit_findings_categories is validated at SECTION level (block_metadata in content blocks).
    At unit level it is inherited/aggregated — still worth cross-checking if present.
    """
    errors: list[str] = []
    for unit_file in rl.unit_json_files(report_dir):
        try:
            unit = json.loads(unit_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        metadata = unit.get("metadata", {})
        if metadata:
            errors.extend(validate_inheritable(
                metadata, registries, f"units/{unit_file.name}",
                audit_findings_ids=audit_findings_ids
            ))
    return errors


def validate_report_dir(report_dir: Path, registries: dict) -> dict[str, list[str]]:
    all_errors: dict[str, list[str]] = {}

    # Resolve product_type → findings taxonomy (per-product-type file)
    manifest = rl.load_manifest(report_dir)
    product_type = (manifest or {}).get("product_type")
    audit_findings_ids = load_audit_findings_ids(product_type)
    if product_type and audit_findings_ids is None:
        fname = audit_findings_taxonomy_filename(product_type)
        # Warn but don't fail — file may not be built yet for this product type
        all_errors.setdefault("_warnings", []).append(
            f"  [warn] {fname} not found — audit_findings_categories not validated"
        )

    errs = validate_metadata_file(report_dir, registries, audit_findings_ids)
    if errs:
        all_errors["metadata.json"] = errs

    errs = validate_structure_file(report_dir, registries, audit_findings_ids)
    if errs:
        all_errors["structure.json"] = errs

    errs = validate_unit_files(report_dir, registries, audit_findings_ids)
    if errs:
        all_errors["units/"] = errs

    return all_errors


def main():
    parser = argparse.ArgumentParser(description="Validate registry references in report files")
    parser.add_argument("--product-id", help="Single product_id to check (searches full tree)")
    args = parser.parse_args()

    registries = load_registries()
    failed = 0

    if args.product_id:
        found = rl.locate_report(args.product_id)
        if not found:
            print(f"ERROR: product_id '{args.product_id}' not found under reports/")
            sys.exit(1)
        dirs = [found]
    else:
        dirs = rl.all_report_dirs()

    if not dirs:
        print("No report directories found.")
        sys.exit(0)

    for report_dir in dirs:
        errors = validate_report_dir(report_dir, registries)
        try:
            label = str(report_dir.relative_to(rl.REPO_ROOT))
        except ValueError:
            label = str(report_dir)

        if errors:
            failed += 1
            print(f"\nFAIL  {label}")
            for filename, errs in errors.items():
                print(f"  ── {filename}")
                for e in errs:
                    print(e)
        else:
            print(f"OK    {label}")

    print(f"\n{'─'*60}")
    total = len(dirs)
    print(f"Results: {total - failed}/{total} passed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
