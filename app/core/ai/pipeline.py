# app/core/ai/pipeline.py
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.core.ai.base import LLMProvider


class CommandHistory:
    """Stores command execution history for context."""
    
    def __init__(self, max_history: int = 10):
        self.history: List[Dict[str, Any]] = []
        self.max_history = max_history
    
    def add(self, prompt: str, command: str, result: Optional[Dict[str, Any]] = None, success: bool = False):
        """Add a command to history."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'prompt': prompt,
            'command': command,
            'result': result,
            'success': success,
        }
        self.history.append(entry)
        
        # Keep only recent history
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def get_context(self, last_n: int = 3) -> str:
        """Get recent history as context for LLM."""
        if not self.history:
            return ""
        
        recent = self.history[-last_n:]
        context = "\n## Recent Command History:\n"
        
        for entry in recent:
            status = "✓ SUCCESS" if entry['success'] else "✗ FAILED"
            context += f"\n- Prompt: {entry['prompt']}\n  Command: {entry['command']}\n  Status: {status}"
            if entry.get('result') and entry['result'].get('error'):
                context += f"\n  Error: {entry['result']['error']}"
        
        return context
    
    def clear(self):
        """Clear history."""
        self.history.clear()


class AICommandPipeline:
    """Main AI pipeline for command generation and execution."""
    
    def __init__(self, provider: Optional[LLMProvider] = None, max_retries: int = 3):
        self.provider = provider
        self.max_retries = max_retries
        self.history = CommandHistory()
    
    def generate_command(self, prompt: str, target_info: Optional[Dict[str, str]] = None, 
                         include_history: bool = True) -> str:
        """
        Generate a command using the LLM provider.
        
        Args:
            prompt: User's natural language prompt
            target_info: Information about target (os, shell, etc.)
            include_history: Whether to include recent command history as context
            
        Returns:
            Generated command string
        """
        if self.provider is None:
            raise ValueError("No LLM provider configured")
        
        # Build enhanced prompt
        enhanced_prompt = self._build_prompt(prompt, target_info, include_history)
        
        try:
            response = self.provider.generate(enhanced_prompt)
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to generate command: {str(e)}")
    
    def _build_prompt(self, user_prompt: str, target_info: Optional[Dict[str, str]] = None,
                     include_history: bool = True) -> str:
        """Build an enhanced prompt with context and instructions."""
        
        system_instructions = """You are a command generation AI. Your task is to generate a single, safe shell command.

RULES:
1. Return ONLY the command, nothing else
2. Do NOT include explanations, markdown, or backticks
3. The command must be valid and executable
4. Prefer safe, non-destructive operations
5. Do NOT generate commands that modify system files or delete data
6. If unsure, use 'ls' or 'pwd' as fallback

Example responses:
- ls -la /home
- cat /etc/hostname
- ps aux | grep python
"""
        
        prompt = system_instructions + "\n"
        
        # Add target info if available
        if target_info:
            prompt += f"\nTarget Information:\n"
            for key, value in target_info.items():
                prompt += f"- {key}: {value}\n"
        
        # Add history context
        if include_history:
            history_context = self.history.get_context()
            if history_context:
                prompt += history_context + "\n"
        
        # Add user prompt
        prompt += f"\nGenerate a command for: {user_prompt}"
        
        return prompt
    
    def record_success(self, prompt: str, command: str, result: Optional[Dict[str, Any]] = None):
        """Record a successful command execution."""
        self.history.add(prompt, command, result, success=True)
    
    def record_failure(self, prompt: str, command: str, error: Optional[str] = None):
        """Record a failed command execution."""
        result = {'error': error} if error else None
        self.history.add(prompt, command, result, success=False)
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get full command history."""
        return self.history.history.copy()
    
    def clear_history(self):
        """Clear command history."""
        self.history.clear()
