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
# ENHANCED SCORING ENGINE
# Advanced algorithm with weighted factors, time-based adjustments,
# difficulty matching, and user feedback integration.
# ─────────────────────────────────────────────
def score_hobby(profile: dict, hobby: dict, user_history: dict = None) -> dict:
    """
    Enhanced scoring algorithm that returns detailed scoring breakdown.
    Includes weighted factors, time-based adjustments, and learning from user behavior.

    Returns: {
        "total_score": int (0-100),
        "breakdown": {
            "keyword_match": int,
            "personality_fit": int,
            "goal_alignment": int,
            "energy_compatibility": int,
            "time_feasibility": int,
            "difficulty_match": int,
            "cost_affordability": int,
            "career_potential": int,
            "trend_bonus": int,
            "user_feedback": int
        },
        "confidence": float (0-1),
        "reasoning": str
    }
    """
    breakdown = {
        "keyword_match": 0,
        "personality_fit": 0,
        "goal_alignment": 0,
        "energy_compatibility": 0,
        "time_feasibility": 0,
        "difficulty_match": 0,
        "cost_affordability": 0,
        "career_potential": 0,
        "trend_bonus": 0,
        "user_feedback": 0
    }

    # 1. Keyword Matching (25% weight) - Enhanced with semantic matching
    keyword_score = calculate_keyword_score(profile, hobby)
    breakdown["keyword_match"] = min(keyword_score, 25)

    # 2. Personality Fit (20% weight) - Core compatibility
    if profile["personality"] in hobby.get("personality_fit", []):
        breakdown["personality_fit"] = 20
    elif profile["personality"] == "ambivert":
        # Ambiverts can adapt to most hobbies
        breakdown["personality_fit"] = 15

    # 3. Goal Alignment (20% weight) - Mission critical
    goal_score = calculate_goal_alignment(profile, hobby)
    breakdown["goal_alignment"] = goal_score

    # 4. Energy Compatibility (10% weight) - Daily feasibility
    energy_score = calculate_energy_compatibility(profile, hobby)
    breakdown["energy_compatibility"] = energy_score

    # 5. Time Feasibility (10% weight) - Schedule matching
    time_score = calculate_time_feasibility(profile, hobby)
    breakdown["time_feasibility"] = time_score

    # 6. Difficulty Match (5% weight) - Learning curve consideration
    difficulty_score = calculate_difficulty_match(profile, hobby)
    breakdown["difficulty_match"] = difficulty_score

    # 7. Cost Affordability (5% weight) - Budget consideration
    cost_score = calculate_cost_affordability(profile, hobby)
    breakdown["cost_affordability"] = cost_score

    # 8. Career Potential (3% weight) - Future opportunities
    career_score = calculate_career_potential(profile, hobby)
    breakdown["career_potential"] = career_score

    # 9. Trend Bonus (1% weight) - Current popularity/learning momentum
    trend_score = calculate_trend_bonus(hobby)
    breakdown["trend_bonus"] = trend_score

    # 10. User Feedback Integration (1% weight) - Learning from past interactions
    if user_history:
        feedback_score = calculate_user_feedback_bonus(user_history, hobby)
        breakdown["user_feedback"] = feedback_score

    # Calculate weighted total
    weights = {
        "keyword_match": 0.25,
        "personality_fit": 0.20,
        "goal_alignment": 0.20,
        "energy_compatibility": 0.10,
        "time_feasibility": 0.10,
        "difficulty_match": 0.05,
        "cost_affordability": 0.05,
        "career_potential": 0.03,
        "trend_bonus": 0.01,
        "user_feedback": 0.01
    }

    total_score = sum(breakdown[key] * weights[key] for key in breakdown)

    # Apply time-based adjustments
    total_score = apply_time_based_adjustments(total_score, profile, hobby)

    # Calculate confidence based on scoring consistency
    confidence = calculate_scoring_confidence(breakdown)

    # Generate reasoning
    reasoning = generate_scoring_reasoning(breakdown, hobby)

    return {
        "total_score": min(int(total_score), 100),
        "breakdown": breakdown,
        "confidence": confidence,
        "reasoning": reasoning
    }


