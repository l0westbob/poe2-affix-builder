# Architecture

`poe-affix-builder` is structured as a small modular monolith with parity-preserving boundaries.

## Runtime Flow

1. The CLI parses a command and resolves local source data.
2. Adapters handle external concerns such as sparse checkout, JSON persistence, and poe2db fetching.
3. Services execute the business workflows:
   - build affix outputs
   - validate mapping coverage
   - rebuild the mapping from snapshot + source mods
4. Contracts serialize typed domain objects back to the stable JSON shapes committed in the repository.

## Module Boundaries

- `domain`
  - Typed models for source mods, manifests, snapshots, output files, and reports.
  - No filesystem, subprocess, or HTTP dependencies.
- `contracts`
  - Round-trip-safe conversion between typed models and committed JSON structures.
  - Preserves deterministic ordering and compatibility.
- `policies`
  - Item-category-to-domain rules.
  - Slug-to-spawn-tag rules.
- `adapters`
  - `json_store`: canonical JSON load/write helpers.
  - `poe2_source_repo`: sparse checkout and source resolution.
  - `poe2db_client`: HTTP fetch, retry behavior, and page parsing helpers.
- `services`
  - `build_service`
  - `rebuild_mapping_service`
  - shared `matching_service`

## Parity Rules

- `result/affixes/*.json` are canonical outputs.
- `config/item_mapping.json` rebuilt from the same snapshot must match the committed version unless logic is intentionally changed.
- `result/build_report.json`, `result/rebuild_mapping_report.json`, and `result/mapping_validation.json` are part of the regression baseline.
- Validation advisories are expected. They indicate possible mapping coverage expansion, not that the current affix files are invalid.

## Testing Strategy

- Characterization tests protect matching heuristics and normalization rules.
- Contract round-trip tests protect JSON schemas and ordering semantics.
- Golden parity tests compare generated artifacts and reports against committed baselines.
- CLI tests protect sparse checkout behavior and user-facing command wording.
