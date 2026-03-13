# Architectural Guide

## Objective

This project should grow through explicit layers, small contracts, and low-coupling flows.
New code must favor maintainability, predictable tests, and incremental evolution without forcing broad rewrites.

## Core Principles

- Keep responsibilities narrow and obvious.
- Prefer composition over large multipurpose modules.
- Keep business flow independent from CLI and infrastructure details.
- Make data contracts explicit.
- Optimize for testability before cleverness.
- Preserve backward-compatible behavior when refactoring public flows.

## Layer Model

### Domain

The domain layer defines semantic concepts and failures.

- Store domain errors and domain-level concepts here.
- Domain types should describe intent, not infrastructure.
- Domain code must not depend on CLI, terminal rendering, Docker, subprocesses, or filesystem APIs.
- If a rule is meaningful even if the transport changes, it belongs closer to the domain.

### Services

The service layer handles focused operational capabilities.

- Each service module should represent a single context.
- Service functions may talk to infrastructure when that is their job.
- Keep service functions small and cohesive.
- Avoid mixing unrelated concerns such as filesystem manipulation, status calculation, and container orchestration in the same function.
- Extract pure helpers from IO-heavy functions whenever possible.

### Application

The application layer orchestrates use cases.

- Use application functions to compose service calls into complete flows.
- Application code should be the default place for command workflows, read models, and coordination logic.
- Application should define clear inputs and outputs for each use case.
- Prefer DTOs over free-form dictionaries for values crossing layer boundaries.
- Application is allowed to depend on domain and services, but not on CLI rendering details.

### Interface / CLI

The CLI is an adapter layer.

- It should parse input, call application use cases, and render output.
- Do not place business decisions or infrastructure orchestration in CLI commands.
- Error translation to user-facing messages belongs here.
- Keep commands thin and predictable.

## Module Organization Rules

- Organize code by context, not by technical accident.
- Prefer folders that make intent visible, such as domain, services, and application.
- Add a new module only when it creates a clearer boundary, not just to reduce line count.
- Avoid monolithic modules that accumulate every workflow.
- Keep public facades stable when internal reorganization is needed.

## Dependency Direction

Dependencies should flow inward toward more stable rules.

- Interface may depend on application.
- Application may depend on domain and services.
- Services may depend on domain.
- Domain should not depend outward.
- Avoid circular imports by keeping contracts explicit and contexts separated.

## Data Contracts

- Use DTOs for values returned by application use cases.
- DTOs should be small, explicit, and immutable when practical.
- Do not pass loosely shaped dictionaries between layers unless there is a strong reason.
- When adding fields to a contract, do so intentionally and update tests with the new contract shape.

## Error Handling

- Prefer semantic exceptions over generic exceptions.
- Raise errors at the layer where the failure becomes meaningful.
- Convert infrastructure failures into domain-meaningful or application-meaningful errors as early as practical.
- User-facing formatting of errors belongs in the interface layer.
- Preserve compatibility when replacing older generic failures with more specific ones.

## Testing Strategy

### Unit Tests

- Pure helpers must have direct unit tests.
- Status calculation, parsing, transformation, and aggregation logic should be tested without infrastructure.
- DTO-producing application functions should have contract-focused tests.

### Service Tests

- Service tests should isolate external dependencies through mocks or fakes.
- Filesystem, subprocess, container runtime, and environment access should be replaceable in tests.
- Test service behavior at the seam where infrastructure is invoked.

### CLI Tests

- CLI tests should validate parsing, exit codes, and visible output.
- Mock application use cases instead of mocking deep infrastructure whenever possible.
- Keep CLI tests focused on adapter behavior, not internal orchestration.

### Refactoring Safety

- Add characterization tests before changing behavior in legacy flows.
- Prefer incremental refactors with passing tests between each step.
- If a refactor changes only structure, keep public behavior unchanged.

## Side Effects and State

- Avoid side effects at import time.
- Create external clients lazily.
- Keep global state minimal and deliberate.
- Make environment lookups explicit in the functions that need them, or centralize them behind clear seams.
- Read-only operations should not create or mutate resources unless explicitly documented.

## Function Design Rules

- Functions should do one thing at one level of abstraction.
- If a function mixes validation, IO, formatting, and orchestration, split it.
- Prefer returning structured values over preformatted text.
- Keep formatting logic near the interface layer.
- Name functions by intent, not implementation detail.

## Scalability Guidelines

- When a context grows, split by use case or capability, not arbitrarily.
- Promote repeated orchestration into application use cases.
- Promote repeated transformations into pure helpers or DTO factories.
- Introduce new abstractions only when they reduce complexity or duplication across more than one flow.
- Avoid speculative architecture; prefer structure that solves a current maintenance problem cleanly.

## Refactoring Rules

- Keep refactors incremental.
- Preserve external behavior unless the change is intentional and tested.
- Maintain compatibility facades when reorganizing internal modules.
- Remove deprecated internal paths only after all callers are migrated.
- Do not combine behavior changes with broad structural moves unless necessary.

## Review Checklist For New Code

- Is the responsibility of this code obvious?
- Does this belong in domain, service, application, or interface?
- Is any infrastructure concern leaking into orchestration or presentation?
- Is the return type explicit and stable?
- Can this be tested without real external dependencies?
- Does this add a new abstraction only where it pays for itself?
- Does this preserve the direction of dependencies?
- Does this keep the project easier to extend than before?
