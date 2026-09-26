# Archer C7 LuCI Dashboard — Design Spec

## Objective

Build a lightweight, premium-looking LuCI theme and dashboard for the user's TP-Link Archer C7 v5 running OpenWrt 25.12.5. The visual target is the supplied PrivateRouter/OAT-style dashboard: dark navy UI, left sidebar, rounded status cards, compact status badges, and a Simple/Advanced control. The implementation must preserve standard LuCI as the advanced/fallback interface.

## Verified target device

- Model: TP-Link Archer C7 v5
- Board: `tplink,archer-c7-v5`
- OpenWrt: `25.12.5 r33051-f5dae5ece4`
- Target: `ath79/generic`
- Kernel: `6.12.94`
- Rootfs: squashfs + overlay
- Free overlay at design time: about 4.7 MB
- Package manager: `apk`
- Existing LuCI packages: `luci-base`, `luci-theme-bootstrap`
- USB storage currently mounted at `/mnt/usb`
- The USB disk is actively used for backup; repartitioning, resizing, formatting, or extroot work is explicitly out of scope for this phase.

## Design intent

The UI should look very close to the approved mockup and the PrivateRouter reference, without cosmetic over-design or unrelated visual experiments.

Branding:

- Primary: `OpenWrt • Archer C7`
- Secondary: `OpenWrt 25.12.5 • TP-Link Archer C7 v5`
- No PrivateRouter, TorGuard, or BlackServ branding.

Visual language:

- dark navy/charcoal background
- left navigation rail
- rounded cards with subtle borders
- restrained blue/purple accent
- compact green/blue/gray state pills
- clean sans-serif typography
- SVG icons where possible
- desktop first, but responsive for tablet/mobile
- no heavy JS framework and no external CDN

## Scope for v1

### Simple dashboard

The dashboard contains six primary cards.

#### Internet

Show:

- WAN online/offline
- IPv4 address
- IPv6 address when present
- gateway
- logical interface
- protocol
- connection uptime when available

The card links to the existing LuCI network settings rather than reimplementing network configuration.

#### Wi-Fi

Show:

- 2.4 GHz radio status
- 5 GHz radio status
- SSID(s)
- channel
- mode where useful
- connected client count
- signal information where available and meaningful

The card links to standard LuCI wireless configuration.

#### VPN

For v1, prioritize WireGuard status only.

Show when available:

- interface name
- connected/inactive state
- latest handshake
- transfer counters
- peer/endpoint summary without exposing secrets

The card links to the existing LuCI/WireGuard configuration page if installed. It does not implement a TorGuard-specific client.

#### Devices

Show a concise client summary:

- total active clients
- wired count where determinable
- Wi-Fi 2.4 GHz count
- Wi-Fi 5 GHz count

No new device inventory subsystem or database is introduced.

#### Storage

Show `/mnt/usb` status:

- mounted/unmounted
- total capacity
- used space
- free space
- filesystem type when available

No partition management or filesystem mutation is included.

#### System

Show:

- router model
- OpenWrt version
- architecture/SoC summary
- load averages
- memory use
- uptime
- temperature only if the target exposes a reliable sensor

Do not show fabricated values when the device does not expose a metric.

## Navigation

Simple-mode sidebar:

1. Dashboard
2. Internet
3. Wi-Fi
4. VPN
5. Devices
6. Storage
7. System
8. separator
9. Advanced LuCI
10. Log out

For v1, menu items may link to existing LuCI pages instead of cloning every settings screen. The goal is a premium dashboard and navigation shell, not a complete rewrite of LuCI.

## Simple / Advanced behavior

- Simple mode opens the custom dashboard/navigation shell.
- Advanced mode exposes the normal LuCI navigation and configuration pages.
- Advanced mode must remain usable even if the custom dashboard has a rendering problem.
- The custom code must not patch or replace LuCI core files.
- Bootstrap remains available as a rollback theme.

Implementation should follow standard LuCI extension points: theme assets, view files, menu definitions, and RPC/ubus access through LuCI facilities.

## Architecture

Use a small repository containing only the custom work, not a fork of the full OpenWrt source tree.

Proposed package layout:

