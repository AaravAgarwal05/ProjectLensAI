"""Prompt templates and prompt management."""

from typing import Any


class PromptTemplate:
    """A reusable prompt template with named placeholders.

    Placeholders are expressed as ``{placeholder_name}`` in the template
    string and filled via ``format()``.
    """

    def __init__(self, template: str, name: str = "") -> None:
        self.template = template
        self.name = name

    def format(self, **kwargs: Any) -> str:
        """Fill template placeholders with the provided values.

        Args:
            **kwargs: Values for each placeholder in the template.

        Returns:
            The fully rendered prompt string.

        Raises:
            KeyError: If a placeholder in the template is missing from kwargs.
        """
        return self.template.format(**kwargs)


class PromptManager:
    """Manages a collection of named PromptTemplates.

    Provides convenient CRUD access so that prompts can be loaded from
    configuration or files and retrieved by name at runtime.
    """

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}

    def add(self, name: str, template: str) -> PromptTemplate:
        """Register a new template.

        Args:
            name: Unique identifier for the template.
            template: The template string with ``{placeholders}``.

        Returns:
            The newly created PromptTemplate instance.
        """
        pt = PromptTemplate(template=template, name=name)
        self._templates[name] = pt
        return pt

    def get(self, name: str) -> PromptTemplate:
        """Retrieve a registered template by name.

        Raises:
            KeyError: If no template with that name exists.
        """
        if name not in self._templates:
            msg = f"Unknown prompt template: '{name}'"
            raise KeyError(msg)
        return self._templates[name]

    def remove(self, name: str) -> None:
        """Unregister a template."""
        self._templates.pop(name, None)

    @property
    def available(self) -> list[str]:
        """List of registered template names."""
        return list(self._templates)
