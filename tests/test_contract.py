import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIRS = [ROOT / "luci-theme-archer", ROOT / "luci-app-archer-dashboard"]
RUNTIME_SUFFIXES = {".css", ".js", ".ut", ".svg"}
REMOTE_RE = re.compile(r"https?://", re.IGNORECASE)


class RepositoryContractTests(unittest.TestCase):
    def test_required_package_directories_exist(self):
        for path in PACKAGE_DIRS:
            with self.subTest(path=path.name):
                self.assertTrue(path.is_dir(), f"missing package directory: {path.name}")

    def test_runtime_assets_have_no_remote_dependencies(self):
        offenders = []
        for package_dir in PACKAGE_DIRS:
            if not package_dir.exists():
                continue
            for path in package_dir.rglob("*"):
                if path.is_file() and path.suffix in RUNTIME_SUFFIXES:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                    if REMOTE_RE.search(text):
                        offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual([], offenders)

    def test_menu_and_acl_json_is_valid(self):
        for package_dir in PACKAGE_DIRS:
            if not package_dir.exists():
                continue
            for path in package_dir.rglob("*.json"):
                with self.subTest(path=str(path.relative_to(ROOT))):
                    json.loads(path.read_text(encoding="utf-8"))

    def test_combined_runtime_assets_stay_below_one_megabyte(self):
        total = 0
        for package_dir in PACKAGE_DIRS:
            if not package_dir.exists():
                continue
            for path in package_dir.rglob("*"):
                if path.is_file() and path.suffix in RUNTIME_SUFFIXES:
                    total += path.stat().st_size
        self.assertLess(total, 1_000_000, f"runtime assets are {total} bytes")


if __name__ == "__main__":
    unittest.main()
