# ProjectLens Shared

Shared models, schemas, DTOs, constants, and types used across the ProjectLens AI platform.

## Overview

This package provides the canonical data contracts for the ProjectLens ecosystem:

- **Models** — Core domain entities (Document, Message, Conversation, User, AnalysisResult, etc.)
- **Schemas** — API request/response schemas for create, update, and response operations
- **DTOs** — Data transfer objects for filtering, sorting, pagination, and context passing
- **Constants** — Enumerations for roles, statuses, event types, and system limits
- **Types** — Shared type aliases and generic type utilities

## Installation

```bash
pip install projectlens-shared
```

For development:

```bash
pip install -e ".[dev]"
```
