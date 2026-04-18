#!/usr/bin/env python3
"""
Test script for the enhanced hobby scoring algorithm.
Validates that the new scoring system works correctly and provides
meaningful recommendations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot import score_hobby, get_recommendations, HOBBIES

def test_scoring_algorithm():
    """Test the enhanced scoring algorithm with various profiles."""

    print("🧪 Testing Enhanced Hobby Scoring Algorithm")
    print("=" * 50)

    # Test Profile 1: Creative, high-energy person looking to express themselves
    profile1 = {
        "interests": ["visual", "creative", "art"],
        "personality": "extrovert",
        "goal": "express",
        "energy": "high",
        "time": "flexible"
    }

    print("\n📊 Test Profile 1: Creative Extrovert")
    print(f"Interests: {profile1['interests']}")
    print(f"Personality: {profile1['personality']}, Goal: {profile1['goal']}, Energy: {profile1['energy']}")

    recommendations1 = get_recommendations(profile1, top_n=3)

    for i, rec in enumerate(recommendations1, 1):
        print(f"\n{i}. {rec['name']} (Score: {rec['score']})")
        print(f"   Confidence: {rec['confidence']:.2f}")
        print(f"   Reasoning: {rec['reasoning']}")
        print(f"   Breakdown: {rec['breakdown']}")

    # Test Profile 2: Introverted learner with limited time
    profile2 = {
        "interests": ["writing", "reading", "intellectual"],
        "personality": "introvert",
        "goal": "learn",
        "energy": "low",
        "time": "short"
    }

    print("\n\n📊 Test Profile 2: Introverted Learner")
    print(f"Interests: {profile2['interests']}")
    print(f"Personality: {profile2['personality']}, Goal: {profile2['goal']}, Energy: {profile2['energy']}")

    recommendations2 = get_recommendations(profile2, top_n=3)

    for i, rec in enumerate(recommendations2, 1):
        print(f"\n{i}. {rec['name']} (Score: {rec['score']})")
        print(f"   Confidence: {rec['confidence']:.2f}")
        print(f"   Reasoning: {rec['reasoning']}")

    # Test detailed scoring for a specific hobby
    print("\n\n🔍 Detailed Analysis: Digital Photography")
    scoring_result = score_hobby(profile1, HOBBIES.get("digital_photography", {}))
    print(f"Total Score: {scoring_result['total_score']}")
    print(f"Confidence: {scoring_result['confidence']:.2f}")
    print(f"Reasoning: {scoring_result['reasoning']}")
    print("Breakdown:")
    for factor, score in scoring_result['breakdown'].items():
        print(f"  {factor}: {score}")

    print("\n✅ Scoring algorithm test completed!")

if __name__ == "__main__":
    test_scoring_algorithm()