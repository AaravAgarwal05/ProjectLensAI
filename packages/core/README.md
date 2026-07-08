# ProjectLens Core

Foundational package for the ProjectLens AI platform. Provides base abstractions,
configuration management, event bus, plugin/provider registries, logging, and
utility components used by all higher-level packages.

## Installation

```bash
pip install projectlens-core
```

## Features

- **Interfaces**: Abstract base classes for providers, repositories, services, plugins, and workflows
- **Configuration**: Pydantic-settings based config management with env loading
- **Registry**: Plugin and provider registries with lazy instantiation
- **Events**: Thread-safe event bus with async handler support
- **Logging**: Structured logging with configurable output formats
- **Exceptions**: Rich exception hierarchy for fine-grained error handling
- **Utilities**: Singleton pattern, string helpers, deep merge
