from abc import ABC, abstractmethod
from typing import Any, Dict


class Tool(ABC):
    """Base class for all tools"""

    name: str
    description: str
    parameters: Dict[str, Any] = {}

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary for LLM"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
