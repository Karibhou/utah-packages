#!/usr/bin/env python3
"""A maintainer-reviewed fork pull request may be copied in for a Canary run, and nothing else."""

import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from tools import fork_canary

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "canary-fork-pr.yml"

REPO = "projectbluefin/utah-packages"
REVIEWED = "a" * 40
MOVED = "b" * 40


def pr(**over):
    base = {
        "state": "open",
        "base": {"ref": "main"},
        "head": {"sha": REVIEWED, "repo": {"full_name": "someone/utah-packages"}},
    }
    base.update(over)
    return base


class DecideTests(unittest.TestCase):
    def test_a_reviewed_fork_pull_request_is_copied(self):
        self.assertEqual(fork_canary.decide(pr(), ["packages/foo/foo.spec"], REPO, REVIEWED), "copy")

    def test_a_head_that_moved_since_review_is_refused(self):
        # The maintainer approved REVIEWED; a push after that is unreviewed code.
        moved = pr(head={"sha": MOVED, "repo": {"full_name": "someone/utah-packages"}})
        with self.assertRaisesRegex(fork_canary.Refused, "moved"):
            fork_canary.decide(moved, [], REPO, REVIEWED)

    def test_only_a_full_sha_is_accepted(self):
        for sha in ("", "abc123", REVIEWED[:12], REVIEWED.upper(), "main", REVIEWED + "0"):
            with self.subTest(sha=sha), self.assertRaisesRegex(fork_canary.Refused, "40-character"):
                fork_canary.decide(pr(), [], REPO, sha)

    def test_a_closed_or_non_main_pull_request_is_refused(self):
        with self.assertRaises(fork_canary.Refused):
            fork_canary.decide(pr(state="closed"), [], REPO, REVIEWED)
        with self.assertRaises(fork_canary.Refused):
            fork_canary.decide(pr(base={"ref": "release"}), [], REPO, REVIEWED)

    def test_workflow_changes_from_a_fork_are_never_copied(self):
        # canary.yml and the workflows it calls hold packages: write.
        for name in (".github/workflows/canary.yml", ".github/actions/x/action.yml", ".github/CODEOWNERS"):
            with self.subTest(name=name), self.assertRaisesRegex(fork_canary.Refused, r"\.github/"):
                fork_canary.decide(pr(), ["packages/foo/foo.spec", name], REPO, REVIEWED)

    def test_a_rename_out_of_dot_github_is_still_a_workflow_change(self):
        # The workflow lists previous_filename too, so moving a workflow away
        # is judged like editing it.
        with self.assertRaises(fork_canary.Refused):
            fork_canary.decide(pr(), ["workflows/x.yml", ".github/workflows/x.yml"], REPO, REVIEWED)

    def test_a_path_that_only_looks_like_dot_github_is_fine(self):
        for name in ("docs/.github/notes.md", "x.github/y", "packages/.github-keep/x"):
            with self.subTest(name=name):
                self.assertEqual(fork_canary.decide(pr(), [name], REPO, REVIEWED), "copy")

    def test_an_in_repository_pull_request_needs_no_copy(self):
        own = pr(head={"sha": REVIEWED, "repo": {"full_name": REPO}})
        self.assertEqual(fork_canary.decide(own, [".github/workflows/x.yml"], REPO, REVIEWED), "skip")

    def test_a_deleted_fork_is_refused_not_crashed_on(self):
        gone = pr(head={"sha": REVIEWED, "repo": None})
        with self.assertRaisesRegex(fork_canary.Refused, "deleted"):
            fork_canary.decide(gone, [], REPO, REVIEWED)

    def test_branch_names_stay_inside_the_copy_namespace(self):
        self.assertEqual(fork_canary.branch_for(618), "canary/pr-618")
        self.assertTrue(fork_canary.branch_for(1).startswith(fork_canary.BRANCH_PREFIX))


