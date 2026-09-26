# Archer C7 LuCI Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and deploy a lightweight premium LuCI theme and read-only dashboard for TP-Link Archer C7 v5 on OpenWrt 25.12.5, matching the approved mockup while keeping stock LuCI available as the Advanced/fallback interface.

**Architecture:** Two small LuCI packages: `luci-theme-archer` owns the shell, responsive styling, branding, Simple/Advanced toggle and icons; `luci-app-archer-dashboard` owns the dashboard view, menu entry and read-only RPC permissions. Standard LuCI pages remain authoritative for configuration. The implementation uses current LuCI ucode templates and JS views; no LuCI core files, daemon, database, external CDN, USB repartitioning or extroot changes.

**Tech Stack:** OpenWrt 25.12.5, LuCI ucode templates, LuCI JavaScript view framework, ubus/RPC, CSS, SVG, Python stdlib contract tests, OpenWrt 25.12.5 ath79/generic SDK, `apk` v3.

**Spec:** `docs/superpowers/specs/2026-09-27-archer-c7-luci-dashboard-design.md`

## Global Constraints

- Target device: `TP-Link Archer C7 v5`, board `tplink,archer-c7-v5`, OpenWrt `25.12.5 r33051-f5dae5ece4`, target `ath79/generic`.
- Current persistent free overlay is about `4.7 MB`; combined custom theme + dashboard target is `<1 MB`, preferred `400–700 KB`.
- Branding: `OpenWrt • Archer C7`; secondary text `OpenWrt 25.12.5 • TP-Link Archer C7 v5`.
- Preserve `luci-theme-bootstrap` as rollback; custom code must not patch LuCI core files.
- No TorGuard/PrivateRouter/BlackServ branding; no Docker, mesh manager, firmware flasher, package-manager UI, partition editor or extroot work.
- `/mnt/usb` is an active backup disk. Do not repartition, resize, format, remount destructively or move package payloads there in v1.
- No bundled frontend framework, external CDN or remote font dependency. Use system fonts and local SVG assets.
- Use OpenWrt 25.12 package workflow and `.apk`, not legacy `.ipk`/`opkg` instructions.
- Use current LuCI 25.12 conventions: ucode theme templates under `ucode/template/themes/...`, menu definitions under `root/usr/share/luci/menu.d/`, ACL definitions under `root/usr/share/rpcd/acl.d/`.
- Simple mode is progressive enhancement: if custom JS fails, the full standard LuCI navigation must remain accessible.
- Volatile dashboard refresh interval: 10 seconds by default; no faster than 5 seconds.

## Review Focus

1. Missing WAN6 or IPv6 address must render `Not available`, not throw or leave a permanent spinner; covered in Task 3 dashboard-data tests.
2. No WireGuard interface or missing `wg` tooling must render `Inactive / Not installed`, without failing the rest of the dashboard; covered in Task 3 tests.
3. Multiple wireless SSIDs and disabled radios must not be double-counted as client devices; covered in Task 3 fixture tests.
4. `/mnt/usb` absent during boot or backup transitions must render `Not mounted`, with no write or mount attempt; covered in Task 3 tests.
5. Theme JS failure/localStorage corruption must leave full LuCI navigation usable; covered in Task 2 fallback contract tests.

---

### Task 1: Repository scaffold and contract-test harness

**Files:**
- Create: `README.md`
- Create: `tests/test_contract.py`
- Create: `scripts/check.sh`
- Create: `.gitignore`

**Interfaces:**
- Consumes: approved design spec.
- Produces: `scripts/check.sh` as the single local verification entrypoint; repository-wide tests that later tasks extend.

- [ ] **Step 1: Write failing repository contract tests**

Add `unittest` cases for required package directories, no remote `http://`/`https://` asset references in runtime CSS/JS/templates, valid JSON under `menu.d` and `acl.d`, and a hard combined runtime asset budget of `1_000_000` bytes.

- [ ] **Step 2: Run tests and verify the initial failure**

Run: `python3 -m unittest discover -s tests -v`

Expected: FAIL because theme/dashboard package paths do not yet exist.

- [ ] **Step 3: Add repository scaffold and check script**

