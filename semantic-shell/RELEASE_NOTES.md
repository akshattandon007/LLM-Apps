# Release Notes: semantic-shell v0.1.0

## 🚀 New Tool: Semantic Shell

AI-powered command autocomplete that converts natural language intent into actual shell commands.

### What's New

**Core Features:**
- Natural language to shell command translation using Claude 3.5 Sonnet
- Context-aware suggestions based on:
  - Recent command history (~/.bash_history)
  - Current working directory
  - Files in current directory
  - System environment (shell, OS, user)
- Interactive mode with command confirmation
- Bash integration via wrapper script

**What's Included:**
- `semantic_shell.py` - Main CLI tool
- `wrapper.sh` - Bash integration for interactive mode
- `test.sh` - Smoke test suite
- `requirements.txt` - Python dependencies
- `README.md` - Complete setup and usage guide
- `.gitignore` - Standard Python gitignore

### Installation

```bash
cd semantic-shell
pip install -r requirements.txt
export ANTHROPIC_API_KEY='***'
chmod +x semantic_shell.py
```

### Usage Examples

**Direct mode:**
```bash
./semantic_shell.py "find large files"
# → find . -type f -size +100M -exec ls -lh {} \;

./semantic_shell.py "kill process on port 8080"
# → lsof -ti:8080 | xargs kill -9
```

**Interactive mode:**
```bash
eval "$(./wrapper.sh)"
ss compress current directory
# Shows: ▶ tar -czf archive.tar.gz .
# Run this command? [Y/n]
```

### Technical Details

- **API**: Anthropic Claude 3.5 Sonnet
- **Context window**: Last 100 commands + current directory state
- **Response time**: ~1-2 seconds typical
- **Safety**: Commands require explicit confirmation in interactive mode

### Testing

Run the smoke test suite:
```bash
./test.sh
```

All checks should pass (API key not required for tests).

### Requirements

- Python 3.8+
- Anthropic API key
- bash (for wrapper script)

### Known Limitations

- Requires internet connection for API calls
- Limited to bash shell integration (zsh/fish wrapper not yet implemented)
- Command history limited to ~/.bash_history

### What's Next

Potential future enhancements:
- Shell history integration (not just bash)
- Command explanation mode
- Safety checks for destructive operations
- Local caching of common patterns
- Support for zsh/fish shells

---

**Full Changelog**: Initial release

**Commit**: 4bd9332
