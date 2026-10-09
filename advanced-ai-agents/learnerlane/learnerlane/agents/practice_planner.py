"""
Practice Planner Agent — Generates weekly exercises and mini-projects.

For each module, assigns a concrete practice exercise or mini-project
that the user can complete within their available time.
"""

from dataclasses import dataclass, field
from typing import Optional

from .curriculum_builder import Curriculum, Module
from .skill_assessor import SkillProfile


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class PracticeTask:
    week: int
    title: str
    description: str
    estimated_minutes: int = 30
    task_type: str = "exercise"  # "exercise" or "project"


@dataclass
class PracticePlan:
    tasks: list[PracticeTask] = field(default_factory=list)


# ── Template practice plans ──────────────────────────────────────────────────

PRACTICE_TEMPLATES: dict[str, list[dict]] = {
    "photography": [
        {"title": "Aperture Exploration", "description": "Take the same object at every aperture your lens supports (f/2.8, f/4, f/5.6, f/8, f/11, f/16). Notice how background blur changes. Which do you prefer?", "minutes": 45},
        {"title": "Rule of Thirds", "description": "Shoot 10 photos using the rule of thirds grid. Then shoot 10 intentionally breaking it. Compare which feels more dynamic.", "minutes": 40},
        {"title": "Genre Mini-Project", "description": "Pick one genre (portrait, landscape, macro). Shoot 20 photos in that genre. Edit your top 3.", "minutes": 90},
        {"title": "Edit a Photo", "description": "Download GIMP or Snapseed. Take one photo and create 3 versions: natural, dramatic, and black & white.", "minutes": 60},
        {"title": "Portfolio Selection", "description": "Review everything you've shot this month. Select your best 10 images. Write a one-sentence reflection on what you've learned.", "minutes": 45},
    ],
    "guitar": [
        {"title": "Chord Transitions", "description": "Practice switching between Am, C, G, Em. Set a timer for 10 minutes. Count how many clean transitions you can do per minute. Target: 20/min.", "minutes": 20},
        {"title": "Learn Your First Song", "description": "Pick a 3-chord song (e.g. \"Horse With No Name\", \"Bad Moon Rising\"). Play through it slowly with a metronome at 60 BPM.", "minutes": 45},
        {"title": "Strumming Patterns", "description": "Practice 4 different strumming patterns: down-only, down-up, down-down-up, and syncopated. Record 30 seconds of each.", "minutes": 30},
        {"title": "Barre Chord Practice", "description": "Practice F major barre chord. Aim for 10 seconds of clean sound. Move it to the 5th fret for A barre. Practice transitioning from open G to F barre.", "minutes": 45},
        {"title": "Jam Session", "description": "Find a 12-bar blues backing track on YouTube. Play along using A, D, E chords. Focus on staying in time.", "minutes": 30},
    ],
    "baking": [
        {"title": "Cookie Science", "description": "Bake one batch of chocolate chip cookies. Take notes on: butter temperature, chill time, spread, texture. What would you change next time?", "minutes": 90},
        {"title": "Vanilla Cake", "description": "Bake a single-layer vanilla cake from scratch. Check doneness with a toothpick. Practice leveling the top.", "minutes": 120},
        {"title": "Pie Dough Practice", "description": "Make pie dough twice: once with butter, once with shortening. Compare flakiness. Blind bake both.", "minutes": 120},
        {"title": "Simple Bread", "description": "Make the no-knead bread recipe. Focus on: yeast activation, folding technique, steam baking. Document the crumb structure.", "minutes": 150},
        {"title": "Baking Portfolio", "description": "Bake your best item from the course. Plate it beautifully. Take a photo. Write a one-paragraph reflection on your progress.", "minutes": 120},
    ],
    "gardening": [
        {"title": "Sunlight Map", "description": "Sketch your garden/balcony. Every hour on a sunny day, note which areas are in sun vs shade. Create a sunlight map.", "minutes": 60},
        {"title": "Soil Test", "description": "Do a jar test for soil texture (sand/silt/clay). Check your soil pH with a kitchen kit or vinegar/baking soda test.", "minutes": 30},
        {"title": "Plant Your First Seedlings", "description": "Start 6 seeds indoors (easy: basil, marigold, or tomato). Label each. Create a watering log.", "minutes": 45},
        {"title": "Pest Patrol", "description": "Inspect every plant in your garden. Identify any pests. Research one organic treatment. Apply if needed.", "minutes": 40},
        {"title": "Harvest & Journal", "description": "Harvest anything ready. Record weights and quality notes. Write a \"lessons learned\" entry in your garden journal.", "minutes": 45},
    ],
    "python": [
        {"title": "Hello, Python", "description": "Write a script that asks for the user's name, age, and favorite color. Print a personalized greeting using f-strings. Use a conditional to check if they're old enough to vote.", "minutes": 30},
        {"title": "Function Fun", "description": "Write a module with 5 functions: factorial, fibonacci, palindrome check, vowel count, temperature converter. Import and test each one.", "minutes": 45},
        {"title": "Data Wrangler", "description": "Download a CSV (weather data or any public dataset). Write a script that reads it, filters rows, computes averages, and writes a summary CSV.", "minutes": 60},
        {"title": "API Explorer", "description": "Use the requests library to fetch data from a free API (e.g., Open-Meteo weather, or a public JSON API). Parse the response and print a readable report.", "minutes": 60},
        {"title": "CLI Project", "description": "Build a CLI tool of your choice: a to-do list, a note taker, or a unit converter. Add error handling, a help flag, and a requirements.txt.", "minutes": 90},
    ],
}


def generate_plan(curriculum: Curriculum, profile: SkillProfile) -> PracticePlan:
    """Generate a practice plan from the curriculum and skill profile."""
    tasks = []
    template_key = profile.topic.lower().strip()
    
    # Find matching template
    template_tasks = None
    for key, practices in PRACTICE_TEMPLATES.items():
        if key in template_key or template_key in key:
            key_words = key.split()
            match_ratio = sum(1 for w in key_words if w in template_key) / len(key_words)
            if match_ratio >= 0.5:
                template_tasks = practices
                break
    
    if not template_tasks:
        # Generic practice tasks for any skill
        template_tasks = [
            {"title": "Foundations Practice", "description": f"Practice the core techniques of {profile.topic} for 30 minutes. Focus on proper form and understanding the basics.", "minutes": 30},
            {"title": "Skill-Building Exercise", "description": f"Identify the three most important sub-skills in {profile.topic}. Practice each for 15 minutes.", "minutes": 45},
            {"title": "Applied Practice", "description": f"Apply your {profile.topic} knowledge to a real-world scenario. Document what worked and what didn't.", "minutes": 60},
            {"title": "Review & Refine", "description": "Review your work from the past weeks. What improved? What still needs work? Set goals for next week.", "minutes": 30},
            {"title": "Capstone Mini-Project", "description": f"Complete a small project that demonstrates your {profile.topic} skills. Show it to someone and get feedback.", "minutes": 60},
        ]
    
    # Match tasks to modules
    for i, module in enumerate(curriculum.modules):
        if i < len(template_tasks):
            task_data = template_tasks[i]
        else:
            # Wrap around
            task_data = template_tasks[i % len(template_tasks)]
        
        tasks.append(PracticeTask(
            week=module.week,
            title=task_data["title"],
            description=task_data["description"],
            estimated_minutes=task_data.get("minutes", 30),
            task_type="project" if "project" in task_data["title"].lower() or "mini-project" in task_data["title"].lower() else "exercise",
        ))
    
    return PracticePlan(tasks=tasks)