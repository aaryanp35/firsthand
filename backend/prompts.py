"""
All prompt templates for Walk A Mile.
Isolated here so they can be tuned without touching any other file.
"""

# ─────────────────────────────────────────────
# STEP 1: Classify the article
# ─────────────────────────────────────────────

CLASSIFIER_PROMPT = """You are analyzing a news article to understand its political lean and the core human tension underneath it.

Return ONLY a valid JSON object — no markdown, no explanation, no extra text. Exactly this structure:

{{
  "topic": "brief topic in 8 words or fewer",
  "article_lean": "left" or "right" or "neutral",
  "lean_confidence": "high" or "medium" or "low",
  "core_tension": {{
    "article_side_value": "the fear or value driving the article's perspective — one plain sentence",
    "other_side_value": "the fear or value driving the opposing perspective — one plain sentence, grounded in lived experience not ideology"
  }},
  "other_side_profile": {{
    "region": "one of: rural South | rural Midwest | rural West | small-town Northeast | suburban South | suburban Midwest | suburban West | urban",
    "occupation": "one specific, realistic occupation for someone likely on the other side",
    "life_stage": "one of: young adult (20s) | young parent (late 20s-30s) | middle-aged parent (40s) | older adult (50s-60s) | retired (65+)",
    "anchor_theme": "a specific life experience — NOT a belief — that would connect this person emotionally to this issue. One brief phrase."
  }},
  "skip": false
}}

If the article has no meaningful political or values-based tension (e.g. sports, entertainment, pure science news), return the same structure but set "skip": true and leave other fields as empty strings.

ARTICLE:
{article_text}
"""


# ─────────────────────────────────────────────
# STEP 2: Generate the story
# ─────────────────────────────────────────────

STORY_PROMPT = """You are writing a short first-person piece in the voice of a real, specific American.

CHARACTER:
- Name: {name}
- Age: {age}
- Location: {location}
- Occupation: {occupation}
- Something that shaped them: {anchor_theme}

CONTEXT:
The reader just finished an article about: {topic}
The reader's article leaned {article_lean}.
This story comes from someone whose life put them on the other side — not because of politics, but because of where they grew up, what they've been through, what they care about protecting.
Their core experience: {other_side_value}

RULES — every single one matters:

1. Start with a specific moment, image, or physical detail. NOT "I've always believed" or "I think" or "Growing up."
2. Include one concrete scene — a specific place, a specific moment in time, something that happened.
3. Never mention: political parties, politicians by name, statistics, polling, policy names, ideology labels.
4. Never draw a moral. Never say "and that's why I..." or "I guess what I'm trying to say is..."
5. Write in a natural, slightly uneven voice — contractions, run-on thoughts, simple words. Like someone talking, not writing.
6. 290–340 words exactly.
7. End mid-thought. No resolution. No conclusion. Just... stop. Like the person got interrupted or ran out of words.
8. The goal: the reader should feel like they just met a real person. Not like they read a perspective piece.

Write only the story. No title. No label. No "Here is the story:". Just start writing as {name}.
"""


# ─────────────────────────────────────────────
# Name banks by region (for realistic persona generation)
# ─────────────────────────────────────────────

