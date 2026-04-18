# hobbies.py
# This file is your hobby database.
# Each hobby has: keywords, description, difficulty, time, cost, career path,
# a 7-day starter plan, and common beginner mistakes to avoid.

HOBBIES = {
    "digital_illustration": {
        "name": "Digital Illustration",
        "keywords": ["visual", "creative", "drawing", "art", "design",
                     "color", "aesthetic", "painting", "sketch"],
        "personality_fit": ["introvert", "ambivert", "creative"],
        "energy_fit": ["low", "moderate"],
        "goal_fit": ["express", "career", "side_hustle", "relax"],
        "description": "Create art digitally using apps like Procreate or Canva.",
        "difficulty": "Beginner",
        "time_needed": "20–30 mins/day",
        "cost": "Free – $15/month",
        "tools": ["Procreate (iPad)", "Canva (free)", "Krita (free PC)"],
        "career_path": "Freelance illustrator, Etsy print shop, Fiverr commissions",
        "why_it_fits": "Blends visual creativity with technology. Great for solo deep-work sessions with huge sharing potential online.",
        "seven_day_plan": [
            "Day 1–2: Download Krita (free). Watch one 10-min YouTube intro. Draw basic shapes — circles, squares, lines.",
            "Day 3–4: Try coloring your shapes. Experiment with 3 brush types.",
            "Day 5: Draw a simple object from your room (a cup, a plant).",
            "Day 6: Recreate the same object with a different color palette.",
            "Day 7: Share your first piece on Instagram or Reddit r/learnart. Celebrate!"
        ],
        "mistakes_to_avoid": [
            "Buying expensive tools before practicing with free ones.",
            "Comparing your Day 1 work to professionals with 10 years of practice.",
            "Skipping fundamentals — shapes and lines before complex scenes."
        ]
    },

    "content_writing": {
        "name": "Content Writing & Blogging",
        "keywords": ["writing", "words", "stories", "reading", "ideas",
                     "language", "communication", "articles", "blog"],
        "personality_fit": ["introvert", "ambivert", "creative"],
        "energy_fit": ["low", "moderate"],
        "goal_fit": ["express", "career", "side_hustle", "learn"],
        "description": "Write articles, blog posts, or stories online.",
        "difficulty": "Beginner",
        "time_needed": "15–20 mins/day",
        "cost": "Free",
        "tools": ["Notion (free)", "Medium (free)", "Google Docs"],
        "career_path": "Freelance writer, copywriter, blogger with ad revenue",
        "why_it_fits": "The lowest barrier creative hobby — just open a doc and start. Ideal for 15-min daily windows and builds directly into a monetizable skill.",
        "seven_day_plan": [
            "Day 1: Open Notion or Google Docs. Write freely for 10 mins — anything on your mind. No editing.",
            "Day 2: Pick one topic you know well. Write 5 bullet points about it.",
            "Day 3: Expand those bullets into 3 short paragraphs.",
            "Day 4: Read one blog post in your niche. Note what you liked about the style.",
            "Day 5: Write a 200-word opinion piece on any topic.",
            "Day 6: Edit yesterday's piece — improve the opening sentence.",
            "Day 7: Publish your first post on Medium (free). You're officially a writer!"
        ],
        "mistakes_to_avoid": [
            "Waiting until you feel 'ready' — just write badly at first.",
            "Editing while writing (kills flow). Write first, edit second.",
            "Ignoring a niche — pick one topic to build authority faster."
        ]
    },

    "music_production": {
        "name": "Music Production",
        "keywords": ["music", "sound", "beats", "rhythm", "audio",
                     "singing", "instruments", "compose", "songs"],
        "personality_fit": ["introvert", "ambivert", "creative"],
        "energy_fit": ["low", "moderate", "high"],
        "goal_fit": ["express", "career", "side_hustle", "fun"],
        "description": "Create beats, melodies, and full tracks using free software.",
        "difficulty": "Beginner",
        "time_needed": "20–30 mins/day",
        "cost": "Free – $10/month",
        "tools": ["GarageBand (Mac/iOS, free)", "BandLab (free, all platforms)", "LMMS (free PC)"],
        "career_path": "Sell beats on BeatStars, music licensing, film/game scoring",
        "why_it_fits": "Deeply satisfying for creative + analytical minds. Combines art and technology. Solo activity that rewards daily 20-min practice sessions.",
        "seven_day_plan": [
            "Day 1: Install BandLab (free). Spend 20 mins just clicking through sounds and loops.",
            "Day 2: Create a simple 4-bar drum loop using the built-in kit.",
            "Day 3: Add a bass line over your drum loop.",
            "Day 4: Add one melodic element (piano or synth). Just 4 notes is fine.",
            "Day 5: Export and listen back. Notice what you'd change.",
            "Day 6: Make a variation — change the tempo or swap one instrument.",
            "Day 7: Share on SoundCloud (free). Post in r/WeAreTheMusicMakers for feedback."
        ],
        "mistakes_to_avoid": [
            "Buying plugins/software before mastering the free tools.",
            "Trying to make a full song on Day 1. Build loops first.",
            "Ignoring music theory — learn just 3 chords in Week 2."
        ]
    },

    "photography": {
        "name": "Photography & Photo Editing",
        "keywords": ["photography", "photos", "camera", "visual", "capture",
                     "nature", "travel", "light", "aesthetic", "images"],
        "personality_fit": ["introvert", "ambivert", "extrovert"],
        "energy_fit": ["low", "moderate", "high"],
        "goal_fit": ["express", "relax", "career", "side_hustle", "fun"],
        "description": "Capture and edit photos using your phone or camera.",
        "difficulty": "Beginner",
        "time_needed": "15–25 mins/day",
        "cost": "Free (phone camera)",
        "tools": ["Snapseed (free)", "Lightroom Mobile (free tier)", "VSCO"],
        "career_path": "Stock photos on Shutterstock, Instagram brand deals, event photography",
        "why_it_fits": "Zero startup cost — your phone is enough. Works on low and high energy days. Great for ambiverts: solo shooting + social sharing.",
        "seven_day_plan": [
            "Day 1: Take 10 photos of things in your home. No filter, no editing. Just explore angles.",
            "Day 2: Learn the 'rule of thirds'. Retake 3 photos using this principle.",
            "Day 3: Install Snapseed. Edit one photo — adjust brightness and contrast only.",
            "Day 4: Go outside. Photograph natural light at golden hour (1hr before sunset).",
            "Day 5: Pick your 3 best photos from the week. What makes them better than the rest?",
            "Day 6: Try a specific theme — only shoot textures, or only shoot shadows.",
            "Day 7: Post your 3 best shots on Instagram with relevant hashtags."
        ],
        "mistakes_to_avoid": [
            "Over-editing — heavy filters hide good composition skills.",
            "Ignoring lighting — it's the #1 factor in a great photo.",
            "Shooting in auto mode forever — learn manual exposure in Week 2."
        ]
    },

    "diy_crafts": {
        "name": "DIY Crafts & Resin Art",
        "keywords": ["crafts", "making", "building", "hands-on", "diy",
                     "art", "create", "physical", "resin", "handmade"],
        "personality_fit": ["introvert", "ambivert", "creative"],
        "energy_fit": ["low", "moderate"],
        "goal_fit": ["relax", "express", "side_hustle", "fun"],
        "description": "Make handmade crafts, jewelry, or resin art pieces.",
        "difficulty": "Beginner",
        "time_needed": "20–30 mins/day",
        "cost": "$10–$25 starter kit",
        "tools": ["Resin starter kit", "Silicone molds", "Basic craft supplies"],
        "career_path": "Etsy shop, local markets, custom orders on Instagram",
        "why_it_fits": "Deeply satisfying hands-on creative outlet. Resin art is trending heavily on Etsy. Works perfectly on low-energy days — calming, meditative work.",
        "seven_day_plan": [
            "Day 1–2: Watch 2 resin art YouTube videos. Order a $15 starter kit online.",
            "Day 3: While waiting for kit — sketch 3 designs you'd like to make.",
            "Day 4: Kit arrives. Mix your first small test batch following safety instructions.",
            "Day 5: Pour your first mold. Simple shape — coaster or small tray.",
            "Day 6: While it cures (24hrs), research Etsy pricing for similar items.",
            "Day 7: Unmold your first piece. Photograph it. Post on Instagram or Pinterest!"
        ],
        "mistakes_to_avoid": [
            "Skipping gloves/ventilation — resin fumes are serious. Always work safely.",
            "Adding too much pigment on your first pour. Less is more.",
            "Impatience — resin needs 24–48hrs to cure. Don't rush the unmolding."
        ]
    }
}
