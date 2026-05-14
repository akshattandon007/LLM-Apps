"""
Mock Spotify API data for tests.
Represents a melancholic late-night listening session.
"""

MOCK_RECENTLY_PLAYED = {
    "items": [
        {
            "track": {
                "id": "track_001",
                "name": "Holocene",
                "artists": [{"id": "artist_bon_iver", "name": "Bon Iver"}],
                "album": {"name": "Bon Iver, Bon Iver", "release_date": "2011"},
                "popularity": 72,
                "explicit": False,
            },
            "played_at": "2024-01-15T23:45:00Z",
        },
        {
            "track": {
                "id": "track_002",
                "name": "Skinny Love",
                "artists": [{"id": "artist_bon_iver", "name": "Bon Iver"}],
                "album": {"name": "For Emma, Forever Ago", "release_date": "2008"},
                "popularity": 68,
                "explicit": False,
            },
            "played_at": "2024-01-15T23:20:00Z",
        },
        {
            "track": {
                "id": "track_003",
                "name": "Re: Stacks",
                "artists": [{"id": "artist_bon_iver", "name": "Bon Iver"}],
                "album": {"name": "For Emma, Forever Ago", "release_date": "2008"},
                "popularity": 64,
                "explicit": False,
            },
            "played_at": "2024-01-15T23:00:00Z",
        },
        {
            "track": {
                "id": "track_004",
                "name": "Lua",
                "artists": [{"id": "artist_bright_eyes", "name": "Bright Eyes"}],
                "album": {"name": "I'm Wide Awake, It's Morning", "release_date": "2005"},
                "popularity": 61,
                "explicit": False,
            },
            "played_at": "2024-01-15T22:40:00Z",
        },
        {
            "track": {
                "id": "track_005",
                "name": "First Day of My Life",
                "artists": [{"id": "artist_bright_eyes", "name": "Bright Eyes"}],
                "album": {"name": "I'm Wide Awake, It's Morning", "release_date": "2005"},
                "popularity": 70,
                "explicit": False,
            },
            "played_at": "2024-01-15T22:15:00Z",
        },
    ],
    "cursors": None,
}

MOCK_AUDIO_FEATURES = [
    {
        "id": "track_001",
        "danceability": 0.323,
        "energy": 0.299,
        "key": 5,
        "loudness": -12.1,
        "mode": 0,
        "speechiness": 0.027,
        "acousticness": 0.889,
        "instrumentalness": 0.0,
        "liveness": 0.107,
        "valence": 0.261,
        "tempo": 100.4,
        "duration_ms": 337120,
        "time_signature": 4,
    },
    {
        "id": "track_002",
        "danceability": 0.387,
        "energy": 0.411,
        "key": 9,
        "loudness": -10.5,
        "mode": 0,
        "speechiness": 0.031,
        "acousticness": 0.792,
        "instrumentalness": 0.0,
        "liveness": 0.112,
        "valence": 0.337,
        "tempo": 132.1,
        "duration_ms": 216000,
        "time_signature": 4,
    },
    {
        "id": "track_003",
        "danceability": 0.356,
        "energy": 0.241,
        "key": 2,
        "loudness": -14.2,
        "mode": 0,
        "speechiness": 0.025,
        "acousticness": 0.931,
        "instrumentalness": 0.012,
        "liveness": 0.098,
        "valence": 0.198,
        "tempo": 87.3,
        "duration_ms": 377000,
        "time_signature": 4,
    },
    {
        "id": "track_004",
        "danceability": 0.412,
        "energy": 0.352,
        "key": 7,
        "loudness": -11.8,
        "mode": 0,
        "speechiness": 0.038,
        "acousticness": 0.871,
        "instrumentalness": 0.0,
        "liveness": 0.091,
        "valence": 0.287,
        "tempo": 94.6,
        "duration_ms": 254000,
        "time_signature": 3,
    },
    {
        "id": "track_005",
        "danceability": 0.489,
        "energy": 0.421,
        "key": 4,
        "loudness": -10.1,
        "mode": 1,
        "speechiness": 0.042,
        "acousticness": 0.842,
        "instrumentalness": 0.0,
        "liveness": 0.115,
        "valence": 0.442,
        "tempo": 108.2,
        "duration_ms": 231000,
        "time_signature": 4,
    },
]

MOCK_ARTISTS = {
    "artists": [
        {
            "id": "artist_bon_iver",
            "name": "Bon Iver",
            "genres": ["indie folk", "folk", "chamber pop", "stomp and holler"],
            "popularity": 73,
        },
        {
            "id": "artist_bright_eyes",
            "name": "Bright Eyes",
            "genres": ["indie folk", "sadcore", "lo-fi", "indie pop"],
            "popularity": 62,
        },
    ]
}