```text
openwrt/
├── luci-theme-archer/
│   ├── htdocs/luci-static/archer/
│   │   ├── css/
│   │   ├── js/
│   │   └── icons/
│   ├── ucode/template/themes/archer/
│   ├── root/etc/uci-defaults/
│   └── Makefile
├── luci-app-archer-dashboard/
│   ├── htdocs/luci-static/resources/view/archer-dashboard/
│   ├── root/usr/share/luci/menu.d/
│   ├── root/usr/share/rpcd/acl.d/
│   └── Makefile
├── docs/
└── README.md
```

Exact paths may be adjusted to match current LuCI/OpenWrt 25.12 patterns after validation against upstream source. No legacy Lua-specific assumption should be hard-coded without verification.

## Data flow

The browser-side LuCI view requests read-only runtime information through existing LuCI RPC/ubus interfaces.

Preferred sources include:

- network/interface state from ubus/network model
- wireless state from LuCI wireless/network model
- system info from ubus/system calls
- mount/storage info from system/mount data exposed safely to LuCI
- WireGuard status from existing network/runtime interfaces when installed

No long-running daemon, database, collector, or background polling service is added. Browser-side refresh should be conservative, target approximately 5–10 seconds for volatile status values, and avoid unnecessary CPU load on the Archer C7.

## Storage footprint target

Primary target: less than 1 MB additional persistent overlay usage for the custom theme + dashboard.

Preferred target: roughly 400–700 KB if practical.

Rules:

- no bundled web framework
- no large bitmap artwork
- no external font bundle unless justified by measured size
- use system fonts and SVG icons
- minify production CSS/JS when supported by the build path
- do not move files to `/mnt/usb` in v1 unless measured package size proves the overlay target cannot be met

The existing USB backup workflow must not be disturbed.

## Package compatibility

The target firmware uses `apk`, not `opkg`. Upstream PrivateRouter release instructions that install `.ipk` files are therefore not directly applicable to this router.

The implementation must be built or packaged for the actual OpenWrt 25.12 package format/toolchain before installation. Compatibility is to be verified against current OpenWrt/LuCI source rather than assumed from older release examples.

## Safety and rollback

Before any install on the router:

1. verify current SSH access through Proxmox -> VM101 -> WireGuard -> OpenWrt
2. record current LuCI theme selection
3. create an OpenWrt configuration backup
4. record current free overlay space
5. verify the new package footprint before installation

Installation must not modify partitions, reformat storage, or alter the active backup disk.

Rollback path:

1. switch LuCI theme back to Bootstrap
2. remove/disable the custom dashboard package if needed
3. restart LuCI/uhttpd only if required
4. verify stock LuCI and SSH access

No operation may make SSH dependent on the custom UI.

## Validation

Before router deployment:

- validate package/file layout against OpenWrt 25.12 LuCI conventions
- lint/parse JavaScript and CSS as applicable
- ensure all menu/ACL JSON is syntactically valid
- verify there are no external CDN/runtime dependencies
- measure unpacked asset/package size

On-router smoke tests:

- login page loads
- dashboard loads without browser console errors
- Internet card shows real runtime data
- Wi-Fi card shows both radios correctly
- WireGuard card degrades gracefully when no WG interface exists
- Devices summary is correct enough to be useful and does not double-count obvious duplicates
- `/mnt/usb` storage values match `df`/mount state
- System values match device runtime values
- Simple/Advanced navigation works
- stock LuCI settings pages remain functional
- Bootstrap fallback works
- SSH remains reachable
- overlay free space remains within safe margin

## Explicit non-goals for v1

- no TorGuard-specific UI
- no Docker app store
- no mesh management UI
- no custom firewall editor
- no package-manager replacement UI
- no firmware flashing UI
- no partition editor
- no extroot conversion
- no large frontend framework
- no full rewrite of every LuCI settings page

## Success criteria

The project is successful when the Archer C7 presents the approved premium dark dashboard and navigation, reports real router data, retains standard LuCI in Advanced mode, stays lightweight enough for the current flash constraints, and can be rolled back to Bootstrap without affecting router connectivity or the active USB backup workflow.
