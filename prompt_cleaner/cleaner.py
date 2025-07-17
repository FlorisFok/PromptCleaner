from typing import Dict, Any, List, Optional
import openai
from .utils import process_messages


class PromptCleanerClient:
    """Wrapper for OpenAI client that automatically cleans UUIDs from messages."""
    
    def __init__(self, client: openai.OpenAI, sep: str = "[", nr_digits: int = 2):
        """
        Initialize the prompt cleaner client.
        
        Args:
            client: OpenAI client instance
            sep: Separator character for UUID pattern ('[', '(', '{', '<')
            nr_digits: Number of digits for replacement (2 for 00-99, 3 for 000-999)
        """
        self._client = client
        self.sep = sep
        self.nr_digits = nr_digits
        self.uuid_mappings: Dict[str, str] = {}
    
    def _process_chat_completion_kwargs(self, **kwargs) -> Dict[str, Any]:
        """Process chat completion arguments to clean UUIDs from messages."""
        processed_kwargs = kwargs.copy()
        
        if 'messages' in kwargs:
            processed_messages, mappings = process_messages(
                kwargs['messages'], 
                sep=self.sep, 
                nr_digits=self.nr_digits
            )
            processed_kwargs['messages'] = processed_messages
            self.uuid_mappings.update(mappings)
        
        return processed_kwargs
    
    @property
    def chat(self):
        """Access to chat completions with UUID cleaning."""
        return ChatCompletionsWrapper(self)
    
    def __getattr__(self, name):
        """Delegate other attributes to the wrapped client."""
        return getattr(self._client, name)


class ChatCompletionsWrapper:
    """Wrapper for chat completions that processes messages."""
    
    def __init__(self, cleaner_client: PromptCleanerClient):
        self.cleaner_client = cleaner_client
        self._completions = cleaner_client._client.chat.completions
    
    @property
    def completions(self):
        """Access to completions with UUID cleaning."""
        return CompletionsWrapper(self.cleaner_client)
    
    def __getattr__(self, name):
        """Delegate other attributes to the wrapped completions."""
        return getattr(self._completions, name)


class CompletionsWrapper:
    """Wrapper for completions that processes create method."""
    
    def __init__(self, cleaner_client: PromptCleanerClient):
        self.cleaner_client = cleaner_client
        self._completions = cleaner_client._client.chat.completions
    
    def create(self, **kwargs):
        """Create chat completion with UUID cleaning."""
        processed_kwargs = self.cleaner_client._process_chat_completion_kwargs(**kwargs)
        return self._completions.create(**processed_kwargs)
    
    def __getattr__(self, name):
        """Delegate other attributes to the wrapped completions."""
        return getattr(self._completions, name)


class prompt_cleaner:
    """Context manager for OpenAI client with UUID cleaning."""
    
    def __init__(self, client: openai.OpenAI, sep: str = "[", nr_digits: int = 2):
        """
        Initialize the prompt cleaner context manager.
        
        Args:
            client: OpenAI client instance
            sep: Separator character for UUID pattern ('[', '(', '{', '<')
            nr_digits: Number of digits for replacement (2 for 00-99, 3 for 000-999)
        
        Example:
            with prompt_cleaner(openai.OpenAI(), sep="[", nr_digits=3) as client:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello [550e8400-e29b-41d4-a716-446655440000]"}]
                )
        """
        self.original_client = client
        self.sep = sep
        self.nr_digits = nr_digits
        self.cleaner_client: Optional[PromptCleanerClient] = None
    
    def __enter__(self) -> PromptCleanerClient:
        """Enter the context manager and return the wrapped client."""
        self.cleaner_client = PromptCleanerClient(
            self.original_client, 
            sep=self.sep, 
            nr_digits=self.nr_digits
        )
        return self.cleaner_client
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        # Could add cleanup logic here if needed
        pass
    
    def get_uuid_mappings(self) -> Dict[str, str]:
        """Get the UUID mappings from the last context manager session."""
        if self.cleaner_client:
            return self.cleaner_client.uuid_mappings.copy()
        return {}

