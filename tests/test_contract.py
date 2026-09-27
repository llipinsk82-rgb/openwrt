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
                    text = text.replace('xmlns="http://www.w3.org/2000/svg"', "")
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


class ArcherThemeContractTests(unittest.TestCase):
    def setUp(self):
        self.theme = ROOT / "luci-theme-archer"

    def test_theme_registers_archer_without_removing_bootstrap(self):
        defaults = self.theme / "root/etc/uci-defaults/30_luci-theme-archer"
        self.assertTrue(defaults.is_file())
        text = defaults.read_text(encoding="utf-8")
        self.assertIn("themes.Archer", text)
        self.assertIn("/luci-static/archer", text)
        self.assertNotIn("delete luci.themes.Bootstrap", text)

    def test_theme_templates_use_dispatcher_urls_and_keep_stock_menu_dom(self):
        header = self.theme / "ucode/template/themes/archer/header.ut"
        footer = self.theme / "ucode/template/themes/archer/footer.ut"
        self.assertTrue(header.is_file())
        self.assertTrue(footer.is_file())
        text = header.read_text(encoding="utf-8") + footer.read_text(encoding="utf-8")
        self.assertIn("dispatcher.build_url", text)
        self.assertIn('id="topmenu"', text)
        self.assertIn('id="modemenu"', text)
        self.assertIn('id="archer-mode-toggle"', text)
        self.assertIn("menu-archer", text)

    def test_simple_mode_is_progressive_enhancement(self):
        menu = self.theme / "htdocs/luci-static/resources/menu-archer.js"
        css = self.theme / "htdocs/luci-static/archer/cascade.css"
        self.assertTrue(menu.is_file())
        self.assertTrue(css.is_file())
        js = menu.read_text(encoding="utf-8")
        styles = css.read_text(encoding="utf-8")
        self.assertIn("archer-ui-mode", js)
        self.assertIn("data-archer-ready", js)
        self.assertIn("setMode", js)
        self.assertIn("getMode", js)
        self.assertRegex(js, r"simple.*advanced|advanced.*simple")
        self.assertIn('[data-archer-ready="1"][data-archer-mode="simple"]', styles)
        self.assertNotIn(".archer-advanced-shell { display: none", styles)

    def test_theme_runtime_assets_stay_below_600kb(self):
        total = 0
        for path in self.theme.rglob("*"):
            if path.is_file() and path.suffix in RUNTIME_SUFFIXES:
                total += path.stat().st_size
        self.assertLess(total, 600_000, f"theme runtime assets are {total} bytes")