`README.md` documents target device, build/install scope and rollback principle. `scripts/check.sh` runs Python tests plus `node --check` for every repository JS file when Node is available.

- [ ] **Step 4: Re-run tests**

Expected: tests still fail only for package files intentionally created in Tasks 2–4; harness itself runs cleanly.

- [ ] **Step 5: Commit**

Commit: `test: add LuCI dashboard contract harness`

---

### Task 2: Implement the lightweight Archer LuCI theme shell

**Files:**
- Create: `luci-theme-archer/Makefile`
- Create: `luci-theme-archer/root/etc/uci-defaults/30_luci-theme-archer`
- Create: `luci-theme-archer/ucode/template/themes/archer/header.ut`
- Create: `luci-theme-archer/ucode/template/themes/archer/footer.ut`
- Create: `luci-theme-archer/ucode/template/themes/archer/sysauth.ut`
- Create: `luci-theme-archer/htdocs/luci-static/archer/cascade.css`
- Create: `luci-theme-archer/htdocs/luci-static/archer/mobile.css`
- Create: `luci-theme-archer/htdocs/luci-static/archer/logo.svg`
- Create: `luci-theme-archer/htdocs/luci-static/archer/logo_48.png`
- Create: `luci-theme-archer/htdocs/luci-static/resources/menu-archer.js`
- Modify: `tests/test_contract.py`

**Interfaces:**
- Consumes: stock LuCI menu tree via `ui.menu.load()` and dispatcher URLs.
- Produces: theme name `Archer`, media base `/luci-static/archer`, localStorage key `archer-ui-mode` with values `simple|advanced`, DOM attribute `data-archer-mode`.

- [ ] **Step 1: Extend tests for theme registration and fail-safe behavior**

Assert: UCI defaults register `themes.Archer=/luci-static/archer` without deleting Bootstrap; templates use `dispatcher.build_url()`; standard menu DOM exists before `menu-archer.js` applies Simple mode; invalid/missing `archer-ui-mode` defaults to `simple`, while JS absence does not hide standard LuCI navigation.

- [ ] **Step 2: Run tests and verify failure**

Run: `python3 -m unittest discover -s tests -v`

Expected: FAIL for missing theme files.

- [ ] **Step 3: Implement package metadata and UCI registration**

Follow OpenWrt 25.12 LuCI theme Makefile pattern: `LUCI_TITLE`, `LUCI_DEPENDS:=+luci-base`, Apache-2.0 metadata, `include ../../luci.mk`; register Archer while keeping Bootstrap intact.

- [ ] **Step 4: Implement ucode shell and progressive-enhancement toggle**

Use `system board` in `header.ut`, render primary/secondary branding, Simple/Advanced control, simple sidebar links built with `dispatcher.build_url()`, full LuCI menu containers, and local theme script. `menu-archer.js` must expose `setMode(mode)` and `getMode()`; Simple mode hides the stock navigation only after JS initializes successfully; Advanced mode restores it immediately.

- [ ] **Step 5: Implement approved visual system**

Create dark navy/charcoal layout, left rail, rounded cards, restrained blue/purple accent, status pills and responsive mobile collapse. Use only local assets and system fonts.

- [ ] **Step 6: Validate**

Run: `./scripts/check.sh`

Expected: PASS for theme tests and JS syntax; total theme runtime assets remain below `600_000` bytes.

- [ ] **Step 7: Commit**

Commit: `feat: add Archer LuCI theme shell`

---

### Task 3: Implement dashboard data adapter and six-card view

**Files:**
- Create: `luci-app-archer-dashboard/Makefile`
- Create: `luci-app-archer-dashboard/htdocs/luci-static/resources/view/archer-dashboard/dashboard.js`
- Create: `luci-app-archer-dashboard/htdocs/luci-static/resources/archer-dashboard/data.js`
- Create: `luci-app-archer-dashboard/htdocs/luci-static/resources/archer-dashboard/dashboard.css`
- Create: `tests/fixtures/dashboard/*.json`
- Modify: `tests/test_contract.py`

**Interfaces:**
- Consumes: LuCI `rpc`, `network`, `fs`/RPC facilities and standard runtime ubus data.
- Produces: `data.loadSnapshot() -> Promise<Snapshot>` where `Snapshot` contains `internet`, `wifi`, `vpn`, `devices`, `storage`, `system`; every section is renderable even when its source is unavailable.

