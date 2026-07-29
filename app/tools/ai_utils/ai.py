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

    text = text.replace("```bash", "").replace("```", "").strip()

    command_patterns = [
        r"`([^`]+)`",
        r"\\b(ls|find|pwd|whoami|ps|dir|tree|cat|echo|cd)\\b[^\\n]*",
    ]

    for pattern in command_patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            candidate = matches[0]
            if isinstance(candidate, tuple):
                candidate = candidate[0]
            candidate = str(candidate).strip()
            if candidate and not candidate.lower().startswith(("here are", "you can", "this will", "if you want", "alternatively")):
                return candidate

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""

    candidates = []
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
        if cleaned.startswith("$"):
            candidates.append(cleaned[1:].strip())
            continue
        if cleaned.startswith("http") or cleaned.startswith("Note:"):
            continue
        if cleaned.lower().startswith(("here are", "you can", "this will", "if you want", "alternatively", "the", "linux", "windows")):
            continue
        if re.match(r"^(?:\d+\.|[-*])\s+", cleaned):
            cleaned = re.sub(r"^(?:\d+\.|[-*])\s+", "", cleaned)
        if cleaned.startswith("`") and cleaned.endswith("`"):
            cleaned = cleaned[1:-1].strip()
        if re.match(r"^[a-zA-Z0-9_./\-\\: ]+$", cleaned) and not any(token in cleaned.lower() for token in ["here are", "you can", "this will", "if you want", "alternatively", "linux", "windows", "note:"]):
            candidates.append(cleaned)

    if candidates:
        return candidates[0]

    return lines[0]


def _fallback_command(prompt):
    if not prompt:
        return "whoami"

    prompt_lower = prompt.lower()
    if any(keyword in prompt_lower for keyword in ["list", "folder", "directories", "dir", "root"]):
        return "ls -la /"
    if any(keyword in prompt_lower for keyword in ["whoami", "user", "logged"]):
        return "whoami"
    if any(keyword in prompt_lower for keyword in ["pwd", "current", "directory"]):
        return "pwd"
    if any(keyword in prompt_lower for keyword in ["process", "ps"]):
        return "ps"
    return "whoami"