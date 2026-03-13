# CAG Audit Report Repository — Complete Reference

**JSON Schema (draft-07) system for digitising, structuring, and publishing CAG (Comptroller and Auditor General of India) audit reports.**

This file is the single source of truth for a new session. It documents every schema, taxonomy, registry, script, and architectural decision made in this project. It is designed to be read by both humans and LLMs resuming work mid-project.

---

## Table of Contents

1. [Project Purpose](#1-project-purpose)
2. [Repository Layout](#2-repository-layout)
3. [Architecture Overview](#3-architecture-overview)
4. [Schema System](#4-schema-system)
   - 4.1 [Design Principles](#41-design-principles)
   - 4.2 [ID Conventions](#42-id-conventions)
   - 4.3 [Multilingual Pattern](#43-multilingual-pattern)
   - 4.4 [Schema Dependency Map](#44-schema-dependency-map)
   - 4.5 [Schema Version Table](#45-schema-version-table)
5. [Schema Reference — Field by Field](#5-schema-reference--field-by-field)
   - 5.1 [common_metadata.schema v2.1](#51-common_metadataschema-v21)
   - 5.2 [audit_report_metadata.schema v3.5](#52-audit_report_metadataschema-v35)
   - 5.3 [inheritable_audit_metadata.schema v3.6](#53-inheritable_audit_metadataschema-v36)
   - 5.4 [structure.schema v3.2](#54-structureschema-v32)
   - 5.5 [content_block.schema v3.4](#55-content_blockschema-v34)
   - 5.6 [atn.schema v3.2](#56-atnschema-v32)
   - 5.7 [dataset.schema v3.0](#57-datasetschema-v30)
   - 5.8 [footnote.schema v3.1](#58-footnoteschema-v31)
   - 5.9 [reference.schema v3.0](#59-referenceschema-v30)
   - 5.10 [catalog.schema v3.3](#510-catalogschema-v33)
   - 5.11 [manifest.schema v3.1](#511-manifestschema-v31)
   - 5.12 [product.schema v2.1](#512-productschema-v21)
6. [Inheritance System](#6-inheritance-system)
7. [Taxonomies](#7-taxonomies)
   - 7.1 [taxonomy_product_types.json](#71-taxonomy_product_typesjson)
   - 7.2 [taxonomy_audit_type.json](#72-taxonomy_audit_typejson)
   - 7.3 [taxonomy_report_sector.json](#73-taxonomy_report_sectorjson)
   - 7.4 [taxonomy_audit_findings_{product_type}.json](#74-taxonomy_audit_findings_product_typejson)
   - 7.5 [taxonomy_topics.json](#75-taxonomy_topicsjson-v10)
8. [Registries](#8-registries)
   - 8.1 [registry_states_uts.json](#81-registry_states_utsjson)
   - 8.2 [registry_entities.json](#82-registry_entitiesjson)
   - 8.3 [registry_schemes.json](#83-registry_schemesjson)
9. [Pipeline and Scripts](#9-pipeline-and-scripts)
   - 9.1 [Validation Scripts (auto, CI)](#91-validation-scripts-auto-ci)
   - 9.2 [Ingestion Scripts (manual trigger)](#92-ingestion-scripts-manual-trigger)
   - 9.3 [GitHub Actions Workflows](#93-github-actions-workflows)
   - 9.4 [Full Pipeline Responsibilities](#94-full-pipeline-responsibilities)
10. [MongoDB Atlas Collections](#10-mongodb-atlas-collections)
11. [Repository Status](#11-repository-status)
12. [First Report — Quick Start](#12-first-report--quick-start)
13. [Pending Items](#13-pending-items)

---

## 1. Project Purpose

The CAG issues hundreds of audit reports per year covering Union and State finances, public sector undertakings, performance audits, compliance audits, and more. These reports are currently only available as PDFs.

This repository system:
- Provides a JSON schema structure for encoding every element of an audit report (paragraphs, tables, figures, findings, recommendations, ATNs, footnotes)
- Links all report content to shared registries (states/UTs, government entities, schemes) and controlled taxonomies (audit types, sectors)
- Powers a full-stack portal: browsable report reader, full-text and semantic (RAG) search, ATN tracker, and public API

---

## 2. Repository Layout

```
/
├── schemas/                        # JSON Schema files (draft-07)
│   ├── atn.schema
│   ├── audit_report_metadata.schema
│   ├── catalog.schema
│   ├── common_metadata.schema
│   ├── content_block.schema
│   ├── dataset.schema
│   ├── footnote.schema
│   ├── inheritable_audit_metadata.schema
│   ├── manifest.schema
│   ├── product.schema
│   ├── reference.schema
│   └── structure.schema
│
├── taxonomies/                     # Taxonomy and registry JSON files
│   ├── taxonomy_product_types.json
│   ├── taxonomy_audit_type.json
│   ├── taxonomy_report_sector.json
│   ├── taxonomy_audit_findings_audit_report.json
│   ├── taxonomy_audit_findings_accounts_report.json  ← PENDING
│   ├── taxonomy_topics.json
│   ├── registry_states_uts.json
│   ├── registry_entities.json
│   └── registry_schemes.json
│
├── reports/
│   └── {product_type}/             # audit_report | accounts_report | state_finance_report
│       └── {year}/                 #              | study_report | audit_impact_report | other
│           │
│           ├── {product_id}/       # UNION jurisdiction — no state folder
│           │   └── …
│           │
│           └── {jurisdiction}/     # state | ut | union | lg
│               └── {state_code}/   # e.g. in-mp, in-jk  ← STATE, UT, LG only
│                   └── {product_id}/ # e.g. AR06-CAG-2023-STATE-MP
│                   ├── manifest.json
│                   ├── metadata.json
│                   ├── structure.json
│                   ├── units/              # one .json per content_unit
│                   │   ├── AR06-…-CH01.json
│                   │   ├── AR06-…-CH02.json
│                   │   └── …
│                   ├── blocks/             # one NDJSON per chapter
│                   │   ├── content_block_ch01.ndjson
│                   │   ├── content_block_ch02.ndjson
│                   │   └── …
│                   ├── atn/                # one JSON per chapter (optional)
│                   │   ├── atn_ch01.json
│                   │   └── …
│                   ├── datasets/           # one JSON per dataset (optional)
│                   │   ├── DS01.json
│                   │   └── ndjson/         # NDJSON companions for large datasets
│                   │       └── CH02-DS03.ndjson
│                   ├── footnotes/          # one JSON per chapter (optional)
│                   │   ├── footnotes_ch01.json
│                   │   └── …
│                   ├── pdfs/               # sub-structured by language
│                   │   ├── en/
│                   │   │   ├── complete/
│                   │   │   └── chapters/
│                   │   └── hi/
│                   ├── assets/             # images, figures, maps
│                   └── embeddings/         # pipeline-generated; .gitignore'd
│                       ├── embeddings_ch01.ndjson
│                       ├── embeddings_ch01.checksums.json
│                       └── …
│
├── scripts/                        # All pipeline and validation scripts
│   ├── repo_layout.py              # ← Single source of truth for all paths
│   ├── validate_report.py
│   ├── validate_registry_refs.py
│   ├── check_registry_integrity.py
│   ├── bump_schema_versions.py
│   ├── sync_product_type_enum.py
│   ├── generate_embeddings.py
│   ├── write_to_atlas.py
│   └── invalidate_cache.py
│
├── .github/workflows/
│   ├── validate.yml                # Runs on every push/PR
│   └── ingest.yml                  # Manual workflow_dispatch
│
└── requirements.txt
```

### Path rules (derived from schemas)

**Category folder** = `product_type` value from `taxonomy_product_types.json`: `audit_report`, `accounts_report`, `state_finance_report`, `study_report`, `audit_impact_report`, `other`.

**Jurisdiction folder** = lowercase jurisdiction value: `STATE` → `state`, `UT` → `ut`, `UNION` → `union`, `LG` → `lg`. Always present for all reports.

**State code folder** = lowercase registry ID without `IN-` prefix: `IN-MP` → `in-mp`, `IN-JK` → `in-jk`. Present only when `jurisdiction ∈ {STATE, UT, LG}`. UNION reports have no state folder.

**LG reports** use the state_code of the state in which the local government operates.

**product_id folder** = the `product_id` from `manifest.json`. Always the innermost folder that contains `manifest.json`. Scripts locate reports by searching for `manifest.json` via `repo_layout.locate_report(product_id)` — no hard-coded paths.

**Report folder naming:** `{type_prefix}{N}-CAG-{year}-{jurisdiction}-{state_code}`
Examples: `AR06-CAG-2023-STATE-MP`, `AR01-CAG-2025-UT-JK`, `AR03-CAG-2024-UNION`

### Sub-folder contents (derived from `manifest.schema` `file_lists` keys)

| Folder | Contents | Required | Schema validated |
|--------|----------|----------|-----------------|
| *(root)* | `manifest.json`, `metadata.json`, `structure.json` | Yes | Yes |
| `units/` | `{unit_id}.json` — one per `content_unit` | Yes | JSON parse only |
| `blocks/` | `content_block_{chapter}.ndjson` — one per chapter | Yes | `content_block.schema` line-by-line |
| `atn/` | `atn_{chapter}.json` — one per chapter | Optional | `atn.schema` |
| `datasets/` | `{dataset_id}.json` | Optional | `dataset.schema` |
| `datasets/ndjson/` | `{dataset_id}.ndjson` — large dataset row companions | Optional | Not validated |
| `footnotes/` | `footnotes_{chapter}.json` — one per chapter | Optional | `footnote.schema` |
| `pdfs/` | `{lang}/complete/` and `{lang}/chapters/` | Optional | Not validated |
| `assets/` | Images, figures, maps | Optional | Not validated |
| `embeddings/` | `embeddings_{chapter}.ndjson` + `.checksums.json` | Pipeline only | Not validated; .gitignore'd |

---

## 3. Architecture Overview

```
Git Repository (source of truth)
        │
        │  push / PR
        ▼
GitHub Actions: validate.yml
  validate_report.py
  validate_registry_refs.py
  check_registry_integrity.py
  sync_product_type_enum.py --check
  bump_schema_versions.py --dry-run
        │
        │  manual trigger (workflow_dispatch)
        ▼
GitHub Actions: ingest.yml
  generate_embeddings.py  ──── OpenAI text-embedding-3-large (3072 dims)
  write_to_atlas.py       ──── MongoDB Atlas
  invalidate_cache.py     ──── Redis
        │
        ├──── MongoDB Atlas (derived index only — never source of truth)
        │      ├── report_meta
        │      ├── block_vectors        (content + embedding vectors)
        │      ├── atn_index
        │      └── catalog_index
        │
        ├──── Redis (cache layer)
        │      ├── toc:{product_id}
        │      ├── filters:{product_id}
        │      ├── report_meta:{product_id}
        │      ├── atn_summary:{product_id}
        │      └── global:filter_options / report_list / sector_counts
        │
        ├──── Cloudflare R2 (object storage)
        │      └── PDFs, images, large NDJSON datasets
        │
        └──── Vercel (frontend)
               └── Next.js portal
                    ├── Report reader
                    ├── ATN tracker
                    ├── Search (full-text + semantic RAG)
                    └── Public API (FastAPI backend)
```

**Cost estimate:** ~$200–250/month production

**Embeddings:** OpenAI `text-embedding-3-large`, 3072 dimensions, multilingual. Stored as NDJSON sidecar files in `embeddings/` within each report folder, then written to `block_vectors` collection in Atlas.

---

## 4. Schema System

### 4.1 Design Principles

- All schemas use **JSON Schema draft-07**
- All schemas use `additionalProperties: false` unless explicitly noted — this is strict by default
- All text fields that are multilingual use **objects keyed by ISO-639 language code** (e.g. `{"en": "...", "hi": "..."}`)
- IDs follow **UPPER-CASE-WITH-HYPHENS** pattern (`^[A-Z0-9][A-Z0-9\-]+[A-Z0-9]$`)
- Ordering uses **decimal seq spacing** (10, 20, 30...) to allow insertion without renumbering
- `additionalProperties: false` is the default; exceptions are noted per schema

### 4.2 ID Conventions

| Type | Pattern | Example |
|------|---------|---------|
| product_id | `{type}{N}-CAG-{year}-{jurisdiction}-{state}` | `AR06-CAG-2023-STATE-MP` |
| unit_id | `{product_id}-{prefix}{N}` | `AR06-CAG-2023-STATE-MP-CH02` |
| block_id | `{unit_id}-{type_prefix}{N}` | `AR06-CAG-2023-STATE-MP-CH02-SEC03-P001` |
| atn_id | `ATN-{product_id}-{chapter}-{N}` | `ATN-AR06-CAG-2023-STATE-MP-CH02-001` |
| annotation_id | `ANN-{unit_id}-{N}` | `ANN-AR06-CH02-P001-001` |
| reference_id | `REF-{product_id}-{N}` | `REF-AR01-CAG-2025-UT-JK-0042` |
| footnote_id | `{unit_id}-FN{N}` | `CH02-FN3` |
| finding_id | same as block_id pattern | |
| dataset_id | `{chapter_prefix}-DS{N}` | `CH02-DS03` |
| state_ut_id | `IN-{2-3 letter code}` | `IN-MP`, `IN-JK`, `IN-LA` |
| entity_id | see §8.2 | `GOI-MIN-FINANCE`, `GOI-AUTH-CBDT` |
| scheme_id | see §8.3 | `GOI-SCH-MGNREGS` |

### 4.3 Multilingual Pattern

All display-facing text fields are multilingual objects:
```json
"title": { "en": "Report of the CAG", "hi": "भारत के नियंत्रक-महालेखापरीक्षक का प्रतिवेदन" }
```
`en` is always required. `hi` is strongly recommended. Other ISO-639 codes are permitted.

### 4.4 Schema Dependency Map

```
product.schema
  └── common_metadata.schema          (product.metadata.common)
  └── audit_report_metadata.schema    (product.metadata.specific for audit_report type)
        └── inheritable_audit_metadata.schema  (audit_report_metadata.inheritable)
        └── reference.schema
  └── structure.schema                (product.structure)
        └── inheritable_audit_metadata.schema  (content_unit.metadata)
        └── reference.schema

manifest.schema                       (entry point, standalone)

content_block.schema                  (stored as NDJSON per chapter)
  └── reference.schema

dataset.schema
  └── reference.schema (via cell cross_ref)

footnote.schema
  └── reference.schema

atn.schema
  └── reference.schema

catalog.schema                        (repository-wide index, pipeline-generated)
```

### 4.5 Schema Version Table

| Schema File | Version | Key Changes in Current Version |
|---|---|---|
| `atn.schema` | **3.2** | `chapter_id` optional at file level; `scope.required` = `[level, report_id]` only; all per-level IDs driven by `allOf` if/then |
| `audit_report_metadata.schema` | **3.5** | `state_ut` object; `report_structure` (standalone/collection); `not_to_be_tabled` status; structured `tabling` object with `lower_house`/`upper_house` |
| `catalog.schema` | **3.3** | `additionalProperties:false` on entity chain objects |
| `common_metadata.schema` | **2.1** | `product_type` taxonomy-driven enum; multilingual `title`, `summary`; `distributions[]` for download links |
| `content_block.schema` | **3.4** | `scope_for_improvement` added to `para_type` and `annotation_type`; `annotations[]` at block level |
| `dataset.schema` | **3.0** | `data_ref` escape hatch for large datasets (NDJSON companion); `oneOf` enforces `data[]` XOR `data_ref`; `summary` field |
| `footnote.schema` | **3.1** | `oneOf` anchor enforcement; `footnote_id` regex |
| `inheritable_audit_metadata.schema` | **3.6** | `examination_coverage` (OVERRIDE, inheritable); `dpc_act_sections` (OVERRIDE, inheritable) |
| `manifest.schema` | **3.1** | `schema_versions` map; `ndjson` in `file_lists` |
| `product.schema` | **2.1** | Base container, largely unchanged |
| `reference.schema` | **3.0** | `target_format` field; `reference_id`; `inverse_relationship_type` |
| `structure.schema` | **3.2** | `executive_summary` on `content_unit` |

---

## 5. Schema Reference — Field by Field

### 5.1 `common_metadata.schema` v2.1

Applied to every product in the repository. All fields optional except `required: [product_id, product_type, title, year, default_language, languages]`.

| Field | Type | Notes |
|-------|------|-------|
| `product_id` | string | Pattern: `^[A-Z0-9][A-Z0-9\-]+[A-Z0-9]$` |
| `product_type` | enum | Values from `taxonomy_product_types.json` |
| `title` | multilingual object | Required |
| `subtitle` | multilingual object | |
| `summary` | multilingual object | Used as search result snippet |
| `description` | multilingual object | Extended description |
| `year` | integer | 1860–2100. Year of publication/tabling |
| `languages` | array of ISO-639 codes | min 1, unique |
| `default_language` | string | ISO-639 code |
| `keywords` | array of strings | |
| `slug` | string | URL-safe: `^[a-z0-9\-]+$` |
| `canonical_url` | URI | |
| `version` | string | `^\d+\.\d+$` — record version |
| `revision_date` | date | |
| `archived_date` | date | |
| `supersedes` | string | product_id of replaced report |
| `superseded_by` | string | Set by pipeline when successor published |
| `citation` | multilingual object | |
| `publisher` | multilingual object | |
| `doi` | string | |
| `distributions` | array | Each: `{format, language, url, size_mb, checksum, checksum_algorithm}`. Formats: pdf/epub/html/docx/odt |
| `related_reports` | array | Each: `{product_id, relationship_type, label}`. Types: same_entity/same_scheme/same_sector/prior_year/follow_up/companion |
| `references` | array | `$ref: reference.schema` |

---

### 5.2 `audit_report_metadata.schema` v3.5

Product-type-specific metadata for `audit_report` products. Structure: `{inheritable, report_level}`.

**`inheritable`:** `$ref: inheritable_audit_metadata.schema` — report-level starting values that cascade down. Do NOT set `audit_findings_categories` here.

**`report_level` required fields:** `report_number`, `jurisdiction`, `audit_report_status`

| Field | Type | Notes |
|-------|------|-------|
| `report_number` | object | `{number: integer, year: integer}` — e.g. Report No. 6 of 2023 |
| `jurisdiction` | enum | `UNION` / `STATE` / `UT` / `LG` |
| `audit_report_status` | enum | `draft` / `submitted_to_government` / `not_to_be_tabled` / `tabled` / `published` / `archived` |
| `date_of_submission_to_government` | date | |
| `tabling` | object | See below |
| `signed_by` | object | `{name, designation, date, place}` — multilingual |
| `countersigned_by` | object | Same structure; typically the CAG of India |
| `pac_report_level` | object | `{selected_for_discussion, discussed, pac_report_reference, discussion_date}` |
| `atn` | object | `{atn_received, atn_date, atn_folder, pending_paragraphs, settled_paragraphs}` |
| `amendment` | object | `{amendment_type, amends_report, amends_blocks[], amendment_description}` |
| `pdf_assets` | object | `{complete: {lang_code: {local_path, url, size_mb, checksum, page_count}}, chapters: {unit_id: {lang_code: ...}}}` |
| `references` | array | |
| `government_context` | object | `{nodal_ministry, nodal_departments[]}` — for portal display |
| `state_ut` | object | Required when jurisdiction=STATE or UT. `{id, name, status_at_report_date}`. `id` must exist in `registry_states_uts.json` |
| `report_structure` | enum | `standalone` (unified engagement) / `collection` (omnibus — chapters are independent audits) |

**`tabling` object:**
```
tabling.applicable = true  → legislature + lower_house required; upper_house present only for bicameral
tabling.applicable = false → submitted_to[] + reason_not_tabled required
```
Bicameral states (have Vidhan Parishad): UP, Bihar, Maharashtra, Karnataka, Telangana, AP

**`state_ut.status_at_report_date`:** Pipeline-computed from `registry_states_uts.json` status_history + report year. Never set manually.

---

### 5.3 `inheritable_audit_metadata.schema` v3.6

The cascade/inheritance schema. Applied at report level (inside `audit_report_metadata`) and at unit level (inside `structure.schema` `content_unit.metadata`). NOT applied at block level.

All fields optional. `additionalProperties: false`.

#### Inheritance semantics (critical — read before writing pipeline code)

| Field | Inheritance mode | Level constraints |
|-------|-----------------|-------------------|
| `impact[]` | **ADDITIVE** — child values merge upward, never replaced | Any level |
| `regions.states_uts` | **ADDITIVE** | Any level |
| `regions.ulbs` | **ADDITIVE** | Any level |
| `regions.pris` | **ADDITIVE** | Any level |
| `referenced_entities[]` | **ADDITIVE** — flat union, dedup by entity_id | Any level |
| `primary_schemes[]` | **ADDITIVE** | Any level |
| `other_schemes[]` | **ADDITIVE** | Any level |
| `main_audited_entities[]` | **ADDITIVE bottom-up** from section level | Report, Chapter, Section only |
| `audit_type[]` | **OVERRIDE** — child replaces parent entirely | Any level |
| `report_sector[]` | **OVERRIDE** | Any level |
| `topics[]` | **ADDITIVE** — chapter topics aggregate upward to report | Report and Chapter only; NOT section |
| `audit_period` | **OVERRIDE** | Any level |
| `other_audited_entities[]` | **OVERRIDE** | Any level |
| `examination_coverage` | **OVERRIDE** | Report level default; override per chapter |
| `dpc_act_sections[]` | **OVERRIDE** — chapter set replaces report set | Report and Chapter; NOT below section |
| `audit_findings_categories[]` | **ADDITIVE bottom-up** — section→chapter→report | **SECTION level ONLY** — never set manually at chapter or report |
| `pac_status` | **RESTRICTED** — chapter level only | **CHAPTER level ONLY** |

**Override mode exception:** A `content_unit` with `metadata_override_mode: replace` receives NO inherited metadata from its parent. Used for chapters in omnibus reports covering unrelated audit contexts.

#### Field reference

| Field | Type | Notes |
|-------|------|-------|
| `audit_type[]` | array of strings | IDs from `taxonomy_audit_type.json` |
| `primary_schemes[]` | array of strings | IDs from `registry_schemes.json` |
| `other_schemes[]` | array of strings | IDs from `registry_schemes.json` |
| `audit_period` | object | `{start_year, end_year}` — financial years |
| `report_sector[]` | array of strings | IDs from `taxonomy_report_sector.json` |
| `audit_findings_categories[]` | array of strings | IDs from `taxonomy_audit_findings_{product_type}.json` (product-type-specific file) |
| `regions` | object | `{states_uts: ["MP","GJ",...], ulbs: [...], pris: [...]}` |
| `topics[]` | array of strings | IDs from `taxonomy_topics.json` |
| `impact[]` | array | Each: `{impact_type, description, amount, unit, currency, approximate, entity_ids[], period}`. Types: financial/social/environmental/regulatory/health/infrastructure/governance/reputational/other |
| `pac_status` | object | `{selected_for_discussion, discussed, discussion_date, discussion_reference, atn_status}` |
| `references[]` | array | `$ref: reference.schema` |
| `main_audited_entities[]` | array | Each: `{ministry, department, autonomous_bodies[], other_bodies[]}` — all entity_ids |
| `other_audited_entities[]` | array | Same structure as main_audited_entities |
| `unit_structure` | enum | `standalone` / `collective`. NOT inherited — set explicitly per unit |
| `examination_coverage` | object | See below |
| `dpc_act_sections[]` | array of enums | DPC Act 1971 sections |

#### `examination_coverage` object

```
required: [coverage_type]
```

| Field | Type | Values |
|-------|------|--------|
| `coverage_type` | enum | `national` / `selected_states` / `single_state` / `headquarter_only` / `multi_state_comparative` |
| `state_ut_ids[]` | array | Required for `selected_states` and `multi_state_comparative`. IDs from `registry_states_uts.json` |
| `selection_basis` | enum | `test_check` / `risk_based` / `all_units` / `purposive` / `random` |
| `sample_size` | object | `{states_examined, districts_examined, units_examined, total_universe}` |
| `coverage_note` | multilingual | Explanatory note |

Key distinction: `jurisdiction` = constitutional accountability (always single); `examination_coverage` = where auditors physically went.

#### `dpc_act_sections[]` enum values

| Value | Subject |
|-------|---------|
| `S13` | Receipts and expenditure of Union and States |
| `S14` | Bodies substantially financed by grants/loans |
| `S15` | All grants or loans given by Union/State |
| `S16` | Audit of receipts of Union or State |
| `S17` | Stores and stock |
| `S18` | Powers of CAG — right of access to records |
| `S19` | Government companies (Companies Act) |
| `S19A` | Corporations established by Parliamentary law |
| `S20` | Certain authorities/bodies — discretion or request |
| `S21` | Authorities entrusted with Union receipts/expenditure |
| `S22` | Audit on application by State Government |
| `S23` | Power to dispense with detailed audit |

---

### 5.4 `structure.schema` v3.2

Defines the document tree. Three top-level arrays: `front_matter`, `content_units`, `back_matter`. Each element is a `content_unit`.

**`content_unit` required:** `unit_id`, `unit_type`, `title`

| Field | Type | Notes |
|-------|------|-------|
| `unit_id` | string | ID pattern |
| `unit_type` | enum | `preface` / `executive_summary` / `chapter` / `section` / `subsection` / `sub_subsection` / `appendix` / `annexure` / `statement` / `schedule` |
| `seq` | number | Unit-scoped display order. Decimal spacing 10/20/30... |
| `title` | multilingual | |
| `executive_summary` | multilingual | Short plain-language summary for TOC preview and unit-level vector search. NOT a content block — this is metadata on the unit |
| `slug` | string | URL-safe |
| `para_number` | string | Official number as printed |
| `toc_include` | boolean | Default true. `sub_subsection` and `annexure` default to false |
| `taggable` | boolean | If true, metadata cascades to children |
| `collapsible` | boolean | Default true |
| `default_collapsed` | boolean | Default false. Use for appendices/annexures |
| `metadata_override_mode` | enum | `merge` (default) / `replace` — see §6 |
| `metadata` | object | `$ref: inheritable_audit_metadata.schema` |
| `translation_status` | object | Keyed by ISO-639: `original` / `human_translated` / `machine_translated` / `pending` / `not_applicable` |
| `references[]` | array | |
| `children[]` | array of strings | Ordered child `unit_id`s |

---

### 5.5 `content_block.schema` v3.4

Stored one block per line in NDJSON files (`content_block_ch{N}.ndjson`).

**Required:** `block_id`, `block_type`, `content`

#### Block types

```
paragraph, heading, list, table, image, image_gallery, figure, map, chart,
live_chart, formula, callout, audit_finding, recommendation, signature_block,
quote, pullquote, sidebar, code, divider
```

#### Core fields (all block types)

| Field | Type | Notes |
|-------|------|-------|
| `block_id` | string | ID pattern |
| `block_type` | enum | See above |
| `unit_id` | string | Containing section/chapter. Set by pipeline |
| `seq` | number | Display order within `unit_id`. Decimal spacing. Set by pipeline |
| `toc_include` | boolean | Default false. True only for `heading` blocks that should appear in TOC |
| `para_number` | string | Official audit para number e.g. `2.3.1`. Critical for ATN/PAC back-referencing |
| `lang` | string | ISO-639 |
| `translation_status` | object | Per-language status |
| `content` | object | Structure governed by `block_type` via `allOf` if/then |
| `block_metadata` | object | Scoped override: `{audit_findings_categories[], key_findings[], referenced_entities[]}` |
| `impact[]` | array | Same structure as inheritable_audit_metadata impact[] |
| `group_id` | string | Group consecutive related blocks (e.g. government_reply + audit_comment) |
| `group_role` | enum | `primary` / `member` |
| `footnote_ids[]` | array | |
| `vector_embedding_id` | string | Pointer to vector store record |
| `embedding_model` | string | e.g. `text-embedding-3-large` |
| `references[]` | array | |
| `annotations[]` | array | Span annotations — see below |

#### `para_type` values (paragraph block type)

```
normal, background, scope, methodology, legal_basis, audit_criteria,
audit_observation, effect, cause, data_analysis, conclusion,
executive_summary, recommendation_summary, best_practice, scope_for_improvement
```

#### `callout_type` values

```
key_finding, note, warning, definition, legal_provision, audit_comment,
conclusion, best_practice, good_practice, adverse_finding
```
Note: `government_reply`, `audit_observation`, `recommendation` were removed — use dedicated `audit_finding` and `recommendation` block types instead.

#### `annotations[]` array

Non-destructive span annotations on paragraph text. Original text is never modified.

| Field | Type | Notes |
|-------|------|-------|
| `annotation_id` | string | `ANN-{block_id}-{N}` |
| `lang` | string | Which language key in `content.text` this applies to |
| `start` | integer | Zero-based character offset (inclusive) |
| `end` | integer | Zero-based character offset (exclusive) |
| `annotation_type` | enum | Same vocabulary as `para_type` (15 values) |
| `source` | enum | `ai` / `human` / `rule_based` |
| `confidence` | 0-1 float | Required for `source=ai` |
| `model` | string | e.g. `claude-sonnet-4-20250514` for `source=ai` |
| `rule_id` | string | For `source=rule_based` |
| `annotated_at` | datetime | |
| `reviewed` | boolean | Human review status. Always `true` for `source=human` |
| `reviewed_by` | string | User ID |
| `reviewed_at` | datetime | |
| `notes` | string | Reviewer note |
| `supersedes[]` | array of annotation_ids | When human corrects an AI annotation |
| `superseded_by` | string | Set by pipeline when this annotation appears in another's `supersedes[]`. Never set manually |

---

### 5.6 `atn.schema` v3.2

Action Taken Note files stored one per chapter in `atn/atn_{chapter_id}.json`. Report-level ATN files (covering whole report) omit `chapter_id`.

**File-level required:** `report_id`, `atn_records[]`

**File-level fields:** `report_id`, `chapter_id` (optional), `chapter_ref` (multilingual), `generated_at`

**`atn_records[]` item required:** `atn_id`, `scope`, `current_status`

#### `scope` object

`required: [level, report_id]` — additional fields required per level via `allOf` if/then:

| Level | Additional required fields |
|-------|--------------------------|
| `report` | *(none beyond report_id)* |
| `chapter` | `chapter_id` |
| `section` | `chapter_id`, `unit_id` |
| `paragraph` | `chapter_id`, `unit_id`, `block_id`, `para_ref` |
| `multi_paragraph` | `chapter_id`, `unit_id`, `block_ids[]` (min 2), `para_refs[]` (min 2) |

Optional scope fields: `recommendation_block_id`, `recommendation_block_ids[]`, `section_ref` (multilingual)

#### ATN record fields

| Field | Type | Notes |
|-------|------|-------|
| `atn_id` | string | `ATN-{product_id}-{chapter}-{N}` |
| `scope` | object | See above |
| `department` | string | entity_id of responsible department |
| `current_status` | enum | `pending` / `received` / `under_review` / `partially_implemented` / `implemented` / `not_implemented` / `not_accepted` / `settled` |
| `current_round` | integer | = `len(rounds[])`. Set by pipeline |
| `settled_date` | date | Only when `current_status=settled` |
| `pac_reference` | string | PAC report reference |
| `follow_up_report_id` | string | product_id of follow-up audit |
| `rounds[]` | array | Full exchange history. See below |
| `notes` | multilingual | Notes across all rounds |
| `references[]` | array | |

#### `rounds[]` item required: `round_number`, `round_type`, `atn_date`, `atn_reference`, `atn_text`, `status_after_round`

| Field | Notes |
|-------|-------|
| `round_type` | `initial` / `follow_up` / `pac_directed` / `revised` / `final` |
| `status_after_round` | Must match `current_status` on the last round — pipeline enforced |
| `audit_office_assessment` | multilingual |
| `assessed_by` | e.g. `AG-MP`, `CAG-HQ` |
| `pac_sitting_reference` | e.g. `3rd Sitting, 14th PAC (2024-25)` |

**Pipeline rule:** `current_round = len(rounds)`. `status_after_round` of last round must equal `current_status`.

---

### 5.7 `dataset.schema` v3.0

Structured tabular data. Either `data[]` (inline) or `data_ref` (NDJSON companion file) — `oneOf` enforces exactly one.

**Required:** `dataset_id`, `columns`, and exactly one of `data` or `data_ref`

| Field | Type | Notes |
|-------|------|-------|
| `dataset_id` | string | e.g. `CH02-DS03` |
| `title` | multilingual | |
| `summary` | multilingual | Natural language description. **Primary text for vector embedding of tabular data** |
| `source_block` | string | block_id of the table block this was extracted from |
| `source` | multilingual | Human-readable data source citation |
| `related_datasets[]` | array | dataset_ids of prior-year versions etc. |
| `cross_report_ref` | string | `product_id/dataset_id` format |
| `unit` | string | Default unit e.g. `₹ in crore` |
| `dataset_type` | enum | `flat` / `hierarchical` / `time_series` / `pivot` / `cross_tab` |
| `columns[]` | array | Column definitions. Each: `{id, label, unit, data_type, currency, is_stub, is_computed, formula, period, group, group_order, align, width_hint}` |
| `header_rows[]` | array | Multi-row merged header structure |
| `data[]` | array | Inline rows. Each row: `{row_id, row_type, group_id, indent_level, style, row_colour, cells{col_id: value}}` |
| `data_ref` | string | Relative path to NDJSON companion. Use when > ~150 rows or cross_report_ref set |
| `footnotes[]` | array | `{marker, text}` |
| `notes` | multilingual | General notes below table |
| `column_group_borders[]` | array | Column IDs after which a thick vertical border is drawn |

`data_ref` example: `"datasets/ndjson/CH02-DS03.ndjson"`

---

### 5.8 `footnote.schema` v3.1

Chapter-level footnote files.

**Required:** `unit_id`, `footnotes[]`

Each footnote **must have exactly one anchor type** — enforced by `oneOf`:
- `anchor_block_id` — for paragraph/list/callout anchors
- `anchor_dataset_id + anchor_row_id + anchor_col_id` — for table cell anchors
- Both — only when the same marker appears in both a block and a table derived from it

| Field | Notes |
|-------|-------|
| `footnote_id` | Pattern: `{unit_id}-FN{N}` |
| `marker` | Printed superscript e.g. `*`, `†`, `1` |
| `footnote_type` | `legal_citation` / `statistical_source` / `data_note` / `cross_reference` / `explanatory` / `editorial` |
| `display_scope` | `chapter` (default) / `section` — where footnote renders |
| `section_id` | unit_id of section — required if `display_scope=section` |
| `text` | multilingual |
| `references[]` | |

---

### 5.9 `reference.schema` v3.0

Typed cross-reference object. Used in blocks, dataset cells, unit metadata, and footnotes.

**Required:** `type`, `target`, `target_format`

| Field | Type | Notes |
|-------|------|-------|
| `reference_id` | string | `REF-{product_id}-{N}`. Set by pipeline |
| `type` | enum | `report` / `chapter` / `section` / `subsection` / `block` / `dataset` / `figure` / `image` / `asset` / `footnote` / `finding` / `recommendation` / `entity` / `location` / `taxonomy` / `legislation` / `external` / `atn` |
| `target_format` | enum | `product_id` / `product_id/unit_id` / `product_id/block_id` / `product_id/dataset_id` / `product_id/atn_id` / `entity_id` / `location_id` / `legislation_code` / `taxonomy_id` / `uri` |
| `target` | string | The actual ID or URI |
| `relationship_type` | enum | `cites` / `confirms` / `contradicts` / `extends` / `follows_up` / `supersedes` / `amends` / `implements` / `evidences` / `related_same_entity` / `related_same_scheme` / `related_same_sector` / `related_prior_year` |
| `inverse_relationship_type` | enum | Set by pipeline. Symmetric `related_*` values are the same in both directions |
| `label` | multilingual | Display label |
| `note` | multilingual | Editorial context |

**Pipeline sets:** `reference_id`, `inverse_relationship_type`

---

### 5.10 `catalog.schema` v3.3

Repository-wide catalog index. Pipeline-generated. One entry per report.

**Required:** `catalog_version`, `generated_at`, `entries[]`

Each entry required fields: `product_id`, `product_type`, `title`, `year`, `default_language`, `languages`, `jurisdiction`, `audit_status`

Entry fields mirror `common_metadata` and `audit_report_metadata` for search/filter. Key additions: `has_atn`, `has_pdfs`, `has_distributions`, `report_path`, `last_indexed`.

---

### 5.11 `manifest.schema` v3.1

Entry point for a report folder. Lists every file with SHA-256 checksums.

**Required:** `product_id`, `product_type`, `year`, `generated_at`

| Field | Notes |
|-------|-------|
| `schema_versions` | Object mapping schema name → `$version` string at manifest generation time. Used to detect schema drift on re-ingestion |
| `file_checksums` | `{relative_path: sha256_hex}` for all JSON files |
| `file_lists` | Categorised: `metadata`, `structure`, `units[]`, `blocks[]`, `datasets[]`, `footnotes[]`, `atn[]`, `pdfs[]`, `ndjson[]`, `assets[]`, `other[]` |
| `files` | DEPRECATED in v3. Retained for backward compatibility |

---

### 5.12 `product.schema` v2.1

Top-level container. Wraps `common_metadata`, `audit_report_metadata`, `structure`, and `datasets`.

```json
{
  "product": {
    "metadata": {
      "common": { "$ref": "common_metadata.schema" },
      "specific": { "...audit_report_metadata or other product type..." }
    },
    "structure": { "$ref": "structure.schema" },
    "datasets": [ ... ]
  }
}
```

**Pending:** `specific` field needs `if/then` conditional validation against the correct type-specific schema based on `product_type`.

---

## 6. Inheritance System

The inheritance system allows metadata to be declared once at the report level and cascade down without duplication. Pipeline resolves inheritance before writing to Atlas.

```
report-level metadata (audit_report_metadata.inheritable)
    │
    ▼  cascade (merge or replace per metadata_override_mode)
chapter-level metadata (content_unit.metadata)
    │
    ▼  cascade
section-level metadata (content_unit.metadata)
    │
    ▼  cascade
block-level (block_metadata — only 3 fields: audit_findings_categories, key_findings, referenced_entities)
```

**`metadata_override_mode: merge`** (default) — inheritable fields combine with parent per the ADDITIVE/OVERRIDE rules in §5.3.

**`metadata_override_mode: replace`** — this unit's metadata is standalone. No parent inheritance. Used for chapters in omnibus/collection reports covering different states or departments.

**Aggregation direction for bottom-up additive fields:**
- `audit_findings_categories`: section → chapter → report (pipeline computes chapter and report values; never set manually above section)
- `main_audited_entities` (from section level): section entities deduplicated upward into chapter and report
- `topics`: chapter topics unioned with explicitly-set report topics to form final report topics

---

## 7. Taxonomies

### 7.1 `taxonomy_product_types.json`

6 entries. Enum values used in `product_type` field across all schemas.

| ID | Label |
|----|-------|
| `audit_report` | Audit Report |
| `accounts_report` | Accounts Report |
| `state_finance_report` | State Finance Report |
| `study_report` | Study Report |
| `audit_impact_report` | Audit Impact Report |
| `other` | Other |

Each entry has: `atn_applicable` (bool), `pac_applicable` (bool), `description`.

**Sync script:** `scripts/sync_product_type_enum.py` — syncs the enum list from this file into `common_metadata.schema`, `catalog.schema`, `manifest.schema`, and `product.schema`. Run after any change. `--check` flag for CI gate.

---

### 7.2 `taxonomy_audit_type.json`

11 entries. Used in `inheritable_audit_metadata.audit_type[]`.

| ID | Label | ISSAI Reference |
|----|-------|----------------|
| `ATYPE-COMPLIANCE` | Compliance Audit | ISSAI 400 |
| `ATYPE-PERFORMANCE` | Performance Audit | ISSAI 300 |
| `ATYPE-FINANCIAL` | Financial Audit | ISSAI 200 |
| `ATYPE-IT-AUDIT` | IT Audit | ISSAI 5300 |
| `ATYPE-CERTIFICATION` | Certification Audit | ISSAI 200 |
| `ATYPE-ENVIRONMENTAL` | Environmental Audit | ISSAI 5130 |
| `ATYPE-IT-ASSISTED` | IT-Assisted Audit | ISSAI 5400 |
| `ATYPE-OUTCOME` | Outcome Audit | — |
| `ATYPE-HORIZONTAL` | Horizontal Audit | — |
| `ATYPE-COMBINED` | Combined Audit | — |
| `ATYPE-SPECIAL-PURPOSE` | Special Purpose Audit | — |

**Key distinctions:**
- `ATYPE-IT-AUDIT` = IT systems are the **subject** of audit
- `ATYPE-IT-ASSISTED` = data analytics / CAAT is the **method** of audit
- `ATYPE-PERFORMANCE` = 3Es of programme implementation (economy, efficiency, effectiveness)
- `ATYPE-OUTCOME` = long-term real-world impact of a programme
- `ATYPE-HORIZONTAL` = cross-cutting audit across multiple ministries simultaneously

---

### 7.3 `taxonomy_report_sector.json`

37 entries. 7 top-level sectors, 30 sub-sectors. Used in `inheritable_audit_metadata.report_sector[]`.

| Sector ID | Label | Sub-sectors |
|-----------|-------|-------------|
| `SECT-CIVIL` | Civil | *(flat — no sub-sectors)* |
| `SECT-COMMERCIAL` | Commercial | `SECT-COMM-PSU-CENTRAL`, `SECT-COMM-PSU-STATE`, `SECT-COMM-AUTONOMOUS`, `SECT-COMM-EAP` |
| `SECT-REVENUE` | Revenue | `SECT-REV-DIRECT-TAX`, `SECT-REV-INDIRECT-TAX`, `SECT-REV-STATE-TAX`, `SECT-REV-NON-TAX`, `SECT-REV-RECEIPTS-ADMIN` |
| `SECT-DEFENCE` | Defence | `SECT-DEF-ARMY`, `SECT-DEF-NAVY`, `SECT-DEF-AIRFORCE`, `SECT-DEF-ORDNANCE`, `SECT-DEF-PROCUREMENT`, `SECT-DEF-COAST-GUARD` |
| `SECT-TELECOM` | Telecommunications | `SECT-TEL-DOT`, `SECT-TEL-PSU`, `SECT-TEL-SPECTRUM`, `SECT-TEL-DIGITAL` |
| `SECT-RAILWAYS` | Railways | `SECT-RAIL-OPERATIONS`, `SECT-RAIL-CONSTRUCTION`, `SECT-RAIL-PROCUREMENT`, `SECT-RAIL-PSU`, `SECT-RAIL-FINANCE` |
| `SECT-LOCAL-GOVT` | Local Government | `SECT-LG-ULB`, `SECT-LG-PRI`, `SECT-LG-CANTONMENT`, `SECT-LG-PESA`, `SECT-LG-ADC`, `SECT-LG-REGIONAL-COUNCIL` |

**Local Government boundary notes:**
- `SECT-LG-PESA` — PESA Act 1996 Scheduled Areas in 10 states only. Regular gram panchayats in those states still use `SECT-LG-PRI`
- `SECT-LG-ADC` — main Sixth Schedule district councils (Assam, Meghalaya, Tripura, Mizoram)
- `SECT-LG-REGIONAL-COUNCIL` — sub-divisional regional councils + Ladakh AHDC + Darjeeling GHC
- `SECT-LG-CANTONMENT` — Cantonment Boards straddle Local Government and Defence; primary sector is this

---

### 7.4 `taxonomy_audit_findings_{product_type}.json`

**One file per product type** — naming convention: `taxonomy_audit_findings_{product_type}.json`.
Each file declares which product types it covers via a root `product_types[]` field.

This design decouples the finding classification vocabulary per CAG product type.
`audit_report` and `accounts_report` have structurally different findings (DPC Act sections, appropriation heads, finance accounts categories etc.) and need separate taxonomies.
`validate_registry_refs.py` reads `product_type` from `manifest.json` and loads the appropriate file automatically. Scripts never need to change when a new product type is added — only a new taxonomy file.

**Current files:**

| File | product_types | Status | Entries |
|------|--------------|--------|---------|
| `taxonomy_audit_findings_audit_report.json` | `["audit_report"]` | ✓ v1.0 | 470 (18 cat / 79 sub / 373 detail) |
| `taxonomy_audit_findings_accounts_report.json` | `["accounts_report"]` | ⏳ PENDING | — |

**Entry fields:** `id` (snake_case), `label` (multilingual), `short_label` (multilingual, ≤5 words), `level` (`category` / `sub_category` / `detail`), `parent_id` (null for category), `sub_categories[]` (child IDs, on category entries only), `description` (multilingual), `deprecated`

**3-level structure:** `category` → `sub_category` → `detail`

**18 top-level categories in `taxonomy_audit_findings_audit_report.json`:**

| Category ID | Label | Sub-cat | Detail |
|-------------|-------|---------|--------|
| `financial_irregularities` | Financial Irregularities | 11 | 63 |
| `contract_procurement` | Contract & Procurement Failures | 4 | 29 |
| `works_technical_quality` | Works & Technical Quality | 5 | 20 |
| `revenue_receipts` | Revenue & Receipts | 4 | 23 |
| `grants_loans` | Grants & Loans | 4 | 16 |
| `scheme_implementation` | Scheme Implementation Failures | 5 | 19 |
| `asset_management` | Asset Management & Inventory | 4 | 15 |
| `human_resources_staffing` | Human Resources & Staffing | 12 | 61 |
| `pay_pension` | Pay, Allowances & Pension | 3 | 19 |
| `subsidy_dbt` | Subsidy & DBT Leakage | 3 | 9 |
| `public_enterprises` | Public Enterprises & PSUs | 3 | 16 |
| `regulatory_compliance` | Regulatory & Statutory Compliance | 3 | 14 |
| `governance_monitoring` | Governance & Monitoring Failures | 4 | 15 |
| `data_information` | Data, Information & IT Systems | 3 | 12 |
| `environmental_social` | Environmental & Social Safeguards | 3 | 12 |
| `disaster_relief` | Disaster Relief & SDRF | 2 | 8 |
| `performance_audit_3e` | Performance Audit — Economy, Efficiency, Effectiveness | 3 | 12 |
| `audit_followup` | Audit Follow-Up & Previous Para Compliance | 3 | 10 |

**Usage:** Set `audit_findings_categories[]` in `block_metadata` at **SECTION level only**. Pipeline aggregates section → chapter → report. Never set manually at chapter or report level.

---

### 7.5 `taxonomy_topics.json` v1.0

257 entries. 33 top-level topics, 224 sub-topics. Derived from the Seventh, Eleventh and Twelfth Schedules of the Constitution of India. Used in `inheritable_audit_metadata.topics[]`.

**Entry fields:** `id` (snake_case string), `label` (multilingual), `short_label` (multilingual, ≤4 words), `level` (`topic` / `sub_topic`), `parent_id` (null for top-level), `sub_topics[]` (child IDs), `description`, `deprecated`

**Usage rule:** Use the most specific applicable sub-topic ID, not the parent. Multiple topics permitted per unit. Set at report level for report-wide themes; set at chapter level for chapter-specific themes. Never set at section level.

**33 top-level topics and their sub-topic counts:**

| Topic ID | Label | Sub-topics |
|----------|-------|-----------|
| `defence_security` | Defence & National Security | 5 |
| `foreign_affairs` | Foreign Affairs & International Relations | 4 |
| `railways` | Railways | 6 |
| `road_transport` | Road Transport & Highways | 5 |
| `shipping_ports` | Shipping, Ports & Waterways | 4 |
| `civil_aviation` | Civil Aviation | 5 |
| `posts_telecom` | Posts & Telecommunications | 5 |
| `banking_finance` | Banking & Financial Services | 5 |
| `insurance` | Insurance | 4 |
| `currency_forex` | Currency, Coinage & Foreign Exchange | 4 |
| `direct_taxation` | Direct Taxation | 5 |
| `indirect_taxation` | Indirect Taxation | 5 |
| `trade_commerce` | Trade, Commerce & Industry Regulation | 5 |
| `industry_manufacturing` | Industry & Manufacturing | 5 |
| `mining_minerals` | Mining & Minerals | 5 |
| `energy_electricity` | Energy & Electricity | 6 |
| `environment_forests` | Environment & Forests | 9 |
| `water_resources` | Water Resources & Irrigation | 9 |
| `agriculture_food` | Agriculture, Food & Rural Livelihoods | 7 |
| `public_health` | Public Health & Family Welfare | 7 |
| `education_research` | Education, Science & Research | 7 |
| `labour_welfare` | Labour, Employment & Social Welfare | 6 |
| `land_housing` | Land, Housing & Urban Development | 6 |
| `law_justice` | Law, Justice & Constitutional Bodies | 6 |
| `public_finance` | Public Finance & Fiscal Management | 9 |
| `elections_democracy` | Elections & Democratic Processes | 5 |
| `rural_governance` | Rural Governance & Panchayati Raj | 12 |
| `rural_infrastructure` | Rural Infrastructure | 10 |
| `agri_allied_district` | Agriculture, Allied Sectors & District-Level | 8 |
| `urban_governance` | Urban Governance & Municipal Bodies | 14 |
| `urban_infrastructure` | Urban Infrastructure & Services | 12 |
| `digital_governance` | Digital Governance & Emerging Technology | 11 |
| `climate_disaster` | Climate, Disaster & Resilience Governance | 8 |

---

## 8. Registries

### 8.1 `registry_states_uts.json`

37 entries (36 active + 1 inactive). All Indian States and Union Territories.

**ID pattern:** `IN-{2-3 letter code}` e.g. `IN-MP`, `IN-JK`, `IN-LA`

Each entry fields: `id`, `iso_3166_2`, `name` (multilingual), `type` (state/ut_with_legislature/ut_without_legislature), `active` (bool), `capital` (multilingual), `status_history[]`, `name_history[]`, `legislature`, `bicameral` (bool), `pesa_state` (bool), `sixth_schedule_areas` (bool), `predecessor_id`, `successor_id`, `dissolved_on`, `dissolution_reason`

**All active entries:**

| ID | Name | Type |
|----|------|------|
| IN-AN | Andaman and Nicobar Islands | UT without legislature |
| IN-AP | Andhra Pradesh | State |
| IN-AR | Arunachal Pradesh | State |
| IN-AS | Assam | State |
| IN-BR | Bihar | State |
| IN-CH | Chandigarh | UT without legislature |
| IN-CT | Chhattisgarh | State |
| IN-DD | Dadra and Nagar Haveli and Daman and Diu | UT without legislature |
| IN-DL | Delhi | UT with legislature |
| IN-GA | Goa | State |
| IN-GJ | Gujarat | State |
| IN-HR | Haryana | State |
| IN-HP | Himachal Pradesh | State |
| IN-JH | Jharkhand | State |
| IN-JK | Jammu and Kashmir | UT with legislature |
| IN-KA | Karnataka | State |
| IN-KL | Kerala | State |
| IN-LA | Ladakh | UT without legislature |
| IN-LD | Lakshadweep | UT without legislature |
| IN-MP | Madhya Pradesh | State |
| IN-MH | Maharashtra | State |
| IN-MN | Manipur | State |
| IN-ML | Meghalaya | State |
| IN-MZ | Mizoram | State |
| IN-NL | Nagaland | State |
| IN-OD | Odisha | State |
| IN-PB | Punjab | State |
| IN-PY | Puducherry | UT with legislature |
| IN-RJ | Rajasthan | State |
| IN-SK | Sikkim | State |
| IN-TN | Tamil Nadu | State |
| IN-TG | Telangana | State |
| IN-TR | Tripura | State |
| IN-UP | Uttar Pradesh | State |
| IN-UK | Uttarakhand | State |
| IN-WB | West Bengal | State |

**Inactive:** `IN-DN` (Dadra and Nagar Haveli — merged into IN-DD in 2020)

**`status_at_report_date`** on `audit_report_metadata.state_ut` is pipeline-computed from `status_history + report year`. JK changed from state to UT in 2019; J&K/Ladakh split. Pipeline must handle this.

---

### 8.2 `registry_entities.json`

12 sample entries currently. Full registry under construction. Government ministries, departments, PSUs, statutory bodies, constitutional bodies.

**ID convention:**

| Prefix | Type |
|--------|------|
| `CONST-` | Constitutional bodies (CAG, Election Commission, etc.) |
| `GOI-MIN-` | Union Ministries |
| `GOI-DEPT-` | Departments under Union Ministries |
| `GOI-OFF-` | Offices under departments |
| `GOI-PSU-` | Central Public Sector Undertakings |
| `GOI-AUTH-` | Statutory authorities/boards (CBDT, CBIC, etc.) |
| `STAT-` | Statutory/quasi-governmental bodies (NITI Aayog, etc.) |
| `IN-{ST}-DEPT-` | State departments e.g. `IN-MP-DEPT-RURAL-DEV` |
| `IN-{ST}-PSU-` | State PSUs |
| `IN-{ST}-AUTH-` | State statutory authorities |

**Each entry:** `id`, `name` (multilingual), `level` (constitutional/ministry/department/office/psu/authority/statutory), `active` (bool), `parent_id`, `functions[]` (from function_vocabulary), `jurisdiction`, `state_ut_id` (for state entities), `archived`, `dissolved_on`, `dissolution_reason`, `dissolution_type` (merged/abolished/renamed/restructured)

**Current 12 sample entries:**
- `CONST-CAG` — Office of the CAG of India
- `GOI-MIN-FINANCE` → `GOI-DEPT-REVENUE` → `GOI-AUTH-CBDT`, `GOI-AUTH-CBIC`
- `GOI-MIN-RURAL-DEV`
- `GOI-MIN-HEALTH`
- `GOI-MIN-POWER`
- `GOI-PSU-ONGC`
- `STAT-NITI-AAYOG`
- `STAT-PLANNING-COMMISSION` (archived — dissolved 2014, succeeded by NITI Aayog)
- `IN-MP-DEPT-RURAL-DEV`

**Note:** `function_vocabulary` is inline in the file (~18 entries). Promote to a separate taxonomy file when it reaches ~50 entries.

---

### 8.3 `registry_schemes.json`

9 sample entries. Government schemes and programmes. Each phase/successor scheme is a separate entry.

**ID convention:**
- `GOI-SCH-{ABBR}` — Central Government scheme
- `GOI-FUND-{ABBR}` — Central Government fund
- `IN-{ST}-SCH-{ABBR}` — State scheme

**Each entry:** `id`, `name` (multilingual), `ministry_id`, `department_id`, `launch_year`, `end_year`, `status` (active/completed/merged/subsumed/archived), `active` (bool), `predecessor_id`, `successor_id`, `description` (multilingual), `sector`, `scheme_type` (centrally_sponsored/central/state/etc.)

**Current 9 sample entries with lifecycle chains:**

| ID | Name | Status | Chain |
|----|------|--------|-------|
| `GOI-SCH-MGNREGS` | MGNREGS | active | — |
| `GOI-SCH-PMGSY` | PMGSY | completed | → PMGSY-II |
| `GOI-SCH-PMGSY-II` | PMGSY Phase II | completed | PMGSY → PMGSY-II → PMGSY-III |
| `GOI-SCH-PMGSY-III` | PMGSY Phase III | active | PMGSY-II → |
| `GOI-SCH-RGGVY` | RGGVY | archived/merged | → DDUGJY |
| `GOI-SCH-DDUGJY` | DDUGJY | archived/subsumed | RGGVY → DDUGJY → RDSS |
| `GOI-SCH-RDSS` | RDSS | active | DDUGJY → |
| `GOI-SCH-NHM` | National Health Mission | active | NRHM → NHM |
| `GOI-SCH-NRHM` | NRHM | archived/subsumed | → NHM |

---

## 9. Pipeline and Scripts

### `repo_layout.py` — the path contract

**Every script imports this module instead of hard-coding paths.** It is the single source of truth for the folder structure.

Key exports:

| Symbol | Returns | Notes |
|--------|---------|-------|
| `REPO_ROOT` | `Path` | |
| `SCHEMAS_DIR` | `Path` | |
| `TAXONOMIES_DIR` | `Path` | |
| `REPORTS_DIR` | `Path` | |
| `all_report_dirs()` | `list[Path]` | Finds all folders containing `manifest.json` |
| `locate_report(product_id)` | `Path \| None` | Searches full tree — no hard-coded path needed |
| `report_dir(product_type, year, product_id, jurisdiction, state_ut_id)` | `Path` | Constructs the canonical path |
| `product_id_from_dir(folder)` | `str` | `folder.name` |
| `state_folder_name(state_ut_id)` | `str` | `IN-MP` → `in-mp` |
| `units_dir(report_dir)` | `Path` | `report_dir/units/` |
| `blocks_dir(report_dir)` | `Path` | `report_dir/blocks/` |
| `atn_dir(report_dir)` | `Path` | `report_dir/atn/` |
| `datasets_dir(report_dir)` | `Path` | `report_dir/datasets/` |
| `ndjson_dir(report_dir)` | `Path` | `report_dir/datasets/ndjson/` |
| `footnotes_dir(report_dir)` | `Path` | `report_dir/footnotes/` |
| `embeddings_dir(report_dir)` | `Path` | `report_dir/embeddings/` |
| `block_ndjson_files(report_dir)` | `list[Path]` | `blocks/content_block_*.ndjson` |
| `atn_json_files(report_dir)` | `list[Path]` | `atn/atn_*.json` |
| `unit_json_files(report_dir)` | `list[Path]` | `units/*.json` |
| `dataset_json_files(report_dir)` | `list[Path]` | `datasets/*.json` |
| `footnote_json_files(report_dir)` | `list[Path]` | `footnotes/footnotes_*.json` |
| `embedding_sidecar_files(report_dir)` | `list[Path]` | `embeddings/embeddings_*.ndjson` |
| `load_manifest(report_dir)` | `dict \| None` | |
| `load_metadata(report_dir)` | `dict \| None` | |
| `load_structure(report_dir)` | `dict \| None` | |

### 9.1 Validation Scripts (auto, CI)

All run on every push/PR via `validate.yml`.

#### `validate_report.py`
Validates one or all report packages against JSON schemas.
```
python scripts/validate_report.py --all
python scripts/validate_report.py --product-id AR06-CAG-2023-STATE-MP
python scripts/validate_report.py --path reports/audit_report/2023/state/in-mp/AR06-CAG-2023-STATE-MP
```
Uses `repo_layout.locate_report()` to find reports anywhere in the nested tree — caller needs no path knowledge. Validates: `manifest.json`, `metadata.json`, `structure.json` at report root; `units/*.json` (JSON parse); `blocks/content_block_*.ndjson` line-by-line against `content_block.schema`; `atn/atn_*.json`; `datasets/*.json`; `footnotes/footnotes_*.json`. Uses `Draft7Validator` with a shared `RefResolver` against `schemas/`.

#### `validate_registry_refs.py`
Checks every registry ID referenced in report files exists in the corresponding registry/taxonomy.
```
python scripts/validate_registry_refs.py
python scripts/validate_registry_refs.py --product-id AR06-CAG-2023-STATE-MP
```
Checks: `state_ut.id`, `examination_coverage.state_ut_ids[]`, `main_audited_entities[]`, `other_audited_entities[]`, `primary_schemes[]`, `other_schemes[]`, `report_sector`, `audit_type`, `product_type`. Recurses into `structure.json` unit tree and individual `units/*.json` files.

#### `check_registry_integrity.py`
Validates internal consistency of all registry/taxonomy files.
```
python scripts/check_registry_integrity.py
```
Checks per file: no duplicate IDs; cross-references (`parent_id`, `predecessor_id`, `successor_id`) point to real entries; inactive/archived entries have `dissolved_on` and `dissolution_reason`.

#### `sync_product_type_enum.py`
Syncs `product_type` enum values from `taxonomy_product_types.json` into 4 schema files.
```
python taxonomies/sync_product_type_enum.py         # apply changes
python taxonomies/sync_product_type_enum.py --check  # CI check mode (no writes)
```

#### `bump_schema_versions.py`
Detects changed schema files via `git diff` and bumps version numbers. Updates `schema_versions` in manifest files.
```
python scripts/bump_schema_versions.py                          # auto-detect and bump
python scripts/bump_schema_versions.py --dry-run                # CI check mode
python scripts/bump_schema_versions.py --schema atn.schema --level minor
```
Bump levels: `major` (removed required field/changed type), `minor` (new required field/new enum — default), `patch` (alias for minor in this two-part version scheme).

---

### 9.2 Ingestion Scripts (manual trigger)

Run via `ingest.yml` workflow dispatch or locally.

#### `generate_embeddings.py`
Generates `text-embedding-3-large` (3072 dims) embeddings for all content blocks.
```
python scripts/generate_embeddings.py --product-id AR06-CAG-2023-STATE-MP
python scripts/generate_embeddings.py --product-ids "ID1,ID2"
python scripts/generate_embeddings.py --all
python scripts/generate_embeddings.py --all --force
```
Requires: `OPENAI_API_KEY` env var.

Behaviour:
- Reads from `blocks/content_block_*.ndjson`
- Builds embedding text from: heading + subheading + paragraph text (English preferred) + table headers/rows (capped at 10) + list items (capped at 20)
- SHA-256 checksum per block for skip logic; `--force` overrides
- Writes sidecar: `embeddings/embeddings_{chapter}.ndjson` — one line per block: `{block_id, embedding}`
- Writes checksum index: `embeddings/embeddings_{chapter}.checksums.json`
- Sidecar stem mirrors source: `blocks/content_block_ch02.ndjson` → `embeddings/embeddings_ch02.ndjson`
- Batches 100 texts per API call with 0.5s sleep between batches

#### `write_to_atlas.py`
Upserts all 4 MongoDB collections.
```
python scripts/write_to_atlas.py --product-id AR06-CAG-2023-STATE-MP
python scripts/write_to_atlas.py --product-ids "ID1,ID2"
python scripts/write_to_atlas.py --all
python scripts/write_to_atlas.py --all --dry-run
python scripts/write_to_atlas.py --all --force
```
Requires: `MONGODB_URI` env var.

Behaviour:
- Uses `repo_layout.locate_report()` to find report folders anywhere in the nested tree
- Checksum gate: SHA-256 of `file_checksums` dict from manifest; skips if unchanged (unless `--force`)
- Reads blocks from `blocks/content_block_*.ndjson`, ATN records from `atn/atn_*.json`
- Embeddings loaded from `embeddings/embeddings_*.ndjson` sidecars (if present)
- Upserts: `report_meta` (1 doc/report), `block_vectors` (1 doc/block + embedding), `atn_index` (1 doc/ATN record), `catalog_index` (1 doc/entity chain)
- `--dry-run` logs counts without writing

#### `invalidate_cache.py`
Deletes Redis cache keys after ingestion.
```
python scripts/invalidate_cache.py --product-ids AR06-CAG-2023-STATE-MP
python scripts/invalidate_cache.py --all-globals
```
Requires: `REDIS_URL` env var.

Per-report keys: `toc:{id}`, `filters:{id}`, `report_meta:{id}`, `atn_summary:{id}`
Global keys: `global:filter_options`, `global:report_list`, `global:sector_counts`

---

### 9.3 GitHub Actions Workflows

#### `validate.yml`
- Trigger: every push to any branch, every PR to main
- Steps: install deps → `sync_product_type_enum --check` → `check_registry_integrity` → `validate_registry_refs` → `validate_report --all` → `bump_schema_versions --dry-run`

#### `ingest.yml`
- Trigger: `workflow_dispatch` with inputs:
  - `product_ids`: comma-separated (blank = auto-detect from git diff)
  - `force_reingest`: boolean
  - `skip_embeddings`: boolean
  - `dry_run`: boolean
- Environment: `production`
- Secrets required: `OPENAI_API_KEY`, `MONGODB_URI`, `REDIS_URL`
- Steps: checkout (fetch-depth: 2) → validation gate → resolve product IDs → `generate_embeddings` → `write_to_atlas` → `invalidate_cache`
- Auto-detection: `git diff HEAD~1 HEAD` filtered to `reports/` paths; Python walks upward from each changed file to find the enclosing folder containing `manifest.json`, extracts its name as the `product_id`. Handles both UNION (`reports/{type}/{year}/{product_id}/`) and STATE/UT/LG (`reports/{type}/{year}/{state_code}/{product_id}/`) layouts transparently.

---

### 9.4 Full Pipeline Responsibilities

The ingestion pipeline (not the JSON files) is responsible for computing and setting these values:

| Responsibility | Notes |
|---|---|
| Assign `seq` values | 10, 20, 30... for blocks and units |
| Assign `reference_id` | `REF-{product_id}-{N:04d}` |
| Set `inverse_relationship_type` | Derived from `relationship_type` |
| Compute `absolute_seq` | Transient, render-time only — not stored |
| Validate `audit_findings_categories` not manually set at chapter/report | Reject if found |
| Validate `pac_status` only at chapter level | Reject if found below chapter |
| Generate `schema_versions` in manifest | At manifest generation time |
| Verify `file_checksums` on re-ingestion | |
| Qualify local IDs to `product_id/local_id` format | For cross-report references |
| Sync `product_type` enum | From taxonomy on any taxonomy edit |
| Set `current_round = len(rounds[])` on ATN records | |
| Validate `status_after_round` of last round matches `current_status` | |
| Set `superseded_by` on annotations listed in another's `supersedes[]` | |
| Compute `pending_paragraphs` / `settled_paragraphs` in ATN summary | |
| Compute `state_ut.status_at_report_date` | From registry `status_history` + report year |
| Aggregate `audit_findings_categories` section → chapter → report | |
| Aggregate `topics` chapter → report | Union with explicitly-set report topics |
| Aggregate `main_audited_entities` section → chapter → report | Dedup by entity chain |
| Infer `unit_structure` default from `report_structure` | `collection` → chapters default to `standalone`; `standalone` → chapters default to `collective` |

---

## 10. MongoDB Atlas Collections

Database: `cag_audit`

| Collection | Key | Contents |
|---|---|---|
| `report_meta` | `product_id` | Full metadata + structure summary + ingestion metadata |
| `block_vectors` | `block_id` | Block fields + `embedding` (3072-dim float array) for vector search |
| `atn_index` | `atn_id` | ATN record with rounds, status, scope |
| `catalog_index` | `entity_id` | Catalog entity chains per report |

**All collections are derived** — the Git repository is the source of truth. Atlas can be fully rebuilt from the repository by running `write_to_atlas.py --all --force`.

**Vector search:** Atlas Vector Search on `block_vectors.embedding`, model `text-embedding-3-large`, 3072 dims.

---

## 11. Repository Status

### What Is Complete

| Layer | Item | Status |
|-------|------|--------|
| **Schemas** | All 12 schema files | ✓ v3.x — stable |
| **Taxonomy** | `taxonomy_product_types.json` | ✓ v1.0 — 6 entries |
| **Taxonomy** | `taxonomy_audit_type.json` | ✓ v1.0 — 11 entries |
| **Taxonomy** | `taxonomy_report_sector.json` | ✓ v1.0 — 37 entries |
| **Taxonomy** | `taxonomy_topics.json` | ✓ v1.0 — 257 entries (33 topics, 224 sub-topics) |
| **Taxonomy** | `taxonomy_audit_findings_audit_report.json` | ✓ v1.0 — 470 entries (18/79/373) |
| **Registry** | `registry_states_uts.json` | ✓ v1.0 — 37 entries (36 active + 1 dissolved) |
| **Registry** | `registry_entities.json` | ✓ v1.0 — 12 sample entries |
| **Registry** | `registry_schemes.json` | ✓ v1.0 — 9 sample entries |
| **Scripts** | `repo_layout.py` | ✓ — canonical path contract |
| **Scripts** | `validate_report.py` | ✓ — schema validation, all sub-folders |
| **Scripts** | `validate_registry_refs.py` | ✓ — cross-file ref checks + findings taxonomy |
| **Scripts** | `check_registry_integrity.py` | ✓ — all 8 taxonomy/registry files |
| **Scripts** | `bump_schema_versions.py` | ✓ |
| **Scripts** | `sync_product_type_enum.py` | ✓ |
| **Scripts** | `generate_embeddings.py` | ✓ |
| **Scripts** | `write_to_atlas.py` | ✓ |
| **Scripts** | `invalidate_cache.py` | ✓ |
| **CI/CD** | `validate.yml` | ✓ — runs on every push/PR |
| **CI/CD** | `ingest.yml` | ✓ — manual dispatch |

---

## 12. First Report — Quick Start

This section is a step-by-step guide for preparing and ingesting the first report into the repository.

### Step 1 — GitHub repository setup

```bash
# Create repo, push everything that is already built
git init
git add schemas/ taxonomies/ scripts/ .github/ requirements.txt README.md
git commit -m "chore: initial repository scaffold"
git remote add origin https://github.com/your-org/cag-audit-reports.git
git push -u origin main
```

Configure GitHub Actions secrets in **Settings → Secrets and variables → Actions**:
- `OPENAI_API_KEY`
- `MONGODB_URI`
- `REDIS_URL`

Add `embeddings/` to `.gitignore`:
```
reports/**/embeddings/
```

---

### Step 2 — Choose the first report

Pick any completed audit report you have a PDF for. Recommended: a **State Audit Report** (`audit_report`, `STATE` jurisdiction) — it exercises the most fields.

You need:
- The PDF (one per language)
- The official report number and year
- The tabling date (or approximate)

---

### Step 3 — Create the folder structure

```bash
# Example: CAG Report No. 6 of 2023, Madhya Pradesh
PRODUCT_ID="AR06-CAG-2023-STATE-MP"
mkdir -p reports/audit_report/2023/state/in-mp/$PRODUCT_ID/{units,blocks,atn,datasets/ndjson,footnotes,pdfs/en/{complete,chapters},assets}
```

---

### Step 4 — Write `manifest.json`

```json
{
  "$schema": "../../../../../schemas/manifest.schema",
  "$version": "3.1",
  "product_id": "AR06-CAG-2023-STATE-MP",
  "product_type": "audit_report",
  "year": 2023,
  "title": { "en": "Report of the Comptroller and Auditor General of India — General and Social Sector — for the year ended 31 March 2023", "hi": "..." },
  "languages": ["en"],
  "schema_versions": {
    "manifest.schema": "3.1",
    "audit_report_metadata.schema": "3.5",
    "inheritable_audit_metadata.schema": "3.6",
    "structure.schema": "3.2",
    "content_block.schema": "3.4",
    "atn.schema": "3.2"
  },
  "file_lists": {
    "metadata":  "metadata.json",
    "structure":  "structure.json",
    "units":     ["units/AR06-CAG-2023-STATE-MP-CH01.json"],
    "blocks":    ["blocks/content_block_ch01.ndjson"],
    "pdfs":      ["pdfs/en/complete/AR06-CAG-2023-STATE-MP-en.pdf"]
  },
  "file_checksums": {}
}
```

> Compute `file_checksums` last: `sha256sum` each listed file and populate the map.

---

### Step 5 — Write `metadata.json`

```json
{
  "$schema": "../../../../../schemas/audit_report_metadata.schema",
  "inheritable": {
    "audit_type": ["ATYPE-COMPLIANCE"],
    "report_sector": ["SECT-CIVIL"],
    "audit_period": { "from": "2022-04-01", "to": "2023-03-31" },
    "main_audited_entities": ["DEPT-MP-FINANCE"],
    "primary_schemes": [],
    "topics": ["public_finance", "governance_monitoring"]
  },
  "report_level": {
    "report_number": "6",
    "jurisdiction": "STATE",
    "state_ut": {
      "id": "IN-MP",
      "name": { "en": "Madhya Pradesh" },
      "status_at_report_date": "active"
    },
    "audit_report_status": "tabled",
    "tabling": {
      "tabled_on": "2023-12-15",
      "lower_house": { "tabled": true, "tabled_on": "2023-12-15" }
    },
    "report_structure": "standalone",
    "pdf_assets": {
      "complete": {
        "en": {
          "local_path": "pdfs/en/complete/AR06-CAG-2023-STATE-MP-en.pdf",
          "page_count": 312
        }
      }
    }
  }
}
```

---

### Step 6 — Write `structure.json`

Defines the chapter/section tree. Minimal example for a single chapter:

```json
{
  "$schema": "../../../../../schemas/structure.schema",
  "product_id": "AR06-CAG-2023-STATE-MP",
  "content_units": [
    {
      "unit_id": "AR06-CAG-2023-STATE-MP-CH01",
      "unit_type": "chapter",
      "title": { "en": "Chapter 1: Financial Management" },
      "seq": 10,
      "metadata": {
        "audit_type": ["ATYPE-COMPLIANCE"],
        "report_sector": ["SECT-CIVIL"],
        "audit_period": { "from": "2022-04-01", "to": "2023-03-31" }
      },
      "content_units": [
        {
          "unit_id": "AR06-CAG-2023-STATE-MP-CH01-S01",
          "unit_type": "section",
          "title": { "en": "1.1 Budget Management" },
          "seq": 10,
          "metadata": {
            "audit_findings_categories": ["excess_payment", "avoidable_expenditure"],
            "topics": ["public_finance"]
          }
        }
      ]
    }
  ]
}
```

---

### Step 7 — Write content blocks

Each chapter gets one NDJSON file at `blocks/content_block_ch01.ndjson`. One JSON object per line:

```jsonl
{"block_id":"AR06-CAG-2023-STATE-MP-CH01-B001","unit_id":"AR06-CAG-2023-STATE-MP-CH01-S01","seq":10,"block_type":"paragraph","para_number":"1.1","content":{"para_type":"background","text":{"en":"The Finance Department is responsible for..."}}}
{"block_id":"AR06-CAG-2023-STATE-MP-CH01-B002","unit_id":"AR06-CAG-2023-STATE-MP-CH01-S01","seq":20,"block_type":"paragraph","para_number":"1.2","content":{"para_type":"audit_observation","text":{"en":"Audit observed that funds amounting to ₹12.34 crore were diverted..."}}}
```

---

### Step 8 — Validate locally

```bash
# Run all validators in order (same as CI)
python scripts/sync_product_type_enum.py --check
python scripts/check_registry_integrity.py
python scripts/validate_registry_refs.py --product-id AR06-CAG-2023-STATE-MP
python scripts/validate_report.py --product-id AR06-CAG-2023-STATE-MP
```

Fix any errors before committing.

---

### Step 9 — Commit and push

```bash
git add reports/audit_report/2023/state/in-mp/AR06-CAG-2023-STATE-MP/
git commit -m "feat(report): add AR06-CAG-2023-STATE-MP"
git push
```

`validate.yml` runs automatically. Check the Actions tab for results.

---

### Step 10 — Ingest into Atlas

Once CI passes, trigger ingestion from GitHub Actions:

**Actions → Ingest Reports → Run workflow**
- `product_ids`: `AR06-CAG-2023-STATE-MP`
- `force_reingest`: false
- `skip_embeddings`: false
- `dry_run`: true  ← run dry first

Review the dry-run summary. If counts look right, run again with `dry_run: false`.

---

## 13. Pending Items

### Before Second Report

| Item | Notes |
|------|-------|
| `taxonomy_audit_findings_accounts_report.json` | Needed only when adding an `accounts_report`. Structurally different from audit report findings — appropriation excess/savings, grants not surrendered, finance accounts misclassification |
| `registry_entities.json` expansion | Currently 12 sample entries. Add actual ministry/department entries as reports are added. Add only entities referenced in real reports |
| `registry_schemes.json` expansion | Currently 9 sample entries. Same approach — add on demand |
| GitHub Actions secrets | `OPENAI_API_KEY`, `MONGODB_URI`, `REDIS_URL` must be set in repo settings before `ingest.yml` can run |
| `.gitignore` | Add `reports/**/embeddings/` before first commit |
| `file_checksums` in manifest | Compute sha256 of each listed file and populate — `sha256sum` or Python `hashlib` |

### Medium Term

| Item | Notes |
|------|-------|
| `product.schema` conditional validation | `specific` field `if/then` — when `product_type=audit_report`, validate against `audit_report_metadata.schema` |
| `location_registry.json` | ULB and PRI IDs for `regions.ulbs[]` and `regions.pris[]` — needed for Local Government audit reports |
| Annotation review pipeline | Frontend workflow for `reviewed` / `reviewed_by` / `reviewed_at` on content block annotations |
| Pipeline testing against real data | All scripts written but not yet tested on a real report |

### Long Term

| Item | Notes |
|------|-------|
| Schema v4 split | Split `inheritable_audit_metadata` → `classification_metadata` + `accountability_metadata` |
| Frontend (Next.js) | Portal reader, ATN tracker, RAG chat — not started |
| Public API (FastAPI) | RAG endpoint, report search, ATN status — not started |

---

*Last updated: March 2026. Schema system complete through v3.6. All taxonomies and pipeline scripts built. Repository ready for first report ingestion.*
