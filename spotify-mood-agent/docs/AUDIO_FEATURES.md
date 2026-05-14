# Spotify Audio Features Reference

Spotify computes 13 audio feature dimensions for every track in its catalogue. The mood agent uses all of them.

## Features

### Valence (0–1)
The most important mood indicator. Measures the musical positiveness of a track.

- **High (>0.7)**: Sounds happy, cheerful, euphoric
- **Medium (0.3–0.7)**: Emotionally neutral or mixed
- **Low (<0.3)**: Sounds sad, depressed, angry

### Energy (0–1)
Perceptual measure of intensity and activity. Energetic tracks feel fast, loud, noisy.

- **High (>0.7)**: High energy, intense, loud rock or EDM
- **Low (<0.3)**: Slow, quiet, acoustic music

### Danceability (0–1)
How suitable a track is for dancing, based on tempo, rhythm stability, beat strength, and regularity.

### Acousticness (0–1)
Confidence measure of whether the track is acoustic (0 = not acoustic, 1 = acoustic).
High acousticness correlates with introspective, stripped-back moods.

### Instrumentalness (0–1)
Predicts whether a track contains no vocals. Values >0.5 suggest instrumental tracks.
High instrumentalness often correlates with introspective or meditative states.

### Liveness (0–1)
Detects the presence of an audience in the recording.
Values >0.8 strongly suggest a live recording.
Live music often signals a desire for social, communal experience.

### Speechiness (0–1)
Detects spoken word in a track.
- **>0.66**: Likely all speech (podcast, audiobook, spoken word)
- **0.33–0.66**: Mix of music and speech
- **<0.33**: Mostly music

### Tempo (BPM)
Estimated tempo in beats per minute. Correlates with energy and emotional activation.
- **Fast (>130 BPM)**: Excitement, anxiety, euphoria
- **Moderate (90–130 BPM)**: Neutral
- **Slow (<90 BPM)**: Calm, sad, reflective

### Loudness (dB)
Overall loudness, typically ranging from -60 to 0 dB.
Higher loudness (closer to 0) suggests more intense, energetic music.

### Mode (0 or 1)
The modality of a track.
- **1 = Major**: Tends to sound brighter, happier
- **0 = Minor**: Tends to sound darker, sadder

### Key (0–11)
Estimated key of the track (0=C, 1=C#, 2=D, ..., 11=B). -1 if key is undetected.

### Duration (ms)
Track length in milliseconds.

### Time Signature (3–7)
Estimated number of beats per bar. Most pop music is 4/4.

---

## Mood Interpretation Guide

| Pattern | Mood Signal |
|---------|-------------|
| High valence + High energy | Joyful, euphoric, celebratory |
| High valence + Low energy | Content, peaceful, relaxed |
| Low valence + High energy | Angry, frustrated, intense |
| Low valence + Low energy | Sad, depressed, exhausted |
| High acousticness + Low valence | Introspective sadness, folk-influenced grief |
| High instrumentalness | Meditative, cerebral, withdrawn |
| High liveness | Social, communal, nostalgic for live events |
| High speechiness | Possibly using music for distraction or stimulation |
| High danceability + Low valence | Melancholic dancing — "dancing through sadness" |

---

## Temporal Patterns

The agent analyses how these features change *over time* during a session:

- **Valence trending up**: Mood is lifting, possibly working through difficult emotions
- **Valence trending down**: Mood declining, or seeking deeper introspection
- **Energy trending up**: Building motivation or escalating anxiety
- **High volatility**: Emotional instability, seeking distraction, or exploring mood
- **Stable low valence**: Settled into a melancholic state (not necessarily negative)
