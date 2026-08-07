#ai_utils/ai.py
import re

def _extract_command_text(response):
    text = ""

    if isinstance(response, str):
        text = response.strip()
    elif isinstance(response, dict):
        if isinstance(response.get("response"), str):
            text = response["response"].strip()
        elif isinstance(response.get("content"), str):
            text = response["content"].strip()
        elif isinstance(response.get("message"), dict):
            content = response["message"].get("content")
            if isinstance(content, str):
                text = content.strip()
    elif hasattr(response, "response") and isinstance(response.response, str):
        text = response.response.strip()
    elif hasattr(response, "content") and isinstance(response.content, str):
        text = response.content.strip()

    if not text:
        return ""

    # Remove markdown code blocks but preserve content
    text = text.replace("```bash", "").replace("```", "").strip()
    
    # Remove "Command:" prefix if present
    if text.startswith("Command:"):
        text = text[8:].strip()

    # Look for backtick-wrapped commands first
    backtick_match = re.search(r"`([^`]+)`", text, re.DOTALL)
    if backtick_match:
        candidate = backtick_match.group(1).strip()
        if candidate and not candidate.lower().startswith(("here are", "you can", "this will", "if you want", "alternatively")):
            return candidate

    lines = [line.rstrip() for line in text.split('\n')]
    
    # Filter out empty lines and comments
    filtered_lines = []
    skip_section = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip explanatory text
        if stripped.lower().startswith(("here are", "you can", "this will", "if you want", "alternatively", "example:", "note:", "the", "linux", "windows")):
            skip_section = True
            continue
        
        # Start of a command block
        if stripped and not skip_section:
            filtered_lines.append(line)
        elif stripped and skip_section and (stripped.startswith("-") or stripped.startswith("$") or re.match(r"^[a-zA-Z]", stripped)):
            skip_section = False
            filtered_lines.append(line)
        elif stripped.startswith("$"):
            filtered_lines.append(stripped[1:].strip())
        elif stripped and not stripped.startswith("http"):
            if not any(x in stripped.lower() for x in ["here are", "you can", "this will", "alternatively"]):
                filtered_lines.append(line)

    # Reconstruct the command
    if filtered_lines:
        # Find the first non-empty line that looks like a command
        for i, line in enumerate(filtered_lines):
            if line.strip():
                # Collect all subsequent lines that are part of the command
                command_lines = []
                for j in range(i, len(filtered_lines)):
                    command_lines.append(filtered_lines[j])
                
                # For here-documents, include all lines until EOF
                result = '\n'.join(command_lines).strip()
                if result:
                    return result
    
    # Last resort: return first non-empty line
    for line in lines:
        if line.strip() and not line.strip().lower().startswith(("here are", "example", "note")):
            return line.strip()
    
    return ""


def _fallback_command(prompt):
    if not prompt:
        return "whoami"

    prompt_lower = prompt.lower()
    if any(keyword in prompt_lower for keyword in ["delete", "remove", "rm", "erase"]):
        return "rm ~/tmp_file"
    if any(keyword in prompt_lower for keyword in ["list", "folder", "directories", "dir", "root"]):
        return "ls -la /"
    if any(keyword in prompt_lower for keyword in ["create", "file", "code", "python"]):
        return "echo '# Python file' > /tmp/test.py"
    if any(keyword in prompt_lower for keyword in ["whoami", "user", "logged"]):
        return "whoami"
    if any(keyword in prompt_lower for keyword in ["pwd", "current", "directory"]):
        return "pwd"
    if any(keyword in prompt_lower for keyword in ["process", "ps"]):
        return "ps"
    return "whoami"