- [ ] **Step 1: Add fixture-driven contract tests**

Cover: WAN up/down, WAN6 missing, two active radios, disabled radio, multiple SSIDs, no WG, WG active, `/mnt/usb` mounted/unmounted, temperature missing. Assert no secret/private key field can appear in serialized VPN output.

- [ ] **Step 2: Run tests and verify failure**

Expected: FAIL because data adapter/view do not exist.

- [ ] **Step 3: Implement read-only data normalization**

`data.js` normalizes runtime values into stable card objects. Use standard LuCI RPC/network interfaces first. WireGuard and storage must degrade gracefully when the corresponding runtime source is absent. Do not run write commands, modify UCI or mount filesystems.

- [ ] **Step 4: Implement dashboard rendering**

`dashboard.js` renders exactly six cards: Internet, Wi-Fi, VPN, Devices, Storage, System. Each card uses real values or explicit `Not available` states and links to existing LuCI configuration pages with `L.url(...)`. Auto-refresh the volatile snapshot every 10 seconds and stop/update cleanly on view teardown.

- [ ] **Step 5: Match the approved mockup without inventing metrics**

Use the approved card hierarchy, spacing and badges. Do not hard-code screenshot values such as client counts, temperatures, IPs or transfer counters.

- [ ] **Step 6: Validate**

Run: `./scripts/check.sh`

Expected: PASS; no external runtime URL; no secrets; dashboard assets keep combined package budget below `1_000_000` bytes.

- [ ] **Step 7: Commit**

Commit: `feat: add Archer status dashboard`

---

### Task 4: Add LuCI menu/ACL integration and navigation targets

**Files:**
- Create: `luci-app-archer-dashboard/root/usr/share/luci/menu.d/luci-app-archer-dashboard.json`
- Create: `luci-app-archer-dashboard/root/usr/share/rpcd/acl.d/luci-app-archer-dashboard.json`
- Modify: `tests/test_contract.py`

**Interfaces:**
- Consumes: `dashboard.js` view and the minimum ubus/RPC methods used by `data.js`.
- Produces: LuCI path `admin/archer/dashboard` titled `Dashboard`; ACL name `luci-app-archer-dashboard` with read-only permissions only.

- [ ] **Step 1: Add failing JSON/menu/ACL tests**

Assert: dashboard menu action is type `view` with path `archer-dashboard/dashboard`; ACL contains no `write` section; ACL grants only methods actually used by Task 3.

- [ ] **Step 2: Run tests and verify failure**

Expected: FAIL for missing integration JSON.

- [ ] **Step 3: Implement menu and least-privilege ACL**

Use OpenWrt 25.12 `menu.d` and `rpcd/acl.d` JSON conventions. Do not expose arbitrary shell execution. If one exact read command proves unavoidable for a metric, whitelist only that exact executable/argument form and add a regression test; otherwise omit command execution entirely.

- [ ] **Step 4: Validate navigation paths**

Check simple sidebar links resolve to existing LuCI paths and Advanced mode still uses the normal menu tree. Missing optional pages must not break dashboard rendering.

- [ ] **Step 5: Run full checks and commit**

Run: `./scripts/check.sh`

Expected: PASS.

Commit: `feat: wire Archer dashboard into LuCI`

---

### Task 5: Build real OpenWrt 25.12.5 `.apk` packages and measure footprint

**Files:**
- Create: `scripts/build-openwrt-25.12.5.sh`
- Create: `docs/build.md`
- Modify: `tests/test_contract.py`

**Interfaces:**
- Consumes: OpenWrt SDK `openwrt-sdk-25.12.5-ath79-generic_gcc-14.3.0_musl.Linux-x86_64.tar.zst` with published SHA256 `bc4307ae2065c0c0b7c84627356e9f3d368a5a803c81552fcb77aa034a843f5a`.
- Produces: `luci-theme-archer*.apk` and `luci-app-archer-dashboard*.apk`, plus measured installed/runtime sizes.

- [ ] **Step 1: Add build-script contract tests**

