#!/usr/bin/env python3
"""
Test the updated mood suggestions API that uses enhanced scoring.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot import get_recommendations, HOBBIES

def test_mood_based_scoring():
    """Test mood-based profile enhancement and scoring."""
    print("🧪 Testing Mood-Based Enhanced Scoring")
    print("=" * 40)

    # Test different moods
    moods = ["stressed", "energetic", "creative", "bored"]

    for mood in moods:
        print(f"\n📊 Testing mood: {mood}")

        # Simulate mood mapping (same logic as in the endpoint)
        mood_mappings = {
            "energetic": {"energy": "high", "time": "flexible"},
            "relaxed": {"energy": "low", "goal": "relax"},
            "creative": {"goal": "express", "interests": ["creative", "visual"]},
            "adventurous": {"energy": "high", "interests": ["outdoor", "physical"]},
            "social": {"personality": "extrovert", "interests": ["social"]},
            "focused": {"energy": "moderate", "goal": "learn"},
            "stressed": {"energy": "low", "goal": "relax"},
            "bored": {"energy": "moderate", "goal": "express"}
        }

        # Create enhanced profile based on mood
        base_profile = {
            "personality": "ambivert",
            "goal": "express",
            "energy": "moderate",
            "time": "flexible",
            "interests": ["reading"]
        }

        enhanced_profile = base_profile.copy()
        if mood in mood_mappings:
            mood_profile = mood_mappings[mood]
            for key, value in mood_profile.items():
                if key == "interests":
                    existing = set(enhanced_profile.get("interests", []))
                    existing.update(value)
                    enhanced_profile["interests"] = list(existing)
                else:
                    enhanced_profile[key] = value

        print(f"Enhanced profile: {enhanced_profile}")

        # Get recommendations using enhanced scoring
        recommendations = get_recommendations(enhanced_profile, top_n=3)

        print("Top recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec['name']} (Score: {rec['score']})")

        # Generate mood reasoning (simulate endpoint logic)
        for rec in recommendations[:2]:  # Just show first 2
            mood_reasoning = generate_mood_reasoning(mood, rec["name"], rec["data"])
            print(f"    → {mood_reasoning}")

    print("\n✅ Mood-based scoring test completed!")


def generate_mood_reasoning(mood: str, hobby_name: str, hobby_data: dict) -> str:
    """Generate mood-specific reasoning (copied from app.py)."""
    mood_reasons = {
        "energetic": [
            f"{hobby_name} is perfect for high energy - it channels your enthusiasm into productive activity.",
            f"When you're feeling energetic, {hobby_name} provides an outlet for your vitality and keeps you engaged.",
            f"This hobby matches your current energy level and will help you make the most of feeling pumped up."
        ],
        "relaxed": [
            f"{hobby_name} is ideal for relaxation - it helps you unwind and find peace in the process.",
            f"When you're in a calm mood, {hobby_name} enhances your sense of tranquility and mindfulness.",
            f"This gentle activity complements your relaxed state and promotes continued well-being."
        ],
        "creative": [
            f"{hobby_name} sparks creativity - it gives your imaginative side free rein to express itself.",
            f"When you're feeling creative, {hobby_name} provides the perfect canvas for your ideas.",
            f"This hobby nurtures your artistic impulses and helps bring your visions to life."
        ],
        "adventurous": [
            f"{hobby_name} satisfies your sense of adventure - it offers excitement and new experiences.",
            f"When you're feeling adventurous, {hobby_name} provides the thrill and discovery you crave.",
            f"This hobby channels your exploratory spirit into meaningful and enjoyable pursuits."
        ],
        "social": [
            f"{hobby_name} is great for connecting with others - it combines fun with social interaction.",
            f"When you're in a social mood, {hobby_name} helps you build connections and share experiences.",
            f"This hobby brings people together and enhances your social bonds."
        ],
        "focused": [
            f"{hobby_name} helps maintain concentration - it provides structured, absorbing activities.",
            f"When you're feeling focused, {hobby_name} allows you to dive deep and achieve flow state.",
            f"This hobby supports your concentrated mindset with meaningful challenges."
        ],
        "stressed": [
            f"{hobby_name} helps reduce stress - it provides calming, therapeutic activities.",
            f"When you're feeling stressed, {hobby_name} offers relief and mental respite.",
            f"This hobby serves as a healthy coping mechanism for managing stress levels."
        ],
        "bored": [
            f"{hobby_name} combats boredom - it introduces novelty and engaging challenges.",
            f"When you're feeling bored, {hobby_name} provides stimulation and renewed interest.",
            f"This hobby reawakens your sense of curiosity and brings excitement back."
        ]
    }

    reasons = mood_reasons.get(mood, [
        f"{hobby_name} is a great match for your current mood and interests.",
        f"This hobby aligns well with how you're feeling right now.",
        f"{hobby_name} provides the perfect activity for your present state of mind."
    ])

    return reasons[0]


if __name__ == "__main__":
    test_mood_based_scoring()