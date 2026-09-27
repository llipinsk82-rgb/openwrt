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


class DashboardContractTests(unittest.TestCase):
    def setUp(self):
        self.app = ROOT / "luci-app-archer-dashboard"

    def test_dashboard_normalizer_and_view_exist(self):
        normalize = self.app / "htdocs/luci-static/resources/archer-dashboard/normalize.js"
        data = self.app / "htdocs/luci-static/resources/archer-dashboard/data.js"
        view = self.app / "htdocs/luci-static/resources/view/archer-dashboard/dashboard.js"
        css = self.app / "htdocs/luci-static/resources/archer-dashboard/dashboard.css"
        for path in (normalize, data, view, css):
            self.assertTrue(path.is_file(), f"missing dashboard file: {path.relative_to(ROOT)}")
        ntext = normalize.read_text(encoding="utf-8")
        self.assertIn("normalizeSnapshot", ntext)
        self.assertIn("Not available", ntext)
        self.assertIn("not-mounted", ntext)
        self.assertNotIn("private_key", ntext.lower())
        self.assertNotIn("privatekey", ntext.lower())

    def test_dashboard_loads_six_sections_and_refreshes_conservatively(self):
        data = self.app / "htdocs/luci-static/resources/archer-dashboard/data.js"
        view = self.app / "htdocs/luci-static/resources/view/archer-dashboard/dashboard.js"
        self.assertTrue(data.is_file())
        self.assertTrue(view.is_file())
        dtext = data.read_text(encoding="utf-8")
        vtext = view.read_text(encoding="utf-8")
        self.assertIn("loadSnapshot", dtext)
        for section in ("internet", "wifi", "vpn", "devices", "storage", "system"):
            self.assertIn(section, vtext)
        self.assertRegex(vtext, r"10000|10\s*\*\s*1000")

    def test_dashboard_fixtures_cover_required_degraded_states(self):
        fixture_dir = ROOT / "tests/fixtures/dashboard"
        names = {p.name for p in fixture_dir.glob("*.json")}
        self.assertTrue({"normal.json", "missing_optional.json", "wifi_edge.json"}.issubset(names))
        missing = json.loads((fixture_dir / "missing_optional.json").read_text(encoding="utf-8"))
        self.assertIsNone(missing["wan6"])
        self.assertEqual([], missing["wireguard"])
        self.assertEqual([], missing["mounts"])
        edge = json.loads((fixture_dir / "wifi_edge.json").read_text(encoding="utf-8"))
        self.assertTrue(any(r.get("disabled") for r in edge["wifi"]))
        macs = [c["mac"] for r in edge["wifi"] for c in r.get("clients", [])]
        self.assertLess(len(set(macs)), len(macs))


class LuCIIntegrationContractTests(unittest.TestCase):
    def setUp(self):
        self.app = ROOT / "luci-app-archer-dashboard"
        self.menu = self.app / "root/usr/share/luci/menu.d/luci-app-archer-dashboard.json"
        self.acl = self.app / "root/usr/share/rpcd/acl.d/luci-app-archer-dashboard.json"

    def test_dashboard_menu_points_to_view(self):
        menu = json.loads(self.menu.read_text(encoding="utf-8"))
        node = menu["admin/archer/dashboard"]
        self.assertEqual("Dashboard", node["title"])
        self.assertEqual("view", node["action"]["type"])
        self.assertEqual("archer-dashboard/dashboard", node["action"]["path"])
        self.assertIn("luci-app-archer-dashboard", node["depends"]["acl"])

    def test_dashboard_acl_is_read_only_and_least_privilege(self):
        acl = json.loads(self.acl.read_text(encoding="utf-8"))["luci-app-archer-dashboard"]
        self.assertNotIn("write", acl)
        read = acl["read"]
        self.assertEqual(["board", "info"], sorted(read["ubus"]["system"]))
        self.assertEqual(["getMountPoints"], read["ubus"]["luci"])
        self.assertEqual(["getDHCPLeases"], read["ubus"]["luci-rpc"])
        self.assertEqual(["assoclist"], read["ubus"]["iwinfo"])
        self.assertNotIn("file", read["ubus"])

    def test_dashboard_view_loads_local_stylesheet(self):
        view = self.app / "htdocs/luci-static/resources/view/archer-dashboard/dashboard.js"
        text = view.read_text(encoding="utf-8")
        self.assertIn("L.resource('archer-dashboard/dashboard.css')", text)
        self.assertIn("rel: 'stylesheet'", text)


class BuildContractTests(unittest.TestCase):
    def setUp(self):
        self.script = ROOT / "scripts/build-openwrt-25.12.5.sh"

    def test_build_script_pins_verified_openwrt_sdk(self):
        self.assertTrue(self.script.is_file())
        text = self.script.read_text(encoding="utf-8")
        self.assertIn("25.12.5", text)
        self.assertIn("ath79-generic", text)
        self.assertIn("openwrt-sdk-25.12.5-ath79-generic_gcc-14.3.0_musl.Linux-x86_64.tar.zst", text)
        self.assertIn("bc4307ae2065c0c0b7c84627356e9f3d368a5a803c81552fcb77aa034a843f5a", text)
        self.assertIn("sha256sum", text)

    def test_build_script_targets_apk_only(self):
        text = self.script.read_text(encoding="utf-8")
        self.assertNotIn("opkg", text)
        self.assertNotIn(".ipk", text)
        self.assertIn("*.apk", text)
        self.assertIn("luci-theme-archer", text)
        self.assertIn("luci-app-archer-dashboard", text)
        self.assertNotIn("./scripts/feeds", text)


class ExternalSDKLuCIMakefileContractTests(unittest.TestCase):
    def test_custom_packages_use_standalone_package_mk(self):
        for package in ("luci-theme-archer", "luci-app-archer-dashboard"):
            makefile = ROOT / package / "Makefile"
            text = makefile.read_text(encoding="utf-8")
            self.assertIn("include $(INCLUDE_DIR)/package.mk", text)
            self.assertNotIn("luci.mk", text)
            self.assertIn("PKGARCH:=all", text)
            self.assertIn("EXTRA_DEPENDS:=luci-base (>=26.180.75667~128a781)", text)
            self.assertNotIn("DEPENDS:=+luci-base", text)
            self.assertIn("define Package/", text)
            self.assertIn("/install", text)
