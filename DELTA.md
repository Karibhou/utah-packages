<<<<<<< HEAD
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
||||||| parent of 4f70878 (chore(backlog): close netfs/auth starter gaps as resolved)
=======
# DELTA — wave/netfs-auth-starters (NetFsAuth)

Worktree: /tmp/parity-netfs, branch wave/netfs-auth-starters, base upstream/main aec307a.
Recipe count: 426 → 431 (+5 dirs). pinentry-gnome3 is a subpackage of the
pinentry recipe (%package gnome3), so 6 assigned names = 5 recipe dirs.

## New recipe dirs (untracked additions)
- packages/cifs-utils/ — rawhide 7.9, commit 7d394f53deee72d404af69ff3e3a77d5950b99ba
- packages/nfs-utils/ — rawhide 2.9.2, commit 26e3c738bded2e3718add203bbbe16429fce53b2
- packages/rpcbind/ — rawhide 1.3.1, commit 21e390d3b83324e7439d98ef635be4fce8652524
- packages/autofs/ — rawhide 5.1.9, commit 1e2a140aa8f797d7de0269c9a47f615ad678fca0
- packages/pinentry/ — rawhide 1.3.3, commit 5925b9a70559e697b7fc7b6560689266b264a5ac

## Modified tracked files (union-merge against siblings)
1. config/upstream-sources.json — APPEND 5 entries at end of .packages
   (after pinentry): cifs-utils, pinentry (via bootstrap --merge), then
   nfs-utils, rpcbind, autofs (hand-added, same object shape, no
   fallback_urls — same as 261 existing entries).
   - cifs-utils 7.9 https://download.samba.org/pub/linux-cifs/cifs-utils/cifs-utils-7.9.tar.bz2 sha512 42034f9e… **plus "stage": 3** (ICU rule: cifs-utils BuildRequires libwbclient-devel from samba, an ICU linker at stage 2, so the consumer must build strictly later — same fix as gvfs at stage 3; tests/test_icu_staging.py enforced it)
   - pinentry 1.3.3 https://gnupg.org/ftp/gcrypt/pinentry/pinentry-1.3.3.tar.bz2 sha512 3562d6a8…
   - nfs-utils 2.9.2 https://www.kernel.org/pub/linux/utils/nfs-utils/2.9.2/nfs-utils-2.9.2.tar.xz sha512 3752a284…
   - rpcbind 1.3.1 https://downloads.sourceforge.net/rpcbind/rpcbind-1.3.1.tar.bz2 (https upgrade of spec's http Source0; bytes verified identical) sha512 364e8417…
   - autofs 5.1.9 https://www.kernel.org/pub/linux/daemons/autofs/v5/autofs-5.1.9.tar.gz sha512 f176eecd…
2. .packit.yaml — APPEND 5 blocks (render_packit_config.py --write):
   autofs, cifs-utils, nfs-utils, pinentry, rpcbind (alpha order in file).
3. docs/architecture.md — counts 426 → 431 (render_architecture_counts.py --write).
4. reports/factory-build-backlog.json — regen (factory_build_backlog.py):
   dev-tools already_recipe 2→12, pending 136→126; long-tail
   already_recipe 9→11, pending 170→168. Entries flipped
   pending→already_recipe: autofs, cifs-utils, cifs-utils-info,
   nfs-client-utils, nfs-common-utils, nfs-utils, nfsv3-client-utils,
   nfsv4-client-utils, pinentry, pinentry-gnome3 (+2 long-tail entries).

## Repinned manifests (part of recipe dirs, listed for review)
- packages/nfs-utils/sources: upstream re-rolled tar.xz (same tree, new
  compression bytes); repinned SHA512 to 3752a284… (was 17fffef4…).
- packages/rpcbind/sources: same, repinned to 364e8417… (was 469cddc6…).
- packages/autofs/sources: same, repinned to f176eecd… (was 30a7a47b…).
- Tree-equality proof: Fedora lookaside copies vs upstream downloads
  unpacked byte-identical (diff -r -q clean for all three pairs).
- rpcbind lock uses https:// although spec Source0 is http:// (validate
  forbids http primaries; exact https URL fetched, digest matches).

## Intra-wave BuildRequires
- None of the 5 BuildRequire each other. External factory deps, all
  already landed: cifs-utils → samba (libwbclient-devel); pinentry →
  gcr, libsecret, gtk2 (gtk2/qt/kf6 flavors per spec bconds).
  Non-factory BRs (rpcgen, libsss_autofs, krb5/ldap stacks) resolve from
  the buildroot, not this factory — no blocker.
- samba-winbind NOT touched (Closures lane).

## Validation
- tools/validate.py: exit 0 (431 recipes, 427 rawhide + 4 upstream).
- just check: exit 0.
- just test (pytest): 1273 passed, 2 skipped, 2649 subtests passed.
- pre-commit run --all-files: passed (one hook stripped a trailing blank
  line in unrelated docs/skills/package-build-cache.md; reverted to keep
  this wave scoped).
- Commit 1fac1e5 on branch wave/netfs-auth-starters. DELTA.md left
  untracked by design.
>>>>>>> 4f70878 (chore(backlog): close netfs/auth starter gaps as resolved)
