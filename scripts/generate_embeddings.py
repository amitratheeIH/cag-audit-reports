#!/usr/bin/env python3
"""
generate_embeddings.py
----------------------
Reads content block NDJSON files from blocks/, generates text-embedding-3-large
embeddings (3072 dims) via OpenAI API, and writes embedding sidecar files to
embeddings/.

Sidecar format (one line per block):
  {"block_id": "...", "embedding": [...3072 floats...]}

Sidecar files:
  {report_dir}/embeddings/embeddings_{stem}.ndjson
  {report_dir}/embeddings/embeddings_{stem}.checksums.json

Where {stem} mirrors the source file's stem:
  blocks/content_block_ch02.ndjson → embeddings/embeddings_ch02.ndjson

embeddings/ is pipeline-generated and should be .gitignore'd.

Usage:
    python scripts/generate_embeddings.py --product-id AR06-CAG-2023-STATE-MP
    python scripts/generate_embeddings.py --product-ids "ID1,ID2"
    python scripts/generate_embeddings.py --all
    python scripts/generate_embeddings.py --all --force
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_layout as rl

EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMS = 3072
BATCH_SIZE = 100       # texts per API call (OpenAI max: 2048)
RATE_LIMIT_SLEEP = 0.5 # seconds between batches


def get_openai_client():
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package not installed. Run: pip install openai")
        sys.exit(1)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    return OpenAI(api_key=api_key)


def _multilingual_str(obj) -> str:
    """Extract English text from a multilingual {lang: str} object, or return str as-is."""
    if isinstance(obj, dict):
        return obj.get("en") or next(iter(obj.values()), "")
    return str(obj) if obj else ""


def build_embedding_text(block: dict) -> str:
    """
    Concatenate meaningful text fields from a content block for embedding.

    Dispatch order:
      executive_summary_block — title + paragraphs[] + bullets[]
      paragraph               — content.text
      heading                 — content.text
      list                    — content.items[]
      table                   — headers + first 10 rows
      callout / sidebar       — content.title + content.text
      image / figure / map    — content.caption + content.alt_text
      (fallback)              — content.text if present
    """
    parts = []
    block_type = block.get("block_type", "")
    content = block.get("content", {})

    # ── top-level heading/subheading fields (legacy; not in current schema) ──
    if heading := block.get("heading"):
        parts.append(heading)
    if subheading := block.get("subheading"):
        parts.append(subheading)

    # ── dispatch by block_type ────────────────────────────────────────────────

    if block_type == "executive_summary_block":
        # title
        if title := content.get("title"):
            parts.append(_multilingual_str(title))
        # prose paragraphs
        for para in content.get("paragraphs", []):
            t = _multilingual_str(para)
            if t:
                parts.append(t)
        # structured bullets — include text and any sub_items
        for bullet in content.get("bullets", []):
            t = _multilingual_str(bullet.get("text", {}))
            if t:
                parts.append(t)
            for sub in bullet.get("sub_items", []):
                s = _multilingual_str(sub)
                if s:
                    parts.append(s)

    elif block_type in ("paragraph", "heading", "pullquote", "quote"):
        if text := content.get("text"):
            parts.append(_multilingual_str(text))

    elif block_type in ("callout", "sidebar"):
        if title := content.get("title"):
            parts.append(_multilingual_str(title))
        if text := content.get("text"):
            parts.append(_multilingual_str(text))

    elif block_type == "list":
        for item in content.get("items", [])[:20]:
            if isinstance(item, dict):
                t = _multilingual_str(item.get("text", {}))
                if t:
                    parts.append(t)
                for sub in item.get("sub_items", []):
                    s = _multilingual_str(sub)
                    if s:
                        parts.append(s)
            elif isinstance(item, str):
                parts.append(item)

    elif block_type == "table":
        # dataset_ref-based tables have no inline rows here; fall through
        if table := content.get("table"):
            headers = table.get("headers", [])
            if headers:
                parts.append(" | ".join(str(h) for h in headers))
            for row in table.get("rows", [])[:10]:
                parts.append(" | ".join(str(c) for c in row.get("cells", [])))
        if caption := content.get("caption"):
            parts.append(_multilingual_str(caption))

    elif block_type in ("image", "figure", "map", "chart"):
        if caption := content.get("caption"):
            parts.append(_multilingual_str(caption))
        if alt := content.get("alt_text"):
            parts.append(_multilingual_str(alt))

    elif block_type == "audit_finding":
        for field in ("title", "observation", "effect", "cause", "recommendation"):
            val = content.get(field)
            if val:
                parts.append(_multilingual_str(val))

    elif block_type == "recommendation":
        if text := content.get("text"):
            parts.append(_multilingual_str(text))

    else:
        # generic fallback — grab content.text if it exists
        if text := content.get("text"):
            parts.append(_multilingual_str(text))

    return "\n".join(p for p in parts if p).strip()


def embed_batch(client, texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
        dimensions=EMBEDDING_DIMS,
    )
    return [item.embedding for item in response.data]


def text_checksum(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def sidecar_stem(source_ndjson: Path) -> str:
    """
    blocks/content_block_ch02.ndjson → embeddings_ch02
    Strips 'content_block_' prefix.
    """
    stem = source_ndjson.stem  # e.g. "content_block_ch02"
    return stem.replace("content_block_", "embeddings_", 1)


def process_report(report_dir: Path, client, force: bool) -> dict:
    stats = {"blocks": 0, "embedded": 0, "skipped": 0, "errors": 0}

    block_files = rl.block_ndjson_files(report_dir)
    if not block_files:
        print(f"    WARN: no content_block_*.ndjson files in {rl.blocks_dir(report_dir)}")
        return stats

    emb_dir = rl.embeddings_dir(report_dir)
    emb_dir.mkdir(exist_ok=True)

    for ndjson_path in block_files:
        stem = sidecar_stem(ndjson_path)
        sidecar_path = emb_dir / f"{stem}.ndjson"
        checksum_path = emb_dir / f"{stem}.checksums.json"

        # Load existing checksums
        existing: dict[str, str] = {}
        if sidecar_path.exists() and checksum_path.exists() and not force:
            try:
                existing = json.loads(checksum_path.read_text())
            except (json.JSONDecodeError, OSError):
                existing = {}

        # Parse blocks
        blocks = []
        for line in ndjson_path.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    blocks.append(json.loads(line))
                except json.JSONDecodeError:
                    stats["errors"] += 1
        stats["blocks"] += len(blocks)

        # Build work queue
        to_embed: list[tuple[int, dict, str, str]] = []
        for idx, block in enumerate(blocks):
            block_id = block.get("block_id", f"block_{idx}")
            text = build_embedding_text(block)
            if not text:
                stats["skipped"] += 1
                continue
            chk = text_checksum(text)
            if not force and existing.get(block_id) == chk:
                stats["skipped"] += 1
                continue
            to_embed.append((idx, block, text, chk))

        if not to_embed:
            continue

        # Load existing sidecar
        sidecar_data: dict[str, list[float]] = {}
        if sidecar_path.exists():
            for line in sidecar_path.read_text().splitlines():
                if line.strip():
                    try:
                        row = json.loads(line)
                        sidecar_data[row["block_id"]] = row["embedding"]
                    except (json.JSONDecodeError, KeyError):
                        pass

        new_checksums = dict(existing)

        # Embed in batches
        for batch_start in range(0, len(to_embed), BATCH_SIZE):
            batch = to_embed[batch_start:batch_start + BATCH_SIZE]
            texts = [item[2] for item in batch]
            try:
                embeddings = embed_batch(client, texts)
            except Exception as exc:
                print(f"    ERROR batch starting at {batch_start}: {exc}")
                stats["errors"] += len(batch)
                time.sleep(2)
                continue

            for (idx, block, text, chk), embedding in zip(batch, embeddings):
                block_id = block.get("block_id", f"block_{idx}")
                sidecar_data[block_id] = embedding
                new_checksums[block_id] = chk
                stats["embedded"] += 1

            time.sleep(RATE_LIMIT_SLEEP)

        # Write sidecar in canonical block order
        with sidecar_path.open("w") as f:
            for block in blocks:
                bid = block.get("block_id")
                if bid and bid in sidecar_data:
                    f.write(json.dumps({"block_id": bid, "embedding": sidecar_data[bid]}) + "\n")

        checksum_path.write_text(json.dumps(new_checksums, indent=2))
        print(f"    {ndjson_path.name}: {len(to_embed)} embedded, "
              f"{sum(1 for _, b, _, _ in to_embed if b not in sidecar_data)} new")

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
    parser = argparse.ArgumentParser(description="Generate embeddings for content blocks")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--product-id", help="Single product_id")
    group.add_argument("--product-ids", help="Comma-separated product_ids")
    group.add_argument("--all", action="store_true")
    parser.add_argument("--force", action="store_true", help="Re-embed even if checksum matches")
    args = parser.parse_args()

    client = get_openai_client()
    dirs = resolve_dirs(args)

    if not dirs:
        print("No report directories to process.")
        sys.exit(0)

    total = {"blocks": 0, "embedded": 0, "skipped": 0, "errors": 0}

    for report_dir in dirs:
        try:
            label = str(report_dir.relative_to(rl.REPO_ROOT))
        except ValueError:
            label = str(report_dir)
        print(f"\nProcessing {label} ...")
        stats = process_report(report_dir, client, args.force)
        for k in total:
            total[k] += stats[k]

    print(f"\n{'─'*60}")
    print(f"Total blocks : {total['blocks']}")
    print(f"Embedded     : {total['embedded']}")
    print(f"Skipped      : {total['skipped']}  (checksum match)")
    print(f"Errors       : {total['errors']}")

    if total["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
