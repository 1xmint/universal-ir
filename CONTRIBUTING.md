# Contributing

Universal IR currently contains documentation and a worked example. Start with the [README](README.md), [architecture](docs/architecture.md), and [roadmap](ROADMAP.md).

## Propose a change

Open an issue describing the problem, the desired behavior, and a concrete example. For changes to the program format or architecture, discuss the proposal before building a large implementation.

Keep pull requests focused on one coherent change. Explain what changed, why, and how it was checked. Update related documentation and examples together.

## Record design decisions

For now, record accepted architecture decisions in the relevant document. Include the decision, its reason, important tradeoffs, and unresolved questions. Keep proposals visibly separate from accepted decisions and implemented behavior.

The implementation language and final encoding will be chosen in milestone 1. Executable code, source directories, build tooling, and CI belong to the implementation milestones.

## Provide evidence

For documentation changes, check relative links, rendered Markdown, and consistency with the roadmap and example.

For future behavior changes, include checks for the intended behavior and relevant failure cases. Permission changes must be tested through trusted execution boundaries, including requests that bypass the interface.

For efficiency claims, report the complete task: model and tool configuration, acceptance criteria, context and generation tokens, checking and repair costs, latency, and review effort. Include failed attempts and enough detail to reproduce the comparison.

Mark a roadmap milestone complete only when its completion conditions are met. Do not describe proposed features as working features.

## License

Contributions are provided under the repository's [MIT license](LICENSE).
