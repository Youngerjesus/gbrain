# Post-Bootstrap Customization Checklist

After bootstrapping, customize these items before serious implementation starts:

1. Update root `README.md` with the project purpose and local setup notes.
2. Replace placeholder values in `AGENTS.md`, especially product direction, non-goals, critical operating rules, engineering rules, and verification policy.
3. Fill `main/docs/project_overview.md` and remove any non-applicable sections.
4. Fill `main/docs/tech_stack.md` with the actual runtime, data, testing, linting, deployment, and observability choices.
5. Decide whether the project needs a root `DESIGN.md`.
6. If the project has no meaningful UI or brand surface, delete `DESIGN.md` or never generate it.
7. If the project has a meaningful UI or brand surface, replace the placeholder token examples in `DESIGN.md` with project-specific rules.
8. Create the first real requirement under `main/requirements/`, or create a goal sequence under `main/goal-requirements/` for multi-slice work.
9. Remove any sections that are explicitly out of scope for the project instead of leaving dead placeholder text behind.
10. Review the curated agent and skill bundle and remove any defaults the repository does not intend to use.
