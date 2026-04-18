# Enhanced Hobby Scoring Algorithm

## Overview

The hobby recommendation system now uses an advanced scoring algorithm that evaluates hobbies across 10 weighted factors to provide more accurate and personalized recommendations.

## Scoring Factors

### 1. Keyword Match (25% weight, max 25 points)
- **Exact matches**: Direct keyword matches between user interests and hobby keywords
- **Semantic matches**: Related concepts (e.g., "visual" matches "art", "design")
- **Category matches**: Broader category alignment

### 2. Personality Fit (20% weight, max 20 points)
- Perfect match: 20 points
- Ambivert flexibility: 15 points (can adapt to most hobbies)

### 3. Goal Alignment (20% weight, max 20 points)
- Maps user goals to hobby goal categories:
  - "relax" → relaxation/fun hobbies
  - "learn" → skill-building hobbies
  - "express" → creative hobbies
  - "career" → professional/side-hustle hobbies

### 4. Energy Compatibility (10% weight, max 10 points)
- Direct energy level match: 10 points
- Moderate energy users get flexibility bonus: 7 points
- Low energy users can adapt to moderate activities: 5 points

### 5. Time Feasibility (10% weight, max 10 points)
- Flexible users: 8 points (can adapt to any schedule)
- Direct time match: 10 points
- Partial matches for moderate adjustments

### 6. Difficulty Match (5% weight, max 5 points)
- Beginners and learners prefer easier starts
- Career-focused users want challenge
- General preference for accessible entry points

### 7. Cost Affordability (5% weight, max 5 points)
- Free hobbies: 5 points
- Under $15: 5 points
- $15-50: 3 points
- Over $50: 1 point

### 8. Career Potential (3% weight, max 3 points)
- Hobbies with documented career paths
- Detailed career information increases score

### 9. Trend Bonus (1% weight, max 1 point)
- Currently trending hobbies get small bonus
- Based on community popularity and momentum

### 10. User Feedback (1% weight, max 1 point)
- Learning from past user interactions (placeholder for future implementation)

## Scoring Output

Each recommendation includes:
- **Total Score**: 0-100 weighted combination
- **Confidence**: 0-1 based on factor alignment consistency
- **Reasoning**: Human-readable explanation
- **Breakdown**: Detailed points per factor

## API Endpoints

### `/api/analyze-scoring` (POST)
Analyze scoring for specific hobbies or compare all hobbies.

**Request Body:**
```json
{
  "profile": {
    "interests": ["visual", "creative"],
    "personality": "extrovert",
    "goal": "express",
    "energy": "high",
    "time": "flexible"
  },
  "hobby_key": "digital_illustration",
  "compare_all": false
}
```

**Response:**
```json
{
  "hobby": "digital_illustration",
  "name": "Digital Illustration",
  "scoring": {
    "total_score": 85,
    "confidence": 0.8,
    "reasoning": "Strong keyword alignment with your interests. Perfect personality fit...",
    "breakdown": {
      "keyword_match": 25,
      "personality_fit": 20,
      // ... other factors
    }
  }
}
```

### `/api/user-engagement-score` (GET)
Calculate user engagement score based on chat completion and activity.

## Backward Compatibility

The original `score_hobby_simple()` and `get_recommendations_simple()` functions are preserved for backward compatibility.

## Future Enhancements

- User feedback integration
- Time-based trend analysis
- A/B testing of scoring weights
- Machine learning personalization
- Social proof integration