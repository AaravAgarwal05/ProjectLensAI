# Coding Standards

## Python

- **Type hints** are required on all function signatures and public methods.
- **Docstrings** follow the Google style guide (`"""Summary line.\n\nArgs:\n    ...\nReturns:\n    ...\n"""`).
- **Formatting** uses Ruff with a line length of 100 characters.
- **Linting** uses Ruff with rule sets: E, F, I, N, W, D (pycodestyle, pyflakes, import ordering, naming, pycodestyle warnings, pydocstyle).
- **Type checking** uses mypy in strict mode.

## TypeScript / React

- **TypeScript strict mode** is enabled (all strict flags on).
- **ESLint** with the Next.js recommended configuration.
- **Prettier** for automatic formatting.
- **Tailwind CSS** for all styling — no CSS-in-JS or plain CSS files unless unavoidable.

## General

- **File size** — Keep files under 500 lines. If a module exceeds this limit, extract responsibilities into separate files.
- **Input validation** — Validate data at every system boundary (API endpoints, CLI, file imports). Never trust external input.
- **SOLID principles** — Follow single responsibility, open/closed, Liskov substitution, interface segregation, and dependency inversion.
- **Testing** — Write tests for all public interfaces and critical internal logic. Aim for >90% coverage on core modules.
- **Dependency injection** — Pass dependencies explicitly rather than relying on global state or singletons (except for registries).
