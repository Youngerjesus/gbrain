# Fix Loop

Use this loop after findings are triaged.

## 1. Verify the Scope

- Confirm the issue is visible in the rendered UI.
- Identify the smallest source area that can plausibly fix it.
- If the worktree is dirty and the same files are already changing, slow down and avoid trampling user work.

## 2. Prefer Safe Fixes

Fix order:

1. token or utility-class adjustment
2. local component styling change
3. markup cleanup for hierarchy or spacing
4. interaction logic change only if the bug is behavioral

Do not expand scope unless the original finding cannot be solved otherwise.

## 3. Re-Verify Immediately

After each fix:

- re-open the affected page
- capture or inspect the updated rendered state
- confirm the original problem is gone
- check that adjacent UI did not regress

If the change affects layout, re-check at least one mobile width and one desktop width.

## 4. Handle Risk Honestly

Stop and surface risk when:

- the fix requires broad refactoring
- the same files are heavily modified by unrelated user work
- the rendered result is ambiguous
- the issue is really a product/copy decision, not a polish issue

## 5. Close the Finding Cleanly

Mark each finding as one of:

- `verified`: fixed and re-checked in the rendered UI
- `best-effort`: likely fixed, but full verification was blocked
- `deferred`: real issue, but should not be changed inside this pass

End with the smallest credible summary:

- what was fixed
- what was deferred
- what still needs broader design direction rather than polish work
