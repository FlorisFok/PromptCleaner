import pytest
from prompt_cleaner.utils import UUIDReplacer, process_messages, clean_prompt, restore_output


class TestUUIDReplacer:
    """Test cases for UUIDReplacer class."""
    
    def test_init_default_params(self):
        """Test UUIDReplacer initialization with default parameters."""
        replacer = UUIDReplacer()
        assert replacer.sep == "["
        assert replacer.nr_digits == 2
        assert replacer.close_sep == "]"
        assert replacer.counter == 0
        assert replacer.uuid_mapping == {}
    
    def test_init_custom_params(self):
        """Test UUIDReplacer initialization with custom parameters."""
        replacer = UUIDReplacer(sep="(", nr_digits=3)
        assert replacer.sep == "("
        assert replacer.nr_digits == 3
        assert replacer.close_sep == ")"
    
    def test_init_different_separators(self):
        """Test UUIDReplacer with different separator types."""
        test_cases = [
            ("[", "]"),
            ("(", ")"),
            ("{", "}"),
            ("<", ">")
        ]
        
        for open_sep, close_sep in test_cases:
            replacer = UUIDReplacer(sep=open_sep)
            assert replacer.sep == open_sep
            assert replacer.close_sep == close_sep
    
    def test_generate_replacement(self):
        """Test sequential replacement generation."""
        replacer = UUIDReplacer(nr_digits=2)
        
        assert replacer._generate_replacement() == "00"
        assert replacer._generate_replacement() == "01"
        assert replacer._generate_replacement() == "02"
        
        # Test with 3 digits
        replacer = UUIDReplacer(nr_digits=3)
        assert replacer._generate_replacement() == "000"
        assert replacer._generate_replacement() == "001"
    
    def test_is_valid_uuid(self):
        """Test UUID validation."""
        replacer = UUIDReplacer()
        
        # Valid UUIDs
        valid_uuids = [
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "6ba7b811-9dad-11d1-80b4-00c04fd430c8"
        ]
        
        for uuid_str in valid_uuids:
            assert replacer._is_valid_uuid(uuid_str)
        
        # Invalid UUIDs
        invalid_uuids = [
            "not-a-uuid",
            "550e8400-e29b-41d4-a716",  # Too short
            "550e8400-e29b-41d4-a716-446655440000-extra",  # Too long
            "ggge8400-e29b-41d4-a716-446655440000"  # Invalid hex
        ]
        
        for uuid_str in invalid_uuids:
            assert not replacer._is_valid_uuid(uuid_str)
    
    def test_replace_uuids_basic(self):
        """Test basic UUID replacement."""
        replacer = UUIDReplacer(sep="[", nr_digits=2)
        
        text = "Hello [550e8400-e29b-41d4-a716-446655440000] world"
        result, mappings = replacer.replace_uuids(text)
        
        assert result == "Hello [00] world"
        assert "550e8400-e29b-41d4-a716-446655440000" in mappings
        assert mappings["550e8400-e29b-41d4-a716-446655440000"] == "00"
    
    def test_replace_uuids_multiple(self):
        """Test replacement of multiple UUIDs."""
        replacer = UUIDReplacer(sep="[", nr_digits=2)
        
        text = "UUID1: [550e8400-e29b-41d4-a716-446655440000] UUID2: [6ba7b810-9dad-11d1-80b4-00c04fd430c8]"
        result, mappings = replacer.replace_uuids(text)
        
        assert result == "UUID1: [00] UUID2: [01]"
        assert len(mappings) == 2
        assert mappings["550e8400-e29b-41d4-a716-446655440000"] == "00"
        assert mappings["6ba7b810-9dad-11d1-80b4-00c04fd430c8"] == "01"
    
    def test_replace_uuids_duplicate(self):
        """Test replacement of duplicate UUIDs."""
        replacer = UUIDReplacer(sep="[", nr_digits=2)
        
        text = "First: [550e8400-e29b-41d4-a716-446655440000] Second: [550e8400-e29b-41d4-a716-446655440000]"
        result, mappings = replacer.replace_uuids(text)
        
        assert result == "First: [00] Second: [00]"
        assert len(mappings) == 1
        assert mappings["550e8400-e29b-41d4-a716-446655440000"] == "00"
    
    def test_replace_uuids_different_separators(self):
        """Test replacement with different separators."""
        test_cases = [
            ("(", ")", "Hello (550e8400-e29b-41d4-a716-446655440000) world", "Hello (00) world"),
            ("{", "}", "Hello {550e8400-e29b-41d4-a716-446655440000} world", "Hello {00} world"),
            ("<", ">", "Hello <550e8400-e29b-41d4-a716-446655440000> world", "Hello <00> world")
        ]
        
        for open_sep, close_sep, input_text, expected in test_cases:
            replacer = UUIDReplacer(sep=open_sep, nr_digits=2)
            result, mappings = replacer.replace_uuids(input_text)
            assert result == expected
    
    def test_replace_uuids_no_match(self):
        """Test text with no UUIDs."""
        replacer = UUIDReplacer()
        
        text = "Hello world, no UUIDs here!"
        result, mappings = replacer.replace_uuids(text)
        
        assert result == text
        assert mappings == {}
    
    def test_replace_uuids_invalid_uuid(self):
        """Test text with invalid UUID format."""
        replacer = UUIDReplacer()
        
        text = "Hello [not-a-valid-uuid] world"
        result, mappings = replacer.replace_uuids(text)
        
        assert result == text  # Should remain unchanged
        assert mappings == {}
    
    def test_reset(self):
        """Test resetting replacer state."""
        replacer = UUIDReplacer()
        
        # Process some UUIDs
        text = "Hello [550e8400-e29b-41d4-a716-446655440000] world"
        replacer.replace_uuids(text)
        
        assert len(replacer.uuid_mapping) == 1
        assert replacer.counter == 1
        
        # Reset
        replacer.reset()
        
        assert len(replacer.uuid_mapping) == 0
        assert replacer.counter == 0


