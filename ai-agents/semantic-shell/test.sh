#!/usr/bin/env bash
# Smoke test for semantic-shell

set -e

echo "=== Semantic Shell Smoke Test ==="
echo

cd "$(dirname "$0")"

echo "1. Checking files..."
for file in semantic_shell.py requirements.txt README.md wrapper.sh .gitignore; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (missing)"
        exit 1
    fi
done
echo

echo "2. Checking dependencies..."
if python3 -c "import anthropic" 2>/dev/null; then
    echo "  ✓ anthropic library installed"
else
    echo "  ✗ anthropic library not installed"
    echo "    Run: pip install -r requirements.txt"
    exit 1
fi
echo

echo "3. Testing CLI interface..."
# Test without API key (should show error message)
output=$(./semantic_shell.py "test" 2>&1 || true)
if [[ $output == *"ANTHROPIC_API_KEY"* ]] || [[ $output == *"ERROR"* ]]; then
    echo "  ✓ CLI runs (API key check working)"
else
    echo "  ? Unexpected output: $output"
fi
echo

echo "4. Testing help/usage..."
output=$(./semantic_shell.py 2>&1 || true)
if [[ $output == *"Usage"* ]]; then
    echo "  ✓ Usage message displays"
else
    echo "  ✗ Usage message not found"
    exit 1
fi
echo

echo "5. Checking wrapper script..."
if bash wrapper.sh | grep -q "Semantic Shell integration"; then
    echo "  ✓ Wrapper script outputs integration code"
else
    echo "  ✗ Wrapper script failed"
    exit 1
fi
echo

echo "=== All checks passed! ==="
echo
echo "To use semantic-shell, you need to:"
echo "  1. Set ANTHROPIC_API_KEY environment variable"
echo "  2. Run: export ANTHROPIC_API_KEY='***'"
echo "  3. Test: ./semantic_shell.py 'find large files'"
echo "  4. For interactive mode: eval \"\$(./wrapper.sh)\""
