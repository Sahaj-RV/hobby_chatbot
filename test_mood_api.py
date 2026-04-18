#!/usr/bin/env python3
"""
Test the mood suggestions API endpoint directly.
"""

import requests
import json

def test_mood_api():
    """Test the mood suggestions API endpoint."""
    print("🧪 Testing Mood Suggestions API Endpoint")
    print("=" * 45)

    # Test data
    test_data = {
        "mood": "stressed",
        "profile": {
            "interests": ["creative", "outdoor"],
            "personality": "introvert",
            "goal": "relax",
            "energy": "low",
            "time": "short"
        }
    }

    print(f"Test data: {json.dumps(test_data, indent=2)}")

    # Note: This would require a running Flask server with authentication
    # For now, we'll just test the logic by importing the function

    try:
        # Import the mood_suggestions function logic
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))

        # Mock the required dependencies
        class MockUser:
            def __init__(self, id):
                self.id = id
                self.email = "test@example.com"

        def mock_require_auth():
            return MockUser(1)

        # Mock the generate_ai_response function
        def mock_generate_ai_response(prompt, system_msg=None, max_tokens=1024):
            return json.dumps([
                {
                    "name": "Meditation & Mindfulness",
                    "reason": "When you're feeling stressed, meditation helps calm your mind and reduce anxiety. It's a gentle activity that can be done anywhere and provides immediate stress relief through focused breathing and mental clarity."
                },
                {
                    "name": "Nature Photography",
                    "reason": "Getting outside to photograph nature can help shift your focus from stress to the beauty around you. The act of observing and capturing peaceful scenes promotes mindfulness and provides a creative outlet."
                }
            ])

        # Test the endpoint logic
        from unittest.mock import patch

        with patch('app.require_auth', mock_require_auth), \
             patch('app.generate_ai_response', mock_generate_ai_response):

            # Simulate the endpoint
            from app import app

            with app.test_client() as client:
                # Test without auth first (should fail)
                response = client.post('/api/mood-suggestions',
                                     json=test_data,
                                     content_type='application/json')
                print(f"Without auth: {response.status_code}")

                # Mock session
                with client.session_transaction() as sess:
                    sess['user_id'] = 1
                    sess['email'] = 'test@example.com'

                # Test with auth
                response = client.post('/api/mood-suggestions',
                                     json=test_data,
                                     content_type='application/json')

                print(f"With auth: {response.status_code}")
                if response.status_code == 200:
                    data = json.loads(response.data)
                    print(f"Response: {json.dumps(data, indent=2)}")
                    print("✅ API endpoint working!")
                else:
                    print(f"❌ API error: {response.data}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mood_api()