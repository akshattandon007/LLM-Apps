"""AST-based code chunking using tree-sitter.

Chunks source code at function/class boundaries with docstrings and metadata.
"""

from __future__ import annotations

from src.models import Chunk

try:
    from tree_sitter import Language, Parser
except ImportError:
    Language = None
    Parser = None

# Language grammar import mapping
_LANGUAGE_GRAMMARS: dict[str, tuple] = {}

try:
    from tree_sitter_python import language as python_language

    _LANGUAGE_GRAMMARS["python"] = (python_language,)
except ImportError:
    pass

try:
    from tree_sitter_javascript import language as javascript_language

    _LANGUAGE_GRAMMARS["javascript"] = (javascript_language,)
except ImportError:
    pass

try:
    from tree_sitter_typescript import language_typescript as typescript_language

    _LANGUAGE_GRAMMARS["typescript"] = (typescript_language,)
except ImportError:
    pass

# Node types that represent function-like constructs per language
_FUNCTION_NODES: dict[str, set[str]] = {
    "python": {
        "function_definition",
        "async_function_definition",
    },
    "javascript": {
        "function_declaration",
        "arrow_function",
        "function_expression",
        "method_definition",
        "generator_function_declaration",
    },
    "typescript": {
        "function_declaration",
        "arrow_function",
        "function_expression",
        "method_definition",
        "generator_function_declaration",
    },
}

_CLASS_NODES: dict[str, set[str]] = {
    "python": {"class_definition"},
    "javascript": {"class_declaration", "class_expression"},
    "typescript": {"class_declaration", "class_expression"},
}


def _init_parser(language: str) -> Parser | None:
    """Create a tree-sitter Parser for the given language."""
    if Parser is None or Language is None:
        return None

    grammars = _LANGUAGE_GRAMMARS.get(language)
    if not grammars:
        return None

    try:
        lang = Language(*grammars[0])
        parser = Parser()
        parser.set_language(lang)
        return parser
    except Exception:
        return None


def _get_node_text(source_bytes: bytes, node) -> str:
    """Extract text for a tree-sitter node."""
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _get_docstring(source_bytes: bytes, node, language: str) -> str:
    """Extract docstring/comment block preceding a node."""
    # Get the leading comments / docstring
    prev_sibling = node.prev_sibling
    if prev_sibling is not None:
        text = _get_node_text(source_bytes, prev_sibling).strip()
        if language == "python" and '"""' in text:
            return text
        if text.startswith(("//", "/*", "#")):
            return text

    # Also check first child for docstring (python: suite -> expression_statement -> string)
    if language == "python":
        try:
            suite = node.child_by_field_name("body")
            if suite:
                first_stmt = suite.child(0)
                if first_stmt and first_stmt.type == "expression_statement":
                    expr = first_stmt.child(0)
                    if expr and expr.type == "string":
                        return _get_node_text(source_bytes, expr).strip('"').strip("'")
        except Exception:
            pass

    return ""


def _chunk_lines(source_bytes: bytes, node) -> tuple[int, int]:
    """Get (start_line, end_line) 1-indexed for a node."""
    start = node.start_point[0] + 1
    end = node.end_point[0] + 1
    return start, end


def _extract_chunks_from_tree(
    source_bytes: bytes,
    tree,
    file_path: str,
    language: str,
    content: str,
) -> list[Chunk]:
    """Walk the AST and extract function/class chunks."""
    chunks: list[Chunk] = []
    root = tree.root_node

    func_nodes = _FUNCTION_NODES.get(language, set())
    class_nodes = _CLASS_NODES.get(language, set())

    def _walk(node):
        if node.type in func_nodes:
            name_node = node.child_by_field_name("name")
            name = _get_node_text(source_bytes, name_node) if name_node else "anonymous"
            start, end = _chunk_lines(source_bytes, node)
            docstring = _get_docstring(source_bytes, node, language)
            code = _get_node_text(source_bytes, node)

            chunks.append(
                Chunk(
                    file_path=file_path,
                    language=language,
                    start_line=start,
                    end_line=end,
                    chunk_type="function",
                    name=name,
                    content=code,
                    docstring=docstring,
                )
            )
            # Don't recurse into function bodies — functions are the leaf unit
            return

        if node.type in class_nodes:
            name_node = node.child_by_field_name("name")
            name = _get_node_text(source_bytes, name_node) if name_node else "anonymous"
            start, end = _chunk_lines(source_bytes, node)
            docstring = _get_docstring(source_bytes, node, language)
            code = _get_node_text(source_bytes, node)

            chunks.append(
                Chunk(
                    file_path=file_path,
                    language=language,
                    start_line=start,
                    end_line=end,
                    chunk_type="class",
                    name=name,
                    content=code,
                    docstring=docstring,
                )
            )

        # Recurse into children (to find nested functions and methods)
        for child in node.children:
            _walk(child)

    _walk(root)

    return chunks


