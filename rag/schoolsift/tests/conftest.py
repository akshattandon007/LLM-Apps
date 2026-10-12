"""Shared fixtures: synthetic school documents generated on the fly."""
from __future__ import annotations

from pathlib import Path

import fitz
import pytest


def _write_pdf(path: Path, pages: list[list[str]]) -> None:
    """Create a searchable PDF from lists of text lines."""
    doc = fitz.open()
    try:
        for lines in pages:
            page = doc.new_page()
            y = 72
            for line in lines:
                page.insert_text((72, y), line, fontsize=11)
                y += 16
        doc.save(path)
    finally:
        doc.close()


@pytest.fixture
def newsletter_pdf(tmp_path: Path) -> Path:
    """A 2-page school newsletter."""
    path = tmp_path / "newsletter-october.pdf"
    _write_pdf(path, [
        [
            "Maplewood Elementary School Newsletter - October 2026",
            "",
            "Welcome back, families!",
            "The annual Book Fair will be held on October 14 in the school library.",
            "Students may browse during library time all week.",
        ],
        [
            "The Fall Family Picnic is scheduled for Saturday, October 24 at the park.",
            "Please bring a dish to share.",
            "School picture day is November 3.",
            "Lunch menus for the month are attached.",
        ],
    ])
    return path


@pytest.fixture
def permission_slip_pdf(tmp_path: Path) -> Path:
    """A one-page science-fair permission slip with a deadline."""
    path = tmp_path / "permission-slip-science-fair.pdf"
    _write_pdf(path, [
        [
            "Science Fair Permission Slip",
            "",
            "The Maplewood Science Fair will take place on November 20.",
            "Please complete and return this slip to your child's teacher by October 28.",
            "Student name: ______  Room: ______",
            "Parent signature: ______",
            "Check one: [ ] I can volunteer   [ ] My child will attend.",
            "Questions? Email Mrs. Alvarez at alvarez@maplewood.example.",
        ],
    ])
    return path


@pytest.fixture
def sample_folder(tmp_path: Path, newsletter_pdf: Path,
                  permission_slip_pdf: Path) -> Path:
    """A realistic parent's school-document folder."""
    (tmp_path / "pta-notes.txt").write_text(
        "PTA meeting notes - October 5\n"
        "\n"
        "Room parent signup is due by November 14.\n"
        "The winter bakesale is planned for December 5.\n"
        "Volunteers needed for the bakesale setup on October 13.\n",
        encoding="utf-8",
    )
    return tmp_path