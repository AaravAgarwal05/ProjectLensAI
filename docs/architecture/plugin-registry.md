# Plugin Registry Pattern

The plugin registry pattern is a foundational design choice in ProjectLens AI. It enables the AI layer to support multiple providers (OpenAI, Claude, Ollama, etc.) without hardcoding dependencies or maintaining lengthy if-else chains.

---

## Problem

Applications that integrate multiple AI providers often end up with code like:

```python
def embed(text: str, provider: str):
    if provider == "openai":
        return openai_embed(text)
    elif provider == "claude":
        return claude_embed(text)
    elif provider == "ollama":
        return ollama_embed(text)
    else:
        raise ValueError(f"Unknown provider: {provider}")
```

This approach does not scale. Every new provider requires modifying existing functions, and testing all branches becomes cumbersome.

---

## Solution: Registry Pattern

The registry pattern inverts the control: plugins register themselves with a central registry, and consumers query the registry by name.

```python
class EmbeddingProvider(ABC):
    """Abstract base for all embedding providers."""

    @abstractmethod
    def embed(self, text: str) -> list[float]: ...


class EmbeddingRegistry:
    """Registry of named embedding providers."""

    def __init__(self):
        self._providers: dict[str, type[EmbeddingProvider]] = {}

    def register(self, name: str, provider: type[EmbeddingProvider]):
        self._providers[name] = provider

    def get(self, name: str) -> EmbeddingProvider:
        cls = self._providers.get(name)
        if cls is None:
            raise KeyError(f"Unknown embedding provider: {name}")
        return cls()  # Lazy instantiation
```

---

## How It Works

### 1. Registration

Each provider plugin registers itself with the registry at import time or during application startup:

```python
class OpenAIEmbeddingProvider(EmbeddingProvider):
    def embed(self, text: str) -> list[float]:
        # OpenAI-specific implementation
        ...

# Register on import
EmbeddingRegistry.instance().register("openai", OpenAIEmbeddingProvider)
```

### 2. Lazy Instantiation

The registry does not create instances until they are requested. This keeps startup fast and avoids allocating resources for providers that may never be used.

### 3. Retrieval

Consumers retrieve a provider by name with a single line of code:

```python
provider = EmbeddingRegistry.instance().get("openai")
embeddings = provider.embed("Hello, world!")
```

Adding support for a new provider requires only writing a new plugin class and registering it — no existing code changes.

---

## Provider Registry vs. Plugin Registry

ProjectLens AI uses two distinct registries:

| Registry | Purpose | Example Entries |
|----------|---------|-----------------|
| **Provider Registry** | AI provider implementations | OpenAI, Claude, Ollama |
| **Plugin Registry** | Extensible application plugins | Custom analyzers, export formats |

The Provider Registry is a specific application of the broader Plugin Registry pattern. The Plugin Registry is generic and can be used for any extension point in the system (e.g., document parsers, output formatters, analysis modules).

---

## Benefits

- **No if-else chains** — Provider selection is a dictionary lookup, not a conditional tree.
- **Extensible** — Adding a new provider means writing a single class and a registration call. No existing files are modified.
- **Testable** — Providers are isolated behind interfaces. Tests can swap real providers with mocks via the registry.
- **Configuration-driven** — The active provider can be selected via configuration without code changes.
