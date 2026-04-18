# chatbot.py
# This file handles:
# 1. The conversation flow (what questions to ask and when)
# 2. Building a user profile from answers
# 3. Scoring each hobby against the user profile
# 4. Returning ranked recommendations with reasoning

from hobbies import HOBBIES


# ─────────────────────────────────────────────
# CONVERSATION QUESTIONS
# Each question has an 'id', the text to show
# the user, and the answer options.
# ─────────────────────────────────────────────
QUESTIONS = [
    {
        "id": "personality",
        "text": "How would you describe your social energy?",
        "options": [
            "Introvert — I recharge alone",
            "Extrovert — I thrive around people",
            "Ambivert — a bit of both"
        ]
    },
    {
        "id": "creative_type",
        "text": "When you imagine creating something, what excites you most?",
        "options": [
            "Visual things — drawing, painting, design",
            "Words — writing, stories, poetry",
            "Sound — music, beats, audio",
            "Hands-on — crafts, building, making"
        ]
    },
    {
        "id": "time",
        "text": "How much free time can you dedicate to a hobby each day?",
        "options": [
            "15–30 minutes",
            "1–2 hours",
            "Weekends only",
            "Flexible"
        ]
    },
    {
        "id": "goal",
        "text": "What's your main goal with this hobby?",
        "options": [
            "Relax and de-stress",
            "Learn something new",
            "Express myself creatively",
            "Turn it into a side hustle or career"
        ]
    },
    {
        "id": "energy",
        "text": "How do you feel after a typical day?",
        "options": [
            "Pretty drained — I need low-effort activities",
            "Moderate energy — something light but engaging",
            "High energy — bring on the challenge!",
            "It varies day to day"
        ]
    }
]


# ─────────────────────────────────────────────
# ANSWER → PROFILE MAPPER
# Converts raw answer text into clean keywords
# that the scoring engine can work with.
# ─────────────────────────────────────────────
def build_profile(answers: dict) -> dict:
    """
    Takes the raw answers dict like:
      {"personality": "Introvert — I recharge alone", ...}
    Returns a clean profile dict like:
      {"personality": "introvert", "interests": ["visual", "creative"], ...}
    """
    profile = {
        "personality": "ambivert",
        "interests": [],
        "time": "short",
        "goal": "express",
        "energy": "moderate"
    }

    # --- Personality ---
    p = answers.get("personality", "").lower()
    if "introvert" in p:
        profile["personality"] = "introvert"
    elif "extrovert" in p:
        profile["personality"] = "extrovert"
    else:
        profile["personality"] = "ambivert"

    # --- Creative interests ---
    c = answers.get("creative_type", "").lower()
    if "visual" in c or "drawing" in c or "design" in c:
        profile["interests"] += ["visual", "creative", "drawing", "art", "design", "color"]
    if "word" in c or "writing" in c or "stories" in c:
        profile["interests"] += ["writing", "words", "stories", "blog", "ideas"]
    if "sound" in c or "music" in c or "audio" in c:
        profile["interests"] += ["music", "sound", "beats", "audio", "compose"]
    if "hands" in c or "crafts" in c or "building" in c:
        profile["interests"] += ["crafts", "making", "hands-on", "diy", "physical"]

    # --- Time available ---
    t = answers.get("time", "").lower()
    if "15" in t or "30" in t:
        profile["time"] = "short"
    elif "1" in t or "2" in t:
        profile["time"] = "medium"
    else:
        profile["time"] = "flexible"

    # --- Goal ---
    g = answers.get("goal", "").lower()
    if "relax" in g or "stress" in g:
        profile["goal"] = "relax"
    elif "learn" in g:
        profile["goal"] = "learn"
    elif "express" in g or "creative" in g:
        profile["goal"] = "express"
    elif "hustle" in g or "career" in g:
        profile["goal"] = "career"

    # --- Energy level ---
    e = answers.get("energy", "").lower()
    if "drained" in e or "low" in e:
        profile["energy"] = "low"
    elif "high" in e or "challenge" in e:
        profile["energy"] = "high"
    elif "varies" in e:
        profile["energy"] = "moderate"
    else:
        profile["energy"] = "moderate"

    return profile


