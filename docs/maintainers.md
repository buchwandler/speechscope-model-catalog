# Maintainers

Run before committing catalog changes:

```bash
python scripts/rebuild_catalog.py
python scripts/verify_catalog.py
python -m unittest discover -s tests -v
```

Review upstream licenses and runtime compatibility manually. Pin full 40-hex
revisions. Managed artifacts require exact byte size and SHA-256. Do not commit
model weights, generated downloads, audio fixtures, or credentials.

`check_upstream_drift.py` returning 2 means an upstream repository head changed;
it is a review signal, not permission to repin automatically.