def _fallback_chunk_by_lines(
    content: str,
    file_path: str,
    language: str,
    chunk_size: int = 100,
    chunk_overlap: int = 20,
) -> list[Chunk]:
    """Fallback chunking when tree-sitter is unavailable or fails."""
    lines = content.split("\n")
    chunks: list[Chunk] = []
    total = len(lines)

    # Try to detect top-level functions/classes via simple regex
    import re

    # Python: def/class at line start
    # JS/TS: function/class/const/let/var at line start
    patterns = {
        "python": re.compile(r"^(async\s+)?(def|class)\s+(\w+)"),
        "javascript": re.compile(
            r"^(export\s+)?(function|class|const\s+\w+\s*=\s*(\(|async)|let\s+\w+\s*=\s*(\(|async))"
        ),
        "typescript": re.compile(
            r"^(export\s+)?(function|class|const\s+\w+\s*=\s*(\(|async)|let\s+\w+\s*=\s*(\(|async))"
        ),
    }
    pattern = patterns.get(language, re.compile(r"^(def|class|function)\s+(\w+)"))

    i = 0
    while i < total:
        # Look for a function/class definition starting at line i
        match = None
        for j in range(i, min(i + 20, total)):
            m = pattern.match(lines[j])
            if m:
                match = m
                start_idx = j
                break

        if match:
            name = match.group(2) if match.lastindex >= 2 else match.group(0)
            chunk_type = "function"
            if match.group(0).startswith("class"):
                chunk_type = "class"
            # Find end: next def/class at same indent level or EOF
            end_idx = start_idx + 1
            indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
            while end_idx < total:
                stripped = lines[end_idx].strip()
                if stripped and not stripped.startswith(("#", "//", "/*", "*")):
                    line_indent = len(lines[end_idx]) - len(lines[end_idx].lstrip())
                    if line_indent <= indent and (
                        pattern.match(stripped) or stripped.startswith(("def ", "class ", "function ", "export "))
                    ):
                        break
                end_idx += 1
            end_idx = max(end_idx, start_idx + 1)
            code = "\n".join(lines[start_idx:end_idx])

            # Extract leading docstring/comments
            docstring = ""
            for k in range(start_idx + 1, min(end_idx, start_idx + 10)):
                dl = lines[k].strip()
                if dl.startswith(('"""', "'''", "//", "/*", "*", "#")):
                    docstring += dl + "\n"
                else:
                    break
            docstring = docstring.strip()

            chunks.append(
                Chunk(
                    file_path=file_path,
                    language=language,
                    start_line=start_idx + 1,
                    end_line=end_idx,
                    chunk_type=chunk_type,
                    name=name,
                    content=code,
                    docstring=docstring,
                )
            )
            i = end_idx
        else:
            # No function/class found — slide window
            end = min(i + chunk_size, total)
            code = "\n".join(lines[i:end])
            chunks.append(
                Chunk(
                    file_path=file_path,
                    language=language,
                    start_line=i + 1,
                    end_line=end,
                    chunk_type="module",
                    name=file_path.split("/")[-1],
                    content=code,
                    docstring="",
                )
            )
            i = end - chunk_overlap if end < total else total

    return chunks


def chunk_file(
    content: str,
    file_path: str,
    language: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Chunk]:
    """Chunk a single source file into function/class-level pieces.

    Uses tree-sitter AST parsing when available, falls back to line-based
    heuristics otherwise.
    """
    source_bytes = content.encode("utf-8")

    parser = _init_parser(language)
    if parser is not None:
        try:
            tree = parser.parse(source_bytes)
            chunks = _extract_chunks_from_tree(
                source_bytes, tree, file_path, language, content
            )
            if chunks:
                return chunks
        except Exception:
            pass

    # Fallback
    return _fallback_chunk_by_lines(content, file_path, language, chunk_size, chunk_overlap)
