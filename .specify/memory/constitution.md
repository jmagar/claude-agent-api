<!--
Sync Impact Report
==================
Version change: NEW (1.0.0) - Initial ratification
Modified principles: N/A (new document)
Added sections:
  - Core Principles (8 principles)
  - Code Standards
  - Repository Structure
  - Documentation Standards
  - Service Lifecycle
  - Development Workflow
  - Governance
Removed sections: N/A
Templates requiring updates:
  ✅ plan-template.md - Constitution Check section compatible
  ✅ spec-template.md - Requirements and testing alignment compatible
  ✅ tasks-template.md - TDD and phase structure compatible
Follow-up TODOs: None
-->

# Project Constitution

## Preamble

This constitution establishes the governing principles and development guidelines for this project. All contributors, automated agents, and tooling MUST adhere to these principles. The constitution is technology-agnostic and applies regardless of programming language, framework, or platform.

## Core Principles

### I. Research-Driven Development

All development work MUST follow the sequence: **Investigate → Plan → Validate → Implement**.

- NEVER write code before understanding the problem domain
- Research existing patterns, dependencies, and constraints before proposing solutions
- Document research findings and reasoning for architectural decisions
- Plan implementation steps before writing any code
- Validate plans against requirements before execution

**Rationale**: Uninformed implementation leads to rework, technical debt, and misaligned solutions. Research prevents wasted effort.

### II. Verification-First

No claims of completion without proof. Evidence MUST precede assertions.

- Every feature MUST be demonstrably working before marking complete
- Tests MUST pass and be verified, not assumed
- Build artifacts MUST be validated
- Integration points MUST be tested with real dependencies where feasible
- Claims like "it works" or "done" require accompanying evidence (logs, test output, screenshots)

**Rationale**: Unverified claims mask bugs and create false confidence. Proof prevents production failures.

### III. Security by Default

Credentials and secrets MUST NEVER appear in code, documentation, logs, or version control.

- Use environment variables or secure secret management for all sensitive data
- Validate and sanitize all external inputs at system boundaries
- Follow the principle of least privilege for all access controls
- Audit logs MUST NOT contain sensitive information
- Default to secure configurations; insecure options MUST be explicitly enabled

**Rationale**: Security breaches are costly and often irreversible. Prevention is mandatory.

### IV. Modularity and Simplicity

Code MUST be organized into small, focused, single-responsibility components.

- Functions MUST NOT exceed 50 lines; extract helpers if longer
- Functions MUST NOT accept more than 5 parameters; use structured objects for more
- Each module/file MUST have a clear, singular purpose
- Prefer early returns over deep nesting
- Cyclomatic complexity MUST remain below 10 per function

**Rationale**: Large, complex code is harder to test, debug, and maintain. Simplicity enables velocity.

### V. Test-Driven Development

All features and bug fixes MUST follow the TDD cycle: **RED → GREEN → REFACTOR**.

1. **RED**: Write a failing test first (proves the test catches the problem)
2. **GREEN**: Write minimal code to make the test pass
3. **REFACTOR**: Improve code quality while keeping tests green

Requirements:
- Unit tests for all new code; mock external dependencies
- Integration tests for critical workflows
- Tests MUST be deterministic (same input → same output)
- Tests MUST be isolated (can run in any order)
- Tests MUST be fast (optimize slow tests, use parallel execution)
- Target 85%+ code coverage
- Zero tolerance for flaky tests

**Rationale**: Tests written after implementation often miss edge cases. TDD ensures testability by design.

### VI. Self-Hosted Infrastructure

Prefer self-hosted services over cloud providers and SaaS solutions.

- Avoid vendor lock-in; maintain control over data and infrastructure
- Use containerization for consistent deployment environments
- Document all infrastructure dependencies and setup procedures
- Ensure offline capability where feasible

**Rationale**: Self-hosting provides full control, privacy, cost predictability, and independence from third-party service changes.

### VII. Permission-Based Operations

Always ask before managing service lifecycles (deploy, shutdown, restart, migrate).

- NEVER force-terminate existing services without explicit approval
- Verify resource availability before allocation
- Document all lifecycle changes with timestamps and reasoning
- Provide rollback procedures for destructive operations

**Rationale**: Unexpected service disruptions cause data loss and downtime. Explicit permission prevents accidents.

### VIII. Tactical Revisions

Changes MUST be minimally invasive and follow established patterns.

- Fix the specific problem; do not refactor surrounding code
- Follow existing code conventions in the codebase
- Avoid introducing new patterns unless explicitly approved
- Do not add features, improvements, or "cleanup" beyond the request
- If a pattern seems wrong, discuss before changing

**Rationale**: Scope creep and unsolicited changes introduce risk and delay delivery.

## Code Standards

### Universal Design Principles

All code MUST adhere to these principles regardless of language:

| Principle | Description |
|-----------|-------------|
| **SOLID** | Single responsibility, Open/closed, Liskov substitution, Interface segregation, Dependency inversion |
| **DRY** | Don't Repeat Yourself - extract shared logic to reusable modules |
| **KISS** | Keep It Simple - avoid over-engineering |
| **YAGNI** | You Aren't Gonna Need It - don't build features until required |