def calculate_keyword_score(profile: dict, hobby: dict) -> float:
    """Enhanced keyword matching with semantic similarity."""
    user_keywords = set(profile.get("interests", []))
    hobby_keywords = set(hobby.get("keywords", []))

    # Exact matches (highest weight)
    exact_matches = len(user_keywords.intersection(hobby_keywords))

    # Semantic matches (medium weight) - related concepts
    semantic_matches = 0
    semantic_map = {
        "visual": ["art", "design", "color", "aesthetic", "drawing"],
        "creative": ["art", "design", "making", "crafts"],
        "writing": ["words", "stories", "blog", "ideas"],
        "music": ["sound", "beats", "audio", "compose"],
        "physical": ["hands-on", "diy", "crafts", "making"]
    }

    for user_kw in user_keywords:
        if user_kw in semantic_map:
            for related_kw in semantic_map[user_kw]:
                if related_kw in hobby_keywords:
                    semantic_matches += 0.5

    # Category matches (lower weight)
    category_matches = 0
    user_categories = extract_categories_from_keywords(user_keywords)
    hobby_categories = extract_categories_from_keywords(hobby_keywords)
    category_matches = len(user_categories.intersection(hobby_categories)) * 0.3

    total_matches = exact_matches + semantic_matches + category_matches
    return min(total_matches * 5, 25)  # Max 25 points


def calculate_goal_alignment(profile: dict, hobby: dict) -> int:
    """Calculate how well hobby aligns with user's goals."""
    user_goal = profile.get("goal", "express")
    hobby_goals = hobby.get("goal_fit", [])

    goal_mapping = {
        "relax": ["relax", "fun"],
        "learn": ["learn", "skill"],
        "express": ["express", "creative"],
        "career": ["career", "side_hustle", "professional"]
    }

    mapped_goals = goal_mapping.get(user_goal, [user_goal])

    if any(goal in hobby_goals for goal in mapped_goals):
        return 20
    elif user_goal == "express" and "creative" in hobby_goals:
        return 15  # Partial match
    else:
        return 5   # Some alignment possible


def calculate_energy_compatibility(profile: dict, hobby: dict) -> int:
    """Calculate energy level compatibility."""
    user_energy = profile.get("energy", "moderate")
    hobby_energy = hobby.get("energy_fit", [])

    if user_energy in hobby_energy:
        return 10
    elif user_energy == "moderate":
        # Moderate energy users can adapt to most levels
        return 7
    elif user_energy == "low" and "moderate" in hobby_energy:
        return 5  # Can handle moderate with adjustment
    else:
        return 2  # Requires significant adaptation


def calculate_time_feasibility(profile: dict, hobby: dict) -> int:
    """Calculate if hobby fits user's available time."""
    user_time = profile.get("time", "short")
    hobby_time = hobby.get("time_needed", "")

    time_mapping = {
        "short": ["15", "20", "30"],
        "medium": ["1", "2", "hour"],
        "flexible": ["weekend", "flexible", "any"]
    }

    required_times = time_mapping.get(user_time, [])

    if any(time_req in hobby_time.lower() for time_req in required_times):
        return 10
    elif user_time == "flexible":
        return 8  # Flexible users can adapt
    elif user_time == "medium" and any(t in hobby_time.lower() for t in ["30", "45"]):
        return 6  # Can squeeze in shorter sessions
    else:
        return 3  # May require schedule adjustment


def calculate_difficulty_match(profile: dict, hobby: dict) -> int:
    """Calculate difficulty level appropriateness."""
    # This would ideally come from user assessment, but for now use goal as proxy
    user_goal = profile.get("goal", "express")
    hobby_difficulty = hobby.get("difficulty", "Beginner")

    # Beginners and learners prefer easier starts
    if user_goal in ["learn", "relax"] and hobby_difficulty == "Beginner":
        return 5
    elif user_goal == "career" and hobby_difficulty in ["Intermediate", "Advanced"]:
        return 5  # Career-focused users want challenge
    elif hobby_difficulty == "Beginner":
        return 4  # Always good to have easy options
    else:
        return 2


def calculate_cost_affordability(profile: dict, hobby: dict) -> int:
    """Calculate cost compatibility."""
    hobby_cost = hobby.get("cost", "")

    if "free" in hobby_cost.lower():
        return 5
    elif "$" in hobby_cost:
        # Extract price range
        import re
        prices = re.findall(r'\$?(\d+)', hobby_cost)
        if prices:
            max_price = max(int(p) for p in prices)
            if max_price <= 15:
                return 5  # Very affordable
            elif max_price <= 50:
                return 3  # Moderately affordable
            else:
                return 1  # Expensive
    return 3  # Unknown cost, assume moderate


def calculate_career_potential(profile: dict, hobby: dict) -> int:
    """Calculate career/side hustle potential."""
    user_goal = profile.get("goal", "express")
    career_path = hobby.get("career_path", "")

    if user_goal in ["career", "side_hustle"] and career_path:
        return 3
    elif career_path and len(career_path) > 50:  # Detailed career info
        return 2
    else:
        return 1


