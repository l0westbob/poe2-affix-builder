# Third-Party Notices

## PoE2DB wiki content

This project fetches and may bundle or derive data from PoE2DB:

- Site: [https://poe2db.tw](https://poe2db.tw)
- Example source index used by the fetcher: [https://poe2db.tw/us/Modifiers](https://poe2db.tw/us/Modifiers)

PoE2DB states on its site:

> Wikis Content is available under CC BY-NC-SA 3.0 unless otherwise noted.

Implications for this repository:

- The repository's own source code is licensed separately under `CC0 1.0`, as described in `LICENSE`.
- Bundled or generated data that contains or is derived from PoE2DB wiki content is not treated as `CC0`.
- Such PoE2DB-derived content should be treated as covered by `CC BY-NC-SA 3.0` unless otherwise noted by PoE2DB.

This includes, at minimum, content fetched from PoE2DB and files materially derived from that fetched content, such as:

- `config/poe2db_snapshot.json`
- `config/item_mapping.json`
- `result/rebuild_mapping_report.json`
- any generated outputs or reports that incorporate PoE2DB-derived data

Users redistributing PoE2DB-derived materials from this repository should preserve attribution to PoE2DB and comply with the applicable `CC BY-NC-SA 3.0` terms, including non-commercial and share-alike requirements.
