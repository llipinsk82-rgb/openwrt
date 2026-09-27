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
            if not package_dir.exists(): continue
            for path in package_dir.rglob("*"):
                if path.is_file() and path.suffix in RUNTIME_SUFFIXES:
                    text = path.read_text(encoding="utf-8", errors="ignore").replace('xmlns="http://www.w3.org/2000/svg"', "")
                    if REMOTE_RE.search(text): offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual([], offenders)

    def test_menu_and_acl_json_is_valid(self):
        for package_dir in PACKAGE_DIRS:
            if not package_dir.exists(): continue
            for path in package_dir.rglob("*.json"):
                with self.subTest(path=str(path.relative_to(ROOT))): json.loads(path.read_text(encoding="utf-8"))

    def test_combined_runtime_assets_stay_below_one_megabyte(self):
        total = sum(path.stat().st_size for package_dir in PACKAGE_DIRS if package_dir.exists() for path in package_dir.rglob("*") if path.is_file() and path.suffix in RUNTIME_SUFFIXES)
        self.assertLess(total, 1_000_000, f"runtime assets are {total} bytes")

class ArcherThemeContractTests(unittest.TestCase):
    def setUp(self): self.theme = ROOT / "luci-theme-archer"
    def test_theme_registers_archer_without_removing_bootstrap(self):
        defaults=self.theme/"root/etc/uci-defaults/30_luci-theme-archer"; self.assertTrue(defaults.is_file()); text=defaults.read_text(); self.assertIn("themes.Archer",text); self.assertIn("/luci-static/archer",text); self.assertNotIn("delete luci.themes.Bootstrap",text)
    def test_theme_templates_use_dispatcher_urls_and_keep_stock_menu_dom(self):
        text=(self.theme/"ucode/template/themes/archer/header.ut").read_text()+(self.theme/"ucode/template/themes/archer/footer.ut").read_text(); self.assertIn("dispatcher.build_url",text); self.assertIn('id="topmenu"',text); self.assertIn('id="modemenu"',text); self.assertIn('id="archer-mode-toggle"',text); self.assertIn("menu-archer",text)
    def test_simple_mode_is_progressive_enhancement(self):
        js=(self.theme/"htdocs/luci-static/resources/menu-archer.js").read_text(); styles=(self.theme/"htdocs/luci-static/archer/cascade.css").read_text(); self.assertIn("archer-ui-mode",js); self.assertIn("data-archer-ready",js); self.assertIn("setMode",js); self.assertIn("getMode",js); self.assertRegex(js,r"simple.*advanced|advanced.*simple"); self.assertIn('[data-archer-ready="1"][data-archer-mode="simple"]',styles)
    def test_theme_runtime_assets_stay_below_600kb(self):
        total=sum(p.stat().st_size for p in self.theme.rglob("*") if p.is_file() and p.suffix in RUNTIME_SUFFIXES); self.assertLess(total,600_000)

class DashboardContractTests(unittest.TestCase):
    def setUp(self): self.app=ROOT/"luci-app-archer-dashboard"
    def test_dashboard_normalizer_and_view_exist(self):
        paths=[self.app/"htdocs/luci-static/resources/archer-dashboard/normalize.js",self.app/"htdocs/luci-static/resources/archer-dashboard/data.js",self.app/"htdocs/luci-static/resources/view/archer-dashboard/dashboard.js",self.app/"htdocs/luci-static/resources/archer-dashboard/dashboard.css"]
        for path in paths: self.assertTrue(path.is_file())
        ntext=paths[0].read_text(); self.assertIn("normalizeSnapshot",ntext); self.assertIn("Not available",ntext); self.assertIn("not-mounted",ntext); self.assertNotIn("private_key",ntext.lower())
    def test_dashboard_loads_six_sections_and_refreshes_conservatively(self):
        dtext=(self.app/"htdocs/luci-static/resources/archer-dashboard/data.js").read_text(); vtext=(self.app/"htdocs/luci-static/resources/view/archer-dashboard/dashboard.js").read_text(); self.assertIn("loadSnapshot",dtext)
        for section in ("internet","wifi","vpn","devices","storage","system"): self.assertIn(section,vtext)
        self.assertRegex(vtext,r"10000|10\s*\*\s*1000")
    def test_dashboard_fixtures_cover_required_degraded_states(self):
        fixture_dir=ROOT/"tests/fixtures/dashboard"; names={p.name for p in fixture_dir.glob("*.json")}; self.assertTrue({"normal.json","missing_optional.json","wifi_edge.json"}.issubset(names)); missing=json.loads((fixture_dir/"missing_optional.json").read_text()); self.assertIsNone(missing["wan6"]); self.assertEqual([],missing["wireguard"]); self.assertEqual([],missing["mounts"]); edge=json.loads((fixture_dir/"wifi_edge.json").read_text()); self.assertTrue(any(r.get("disabled") for r in edge["wifi"])); macs=[c["mac"] for r in edge["wifi"] for c in r.get("clients",[])]; self.assertLess(len(set(macs)),len(macs))
