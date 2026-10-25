---
name: lane-validation
description: Validate wave recipes with dispatched Canary lane runs — lane_packages scoping, per-ref inventory, fork limits, and what a green run actually proves.
---

# Validating recipe waves with lane runs

A Canary run without package selection builds only the default canary set
(`libical`, `vulkan-headers`, `vulkan-loader`). A green run that did not name
your recipes proves nothing about them — this mistake has been made and
merged on, so treat every unattributed green with suspicion.

## Dispatching a lane

```bash
gh workflow run canary.yml -R projectbluefin/utah-packages --ref <branch> \
  -f lane_packages='["pkg-a","pkg-b"]'
```

- `lane_packages` is a JSON array of **source** package names (recipe
  directory names).
- Names resolve against the **dispatched ref's** inventory. Unmerged recipes
  are unknown on `main` — dispatch wave branches for unmerged content, `main`
  only for what is already merged there.
- The lane builds the named set `skip_publish`-style against the published
  factory for BuildRequires it does not build itself. A recipe whose
  dependencies are themselves unmerged and unpublished fails here by design;
  land dependencies first, then retry the dependent.
- `lane_backend` selects the pass6 backend. The dispatch default is
  `container` (`canary.yml`), while production builds `hermetic`
  (`rebuild-rpms.yml` default; AGENTS.md). A green lane therefore proves the
  container lane only — pass `-f lane_backend=hermetic` when the claim needs
  the production backend.
- API-opened PRs currently produce no `pull_request` workflow runs in this
  repository, so a dispatched lane is the working validation path and the
  required-check display needs admin interpretation at merge time.

## Reading a lane result

- Per-package `rebuild` jobs are the verdict. `plan` succeeding while `build`
  fails usually means dependency resolution (`builddep` conflicts, missing
  `crate()` providers, excluded ICU-era libraries).
- Common failure shapes and where they point:
  - `nothing provides libicuuc.so.77`-class conflicts → the dependency needs
    a factory build against the current ICU, not the Fedora-linked one.
  - `nothing provides crate(...)` → the Rust crate stack has no provider;
    needs a vendoring-vs-packaging decision, not a retry.
  - `Bad file` on dist-git extras (PPDs, scripts) → Fedora `.gitignore`
    patterns (`*.gz`, bare script names) left them untracked at import;
    force-add and re-run.
  - `%prep` patch hunks failing under RPM's `--fuzz=0` → write the patch
    against the post-predecessor tree (replay the spec's patch order
    locally), or use a scripted `sed` next to the spec's existing
    workarounds for backslash-continued lines unified diff cannot touch.
- A lane that fails only on recipes outside your wave is someone else's
  signal — do not re-run the whole lane to chase it; narrow `lane_packages`.

## Fork limits

Fork dispatches run the same workflow but publish to the fork registry, where
the first publish of a canary tag fails (`manifest unknown`) and the run goes
red after otherwise successful builds. Use forks for parallel signal only;
merge decisions cite upstream runs.

## Fork pull requests and the required Canary (#369)

The required `Canary` check cannot pass from a fork pull request that touches a
pipeline path: its token has no `packages: write`, so `canary.yml` fails it with
"a fork pull request cannot publish the canary image". The author cannot fix
that, and neither can an agent working from a fork; do not ask them to.

A maintainer who has reviewed the diff runs **Canary for a fork pull request**
(Actions tab, `canary-fork-pr.yml`) with the pull request number and the full
head commit they reviewed. It copies exactly that commit to `canary/pr-<N>`
and dispatches `canary.yml` there, so the `Canary` check is created on the
pull request's own head commit. It refuses when the head moved since review,
when the pull request is not open against `main`, and when it changes
`.github/` (workflow changes never run with this repository's credentials from
a fork; push those by hand). A new push to the pull request needs a new
review and a new run.

The canary run builds the fork's code with `packages: write`, so the review is
the security boundary, exactly as it was when a maintainer pushed the branch by
hand. The fork's own red `pull_request` Canary run stays on the pull request.
The dispatched run is a second `Canary` check on the same commit; it is
expected to supersede the red one for the required-check rule (the newest run
of a check name counts), but that was not observed when this was written. If a
pull request still shows the check as failing after a green dispatched run,
record it on #369 rather than bypassing the check.
