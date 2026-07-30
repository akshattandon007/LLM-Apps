#!/usr/bin/env python3
"""
regex-please - Convert natural language descriptions to regex patterns with live highlighting.
"""

import os
import sys
import re
import argparse
from pathlib import Path
from anthropic import Anthropic


def get_regex_pattern(description):
    """Use Claude API to convert natural language to regex pattern."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)
    
    client = Anthropic(api_key=api_key)
    
    system_prompt = "Return ONLY a valid regex pattern. No explanation, no markdown, just the regex."
    
    user_prompt = f"""Description: {description}

Regex pattern:"""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        pattern = response.content[0].text.strip()
        # Remove markdown code blocks if present
        if pattern.startswith('```'):
            lines = pattern.split('\n')
            if len(lines) > 2:
                pattern = '\n'.join(lines[1:-1])
            else:
                pattern = pattern.strip('`')
        pattern = pattern.strip('`').strip()
        
        # Validate that it's a reasonable regex pattern (not empty)
        if not pattern:
            print("Error: Generated empty regex pattern.", file=sys.stderr)
            sys.exit(1)
            
        return pattern
    except Exception as e:
        print(f"Error calling Claude API: {e}", file=sys.stderr)
        sys.exit(1)


def explain_regex(pattern):
    """Get plain English explanation of what the regex matches."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)
    
    client = Anthropic(api_key=api_key)
    
    system_prompt = "Explain in plain English what this regex pattern matches. Be concise and clear."
    
    user_prompt = f"""Regex pattern: {pattern}

Explanation:"""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        explanation = response.content[0].text.strip()
        return explanation
    except Exception as e:
        print(f"Error calling Claude API: {e}", file=sys.stderr)
        sys.exit(1)


def highlight_matches(text, pattern):
    """Highlight all matches of pattern in text using ANSI escape codes."""
    try:
        regex = re.compile(pattern)
    except re.error as e:
        print(f"Error: Invalid regex pattern '{pattern}': {e}", file=sys.stderr)
        sys.exit(1)
    
    # Use yellow background for highlighting
    YELLOW_BG = '\033[43m'
    RESET = '\033[0m'
    
    # Find all matches and highlight them
    def replace_func(match):
        return f"{YELLOW_BG}{match.group()}{RESET}"
    
    highlighted = regex.sub(replace_func, text)
    return highlighted


def process_input(file_path=None):
    """Read input from file or stdin."""
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file '{file_path}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Read from stdin
        if not sys.stdin.isatty():
            return sys.stdin.read()
        else:
            print("Error: No input provided. Provide a file or pipe input via stdin.", file=sys.stderr)
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Convert natural language descriptions to regex patterns with live highlighting.",
        epilog='Example: regex-please "all email addresses" data.txt'
    )
    parser.add_argument(
        'description',
        nargs='?',
        help='Natural language description of the pattern to match'
    )
    parser.add_argument(
        'file',
        nargs='?',
        help='File to search (if omitted, reads from stdin)'
    )
    parser.add_argument(
        '--test',
        metavar='STRING',
        help='Test the regex against a sample string without needing a file'
    )
    parser.add_argument(
        '--explain',
        action='store_true',
        help='Get a plain English explanation of what the regex matches'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Just show the generated regex without executing it'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.description:
        print("Error: Description argument is required.", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    if args.test and (args.file or not sys.stdin.isatty()):
        print("Error: --test cannot be used with file/stdin input.", file=sys.stderr)
        sys.exit(1)
    
    if not args.test and not args.file and sys.stdin.isatty():
        print("Error: Either provide a file or pipe input via stdin.", file=sys.stderr)
        sys.exit(1)
    
    # Generate regex pattern
    pattern = get_regex_pattern(args.description)
    
    if args.dry_run:
        print(pattern)
        return 0
    
    if args.explain:
        explanation = explain_regex(pattern)
        print(f"Explanation: {explanation}")
        # Still show the pattern unless dry-run
        if not args.dry_run:
            print(f"Pattern: {pattern}")
        return 0
    
    if args.test:
        # Test mode: apply pattern to test string
        try:
            regex = re.compile(pattern)
            if regex.search(args.test):
                print(f"Match found in '{args.test}':")
                highlighted = highlight_matches(args.test, pattern)
                print(highlighted)
            else:
                print(f"No match found in '{args.test}' for pattern: {pattern}")
            return 0
        except re.error as e:
            print(f"Error: Invalid regex pattern '{pattern}': {e}", file=sys.stderr)
            sys.exit(1)
    
    # Normal mode: process file or stdin
    text = process_input(args.file)
    
    if not text.strip():
        print("Warning: Input is empty.", file=sys.stderr)
        # Still show pattern for reference
        print(f"Generated pattern: {pattern}")
        return 0
    
    try:
        regex = re.compile(pattern)
        matches = list(regex.finditer(text))
        
        if not matches:
            print(f"No matches found for pattern: {pattern}")
            return 0
        
        # Highlight and print the entire text with matches highlighted
        highlighted_text = highlight_matches(text, pattern)
        print(highlighted_text, end='')
        
        # Print summary
        print(f"\n\nFound {len(matches)} match(es).", file=sys.stderr)
        
    except re.error as e:
        print(f"Error: Invalid regex pattern '{pattern}': {e}", file=sys.stderr)
        sys.exit(1)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())