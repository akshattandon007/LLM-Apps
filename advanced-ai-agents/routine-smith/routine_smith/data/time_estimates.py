"""Built-in duration estimates for common activities (minutes)."""

# Default durations for common morning activities
MORNING_ACTIVITIES = {
    "wake_up_gradually": 5,
    "stretching": 10,
    "meditation": 10,
    "journaling": 10,
    "reading": 20,
    "exercise_cardio": 30,
    "exercise_strength": 30,
    "exercise_yoga": 20,
    "shower": 15,
    "skincare": 5,
    "dressing": 10,
    "breakfast": 20,
    "meal_prep": 30,
    "walk_dog": 20,
    "plan_day": 5,
    "commute": 30,
    "podcasts": 20,
    "language_learning": 15,
}

# Default durations for daytime activities
DAY_ACTIVITIES = {
    "deep_work": 90,
    "meetings": 60,
    "email": 20,
    "planning": 15,
    "learning_course": 30,
    "reading_articles": 15,
    "stretch_break": 5,
    "walk_break": 10,
    "lunch": 30,
    "nap": 20,
}

# Default durations for evening activities
EVENING_ACTIVITIES = {
    "exercise_evening": 30,
    "walk": 20,
    "cook_dinner": 45,
    "eat_dinner": 30,
    "social_time": 60,
    "phone_call": 15,
    "tv": 30,
    "read_fiction": 20,
    "hobby": 45,
    "plan_tomorrow": 10,
    "wind_down": 15,
    "skincare_evening": 10,
    "meditation_evening": 15,
    "journal_evening": 10,
    "prepare_bed": 10,
    "no_screens": 30,
}

# All activities combined
ALL_ACTIVITIES = {}
ALL_ACTIVITIES.update(MORNING_ACTIVITIES)
ALL_ACTIVITIES.update(DAY_ACTIVITIES)
ALL_ACTIVITIES.update(EVENING_ACTIVITIES)


def estimate_duration(activity: str) -> int:
    """Get the estimated duration for an activity in minutes."""
    return ALL_ACTIVITIES.get(activity, 15)  # Default 15 min for unknowns