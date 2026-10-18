# DELTA — PowerVpn wave (laptop power + VPN)

Worktree: /tmp/parity-powervpn
Branch: wave/powervpn-imports (1 commit: 1542a14, based on upstream/main aec307a)
Scope: 4 recipe dirs (cap 6, used 4). No other area's packages touched.

## Recipe dirs added
- packages/tuned/ (covers assigned `tuned` + `tuned-ppd` subpackage; tuned-ppd has no dist-git source)
- packages/thermald/ (covers assigned `thermald`)
- packages/openvpn/ (covers assigned `openvpn`)
- packages/NetworkManager-openvpn/ (covers assigned `NetworkManager-openvpn` + `NetworkManager-openvpn-gnome` subpackage; -gnome has no dist-git source)

Provenance commits (Rawhide HEAD at import):
- tuned: 552f03c0fd7fbd62e62d7a1e89c4fa7bb01a291f
- thermald: dbfb69a9b7eea8dfa8a73683e5b778738410edd5
- openvpn: f46be18f1ee832437b1aa8c55daf9aa3a1ed01de
- NetworkManager-openvpn: efa5e4ad8c397ad8d97eb9b95f85f3392a95f451

## Registry deltas (for union-merge; all append-only, expect textual adjacency collisions only)
1. config/upstream-sources.json: +4 entries appended at end of `packages` array (after `htop`):
   tuned 2.28.0 (github redhat-performance), openvpn 2.7.8 (build.openvpn.net),
   NetworkManager-openvpn 1.12.5 (download.gnome.org), thermald 2.5.13
   (github intel/thermal_daemon). No `stage`, no `fallback_urls` on any of the 4
   (matches bootstrap tool output shape). NOTE: thermald entry added by hand —
   host rpmspec predates `%autosetup -C` so bootstrap_upstream_sources.py could
   not parse the spec; URL resolved manually and downloaded bytes verified
   byte-identical to the Fedora manifest pin (SHA512 3efa93be...) before locking.
2. .packit.yaml: +4 blocks under `packages:` in sorted position —
   NetworkManager-openvpn (after ModemManager), openvpn (after openrgb),
   thermald (after tecla), tuned (after tsl-area entries).
   Rendered via `tools/render_packit_config.py --write`.
3. docs/architecture.md: counts 426 -> 430 in 4 spots (list of N, root Packit +
   source lock sentence, table rows, `validated 430` line) via
   `tools/render_architecture_counts.py --write`. (Base here was 426; sibling
   waves on other branches will shift these lines — union-merge takes max/set-union.)
4. reports/factory-build-backlog.json: regenerated via `tools/factory_build_backlog.py`
   (bare run, then `--check` green). Area buckets: power pending 6->3
   (already_recipe 0->3), vpn already_recipe 3->6, pending 24->21. Entry states
   pending->already_recipe: thermald, tuned, tuned-ppd, NetworkManager-openvpn,
   NetworkManager-openvpn-gnome, openvpn (confirm openvpn hunk at push time).

## Verification
- `just check`: exit 0 (validate, factory-check, multimedia, workflow-quoting,
  runtime-contract, factory-build-backlog --check, pytest 1273 passed, 2 skipped).
- `just test`: green via the pytest gate inside `just check` (same 1273 passed).
- Deleted scratch artifact reports/direct-source-bootstrap.json (workflow-only file, not committed).

## Deliberately left out / not attempted (still queued)
- intel-lpmd, powerstat, powertop and all other VPN names (e.g. openconnect,
  strongswan, wireguard-tools, NetworkManager-libreswan etc.) — out of scope,
  remain pending in backlog.
- Factory issues #477/#478/#479: referenced for scope only, not edited.
- docs/skills/factory-build-backlog.md and config/factory-build-backlog.toml
  named in the assignment do not exist in this repo (backlog lives in
  tools/factory_build_backlog.py + reports/factory-build-backlog.json); used those.

## Dependency note (not a blocker)
- Factory-internal BuildRequires all present: desktop-file-utils, libnma,
  upower, libevdev, gtk3 (in packages/).
- NetworkManager-openvpn BuildRequires NetworkManager-libnm-devel whose source
  (NetworkManager) is NOT a factory package — it resolves from the Hummingbird
  base/buildroot, not the factory; same for toolchain BRs (gcc, make, glib2…).
  No missing factory-side source; wave order solved by build_graph at prepare.
