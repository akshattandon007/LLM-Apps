"""Stain removal database — stain + fabric → cleaning method."""

# Stain removal database
# Structure: stain_name -> {fabric_type -> (method, caution)}
# fabric_type "all" applies to all fabrics not otherwise specified

STAIN_DB = {
    "red wine": {
        "cotton": (
            "Blot excess immediately. Cover stain with salt to absorb remaining wine. "
            "Rinse with cold water from the back. Apply liquid laundry detergent and "
            "let sit 5 min. Launder in warm water with oxygen bleach.",
            "Do NOT use hot water — it sets the stain."
        ),
        "silk": (
            "Blot gently with a clean cloth. Mix 1 part white vinegar with 2 parts "
            "cold water. Dab the stain with this solution using a soft cloth. "
            "Rinse with cold water. If stain remains, take to a professional dry cleaner.",
            "Do NOT rub vigorously — silk is delicate. Do NOT use bleach."
        ),
        "wool": (
            "Blot excess wine. Sprinkle cornstarch or talcum powder to absorb. "
            "Let sit 15 min, then brush off. Mix mild detergent with cold water and "
            "dab the stain. Rinse thoroughly with cold water.",
            "Do NOT use hot water. Avoid alkaline cleaners (ammonia)."
        ),
        "synthetic": (
            "Blot excess. Rinse with cold water from the back of the fabric. "
            "Apply a drop of dish soap, work in gently. Rinse with cold water. "
            "Launder as usual with cold water.",
            "Do NOT use hot water. Polyester/nylon can be heat-sensitive."
        ),
        "carpet": (
            "Blot immediately with a clean white cloth (don't rub). "
            "Mix 1 tbsp dish soap + 1 tbsp white vinegar + 2 cups warm water. "
            "Dab the solution onto the stain, blot with a dry cloth. "
            "Repeat until stain lifts. Rinse with cold water and blot dry.",
            "Do NOT scrub — it spreads the stain. Blot from edges inward."
        ),
        "upholstery": (
            "Blot excess with a clean cloth. Mix 1 cup warm water with 1 tbsp "
            "dish soap. Dab the stain with a cloth dipped in the solution. "
            "Blot with a dry cloth. Repeat until clean. "
            "Vacuum the area when dry to restore texture.",
            "Test in an inconspicuous area first. Do NOT saturate the fabric."
        ),
        "all": (
            "Blot excess immediately. Rinse with cold water from the back. "
            "Apply a small amount of liquid detergent and work in gently. "
            "Launder or clean according to fabric care label.",
            "Always treat stains as soon as possible. Dried stains are much harder."
        ),
    },
    "coffee": {
        "cotton": (
            "Rinse with cold water immediately. Apply liquid laundry detergent "
            "directly to the stain and rub gently. Let sit 5 min. "
            "Launder in warm water with oxygen bleach. For dried stains, "
            "apply white vinegar before washing.",
            "Do NOT use soap before rinsing — it can set the stain."
        ),
        "silk": (
            "Blot gently. Mix 1 part white vinegar with 2 parts cold water. "
            "Dab with a soft cloth. Rinse with cold water. "
            "Professional dry cleaning recommended for valuable items.",
            "Do NOT rub. Avoid alkaline cleaners."
        ),
        "wool": (
            "Blot excess. Mix cool water with a few drops of mild wool-safe "
            "detergent. Dab the stain gently. Rinse with cool water. "
            "Lay flat to dry away from heat.",
            "Do NOT wring or twist. Do NOT use hot water."
        ),
        "synthetic": (
            "Rinse with cold water. Apply dish soap directly to stain and "
            "work in gently. Rinse. Launder as usual.",
            "Check care label — some synthetics are dry-clean only."
        ),
        "carpet": (
            "Blot immediately with a clean cloth. Mix 1 tbsp dish soap + "
            "1 tbsp white vinegar + 2 cups warm water. Dab onto stain, "
            "blot with dry cloth. Repeat. Rinse with cold water.",
            "Do NOT scrub. Blot from edges inward."
        ),
        "upholstery": (
            "Blot with a dry cloth. Mix mild detergent with cold water. "
            "Dab the stain. Blot dry. Repeat as needed.",
            "Test in an inconspicuous area first."
        ),
        "all": (
            "Blot or scrape excess. Rinse with cold water from the back. "
            "Apply a small amount of dish soap, work in gently. Rinse. "
            "For milk/cream coffee, use an enzyme-based cleaner.",
            "Treat quickly — coffee stains become permanent as they dry."
        ),
    },
    "grass": {
        "cotton": (
            "Pre-treat with liquid laundry detergent, rubbing gently. "
            "Let sit 15 min. Launder in warm water with oxygen bleach. "
            "For stubborn stains, apply rubbing alcohol with a cotton ball, "
            "then rinse and wash.",
            "Do NOT use chlorine bleach on colored fabrics."
        ),
        "silk": (
            "Take to a professional dry cleaner. Grass stains are very "
            "difficult to remove from silk.",
            "Do NOT attempt home remedies — silk is too delicate."
        ),
        "wool": (
            "Mix a few drops of mild detergent with cold water. Dab gently. "
            "Rinse thoroughly. If stain remains, consult a professional.",
            "Do NOT use rubbing alcohol on wool."
        ),
        "synthetic": (
            "Apply rubbing alcohol to a cloth and dab the stain. "
            "Rinse with cold water. Launder as usual.",
            "Test rubbing alcohol in an inconspicuous area first."
        ),
        "carpet": (
            "Mix 1 tbsp dish soap + 1 tbsp white vinegar + 2 cups warm water. "
            "Apply to stain and blot. If stain remains, apply rubbing alcohol "
            "with a cloth, then blot. Rinse with cold water.",
            "Do NOT scrub vigorously."
        ),
        "upholstery": (
            "Mix mild detergent with cold water. Dab the stain gently. "
            "Blot dry. For tough stains, use a small amount of rubbing alcohol.",
            "Test in an inconspicuous area first."
        ),
        "all": (
            "Pre-treat with laundry detergent or rubbing alcohol. "
            "Let sit 10-15 min. Launder in warm water. "
            "For dried stains, soak in warm water with enzyme detergent.",
            "Grass is a protein stain — hot water can set it initially."
        ),
    },
    "blood": {
        "cotton": (
            "Rinse with COLD water immediately (hot water sets blood stains). "
            "Apply hydrogen peroxide directly to the stain — it will fizz. "
            "Blot with a clean cloth. Repeat until stain is gone. "
            "Launder in cold water.",
            "NEVER use hot water — it cooks the protein and sets the stain permanently."
        ),
        "silk": (
            "Rinse with cold water. Mix a small amount of mild detergent with "
            "cold water and dab gently. Rinse thoroughly. "
            "Professional dry cleaning recommended.",
            "Do NOT use hydrogen peroxide on silk — it may damage the fibers."
        ),
        "wool": (
            "Rinse with cold water. Mix a few drops of mild wool detergent "
            "with cold water. Dab gently. Rinse. Repeat.",
            "Do NOT use hydrogen peroxide or bleach on wool."
        ),
        "synthetic": (
            "Rinse with cold water. Apply a drop of dish soap and work in gently. "
            "Rinse with cold water. Repeat until clean. Launder in cold water.",
            "Cold water only — even warm water can set blood."
        ),
        "carpet": (
            "Blot with a cloth soaked in cold water (don't rub). "
            "Mix 1 tbsp dish soap + 2 cups cold water. Dab onto stain, "
            "blot with dry cloth. For stubborn stains, apply hydrogen peroxide "
            "and blot after 5 min.",
            "Cold water ONLY. Do NOT use warm or hot water."
        ),
        "upholstery": (
            "Blot with a cloth soaked in cold water. Mix mild detergent "
            "with cold water. Dab gently. Blot dry. Repeat.",
            "Do NOT saturate the cushion. Cold water only."
        ),
        "all": (
            "Rinse with COLD water from the back of the fabric. "
            "Apply hydrogen peroxide or cold water + detergent. "
            "Blot, don't rub. Launder in cold water.",
            "Hot water, warm water, and heat drying all set blood stains permanently."
        ),
    },
    "grease_oil": {
        "cotton": (
            "Sprinkle cornstarch, baking soda, or talcum powder on the stain "
            "to absorb the grease. Let sit 15-30 min. Brush off powder. "
            "Apply dish soap directly to the stain and work in. "
            "Launder in HOT water with heavy-duty detergent.",
            "Do NOT rinse with water first — water repels oil."
        ),
        "silk": (
            "Sprinkle cornstarch on the stain. Let sit 30 min. Brush off. "
            "Take to a professional dry cleaner.",
            "Do NOT use dish soap or water on silk grease stains."
        ),
        "wool": (
            "Sprinkle cornstarch or baking soda. Let sit 30 min. Brush off. "
            "If stain remains, take to a professional cleaner.",
            "Do NOT use hot water on wool."
        ),
        "synthetic": (
            "Sprinkle baking soda on the stain. Let sit 15 min. Brush off. "
            "Apply dish soap, work in gently. Launder in warm water.",
            "Check care label — some synthetics are heat-sensitive."
        ),
        "carpet": (
            "Sprinkle baking soda generously. Let sit 30 min. Vacuum. "
            "Apply dish soap diluted in warm water. Blot with a clean cloth. "
            "Repeat. Rinse with cold water and blot dry.",
            "Do NOT rub — it spreads the grease."
        ),
        "upholstery": (
            "Sprinkle baking soda. Let sit 30 min. Vacuum. "
            "Mix dish soap with warm water. Dab the stain. Blot dry.",
            "Test in an inconspicuous area first."
        ),
        "all": (
            "Absorb excess grease with cornstarch, baking soda, or talcum powder. "
            "Let sit 15-30 min. Brush off. Apply dish soap to break down remaining oil. "
            "Launder in hottest water safe for the fabric.",
            "Do NOT use water first — it seals the oil into the fabric."
        ),
    },
    "ink": {
        "cotton": (
            "Place a cloth behind the stain. Apply rubbing alcohol with a "
            "cotton ball and blot — the ink will transfer to the backing cloth. "
            "Rinse. Repeat until no more ink transfers. Launder in warm water.",
            "Do NOT rub — it spreads the ink. Blot only."
        ),
        "silk": (
            "Take to a professional dry cleaner immediately. "
            "Ink is extremely difficult to remove from silk.",
            "Do NOT attempt home remedies on silk ink stains."
        ),
        "wool": (
            "Blot with rubbing alcohol using a cotton ball. "
            "Rinse with cold water. If stain persists, consult a professional.",
            "Test rubbing alcohol in an inconspicuous area first."
        ),
        "synthetic": (
            "Apply hairspray or rubbing alcohol to the stain. Blot. "
            "Rinse. Repeat. Launder as usual.",
            "Do NOT use acetone on synthetics — it can dissolve the fabric."
        ),
        "carpet": (
            "Blot with rubbing alcohol on a clean cloth. "
            "The ink should transfer to the cloth. Keep blotting with fresh "
            "areas of the cloth until no more ink transfers. "
            "Rinse with cold water and blot dry.",
            "Do NOT saturate the carpet pad underneath."
        ),
        "upholstery": (
            "Apply rubbing alcohol to a clean cloth and dab the stain. "
            "Blot with a dry cloth. Repeat. Rinse with cold water.",
            "Test in an inconspicuous area first."
        ),
        "all": (
            "Act fast — fresh ink is much easier to remove. "
            "Use rubbing alcohol or hairspray. Blot (don't rub) from the "
            "outside of the stain inward to prevent spreading.",
            "Different inks (ballpoint, gel, fountain pen) may need different solvents."
        ),
    },
    "tomato_sauce": {
        "cotton": (
            "Scrape off excess sauce. Rinse with cold water from the back. "
            "Apply liquid laundry detergent and let sit 5 min. "
            "Launder in warm water with oxygen bleach. For dried stains, "
            "apply white vinegar before washing.",
            "Do NOT use hot water initially — it cooks the tomato into the fabric."
        ),
        "silk": (
            "Scrape gently. Dab with a solution of white vinegar and cold water "
            "(1:2 ratio). Rinse with cold water. "
            "Professional dry cleaning recommended.",
            "Do NOT rub vigorously."
        ),
        "wool": (
            "Scrape excess. Dab with cold water and mild detergent. "
            "Rinse thoroughly. If stain remains, consult a professional.",
            "Do NOT use hot water or bleach."
        ),
        "synthetic": (
            "Scrape excess. Rinse with cold water. Apply dish soap, work in gently. "
            "Rinse. Launder in warm water.",
            "Check care label first."
        ),
        "carpet": (
            "Scrape excess. Mix 1 tbsp dish soap + 1 cup cold water. "
            "Dab onto stain. Blot. Repeat. Rinse with cold water.",
            "Do NOT rub — it drives the stain deeper."
        ),
        "upholstery": (
            "Scrape excess. Mix mild detergent with cold water. "
            "Dab the stain. Blot dry. Repeat as needed.",
            "Test in an inconspicuous area first."
        ),
        "all": (
            "Scrape off solids. Rinse with COLD water from the back. "
            "Pre-treat with laundry detergent. Launder in warm water. "
            "For oily sauces (pizza), pre-treat grease first.",
            "Heat sets tomato stains — avoid hot water and dryers until the stain is gone."
        ),
    },
    "mud": {
        "cotton": (
            "Let the mud dry completely first. Brush off dried mud. "
            "Apply liquid laundry detergent and work in. "
            "Launder in warm water. For stubborn stains, pre-soak.",
            "Do NOT rub wet mud — it drives particles deeper into fibers."
        ),
        "silk": (
            "Let dry completely. Gently brush off. "
            "Take to a professional dry cleaner.",
            "Do NOT attempt to wash silk mud stains at home."
        ),
        "wool": (
            "Let dry completely. Brush off. "
            "Dab with cold water and mild wool detergent. Rinse gently.",
            "Do NOT wring or twist wool."
        ),
        "synthetic": (
            "Let dry. Brush off. Apply detergent and launder as usual.",
            "Easy to remove from synthetics — just let it dry first."
        ),
        "carpet": (
            "Let dry completely. Vacuum thoroughly. "
            "Mix dish soap with warm water. Dab the remaining stain. "
            "Blot dry. Repeat.",
            "Do NOT rub wet mud into carpet — let it dry first."
        ),
        "upholstery": (
            "Let dry. Brush or vacuum off. "
            "Dab with mild detergent solution. Blot dry.",
            "Test in an inconspicuous area first."
        ),
        "all": (
            "Let the mud DRY completely before treating. "
            "Brush off as much dry mud as possible. "
            "Then treat remaining stain with detergent and launder.",
            "Wet mud = wet dirt = smear. Dry mud = powder = brush off easily."
        ),
    },
    "wax": {
        "cotton": (
            "Harden the wax with an ice cube in a plastic bag. "
            "Scrape off hardened wax with a dull knife. "
            "Place paper towel over and under the stain, iron on low heat — "
            "the wax will melt and transfer to the paper. Repeat with fresh paper. "
            "Treat any remaining dye stain with rubbing alcohol.",
            "Do NOT scrape without hardening first — it spreads the wax."
        ),
        "silk": (
            "Harden with ice. Scrape gently. "
            "Take to a professional dry cleaner for the remaining stain.",
            "Do NOT use an iron on silk — it will damage the fabric."
        ),
        "wool": (
            "Harden with ice. Scrape. Use paper towel + low heat iron method. "
            "Wool can tolerate low heat. Treat remaining stain professionally.",
            "Test iron heat in an inconspicuous area first."
        ),
        "synthetic": (
            "Harden with ice. Scrape. Use paper towel + low heat iron. "
            "Synthetics melt easily — use very low heat.",
            "Use the lowest iron setting. Synthetics melt at high temperatures."
        ),
        "carpet": (
            "Harden with ice cubes in a bag. Scrape off wax. "
            "Place a brown paper bag or paper towel over the wax spot. "
            "Iron on low heat — wax transfers to the paper. Repeat.",
            "Do NOT use high heat — it can melt the carpet fibers."
        ),
        "upholstery": (
            "Harden with ice. Scrape. Use paper towel + low heat iron. "
            "Treat remaining stain with rubbing alcohol.",
            "Test iron heat in an inconspicuous area first."
        ),
        "all": (
            "Harden wax with ice first. Scrape off as much as possible. "
            "Use paper towels + warm iron to melt and absorb remaining wax. "
            "Treat any dye residue with rubbing alcohol or stain remover.",
            "Candle wax is oil-based — dish soap helps with residue."
        ),
    },
    "marker": {
        "cotton": (
            "For permanent marker: apply rubbing alcohol and blot. "
            "For dry-erase marker: apply more dry-erase marker and wipe. "
            "For washable marker: rinse with cold water and launder. "
            "Rubbing alcohol works on most marker stains.",
            "Test rubbing alcohol in an inconspicuous area first."
        ),
        "silk": (
            "Take to a professional dry cleaner. "
            "Marker stains are extremely difficult on silk.",
            "Do NOT use rubbing alcohol on silk."
        ),
        "wool": (
            "Blot with rubbing alcohol using a cotton ball. "
            "Rinse with cold water. If stain persists, professional cleaning.",
            "Test in an inconspicuous area first."
        ),
        "synthetic": (
            "Apply rubbing alcohol to a cloth and blot. "
            "Rinse. Repeat. Launder as usual.",
            "Test in an inconspicuous area first."
        ),
        "carpet": (
            "Blot with rubbing alcohol. The marker should transfer to the cloth. "
            "Keep blotting with fresh cloth areas. Rinse with cold water.",
            "Do NOT saturate the carpet pad."
        ),
        "upholstery": (
            "Blot with rubbing alcohol. Blot dry. Repeat. Rinse.",
            "Test in an inconspicuous area first."
        ),
        "all": (
            "Act fast. Rubbing alcohol or hand sanitizer works on most markers. "
            "Blot (don't rub) from outside inward. "
            "For whiteboards on clothing, the marker ink is usually alcohol-based.",
            "Different markers (permanent, dry-erase, highlighters) need different solvents."
        ),
    },
    "sweat": {
        "cotton": (
            "Make a paste of baking soda and water. Apply to the stain. "
            "Let sit 30 min. Brush off. Launder in warm water. "
            "For yellow underarm stains, apply white vinegar before washing.",
            "Do NOT use chlorine bleach on yellow sweat stains — it makes them worse."
        ),
        "silk": (
            "Mix a few drops of mild detergent with cold water. "
            "Dab gently. Rinse. Professional cleaning recommended.",
            "Do NOT use baking soda or vinegar on silk."
        ),
        "wool": (
            "Dab with cold water and mild wool detergent. "
            "Rinse thoroughly. Air dry away from heat.",
            "Do NOT use hot water."
        ),
        "synthetic": (
            "Apply baking soda paste. Let sit 15 min. "
            "Rinse. Launder in warm water with enzyme detergent.",
            "Check care label."
        ),
        "all": (
            "Pre-treat with baking soda paste or white vinegar. "
            "Let sit 30 min. Launder in warm water. "
            "Enzyme-based detergents work best on sweat stains.",
            "Antiperspirant + sweat = yellow stains. Switch to deodorant to prevent."
        ),
    },
    "wine_white": {
        "cotton": (
            "Rinse with cold water. Apply liquid detergent and let sit 5 min. "
            "Launder in warm water with oxygen bleach. "
            "For stubborn stains, soak in cold water with oxygen bleach overnight.",
            "White wine stains are less visible but still set with heat."
        ),
        "silk": (
            "Dab with cold water and a few drops of mild detergent. "
            "Rinse. Professional dry cleaning recommended.",
            "Do NOT rub."
        ),
        "wool": (
            "Dab with cold water and mild detergent. Rinse. "
            "Air dry away from heat.",
            "Do NOT use hot water."
        ),
        "all": (
            "Rinse with cold water. Apply detergent. Launder as usual. "
            "White wine stains are usually less stubborn than red wine, "
            "but still treat promptly.",
            "Salt is less effective on white wine — use detergent instead."
        ),
    },
    "chocolate": {
        "cotton": (
            "Scrape off excess. Rinse with cold water. "
            "Apply liquid laundry detergent and work in. Let sit 5 min. "
            "Launder in warm water with oxygen bleach. "
            "For stubborn stains, pre-soak in enzyme detergent.",
            "Do NOT use hot water initially — chocolate has both oil and protein."
        ),
        "silk": (
            "Scrape gently. Dab with cold water and mild detergent. "
            "Professional dry cleaning recommended.",
            "Do NOT rub."
        ),
        "wool": (
            "Scrape excess. Dab with cold water and mild detergent. "
            "Rinse. If stain remains, professional cleaning.",
            "Do NOT use hot water."
        ),
        "synthetic": (
            "Scrape excess. Rinse with cold water. Apply dish soap. "
            "Rinse. Launder as usual.",
            "Check care label."
        ),
        "carpet": (
            "Scrape excess. Mix dish soap with cold water. Dab stain. "
            "Blot. Repeat. Rinse with cold water.",
            "Do NOT rub."
        ),
        "upholstery": (
            "Scrape excess. Mix mild detergent with cold water. "
            "Dab stain. Blot dry. Repeat.",
            "Test in an inconspicuous area first."
        ),
        "all": (
            "Scrape off excess. Rinse with cold water. "
            "Pre-treat with enzyme detergent or dish soap. "
            "Launder in warm water.",
            "Chocolate has both oil (cocoa butter) and protein (milk) — treat both."
        ),
    },
    "berry": {
        "cotton": (
            "Rinse with cold water immediately. Apply white vinegar to the stain. "
            "Let sit 5 min. Rinse. Apply laundry detergent. "
            "Launder in warm water with oxygen bleach. "
            "For stubborn stains, soak in oxygen bleach solution.",
            "Do NOT use soap first — vinegar neutralizes berry pigments better."
        ),
        "silk": (
            "Dab with white vinegar diluted in cold water (1:3 ratio). "
            "Rinse. Professional dry cleaning recommended.",
            "Do NOT rub."
        ),
        "wool": (
            "Dab with diluted white vinegar. Rinse with cold water. "
            "If stain persists, professional cleaning.",
            "Do NOT use hot water."
        ),
        "carpet": (
            "Blot immediately. Mix 1 tbsp white vinegar + 2 cups cold water. "
            "Dab onto stain. Blot. Repeat. Rinse with cold water.",
            "Do NOT rub."
        ),
        "all": (
            "Treat immediately. White vinegar neutralizes berry pigments. "
            "Rinse with cold water. Apply laundry detergent. "
            "Launder in warm water. Sunlight also helps bleach berry stains.",
            "Berries are tannin stains — vinegar works better than soap initially."
        ),
    },
    "pet_stains": {
        "cotton": (
            "Blot up excess. Apply an enzyme-based cleaner (or mix 1 part "
            "white vinegar with 1 part water). Let sit 10 min. Blot. "
            "Sprinkle baking soda, then spray with hydrogen peroxide. "
            "Let sit 15 min. Vacuum when dry.",
            "Do NOT use ammonia — it smells like urine to pets and encourages repeat marking."
        ),
        "carpet": (
            "Blot up as much as possible. Apply enzyme cleaner or vinegar solution. "
            "Let sit 10-15 min. Blot. Sprinkle baking soda generously. "
            "Mix 1 cup hydrogen peroxide + 1 tsp dish soap. Spray over baking soda. "
            "Let dry completely, then vacuum.",
            "Do NOT use steam cleaners — heat sets the stain and odor."
        ),
        "upholstery": (
            "Blot excess. Apply enzyme cleaner or diluted white vinegar. "
            "Let sit 10 min. Blot. Sprinkle baking soda. Let dry. Vacuum.",
            "Test in an inconspicuous area first. Do NOT saturate."
        ),
        "all": (
            "Act fast — dried pet stains are much harder. "
            "Enzyme-based cleaners are best for breaking down urine proteins. "
            "Blacklight helps locate dried stains. "
            "NEVER use ammonia-based cleaners on pet stains.",
            "Regular detergent won't fully remove urine — you need enzyme cleaners."
        ),
    },
}

FABRIC_TYPES = [
    "cotton", "silk", "wool", "synthetic", "carpet", "upholstery", "all"
]

STAIN_TYPES = sorted(STAIN_DB.keys())


def lookup(stain: str, fabric: str) -> dict | None:
    """Look up a stain + fabric combo. Returns dict with method, caution, or None."""
    stain_lower = stain.strip().lower()
    fabric_lower = fabric.strip().lower()

    if stain_lower not in STAIN_DB:
        return None

    fabric_entry = STAIN_DB[stain_lower]
    if fabric_lower in fabric_entry:
        method, caution = fabric_entry[fabric_lower]
    elif "all" in fabric_entry:
        method, caution = fabric_entry["all"]
    else:
        return None

    return {
        "stain": stain_lower,
        "fabric": fabric_lower,
        "method": method,
        "caution": caution,
    }


def list_stains() -> list[str]:
    """Return sorted list of all known stain types."""
    return STAIN_TYPES


def list_fabrics() -> list[str]:
    """Return list of fabric types."""
    return FABRIC_TYPES