# app/tools/tool_utilities/command_validator.py
import re
import shlex
from typing import Tuple


class CommandValidator:
    """Validates generated commands for safety and syntax."""
    
    DANGEROUS_PATTERNS = [
        #r'^rm\s+-rf\s+/',          # rm -rf /
        #r'^dd\s+if=',               # dd commands
        #r'^mkfs',                   # mkfs commands
        #r'^shred',                  # shred sensitive data
        #r'^shutdown\s*-h',          # shutdown
        #r'^reboot',                 # reboot
        #r'^halt',                   # halt
        #r':\(\)\s*{\s*:\|\s*:',    # fork bomb
        #r'>\s*/dev/sda',            # write to disk
        #r'>\s*/dev/null\s+2>&1\s+&',  # background process dump
    ]
    
    SUSPICIOUS_REDIRECTS = [
        #r'>\s*/etc/',               # redirect to /etc
        #r'>\s*/sys/',               # redirect to /sys
        #r'>\s*/dev/sd',             # redirect to disk
    ]
    
    COMMAND_ALLOWLIST = {
        'ls', 'cd', 'pwd', 'cat', 'echo', 'grep', 'find', 'ps', 'whoami',
        'id', 'uname', 'date', 'uptime', 'df', 'du', 'top', 'htop', 'free',
        'mkdir', 'touch', 'cp', 'mv', 'head', 'tail', 'wc', 'sort', 'uniq',
        'file', 'which', 'whereis', 'curl', 'wget', 'ping', 'netstat', 'ss',
        'ifconfig', 'ip', 'arp', 'nslookup', 'dig', 'traceroute', 'mtr',
        'tar', 'zip', 'unzip', 'gzip', 'gunzip', 'git', 'docker', 'python',
        'node', 'npm', 'pip', 'make', 'gcc', 'java', 'mvn', 'rm', 'rmdir',
        'chmod', 'chown', 'sudo', 'apt', 'yum', 'brew',
    }
    
    @staticmethod
    def validate(command: str, unsafe: bool = False) -> Tuple[bool, str]:
        """
        Validates a command for safety and syntax.
        
        Args:
            command: The command string to validate
            unsafe: If True, skip safety checks (allow all commands)
            
        Returns:
            Tuple of (is_safe: bool, reason: str)
        """
        if not command or not isinstance(command, str):
            return False, "Command is empty or invalid type"
        
        command = command.strip()
        
        if not command:
            return False, "Command is empty after stripping"
        
        # If unsafe mode, skip all checks except syntax
        if unsafe:
            try:
                parts = shlex.split(command)
                if not parts:
                    return False, "Could not parse command"
            except ValueError as e:
                return False, f"Command syntax error: {str(e)}"
            return True, "Safe to execute (unsafe mode)"
        
        # Check for dangerous patterns
        for pattern in CommandValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE | re.MULTILINE):
                return False, f"Dangerous command detected: {pattern}"
        
        # Check for suspicious redirects
        for pattern in CommandValidator.SUSPICIOUS_REDIRECTS:
            if re.search(pattern, command):
                return False, f"Suspicious redirect detected: {pattern}"
        
        # Validate syntax
        try:
            parts = shlex.split(command)
            if not parts:
                return False, "Could not parse command"
        except ValueError as e:
            return False, f"Command syntax error: {str(e)}"
        
        # Extract base command
        base_command = parts[0].split('/')[-1]  # Handle paths like /usr/bin/ls
        
        # Check if base command is in allowlist or is a common tool
        if not CommandValidator._is_allowed_command(base_command):
            return False, f"Command '{base_command}' not in allowlist (use with caution)"
        
        return True, "Safe to execute"
    
    @staticmethod
    def _is_allowed_command(cmd: str) -> bool:
        """Check if command is in the allowlist."""
        return cmd.lower() in CommandValidator.COMMAND_ALLOWLIST
    
    @staticmethod
    def add_to_allowlist(commands: list[str]) -> None:
        """Add commands to the allowlist."""
        CommandValidator.COMMAND_ALLOWLIST.update(commands)
    
    @staticmethod
    def preview(command: str) -> str:
        """Generate a preview of the command for user review."""
        return f"[?] Execute: {command}"
