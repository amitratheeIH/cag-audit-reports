#!/usr/bin/env python3
"""
write_to_atlas.py
-----------------
Ingests validated report data into MongoDB Atlas.

Reads from:
  manifest.json, metadata.json, structure.json  (report root)
  units/      *.json
  blocks/     content_block_*.ndjson
  atn/        atn_*.json
  datasets/   *.json
  footnotes/  footnotes_*.json
  embeddings/ embeddings_*.ndjson  (pipeline-generated sidecars)

Collections written:
  report_meta     — one doc per report
  block_vectors   — one doc per content block (with embedding if available)
  atn_index       — one doc per ATN record
  catalog_index   — one doc per catalog entity chain

Usage:
    python scripts/write_to_atlas.py --product-id AR06-CAG-2023-STATE-MP
    python scripts/write_to_atlas.py --all
    python scripts/write_to_atlas.py --all --dry-run
    python scripts/write_to_atlas.py --all --force
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_layout as rl

DB_NAME = "cag_audit"
COLLECTIONS = {
    "report_meta":   "report_meta",
    "block_vectors": "block_vectors",
    "atn_index":     "atn_index",
    "catalog_index": "catalog_index",
}


def get_mongo_client():
    try:
        from pymongo import MongoClient
    except ImportError:
        print("ERROR: pymongo not installed. Run: pip install pymongo")
        sys.exit(1)
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        print("ERROR: MONGODB_URI environment variable not set")
        sys.exit(1)
    return MongoClient(uri)


def load_ndjson(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def load_embedding_sidecar(report_dir: Path) -> dict[str, list[float]]:
    """Load all embeddings from embeddings/ sidecar files. Returns {block_id: embedding}."""
    embeddings: dict[str, list[float]] = {}
    for sidecar in rl.embedding_sidecar_files(report_dir):
        for row in load_ndjson(sidecar):
            if "block_id" in row and "embedding" in row:
                embeddings[row["block_id"]] = row["embedding"]
    return embeddings


def manifest_checksum(manifest: dict) -> str:
    blob = json.dumps(manifest.get("file_checksums", {}), sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:32]


def get_stored_checksum(db, product_id: str) -> str | None:
    doc = db[COLLECTIONS["report_meta"]].find_one(
        {"product_id": product_id}, {"_ingestion.manifest_checksum": 1}
    )
    return doc.get("_ingestion", {}).get("manifest_checksum") if doc else None


def build_report_meta_doc(product_id: str, report_dir: Path,
                           manifest: dict, metadata: dict,
                           structure: dict | None) -> dict:
    # Derive folder path relative to REPO_ROOT for traceability
    try:
        folder_path = str(report_dir.relative_to(rl.REPO_ROOT))
    except ValueError:
        folder_path = str(report_dir)

    return {
        "product_id": product_id,
        "product_type": manifest.get("product_type"),
        "year": manifest.get("year"),
        "folder_path": folder_path,
        "metadata": metadata,
        "structure_summary": {
            "content_unit_count": len((structure or {}).get("content_units", [])),
            "front_matter_count": len((structure or {}).get("front_matter", [])),
            "back_matter_count":  len((structure or {}).get("back_matter", [])),
        },
        "_ingestion": {
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "manifest_checksum": manifest_checksum(manifest),
            "schema_versions": manifest.get("schema_versions", {}),
        },
    }


def _text_snippet(block: dict, max_chars: int = 500) -> str:
    content = block.get("content", {})
    text = content.get("text", {})
    if isinstance(text, dict):
        text = text.get("en") or next(iter(text.values()), "")
    return (text or "")[:max_chars]


def build_block_vector_docs(product_id: str, report_dir: Path,
                             embeddings: dict[str, list[float]]) -> list[dict]:
    docs = []
    for ndjson_path in rl.block_ndjson_files(report_dir):
        for block in load_ndjson(ndjson_path):
            block_id = block.get("block_id")
            if not block_id:
                continue
            doc = {
                "product_id":    product_id,
                "block_id":      block_id,
                "unit_id":       block.get("unit_id"),
                "seq":           block.get("seq"),
                "block_type":    block.get("block_type"),
                "para_type":     block.get("content", {}).get("para_type"),
                "para_number":   block.get("para_number"),
                "audit_metadata": block.get("block_metadata"),
                "annotations":   block.get("annotations", []),
                "text_snippet":  _text_snippet(block),
            }
            if block_id in embeddings:
                doc["embedding"] = embeddings[block_id]
            docs.append(doc)
    return docs


def build_atn_docs(product_id: str, report_dir: Path) -> list[dict]:
    docs = []
    for atn_path in rl.atn_json_files(report_dir):
        data = json.loads(atn_path.read_text())
        for record in data.get("atn_records", []):
            doc = {
                "product_id":    product_id,
                "atn_id":        record.get("atn_id"),
                "chapter_id":    data.get("chapter_id"),
                "department":    record.get("department"),
                "current_status": record.get("current_status"),
                "current_round": record.get("current_round"),
                "scope":         record.get("scope"),
                "rounds":        record.get("rounds", []),
            }
            docs.append(doc)
    return docs


def build_catalog_docs(product_id: str, report_dir: Path) -> list[dict]:
    # catalog.json lives at report root (not in a subfolder)
    catalog_path = report_dir / "catalog.json"
    if not catalog_path.exists():
        return []
    data = json.loads(catalog_path.read_text())
    return [{"product_id": product_id, **entry} for entry in data.get("entries", [])]


def upsert_collection(db, collection_name: str, docs: list[dict],
                      id_field: str, dry_run: bool) -> int:
    if not docs or dry_run:
        return len(docs) if dry_run else 0
    from pymongo import UpdateOne
    ops = [
        UpdateOne({id_field: doc[id_field]}, {"$set": doc}, upsert=True)
        for doc in docs
        if id_field in doc
    ]
    if ops:
        result = db[collection_name].bulk_write(ops)
        return result.upserted_count + result.modified_count
    return 0


def ingest_report(report_dir: Path, db, force: bool, dry_run: bool) -> dict:
    product_id = rl.product_id_from_dir(report_dir)
    stats = {"status": "ok", "blocks": 0, "atn": 0, "catalog": 0}

    manifest = rl.load_manifest(report_dir)
    if not manifest:
        stats["status"] = "skip (no manifest)"
        return stats

    # Checksum gate
    if not force and not dry_run:
        stored = get_stored_checksum(db, product_id)
        if stored == manifest_checksum(manifest):
            stats["status"] = "skip (unchanged)"
            return stats

    metadata  = rl.load_metadata(report_dir) or {}
    structure = rl.load_structure(report_dir)
    embeddings = load_embedding_sidecar(report_dir)

    # report_meta
    meta_doc = build_report_meta_doc(product_id, report_dir, manifest, metadata, structure)
    if not dry_run:
        db[COLLECTIONS["report_meta"]].update_one(
            {"product_id": product_id}, {"$set": meta_doc}, upsert=True
        )

    # block_vectors
    block_docs = build_block_vector_docs(product_id, report_dir, embeddings)
    stats["blocks"] = upsert_collection(
        db, COLLECTIONS["block_vectors"], block_docs, "block_id", dry_run
    )

    # atn_index
    atn_docs = build_atn_docs(product_id, report_dir)
    stats["atn"] = upsert_collection(
        db, COLLECTIONS["atn_index"], atn_docs, "atn_id", dry_run
    )

    # catalog_index
    catalog_docs = build_catalog_docs(product_id, report_dir)
    stats["catalog"] = upsert_collection(
        db, COLLECTIONS["catalog_index"], catalog_docs, "product_id", dry_run
    )

    return stats


def resolve_dirs(args) -> list[Path]:
    if args.all:
        return rl.all_report_dirs()
    ids = []
    if args.product_ids:
        ids = [pid.strip() for pid in args.product_ids.split(",")]
    elif args.product_id:
        ids = [args.product_id.strip()]
    dirs = []
    for pid in ids:
        found = rl.locate_report(pid)
        if not found:
            print(f"WARN: product_id '{pid}' not found — skipping")
        else:
            dirs.append(found)
    return dirs


def main():
    parser = argparse.ArgumentParser(description="Write reports to MongoDB Atlas")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--product-id", help="Single product_id")
    group.add_argument("--product-ids", help="Comma-separated product_ids")
    group.add_argument("--all", action="store_true")
    parser.add_argument("--force", action="store_true", help="Re-ingest even if checksum unchanged")
    parser.add_argument("--dry-run", action="store_true", help="Log without writing")
    args = parser.parse_args()

    db = None if args.dry_run else get_mongo_client()[DB_NAME]
    dirs = resolve_dirs(args)

    if not dirs:
        print("No report directories to process.")
        sys.exit(0)

    print(f"{'DRY RUN — ' if args.dry_run else ''}Ingesting {len(dirs)} report(s)\n")

    for report_dir in dirs:
        stats = ingest_report(report_dir, db, args.force, args.dry_run)
        try:
            label = str(report_dir.relative_to(rl.REPO_ROOT))
        except ValueError:
            label = str(report_dir)

        status = stats["status"]
        if status.startswith("skip"):
            print(f"SKIP  {label}  [{status}]")
        else:
            print(
                f"OK    {label}  "
                f"blocks={stats['blocks']}  atn={stats['atn']}  catalog={stats['catalog']}"
                f"{'  [DRY RUN]' if args.dry_run else ''}"
            )

    print(f"\n{'─'*60}\nDone.")


if __name__ == "__main__":
    main()