class TestProcessMessages:
    """Test cases for process_messages function."""
    
    def test_process_messages_basic(self):
        """Test basic message processing."""
        messages = [
            {"role": "user", "content": "Hello [550e8400-e29b-41d4-a716-446655440000]"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        result, mappings = process_messages(messages, sep="[", nr_digits=2)
        
        assert len(result) == 2
        assert result[0]["content"] == "Hello [00]"
        assert result[1]["content"] == "Hi there!"
        assert len(mappings) == 1
    
    def test_process_messages_multiple_uuids(self):
        """Test processing messages with multiple UUIDs."""
        messages = [
            {"role": "user", "content": "UUID1: [550e8400-e29b-41d4-a716-446655440000] UUID2: [6ba7b810-9dad-11d1-80b4-00c04fd430c8]"},
            {"role": "assistant", "content": "Got UUID: [550e8400-e29b-41d4-a716-446655440000]"}
        ]
        
        result, mappings = process_messages(messages, sep="[", nr_digits=2)
        
        assert result[0]["content"] == "UUID1: [00] UUID2: [01]"
        assert result[1]["content"] == "Got UUID: [00]"  # Same UUID should get same replacement
        assert len(mappings) == 2
    
    def test_process_messages_no_content(self):
        """Test processing messages without content field."""
        messages = [
            {"role": "system", "name": "test"},
            {"role": "user", "content": "Hello [550e8400-e29b-41d4-a716-446655440000]"}
        ]
        
        result, mappings = process_messages(messages)
        
        assert len(result) == 2
        assert result[0] == {"role": "system", "name": "test"}  # Unchanged
        assert result[1]["content"] == "Hello [00]"
    
    def test_process_messages_non_string_content(self):
        """Test processing messages with non-string content."""
        messages = [
            {"role": "user", "content": ["not", "a", "string"]},
            {"role": "user", "content": "Hello [550e8400-e29b-41d4-a716-446655440000]"}
        ]
        
        result, mappings = process_messages(messages)
        
        assert result[0]["content"] == ["not", "a", "string"]  # Unchanged
        assert result[1]["content"] == "Hello [00]"
    
    def test_process_messages_custom_params(self):
        """Test processing with custom separator and digits."""
        messages = [
            {"role": "user", "content": "Hello (550e8400-e29b-41d4-a716-446655440000)"}
        ]
        
        result, mappings = process_messages(messages, sep="(", nr_digits=3)
        
        assert result[0]["content"] == "Hello (000)"
        assert mappings["550e8400-e29b-41d4-a716-446655440000"] == "000"




class TestCleanPrompt:
    """Test cases for clean_prompt function."""
    
    def test_clean_prompt_basic(self):
        """Test basic clean_prompt functionality."""
        prompt = "Hello [550e8400-e29b-41d4-a716-446655440000] world"
        cleaned, mapping = clean_prompt(prompt, sep="[", nr_digits=2)
        
        assert cleaned == "Hello [00] world"
        assert "550e8400-e29b-41d4-a716-446655440000" in mapping
        assert mapping["550e8400-e29b-41d4-a716-446655440000"] == "00"
    
    def test_clean_prompt_multiple_uuids(self):
        """Test clean_prompt with multiple UUIDs."""
        prompt = "User [550e8400-e29b-41d4-a716-446655440000] has order [6ba7b810-9dad-11d1-80b4-00c04fd430c8]"
        cleaned, mapping = clean_prompt(prompt, sep="[", nr_digits=2)
        
        assert cleaned == "User [00] has order [01]"
        assert len(mapping) == 2
        assert mapping["550e8400-e29b-41d4-a716-446655440000"] == "00"
        assert mapping["6ba7b810-9dad-11d1-80b4-00c04fd430c8"] == "01"
    
    def test_clean_prompt_duplicate_uuids(self):
        """Test clean_prompt with duplicate UUIDs."""
        prompt = "First [550e8400-e29b-41d4-a716-446655440000] and second [550e8400-e29b-41d4-a716-446655440000]"
        cleaned, mapping = clean_prompt(prompt, sep="[", nr_digits=2)
        
        assert cleaned == "First [00] and second [00]"
        assert len(mapping) == 1
        assert mapping["550e8400-e29b-41d4-a716-446655440000"] == "00"
    
    def test_clean_prompt_different_separators(self):
        """Test clean_prompt with different separators."""
        test_cases = [
            ("(", "Hello (550e8400-e29b-41d4-a716-446655440000)", "Hello (00)"),
            ("{", "Hello {550e8400-e29b-41d4-a716-446655440000}", "Hello {00}"),
            ("<", "Hello <550e8400-e29b-41d4-a716-446655440000>", "Hello <00>")
        ]
        
        for sep, input_prompt, expected in test_cases:
            cleaned, mapping = clean_prompt(input_prompt, sep=sep, nr_digits=2)
            assert cleaned == expected
            assert len(mapping) == 1
    
    def test_clean_prompt_custom_digits(self):
        """Test clean_prompt with custom digit count."""
        prompt = "Hello [550e8400-e29b-41d4-a716-446655440000]"
        cleaned, mapping = clean_prompt(prompt, sep="[", nr_digits=3)
        
        assert cleaned == "Hello [000]"
        assert mapping["550e8400-e29b-41d4-a716-446655440000"] == "000"
    
    def test_clean_prompt_no_uuids(self):
        """Test clean_prompt with no UUIDs."""
        prompt = "Hello world, no UUIDs here!"
        cleaned, mapping = clean_prompt(prompt)
        
        assert cleaned == prompt
        assert mapping == {}
    
    def test_clean_prompt_invalid_uuid(self):
        """Test clean_prompt with invalid UUID format."""
        prompt = "Hello [not-a-valid-uuid] world"
        cleaned, mapping = clean_prompt(prompt)
        
        assert cleaned == prompt
        assert mapping == {}


class TestRestoreOutput:
    """Test cases for restore_output function."""
    
    def test_restore_output_basic(self):
        """Test basic restore_output functionality."""
        output = "Result for [00]"
        mapping = {"550e8400-e29b-41d4-a716-446655440000": "00"}
        restored = restore_output(output, mapping, sep="[", nr_digits=2)
        
        assert restored == "Result for [550e8400-e29b-41d4-a716-446655440000]"
    
    def test_restore_output_multiple_digits(self):
        """Test restore_output with multiple digit replacements."""
        output = "User [00] has order [01]"
        mapping = {
            "550e8400-e29b-41d4-a716-446655440000": "00",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8": "01"
        }
        restored = restore_output(output, mapping, sep="[", nr_digits=2)
        
        expected = "User [550e8400-e29b-41d4-a716-446655440000] has order [6ba7b810-9dad-11d1-80b4-00c04fd430c8]"
        assert restored == expected
    
    def test_restore_output_duplicate_digits(self):
        """Test restore_output with duplicate digit replacements."""
        output = "First [00] and second [00]"
        mapping = {"550e8400-e29b-41d4-a716-446655440000": "00"}
        restored = restore_output(output, mapping, sep="[", nr_digits=2)
        
        expected = "First [550e8400-e29b-41d4-a716-446655440000] and second [550e8400-e29b-41d4-a716-446655440000]"
        assert restored == expected
    
    def test_restore_output_different_separators(self):
        """Test restore_output with different separators."""
        test_cases = [
            ("(", "Result (00)", "Result (550e8400-e29b-41d4-a716-446655440000)"),
            ("{", "Result {00}", "Result {550e8400-e29b-41d4-a716-446655440000}"),
            ("<", "Result <00>", "Result <550e8400-e29b-41d4-a716-446655440000>")
        ]
        
        mapping = {"550e8400-e29b-41d4-a716-446655440000": "00"}
        
        for sep, input_output, expected in test_cases:
            restored = restore_output(input_output, mapping, sep=sep, nr_digits=2)
            assert restored == expected
    
    def test_restore_output_custom_digits(self):
        """Test restore_output with custom digit count."""
        output = "Result [000]"
        mapping = {"550e8400-e29b-41d4-a716-446655440000": "000"}
        restored = restore_output(output, mapping, sep="[", nr_digits=3)
        
        assert restored == "Result [550e8400-e29b-41d4-a716-446655440000]"
    
    def test_restore_output_no_digits(self):
        """Test restore_output with no digit replacements."""
        output = "Hello world, no digits here!"
        mapping = {"550e8400-e29b-41d4-a716-446655440000": "00"}
        restored = restore_output(output, mapping)
        
        assert restored == output
    
    def test_restore_output_unmapped_digits(self):
        """Test restore_output with digits not in mapping."""
        output = "Result [99]"
        mapping = {"550e8400-e29b-41d4-a716-446655440000": "00"}
        restored = restore_output(output, mapping, sep="[", nr_digits=2)
        
        assert restored == output  # Should remain unchanged
    
    def test_restore_output_empty_mapping(self):
        """Test restore_output with empty mapping."""
        output = "Result [00]"
        mapping = {}
        restored = restore_output(output, mapping)
        
        assert restored == output


class TestCleanRestoreRoundTrip:
    """Test cases for clean_prompt and restore_output round-trip functionality."""
    
    def test_round_trip_basic(self):
        """Test clean and restore round-trip."""
        original = "Hello [550e8400-e29b-41d4-a716-446655440000] world"
        
        # Clean
        cleaned, mapping = clean_prompt(original, sep="[", nr_digits=2)
        assert cleaned == "Hello [00] world"
        
        # Simulate some processing that might modify the output
        processed_output = "Response for [00]"
        
        # Restore
        restored = restore_output(processed_output, mapping, sep="[", nr_digits=2)
        assert restored == "Response for [550e8400-e29b-41d4-a716-446655440000]"
    
    def test_round_trip_multiple_uuids(self):
        """Test clean and restore round-trip with multiple UUIDs."""
        original = "User [550e8400-e29b-41d4-a716-446655440000] order [6ba7b810-9dad-11d1-80b4-00c04fd430c8]"
        
        # Clean
        cleaned, mapping = clean_prompt(original, sep="[", nr_digits=2)
        assert cleaned == "User [00] order [01]"
        
        # Simulate processing
        processed_output = "Processed [00] and [01] successfully"
        
        # Restore
        restored = restore_output(processed_output, mapping, sep="[", nr_digits=2)
        expected = "Processed [550e8400-e29b-41d4-a716-446655440000] and [6ba7b810-9dad-11d1-80b4-00c04fd430c8] successfully"
        assert restored == expected
    
    def test_round_trip_different_separators(self):
        """Test clean and restore round-trip with different separators."""
        test_cases = [
            ("(", "Hello (550e8400-e29b-41d4-a716-446655440000)", "Result (00)", "Result (550e8400-e29b-41d4-a716-446655440000)"),
            ("{", "Hello {550e8400-e29b-41d4-a716-446655440000}", "Result {00}", "Result {550e8400-e29b-41d4-a716-446655440000}"),
            ("<", "Hello <550e8400-e29b-41d4-a716-446655440000>", "Result <00>", "Result <550e8400-e29b-41d4-a716-446655440000>")
        ]
        
        for sep, original, processed, expected_restored in test_cases:
            # Clean
            cleaned, mapping = clean_prompt(original, sep=sep, nr_digits=2)
            
            # Restore
            restored = restore_output(processed, mapping, sep=sep, nr_digits=2)
            assert restored == expected_restored
    
    def test_round_trip_custom_digits(self):
        """Test clean and restore round-trip with custom digit count."""
        original = "Hello [550e8400-e29b-41d4-a716-446655440000]"
        
        # Clean with 3 digits
        cleaned, mapping = clean_prompt(original, sep="[", nr_digits=3)
        assert cleaned == "Hello [000]"
        
        # Simulate processing
        processed_output = "Response [000]"
        
        # Restore with 3 digits
        restored = restore_output(processed_output, mapping, sep="[", nr_digits=3)
        assert restored == "Response [550e8400-e29b-41d4-a716-446655440000]"

