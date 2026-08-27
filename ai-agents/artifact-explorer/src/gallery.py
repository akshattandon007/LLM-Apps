"""Format an Artifact as a gallery-style output card."""

from .models import Artifact, ArtifactCard

CARD_TEMPLATE = """
┌──────────────────────────────────────────────────────────────┐
│  {title:^60}  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  {name}                                 │
│  {category_line}                      │
│                                                              │
│  {description}            │
│                                                              │
│  ═══════════════════  ORIGIN & ERA  ════════════════════════  │
│                                                              │
│  Origin:  {origin}                     │
│  Era:     {era}                                      │
│                                                              │
│  ════════════════════  THE STORY  ═════════════════════════  │
│                                                              │
│  {history} │
│                                                              │
│  ═══════════════════  CULTURAL SIGNIFICANCE  ═══════════════  │
│                                                              │
│  {cultural} │
│                                                              │
│  ═══════════════════  PRACTICAL USES  ═════════════════════  │
│                                                              │
│  {practical} │
│                                                              │
│  ════════════════════  FUN FACTS  ═════════════════════════  │
│                                                              │
{facts_block}
└──────────────────────────────────────────────────────────────┘
"""


def _wrap(text: str, width: int = 56) -> str:
    """Word-wrap text to fit in the card body."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for w in words:
        test = f"{current} {w}".strip()
        if len(test) <= width:
            current = test
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return "\n".join(f"  {line:<{width}}" for line in lines)


def _wrap_facts(facts: list[str], width: int = 54) -> str:
    """Format fun facts as bullet points."""
    blocks: list[str] = []
    for i, fact in enumerate(facts, 1):
        lines: list[str] = []
        current = ""
        words = fact.split()
        for w in words:
            test = f"{current} {w}".strip()
            if len(test) <= width:
                current = test
            else:
                lines.append(current)
                current = w
        if current:
            lines.append(current)
        block = "\n".join(f"  •  {line:<{width}}" if j == 0 else f"     {line:<{width}}" for j, line in enumerate(lines))
        blocks.append(block)
    return "\n".join(blocks)


def format_card(artifact: Artifact) -> ArtifactCard:
    """Render an Artifact as a rich text card."""
    title = f"🪙  ARTIFACT EXPLORER — {artifact.name.upper()}  🪙"
    name_line = f"📛  {artifact.name}"
    cat_line = f"🏷️  {artifact.category}"
    description = _wrap(artifact.description, width=52)
    origin = artifact.origin
    era = artifact.era
    history = _wrap(artifact.history, width=54)
    cultural = _wrap(artifact.cultural_significance, width=54)
    practical = _wrap(artifact.practical_uses, width=54)
    facts_block = _wrap_facts(artifact.fun_facts, width=54)

    body = CARD_TEMPLATE.format(
        title=title,
        name=name_line,
        category_line=cat_line,
        description=description,
        origin=origin,
        era=era,
        history=history,
        cultural=cultural,
        practical=practical,
        facts_block=facts_block,
    )

    return ArtifactCard(
        title=title,
        body=body,
        tags=[artifact.category, artifact.name.split()[0]],
    )


def print_card(artifact: Artifact) -> None:
    """Print the card to stdout."""
    card = format_card(artifact)
    print(card.body)