class CommandLineTests(unittest.TestCase):
    def run_cli(self, pull, files, sha=REVIEWED):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "pr.json").write_text(json.dumps(pull))
            (tmp / "files.txt").write_text("\n".join(files) + ("\n" if files else ""))
            argv = ["--pr-json", str(tmp / "pr.json"), "--files", str(tmp / "files.txt"),
                    "--repository", REPO, "--head-sha", sha]
            with mock.patch("builtins.print") as out:
                code = fork_canary.main(argv)
            return code, "\n".join(str(c.args[0]) for c in out.call_args_list)

    def test_an_approved_copy_prints_the_action_the_workflow_reads(self):
        code, out = self.run_cli(pr(), ["packages/foo/foo.spec"])
        self.assertEqual(code, 0)
        self.assertIn("action=copy", out.splitlines())

    def test_a_refusal_fails_the_run_with_an_annotation_and_no_action(self):
        code, out = self.run_cli(pr(), [".github/workflows/canary.yml"])
        self.assertEqual(code, 1)
        self.assertIn("::error", out)
        self.assertNotIn("action=", out)

    def test_an_in_repository_pull_request_succeeds_with_skip(self):
        own = pr(head={"sha": REVIEWED, "repo": {"full_name": REPO}})
        code, out = self.run_cli(own, ["packages/foo/foo.spec"])
        self.assertEqual(code, 0)
        self.assertIn("action=skip", out.splitlines())


class WorkflowTests(unittest.TestCase):
    """The workflow moves a ref; it must never run what it is moving."""

    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text()
        cls.wf = yaml.safe_load(cls.text)
        cls.steps = cls.wf["jobs"]["dispatch"]["steps"]

    def test_it_runs_only_when_a_maintainer_dispatches_it_with_the_reviewed_commit(self):
        on = self.wf.get("on", self.wf.get(True))
        self.assertEqual(set(on), {"workflow_dispatch"})
        inputs = on["workflow_dispatch"]["inputs"]
        self.assertEqual(set(inputs), {"pr", "head_sha"})
        self.assertTrue(all(i["required"] for i in inputs.values()))

    def test_it_holds_no_more_than_it_needs(self):
        self.assertEqual(self.wf["permissions"],
                         {"contents": "write", "pull-requests": "write", "actions": "write"})

    def test_it_never_checks_out_or_runs_the_pull_request(self):
        for step in self.steps:
            if str(step.get("uses", "")).startswith("actions/checkout"):
                self.assertNotIn("ref", step.get("with", {}),
                                 "the only checkout is this workflow's own ref")
        # The fork's commit is fetched as a ref and pushed; nothing executes it.
        runs = "\n".join(s.get("run", "") for s in self.steps)
        self.assertNotRegex(runs, r"git (checkout|switch|merge|cherry-pick|rebase)")
        self.assertNotRegex(runs, r"\b(just|make|podman|docker)\b")
        self.assertRegex(runs, r'git fetch --no-tags --depth=1 origin "refs/pull/\$\{PR\}/head"')

    def test_the_commit_pushed_is_the_commit_that_was_reviewed(self):
        runs = "\n".join(s.get("run", "") for s in self.steps)
        # Fetched head must equal the reviewed sha before it is pushed, and the
        # push names that sha, never a branch that could move.
        verify = runs.index('test "$(git rev-parse FETCH_HEAD)" = "$HEAD_SHA"')
        push = runs.index('git push --force origin "${HEAD_SHA}:refs/heads/canary/pr-${PR}"')
        self.assertLess(verify, push)
        self.assertIn(fork_canary.BRANCH_PREFIX + "${PR}", runs)

    def test_the_dispatch_names_no_pr_so_an_older_canary_yml_still_runs_it_unconditionally(self):
        # The copied branch carries the pull request's own canary.yml, which may
        # predate any change to the fork guard. Without a pr input every version
        # takes the same-repository path.
        dispatch = next(s for s in self.steps if s.get("name") == "Dispatch Canary on the copy")
        self.assertIn('gh workflow run canary.yml -R "$REPOSITORY" --ref "canary/pr-${PR}"', dispatch["run"])
        self.assertNotRegex(dispatch["run"], r"-f\s+pr=")

    def test_every_later_step_waits_for_the_decision_to_copy(self):
        for name in ("Copy the reviewed commit into this repository", "Dispatch Canary on the copy",
                     "Tell the pull request"):
            step = next(s for s in self.steps if s.get("name") == name)
            self.assertEqual(step["if"], "steps.check.outputs.action == 'copy'")

    def test_copies_of_closed_pull_requests_are_cleaned_up_without_hiding_errors(self):
        cleanup = next(s for s in self.steps if str(s.get("name", "")).startswith("Delete copies"))
        # A bare `|| true` would also swallow a failed API call.
        self.assertNotRegex(cleanup["run"], r"\|\|\s*true")
        self.assertRegex(cleanup["run"], r"grep -E .*\|\| test \$\? -eq 1")
        self.assertTrue(re.search(r'"\$state" != open', cleanup["run"]))


if __name__ == "__main__":
    unittest.main()
