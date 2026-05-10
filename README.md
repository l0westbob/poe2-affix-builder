# poe-affix-builder

Toolchain to build `result/affixes` from:
- poe2db snapshot data (`config/poe2db_snapshot.json`), and
- PoE2 source data (`data/poe2/data/mods.json`, auto-fetched on demand).

The generated affix JSON files are the canonical output. Validation warnings are expected coverage advisories, not evidence that the generated affix files are wrong.

## Requirements

- Python 3.14+
- `uv`

## Setup

```bash
uv sync
```

## Commands

Refresh poe2db snapshot (explicit/manual, not part of `build`):

```bash
uv run poe-affix-build refresh-poe2db \
  --snapshot config/poe2db_snapshot.json \
  --report result/poe2db_refresh_report.json
```

`refresh-poe2db` prints live progress (`[n/total]`) and retries transient upstream failures (including Cloudflare 52x responses) with exponential backoff.

Rebuild mapping from snapshot + mods source:

```bash
uv run poe-affix-build rebuild-mapping \
  --source-dir data/poe2/data \
  --snapshot config/poe2db_snapshot.json \
  --out config/item_mapping.json \
  --report result/rebuild_mapping_report.json
```

Build affix output from source data:

```bash
uv run poe-affix-build build \
  --source-dir data/poe2/data \
  --manifest config/item_mapping.json \
  --out-dir result/affixes \
  --report result/build_report.json
```

Validate mapping coverage against source data:

```bash
uv run poe-affix-build validate-mapping \
  --source-dir data/poe2/data \
  --manifest config/item_mapping.json \
  --out result/mapping_validation.json
```

## Notes

- `refresh-poe2db` fails atomically: snapshot/report are written only after full successful fetch/parse.
- For `build`, `validate-mapping`, and `rebuild-mapping`, if `mods.json` is missing under `--source-dir` and the source dir follows the default `.../poe2/data` layout, the CLI performs a shallow sparse checkout of `https://github.com/repoe-fork/poe2.git` (`master`) into `data/poe2`, materializing only `data/mods.json`.
- `validate-mapping` reports coverage advisories. These are useful for mapping maintenance, but the current affix output files can still be correct even when advisories exist.

## Architecture

- `src/poe_affix_builder/domain`: typed core models and result objects
- `src/poe_affix_builder/contracts`: serializers and round-trip-safe JSON contracts
- `src/poe_affix_builder/adapters`: filesystem, sparse checkout, and poe2db integration boundaries
- `src/poe_affix_builder/services`: build, validation, rebuild, and shared matching logic
- `src/poe_affix_builder/policies`: domain/spawn-tag rules

More detail is in [docs/architecture.md](/Users/benochocki/Herd/poe-affix-builder/docs/architecture.md).

## Contributor Policy

- Preserve parity for `result/affixes`, `config/item_mapping.json`, and the committed reports unless a change explicitly intends to alter logic.
- When changing matching behavior, update or justify any artifact diffs in tests and review notes.
- Run `uv run python -m unittest discover -s tests` before merging logic changes.
