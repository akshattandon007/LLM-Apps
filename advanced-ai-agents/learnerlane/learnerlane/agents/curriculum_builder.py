"""
Curriculum Builder Agent — Constructs a progressive learning plan.

Takes a SkillProfile and produces 4-8 progressive modules,
each with a topic, learning goal, and suggested time commitment.
"""

from dataclasses import dataclass, field
from typing import Optional
from .skill_assessor import SkillProfile


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class Module:
    week: int
    title: str
    goal: str
    topics: list[str] = field(default_factory=list)
    estimated_hours: float = 1.0


@dataclass
class Curriculum:
    topic: str
    modules: list[Module] = field(default_factory=list)
    total_weeks: int = 0

    @property
    def is_valid(self) -> bool:
        return len(self.modules) >= 3 and self.total_weeks > 0


# ── Built-in curriculum templates (for demo/simulated mode) ──────────────────

CURRICULUM_TEMPLATES: dict[str, list[dict]] = {
    "photography": [
        {"title": "Your Camera & Core Concepts", "goal": "Understand exposure triangle (aperture, shutter speed, ISO) and how your camera works",
         "topics": ["Camera anatomy and modes", "Aperture and depth of field", "Shutter speed and motion", "ISO and noise", "Exposure triangle relationship"],
         "hours": 2.0},
        {"title": "Composition & Lighting", "goal": "Learn composition rules and how to work with natural light",
         "topics": ["Rule of thirds and leading lines", "Framing and perspective", "Golden hour and blue hour", "Diffuse vs direct light", "Indoor lighting techniques"],
         "hours": 2.0},
        {"title": "Genre Exploration", "goal": "Experiment with portrait, landscape, macro, and street photography",
         "topics": ["Portrait photography basics", "Landscape and nature", "Macro and close-up", "Street photography", "Choosing your genre focus"],
         "hours": 2.0},
        {"title": "Editing & Post-Processing", "goal": "Learn basic editing with free tools like Snapseed or GIMP",
         "topics": ["Histogram reading", "Exposure and contrast adjustment", "Color temperature and white balance", "Cropping and straightening", "Export settings for web and print"],
         "hours": 2.5},
        {"title": "Building a Portfolio", "goal": "Select your best work and present it coherently",
         "topics": ["Curating your best images", "Creating a simple portfolio", "Giving and receiving critique", "Next steps: advanced techniques"],
         "hours": 1.5},
    ],
    "guitar": [
        {"title": "Getting Started", "goal": "Tune your guitar, hold it properly, and play your first chords",
         "topics": ["Parts of the guitar", "Tuning (standard EADGBE)", "Proper posture and hand position", "Basic open chords: Am, C, G, Em", "Strumming patterns"],
         "hours": 2.0},
        {"title": "First Songs", "goal": "Play 2-3 complete songs using open chords",
         "topics": ["Chord transitions smoothly", "Common progressions (I-IV-V)", "Reading chord charts", "Song 1: simple 3-chord song", "Song 2: 4-chord progression"],
         "hours": 2.0},
        {"title": "Rhythm & Strumming", "goal": "Develop solid rhythm and expand your strumming vocabulary",
         "topics": ["Downstrokes and upstrokes", "Eighth-note rhythms", "Dynamics and accent patterns", "Using a metronome", "Fingerstyle basics"],
         "hours": 2.0},
        {"title": "Barre Chords & Beyond", "goal": "Master barre chords and expand your fretboard knowledge",
         "topics": ["F and Bm barre chords", "The CAGED system intro", "Moving chord shapes up the neck", "Pentatonic scale", "Simple lead patterns"],
         "hours": 2.5},
        {"title": "Playing with Others", "goal": "Jam with other musicians and play in time",
         "topics": ["Listening while playing", "Call and response", "12-bar blues structure", "Playing to backing tracks", "Open mic preparation"],
         "hours": 1.5},
    ],
    "baking": [
        {"title": "Baking Fundamentals", "goal": "Understand essential ingredients, tools, and techniques",
         "topics": ["Measuring correctly (weight vs volume)", "Essential tools and substitutes", "Understanding flour, sugar, fat, leavening", "Oven temperature and positioning", "Reading a recipe properly"],
         "hours": 1.5},
        {"title": "Cookies & Bars", "goal": "Master drop cookies, slice-and-bake, and bar cookies",
         "topics": ["Chocolate chip cookies — the science", "Chilling dough and why", "Bar cookies: brownies and blondies", "Troubleshooting: spread, crumble, doneness", "Freezing and storing"],
         "hours": 2.0},
        {"title": "Cakes & Cupcakes", "goal": "Bake moist, level cakes and basic buttercream",
         "topics": ["Creaming method", "Pound cake and variations", "Cupcake scaling and timing", "Simple buttercream frosting", "Leveling and stacking"],
         "hours": 2.5},
        {"title": "Pies & Tarts", "goal": "Make flaky pie dough and perfect fillings",
         "topics": ["All-butter pie dough", "Blind baking technique", "Fruit fillings and thickeners", "Lattice top and crimping", "Custard pies"],
         "hours": 2.5},
        {"title": "Bread Baking", "goal": "Bake your first yeast bread and understand fermentation",
         "topics": ["Yeast types and activation", "Kneading and windowpane test", "First rise and shaping", "Steam and crust formation", "No-knead beginner bread"],
         "hours": 2.5},
    ],
    "gardening": [
        {"title": "Know Your Space", "goal": "Assess your growing conditions and choose the right plants",
         "topics": ["Sunlight assessment (full sun, part shade, shade)", "Soil type test", "Hardiness zone and microclimate", "Container vs in-ground", "Choosing beginner-friendly plants"],
         "hours": 1.5},
        {"title": "Soil & Composting", "goal": "Build healthy soil for strong plants",
         "topics": ["Soil amendments (compost, perlite, peat moss)", "Starting a compost pile", "Mulching benefits", "Water retention and drainage", "pH testing and adjustment"],
         "hours": 2.0},
        {"title": "Planting & Watering", "goal": "Plant correctly and establish a watering routine",
         "topics": ["Seed starting indoors", "Transplanting seedlings", "Direct sowing", "Watering depth and frequency", "Drought vs overwatering signs"],
         "hours": 2.0},
        {"title": "Pest & Disease Management", "goal": "Identify common problems and treat them naturally",
         "topics": ["Beneficial insects vs pests", "Neem oil and insecticidal soap", "Common diseases: powdery mildew, blight", "Companion planting", "IPM (Integrated Pest Management) basics"],
         "hours": 2.0},
        {"title": "Harvesting & Next Season", "goal": "Harvest at peak and plan the next growing cycle",
         "topics": ["When to harvest vegetables", "Seed saving basics", "Fall cleanup and winter prep", "Crop rotation planning", "Keeping a garden journal"],
         "hours": 1.5},
    ],
    "python": [
        {"title": "Python Basics", "goal": "Write your first Python programs with variables, types, and conditionals",
         "topics": ["Installing Python and running scripts", "Variables and data types", "Lists, tuples, dictionaries", "If/elif/else conditionals", "For and while loops"],
         "hours": 2.0},
        {"title": "Functions & Modules", "goal": "Write reusable code with functions and import modules",
         "topics": ["Defining functions", "Parameters and return values", "Importing standard library modules", "Writing your own module", "Error handling with try/except"],
         "hours": 2.0},
        {"title": "Working with Data", "goal": "Read, write, and manipulate files and data structures",
         "topics": ["File I/O (reading and writing)", "CSV and JSON parsing", "List comprehensions and generators", "String manipulation", "Working with dates and times"],
         "hours": 2.5},
        {"title": "Libraries & Tools", "goal": "Use pip, virtual environments, and popular third-party libraries",
         "topics": ["pip and requirements.txt", "Virtual environments", "Requests library for HTTP", "BeautifulSoup for HTML parsing", "Basic pandas for data analysis"],
         "hours": 2.5},
        {"title": "Project & Next Steps", "goal": "Build a small project and know where to go next",
         "topics": ["Project: CLI tool or data scraper", "Testing with pytest", "Git and GitHub basics", "Web frameworks overview (Flask, FastAPI)", "Learning paths: data science, web, automation"],
         "hours": 2.0},
    ],
}

