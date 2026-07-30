"""The Claude-driven agent loop.

Flow:
1. User asks a question or issues a command.
2. We send the message to Claude with the tool specs attached.
3. If Claude emits `tool_use` blocks, we run them and feed the results back.
4. Loop until Claude returns `stop_reason == "end_turn"`, then print the answer.

Design notes:
- We use the stable `anthropic.Anthropic().messages.create()` API.
- We pass a strong system prompt that tells Claude *how* to use the tools,
  specifically: always cite pages, prefer multiple narrow searches over
  one vague one, and never append content without clear user intent.
- `max_agent_turns` guards against runaway loops.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import anthropic

from .tools import TOOL_SPECS, ToolRunner

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """\
You are a Notion Agent: a careful, concise assistant that reads, searches, and \
writes to a user's Notion workspace via a fixed set of tools.

# Tools available to you
- `read_page(page_id)`: fetch the full contents of a page the user specifies.
- `search_workspace(query, top_k?)`: semantic search over a local vector index \
of all pages the integration can see. Prefer this over any other retrieval.
- `append_section(page_id, heading, body?)`: append a new H2 section to a page.

# How to answer well

1. **Decompose cross-page questions into multiple focused searches.** A question \
like "top risks for Project Phoenix based on my meeting notes and market articles" \
should become several searches: one for "Project Phoenix risks", one for "Project \
Phoenix meeting notes", one for "market trends" — then you synthesise.

2. **Cite every factual claim with the page title.** When you draw on retrieved \
chunks, name the page. Example: "According to *Q4 Planning* ...". If a claim \
is supported by multiple pages, cite all of them.

3. **Never hallucinate page IDs.** If the user hasn't given you a page ID and \
you don't have one from a tool result, search first.

4. **Confirm before writing.** For `append_section`, only act on an explicit \
write instruction from the user ("add a Next Steps section to ...", "append a \
summary to page X"). If the target page is ambiguous, ask.

5. **Be concise.** Favour tight prose and short bulleted lists over sprawling \
explanations. Users are busy.

6. **Admit gaps.** If the vector index has no relevant results, say so and \
suggest running `notion-agent index` to refresh it — don't make things up.
"""


@dataclass
class AgentResult:
    """What the CLI prints at the end of a run."""

    text: str
    turns: int
    tool_calls: list[dict[str, Any]]


class NotionAgent:
    """Stateless agent wrapper — one instance per CLI invocation."""

    def __init__(
        self,
        api_key: str,
        model: str,
        tool_runner: ToolRunner,
        max_turns: int = 10,
        max_tokens: int = 4096,
    ) -> None:
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.tool_runner = tool_runner
        self.max_turns = max_turns
        self.max_tokens = max_tokens

    def run(self, user_message: str, verbose: bool = False) -> AgentResult:
        """Drive a single user request to completion."""
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": user_message}
        ]
        tool_calls_log: list[dict[str, Any]] = []

        for turn in range(1, self.max_turns + 1):
            logger.debug("Agent turn %d", turn)
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=SYSTEM_PROMPT,
                tools=TOOL_SPECS,
                messages=messages,
            )

            # If Claude is done, extract the final text and return.
            if response.stop_reason == "end_turn":
                final_text = _extract_text(response.content)
                # Append the assistant's final turn to the history for completeness.
                messages.append({"role": "assistant", "content": response.content})
                return AgentResult(text=final_text, turns=turn, tool_calls=tool_calls_log)

            # Otherwise, Claude wants to use tools. Run each one and collect results.
            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results: list[dict[str, Any]] = []

                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    if verbose:
                        print(f"  → Tool call: {block.name}({_short(block.input)})")
                    logger.info("Tool call: %s(%s)", block.name, block.input)
                    output = self.tool_runner.run(block.name, dict(block.input))
                    tool_calls_log.append({
                        "name": block.name,
                        "input": dict(block.input),
                        "output_preview": output[:200],
                    })
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output,
                    })

                messages.append({"role": "user", "content": tool_results})
                continue

            # Any other stop_reason (e.g. "max_tokens") — surface what we have.
            logger.warning("Unexpected stop_reason: %s", response.stop_reason)
            final_text = _extract_text(response.content) or (
                f"(Agent stopped early with stop_reason={response.stop_reason})"
            )
            return AgentResult(text=final_text, turns=turn, tool_calls=tool_calls_log)

        # Hit the turn cap.
        return AgentResult(
            text=(
                f"(Agent hit max_turns={self.max_turns} without completing. "
                "Try a more specific question or raise the limit.)"
            ),
            turns=self.max_turns,
            tool_calls=tool_calls_log,
        )


def _extract_text(content_blocks: list[Any]) -> str:
    """Pull the `text` out of Claude's response blocks, skipping tool_use blocks."""
    parts: list[str] = []
    for block in content_blocks:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "\n".join(parts).strip()


def _short(d: dict[str, Any], limit: int = 80) -> str:
    """Compact one-line rendering of a tool-input dict for verbose logging."""
    s = ", ".join(f"{k}={v!r}" for k, v in d.items())
    return s if len(s) <= limit else s[: limit - 1] + "…"
