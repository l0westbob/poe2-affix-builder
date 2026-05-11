# Release Checklist

- Run `uv sync`.
- Run `uv run python -m unittest discover -s tests`.
- Check `uv run poe-affix-build --version`.
- If data sources changed, run the full refresh -> rebuild -> build -> validate workflow from `docs/contributor-workflow.md`.
- Review generated diffs under `config/` and `result/`.
- Confirm `THIRD_PARTY_NOTICES.md` still describes PoE2DB-derived artifacts accurately.
- Confirm the README licensing section still distinguishes project-authored code from PoE2DB-derived data.
- Tag only after committed artifacts and reports match the intended release state.
