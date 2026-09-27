# OpenWrt Archer C7 LuCI Dashboard

Lightweight LuCI theme and read-only dashboard for TP-Link Archer C7 v5 running OpenWrt 25.12.5.

## Goals

- Premium dark dashboard matching the approved project mockup.
- Standard LuCI remains available as the Advanced/fallback interface.
- Combined custom runtime footprint stays below 1 MB.
- No TorGuard/PrivateRouter branding, external CDN, daemon, database, extroot or USB repartitioning.

## Development

Run the repository checks with:

```sh
./scripts/check.sh
```

Build and deployment instructions are added once the OpenWrt 25.12.5 `.apk` artifacts are reproducibly built and verified.

## Rollback principle

The stock `luci-theme-bootstrap` package is never removed. The custom UI must remain removable without affecting SSH, networking, or the active `/mnt/usb` backup workflow.
