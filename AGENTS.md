# Invoice extraction repository instructions

## Architecture

Keep each feature under `src/modules/<feature>/` with `domain/`, `application/`, `adapters/`, and `config/` packages. Domain code must not import FastAPI, SQLAlchemy, LangChain, LangGraph, or other adapters. Application use cases depend on ports and domain contracts. Adapters implement ports; `config/module.py` composes them. Keep file upload and extraction lifecycles separate.

The blueprint `Invoice_Bill_Receipt_Extraction_Architecture_Blueprint.md` is the design baseline. Preserve the Image → DOCX → PDF reader order, source evidence, Decimal-safe validation, and explicit uncertain/review states. Do not fabricate missing financial values.

## Graphify

Graphify skill is installed at `~/.codex/skills/graphify/SKILL.md`. The code graph is in `graphify-out/`. For codebase questions, query the graph first with `graphify query "<question>"`; use `graphify path` or `graphify explain` for relationships. After code changes, run `graphify update .` to refresh the AST graph. The generated graph is a navigation aid, not a substitute for reading source or running tests.

## Verification

Run `docker compose run --rm --no-deps api python -m unittest discover -s tests -q` for the current suite. Run `docker compose config --quiet` after Compose changes. Do not expose the API publicly until authentication and ownership checks are implemented.
