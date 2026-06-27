"""Prompt management using Jinja2 templates."""

import os
from pathlib import Path
from typing import Any
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

class PromptManager:
    """Loads and renders prompt templates from the filesystem."""
    
    def __init__(self, templates_dir: str = "app/prompts"):
        # Resolve path relative to the project root
        self.templates_dir = Path(templates_dir).resolve()
        
        # Ensure directory exists, but don't fail if it doesn't during init
        if not self.templates_dir.exists():
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=False,  # Prompts are plain text, no HTML escaping needed
            trim_blocks=True,
            lstrip_blocks=True
        )
        
    def render(self, template_name: str, **variables: Any) -> str:
        """Render a Jinja2 template with the given variables.
        
        Args:
            template_name: The name of the template file (e.g., 'planner_system.jinja2')
            **variables: Keyword arguments to pass into the template.
            
        Returns:
            The rendered string prompt.
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**variables)
        except TemplateNotFound:
            raise FileNotFoundError(f"Prompt template '{template_name}' not found in {self.templates_dir}")
