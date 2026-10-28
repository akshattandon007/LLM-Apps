"""Ingest an MBOX file — parse, chunk, embed, and store in ChromaDB."""

import hashlib
import mailbox
import os
import re
import sys
from pathlib import Path
from typing import Generator

from .models import EmailChunk, EmailMetadata

# ── Config ──────────────────────────────────────────────────────────────────

DEFAULT_CHUNK_SIZE = 800  # characters per chunk (approx paragraph)
DEFAULT_CHUNK_OVERLAP = 100

# ── MBOX parsing ────────────────────────────────────────────────────────────


def extract_text_from_email(msg: mailbox.mboxMessage) -> str:
    """Extract plain text body from an email message (handles multipart)."""
    if msg.is_multipart():
        parts = []
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        parts.append(payload.decode("utf-8", errors="replace"))
                    except Exception:
                        parts.append(payload.decode("latin-1", errors="replace"))
        return "\n".join(parts)
    payload = msg.get_payload(decode=True)
    if payload:
        try:
            return payload.decode("utf-8", errors="replace")
        except Exception:
            return payload.decode("latin-1", errors="replace")
    return ""


def parse_mbox(path: str | Path) -> Generator[EmailMetadata, None, None]:
    """Yield EmailMetadata for every message in an mbox file."""
    mbox = mailbox.mbox(str(path))
    for msg in mbox:
        mid = msg.get("Message-ID", "") or hashlib.md5(
            (msg.get("Subject", "") + msg.get("Date", "")).encode()
        ).hexdigest()
        labels_raw = msg.get("X-Gmail-Labels", msg.get("X-Keywords", ""))
        labels = [l.strip() for l in labels_raw.split(",") if l.strip()] if labels_raw else []
        yield EmailMetadata(
            message_id=mid,
            subject=msg.get("Subject", "(no subject)"),
            sender=msg.get("From", "(unknown)"),
            date=msg.get("Date", "(no date)"),
            to_=msg.get("To", ""),
            cc=msg.get("Cc", ""),
            labels=labels,
        )


# ── Chunking ────────────────────────────────────────────────────────────────


def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks at paragraph/sentence boundaries."""
    # Normalise whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text).strip()
    if not text:
        return []

    paragraphs = re.split(r"\n\n+", text)
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 2 <= chunk_size:
            current = (current + "\n\n" + para).strip() if current else para
        else:
            if current:
                chunks.append(current)
            # Try sentence-level splitting for long paragraphs
            if len(para) > chunk_size:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                buf = ""
                for sent in sentences:
                    if len(buf) + len(sent) + 1 <= chunk_size:
                        buf = (buf + " " + sent).strip() if buf else sent
                    else:
                        if buf:
                            chunks.append(buf)
                        buf = sent
                if buf:
                    chunks.append(buf)
            else:
                current = para

    if current:
        chunks.append(current)

    # Apply overlap by merging neighbouring chunks
    if overlap > 0 and len(chunks) > 1:
        merged = [chunks[0]]
        for i in range(1, len(chunks)):
            prev = merged[-1]
            # take last `overlap` chars of previous chunk as prefix
            prefix = prev[-overlap:] if len(prev) > overlap else prev
            merged.append((prefix + "\n" + chunks[i]).strip())
        chunks = merged

    return chunks


def chunk_emails(
    mbox_path: str | Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> Generator[EmailChunk, None, None]:
    """Parse an mbox file and yield EmailChunk objects."""
    mbox = mailbox.mbox(str(mbox_path))
    for idx, msg in enumerate(mbox):
        meta_msg_id = msg.get("Message-ID", "") or hashlib.md5(
            (msg.get("Subject", "") + msg.get("Date", "")).encode()
        ).hexdigest()
        labels_raw = msg.get("X-Gmail-Labels", msg.get("X-Keywords", ""))
        labels = [l.strip() for l in labels_raw.split(",") if l.strip()] if labels_raw else []
        meta = EmailMetadata(
            message_id=meta_msg_id,
            subject=msg.get("Subject", "(no subject)"),
            sender=msg.get("From", "(unknown)"),
            date=msg.get("Date", "(no date)"),
            to_=msg.get("To", ""),
            cc=msg.get("Cc", ""),
            labels=labels,
        )
        body = extract_text_from_email(msg)
        if not body:
            continue

        text_chunks = chunk_text(body, chunk_size, overlap)
        for ci, tc in enumerate(text_chunks):
            unique = hashlib.md5(f"{meta_msg_id}:{ci}:{tc[:50]}".encode()).hexdigest()
            yield EmailChunk(
                metadata=meta,
                chunk_index=ci,
                text=tc,
                chunk_id=unique,
            )