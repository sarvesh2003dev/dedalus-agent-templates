"""Verify that every original ZIP file is still present, byte for byte."""
import hashlib
import json
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PreservationTests(unittest.TestCase):
    def test_original_archive_and_all_items_are_preserved(self):
        manifest = json.loads((ROOT / "preservation-manifest.json").read_text(encoding="utf-8"))
        archive_path = ROOT / manifest["archive_path"]
        self.assertEqual(hashlib.sha256(archive_path.read_bytes()).hexdigest(),
                         manifest["archive_sha256"])
        source_root = ROOT / manifest["extracted_path"]
        files = {p.relative_to(source_root).as_posix(): p for p in source_root.rglob("*") if p.is_file()}
        self.assertEqual(set(files), set(manifest["files"]))
        with zipfile.ZipFile(archive_path) as archive:
            zipped_files = {info.filename for info in archive.infolist() if not info.is_dir()}
            self.assertEqual(zipped_files, set(files))
            for relative_path, expected_digest in manifest["files"].items():
                with self.subTest(path=relative_path):
                    content = files[relative_path].read_bytes()
                    self.assertEqual(hashlib.sha256(content).hexdigest(), expected_digest)
                    self.assertEqual(content, archive.read(relative_path))


if __name__ == "__main__":
    unittest.main()
