# 0010 · No monorepo tooling

**Status:** ✅ Accepted · **Date:** 2026-09-06

---

## Context

The repository holds four independent roots — `architecture/`, `frontend/`, `backend/`, `infra/` —
which fits the usual description of a monorepo. The reflex is to reach for Turborepo, Nx or pnpm
workspaces.

But the two applications are in **different languages**. They share no JavaScript dependencies, no
build graph, and no compilation step in common. What they share is JSON Schemas, and those are
consumed by two separate generators.

## Decision

**No monorepo tooling.** A root `Makefile` coordinates everything.

```makefile
make setup · make dev · make gen · make lint · make test · make build · make deploy
```

CI calls the same targets, so local and CI behaviour can't diverge.

## Consequences

### What this makes easier

- Zero configuration to learn, debug or keep current
- `make` is already installed everywhere and will still work in ten years
- Works identically for Python and TypeScript, which JS-ecosystem tools don't
- CI and local development run literally the same commands
- One less dependency in a project that already has plenty

### What this makes harder — the cost we're accepting

- No incremental or cached builds — but full builds here take seconds, not minutes
- No dependency graph, so build ordering is expressed manually in the Makefile
- Makefile syntax is its own small annoyance, tabs included
- If a third or fourth JS package appeared, this would need revisiting

## Alternatives considered

### Turborepo
Excellent caching and task orchestration. Rejected: it orchestrates JS packages, and half this repo
isn't JS. Configuration cost with no return at this size.

### pnpm workspaces
Useful for sharing JS dependencies between packages. There's exactly one JS package here.

### Nx
Considerably more powerful and considerably more machinery. Wrong scale entirely.

## Revisit if

- A second JavaScript package appears (a shared UI library, a CLI)
- Build times get long enough that caching would actually be noticeable
