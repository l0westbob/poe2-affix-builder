# poe-affix-builder

Toolchain to build `result/affixes` from:
- poe2db snapshot data (`config/poe2db_snapshot.json`), and
- PoE2 source data (`data/poe2/data/mods.json`, auto-fetched on demand).

The generated affix JSON files are the canonical output. Validation warnings are expected coverage advisories, not evidence that the generated affix files are wrong.

## Licensing

- The repository's source code and original project-authored content are licensed under `CC0 1.0`; see [LICENSE](./LICENSE) and [LICENSE-CC0.txt](./LICENSE-CC0.txt).
- This project fetches and may bundle or derive data from PoE2DB (`https://poe2db.tw`), including the modifiers index used by `refresh-poe2db`.
- PoE2DB states: `Wikis Content is available under CC BY-NC-SA 3.0 unless otherwise noted.`
- As a result, bundled or generated PoE2DB-derived data in this repository should be treated as `CC BY-NC-SA 3.0` unless otherwise noted, not as `CC0`.
- That includes the fetched snapshot and the generated affix/mapping/report artifacts, including `config/poe2db_snapshot.json`, `config/item_mapping.json`, `result/affixes/*.json`, `result/build_report.json`, `result/rebuild_mapping_report.json`, and `result/mapping_validation.json`.
- If you redistribute PoE2DB-derived artifacts from this repo, preserve attribution to PoE2DB and comply with the applicable non-commercial and share-alike terms.
- Attribution and scope details are documented in [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md).

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

## Unresolved Groups

The rebuild and build reports can still contain unresolved modifier matches. That is expected with the current data sources and does not automatically mean the generated output is wrong.

### What "unresolved" means

An unresolved entry means:

- poe2db exposed a modifier row in one of the saved `modifier_sections`
- the builder preserved that row in the snapshot / mapping / final output
- but the matcher could not find a confident corresponding entry in `data/poe2/data/mods.json` to attach canonical local stat ids

So "unresolved" here is primarily a source-alignment problem, not a data-loss problem.

### What was already fixed

Composite family keys such as `Strength|Intelligence`, `Strength|Dexterity`, and `Dexterity|Intelligence` used to be unresolved because `mods.json` families were being truncated to only the first group entry.

That has been fixed:

- poe2db family keys are matched against the full joined `groups` list from `mods.json`
- those composite stat-pair families now resolve correctly

### What is still unresolved

Most remaining unresolved groups come from non-`normal` modifier sections, especially:

- `socketable`
- `bonded`
- some other special-purpose poe2db-only sections

Typical unresolved family keys currently include:

- `AdeptRune`
- `ResolveRune`
- `RobustRune`
- `BodyRune`
- `DesertRune`
- `GlacialRune`
- `InspirationRune`
- `IronRune`
- `MindRune`
- `RebirthRune`
- `StoneRune`
- `StormRune`
- `VisionRune`
- `TemperedRune`
- `RuneofAlacrity`
- `RuneofLeadership`
- `RuneofNobility`
- `RuneofTithing`
- `SoulCoreofAtmohua`
- `SoulCoreofCholotl`

These are largely rune / soul-core / socket-style modifiers that poe2db surfaces on item pages, but they do not line up cleanly with `mods.json` in the same way ordinary prefix and suffix affixes do.

### Why these remain unresolved

In practice, these unresolved groups usually differ from regular affixes in one or more of these ways:

- the poe2db section is not `normal`
- the poe2db generation kind is often `gen0` instead of a regular `prefix` / `suffix`
- the poe2db family key has no straightforward one-to-one equivalent in `mods.json`
- the poe2db row may represent socketed rune or soul-core behavior that is modeled differently upstream
- multiple poe2db rows can collapse onto the same visible text pattern while still not mapping cleanly to one canonical local mod entry

Because of that, the matcher often has enough information to preserve the displayed modifier text, but not enough to safely assign canonical local stat ids from `mods.json`.

### Why this does not invalidate the normal affix output

The important distinction is:

- `modifier_sections.normal` is the regular affix surface most downstream consumers care about
- the remaining unresolved groups are concentrated in extra sections such as rune/socket/soul-core style data

That means:

- the main affix dataset can still be correct
- the unresolved report should be read as a compatibility / coverage report for extended modifier sections
- the report is useful for future improvement work, but it is not proof that the normal affix files are broken

### Current interpretation

At the moment, the safest interpretation is:

- unresolved `normal` modifiers deserve close attention
- unresolved non-`normal` rune/soul-core/socket-style modifiers are expected until a dedicated matching strategy is implemented for those section types

## Architecture

- `src/poe_affix_builder/domain`: typed core models and result objects
- `src/poe_affix_builder/contracts`: serializers and round-trip-safe JSON contracts
- `src/poe_affix_builder/adapters`: filesystem, sparse checkout, and poe2db integration boundaries
- `src/poe_affix_builder/services`: build, validation, rebuild, and shared matching logic
- `src/poe_affix_builder/policies`: domain/spawn-tag rules

More detail is in [docs/architecture.md](./docs/architecture.md).

## Contributor Policy

- Preserve parity for `result/affixes`, `config/item_mapping.json`, and the committed reports unless a change explicitly intends to alter logic.
- When changing matching behavior, update or justify any artifact diffs in tests and review notes.
- Run `uv run python -m unittest discover -s tests` before merging logic changes.
