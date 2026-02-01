# Style and Conventions

- **Type safety**: Zero tolerance for `Any`, no implicit `Any`, no `# type: ignore`.
- **Protocols**: Use `typing.Protocol` for abstractions; implementations in `apps/api/adapters/`.
- **Async**: All I/O uses async/await.
- **Logging**: structlog with correlation IDs.
- **Testing**: pytest with anyio; unit tests should mock external SDK (see project instructions).
- **Formatting/Lint**: Ruff with line length 88; format via `ruff format`.

Source: `CLAUDE.md`, `pyproject.toml`.