#!/usr/bin/env python3
"""
Semantic Shell - AI-powered command autocomplete
Converts natural language intent to actual shell commands using Claude API
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from anthropic import Anthropic

# Configuration
HISTORY_FILE = Path.home() / ".bash_history"
CACHE_DIR = Path.home() / ".cache" / "semantic-shell"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_command_history(limit=100):
    """Extract recent command history for context"""
    if not HISTORY_FILE.exists():
        return []
    
    with open(HISTORY_FILE, 'r', errors='ignore') as f:
        lines = f.readlines()
    
    # Get unique commands, most recent first
    commands = []
    seen = set()
    for line in reversed(lines[-limit * 2:]):  # Read more to account for duplicates
        cmd = line.strip()
        if cmd and cmd not in seen and not cmd.startswith('#'):
            seen.add(cmd)
            commands.append(cmd)
            if len(commands) >= limit:
                break
    
    return commands


def get_system_context():
    """Gather system context for better suggestions"""
    context = {
        "cwd": os.getcwd(),
        "user": os.environ.get("USER", "unknown"),
        "shell": os.environ.get("SHELL", "unknown"),
        "os": sys.platform,
    }
    
    # Get files in current directory
    try:
        files = os.listdir('.')
        context["files"] = files[:50]  # Limit to 50 files
    except:
        context["files"] = []
    
    return context


def build_prompt(intent, history, context):
    """Build the Claude prompt with context"""
    history_str = "\n".join(f"  {cmd}" for cmd in history[:20])
    files_str = ", ".join(context["files"][:20])
    
    prompt = f"""You are a shell command expert. Convert the user's natural language intent into the exact shell command they need.

Current context:
- Working directory: {context['cwd']}
- Shell: {context['shell']}
- OS: {context['os']}
- Files in current directory: {files_str if files_str else "(empty)"}

Recent command history:
{history_str if history_str else "  (no history)"}

User intent: "{intent}"

Respond with ONLY the shell command, nothing else. No explanations, no markdown, no backticks.
The command should be ready to paste and run immediately.

Examples:
- "find large files" → find . -type f -size +100M -exec ls -lh {{}} \\;
- "show disk usage" → df -h
- "kill process on port 8080" → lsof -ti:8080 | xargs kill -9
- "compress this folder" → tar -czf archive.tar.gz .

Command:"""

    return prompt


def get_command_suggestion(intent):
    """Get command suggestion from Claude API"""
    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "ERROR: ANTHROPIC_API_KEY environment variable not set"
    
    try:
        client = Anthropic(api_key=api_key)
        
        # Gather context
        history = get_command_history()
        context = get_system_context()
        
        # Build prompt
        prompt = build_prompt(intent, history, context)
        
        # Call Claude API
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract command from response
        command = message.content[0].text.strip()
        
        # Clean up any markdown artifacts
        if command.startswith('```'):
            lines = command.split('\n')
            command = '\n'.join(line for line in lines if not line.startswith('```'))
            command = command.strip()
        
        return command
        
    except Exception as e:
        return f"ERROR: {str(e)}"


def main():
    if len(sys.argv) < 2:
        print("Usage: semantic-shell <natural language command>")
        print()
        print("Examples:")
        print('  semantic-shell "find large files"')
        print('  semantic-shell "show disk usage"')
        print('  semantic-shell "compress current directory"')
        sys.exit(1)
    
    # Join all arguments as the intent
    intent = " ".join(sys.argv[1:])
    
    # Get suggestion
    command = get_command_suggestion(intent)
    
    # Output the command
    print(command)


if __name__ == "__main__":
    main()