# ─────────────────────────────────────────────
# SCORING ENGINE
# Compares the user profile against each hobby
# and returns a match percentage + reasoning.
# ─────────────────────────────────────────────
def score_hobby(profile: dict, hobby: dict) -> int:
    """
    Scores a single hobby against the user profile.
    Returns a score from 0 to 100.

    Scoring breakdown:
    - Keyword match:      up to 50 points
    - Personality fit:    up to 20 points
    - Goal fit:           up to 20 points
    - Energy fit:         up to 10 points
    """
    score = 0

    # 1. Keyword matching (up to 50 pts)
    #    Each matching interest keyword = +10 points (max 5 matches)
    matched_keywords = 0
    for interest in profile["interests"]:
        if interest in hobby["keywords"]:
            matched_keywords += 1
    # Cap keyword contribution at 50 points
    score += min(matched_keywords * 10, 50)

    # 2. Personality fit (up to 20 pts)
    if profile["personality"] in hobby["personality_fit"]:
        score += 20

    # 3. Goal fit (up to 20 pts)
    goal_map = {
        "relax":   "relax",
        "learn":   "learn",
        "express": "express",
        "career":  "career"
    }
    mapped_goal = goal_map.get(profile["goal"], "express")
    if mapped_goal in hobby.get("goal_fit", []):
        score += 20

    # 4. Energy fit (up to 10 pts)
    if profile["energy"] in hobby["energy_fit"]:
        score += 10
    elif profile["energy"] == "moderate":
        # moderate energy fits most hobbies partially
        score += 5

    return min(score, 100)  # never exceed 100%


# ─────────────────────────────────────────────
# RECOMMENDATION ENGINE
# Runs scoring on all hobbies and returns
# the top N ranked by match score.
# ─────────────────────────────────────────────
def get_recommendations(profile: dict, top_n: int = 5) -> list:
    """
    Returns a sorted list of hobby recommendations.
    Each item is a dict with: name, score, hobby data.
    """
    results = []

    for hobby_key, hobby_data in HOBBIES.items():
        score = score_hobby(profile, hobby_data)
        results.append({
            "key": hobby_key,
            "name": hobby_data["name"],
            "score": score,
            "data": hobby_data
        })

    # Sort by score, highest first
    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:top_n]


# ─────────────────────────────────────────────
# CONVERSATION STATE MANAGER
# Tracks where the user is in the Q&A flow.
# ─────────────────────────────────────────────
class ConversationManager:
    def __init__(self):
        self.reset()

    def reset(self):
        """Start a fresh conversation."""
        self.step = 0           # which question we're on
        self.answers = {}       # collected answers so far
        self.profile = None     # built after all answers collected
        self.recommendations = []
        self.done = False

    def get_next_message(self) -> dict:
        """
        Returns the next message/question to show.
        Format: {"type": "question"/"result"/"text", "content": ..., "options": [...]}
        """
        # --- Greeting (step 0) ---
        if self.step == 0:
            return {
                "type": "text",
                "content": "Hey there! 👋 I'm your Hobby Discovery Bot. I'll ask you 5 quick questions and then recommend hobbies perfectly matched to your personality and lifestyle. Ready? Let's go!",
                "auto_advance": True   # frontend will show next question automatically
            }

        # --- Questions (steps 1–5) ---
        q_index = self.step - 1
        if q_index < len(QUESTIONS):
            q = QUESTIONS[q_index]
            return {
                "type": "question",
                "question_id": q["id"],
                "content": q["text"],
                "options": q["options"],
                "step": self.step,
                "total": len(QUESTIONS)
            }

        # --- All questions answered → show results ---
        if not self.done:
            self.profile = build_profile(self.answers)
            self.recommendations = get_recommendations(self.profile)
            self.done = True

        return {
            "type": "results",
            "profile": self.profile,
            "recommendations": self.recommendations
        }

    def submit_answer(self, question_id: str, answer: str):
        """Record a user's answer and advance the step."""
        self.answers[question_id] = answer
        self.step += 1

    def get_hobby_detail(self, hobby_key: str) -> dict:
        """Return the full details for a specific hobby."""
        return HOBBIES.get(hobby_key, {})
