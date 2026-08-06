"""Earworm — CLI ingestion pipeline.

Ingest transcripts from RSS feeds, text files (plain/SRT/VTT), or audio files.
Usage:
    python ingest.py rss <feed_url> <show_name>
    python ingest.py file <path> <show_name> <episode_title> [--date YYYY-MM-DD]
    python ingest.py audio <path> <show_name> <episode_title> [--date YYYY-MM-DD]
    python ingest.py stats
    python ingest.py rebuild-index
"""

import argparse
import os
import sys
from datetime import datetime

import feedparser

from models import (
    get_db,
    init_db,
    insert_show,
    insert_episode,
    clear_chunks_for_episode,
    insert_chunk,
    list_shows,
    list_episodes,
    stats as db_stats,
)
from chunker import chunk_transcript
from embedder import (
    load_model,
    load_index,
    save_index,
    load_id_map,
    save_id_map,
    create_index,
    embed_texts,
    rebuild_index_from_db,
)


def parse_srt(text: str) -> str:
    """Extract plain text from SRT subtitle format."""
    import re

    # Remove index numbers and timestamps
    text = re.sub(r"^\d+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(
        r"^\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[.,]\d{3}\s*$",
        "",
        text,
        flags=re.MULTILINE,
    )
    # Collapse blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_vtt(text: str) -> str:
    """Extract plain text from VTT subtitle format."""
    import re

    # Remove WEBVTT header
    text = re.sub(r"^WEBVTT.*\n", "", text, flags=re.IGNORECASE)
    # Remove timestamps and any inline styling
    text = re.sub(
        r"^\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[.,]\d{3}.*$",
        "",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_transcript(filepath: str) -> str:
    """Load and parse a transcript file (txt, srt, vtt)."""
    ext = os.path.splitext(filepath)[1].lower()
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()

    if ext == ".srt":
        return parse_srt(raw)
    elif ext == ".vtt":
        return parse_vtt(raw)
    else:
        return raw.strip()


def transcribe_audio(filepath: str) -> str:
    """Transcribe an audio file using whisper."""
    try:
        import whisper

        model = whisper.load_model("base")
        result = model.transcribe(filepath)
        return result["text"].strip()
    except ImportError:
        print(
            "ERROR: openai-whisper not installed. Install with: pip install openai-whisper"
        )
        sys.exit(1)


def process_transcript(
    conn, show_id: int, episode_id: int, transcript: str, model=None
):
    """Chunk and embed a transcript, storing chunks in DB and FAISS."""
    if model is None:
        model = load_model()

    # Clear existing chunks
    clear_chunks_for_episode(conn, episode_id)

    # Chunk
    chunks = chunk_transcript(transcript, model=model)
    if not chunks:
        print("  No chunks produced — transcript may be too short.")
        return

    # Embed all chunks
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts, model=model)

    # Store chunks in DB
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        insert_chunk(
            conn,
            episode_id=episode_id,
            chunk_index=i,
            text=chunk["text"],
            start_char=chunk["start_char"],
            end_char=chunk["end_char"],
            token_count=len(chunk["text"].split()),
        )

    # Update FAISS index incrementally
    index = load_index()
    id_map = load_id_map()

    if index is None:
        index = create_index(embeddings)
    else:
        index.add(embeddings)

    # Update ID map
    cur = conn.execute(
        "SELECT id FROM chunks WHERE episode_id = ? ORDER BY chunk_index",
        (episode_id,),
    )
    chunk_ids = [row["id"] for row in cur.fetchall()]
    start_pos = len(id_map)
    for j, cid in enumerate(chunk_ids):
        id_map[start_pos + j] = cid

    save_index(index)
    save_id_map(id_map)
    print(f"  Indexed {len(chunks)} chunks ({index.ntotal} total in index).")


def cmd_rss(args):
    """Ingest episodes from an RSS feed."""
    print(f"Ingesting RSS feed: {args.feed_url}")
    feed = feedparser.parse(args.feed_url)
    if not feed.entries:
        print("  No episodes found in feed.")
        return

    conn = get_db()
    init_db(conn)
    model = load_model()

    show_id = insert_show(conn, args.show_name, args.feed_url)
    print(f"  Show: {args.show_name} (id={show_id})")

    count = 0
    for entry in feed.entries:
        title = entry.get("title", "Untitled")
        desc = entry.get("description", "") or entry.get("summary", "")
        pub_date = entry.get("published", None)
        audio_url = None
        for link in entry.get("links", []):
            if link.get("type", "").startswith("audio"):
                audio_url = link.get("href")
                break

        # Use description as transcript if it has substantial text
        transcript = ""
        if desc and len(desc) > 100:
            # Strip HTML
            import re

            transcript = re.sub(r"<[^>]+>", "", desc).strip()

        if not transcript:
            print(f"  Skipping '{title}' — no transcript content in feed.")
            continue

        ep_id = insert_episode(
            conn,
            show_id=show_id,
            title=title,
            description=desc[:500] if desc else None,
            pub_date=pub_date,
            audio_url=audio_url,
            source_file=None,
            transcript=transcript,
        )
        process_transcript(conn, show_id, ep_id, transcript, model=model)
        count += 1
        print(f"  Ingested: {title}")

    print(f"\nDone. Ingested {count} episodes.")


