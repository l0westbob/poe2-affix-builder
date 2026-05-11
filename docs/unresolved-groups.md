# Unresolved Groups

The rebuild and build reports can contain unresolved modifier matches. That is expected with the current data sources and does not automatically mean the generated output is wrong.

## What "unresolved" Means

An unresolved entry means poe2db exposed a modifier row in one of the saved `modifier_sections`, the builder preserved that row in the snapshot, mapping, and final output, but the matcher could not find a confident corresponding entry in `data/poe2/data/mods.json` to attach canonical local stat ids.

In other words, unresolved entries are primarily source-alignment diagnostics, not data-loss diagnostics.

## Already Fixed

Composite family keys such as `Strength|Intelligence`, `Strength|Dexterity`, and `Dexterity|Intelligence` used to be unresolved because `mods.json` families were being truncated to only the first group entry.

That has been fixed. poe2db family keys now match against the full joined `groups` list from `mods.json`, and those composite stat-pair families resolve correctly.

## Still Expected

Most remaining unresolved groups come from non-`normal` modifier sections, especially `socketable`, `bonded`, and other special-purpose poe2db-only sections.

Typical remaining family keys include `AdeptRune`, `ResolveRune`, `RobustRune`, `BodyRune`, `DesertRune`, `GlacialRune`, `InspirationRune`, `IronRune`, `MindRune`, `RebirthRune`, `StoneRune`, `StormRune`, `VisionRune`, `TemperedRune`, `RuneofAlacrity`, `RuneofLeadership`, `RuneofNobility`, `RuneofTithing`, `SoulCoreofAtmohua`, and `SoulCoreofCholotl`.

These are largely rune, soul-core, and socket-style modifiers that poe2db surfaces on item pages, but they do not line up cleanly with `mods.json` in the same way ordinary prefix and suffix affixes do.

## Why They Remain Unresolved

These groups usually differ from regular affixes in one or more ways:

- the poe2db section is not `normal`
- the poe2db generation kind is often `gen0` instead of a regular `prefix` or `suffix`
- the poe2db family key has no straightforward one-to-one equivalent in `mods.json`
- the poe2db row may represent socketed rune or soul-core behavior that is modeled differently upstream
- multiple poe2db rows can collapse onto the same visible text pattern while still not mapping cleanly to one canonical local mod entry

Because of that, the matcher often has enough information to preserve the displayed modifier text, but not enough to safely assign canonical local stat ids from `mods.json`.

## Current Interpretation

`modifier_sections.normal` is the regular affix surface most downstream consumers care about. Unresolved `normal` modifiers deserve close attention.

Unresolved non-`normal` rune, soul-core, and socket-style modifiers are expected until a dedicated matching strategy is implemented for those section types.
