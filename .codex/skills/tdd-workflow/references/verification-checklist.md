# Verification Checklist

Before marking work complete, confirm all of the following:

- A failing test exists for each new behavior or bugfix.
- Each new test was executed and observed failing before implementation.
- The failure reason matched the missing behavior, not setup noise.
- Production code was written only after red.
- The implementation was the minimum needed to reach green.
- The targeted test passed after the implementation.
- The relevant broader suite was re-run after green.
- Refactors, if any, happened only after green and stayed green.
- Tests exercise behavior more than mocks.
- Edge cases and error paths were covered where they materially affect the change.

For pragmatic exceptions, confirm all of the following instead of red proof:

- The work is limited to UI polish, documentation, configuration, verification scripts, formatting, generated metadata, or a tiny change already covered by existing tests.
- The reason a new failing test would be artificial or duplicative is stated.
- Existing tests, checks, screenshots, fixtures, or manual inspection evidence are named.
- The narrowest relevant verification passed after the edit.
- The repo-required broader verification ran before completion.
- No behavior-changing risk was hidden behind the exception path.
