import pytest
from unittest.mock import Mock, MagicMock
import openai
from prompt_cleaner.cleaner import prompt_cleaner, PromptCleanerClient, ChatCompletionsWrapper, CompletionsWrapper


class TestPromptCleanerClient:
    """Test cases for PromptCleanerClient class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=openai.OpenAI)
        self.mock_completions = Mock()
        self.mock_client.chat.completions = self.mock_completions
        
    def test_init(self):
        """Test PromptCleanerClient initialization."""
        client = PromptCleanerClient(self.mock_client, sep="(", nr_digits=3)
        
        assert client._client == self.mock_client
        assert client.sep == "("
        assert client.nr_digits == 3
        assert client.uuid_mappings == {}
    
    def test_process_chat_completion_kwargs_with_uuids(self):
        """Test processing of chat completion kwargs with UUIDs."""
        client = PromptCleanerClient(self.mock_client, sep="[", nr_digits=2)
        
        kwargs = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Hello [550e8400-e29b-41d4-a716-446655440000]"}
            ],
            "temperature": 0.7
        }
        
        result = client._process_chat_completion_kwargs(**kwargs)
        
        assert result["model"] == "gpt-3.5-turbo"
        assert result["temperature"] == 0.7
        assert result["messages"][0]["content"] == "Hello [00]"
        assert "550e8400-e29b-41d4-a716-446655440000" in client.uuid_mappings
    
    def test_process_chat_completion_kwargs_no_messages(self):
        """Test processing kwargs without messages."""
        client = PromptCleanerClient(self.mock_client)
        
        kwargs = {"model": "gpt-3.5-turbo", "temperature": 0.7}
        result = client._process_chat_completion_kwargs(**kwargs)
        
        assert result == kwargs
        assert client.uuid_mappings == {}
    
    def test_chat_property(self):
        """Test chat property returns ChatCompletionsWrapper."""
        client = PromptCleanerClient(self.mock_client)
        chat = client.chat
        
        assert isinstance(chat, ChatCompletionsWrapper)
        assert chat.cleaner_client == client
    
    def test_getattr_delegation(self):
        """Test attribute delegation to wrapped client."""
        self.mock_client.some_attribute = "test_value"
        client = PromptCleanerClient(self.mock_client)
        
        assert client.some_attribute == "test_value"


class TestChatCompletionsWrapper:
    """Test cases for ChatCompletionsWrapper class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=openai.OpenAI)
        self.mock_completions = Mock()
        self.mock_client.chat.completions = self.mock_completions
        self.cleaner_client = PromptCleanerClient(self.mock_client)
        
    def test_init(self):
        """Test ChatCompletionsWrapper initialization."""
        wrapper = ChatCompletionsWrapper(self.cleaner_client)
        
        assert wrapper.cleaner_client == self.cleaner_client
        assert wrapper._completions == self.mock_completions
    
    def test_completions_property(self):
        """Test completions property returns CompletionsWrapper."""
        wrapper = ChatCompletionsWrapper(self.cleaner_client)
        completions = wrapper.completions
        
        assert isinstance(completions, CompletionsWrapper)
        assert completions.cleaner_client == self.cleaner_client
    
    def test_getattr_delegation(self):
        """Test attribute delegation to wrapped completions."""
        self.mock_completions.some_method = Mock(return_value="test_result")
        wrapper = ChatCompletionsWrapper(self.cleaner_client)
        
        result = wrapper.some_method()
        assert result == "test_result"
        self.mock_completions.some_method.assert_called_once()


