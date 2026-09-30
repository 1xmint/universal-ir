# Repository guidance

## Current state

This repository contains documentation and one conceptual example. There is no executable API, compiler, or runtime. Read README.md and ROADMAP.md before changing the project.

## Working rules

- Explain ideas in simple words; define technical terms when needed.
- Make small, focused changes and keep the README, architecture, example, and roadmap consistent.
- Clearly distinguish proposed behavior, accepted design decisions, and implemented features.
- Keep the program representation as the intended source of truth for generated artifacts.
- Treat token efficiency as a hypothesis to measure over complete, correctly finished tasks.
- Record material design choices and their tradeoffs in the relevant document.
- Update roadmap checkboxes when their completion conditions are actually met.
- Introduce source directories, build tooling, and CI with executable code; avoid empty scaffolding.
- For documentation changes, verify local links and Markdown rendering.
- For functional changes, run relevant behavior and failure checks. Permission checks must cover requests that bypass the interface.

The implementation language and final encoding remain decisions for milestone 1. Do not introduce executable syntax in the conceptual example.
