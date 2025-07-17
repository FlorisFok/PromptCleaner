# Prompt Cleaner

A Python package that wraps the OpenAI client to automatically replace UUIDs in messages with sequential digits, making prompts cleaner and more readable.

## Features

- **Automatic UUID Detection**: Finds UUIDs wrapped in configurable separators (`[`, `(`, `{`, `<`)
- **Sequential Replacement**: Replaces UUIDs with sequential digits (00-99, 000-999, etc.)
- **Context Manager**: Easy-to-use context manager interface
- **Consistent Mapping**: Same UUID always gets the same replacement within a session
- **OpenAI Compatible**: Drop-in replacement for OpenAI client
- **Configurable**: Customizable separators and digit count

## Installation

```bash
pip install prompt-cleaner
```

For development:

```bash
git clone <repository-url>
cd prompt-cleaner
pip install -e .[dev]
```

## Quick Start

### Context Manager (Recommended)

```python
import openai
from prompt_cleaner import prompt_cleaner

# Initialize OpenAI client
client = openai.OpenAI(api_key="your-api-key")

# Use prompt_cleaner as a context manager
with prompt_cleaner(client, sep="[", nr_digits=3) as clean_client:
    response = clean_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user", 
                "content": "Process user [550e8400-e29b-41d4-a716-446655440000] and item [6ba7b810-9dad-11d1-80b4-00c04fd430c8]"
            }
        ]
    )
```

The message sent to OpenAI will be:
```
"Process user [000] and item [001]"
```

### Non-Wrapped Functions

```python
from prompt_cleaner import clean_prompt, restore_output

# Clean the prompt
prompt = "Process user [550e8400-e29b-41d4-a716-446655440000]"
cleaned_prompt, mapping = clean_prompt(prompt, sep="[", nr_digits=3)
# cleaned_prompt: "Process user [000]"
# mapping: {"550e8400-e29b-41d4-a716-446655440000": "000"}

# ... do your processing with cleaned_prompt ...
# For example, send to OpenAI API manually
response_content = "User [000] has been processed successfully"

# Restore the original UUIDs in the output
restored_output = restore_output(response_content, mapping, sep="[", nr_digits=3)
# restored_output: "User [550e8400-e29b-41d4-a716-446655440000] has been processed successfully"
```

## Usage Examples

### Basic Usage with Different Separators

```python
import openai
from prompt_cleaner import prompt_cleaner

client = openai.OpenAI()

# Using square brackets with 2 digits
with prompt_cleaner(client, sep="[", nr_digits=2) as clean_client:
    messages = [{"role": "user", "content": "Hello [550e8400-e29b-41d4-a716-446655440000]"}]
    response = clean_client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
    # Sends: "Hello [00]"

# Using parentheses with 3 digits  
with prompt_cleaner(client, sep="(", nr_digits=3) as clean_client:
    messages = [{"role": "user", "content": "User (550e8400-e29b-41d4-a716-446655440000) logged in"}]
    response = clean_client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
    # Sends: "User (000) logged in"

# Using curly braces
with prompt_cleaner(client, sep="{", nr_digits=2) as clean_client:
    messages = [{"role": "user", "content": "Item {550e8400-e29b-41d4-a716-446655440000} processed"}]
    response = clean_client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
    # Sends: "Item {00} processed"
```

### Multiple UUIDs and Consistency

```python
with prompt_cleaner(client, sep="[", nr_digits=2) as clean_client:
    messages = [
        {
            "role": "user", 
            "content": "User [550e8400-e29b-41d4-a716-446655440000] created order [6ba7b810-9dad-11d1-80b4-00c04fd430c8]"
        },
        {
            "role": "assistant", 
            "content": "Order created successfully"
        },
        {
            "role": "user", 
            "content": "Update user [550e8400-e29b-41d4-a716-446655440000] status"
        }
    ]
    
    response = clean_client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
    
    # First message becomes: "User [00] created order [01]"
    # Third message becomes: "Update user [00] status" (same UUID, same replacement)
```

### Accessing UUID Mappings

```python
cleaner = prompt_cleaner(client, sep="[", nr_digits=2)

with cleaner as clean_client:
    messages = [{"role": "user", "content": "Process [550e8400-e29b-41d4-a716-446655440000]"}]
    response = clean_client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)

# Get the UUID mappings after the context
mappings = cleaner.get_uuid_mappings()
print(mappings)
# Output: {'550e8400-e29b-41d4-a716-446655440000': '00'}
```

### Non-Wrapped Function Examples

