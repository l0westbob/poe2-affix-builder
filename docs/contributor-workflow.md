# Contributor Workflow

This repo is easiest to maintain when generated artifacts are refreshed in a predictable order.

## Canonical Pipeline

1. Refresh poe2db snapshot:

```bash
uv run poe-affix-build refresh-poe2db \
  --snapshot config/poe2db_snapshot.json \
  --report result/poe2db_refresh_report.json
```

2. Rebuild mapping:

```bash
uv run poe-affix-build rebuild-mapping \
  --source-dir data/poe2/data \
  --snapshot config/poe2db_snapshot.json \
  --out config/item_mapping.json \
  --report result/rebuild_mapping_report.json
```

3. Build final item files:

```bash
uv run poe-affix-build build \
  --source-dir data/poe2/data \
  --manifest config/item_mapping.json \
  --out-dir result/affixes \
  --report result/build_report.json
```

4. Validate mapping:

```bash
uv run poe-affix-build validate-mapping \
  --source-dir data/poe2/data \
  --manifest config/item_mapping.json \
  --out result/mapping_validation.json
```

## Expected Baseline

The current committed baseline has:

- `78` output item files
- `7058` affixes
- `18182` tiers
- `5457` unresolved rebuild/build matches, mostly expected non-`normal` groups
- `62` item-level validation advisory entries

Run the full suite before committing:

```bash
uv run python -m unittest discover -s tests
```

Generated artifact changes should be reviewed as data changes. If a logic change intentionally alters counts or JSON output, update the relevant golden tests and explain the reason in review notes.

## Optional Diagnostics

When investigating unresolved groups, write separate diagnostic reports instead of changing the canonical reports:

```bash
uv run poe-affix-build rebuild-mapping --diagnostics result/rebuild_mapping_diagnostics.json
uv run poe-affix-build build --diagnostics result/build_diagnostics.json
```

These files are maintainer aids. They split unresolved matches into regular affix concerns, expected non-`normal` groups, and unknown section groups.
