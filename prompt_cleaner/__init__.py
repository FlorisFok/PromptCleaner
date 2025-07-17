"""
Prompt Cleaner - OpenAI Wrapper for UUID Replacement

A Python package that wraps OpenAI client to automatically replace UUIDs 
in messages with sequential digits for cleaner prompts.
"""

from .cleaner import prompt_cleaner
from .utils import clean_prompt, restore_output

__version__ = "1.1.0"
__author__ = "Manus AI"
__all__ = ["prompt_cleaner", "clean_prompt", "restore_output"]

