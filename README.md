# SpeechScope Model Catalog

Metadata-only companion catalog for SpeechScope ASR models.

The repository intentionally does **not** commit model weights. It pins upstream
Hugging Face revisions, artifact URLs, sizes, hashes, runtime metadata, and
acquisition ownership. SpeechScope is the consumer that downloads, verifies,
installs, resolves, and removes models that it owns.

## Model references

Model references are stable `backend:id` strings.

```text
whispercpp:tiny-q5_1
whispercpp:tiny.en-q5_1
whispercpp:base-q5_1
whispercpp:base.en-q5_1
whispercpp:small-q5_1
whispercpp:large-v3-turbo-q5_0
redux:parakeet-redux
```

Aliases such as `base.en` are catalog metadata; canonical refs should be used in
automation.

## Ownership modes

`managed`
: SpeechScope owns the installed copy. All managed artifacts must have a pinned
  revision, byte size, and SHA-256 digest. The CLI may install, verify, resolve,
  and remove them.

`runtime-managed`
: The runtime owns acquisition/cache semantics. The catalog provides provenance
  and compatibility metadata, but SpeechScope must not pretend that its own
  model store contains or controls those bytes.

The current `redux:parakeet-redux` entry is `runtime-managed`: SpeechScope's
Redux backend calls Moondream Photon with `moondream/parakeet-redux`. Until
Photon exposes a stable local-directory/cache ownership contract, this catalog
does not make `speechscope models install/remove/path` manage Photon files.

## Consumer examples

```bash
speechscope models list
speechscope models show whispercpp:base.en-q5_1
speechscope models install whispercpp:base.en-q5_1
speechscope models verify whispercpp:base.en-q5_1
speechscope models path whispercpp:base.en-q5_1

speechscope transcribe sample.wav \
  --backend whispercpp \
  --model whispercpp:base.en-q5_1
```

A Redux entry is discoverable:

```bash
speechscope models show redux:parakeet-redux
```

but `models install redux:parakeet-redux` is intentionally rejected as
runtime-managed.

## Repository contract

- `catalog/models.json`: normalized consumer catalog.
- `catalog/source.json`: upstream pins used by drift checks.
- `catalog/seed.json`: small maintainer input describing curated choices.
- `schemas/model-catalog.schema.json`: JSON Schema.
- `scripts/verify_catalog.py`: dependency-free semantic validator.
- `scripts/check_upstream_drift.py`: checks pinned repository revisions against
  current Hugging Face heads.
- `scripts/rebuild_catalog.py`: refreshes exact sizes/SHA-256 values for curated
  Hugging Face artifacts without downloading LFS blobs.
- CI rejects accidentally committed model binaries.

Catalog updates are data releases. Consumers must not assume that a ref changes
immutably: the pinned revision and digest are the authority for a specific
catalog snapshot.