class TestCompletionsWrapper:
    """Test cases for CompletionsWrapper class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=openai.OpenAI)
        self.mock_completions = Mock()
        self.mock_client.chat.completions = self.mock_completions
        self.cleaner_client = PromptCleanerClient(self.mock_client)
        
    def test_init(self):
        """Test CompletionsWrapper initialization."""
        wrapper = CompletionsWrapper(self.cleaner_client)
        
        assert wrapper.cleaner_client == self.cleaner_client
        assert wrapper._completions == self.mock_completions
    
    def test_create_with_uuid_cleaning(self):
        """Test create method with UUID cleaning."""
        mock_response = Mock()
        self.mock_completions.create.return_value = mock_response
        
        wrapper = CompletionsWrapper(self.cleaner_client)
        
        kwargs = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Hello [550e8400-e29b-41d4-a716-446655440000]"}
            ]
        }
        
        result = wrapper.create(**kwargs)
        
        # Check that the mock was called with processed messages
        call_args = self.mock_completions.create.call_args[1]
        assert call_args["model"] == "gpt-3.5-turbo"
        assert call_args["messages"][0]["content"] == "Hello [00]"
        assert result == mock_response
    
    def test_getattr_delegation(self):
        """Test attribute delegation to wrapped completions."""
        self.mock_completions.some_attribute = "test_value"
        wrapper = CompletionsWrapper(self.cleaner_client)
        
        assert wrapper.some_attribute == "test_value"


class TestPromptCleaner:
    """Test cases for prompt_cleaner context manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=openai.OpenAI)
        self.mock_completions = Mock()
        self.mock_client.chat.completions = self.mock_completions
        
    def test_init(self):
        """Test prompt_cleaner initialization."""
        cleaner = prompt_cleaner(self.mock_client, sep="(", nr_digits=3)
        
        assert cleaner.original_client == self.mock_client
        assert cleaner.sep == "("
        assert cleaner.nr_digits == 3
        assert cleaner.cleaner_client is None
    
    def test_context_manager_enter_exit(self):
        """Test context manager enter and exit."""
        cleaner = prompt_cleaner(self.mock_client, sep="[", nr_digits=2)
        
        with cleaner as client:
            assert isinstance(client, PromptCleanerClient)
            assert client._client == self.mock_client
            assert client.sep == "["
            assert client.nr_digits == 2
            assert cleaner.cleaner_client == client
        
        # After exit, cleaner_client should still be accessible
        assert cleaner.cleaner_client is not None
    
    def test_get_uuid_mappings_with_client(self):
        """Test getting UUID mappings after using context manager."""
        cleaner = prompt_cleaner(self.mock_client)
        
        with cleaner as client:
            # Simulate processing some messages
            client.uuid_mappings["550e8400-e29b-41d4-a716-446655440000"] = "00"
        
        mappings = cleaner.get_uuid_mappings()
        assert mappings == {"550e8400-e29b-41d4-a716-446655440000": "00"}
    
    def test_get_uuid_mappings_without_client(self):
        """Test getting UUID mappings before using context manager."""
        cleaner = prompt_cleaner(self.mock_client)
        mappings = cleaner.get_uuid_mappings()
        assert mappings == {}


class TestIntegration:
    """Integration tests for the complete workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=openai.OpenAI)
        self.mock_response = Mock()
        self.mock_response.choices = [Mock()]
        self.mock_response.choices[0].message.content = "Hello there!"
        
        # Set up the mock chain
        self.mock_completions = Mock()
        self.mock_completions.create.return_value = self.mock_response
        self.mock_client.chat.completions = self.mock_completions
    
    def test_full_workflow_with_context_manager(self):
        """Test the complete workflow using context manager."""
        messages = [
            {"role": "user", "content": "Hello [550e8400-e29b-41d4-a716-446655440000] and [6ba7b810-9dad-11d1-80b4-00c04fd430c8]"}
        ]
        
        with prompt_cleaner(self.mock_client, sep="[", nr_digits=2) as client:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
        
        # Verify the mock was called with processed messages
        call_args = self.mock_completions.create.call_args[1]
        assert call_args["model"] == "gpt-3.5-turbo"
        assert call_args["messages"][0]["content"] == "Hello [00] and [01]"
        
        # Verify response is returned correctly
        assert response == self.mock_response
    
    def test_different_separators_and_digits(self):
        """Test with different separator and digit configurations."""
        test_cases = [
            ("(", ")", 3, "Hello (550e8400-e29b-41d4-a716-446655440000)", "Hello (000)"),
            ("{", "}", 4, "Hello {550e8400-e29b-41d4-a716-446655440000}", "Hello {0000}"),
            ("<", ">", 1, "Hello <550e8400-e29b-41d4-a716-446655440000>", "Hello <0>")
        ]
        
        for open_sep, close_sep, digits, input_content, expected_content in test_cases:
            messages = [{"role": "user", "content": input_content}]
            
            with prompt_cleaner(self.mock_client, sep=open_sep, nr_digits=digits) as client:
                client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
            
            call_args = self.mock_completions.create.call_args[1]
            assert call_args["messages"][0]["content"] == expected_content
    
    def test_uuid_mapping_persistence(self):
        """Test that UUID mappings are preserved across calls."""
        cleaner = prompt_cleaner(self.mock_client, sep="[", nr_digits=2)
        
        with cleaner as client:
            # First call
            messages1 = [{"role": "user", "content": "Hello [550e8400-e29b-41d4-a716-446655440000]"}]
            client.chat.completions.create(model="gpt-3.5-turbo", messages=messages1)
            
            # Second call with same UUID
            messages2 = [{"role": "user", "content": "Again [550e8400-e29b-41d4-a716-446655440000]"}]
            client.chat.completions.create(model="gpt-3.5-turbo", messages=messages2)
        
        # Both calls should use the same replacement
        calls = self.mock_completions.create.call_args_list
        assert calls[0][1]["messages"][0]["content"] == "Hello [00]"
        assert calls[1][1]["messages"][0]["content"] == "Again [00]"
        
        # Check mappings
        mappings = cleaner.get_uuid_mappings()
        assert mappings["550e8400-e29b-41d4-a716-446655440000"] == "00"