### Type Safety

- Use static typing where the language supports it
- Enable strict type checking in tooling
- Validate data at API/system boundaries using schema validation
- Avoid dynamic typing constructs that bypass type checking (e.g., `any`, untyped dictionaries)

### Error Handling

- Fail fast with clear, specific error messages
- No silent failures; all errors MUST be handled or propagated
- Include context in error messages (what failed, why, and what data was involved)
- Validate inputs at API boundaries before processing

### Logging

Use structured logging with appropriate levels:

| Level | Usage |
|-------|-------|
| DEBUG | Detailed diagnostic info (development only) |
| INFO | Normal operations, request handling |
| WARNING | Unexpected but recoverable situations |
| ERROR | Errors requiring attention |
| CRITICAL | System failures requiring immediate action |

### Comments and Documentation

- Comment **why**, not **what** (code should be self-documenting)
- Required comments: complex algorithms, non-obvious logic, workarounds (with ticket reference), public API contracts
- Omit comments for self-explanatory code
- Keep comments up-to-date with code changes

## Repository Structure

### Directory Organization

```
project/
├── apps/          # Deployable applications
├── packages/      # Shared libraries
├── tests/         # Test files (mirrors app structure)
├── docs/          # Architecture, specs, API documentation
├── .docs/         # Session logs, internal documentation
│   ├── sessions/
│   └── deployment-log.md
├── scripts/       # Build and maintenance scripts
├── .cache/        # Temporary files (gitignored)
└── .env.example   # Environment template (tracked)
```

### File Organization Rules

- **Clean root**: No experiments, temp files, or throwaway code at repository root
- **No `src/` directories**: Code lives directly in app/package folders
- **Environment files**: `.env` (gitignored), `.env.example` (tracked)
- **Build artifacts**: All generated files in `.cache/`
- **Single word directories**: Use `api/`, `utils/`, `models/` (not `api-routes/`, `utility-functions/`)

### Git Workflow

- Feature branches → Pull Request → Merge to main
- Descriptive branch names: `feature/add-user-auth`, `fix/login-timeout`
- Atomic commits with clear messages

## Documentation Standards

### Required Documentation

Every project MUST maintain:

| Document | Purpose | Location |
|----------|---------|----------|
| README.md | Project overview, setup, usage | Root, apps/*, packages/* |
| API documentation | Endpoint contracts, schemas | docs/ |
| Session logs | Development reasoning and decisions | .docs/sessions/ |

### Session Logs

Format: `.docs/sessions/YYYY-MM-DD-HH-MM-description.md`

MUST include:
- What was done and why
- Decisions made with reasoning
- Problems encountered and solutions
- Open questions or follow-ups

### Inline Documentation

- Docstrings for all public functions, classes, and modules
- Include parameter descriptions and return types
- Document exceptions/errors that can be raised
- Provide usage examples for complex APIs

## Service Lifecycle

### Resource Verification

Before allocating resources:

1. Verify availability (ports, memory, disk, network)
2. Check for conflicts with existing services
3. Document allocation in service registry

### Deployment Process

1. **Verify prerequisites**: Dependencies, configuration, resources
2. **Request approval**: Confirm with stakeholders before lifecycle changes
3. **Execute change**: Deploy, restart, or shutdown as approved
4. **Verify health**: Confirm service is functioning correctly
5. **Document**: Record change with timestamp and outcome

### Resource Conflicts

- NEVER force-kill existing services to free resources
- If conflict exists, report and await resolution
- Auto-increment to next available resource (e.g., port) when possible

## Development Workflow

### API-First Design

For services with external interfaces:

1. Define contract/schema before implementation
2. Write tests against the contract
3. Implement to satisfy tests
4. Auto-generate documentation from schemas

### Mobile-First UI

For user interfaces:

1. Design for smallest viewport first
2. Use responsive utilities to enhance for larger screens
3. Ensure touch targets meet accessibility standards (44px minimum)
4. Test on actual devices or accurate emulators

### Code Review Requirements

All changes MUST be reviewed before merge:

- Verify adherence to constitution principles
- Ensure tests exist and pass
- Check for security vulnerabilities
- Validate documentation updates

## Governance

### Constitution Authority

This constitution supersedes all other practices, conventions, and preferences. When in conflict, the constitution wins.

### Amendment Process

To amend this constitution:

1. **Propose**: Document the change with rationale
2. **Review**: Stakeholders evaluate impact
3. **Approve**: Explicit approval required
4. **Implement**: Update constitution with version increment
5. **Propagate**: Update dependent templates and documentation

### Version Control

Constitution versioning follows semantic versioning:

- **MAJOR**: Backward-incompatible governance changes, principle removals or redefinitions
- **MINOR**: New principles added, sections materially expanded
- **PATCH**: Clarifications, wording improvements, typo fixes

### Compliance

- All pull requests MUST verify compliance with constitution
- Automated checks SHOULD enforce verifiable principles
- Complexity beyond these guidelines MUST be explicitly justified

**Version**: 1.0.0 | **Ratified**: 2026-01-06 | **Last Amended**: 2026-01-06