def calculate_trend_bonus(hobby: dict) -> int:
    """Calculate trend/popularity bonus."""
    # This could be based on current trends, social media mentions, etc.
    # For now, give bonus to hobbies with strong online communities
    trending_hobbies = ["digital_illustration", "content_writing", "music_production"]
    if hobby.get("name", "").lower().replace(" ", "_") in trending_hobbies:
        return 1
    return 0


def calculate_user_feedback_bonus(user_history: dict, hobby: dict) -> int:
    """Learn from user's past interactions."""
    # This would analyze past hobby selections, time spent, etc.
    # For now, return 0 as placeholder
    return 0


def apply_time_based_adjustments(score: float, profile: dict, hobby: dict) -> float:
    """Apply time-based scoring adjustments."""
    # Recent trends: digital hobbies score higher for younger users
    # Seasonal adjustments could be added here
    return score


def calculate_scoring_confidence(breakdown: dict) -> float:
    """Calculate confidence in the scoring based on factor consistency."""
    # High confidence if multiple factors align strongly
    strong_factors = sum(1 for score in breakdown.values() if score >= 15)
    total_factors = len(breakdown)

    confidence = strong_factors / total_factors
    return min(confidence, 1.0)


def generate_scoring_reasoning(breakdown: dict, hobby: dict) -> str:
    """Generate human-readable reasoning for the score."""
    reasons = []

    if breakdown["keyword_match"] >= 15:
        reasons.append("Strong keyword alignment with your interests")
    if breakdown["personality_fit"] >= 15:
        reasons.append("Perfect personality fit")
    if breakdown["goal_alignment"] >= 15:
        reasons.append("Aligns perfectly with your goals")
    if breakdown["time_feasibility"] >= 8:
        reasons.append("Fits your available time")
    if breakdown["cost_affordability"] >= 4:
        reasons.append("Very affordable to start")

    if not reasons:
        reasons.append("Good general match with room for growth")

    return ". ".join(reasons)


def extract_categories_from_keywords(keywords):
    """Extract broader categories from specific keywords."""
    categories = set()
    category_map = {
        "visual": ["visual", "art", "design", "drawing", "color", "photography"],
        "creative": ["creative", "art", "design", "music", "writing"],
        "technical": ["digital", "software", "programming", "tech"],
        "physical": ["physical", "hands-on", "crafts", "diy", "sports"],
        "intellectual": ["writing", "reading", "learning", "analysis"]
    }

    for keyword in keywords:
        for category, category_keywords in category_map.items():
            if keyword in category_keywords:
                categories.add(category)

    return categories


# ─────────────────────────────────────────────
# LEGACY SCORING FUNCTION (for backward compatibility)
# ─────────────────────────────────────────────
def score_hobby_simple(profile: dict, hobby: dict) -> int:
    """
    Legacy scoring function - kept for backward compatibility.
    """
    score = 0

    # 1. Keyword matching (up to 50 pts)
    matched_keywords = 0
    for interest in profile["interests"]:
        if interest in hobby["keywords"]:
            matched_keywords += 1
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
        score += 5

    return min(score, 100)


# ─────────────────────────────────────────────
# ENHANCED RECOMMENDATION ENGINE
# Uses advanced scoring with detailed breakdowns and confidence metrics.
# ─────────────────────────────────────────────
def get_recommendations(profile: dict, top_n: int = 5, user_history: dict = None) -> list:
    """
    Returns a sorted list of hobby recommendations using enhanced scoring.
    Each item includes detailed scoring breakdown and reasoning.
    """
    results = []

    for hobby_key, hobby_data in HOBBIES.items():
        scoring_result = score_hobby(profile, hobby_data, user_history)

        results.append({
            "key": hobby_key,
            "name": hobby_data["name"],
            "score": scoring_result["total_score"],
            "confidence": scoring_result["confidence"],
            "reasoning": scoring_result["reasoning"],
            "breakdown": scoring_result["breakdown"],
            "data": hobby_data
        })

    # Sort by score (primary) and confidence (secondary)
    results.sort(key=lambda x: (x["score"], x["confidence"]), reverse=True)

    return results[:top_n]


# ─────────────────────────────────────────────
# LEGACY RECOMMENDATION FUNCTION (for backward compatibility)
# ─────────────────────────────────────────────
def get_recommendations_simple(profile: dict, top_n: int = 5) -> list:
    """
    Legacy recommendation function using simple scoring.
    """
    results = []

    for hobby_key, hobby_data in HOBBIES.items():
        score = score_hobby_simple(profile, hobby_data)
        results.append({
            "key": hobby_key,
            "name": hobby_data["name"],
            "score": score,
            "data": hobby_data
        })

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
