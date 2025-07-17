import re
import uuid
from typing import Dict, Tuple, List


class UUIDReplacer:
    """Utility class for detecting and replacing UUIDs in text."""
    
    def __init__(self, sep: str = "[", nr_digits: int = 2):
        """
        Initialize UUID replacer.
        
        Args:
            sep: Separator character for UUID pattern ('[', '(', '{')
            nr_digits: Number of digits for replacement (2 for 00-99, 3 for 000-999)
        """
        self.sep = sep
        self.nr_digits = nr_digits
        self.uuid_mapping: Dict[str, str] = {}
        self.counter = 0
        
        # Define closing separator
        self.close_sep = {
            '[': ']',
            '(': ')',
            '{': '}',
            '<': '>'
        }.get(sep, sep)
        
        # Create regex pattern for UUID detection
        # UUID pattern: 8-4-4-4-12 hex digits
        uuid_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
        
        # Escape special regex characters in separators
        escaped_sep = re.escape(self.sep)
        escaped_close = re.escape(self.close_sep)
        
        # Full pattern with separators
        self.pattern = rf'{escaped_sep}({uuid_pattern}){escaped_close}'
    
    def _generate_replacement(self) -> str:
        """Generate next sequential replacement string."""
        replacement = str(self.counter).zfill(self.nr_digits)
        self.counter += 1
        return replacement
    
    def _is_valid_uuid(self, uuid_str: str) -> bool:
        """Check if string is a valid UUID."""
        try:
            uuid.UUID(uuid_str)
            return True
        except ValueError:
            return False
    
    def replace_uuids(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replace UUIDs in text with sequential digits.
        
        Args:
            text: Input text containing UUIDs
            
        Returns:
            Tuple of (modified_text, uuid_mapping)
        """
        def replace_match(match):
            uuid_str = match.group(1)
            
            # Validate UUID
            if not self._is_valid_uuid(uuid_str):
                return match.group(0)  # Return original if not valid UUID
            
            # Check if we've seen this UUID before
            if uuid_str in self.uuid_mapping:
                replacement = self.uuid_mapping[uuid_str]
            else:
                replacement = self._generate_replacement()
                self.uuid_mapping[uuid_str] = replacement
            
            return f"{self.sep}{replacement}{self.close_sep}"
        
        modified_text = re.sub(self.pattern, replace_match, text)
        return modified_text, self.uuid_mapping.copy()
    
    def reset(self):
        """Reset the replacer state."""
        self.uuid_mapping.clear()
        self.counter = 0


def process_messages(messages: List[Dict], sep: str = "[", nr_digits: int = 2) -> Tuple[List[Dict], Dict[str, str]]:
    """
    Process OpenAI messages to replace UUIDs.
    
    Args:
        messages: List of message dictionaries
        sep: Separator character for UUID pattern
        nr_digits: Number of digits for replacement
        
    Returns:
        Tuple of (processed_messages, uuid_mapping)
    """
    replacer = UUIDReplacer(sep=sep, nr_digits=nr_digits)
    processed_messages = []
    all_mappings = {}
    
    for message in messages:
        processed_message = message.copy()
        
        # Process content field if it exists
        if 'content' in message and isinstance(message['content'], str):
            processed_content, mappings = replacer.replace_uuids(message['content'])
            processed_message['content'] = processed_content
            all_mappings.update(mappings)
        
        processed_messages.append(processed_message)
    
    return processed_messages, all_mappings




def clean_prompt(prompt: str, sep: str = "[", nr_digits: int = 2) -> Tuple[str, Dict[str, str]]:
    """
    Clean UUIDs from a prompt string and return mapping.
    
    Args:
        prompt: Input prompt string containing UUIDs
        sep: Separator character for UUID pattern ('[', '(', '{', '<')
        nr_digits: Number of digits for replacement (2 for 00-99, 3 for 000-999)
        
    Returns:
        Tuple of (cleaned_prompt, uuid_mapping)
        
    Example:
        cleaned, mapping = clean_prompt("Hello [550e8400-e29b-41d4-a716-446655440000]", sep="[", nr_digits=3)
        # cleaned: "Hello [000]"
        # mapping: {"550e8400-e29b-41d4-a716-446655440000": "000"}
    """
    replacer = UUIDReplacer(sep=sep, nr_digits=nr_digits)
    cleaned_prompt, mapping = replacer.replace_uuids(prompt)
    return cleaned_prompt, mapping


def restore_output(output: str, mapping: Dict[str, str], sep: str = "[", nr_digits: int = 2) -> str:
    """
    Restore UUIDs in output string using the provided mapping.
    
    Args:
        output: Output string containing digit replacements
        mapping: UUID mapping from clean_prompt function
        sep: Separator character used for UUID pattern ('[', '(', '{', '<')
        nr_digits: Number of digits used for replacement
        
    Returns:
        String with digit replacements restored to original UUIDs
        
    Example:
        restored = restore_output("Result for [000]", {"550e8400-e29b-41d4-a716-446655440000": "000"}, sep="[")
        # restored: "Result for [550e8400-e29b-41d4-a716-446655440000]"
    """
    # Define closing separator
    close_sep = {
        '[': ']',
        '(': ')',
        '{': '}',
        '<': '>'
    }.get(sep, sep)
    
    # Create reverse mapping (digit -> UUID)
    reverse_mapping = {v: k for k, v in mapping.items()}
    
    # Create regex pattern for digit detection
    escaped_sep = re.escape(sep)
    escaped_close = re.escape(close_sep)
    
    # Pattern to match digit replacements
    digit_pattern = rf'{escaped_sep}(\d{{{nr_digits}}}){escaped_close}'
    
    def restore_match(match):
        digit_str = match.group(1)
        if digit_str in reverse_mapping:
            uuid_str = reverse_mapping[digit_str]
            return f"{sep}{uuid_str}{close_sep}"
        return match.group(0)  # Return original if no mapping found
    
    restored_output = re.sub(digit_pattern, restore_match, output)
    return restored_output