GENERIC_MODULES = [
    {"title": "Getting Started: Fundamentals", "goal": "Understand the core concepts and essential first steps",
     "topics": ["What this skill is and why it matters", "Essential terminology", "Tools and resources you'll need", "Setting up your workspace", "Your first practice exercise"],
     "hours": 1.5},
    {"title": "Building Core Skills", "goal": "Develop foundational techniques through structured practice",
     "topics": ["Core techniques and methods", "Common beginner mistakes to avoid", "Structured practice routine", "Progress benchmarks", "Troubleshooting basics"],
     "hours": 2.0},
    {"title": "Intermediate Techniques", "goal": "Expand your abilities with more advanced approaches",
     "topics": ["Intermediate techniques and concepts", "Combining techniques", "Quality and consistency improvement", "Working with feedback", "Building confidence"],
     "hours": 2.0},
    {"title": "Putting It All Together", "goal": "Complete a capstone project that demonstrates your new skills",
     "topics": ["Planning your capstone project", "Executing step by step", "Reviewing and refining", "Sharing your work", "Planning continued growth"],
     "hours": 2.0},
    {"title": "Going Further", "goal": "Chart your path beyond the basics with community and advanced resources",
     "topics": ["Communities and groups to join", "Advanced resource recommendations", "Specialization paths", "Teaching others to solidify knowledge", "Setting long-term learning goals"],
     "hours": 1.5},
]


def build_curriculum(profile: SkillProfile) -> Curriculum:
    """Build a curriculum for the given skill profile.
    
    Uses built-in templates for common topics, or generates a generic curriculum
    for any other topic. In production, this would be LLM-driven.
    """
    topic_key = profile.topic.lower().strip()
    
    # Check for matching template
    template = None
    for key, modules in CURRICULUM_TEMPLATES.items():
        if key in topic_key or topic_key in key:
            template = modules
            break
        # Partial match: check if topic contains key words
        key_words = key.split()
        if any(word in topic_key for word in key_words):
            # Only match if it's a strong signal
            match_ratio = sum(1 for w in key_words if w in topic_key) / len(key_words)
            if match_ratio >= 0.5:
                template = modules
                break
    
    if not template:
        template = GENERIC_MODULES
    
    # Adjust number of modules based on time commitment and level
    hours = profile.hours_per_week()
    total_weeks = max(4, min(8, len(template)))
    
    # For beginners with less time, use fewer modules
    if profile.level == "beginner" and hours < 2:
        total_weeks = min(4, len(template))
    
    # Build modules
    modules = []
    for i, mod_data in enumerate(template[:total_weeks]):
        modules.append(Module(
            week=i + 1,
            title=mod_data["title"],
            goal=mod_data["goal"],
            topics=mod_data.get("topics", []),
            estimated_hours=mod_data.get("hours", 2.0),
        ))
    
    return Curriculum(
        topic=profile.topic,
        modules=modules,
        total_weeks=total_weeks,
    )