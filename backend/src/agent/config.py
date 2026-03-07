# -*- coding: utf-8 -*-
"""Agent configuration"""
from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Configuration for the computer agent"""
    
    # LLM settings
    max_tokens: int = 4096
    model: str = "claude-sonnet-4-6"
    
    # Agent behavior
    max_iterations: int = 50
    step_delay: float = 0.3  # Delay between iterations
    
    # Tool execution
    tool_timeout: int = 30  # Timeout for individual tool execution
    enable_parallel_execution: bool = True
    
    # Loop detection
    loop_detection_window: int = 10  # Number of recent actions to track
    loop_detection_threshold: int = 3  # Number of repeats to trigger warning
    
    # Screenshot settings
    screenshot_max_width: int = 1280
    
    # Prompt caching
    enable_prompt_caching: bool = True
    
    # Performance
    enable_tool_result_summarization: bool = False  # Future feature
    max_tool_result_length: int = 5000  # Max characters in tool result
