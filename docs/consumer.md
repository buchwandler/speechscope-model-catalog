# Consumer contract

SpeechScope consumes `catalog/models.json`.

A managed model install must:

1. resolve a canonical ref;
2. create a staging directory under the SpeechScope cache root;
3. download only HTTPS artifacts whose URL pins the catalog revision;
4. verify byte count and SHA-256 before activation;
5. write an install manifest;
6. atomically replace the final install directory.

Transcription never implicitly downloads a model. A `backend:id` model selector
must resolve to an already installed model. Explicit file paths remain an
independent escape hatch for whisper.cpp.

`runtime-managed` entries are informational/runtime locators. The consumer must
not expose them as if they were SpeechScope-owned installations.