def cmd_file(args):
    """Ingest a transcript file."""
    if not os.path.exists(args.path):
        print(f"ERROR: File not found: {args.path}")
        sys.exit(1)

    print(f"Ingesting file: {args.path}")
    transcript = load_transcript(args.path)

    conn = get_db()
    init_db(conn)
    model = load_model()

    show_id = insert_show(conn, args.show_name)
    date = args.date or datetime.now().strftime("%Y-%m-%d")
    ep_id = insert_episode(
        conn,
        show_id=show_id,
        title=args.episode_title,
        description=None,
        pub_date=date,
        audio_url=None,
        source_file=os.path.basename(args.path),
        transcript=transcript,
    )
    process_transcript(conn, show_id, ep_id, transcript, model=model)
    print(f"  Ingested: {args.episode_title}")


def cmd_audio(args):
    """Transcribe and ingest an audio file."""
    if not os.path.exists(args.path):
        print(f"ERROR: File not found: {args.path}")
        sys.exit(1)

    print(f"Transcribing: {args.path}")
    transcript = transcribe_audio(args.path)

    conn = get_db()
    init_db(conn)
    model = load_model()

    show_id = insert_show(conn, args.show_name)
    date = args.date or datetime.now().strftime("%Y-%m-%d")
    ep_id = insert_episode(
        conn,
        show_id=show_id,
        title=args.episode_title,
        description=None,
        pub_date=date,
        audio_url=None,
        source_file=os.path.basename(args.path),
        transcript=transcript,
    )
    process_transcript(conn, show_id, ep_id, transcript, model=model)
    print(f"  Ingested: {args.episode_title}")


def cmd_stats(args):
    """Show database statistics."""
    conn = get_db()
    init_db(conn)
    s = db_stats(conn)
    index = load_index()
    print(f"Shows:     {s['shows']}")
    print(f"Episodes:  {s['episodes']}")
    print(f"Chunks:    {s['chunks']}")
    print(f"FAISS idx: {index.ntotal if index else 0} vectors")


def cmd_rebuild(args):
    """Rebuild the FAISS index from scratch."""
    print("Rebuilding FAISS index from database...")
    conn = get_db()
    init_db(conn)
    index, id_map = rebuild_index_from_db(conn)
    print(f"Done. {index.ntotal} vectors indexed.")


def main():
    parser = argparse.ArgumentParser(description="Earworm — podcast transcript ingestion")
    sub = parser.add_subparsers(dest="command", required=True)

    # RSS
    p_rss = sub.add_parser("rss", help="Ingest episodes from an RSS feed")
    p_rss.add_argument("feed_url", help="RSS feed URL")
    p_rss.add_argument("show_name", help="Name of the show")
    p_rss.set_defaults(func=cmd_rss)

    # File
    p_file = sub.add_parser("file", help="Ingest a transcript file (txt, srt, vtt)")
    p_file.add_argument("path", help="Path to transcript file")
    p_file.add_argument("show_name", help="Name of the show")
    p_file.add_argument("episode_title", help="Episode title")
    p_file.add_argument("--date", help="Publication date (YYYY-MM-DD)")
    p_file.set_defaults(func=cmd_file)

    # Audio
    p_audio = sub.add_parser("audio", help="Transcribe and ingest an audio file")
    p_audio.add_argument("path", help="Path to audio file")
    p_audio.add_argument("show_name", help="Name of the show")
    p_audio.add_argument("episode_title", help="Episode title")
    p_audio.add_argument("--date", help="Publication date (YYYY-MM-DD)")
    p_audio.set_defaults(func=cmd_audio)

    # Stats
    p_stats = sub.add_parser("stats", help="Show database statistics")
    p_stats.set_defaults(func=cmd_stats)

    # Rebuild
    p_rebuild = sub.add_parser("rebuild-index", help="Rebuild FAISS index from DB")
    p_rebuild.set_defaults(func=cmd_rebuild)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()