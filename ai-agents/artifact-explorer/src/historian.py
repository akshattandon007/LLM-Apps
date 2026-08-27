"""Generate a rich artifact story from an identification result.

MVP uses a built-in story library keyed on artifact name.
"""

from .models import Artifact, IdentificationResult

# ── Artifact story library ───────────────────────────────────────────────────

STORIES: dict[str, dict] = {
    "Kodak Brownie No. 2": {
        "origin": "Rochester, New York, USA",
        "era": "1901–1935 (Edwardian through Jazz Age)",
        "history": (
            "Invented by Eastman Kodak and introduced in 1901, the Brownie No. 2 "
            "democratised photography. For $2 (about $70 today), anyone could own a "
            "camera that took 2¼-inch square pictures on roll film. Over 2 million "
            "were sold in the first decade, turning snapshot photography from a "
            "studio luxury into a household habit."
        ),
        "cultural_significance": (
            "The Brownie created the 'snapshot' as a cultural concept. For the first "
            "time, ordinary people documented everyday life — birthdays, picnics, "
            "holidays — without a professional photographer. The camera was simple "
            "enough for children, spawning the 'Brownie' name from characters in "
            "Palmer Cox's popular children's books. It shifted photography from "
            "formal portraiture to personal memory-keeping."
        ),
        "practical_uses": (
            "Point the camera at waist level, look down into the viewfinder, press "
            "the shutter button, advance the film with the winding knob. The fixed-"
            "focus meniscus lens means everything 6 feet to infinity is sharp — no "
            "focusing required. Best used in bright daylight."
        ),
        "fun_facts": [
            "The Brownie is credited with creating the home-movie industry — Kodak followed up with the Brownie Movie Camera in 1913.",
            "An original 1901 Brownie in good condition sells for $150–$400 today.",
            "The name 'Brownie' was licensed from Palmer Cox's popular children's book characters — not named after the snack.",
            "The No. 2 model took 120 roll film, which is still made today.",
        ],
    },
    "Ras el Hanout": {
        "origin": "Morocco, North Africa",
        "era": "Medieval (8th century CE onward)",
        "history": (
            "Ras el Hanout translates to 'head of the shop' in Arabic — meaning the "
            "best blend the spice merchant has to offer. Origins trace to medieval "
            "Morocco where spice traders along the trans-Saharan routes combined "
            "ingredients from West Africa, the Mediterranean, and Asia. Each merchant "
            "guarded their recipe jealously. The best blends used up to 100 ingredients."
        ),
        "cultural_significance": (
            "In Moroccan culture, ras el hanout is the cornerstone of ceremonial "
            "cooking — used in couscous, tagines, and pastilla for weddings and Eid "
            "feasts. It represents the art of balance: sweet (cinnamon, rose petals) "
            "against savoury (cumin, coriander) against heat (chilli, peppercorns). "
            "The exact blend signals a household's culinary identity."
        ),
        "practical_uses": (
            "Rub into lamb or chicken before roasting. Stir into couscous with "
            "preserved lemon and olives. Sprinkle over roasted vegetables. Mix with "
            "yogurt as a marinade. Add to rice pilafs or lentil soups. Toast briefly "
            "in a dry pan to bloom the aromatics before using."
        ),
        "fun_facts": [
            "Some traditional recipes include dried rosebuds, ash berries, orris root, or even Spanish fly (a now-illegal aphrodisiac).",
            "There is no single 'official' recipe — every Moroccan spice merchant's blend is unique.",
            "Ras el hanout is sometimes called 'the Moroccan garam masala' but is far more complex.",
            "In France, the blend became popular in the 20th century through colonial trade routes and is now sold in every major supermarket.",
        ],
    },
    "Vintage Egg Slicer": {
        "origin": "Germany / United States",
        "era": "1920s (Art Deco period)",
        "history": (
            "The egg slicer is a deceptively simple invention patented in 1923 by "
            "Willy Mayer, a German immigrant in New York. The original design used "
            "thin piano wire stretched across a hinged frame. It solved the problem "
            "of slicing peeled hard-boiled eggs cleanly — a tedious knife task that "
            "usually ended with crushed whites and uneven slices."
        ),
        "cultural_significance": (
            "The egg slicer belongs to the wave of single-purpose kitchen gadgets "
            "that flooded American homes in the 1920s–1950s, part of a broader "
            "labour-saving movement. It represents an era when industrial design "
            "meet the domestic sphere. Post-war prosperity and home-economics "
            "movements celebrated gadgets that made housewives more 'efficient'."
        ),
        "practical_uses": (
            "Place a peeled hard-boiled egg in the curved well. Press the hinged "
            "top down firmly. The wires pass cleanly through the egg, producing "
            "even slices in one motion. Also works on peeled kiwis, strawberries, "
            "mushrooms, and soft cheeses like mozzarella balls."
        ),
        "fun_facts": [
            "Vintage egg slicers with the original chromium plating and Art Deco lines can fetch $30–$80 at antique shops.",
            "The wire design was inspired by cheese-cutting implements used in German delicatessens.",
            "Modern egg slicers add a second set of perpendicular wires for hard-boiled egg 'dicing'.",
            "Collectors hunt for rare coloured-handle versions from Depression-era glass companies like Anchor Hocking.",
        ],
    },
    "Aloe Vera (Aloe barbadensis miller)": {
        "origin": "Arabian Peninsula (native); now cultivated worldwide",
        "era": "Ancient (earliest records ~2200 BCE, Sumerian clay tablets)",
        "history": (
            "Aloe vera is one of the oldest documented medicinal plants. A Sumerian "
            "clay tablet from 2200 BCE describes it as a 'plant of immortality'. "
            "Egyptian queens Nefertiti and Cleopatra used it in their skincare "
            "routines. Alexander the Great conquered the island of Socotra partly "
            "to secure its aloe groves for treating wounded soldiers. Arab traders "
            "spread it along the Silk Road to India and Southeast Asia."
        ),
        "cultural_significance": (
            "Aloe appears in traditional medicine systems across the world: Ayurveda, "
            "Traditional Chinese Medicine, and Unani. In many cultures it is planted "
            "at doorways as a protective charm. The gel is the only plant-based "
            "treatment recommended by the American Academy of Dermatology (for "
            "sunburn). Its export is a multi-billion-dollar industry, dominated by "
            "Mexico, Costa Rica, and the Dominican Republic."
        ),
        "practical_uses": (
            "Snap off a leaf, squeeze the clear gel onto minor burns or sunburn for "
            "cooling relief. Use as a face mask (leave on 10 min, rinse). Drink "
            "the gel blended with juice (commercial product). Apply to small cuts "
            "after cleaning. NOT for deep wounds or third-degree burns."
        ),
        "fun_facts": [
            "There are over 500 species of aloe, but only Aloe barbadensis miller has significant medicinal properties.",
            "The gel is 99% water — the remaining 1% contains over 75 active compounds including vitamins, enzymes, and amino acids.",
            "Aloe vera can survive months without water — the thick leaves store moisture for drought periods.",
            "The plant is toxic to cats and dogs if ingested — keep houseplants out of reach.",
        ],
    },
    "Amethyst": {
        "origin": "Worldwide — major deposits in Brazil, Uruguay, Zambia, South Korea",
        "era": "Geologic: ~130 million years (Cretaceous); human use: ~25,000 BCE",
        "history": (
            "Amethyst is quartz coloured by iron impurities and natural irradiation. "
            "Paleolithic humans used it as early as 25,000 BCE. Ancient Greeks wore "
            "it to prevent drunkenness (the name means 'not intoxicated'). It adorned "
            "Egyptian jewellery, Roman signet rings, and medieval bishops' rings. "
            "The largest deposits were discovered in Brazil in the 19th century, "
            "turning it from a rare gem into an accessible semi-precious stone."
        ),
        "cultural_significance": (
            "Amethyst is the birthstone of February and a traditional symbol of "
            "sobriety, clarity, and spiritual wisdom. In Christian tradition, it "
            "adorns the rings of Catholic bishops. Tibetan Buddhists use amethyst "
            "in meditation mala beads. During the Renaissance, it was considered a "
            "stone of royalty because the purple dye was also the most expensive colour."
        ),
        "practical_uses": (
            "Wear as jewellery (rings, pendants, earrings). Place in window light "
            "as a decorative piece. Use in crystal healing practices (though no "
            "scientific evidence supports therapeutic claims). Collect as mineral "
            "specimens — amethyst geodes make dramatic displays."
        ),
        "fun_facts": [
            "Heat-treated amethyst turns yellow-green and is sold as citrine — much of the 'citrine' on the market is actually heated amethyst.",
            "The largest amethyst geode ever found weighed 35 tonnes and was discovered in Uruguay in 2007.",
            "Amethyst's purple colour fades with prolonged direct sunlight exposure.",
            "In the Crown Jewels of England, the 'St Edward's Sapphire' was once believed to be an amethyst.",
        ],
    },
    "Slide Rule (Keuffel & Esser 4081-3)": {
        "origin": "United States (manufactured by Keuffel & Esser, Hoboken, New Jersey)",
        "era": "1940s–1970s (the golden age of analog computing)",
        "history": (
            "The slide rule traces its mathematical roots to John Napier's logarithms "
            "(1614) and the first physical slide rule by William Oughtred (1630). "
            "Keuffel & Esser dominated the American market from the 1860s until "
            "the 1970s. The 4081-3 was the gold standard — the 'Deci-Lon' model — "
            "used by NASA engineers during the Apollo program. Then in 1972, HP's "
            "scientific calculator (the HP-35) killed the slide rule industry in a "
            "single year."
        ),
        "cultural_significance": (
            "The slide rule was the symbol of the engineer for 300 years. Every "
            "engineer's pocket or desk held one — it was the laptop of its era. "
            "Apollo astronauts carried slide rules as backup navigation tools. "
            "Its obsolescence in the 1970s marks one of the fastest technological "
            "displacements in history: a three-century-old tool replaced by a "
            "calculator in less than 24 months."
        ),
        "practical_uses": (
            "Slide the cursor hairline to a value on scale C, align with scale D, "
            "read the product. Performs multiplication, division, square roots, "
            "logarithms, and trigonometric functions. Accuracy: 3 significant "
            "figures — good enough for most engineering work in its day."
        ),
        "fun_facts": [
            "A slide rule was aboard Apollo 11 and served as a backup for the onboard computer.",
            "K&E slide rules were made of bamboo — it was more dimensionally stable than wood and self-lubricating.",
            "The HP-35 scientific calculator was nicknamed the 'electronic slide rule' and initially sold for $395.",
            "Collectors pay $100–$500 for a clean K&E Deci-Lon in its original case.",
        ],
    },
    "Roman Denarius (Marcus Aurelius)": {
        "origin": "Roman Empire (minted in Rome)",
        "era": "161–180 CE (reign of Marcus Aurelius)",
        "history": (
            "The denarius was the standard silver coin of the Roman Empire for "
            "nearly 500 years (211 BCE — 284 CE). This particular coin was struck "
            "during the reign of Marcus Aurelius, the Stoic philosopher-emperor. "
            "It paid Roman legionaries, bought grain, and funded the empire's vast "
            "infrastructure. By Marcus's reign, the denarius had already been "
            "debased from pure silver to roughly 75% silver — a sign of inflationary "
            "pressure that would eventually cripple Rome."
        ),
        "cultural_significance": (
            "The denarius is the coin of the New Testament ('Render unto Caesar'). "
            "It funded the Roman military machine that built roads, aqueducts, and "
            "cities across three continents. The portrait rendered the emperor's "
            "image across the entire empire — a propaganda tool before mass media. "
            "Marcus Aurelius is especially revered because his 'Meditations' — "
            "Stoic philosophy written on campaign — survives as a foundational text."
        ),
        "practical_uses": (
            "Buy: a loaf of bread, a litre of wine, or a day's staple grain ration. "
            "One denarius was a typical daily wage for a labourer or soldier. "
            "Handle by the edges — fingers on the faces degrade the already-worn "
            "detail. Store in a climate-controlled holder; silver tarnishes."
        ),
        "fun_facts": [
            "A common Marcus Aurelius denarius costs $80–$300 today depending on condition and strike quality.",
            "The silver content dropped from ~95% in Nero's reign to ~4% by the late 3rd century — one of history's longest currency debasements.",
            "The denarius is mentioned in the Bible as 'the penny' (King James translation for *denarius*).",
            "Marcus Aurelius wrote his 'Meditations' in Greek, not Latin — even though he was Roman emperor.",
        ],
    },
    "The Anatomy of Melancholy (1638 Folio)": {
        "origin": "Oxford, England (printed by John Lichfield)",
        "era": "1638 (Caroline period)",
        "history": (
            "Robert Burton's *The Anatomy of Melancholy* first appeared in 1621. "
            "By 1638 it was already in its third edition — a bestseller by "
            "17th-century standards. The book is a sprawling, satirical, and "
            "astonishingly learned treatise on the causes, symptoms, and cures of "
            "melancholy (depression). Burton wrote under the pseudonym 'Democritus "
            "Junior'. He died in 1640, likely of the melancholy he so thoroughly "
            "catalogued."
        ),
        "cultural_significance": (
            "Samuel Johnson credited the *Anatomy* as the only book he wished "
            "longer. It influenced everyone from Laurence Sterne (Tristram Shandy) "
            "to John Keats. Modern readers discover it through Nick Levey's "
            "introduction in Borges's *Library of Babel*. The book is a monument "
            "of Renaissance learning — a single author quoting hundreds of classical "
            "and medieval sources in a style that lurches between Latin scholarship "
            "and bawdy English jokes."
        ),
        "practical_uses": (
            "Open carefully — 1638 calf binding is fragile. Read with clean hands. "
            "Store upright on a shelf with other folios, not flat. Keep away from "
            "direct sunlight. Handle the text block from the sides, not by the "
            "front cover. If you crack the spine, you lose years of value instantly."
        ),
        "fun_facts": [
            "A 1638 third-edition copy in good condition sells for £2,000–£5,000 at auction.",
            "Burton included a self-authored astrological chart predicting his own death — it was accurate.",
            "The book contains the longest known English sentence: a 4,000-word run-on in the preface.",
            "Samuel Johnson kept an early edition in his library and returned to it throughout his life for both scholarship and solace.",
        ],
    },
}


def generate_story(identification: IdentificationResult) -> Artifact:
    """Enrich an identification into a full Artifact with story."""
    story = STORIES.get(identification.name, _fallback_story(identification))
    return Artifact(
        name=identification.name,
        category=identification.category,
        description=identification.description,
        origin=story["origin"],
        era=story["era"],
        history=story["history"],
        cultural_significance=story["cultural_significance"],
        practical_uses=story["practical_uses"],
        fun_facts=story["fun_facts"],
    )


def _fallback_story(identification: IdentificationResult) -> dict:
    """Generic story for artifacts not in the library."""
    return {
        "origin": "Unknown origin",
        "era": "Undetermined",
        "history": f"{identification.name} is an object of type {identification.category}. "
        f"Detailed history is not yet available in the artifact library.",
        "cultural_significance": "Cultural significance data pending deeper research.",
        "practical_uses": f"A {identification.category} — typical uses vary. "
        "Inspect the object for manufacturer markings or instructions.",
        "fun_facts": [f"{identification.name} was logged in the Artifact Explorer database on an unknown date."],
    }