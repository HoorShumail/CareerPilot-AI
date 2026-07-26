from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

class LLMProvider(ABC):
    """Abstract base class for LLM providers to ensure easy swapping of models."""
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate a raw string response."""
        pass

    @abstractmethod
    async def generate_with_metadata(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """Generate a raw string response with metadata (finish_reason, model, token usage)."""
        pass
        
    @abstractmethod
    async def generate_structured(self, prompt: str, response_schema: Any, system_prompt: Optional[str] = None, **kwargs) -> Any:
        """Generate a response matching a Pydantic schema."""
        pass
        
    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of strings."""
        pass
