# Repository Guidelines

- Read `develop_plan.md` before making code, documentation, test, or asset changes.
- Keep FramePilot local-first. Do not introduce cloud upload, login, payment, or other remote-service requirements.
- Never modify original photo files. Write derived outputs, metadata, caches, or exports separately.
- Do not add large model files to the repository.
- Living documentation is bilingual: each English page (`name.md`) has a matching Chinese counterpart (`name.zh.md`), and each page links to the other near the top. Code, comments, tests, and commit messages remain English.
- Prefer small, deterministic image-processing algorithms for the MVP.
- Add or update tests for scoring, grouping, export, and status update logic when touching those areas.
- Run relevant tests, lint, and type checks before finishing work.
- Review the final diff before summarizing changes.