```python
from prompt_cleaner import clean_prompt, restore_output

# Example 1: Basic usage
prompt = "Hello [550e8400-e29b-41d4-a716-446655440000] world"
cleaned, mapping = clean_prompt(prompt, sep="[", nr_digits=2)
print(f"Cleaned: {cleaned}")  # "Hello [00] world"
print(f"Mapping: {mapping}")  # {"550e8400-e29b-41d4-a716-446655440000": "00"}

# Process with your own logic (e.g., manual API call)
response_text = "Response for [00]"

# Restore UUIDs
restored = restore_output(response_text, mapping, sep="[", nr_digits=2)
print(f"Restored: {restored}")  # "Response for [550e8400-e29b-41d4-a716-446655440000]"

# Example 2: Multiple UUIDs with different separators
prompt = "User (550e8400-e29b-41d4-a716-446655440000) has order (6ba7b810-9dad-11d1-80b4-00c04fd430c8)"
cleaned, mapping = clean_prompt(prompt, sep="(", nr_digits=3)
print(f"Cleaned: {cleaned}")  # "User (000) has order (001)"

# Simulate processing
ai_response = "Processed (000) and (001) successfully"
restored = restore_output(ai_response, mapping, sep="(", nr_digits=3)
print(f"Restored: {restored}")  # "Processed (550e8400-e29b-41d4-a716-446655440000) and (6ba7b810-9dad-11d1-80b4-00c04fd430c8) successfully"

# Example 3: Integration with manual OpenAI API calls
import openai

client = openai.OpenAI()
prompt = "Analyze user {550e8400-e29b-41d4-a716-446655440000} behavior"

# Clean the prompt
cleaned_prompt, mapping = clean_prompt(prompt, sep="{", nr_digits=2)

# Manual API call with cleaned prompt
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": cleaned_prompt}]
)

# Get the response content
response_content = response.choices[0].message.content

# Restore UUIDs in the response
final_response = restore_output(response_content, mapping, sep="{", nr_digits=2)
print(final_response)
```

## API Reference

### `prompt_cleaner(client, sep="[", nr_digits=2)`

Context manager that wraps an OpenAI client to automatically clean UUIDs from messages.

**Parameters:**
- `client` (openai.OpenAI): The OpenAI client instance to wrap
- `sep` (str, optional): Separator character for UUID detection. Supports `[`, `(`, `{`, `<`. Default: `"["`
- `nr_digits` (int, optional): Number of digits for replacement (2 for 00-99, 3 for 000-999, etc.). Default: `2`

**Returns:**
- `PromptCleanerClient`: Wrapped client with UUID cleaning functionality

**Methods:**
- `get_uuid_mappings()`: Returns dictionary mapping original UUIDs to their replacements

### `clean_prompt(prompt, sep="[", nr_digits=2)`

Clean UUIDs from a prompt string and return the mapping.

**Parameters:**
- `prompt` (str): Input prompt string containing UUIDs
- `sep` (str, optional): Separator character for UUID detection. Supports `[`, `(`, `{`, `<`. Default: `"["`
- `nr_digits` (int, optional): Number of digits for replacement (2 for 00-99, 3 for 000-999, etc.). Default: `2`

**Returns:**
- `Tuple[str, Dict[str, str]]`: Tuple of (cleaned_prompt, uuid_mapping)

**Example:**
```python
cleaned, mapping = clean_prompt("Hello [550e8400-e29b-41d4-a716-446655440000]", sep="[", nr_digits=3)
# cleaned: "Hello [000]"
# mapping: {"550e8400-e29b-41d4-a716-446655440000": "000"}
```

### `restore_output(output, mapping, sep="[", nr_digits=2)`

Restore UUIDs in output string using the provided mapping.

**Parameters:**
- `output` (str): Output string containing digit replacements
- `mapping` (Dict[str, str]): UUID mapping from clean_prompt function
- `sep` (str, optional): Separator character used for UUID pattern. Default: `"["`
- `nr_digits` (int, optional): Number of digits used for replacement. Default: `2`

**Returns:**
- `str`: String with digit replacements restored to original UUIDs

**Example:**
```python
restored = restore_output("Result for [000]", {"550e8400-e29b-41d4-a716-446655440000": "000"}, sep="[", nr_digits=3)
# restored: "Result for [550e8400-e29b-41d4-a716-446655440000]"
```

### Supported UUID Formats

The package detects UUIDs in the standard format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` where each `x` is a hexadecimal digit.

Examples of detected patterns:
- `[550e8400-e29b-41d4-a716-446655440000]`
- `(6ba7b810-9dad-11d1-80b4-00c04fd430c8)`
- `{123e4567-e89b-12d3-a456-426614174000}`
- `<f47ac10b-58cc-4372-a567-0e02b2c3d479>`

### Supported Separators

| Separator | Opening | Closing | Example |
|-----------|---------|---------|---------|
| `[` | `[` | `]` | `[uuid]` → `[00]` |
| `(` | `(` | `)` | `(uuid)` → `(00)` |
| `{` | `{` | `}` | `{uuid}` → `{00}` |
| `<` | `<` | `>` | `<uuid>` → `<00>` |

## Error Handling

The package gracefully handles various edge cases:

- **Invalid UUIDs**: Non-UUID strings are left unchanged
- **Missing separators**: UUIDs without proper separators are ignored
- **Non-string content**: Message content that isn't a string is left unchanged
- **Missing content**: Messages without content field are left unchanged

## Testing

Run the test suite:

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=prompt_cleaner
```

## Development

### Project Structure

```
prompt_cleaner_package/
├── prompt_cleaner/
│   ├── __init__.py
│   ├── cleaner.py          # Main context manager and wrapper classes
│   └── utils.py            # UUID detection and replacement utilities
├── tests/
│   ├── __init__.py
│   ├── test_cleaner.py     # Tests for main functionality
│   └── test_utils.py       # Tests for utility functions
├── setup.py
└── README.md
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Changelog

### Version 1.1.0
- Added non-wrapped functions: `clean_prompt()` and `restore_output()`
- Enhanced API for manual UUID cleaning and restoration
- Added comprehensive tests for new functionality
- Updated documentation with detailed examples

### Version 1.0.0
- Initial release
- Support for UUID detection and replacement
- Context manager interface
- Configurable separators and digit count
- Comprehensive test suite

