# Data Contracts

The committed JSON files are part of the public surface of this repository. Keep these shapes stable unless a change explicitly introduces a versioned migration.

## Snapshot

`config/poe2db_snapshot.json` is produced by `refresh-poe2db`.

Top-level shape:

```json
{
  "version": 1,
  "source": "https://poe2db.tw/us/Modifiers",
  "fetched_at": "2026-05-11T00:00:00+00:00",
  "items": []
}
```

Each item contains `slug`, `category`, `label`, `href`, optional `bases`, and `modifier_sections`. New snapshots use `modifier_sections`; legacy snapshot input with top-level `affixes` is still accepted and normalized to `modifier_sections.normal`.

## Manifest

`config/item_mapping.json` is produced by `rebuild-mapping`.

Each item contains `slug`, `category`, `label`, `include_domains`, `include_spawn_tags`, optional `bases`, `modifier_sections`, and the compatibility `affixes` field. The compatibility `affixes` field mirrors `modifier_sections.normal` for build and validation internals.

## Output

`result/affixes/*.json` is produced by `build`.

Each output item contains:

```json
{
  "category": "Weapons",
  "label": "Claws",
  "bases": [
    {
      "name": "Crude Claw",
      "href": "https://poe2db.tw/Crude_Claw",
      "required_level": null
    }
  ],
  "modifier_sections": {
    "normal": []
  },
  "slug": "Claws"
}
```

`modifier_sections.normal` is the regular affix surface. Other observed sections are `corrupted`, `desecrated`, `essence`, `perfect_essence`, `socketable`, and `bonded`.

## Diagnostics

`build --diagnostics` and `rebuild-mapping --diagnostics` write optional contributor-only reports. These reports categorize unresolved matches without changing canonical build or rebuild reports.

Current categories are:

- `normal_unresolved`
- `expected_non_normal_unresolved`
- `unknown_unresolved`

Diagnostic entries include the item slug, modifier section, family key, kind, level, and a reason code.

## Reports

`result/build_report.json`, `result/rebuild_mapping_report.json`, and `result/mapping_validation.json` are regression artifacts. They intentionally preserve their current default shapes.

Diagnostic-only improvements should be additive or written to separate diagnostic outputs so the canonical artifacts remain easy to compare.

## Schema Examples

Example JSON shapes live under [docs/schema-examples](./schema-examples/). They are documentation fixtures, not enforced JSON Schema files.
