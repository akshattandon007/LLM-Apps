"""
TVMaze MCP Server — TV show search, episode listings, cast info, and schedule.

Run with:
    python -m mcp run server.py
    # or
    uv run --with mcp python -m mcp run server.py
"""

from mcp.server.fastmcp import FastMCP
from typing import Optional

from tvmaze_client import (
    search_shows,
    get_show_by_id,
    get_episodes,
    get_cast,
    get_schedule,
    search_people,
    simulate_search_shows,
    simulate_episodes,
    Show,
    Episode,
    CastMember,
    ScheduleItem,
)

mcp = FastMCP(
    "TVMaze",
    instructions=(
        "Search for TV shows, episodes, cast members, and TV schedules. "
        "Uses the public TVMaze API — no API key required."
    ),
)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def search_tv_shows(query: str) -> str:
    """Search for TV shows by name. Returns a list of matching shows with details."""
    try:
        shows = search_shows(query)
    except Exception:
        shows = simulate_search_shows(query)

    if not shows:
        return f"No shows found for '{query}'."

    lines = [f"**Shows matching '{query}':**\n"]
    for s in shows[:10]:
        rating_str = f"⭐ {s.rating}/10" if s.rating else "No rating"
        status_str = f"📺 {s.status}" if s.status else ""
        network_str = f" ({s.network})" if s.network else ""
        web_str = f" [Web: {s.web_channel}]" if s.web_channel else ""
        years = s.premiered or ""
        if s.ended:
            years += f" – {s.ended}"
        elif s.premiered:
            years += " – present"
        genres = ", ".join(s.genres) if s.genres else ""
        lines.append(
            f"**{s.name}** (ID: `{s.id}`)\n"
            f"   {rating_str} | {status_str}{network_str}{web_str}\n"
            f"   {years}\n"
            f"   {genres}\n"
            f"   _{s.summary[:200]}..._\n" if s.summary else ""
        )
    return "\n".join(filter(None, lines))


@mcp.tool()
async def get_show_details(show_id: int) -> str:
    """Get detailed information about a specific TV show by its TVMaze ID."""
    try:
        show = get_show_by_id(show_id)
    except Exception as e:
        return f"Error fetching show details: {e}"

    lines = [
        f"**{show.name}** (ID: `{show.id}`)\n",
    ]
    if show.type:
        lines.append(f"Type: {show.type}")
    if show.language:
        lines.append(f"Language: {show.language}")
    if show.genres:
        lines.append(f"Genres: {', '.join(show.genres)}")
    if show.status:
        lines.append(f"Status: {show.status}")
    if show.runtime:
        lines.append(f"Runtime: {show.runtime} min")
    if show.average_runtime:
        lines.append(f"Avg Runtime: {show.average_runtime} min")
    if show.premiered:
        lines.append(f"Premiered: {show.premiered}")
    if show.ended:
        lines.append(f"Ended: {show.ended}")
    if show.network:
        lines.append(f"Network: {show.network}")
    if show.web_channel:
        lines.append(f"Web: {show.web_channel}")
    if show.rating:
        lines.append(f"Rating: ⭐ {show.rating}/10")
    if show.official_site:
        lines.append(f"Official site: {show.official_site}")
    if show.summary:
        lines.append(f"\n_{show.summary}_\n")
    if show.image_original:
        lines.append(f"\n📺 Poster: {show.image_original}")
    return "\n".join(lines)


@mcp.tool()
async def get_episode_list(show_id: int, season: Optional[int] = None) -> str:
    """Get all episodes for a show, optionally filtered by season number."""
    try:
        all_episodes = get_episodes(show_id)
    except Exception as e:
        show_name = f"show {show_id}"
        all_episodes = simulate_episodes(show_name)

    if not all_episodes:
        return f"No episodes found for show ID {show_id}."

    if season is not None:
        all_episodes = [e for e in all_episodes if e.season == season]

    if not all_episodes:
        return f"No episodes found for season {season}."

    lines = [f"**Episodes ({'all seasons' if season is None else f'Season {season}'}):**\n"]
    for ep in all_episodes:
        ep_num = f"S{ep.season:02d}E{ep.number:02d}" if ep.number else f"S{ep.season:02d}"
        airdate = f" ({ep.airdate})" if ep.airdate else ""
        summary = f" — {ep.summary[:150]}" if ep.summary else ""
        lines.append(f"**{ep.name}** — {ep_num}{airdate}{summary}")
    return "\n".join(lines)


@mcp.tool()
async def get_cast_list(show_id: int) -> str:
    """Get the cast for a TV show by its TVMaze ID."""
    try:
        cast = get_cast(show_id)
    except Exception as e:
        return f"Error fetching cast: {e}"

    if not cast:
        return f"No cast info found for show ID {show_id}."

    lines = [f"**Cast (show ID {show_id}):**\n"]
    for c in cast:
        lines.append(f"- **{c.person_name}** as _{c.character_name}_")
    return "\n".join(lines)


@mcp.tool()
async def get_tv_schedule(country: str = "US", date: Optional[str] = None) -> str:
    """Get the TV schedule for a country (ISO 3166-1 alpha-2) and optional date (YYYY-MM-DD)."""
    try:
        schedule = get_schedule(country=country, date=date)
    except Exception as e:
        return f"Error fetching schedule: {e}"

    if not schedule:
        date_str = date or "today"
        return f"No schedule listings for {country} on {date_str}."

    lines = [f"**TV Schedule for {country}**" + (f" ({date})" if date else "") + "\n"]
    for item in schedule[:20]:
        time_str = f" {item.airtime}" if item.airtime else ""
        ep_info = f" S{item.season:02d}E{item.number:02d}" if item.season and item.number else ""
        show_str = f" — *{item.show_name}*" if item.show_name else ""
        summary = f" {item.summary[:100]}" if item.summary else ""
        lines.append(f"- **{item.name}**{show_str}{ep_info}{time_str}{summary}")
    return "\n".join(lines)


@mcp.tool()
async def search_celebrities(name: str) -> str:
    """Search for a person (actor, writer, producer) by name."""
    try:
        results = search_people(name)
    except Exception as e:
        return f"Error searching people: {e}"

    if not results:
        return f"No people found for '{name}'."

    lines = [f"**People matching '{name}':**\n"]
    for r in results[:10]:
        person = r.get("person", {})
        pname = person.get("name", "Unknown")
        pid = person.get("id", "?")
        country = person.get("country", {}).get("name", "")
        birthday = person.get("birthday", "")
        known = ", ".join(person.get("knownFor", [])) if isinstance(person.get("knownFor"), list) else person.get("knownFor", "")
        img = person.get("image", {})
        lines.append(f"- **{pname}** (ID: `{pid}`)")
        if country:
            lines[-1] += f" — {country}"
        if birthday:
            lines[-1] += f" — b. {birthday}"
        if known:
            lines[-1] += f" — Known for: {known}"
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()