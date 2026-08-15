# 🎧 Spotify DJ Agent — Your Personal AI Music Curator

> **Your personal AI music curator — search, discover, and build playlists without opening Spotify.** 🎵

Ask for playlists by mood, tempo, or genre; discover new releases; get deep track analysis — all from the terminal or integrated into your Hermes agent through the MCP protocol.

---

## ✨ What It Does

| Capability | Description |
|---|---|
| 🔍 **Search Tracks** | Search Spotify for tracks, artists, and albums |
| 🤖 **AI Recommendations** | Get smart recommendations based on energy, BPM, genre, and more |
| 🆕 **New Releases** | See what's dropping this week — filterable by country |
| 🎤 **Artist Top Tracks** | Pull the biggest hits for any artist |
| 📊 **Describe Track** | Deep audio analysis: BPM, key, energy, valence, danceability |
| 📋 **Get Playlist** | View playlist details and full tracklist |
| ✅ **Create Playlist** | Build and publish new Spotify playlists (approval-gated — you confirm before it goes live) |

---

## 🛠️ Tool Surface

| Tool | What it does | Auth |
|---|---|---|
| `search_tracks` | 🔍 Search tracks, artists, albums | Read |
| `get_recommendations` | 🤖 AI-curated picks by seed + audio targets | Read |
| `get_new_releases` | 🆕 Latest album releases | Read |
| `get_artist_top_tracks` | 🎤 Top tracks for an artist | Read |
| `describe_track` | 📊 BPM, key, energy, valence, danceability | Read |
| `get_playlist` | 📋 Playlist details + tracklist | Read |
| `create_playlist` | ✅ Create a new playlist (you approve first) | User auth |

---

## 🚀 Quick Start

### 1. Get Spotify API credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click **Create app**, name it "Spotify DJ"
3. Set **Redirect URI** to `http://localhost:8888/callback`
4. Copy your **Client ID** and **Client Secret**

### 2. Set environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### 3. Install & run

```bash
pip install -r requirements.txt
python main.py stdio
```

Or as HTTP:

```bash
python main.py http
```

---

## 🎯 Example Queries

> *"Build me a 45-minute deep-focus playlist: ambient, 90-110 BPM"*
>
> The agent searches ambient tracks, fetches AI recommendations targeting low energy / high instrumentalness at 100 BPM, and presents a playlist for your approval before creating it.

> *"What are the new releases in electronic music this week?"*
>
> The agent calls `get_new_releases` with country filtering and surfaces albums, artists, and release dates.

> *"Describe this track: 11dFghVXANMlKmJXsNCbNl"*
>
> Returns BPM, key, mode, energy, danceability, valence, and more.

---

## 🏗️ Architecture

```
                     ┌──────────────────────┐
                     │    MCP Host / Client  │
                     │  (Hermes, CLI, etc.)  │
                     └──────┬───────────────┘
                            │ JSON-RPC over stdio or HTTP
                     ┌──────▼───────────────┐
                     │   Spotify DJ Agent    │
                     │   (main.py + tools)   │
                     └──────┬───────────────┘
                            │ HTTP requests
                     ┌──────▼───────────────┐
                     │   Spotify Web API     │
                     └──────────────────────┘
```

---

## 🧪 Testing

```bash
pytest tests/ -v
```

Tests use `FakeSpotifyClient` — no network calls, no real credentials needed.

---

## 📄 License

MIT — go make some playlists. 🎶