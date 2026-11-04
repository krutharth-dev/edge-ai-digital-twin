# GitHub pull request (PR) and review guide

This guide applies to the **current Mac-hosted software MVP** in the repository. Do not use old Raspberry Pi-only installation instructions.

## Which option should I select?

| Situation | GitHub action | Explanation |
| --- | --- | --- |
| Work is not finished; code doesn't yet pass tests | **Create draft pull request** | Visible for collaboration, but not ready to merge |
| Implementation is complete, documented, tests pass and evidence is attached | **Create pull request** (not draft) | Ready for review |
| You started a draft and now completed all checks | **Ready for review** | Changes draft to a reviewable PR |
| PR has reviewer change requests or failing required checks | **Update the same branch** | The PR updates automatically on push; do not create a duplicate |
| PR has passed tests, received the necessary review and has no unsafe breaking contract change | **Squash and merge** (recommended) | Keeps main history concise; retains PR discussion |
| PR is outdated, duplicate or incompatible with current main | **Close with an explanation** | Do not merge stale content merely to empty the PR list |

**Closing is different from deleting a branch**: the PR history remains visible, and you can later reopen if genuinely needed.

## Browser-only GitHub workflow

1. Open the repository and choose **main** in the branch selector.
2. Create a new branch with a descriptive name, such as \`feature/dashboard-alert-history\`.
3. Edit or upload source files on that branch only. Commit changes to that branch.
4. Select **Compare & pull request**.
5. Set **base: main** and **compare: your feature branch**.
6. Fill in the PR template: goal, code changes, interfaces modified, tests, screenshots/logs and limitations.
7. If unfinished, click the dropdown next to **Create pull request** and select **Create draft pull request**. Otherwise, use the regular **Create pull request**.
8. Wait for all GitHub Actions checks. Open the **Checks** tab to read failures.
9. Review the **Files changed** tab, resolve review feedback and update your branch.
10. When finished, click **Ready for review** if it was draft. After checks/review pass, use **Squash and merge**, then **Confirm squash and merge**.
11. If GitHub offers **Delete branch** after merge, it is safe only if the branch is no longer actively in use.

## Review checklist

- Does the feature work, and is the PR description truthful about what was actually tested?
- Do unit tests, syntax checks, documentation checks, and MQTT integration tests pass?
- If \`motor01/\` topics or JSON keys changed, is docs/MQTT_CONTRACT.md updated and are both publishers and consumers compatible?
- Are \`source: SIMULATED\` measurements distinguished from physical telemetry?
- Are current, RPM, vibration, temperature, timestamps, \`run_id\` and quality flags validated?
- Are no usernames/passwords, Wi-Fi credentials, model pickles, SQLite databases or private raw recordings committed?
- For model updates: is feature order pinned, are full experiment runs separated, and are metrics tied to *physical* vs *synthetic* data honestly?
- For hardware updates: is the actual ESP32 board, pinout, 3.3 V handling, calibration and physical motor safety verified?

## Git operations on the Mac

In the **existing** checkout (do not clone again):

~~~bash
cd ~/edge-ai-digital-twin
git status --short
git fetch origin
git switch main
git pull --ff-only origin main
~~~

If \`git status --short\` shows local modifications, preserve them before switching:

~~~bash
git stash push -u -m "Backup before merging team changes"
~~~

Do **not** run \`git reset --hard\`, \`git clean -fd\`, or force push just to make an error disappear. Review conflicts and restore a stash only when you know what it contains.

For current Mac setup and how to run services, see [Mac runbook](MAC_RUNBOOK.md).

## Review standards and project permissions

- Use a **pull request** instead of pushing directly to main.
- Enable branch protection/rulesets in GitHub settings if supported by your repository and plan; at minimum recommend requiring PR review and the software CI checks.
- A repository admin can merge, revert, create branches and update repository documentation, subject to any rulesets/required checks in force.
- Do not bypass safety or testing checks simply because you have admin permission.
- An open PR is not evidence that code is already merged.
- Closing an obsolete PR is a normal, professional repository maintenance action.

## Useful links

- [Software implementation status](IMPLEMENTATION_STATUS.md)
- [Architectural decisions](DECISIONS.md)
- [Software and MQTT tests](../tests/README.md)
- [Contributing guidelines](../CONTRIBUTING.md)
