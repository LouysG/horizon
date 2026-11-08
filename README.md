# Horizon

_This README was generated using AI_

Horizon is a Python-based geospatial data platform for generating digital twins of the operating environments of individual drones and drone fleets.

**Status:** v0.1 — early development. The current focus is establishing the development environment and implementing the initial application components.

## Development environment

Horizon uses the following tools:

| Tool | Purpose |
| --- | --- |
| Python 3.12 | Application runtime |
| [uv](https://docs.astral.sh/uv/) | Python installation, virtual environments, dependency management, and command execution |
| [Ruff](https://docs.astral.sh/ruff/) | Formatting, linting, and import sorting |
| [ty](https://docs.astral.sh/ty/) | Static type checking |
| [pytest](https://docs.pytest.org/) | Automated testing |
| Git and GitHub | Version control and collaboration |
| GitHub Actions | Continuous integration |

Python 3.12 is specified in `.python-version`. Project metadata, dependencies, and tool configuration live in `pyproject.toml`; `uv.lock` records resolved dependencies.

## Getting started

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Git, then clone the repository and open a terminal in its **project root** (the directory containing `pyproject.toml`).

```bash
# From the project root
uv sync
```

`uv sync` creates or updates the project's `.venv` and installs the project and its development dependencies. uv can provision the required Python version if necessary.

Start Horizon with either command:

```bash
uv run horizon
# or
uv run python -m horizon
```

Both invoke the application's `main()` entrypoint in `src/horizon/__main__.py`. At this stage, startup is a basic initialization check rather than a complete application workflow.

> **macOS note:** Prefer a local development directory such as `~/Projects/` over iCloud-synced Desktop or Documents folders. On some macOS setups, filesystem `hidden` flags can cause Python to skip editable-installation `.pth` files, producing `ModuleNotFoundError` even when `uv sync` succeeds. If this occurs, move the repository to a non-synced directory, remove the generated `.venv`, and run `uv sync` again.

## Repository layout

The current source layout includes:

```text
horizon/
├── .python-version
├── pyproject.toml
├── uv.lock
├── data/                     # In-process database
├── docs/                     # Design docs
├── src/
│   └── horizon/
│       ├── __init__.py
│       ├── __main__.py       # Application entrypoint
│       ├── app/              # Application components
│       └── db/               # Database schema and access code
└── tests/                    # Automated tests
```

This is a `src/`-layout Python package. The repository root and the importable `horizon` package directory are different directories; run the commands in this README from the repository root.

## Development commands

Run these commands from the project root:

| Task | Command |
| --- | --- |
| Synchronize the environment | `uv sync` |
| Start Horizon | `uv run horizon` |
| Format code | `uv run ruff format .` |
| Check formatting | `uv run ruff format --check .` |
| Lint code | `uv run ruff check .` |
| Apply supported lint fixes | `uv run ruff check --fix .` |
| Check types | `uv run ty check` |
| Run tests | `uv run pytest` |

Ruff is configured for a 100-character line length and import sorting. VS Code users can configure Ruff to format and organize imports on save; editor-specific configuration is optional.

### Run all checks

Before opening a pull request, run the same checks used in CI:

```bash
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked ty check
uv run --locked pytest
```

The `--locked` option prevents uv from updating `uv.lock` while running these checks.

## Scope of v0.1

Horizon v0.1 is intended to establish the first usable version of the platform, including data acquisition, world-model generation, querying and manipulation, a programming interface, and a graphical interface. These capabilities are being developed incrementally; their inclusion here does not imply they are implemented yet.

Further architecture, data-model, and interface documentation can be added as those components take shape.
