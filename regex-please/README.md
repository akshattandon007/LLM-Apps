# regex-please 🤖✨

> "I have a problem. I'll use regex. Now I have two problems."
> — *Every developer, 1997–forever*

**regex-please** fixes the second problem. You describe what you want in plain English. It gives you a working regex *and* highlights the matches in your terminal with glorious ANSI yellow highlights.

No more regex101.com tabs. No more `regex101.com/r/xyz123` tabs you forget to close. No more `/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/` tattoos.

Just:

```bash
regex-please 'all email addresses' contacts.txt
```

And boom — yellow highlights everywhere there's an email. ✨


## ✨ What it does

| You say | It gives you |
|---------|--------------|
| `"all email addresses"` | `[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}` + yellow highlights |
| `"phone numbers in US format"` | `\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}` + highlights |
| `"ISO 8601 dates"` | `\d{4}-\d{2}-\d{2}` + highlights |
| `"hex colors"` | `#[0-9a-fA-F]{6}\b` + highlights |
| `"IPv4 addresses"` | `\b(?:\d{1,3}\.){3}\d{1,3}\b` + highlights |
| `"credit card numbers"` | `\b(?:\d[ -]*?){13,16}\b` + highlights |

Plus: `--test`, `--explain`, `--dry-run`, and stdin piping. Because regex is hard enough without remembering flag syntax.


## 🚀 Install

```bash
# Clone it
git clone https://github.com/akshattandon007/LLM-Apps.git
cd LLM-Apps/regex-please

# Install the one dependency
pip install -r requirements.txt
# (just anthropic>=0.30.0)

# Make it runnable from anywhere (optional but recommended)
chmod +x regex_please.py
ln -s "$(pwd)/regex_please.py" ~/.local/bin/regex-please
# or copy/move it anywhere on your PATH
```

**Requirement:** `ANTHROPIC_API_KEY` in your environment. Get one at [console.anthropic.com](https://console.anthropic.com).

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# Add to your ~/.bashrc / ~/.zshrc / ~/.config/fish/config.fish to persist
```


## 🎮 Usage

### Basic: file in, highlights out

```bash
$ regex-please 'all email addresses' contacts.txt
```

```
john.doe@company.com
support@startup.io
sales@enterprise.co.uk
admin@localhost          ← wait, that's not valid but the regex caught it
dev+testing@example.org

Found 5 match(es).
```
*(Imagine the emails above highlighted in **bright yellow** — your terminal does the ANSI magic)*


### Pipe from stdin

```bash
$ cat logs.txt | regex-please 'IPv4 addresses'
$ grep -r 'error' /var/log | regex-please 'timestamps in ISO format'
$ curl -s api.example.com/users | regex-please 'email addresses'
```


### Test a pattern against a string (`--test`)

```bash
$ regex-please 'US phone numbers' --test '(555) 123-4567'
Match found in '(555) 123-4567':
(555) 123-4567
```

### Just show me the regex (`--dry-run`)

```bash
$ regex-please 'hex color codes' --dry-run
#[0-9a-fA-F]{6}\b
```

### Explain what the regex actually matches (`--explain`)

```bash
$ regex-please 'ISBN-13 numbers' --explain
Pattern: \b(?:ISBN(?:-13)?:?\s*)?(?=[0-9]{13}\b|(?=(?:[0-9]+[-\s]){4})[-\s0-9]{17}\b)97[89][-\s]?[0-9]{1,5}[-\s]?[0-9]+[-\s]?[0-9]+[-\s]?[0-9]\b
Explanation: Matches ISBN-13 numbers with optional 'ISBN-13:' prefix, allowing hyphens or spaces as separators. Validates the 978/979 prefix and 13-digit structure.
```


## 🎛️ Flags

| Flag | Alias | What it does |
|------|-------|--------------|
| `--test "string"` | | Test the generated regex against a sample string (no file needed) |
| `--explain` | `-e` | Get a plain-English explanation of what the regex matches |
| `--dry-run` | `-d` | Just print the generated regex pattern, don't run it |
| `description` | *(positional)* | Natural language description of what to match |
| `file` | *(positional, optional)* | File to search. Omit or use `-` for stdin |


## 🎭 Why regex-please?

### The regex problem
```
You: "I need to extract all URLs from this log file."
Regex: /https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)/
You: *cries in capture groups*
```

### The regex-please way
```bash
$ regex-please 'all URLs' access.log
```
Done. Highlights. Moving on with your life.

### What you get
- **Natural language → regex** — Powered by Claude (Sonnet 4). It knows regex so you don't have to.
- **Live ANSI highlights** — Yellow-background matches in your actual terminal. No browser tabs.
- **Stdin/stdout friendly** — Pipes in, highlights out. Unix philosophy intact.
- **Explain mode** — Because sometimes the regex is *too* clever and you need to know what it actually catches.
- **Dry-run mode** — Grab the pattern, use it in your code, your editor, your regex101 bookmark collection.
- **Test mode** — Verify against a sample string before unleashing on a 5GB log file.
- **Zero config, one dependency** — `anthropic` package. That's it. `requirements.txt` is literally one line.


## 🎪 Examples gallery

### Extract all UUIDs from a database dump
```bash
$ regex-please 'UUID v4 identifiers' postgres_dump.sql
```

### Find all TODO/FIXME comments in a codebase
```bash
$ grep -r 'TODO\|FIXME' src/ | regex-please 'TODO or FIXME comments with descriptions'
```

### Validate API keys in .env files (dry-run to get the pattern)
```bash
$ regex-please 'API keys like sk_live_..., pk_test_..., bear_...' --dry-run
sk_(?:live|test)_[a-zA-Z0-9]{24}|pk_(?:live|test)_[a-zA-Z0-9]{24}|bearer_[a-zA-Z0-9._-]+
```

### Quick test before committing a regex to production code
```bash
$ regex-please 'semantic version numbers like v1.2.3' --test 'v2.10.0-beta.3'
Match found in 'v2.10.0-beta.3':
v2.10.0-beta.3
```


## ⚙️ Requirements

- Python 3.8+
- `anthropic>=0.30.0` (install via `pip install -r requirements.txt`)
- `ANTHROPIC_API_KEY` environment variable (get one at [console.anthropic.com](https://console.anthropic.com))


## 🤝 Contributing

PRs welcome! Ideas:
- More output formats (JSON, CSV, line numbers)
- Config file for custom patterns / model selection
- `--color never/always/auto` flag
- Support for other LLM providers
- `--context N` lines of context around matches

Open an issue or PR at [github.com/akshattandon007/LLM-Apps](https://github.com/akshattandon007/LLM-Apps).


## 📄 License

MIT — do whatever you want, just don't blame me when your regex matches `localhost` as a valid email.


## 🙏 Credits

Built with [Claude (Anthropic)](https://anthropic.com) because regex is the one thing AI is actually better at than humans.

*"Some people, when confronted with a problem, think 'I know, I'll use regular expressions.' Now they have two problems."* — Jamie Zawinski

*Now they have one. You're welcome.* 😎