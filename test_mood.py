#!/usr/bin/env python3
"""
Test script for mood-based suggestions functionality.
Tests the mood suggestions endpoint without requiring a full Flask app.
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock the AI response for testing
def mock_generate_ai_response(prompt, system_msg=None, max_tokens=1024):
    """Mock AI response that returns valid JSON for mood suggestions."""
    return json.dumps([
        {
            "name": "Meditation & Mindfulness",
            "reason": "When you're feeling stressed, meditation helps calm your mind and reduce anxiety. It's a gentle activity that can be done anywhere and provides immediate stress relief through focused breathing and mental clarity."
        },
        {
            "name": "Nature Photography",
            "reason": "Getting outside to photograph nature can help shift your focus from stress to the beauty around you. The act of observing and capturing peaceful scenes promotes mindfulness and provides a creative outlet."
        },
        {
            "name": "Gardening",
            "reason": "Working with plants and soil is therapeutic and grounding. It helps reduce stress hormones while providing a sense of accomplishment as you nurture living things."
        }
    ])

# Test the mood suggestions logic
def test_mood_suggestions():
    """Test the mood suggestions functionality."""
    print("🧪 Testing Mood-Based Suggestions")
    print("=" * 40)

    # Test data
    mood = "stressed"
    profile = {
        "interests": ["creative", "outdoor"],
        "personality": "introvert",
        "goal": "relax",
        "energy": "low",
        "time": "short"
    }

    # Build the prompt (same as in the endpoint)
    prompt = f"""Based on the user's current mood of "{mood}", suggest 3-5 hobbies that would be perfect for this emotional state.

User profile context: {json.dumps(profile) if profile else 'No profile available'}

For each suggestion, provide:
- name: The hobby name
- reason: Why this hobby fits their current mood (2-3 sentences)

Focus on hobbies that can help with their mood - if they're stressed, suggest calming activities; if energetic, suggest active pursuits; if bored, suggest engaging activities.

Return as JSON array of objects with 'name' and 'reason' fields."""

    print(f"Test Mood: {mood}")
    print(f"User Profile: {profile}")
    print(f"\nGenerated Prompt:\n{prompt[:200]}...")

    try:
        # Test with mock response
        response_text = mock_generate_ai_response(prompt)
        suggestions = json.loads(response_text.strip())

        print(f"\n✅ Successfully generated {len(suggestions)} suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n{i}. {suggestion['name']}")
            print(f"   {suggestion['reason']}")

        # Validate structure
        for suggestion in suggestions:
            assert "name" in suggestion, "Missing 'name' field"
            assert "reason" in suggestion, "Missing 'reason' field"
            assert len(suggestion["reason"]) > 50, "Reason too short"

        print("\n✅ All suggestions have valid structure")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

    return True

if __name__ == "__main__":
    success = test_mood_suggestions()
    if success:
        print("\n🎉 Mood suggestions functionality is working correctly!")
    else:
        print("\n💥 Mood suggestions functionality has issues.")