#!/usr/bin/env python3
"""
check_registry_integrity.py
---------------------------
Validates internal consistency of all registry and taxonomy files:

  registry_states_uts.json
    - No duplicate IDs
    - successor/predecessor IDs exist within the registry
    - dissolved entries have dissolved_on and dissolution_reason

  registry_entities.json
    - No duplicate IDs
    - parent_id references exist within the registry
    - dissolved/archived entries have required dissolution fields

  registry_schemes.json
    - No duplicate IDs
    - predecessor_id / successor_id references exist within registry

  taxonomy_report_sector.json
    - No duplicate IDs
    - sub-sector parent_id references exist within registry

  taxonomy_audit_type.json
    - No duplicate IDs

  taxonomy_product_types.json
    - No duplicate IDs
    - parent references exist (if hierarchy used)

Usage:
    python scripts/check_registry_integrity.py
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TAXONOMIES_DIR = REPO_ROOT / "taxonomies"

OK = True   # module-level flag


def fail(msg: str):
    global OK
    OK = False
    print(f"  FAIL  {msg}")


def info(label: str, count: int):
    print(f"  OK    {label} — {count} entries")


def get_entries(data: dict | list) -> list[dict]:
    if isinstance(data, list):
        return data
    return data.get("entries", [])


def check_no_duplicates(entries: list[dict], id_field: str, label: str) -> set[str]:
    seen: set[str] = set()
    dupes: list[str] = []
    for e in entries:
        eid = e.get(id_field)
        if eid in seen:
            dupes.append(eid)
        seen.add(eid)
    if dupes:
        fail(f"{label}: duplicate IDs: {dupes}")
    return seen


def check_refs(entries: list[dict], ref_fields: list[str], known_ids: set[str], label: str):
    for e in entries:
        eid = e.get("id", "?")
        for field in ref_fields:
            val = e.get(field)
            if val is None:
                continue
            vals = val if isinstance(val, list) else [val]
            for v in vals:
                if v not in known_ids:
                    fail(f"{label} [{eid}].{field} references unknown ID: '{v}'")


# ── States/UTs ────────────────────────────────────────────────────────────────

def check_states_uts():
    path = TAXONOMIES_DIR / "registry_states_uts.json"
    print(f"\n{path.name}")
    data = json.loads(path.read_text())
    entries = get_entries(data)
    ids = check_no_duplicates(entries, "id", path.name)

    check_refs(entries, ["predecessor_id", "successor_id"], ids, path.name)

    for e in entries:
        if e.get("active") is False:
            if not e.get("dissolved_on"):
                fail(f"{path.name} [{e['id']}]: inactive entry missing dissolved_on")
            if not e.get("dissolution_reason"):
                fail(f"{path.name} [{e['id']}]: inactive entry missing dissolution_reason")

    info(path.name, len(entries))


# ── Entities ──────────────────────────────────────────────────────────────────

def check_entities():
    path = TAXONOMIES_DIR / "registry_entities.json"
    print(f"\n{path.name}")
    data = json.loads(path.read_text())
    entries = get_entries(data)
    ids = check_no_duplicates(entries, "id", path.name)

    check_refs(entries, ["parent_id"], ids, path.name)

    for e in entries:
        if not e.get("active", True) or e.get("archived"):
            if not e.get("dissolved_on"):
                fail(f"{path.name} [{e['id']}]: archived/inactive entry missing dissolved_on")
            if not e.get("dissolution_reason"):
                fail(f"{path.name} [{e['id']}]: archived/inactive entry missing dissolution_reason")

    info(path.name, len(entries))


# ── Schemes ───────────────────────────────────────────────────────────────────

def check_schemes():
    path = TAXONOMIES_DIR / "registry_schemes.json"
    print(f"\n{path.name}")
    data = json.loads(path.read_text())
    entries = get_entries(data)
    ids = check_no_duplicates(entries, "id", path.name)

    check_refs(entries, ["predecessor_id", "successor_id"], ids, path.name)

    info(path.name, len(entries))


# ── Report Sector Taxonomy ────────────────────────────────────────────────────

def check_report_sector():
    path = TAXONOMIES_DIR / "taxonomy_report_sector.json"
    print(f"\n{path.name}")
    data = json.loads(path.read_text())
    entries = get_entries(data)
    ids = check_no_duplicates(entries, "id", path.name)

    check_refs(entries, ["parent_id"], ids, path.name)

    # all sub-sectors must have a parent_id pointing to a sector (no parent_id = sector)
    for e in entries:
        if e.get("parent_id") and e["parent_id"] not in ids:
            fail(f"{path.name} [{e['id']}]: parent_id '{e['parent_id']}' not found")

    info(path.name, len(entries))


# ── Audit Type Taxonomy ───────────────────────────────────────────────────────

def check_audit_type():
    path = TAXONOMIES_DIR / "taxonomy_audit_type.json"
    print(f"\n{path.name}")
    data = json.loads(path.read_text())
    entries = get_entries(data)
    check_no_duplicates(entries, "id", path.name)
    info(path.name, len(entries))


# ── Product Types Taxonomy ────────────────────────────────────────────────────

def check_product_types():
    path = TAXONOMIES_DIR / "taxonomy_product_types.json"
    print(f"\n{path.name}")
    data = json.loads(path.read_text())
    entries = get_entries(data)
    ids = check_no_duplicates(entries, "id", path.name)
    check_refs(entries, ["parent_id"], ids, path.name)
    info(path.name, len(entries))


# ── Topics Taxonomy ───────────────────────────────────────────────────────────

def check_topics():
    path = TAXONOMIES_DIR / "taxonomy_topics.json"
    if not path.exists():
        print(f"\n{path.name}  (SKIPPED — file not present)")
        return
    print(f"\n{path.name}")
    data = json.loads(path.read_text())
    entries = get_entries(data)
    ids = check_no_duplicates(entries, "id", path.name)

    # parent_id references must resolve
    check_refs(entries, ["parent_id"], ids, path.name)

    # sub_topics[] list references must all resolve
    for e in entries:
        eid = e.get("id", "?")
        for sid in e.get("sub_topics", []):
            if sid not in ids:
                fail(f"{path.name} [{eid}].sub_topics references unknown ID: '{sid}'")

    # level consistency
    for e in entries:
        level = e.get("level")
        if level == "topic" and e.get("parent_id") is not None:
            fail(f"{path.name} [{e['id']}]: level=topic but has parent_id set")
        if level == "sub_topic" and not e.get("parent_id"):
            fail(f"{path.name} [{e['id']}]: level=sub_topic but parent_id is null/missing")

    n_topics = sum(1 for e in entries if e.get("level") == "topic")
    n_sub    = sum(1 for e in entries if e.get("level") == "sub_topic")
    print(f"  OK    {path.name} — {len(entries)} entries ({n_topics} topics, {n_sub} sub-topics)")


# ── Audit Findings Taxonomies (per product type) ──────────────────────────────

def check_audit_findings():
    """
    Check all taxonomy_audit_findings_{product_type}.json files found in taxonomies/.
    Convention: 3-level tree — category → sub_category → detail.
    Each file declares which product_types it covers via the product_types[] field.
    """
    pattern = "taxonomy_audit_findings_*.json"
    findings_files = sorted(TAXONOMIES_DIR.glob(pattern))
    if not findings_files:
        print(f"\ntaxonomy_audit_findings_*.json  (SKIPPED — no files present)")
        return

    for path in findings_files:
        print(f"\n{path.name}")
        data = json.loads(path.read_text())
        entries = get_entries(data)
        ids = check_no_duplicates(entries, "id", path.name)

        # parent_id references must resolve
        check_refs(entries, ["parent_id"], ids, path.name)

        # sub_categories[] references on category-level entries must resolve
        for e in entries:
            eid = e.get("id", "?")
            for sid in e.get("sub_categories", []):
                if sid not in ids:
                    fail(f"{path.name} [{eid}].sub_categories references unknown ID: '{sid}'")

        # level consistency
        for e in entries:
            level = e.get("level")
            pid = e.get("parent_id")
            if level == "category" and pid is not None:
                fail(f"{path.name} [{e['id']}]: level=category but has parent_id set")
            if level in ("sub_category", "detail") and not pid:
                fail(f"{path.name} [{e['id']}]: level={level} but parent_id is null/missing")

        # product_types[] field must be present
        if "product_types" not in data:
            fail(f"{path.name}: missing product_types[] field at root")

        n_cat = sum(1 for e in entries if e.get("level") == "category")
        n_sub = sum(1 for e in entries if e.get("level") == "sub_category")
        n_det = sum(1 for e in entries if e.get("level") == "detail")
        pt    = data.get("product_types", [])
        print(f"  OK    {path.name} — {len(entries)} entries "
              f"({n_cat} categories, {n_sub} sub-categories, {n_det} detail)  "
              f"product_types={pt}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Registry & Taxonomy Integrity Check")
    print("=" * 50)

    check_states_uts()
    check_entities()
    check_schemes()
    check_report_sector()
    check_audit_type()
    check_product_types()
    check_topics()
    check_audit_findings()

    print(f"\n{'─'*50}")
    if OK:
        print("All checks passed.")
    else:
        print("One or more integrity checks FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()


# NOTE: check_topics() and updated main() appended below — replace the old ones above manually
