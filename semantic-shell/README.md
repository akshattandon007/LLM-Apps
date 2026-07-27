# Semantic Shell

AI-powered command autocomplete for your terminal. Type what you want in plain English, get the actual shell command.

## Features

- **Natural language to shell commands**: Describe what you want, get the exact command
- **Context-aware suggestions**: Uses your command history and current directory
- **Interactive mode**: Review and confirm before running
- **Fast**: Powered by Claude 3.5 Sonnet

## Installation

### Prerequisites

- Python 3.8+
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Setup

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/llm-apps.git
cd llm-apps/semantic-shell
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your API key:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

4. Make the script executable:
```bash
chmod +x semantic_shell.py
```

5. Add to your PATH (optional):
```bash
sudo ln -s $(pwd)/semantic_shell.py /usr/local/bin/semantic-shell
```

## Usage

### Direct mode

Get a command suggestion:

```bash
./semantic_shell.py "find large files"
# Output: find . -type f -size +100M -exec ls -lh {} \;

./semantic_shell.py "show disk usage"
# Output: df -h

./semantic_shell.py "compress current directory"
# Output: tar -czf archive.tar.gz .
```

### Interactive mode (recommended)

Add the shell wrapper to your `~/.bashrc`:

```bash
# Add this line to ~/.bashrc
eval "$(./wrapper.sh)"
```

Then source it:
```bash
source ~/.bashrc
```

Now use the `ss` command:

```bash
ss find large files
# Shows: ▶ find . -type f -size +100M -exec ls -lh {} \;
# Run this command? [Y/n] 
```

## Examples

| What you type | Command you get |
|--------------|----------------|
| `ss find python files` | `find . -name "*.py"` |
| `ss kill process on port 8080` | `lsof -ti:8080 \| xargs kill -9` |
| `ss show my IP address` | `curl -s ifconfig.me` |
| `ss list files by size` | `ls -lhS` |
| `ss count lines of code` | `find . -name "*.py" \| xargs wc -l` |

## How it works

1. **Context gathering**: Reads your recent command history and current directory
2. **AI processing**: Sends your intent + context to Claude API
3. **Command generation**: Returns the exact shell command
4. **Interactive confirmation**: (wrapper mode) Shows command and asks for confirmation

## Configuration

### Environment variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)

### Command history

The tool reads from `~/.bash_history` by default. Recent commands help improve suggestions.

## Troubleshooting

**"ERROR: ANTHROPIC_API_KEY environment variable not set"**
- Set your API key: `export ANTHROPIC_API_KEY='sk-ant-...'`
- Add it to your `~/.bashrc` to persist across sessions

**Permission denied**
- Make the script executable: `chmod +x semantic_shell.py`

**Command not found**
- Ensure the script is in your PATH or use the full path: `./semantic_shell.py`

## Safety

- Commands are shown before execution (interactive mode)
- No commands run automatically without confirmation
- Review every suggested command before running
- API calls are logged to `~/.cache/semantic-shell/`

## License

MIT

## Credits

Built with Claude 3.5 Sonnet by Anthropic.
