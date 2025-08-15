# Release Checklist

1. Tests green & working tree clean
   - `python -m unittest discover tests -v`
   - `black --check . && flake8 . && mypy .`
2. Docs updated (README + relevant docs/*)
3. Changelog: move Unreleased -> new version with date
4. Bump version in `stats_visualization/__init__.py`
5. Commit: `chore(release): vX.Y.Z`
6. Tag: `git tag -a vX.Y.Z -m "League-Stats X.Y.Z"`
7. Push: `git push && git push origin vX.Y.Z`
8. (Optional) GitHub Release (paste changelog section)
9. Add new Unreleased placeholder to changelog (if not present)
10. Communicate release (issue/PR/release notes)

Pre-releases: use `vX.Y.Z-rc.1`; keep README version at last stable until final.