NAMES_BY_REGION = {
    "rural South": {
        "male": ["Bobby", "Travis", "Dale", "Cody", "Jimmy", "Wayne", "Randy", "Ricky", "Donnie", "Earl"],
        "female": ["Brenda", "Tammy", "Crystal", "Sherry", "Donna", "Cindy", "Misty", "Kayla", "Tiffany", "Lisa"],
    },
    "rural Midwest": {
        "male": ["Gary", "Kevin", "Todd", "Brad", "Scott", "Doug", "Mike", "Jeff", "Dan", "Craig"],
        "female": ["Debra", "Karen", "Sandy", "Pam", "Judy", "Barb", "Linda", "Carol", "Diane", "Sharon"],
    },
    "rural West": {
        "male": ["Cole", "Dustin", "Tyler", "Wade", "Brent", "Chad", "Jared", "Lance", "Shane", "Troy"],
        "female": ["Amber", "Heather", "Stacy", "Wendy", "Mandy", "Ashley", "Jodi", "Tara", "Carrie", "Nicole"],
    },
    "small-town Northeast": {
        "male": ["Frank", "Paul", "Joe", "Rich", "Dennis", "Tom", "Steve", "Bill", "Dave", "Lou"],
        "female": ["Maureen", "Patricia", "Kathleen", "Joanne", "Marie", "Rosemary", "Eileen", "Colleen", "Jean", "Ann"],
    },
    "suburban South": {
        "male": ["Brandon", "Justin", "Derek", "Marcus", "Keith", "Eric", "Chris", "Ryan", "Aaron", "Brian"],
        "female": ["Jennifer", "Michelle", "Stephanie", "Amanda", "Jessica", "Kimberly", "Melissa", "Rebecca", "Courtney", "Lauren"],
    },
    "suburban Midwest": {
        "male": ["Jason", "Derek", "Nathan", "Adam", "Kyle", "Brett", "Greg", "Josh", "Cory", "Sean"],
        "female": ["Rachel", "Megan", "Alicia", "Heather", "Erin", "Katie", "Amy", "Sarah", "Jill", "Natalie"],
    },
    "suburban West": {
        "male": ["Derek", "Austin", "Ryan", "Zach", "Trevor", "Dylan", "Cameron", "Logan", "Jordan", "Hunter"],
        "female": ["Brittany", "Kelsey", "Chelsea", "Taylor", "Morgan", "Madison", "Alexis", "Caitlin", "Brooke", "Haley"],
    },
    "urban": {
        "male": ["Marcus", "Andre", "Darnell", "James", "Kevin", "Michael", "Terrence", "Leon", "Malik", "Raymond"],
        "female": ["Keisha", "Tanya", "Monique", "Latasha", "Renee", "Yolanda", "Denise", "Jasmine", "Simone", "Aaliyah"],
    },
}

AGES_BY_LIFE_STAGE = {
    "young adult (20s)": (22, 29),
    "young parent (late 20s-30s)": (27, 39),
    "middle-aged parent (40s)": (40, 49),
    "older adult (50s-60s)": (50, 64),
    "retired (65+)": (65, 78),
}

LOCATIONS_BY_REGION = {
    "rural South": ["Harlan, KY", "Hazard, KY", "Greenville, MS", "Gadsden, AL", "Clarksville, TN", "Natchitoches, LA", "Waycross, GA", "Lufkin, TX"],
    "rural Midwest": ["Chillicothe, OH", "Joplin, MO", "Ottumwa, IA", "Emporia, KS", "Muncie, IN", "Findlay, OH", "Carbondale, IL", "Owatonna, MN"],
    "rural West": ["Pocatello, ID", "Casper, WY", "Roswell, NM", "Yuma, AZ", "Twin Falls, ID", "Billings, MT", "Grand Junction, CO", "Elko, NV"],
    "small-town Northeast": ["Scranton, PA", "Utica, NY", "Bangor, ME", "Claremont, NH", "Johnstown, PA", "Binghamton, NY", "Fitchburg, MA", "Rutland, VT"],
    "suburban South": ["Murfreesboro, TN", "Kennesaw, GA", "Pearland, TX", "Mooresville, NC", "Katy, TX", "Smyrna, GA", "Brentwood, TN", "Collierville, TN"],
    "suburban Midwest": ["Naperville, IL", "Overland Park, KS", "Carmel, IN", "Fishers, IN", "Shawnee, KS", "Edina, MN", "Westerville, OH", "Gahanna, OH"],
    "suburban West": ["Gilbert, AZ", "Surprise, AZ", "Henderson, NV", "Temecula, CA", "Folsom, CA", "Highlands Ranch, CO", "Meridian, ID", "Sammamish, WA"],
    "urban": ["Detroit, MI", "Baltimore, MD", "Memphis, TN", "Newark, NJ", "Cleveland, OH", "Milwaukee, WI", "Birmingham, AL", "St. Louis, MO"],
}
