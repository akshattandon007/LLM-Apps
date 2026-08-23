from __future__ import annotations

from src.models import EraTransformation, PhotoTimeMachineOutput


# ── Terminal / ANSI helpers ──────────────────────────────────────────────────


def _accent_block(hex_colour: str) -> str:
    """Return a small ANSI true-colour block for a hex colour."""
    r, g, b = int(hex_colour[1:3], 16), int(hex_colour[3:5], 16), int(
        hex_colour[5:7], 16
    )
    return f"\033[48;2;{r};{g};{b}m  \033[0m"


def _bold(text: str) -> str:
    return f"\033[1m{text}\033[0m"


def _yellow(text: str) -> str:
    return f"\033[93m{text}\033[0m"


def _cyan(text: str) -> str:
    return f"\033[96m{text}\033[0m"


# ── Gallery builder ──────────────────────────────────────────────────────────


def build_gallery(output: PhotoTimeMachineOutput) -> str:
    """Render the full gallery as a terminal-friendly string.

    Parameters
    ----------
    output:
        The structured result from a Photo Time Machine run.

    Returns
    -------
    str
        Nicely formatted gallery text ready for terminal display.
    """
    lines: list[str] = [
        "",
        _bold("╔══════════════════════════════════════════════════╗"),
        _bold("║         📸  PHOTO TIME MACHINE  📸              ║"),
        _bold("╚══════════════════════════════════════════════════╝"),
        "",
        f"  Original: {_yellow(output.original_name)}",
        "",
        "━━━  Era Gallery ━━━",
        "",
    ]

    for era_out in output.eras:
        block = _render_era_card(era_out)
        lines.append(block)

    lines.append("")
    lines.append(
        _cyan(
            output.gallery_message
            or "See yourself through every decade — from the 1950s to the 2050s!"
        )
    )
    lines.append("")

    return "\n".join(lines)


def _render_era_card(era: EraTransformation) -> str:
    """Render a single era card as a boxed block of text."""
    lines = [
        _bold(f"  ╭── {era.title} ──╮"),
        f"  │                        │",
        f"  │  {era.description}",
        f"  │                        │",
        f"  │  {_cyan(era.caption)}",
        f"  │  {_yellow(era.tagline)}",
        f"  │                        │",
        f"  ╰────────────────────────╯",
    ]
    return "\n".join(lines)


def build_photo_time_machine_output(
    photo_path: str,
    transformations: list[EraTransformation],
) -> PhotoTimeMachineOutput:
    """Assemble the full output model from a list of transformations."""
    from src.eras import all_eras

    # Use the first era's tagline as a gallery message
    gallery_msg = (
        f"✨ See yourself through every decade — "
        f"from the {transformations[0].era} to the {transformations[-1].era}! ✨"
    )

    return PhotoTimeMachineOutput(
        original_name=photo_path,
        eras=transformations,
        gallery_message=gallery_msg,
    )