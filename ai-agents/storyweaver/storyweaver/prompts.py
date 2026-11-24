"""Prompt templates for the story generation engine."""

# System prompt that sets the LLM's role as a storyteller
SYSTEM_PROMPT = """You are an expert interactive fiction writer. Your job is to write
engaging, vivid narrative chapters for a branching story. Each response MUST be valid JSON
with the following structure — nothing else, no markdown, no commentary:

{
  "narrative": "The story text for this chapter, 200-400 words, immersive and descriptive.",
  "choices": [
    {"text": "Choice option 1 (10-60 chars)", "next_node_id": <next_id_int>},
    {"text": "Choice option 2", "next_node_id": <next_id_int>},
    {"text": "Choice option 3", "next_node_id": <next_id_int>}
  ]
}

Rules:
- Provide exactly 3 choices, each opening a different direction.
- Choices must feel meaningfully different — not just "yes/no" variants.
- Keep the narrative 200-400 words per chapter.
- Maintain narrative coherence across the whole story arc.
- The story should feel like it can reach a satisfying conclusion within ~5-8 chapters.
- Write in present tense, second person ("You walk into the room...").
- Each chapter should end on a mini-cliffhanger or decision point.
- next_node_id for the FIRST chapter is always 1. Each subsequent chapter uses the
  next available integer (2, 3, 4...)."""


FIRST_CHAPTER_PROMPT = """Write the first chapter of an interactive fiction story.

Title: {title}
Genre: {genre}
Setting: {setting}
Characters: {characters}
Premise: {premise}

Start with a strong hook that establishes the mood and stakes. End with 3 choices that
set up distinct narrative branches.

Respond with the JSON format specified."""


NEXT_CHAPTER_PROMPT = """Continue the interactive fiction story.

Title: {title}
Genre: {genre}
Recent story history:
{narration_history}

The reader chose: "{chosen_text}"

Write the next chapter of the story that follows from that choice.
Keep the same tone, style, and narrative voice established in previous chapters.
End with 3 new choices.

Respond with the JSON format specified."""


SUMMARY_PROMPT = """The reader has reached the end of their interactive fiction journey
for the story "{title}" in genre "{genre}".

They experienced {chapter_count} chapters. Please generate a brief narrative epilogue
(100-200 words) that provides a satisfying conclusion to the story, tying together the
threads from the chapters they experienced.

Respond with ONLY the epilogue text — no JSON, no formatting."""
