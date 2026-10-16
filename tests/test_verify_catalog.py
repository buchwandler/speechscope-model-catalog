from __future__ import annotations
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_catalog", ROOT / "scripts" / "verify_catalog.py")
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(module)

class VerifyCatalogTests(unittest.TestCase):
    def test_repository_catalog_is_valid(self):
        data = module.verify()
        self.assertGreaterEqual(len(data["models"]), 2)

    def test_managed_digest_is_required(self):
        data = json.loads((ROOT / "catalog" / "models.json").read_text())
        ref = next(r for r, m in data["models"].items() if m["acquisition"]["mode"] == "managed")
        data["models"][ref]["artifacts"][0]["sha256"] = None
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "models.json"
            p.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
            with self.assertRaisesRegex(ValueError, "requires SHA-256"):
                module.verify(p)

if __name__ == "__main__":
    unittest.main()