Assert the build script pins OpenWrt `25.12.5`, target `ath79/generic`, verifies the SDK checksum and never invokes `opkg` or builds an `.ipk` artifact.

- [ ] **Step 2: Run tests and verify failure**

Expected: FAIL for missing build script.

- [ ] **Step 3: Implement deterministic SDK build script**

Download/reuse the verified SDK, stage both local packages under a custom feed/package path, run feed/config preparation and compile only the two packages. Do not build firmware images.

- [ ] **Step 4: Build packages**

Run: `./scripts/build-openwrt-25.12.5.sh`

Expected: two `.apk` artifacts for the target package architecture, no `.ipk` output.

- [ ] **Step 5: Inspect package metadata and size**

Use SDK/host tooling plus `apk adbdump` where available. Record compressed and unpacked sizes in `docs/build.md`. Hard stop if combined persistent footprint estimate is `>=1_000_000` bytes; optimize assets before any router install.

- [ ] **Step 6: Run full checks and commit**

Run: `./scripts/check.sh`

Expected: PASS.

Commit: `build: package Archer dashboard for OpenWrt 25.12`

---

### Task 6: Controlled install, smoke test and rollback proof on Archer C7

**Files:**
- Modify: `README.md` with verified install/rollback commands and measured post-install footprint.
- No firmware, partition or USB filesystem changes.

**Interfaces:**
- Consumes: built `.apk` artifacts and existing SSH path `Proxmox -> VM101 -> WireGuard -> OpenWrt`.
- Produces: verified live dashboard plus documented rollback to Bootstrap.

- [ ] **Step 1: Revalidate live target before mutation**

Over root SSH through VM101, record `ubus call system board`, `df -h /overlay`, current `luci.main.mediaurlbase`, `apk list -I | grep '^luci-'`, `/mnt/usb` mount state, and SSH reachability.

Expected: same Archer C7 v5/OpenWrt 25.12.5 target, healthy SSH, active backup disk untouched.

- [ ] **Step 2: Create rollback backup**

Create an OpenWrt configuration backup to `/tmp` and transfer it off-router to the Proxmox working area. Record SHA256. Do not store backup output on `/mnt/usb` while the existing backup job is active.

- [ ] **Step 3: Transfer and verify package artifacts**

Copy both `.apk` files to `/tmp` on OpenWrt and verify SHA256 against build-host artifacts.

- [ ] **Step 4: Install locally with OpenWrt 25.12 apk**

Run local install with `apk add --allow-untrusted ./<package>.apk` for the two self-built packages. Do not run `apk upgrade`.

- [ ] **Step 5: Activate Archer theme without removing Bootstrap**

Set `luci.main.mediaurlbase=/luci-static/archer`, commit only LuCI config, clear transient LuCI cache if necessary, and restart only the required web/RPC service if necessary.

- [ ] **Step 6: Perform live smoke tests**

Verify login, dashboard render, Internet/Wi-Fi/WG/Devices/Storage/System values against CLI runtime, Simple/Advanced toggle, standard settings pages, `/mnt/usb` unchanged, SSH still reachable and post-install overlay free space safely above the pre-agreed margin.

- [ ] **Step 7: Prove rollback**

Switch `mediaurlbase` back to `/luci-static/bootstrap`, confirm stock LuCI loads, then reactivate Archer only after rollback PASS. This proves fallback before declaring the custom UI complete.

- [ ] **Step 8: Final Git verification and commit**

Update README with the exact verified package names, hashes, footprint and rollback procedure. Run `./scripts/check.sh`, `git diff`, and `git status`.

Expected: all tests PASS, working tree clean after commit, router health PASS, stock Bootstrap fallback proven.

Commit: `docs: record verified Archer dashboard deployment`

---

## Completion Gate

Do not claim PROJECT_DONE until all of the following are true: repository tests PASS; OpenWrt 25.12.5 `.apk` packages build successfully; combined measured persistent footprint is `<1 MB`; SSH remains reachable; `/mnt/usb` backup workflow is untouched; all six cards display truthful live values or explicit unavailable states; Simple/Advanced works; stock LuCI pages work; Bootstrap rollback is proven; commits are pushed to GitHub and deployed router state is verified after the final commit.