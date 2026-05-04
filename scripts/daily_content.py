#!/usr/bin/env python3
"""
Daily content automation:
1. Pick 3 study topics based on day of month
2. Get Blogger OAuth token
3. Create 3 blog posts
4. Create 5 Pinterest pin images with Pillow
5. Upload images to tmpfiles.org
6. Schedule 5 Buffer pins
"""

import os
import sys
import json
import time
import datetime
import textwrap
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

BLOGGER_BLOG_ID = os.environ.get("BLOGGER_BLOG_ID", "5700991576649979749")
PINTEREST_CHANNEL_ID = "69f44c415c4c051afafb3619"

PIN_DIR = Path("/tmp/pins")

# Topic sets keyed by day % 10
TOPIC_SETS = {
    0: ["Active Recall Techniques", "Spaced Repetition System", "Memory Palace Method"],
    1: ["Pomodoro Technique", "Deep Work for Students", "Eliminating Study Distractions"],
    2: ["Mind Mapping for Students", "Cornell Note-Taking Method", "Visual Learning Tips"],
    3: ["Exam Anxiety Relief", "Test-Taking Strategies", "Staying Calm Under Pressure"],
    4: ["Sleep and Memory Retention", "Brain Foods for Studying", "Exercise and Focus"],
    5: ["Goal Setting for Students", "Building a Study Habit", "Daily Study Routine Tips"],
    6: ["Speed Reading Techniques", "Skimming and Scanning", "Reading Comprehension Tips"],
    7: ["Group Study Strategies", "Learning from Mistakes", "Teaching Others to Learn"],
    8: ["Digital Notes vs Paper Notes", "Best Study Apps for Students", "Flashcard Methods"],
    9: ["Managing Multiple Subjects", "Revision Strategies", "Building Exam Confidence"],
}

# ─────────────────────────────────────────────
# CONVERSION: CTAs, PIN TITLES, DESCRIPTIONS
# ─────────────────────────────────────────────

FIVERR_URL = "https://www.fiverr.com/s/zWDj14R"

# 7 Fiverr CTAs — rotated by day % 7
FIVERR_CTAS = [
    f'<p>⚡ <strong>Want a custom study plan built for your exact schedule?</strong> <a href="{FIVERR_URL}" target="_blank">I build them here →</a></p>',
    f'<p>📌 <strong>Struggling to stay consistent?</strong> I help students build study systems that stick. <a href="{FIVERR_URL}" target="_blank">See my Fiverr gig →</a></p>',
    f'<p>🎯 <strong>Need done-for-you Pinterest study content?</strong> I create full content packs for student accounts. <a href="{FIVERR_URL}" target="_blank">Check this out →</a></p>',
    f'<p>🚀 <strong>Get a personalised study system setup</strong> — tailored to your subjects, schedule, and goals. <a href="{FIVERR_URL}" target="_blank">Limited spots →</a></p>',
    f'<p>📚 <strong>I offer done-for-you Pinterest + Blogger content packs</strong> for student accounts. <a href="{FIVERR_URL}" target="_blank">Order here →</a></p>',
    f'<p>💡 <strong>Wish someone could just set this all up for you?</strong> That\'s exactly what I do on Fiverr. <a href="{FIVERR_URL}" target="_blank">See how →</a></p>',
    f'<p>🔥 <strong>Top students don\'t study harder — they study smarter.</strong> Want help building your system? <a href="{FIVERR_URL}" target="_blank">Start here →</a></p>',
]

# 15 high-converting pin titles — rotated by (day + pin_index) % 15
PIN_TITLE_TEMPLATES = [
    "Why You Forget Everything You Study (And How to Fix It)",
    "Study 2 Hours, Remember Like You Studied 6",
    "The One Note-Taking Method Top Students Use",
    "Stop Highlighting — Do This Instead",
    "How to Study When You Have Zero Motivation",
    "The 5-Minute Routine That Doubled My GPA",
    "Why Your Study Schedule Isn't Working",
    "Study Less, Score More: The Smart Student Method",
    "The Memory Trick No One Teaches in School",
    "How to Never Pull an All-Nighter Again",
    "Feel Overwhelmed Before Exams? Read This",
    "What Straight-A Students Do Differently",
    "The Real Reason You Can't Focus While Studying",
    "How to Study 4 Subjects in 2 Hours",
    "The Exam Prep System That Actually Works",
]

# 7 pin description hook templates — rotated by (day + pin_index) % 7
PIN_DESC_TEMPLATES = [
    "Most students study the wrong way 😔 Here are {n} {topic} tips that actually get results. Save this for your next study session! 📌 #StudyTips #StudentLife #SmartStudy #StudyMotivation #ExamPrep",
    "Stop wasting time and start owning your study sessions ⚡ These {n} {topic} strategies will change how you learn. Read the full guide on the blog! 📖 #StudyHacks #StudentSuccess #LearnSmart #StudyTips",
    "If you've ever stared at your notes and retained nothing — this is for you 👇 {n} {topic} tips that top students swear by. #StudyTips #FocusTips #ExamSeason #StudentMotivation",
    "The smartest students don't study more — they study differently 🧠 Here's how: {n} {topic} tips. Full guide linked! #StudySmarter #ProductivityTips #StudyTips #StudentLife",
    "Struggling with {topic}? You're not alone 💪 These {n} proven tips will help you finally make it work. Save + share with a friend! #StudyTips #SmartStudy #StudentHacks",
    "What nobody tells you about {topic} 👀 These {n} tips changed everything for me. Check the full blog post for details! #StudyMotivation #StudyTips #LearnBetter #StudentSuccess",
    "Before your next exam, read this ✅ {n} {topic} tips that work even when you're short on time. #ExamPrep #StudyTips #LastMinuteStudy #StudentLife #SmartStudy",
]

# 21 daily rotating colour themes — (day % 21) picks the daily theme,
# then pin_num selects one of the 5 per-pin variants inside that day's palette.
# Each entry: bg=background, accent=bar colour, text=dark text on white card
DAILY_COLOR_THEMES = [
    # Day 0 — Coral & Cream
    [
        {"bg": (255, 200, 185), "accent": (220,  80,  60), "text": (80, 20, 10)},
        {"bg": (255, 215, 200), "accent": (210,  70,  50), "text": (80, 20, 10)},
        {"bg": (255, 190, 170), "accent": (230,  90,  70), "text": (80, 20, 10)},
        {"bg": (255, 205, 190), "accent": (215,  75,  55), "text": (80, 20, 10)},
        {"bg": (255, 220, 205), "accent": (205,  65,  45), "text": (80, 20, 10)},
    ],
    # Day 1 — Ocean Blue
    [
        {"bg": (180, 220, 245), "accent": ( 25, 110, 190), "text": (10, 35, 75)},
        {"bg": (165, 210, 240), "accent": ( 20, 100, 180), "text": (10, 35, 75)},
        {"bg": (195, 230, 250), "accent": ( 30, 120, 200), "text": (10, 35, 75)},
        {"bg": (170, 215, 242), "accent": ( 22, 105, 185), "text": (10, 35, 75)},
        {"bg": (185, 225, 248), "accent": ( 28, 115, 195), "text": (10, 35, 75)},
    ],
    # Day 2 — Forest Green
    [
        {"bg": (185, 235, 195), "accent": ( 35, 140,  65), "text": (10, 50, 20)},
        {"bg": (175, 228, 185), "accent": ( 28, 130,  58), "text": (10, 50, 20)},
        {"bg": (195, 242, 205), "accent": ( 42, 150,  72), "text": (10, 50, 20)},
        {"bg": (180, 232, 190), "accent": ( 32, 135,  62), "text": (10, 50, 20)},
        {"bg": (190, 238, 200), "accent": ( 38, 145,  68), "text": (10, 50, 20)},
    ],
    # Day 3 — Royal Purple
    [
        {"bg": (220, 195, 245), "accent": (115,  45, 185), "text": (45, 10, 75)},
        {"bg": (210, 185, 240), "accent": (105,  35, 175), "text": (45, 10, 75)},
        {"bg": (230, 205, 250), "accent": (125,  55, 195), "text": (45, 10, 75)},
        {"bg": (215, 190, 242), "accent": (110,  40, 180), "text": (45, 10, 75)},
        {"bg": (225, 200, 247), "accent": (120,  50, 190), "text": (45, 10, 75)},
    ],
    # Day 4 — Sunny Yellow
    [
        {"bg": (255, 245, 170), "accent": (210, 165,   0), "text": (70, 50,  0)},
        {"bg": (255, 240, 155), "accent": (200, 155,   0), "text": (70, 50,  0)},
        {"bg": (255, 250, 185), "accent": (220, 175,   0), "text": (70, 50,  0)},
        {"bg": (255, 242, 160), "accent": (205, 160,   0), "text": (70, 50,  0)},
        {"bg": (255, 248, 178), "accent": (215, 170,   0), "text": (70, 50,  0)},
    ],
    # Day 5 — Rose Gold
    [
        {"bg": (255, 210, 210), "accent": (185,  70,  95), "text": (75, 15, 35)},
        {"bg": (255, 200, 200), "accent": (175,  60,  85), "text": (75, 15, 35)},
        {"bg": (255, 220, 220), "accent": (195,  80, 105), "text": (75, 15, 35)},
        {"bg": (255, 205, 205), "accent": (180,  65,  90), "text": (75, 15, 35)},
        {"bg": (255, 215, 215), "accent": (190,  75, 100), "text": (75, 15, 35)},
    ],
    # Day 6 — Mint Fresh
    [
        {"bg": (185, 245, 225), "accent": ( 20, 160, 115), "text": (10, 55, 40)},
        {"bg": (175, 240, 218), "accent": ( 15, 150, 108), "text": (10, 55, 40)},
        {"bg": (195, 250, 232), "accent": ( 25, 170, 122), "text": (10, 55, 40)},
        {"bg": (180, 242, 220), "accent": ( 18, 155, 112), "text": (10, 55, 40)},
        {"bg": (190, 247, 228), "accent": ( 22, 163, 118), "text": (10, 55, 40)},
    ],
    # Day 7 — Peach Sunset
    [
        {"bg": (255, 220, 175), "accent": (215, 110,  30), "text": (75, 35,  5)},
        {"bg": (255, 212, 162), "accent": (205, 100,  22), "text": (75, 35,  5)},
        {"bg": (255, 228, 188), "accent": (225, 120,  38), "text": (75, 35,  5)},
        {"bg": (255, 216, 168), "accent": (210, 105,  26), "text": (75, 35,  5)},
        {"bg": (255, 224, 182), "accent": (220, 115,  34), "text": (75, 35,  5)},
    ],
    # Day 8 — Sky Lavender
    [
        {"bg": (215, 210, 250), "accent": ( 80,  60, 200), "text": (25, 15, 80)},
        {"bg": (205, 200, 245), "accent": ( 70,  50, 190), "text": (25, 15, 80)},
        {"bg": (225, 220, 255), "accent": ( 90,  70, 210), "text": (25, 15, 80)},
        {"bg": (210, 205, 248), "accent": ( 75,  55, 195), "text": (25, 15, 80)},
        {"bg": (220, 215, 252), "accent": ( 85,  65, 205), "text": (25, 15, 80)},
    ],
    # Day 9 — Steel Teal
    [
        {"bg": (175, 230, 230), "accent": ( 20, 140, 140), "text": ( 5, 50, 50)},
        {"bg": (165, 222, 222), "accent": ( 15, 130, 130), "text": ( 5, 50, 50)},
        {"bg": (185, 238, 238), "accent": ( 25, 150, 150), "text": ( 5, 50, 50)},
        {"bg": (170, 226, 226), "accent": ( 18, 135, 135), "text": ( 5, 50, 50)},
        {"bg": (180, 234, 234), "accent": ( 22, 145, 145), "text": ( 5, 50, 50)},
    ],
    # Day 10 — Deep Crimson
    [
        {"bg": (255, 185, 185), "accent": (170,  20,  30), "text": (70,  5, 10)},
        {"bg": (255, 175, 175), "accent": (160,  15,  25), "text": (70,  5, 10)},
        {"bg": (255, 195, 195), "accent": (180,  25,  35), "text": (70,  5, 10)},
        {"bg": (255, 180, 180), "accent": (165,  18,  28), "text": (70,  5, 10)},
        {"bg": (255, 190, 190), "accent": (175,  22,  32), "text": (70,  5, 10)},
    ],
    # Day 11 — Lime Pop
    [
        {"bg": (220, 250, 175), "accent": (100, 175,  10), "text": (35, 65,  0)},
        {"bg": (210, 245, 165), "accent": ( 90, 165,   5), "text": (35, 65,  0)},
        {"bg": (230, 255, 185), "accent": (110, 185,  15), "text": (35, 65,  0)},
        {"bg": (215, 248, 170), "accent": ( 95, 170,   8), "text": (35, 65,  0)},
        {"bg": (225, 252, 180), "accent": (105, 180,  12), "text": (35, 65,  0)},
    ],
    # Day 12 — Indigo Night
    [
        {"bg": (200, 205, 245), "accent": ( 50,  55, 170), "text": (15, 15, 70)},
        {"bg": (190, 195, 240), "accent": ( 40,  45, 160), "text": (15, 15, 70)},
        {"bg": (210, 215, 250), "accent": ( 60,  65, 180), "text": (15, 15, 70)},
        {"bg": (195, 200, 242), "accent": ( 45,  50, 165), "text": (15, 15, 70)},
        {"bg": (205, 210, 247), "accent": ( 55,  60, 175), "text": (15, 15, 70)},
    ],
    # Day 13 — Warm Sand
    [
        {"bg": (250, 235, 195), "accent": (180, 130,  40), "text": (65, 45, 10)},
        {"bg": (245, 228, 182), "accent": (170, 120,  32), "text": (65, 45, 10)},
        {"bg": (255, 242, 208), "accent": (190, 140,  48), "text": (65, 45, 10)},
        {"bg": (248, 232, 188), "accent": (175, 125,  36), "text": (65, 45, 10)},
        {"bg": (252, 238, 202), "accent": (185, 135,  44), "text": (65, 45, 10)},
    ],
    # Day 14 — Dusty Rose
    [
        {"bg": (245, 205, 215), "accent": (175,  70, 100), "text": (65, 15, 35)},
        {"bg": (240, 195, 208), "accent": (165,  60,  90), "text": (65, 15, 35)},
        {"bg": (250, 215, 222), "accent": (185,  80, 110), "text": (65, 15, 35)},
        {"bg": (242, 200, 212), "accent": (170,  65,  95), "text": (65, 15, 35)},
        {"bg": (248, 210, 218), "accent": (180,  75, 105), "text": (65, 15, 35)},
    ],
    # Day 15 — Electric Cyan
    [
        {"bg": (175, 240, 245), "accent": ( 10, 175, 185), "text": ( 5, 60, 65)},
        {"bg": (165, 235, 240), "accent": (  5, 165, 175), "text": ( 5, 60, 65)},
        {"bg": (185, 245, 250), "accent": ( 15, 185, 195), "text": ( 5, 60, 65)},
        {"bg": (170, 238, 242), "accent": (  8, 170, 180), "text": ( 5, 60, 65)},
        {"bg": (180, 242, 247), "accent": ( 12, 180, 190), "text": ( 5, 60, 65)},
    ],
    # Day 16 — Vintage Olive
    [
        {"bg": (225, 225, 175), "accent": (115, 120,  20), "text": (40, 42,  5)},
        {"bg": (218, 218, 165), "accent": (108, 112,  15), "text": (40, 42,  5)},
        {"bg": (232, 232, 185), "accent": (122, 128,  25), "text": (40, 42,  5)},
        {"bg": (222, 222, 170), "accent": (112, 116,  18), "text": (40, 42,  5)},
        {"bg": (228, 228, 180), "accent": (118, 124,  22), "text": (40, 42,  5)},
    ],
    # Day 17 — Blush Gold
    [
        {"bg": (255, 225, 195), "accent": (190, 140,  55), "text": (70, 45, 10)},
        {"bg": (255, 218, 182), "accent": (182, 132,  48), "text": (70, 45, 10)},
        {"bg": (255, 232, 208), "accent": (198, 148,  62), "text": (70, 45, 10)},
        {"bg": (255, 222, 188), "accent": (186, 136,  52), "text": (70, 45, 10)},
        {"bg": (255, 228, 202), "accent": (194, 144,  58), "text": (70, 45, 10)},
    ],
    # Day 18 — Berry Plum
    [
        {"bg": (230, 185, 230), "accent": (140,  30, 130), "text": (55,  5, 50)},
        {"bg": (222, 175, 222), "accent": (132,  22, 122), "text": (55,  5, 50)},
        {"bg": (238, 195, 238), "accent": (148,  38, 138), "text": (55,  5, 50)},
        {"bg": (226, 180, 226), "accent": (136,  26, 126), "text": (55,  5, 50)},
        {"bg": (234, 190, 234), "accent": (144,  34, 134), "text": (55,  5, 50)},
    ],
    # Day 19 — Arctic White-Blue
    [
        {"bg": (225, 240, 255), "accent": ( 60, 140, 210), "text": (15, 45, 80)},
        {"bg": (215, 232, 250), "accent": ( 50, 130, 200), "text": (15, 45, 80)},
        {"bg": (235, 248, 255), "accent": ( 70, 150, 220), "text": (15, 45, 80)},
        {"bg": (220, 236, 252), "accent": ( 55, 135, 205), "text": (15, 45, 80)},
        {"bg": (230, 244, 254), "accent": ( 65, 145, 215), "text": (15, 45, 80)},
    ],
    # Day 20 — Terracotta
    [
        {"bg": (245, 200, 170), "accent": (180,  80,  40), "text": (70, 25,  8)},
        {"bg": (240, 190, 158), "accent": (172,  72,  34), "text": (70, 25,  8)},
        {"bg": (250, 210, 182), "accent": (188,  88,  46), "text": (70, 25,  8)},
        {"bg": (242, 195, 164), "accent": (176,  76,  38), "text": (70, 25,  8)},
        {"bg": (248, 205, 176), "accent": (184,  84,  43), "text": (70, 25,  8)},
    ],
]

# Keep old COLOR_SCHEMES as a fallback reference (not used directly)
COLOR_SCHEMES = DAILY_COLOR_THEMES[0]

# ─────────────────────────────────────────────
# BLOG CONTENT GENERATION
# ─────────────────────────────────────────────

BLOG_CONTENT = {
    "Active Recall Techniques": {
        "title": "5 Active Recall Techniques for Students That Actually Work",
        "intro": (
            "Most students re-read their notes and hope the information sticks — "
            "but research consistently shows that passive review is one of the least "
            "effective ways to study. Active recall flips the process: instead of "
            "reading information in, you practice pulling it out. This forces your "
            "brain to strengthen the neural pathways tied to each memory, making "
            "retrieval faster and more reliable when it matters most — during exams."
        ),
        "points": [
            (
                "Close the book and write down everything you remember",
                "After reading a section, shut your notes and try to reconstruct the key "
                "ideas from scratch. This 'brain dump' reveals exactly what you retained "
                "and what slipped away, turning passive reading into an active test. "
                "Review your notes only after the attempt to fill in the gaps."
            ),
            (
                "Use question-based flashcards, not definition cards",
                "Instead of 'Term → Definition', frame every card as a question that "
                "demands you think: 'What are the three causes of X?' or 'Explain why Y "
                "matters.' Questions engage deeper processing and mirror the format of "
                "real exam questions, building both knowledge and test-taking fluency."
            ),
            (
                "Practice retrieval at the end of every study session",
                "Spend the last 10 minutes of any session listing every concept you "
                "covered — without looking. What you can retrieve cleanly is learned; "
                "what you can't is exactly what needs another pass. This daily habit "
                "compounds over a semester into dramatically stronger retention."
            ),
            (
                "Answer past exam questions from memory, then check",
                "Past papers are the closest approximation of the real exam environment. "
                "Attempt every question before consulting your notes or model answers. "
                "Even a wrong attempt trains pattern recognition, highlights weak spots, "
                "and makes the correct answer far more memorable when you finally see it."
            ),
            (
                "Teach the topic out loud as if the listener knows nothing",
                "The Feynman Technique exposes hidden confusion instantly — you cannot "
                "explain what you do not truly understand. Speak your explanation aloud "
                "to a study partner, a recording, or even an empty chair. Every stumble "
                "or vague hand-wave marks a gap to revisit before the exam."
            ),
        ],
        "conclusion": (
            "Active recall requires more effort than passive review, and that friction is "
            "precisely why it works. The struggle of retrieval is the learning. Start "
            "with just one technique — close-book summaries — and build the others in "
            "gradually. Within a few weeks, you will notice information surfacing more "
            "quickly and your exam confidence growing alongside it."
        ),
        "label": "Active Recall",
    },
    "Spaced Repetition System": {
        "title": "5 Spaced Repetition Tips for Students That Actually Work",
        "intro": (
            "Cramming packs information into short-term memory, but spaced repetition "
            "builds long-term knowledge. The science is straightforward: reviewing "
            "material at gradually increasing intervals — just before you are about to "
            "forget it — forces stronger re-encoding each time. Whether you use a "
            "dedicated app or a simple calendar, applying these five principles will "
            "transform how much you retain between now and exam day."
        ),
        "points": [
            (
                "Start your first review within 24 hours of learning",
                "Memory decay is steepest in the first day after exposure. A 10-minute "
                "review the evening after a lecture can prevent up to 80% of that initial "
                "forgetting. You do not need a full re-study — a quick self-quiz or "
                "summary is enough to reset the forgetting curve."
            ),
            (
                "Use an SRS app like Anki or RemNote for large card decks",
                "Spaced repetition software (SRS) calculates the optimal review interval "
                "for each card based on how well you recalled it. Cards you struggle with "
                "come back sooner; cards you nail are pushed further out. This automation "
                "is far more efficient than manually scheduling reviews."
            ),
            (
                "Keep cards atomic — one concept, one question",
                "Complex multi-part cards hide which sub-concept you actually forgot. "
                "Break every card down to a single, specific question. This keeps reviews "
                "fast, honest, and surgically targeted at genuine weak points rather than "
                "broad topics."
            ),
            (
                "Be ruthless about rating your recall honestly",
                "SRS apps only work if you score yourself accurately. If you had to "
                "hesitate or peek, that is a miss — rate it accordingly. Inflating your "
                "scores to avoid seeing difficult cards again is the most common way "
                "students undermine their own spaced repetition system."
            ),
            (
                "Do daily reviews before adding new cards",
                "Skipping reviews to add more content is a debt that compounds rapidly. "
                "Clear your due-review queue every day first, even if it means adding "
                "fewer new cards. A small, maintained deck outperforms a large, neglected "
                "one every time."
            ),
        ],
        "conclusion": (
            "Spaced repetition is not a shortcut — it is a long game that rewards "
            "consistency. The students who benefit most are those who treat their daily "
            "review queue the same way they treat brushing their teeth: non-negotiable. "
            "Build the habit now, and by the time exams arrive, the material will feel "
            "less like something to memorize and more like something you simply know."
        ),
        "label": "Spaced Repetition",
    },
    "Memory Palace Method": {
        "title": "5 Memory Palace Method Tips for Students That Actually Work",
        "intro": (
            "The memory palace — also called the method of loci — is one of the oldest "
            "memorization techniques in existence, used by ancient Greek orators and "
            "modern memory champions alike. The idea is to link information to vivid "
            "locations along a familiar mental route, making abstract facts concrete and "
            "spatially organized. With the right approach, students can memorize lists, "
            "processes, and even verbatim definitions far faster than rote repetition allows."
        ),
        "points": [
            (
                "Choose a location you know deeply and can visualize room by room",
                "Your childhood home, your school route, or a familiar park all work well. "
                "The more detail you can mentally walk through — furniture positions, "
                "wall colors, smells — the more anchor points you have available. Do a "
                "mental walk-through before you start placing any information."
            ),
            (
                "Create absurd, exaggerated, multi-sensory images for each fact",
                "Ordinary images fade quickly. Make them bizarre: if you need to remember "
                "that mitochondria produce ATP, imagine a tiny glowing power plant sitting "
                "in your kitchen sink, crackling with electricity. The stranger the image, "
                "the more distinctly it will stand out during recall."
            ),
            (
                "Place one distinct piece of information at each stop on your route",
                "Crowding multiple facts into a single location causes confusion during "
                "retrieval. Assign exactly one concept per landmark. Walk the route in the "
                "same order every time to build a reliable retrieval sequence."
            ),
            (
                "Rehearse the journey forward and backward three times after building it",
                "Immediately after constructing your palace, walk the route mentally three "
                "times: forward, backward, then forward again. This consolidates the "
                "spatial-to-informational links and catches any images that are already "
                "blurring before you leave the study session."
            ),
            (
                "Review the palace at 1 hour, 1 day, and 1 week intervals",
                "Even the most vivid memory palace will fade without review. A quick mental "
                "walk-through at these three intervals locks the images into long-term "
                "memory. After the one-week review most students find the palace stable "
                "enough to survive until exam day with minimal additional upkeep."
            ),
        ],
        "conclusion": (
            "The memory palace takes 20–30 minutes to build the first time, but becomes "
            "faster with practice. Students who use it regularly often find they can recall "
            "a 20-item list from a single study session with near-perfect accuracy. Start "
            "with something small — five vocabulary words or five historical dates — and "
            "experience firsthand why this technique has survived for over two thousand years."
        ),
        "label": "Memory Palace",
    },
    "Pomodoro Technique": {
        "title": "5 Pomodoro Technique Tips for Students That Actually Work",
        "intro": (
            "The Pomodoro Technique breaks study time into focused 25-minute sprints "
            "separated by short breaks — and the structure does something simple but "
            "powerful: it makes starting easier and sustaining focus less exhausting. "
            "Rather than sitting down to 'study for three hours,' you only ever commit "
            "to 25 minutes. These five tips will help you get the most out of each session."
        ),
        "points": [
            (
                "Define a single, specific task before each pomodoro begins",
                "Vague intentions like 'study chemistry' produce vague results. Before "
                "starting the timer, write exactly what you will accomplish: 'summarize "
                "Chapter 4 on reaction kinetics' or 'complete practice problems 1–15.' "
                "Specificity keeps you from drifting during the session."
            ),
            (
                "Treat the timer as a contract — no interruptions until it rings",
                "The 25-minute block is sacred. Every time you switch tabs, check your "
                "phone, or get up unnecessarily, you reset the cognitive warmup your brain "
                "just built. If a random thought surfaces, write it in a capture list and "
                "return to work immediately."
            ),
            (
                "Take your breaks seriously — actually step away from the desk",
                "A break spent scrolling social media in the same chair gives your brain "
                "no real rest. Stand up, walk around, get water, look out a window. "
                "Physical movement during breaks has been shown to restore attention and "
                "improve performance in subsequent blocks."
            ),
            (
                "Adjust session length to match the difficulty of the material",
                "The standard 25/5 split works well for routine tasks, but dense material "
                "like complex maths or unfamiliar theory may benefit from 50-minute "
                "sessions with 10-minute breaks. Experiment until you find the rhythm "
                "where you finish each session feeling stretched but not depleted."
            ),
            (
                "Track your pomodoros to spot productivity patterns",
                "Keep a simple tally of completed sessions each day. Over a week you will "
                "see when your focus is naturally strongest, which subjects cost the most "
                "sessions, and whether your output is growing. This data makes you a "
                "smarter scheduler of your own study time."
            ),
        ],
        "conclusion": (
            "The Pomodoro Technique is powerful precisely because it is simple — a timer "
            "and a task list are all you need. Students who use it consistently report not "
            "just better focus but less end-of-day burnout, because the built-in breaks "
            "prevent the slow accumulation of mental fatigue that derails long unstructured "
            "sessions. Try four pomodoros today and notice the difference."
        ),
        "label": "Pomodoro Technique",
    },
    "Deep Work for Students": {
        "title": "5 Deep Work Habits for Students That Actually Work",
        "intro": (
            "Cal Newport defines deep work as cognitively demanding activity performed "
            "in a state of distraction-free concentration — the kind that produces real "
            "learning and creative output. For students, the ability to do deep work is "
            "becoming rarer and more valuable at the same time. These five habits will "
            "help you build that capacity deliberately."
        ),
        "points": [
            (
                "Schedule your deep work blocks the same way you schedule classes",
                "Spontaneous good intentions rarely survive a day full of notifications "
                "and social pull. Block two to three hours in your calendar for deep work "
                "each day and treat them as fixed appointments. Consistency builds the "
                "neural habit of entering focus quickly when the scheduled time arrives."
            ),
            (
                "Create a ritual that signals the start of a deep work session",
                "Athletes warm up before competing; your brain also benefits from a "
                "consistent pre-work routine. Make a cup of tea, put on the same "
                "playlist, clear your desk, open only the documents you need. Repeated "
                "enough times, the ritual itself triggers a focused mental state."
            ),
            (
                "Embrace boredom during your breaks instead of reaching for your phone",
                "If you fill every idle moment with stimulation, you train your brain to "
                "demand constant novelty — and that makes sustained focus increasingly "
                "painful. Allow yourself to be bored during transit, while waiting, "
                "during meals. This trains the tolerance for monotony that deep work "
                "requires."
            ),
            (
                "Set a clear endpoint and a concrete output goal for each session",
                "Knowing a session ends at a specific time reduces the psychological drag "
                "of open-ended effort. Knowing you are aiming for a concrete deliverable "
                "— a draft completed, a problem set finished, a chapter outlined — gives "
                "your focus something to lock onto."
            ),
            (
                "Quit social media during study hours, not just during sessions",
                "Even knowing that a notification might arrive is enough to split "
                "attention. Log out of social platforms entirely during your study "
                "hours and check them only during designated times. This boundary "
                "protects your attention budget for the work that actually matters."
            ),
        ],
        "conclusion": (
            "Deep work is a skill, not a trait — it deteriorates without practice and "
            "strengthens with consistent use. Start modestly: one 90-minute deep work "
            "block per day, five days a week. As your tolerance for focused effort grows, "
            "you will be able to accomplish in two hours what previously took an entire "
            "unfocused afternoon."
        ),
        "label": "Deep Work",
    },
    "Eliminating Study Distractions": {
        "title": "5 Ways to Eliminate Study Distractions That Actually Work",
        "intro": (
            "Every time you allow a distraction during studying, you pay a hidden cost: "
            "research shows it takes an average of 23 minutes to fully regain deep focus "
            "after an interruption. Over a three-hour session, even a handful of "
            "distractions can reduce your effective study time to under an hour. These "
            "five strategies attack the problem at its source."
        ),
        "points": [
            (
                "Use app blockers during study sessions — not just willpower",
                "Willpower is a finite resource that depletes over the day. Tools like "
                "Cold Turkey, Freedom, or your phone's built-in focus mode remove the "
                "need for willpower entirely by making distracting apps genuinely "
                "inaccessible during study time. Set them before you sit down, not when "
                "temptation strikes."
            ),
            (
                "Put your phone in another room, face down and silenced",
                "The mere visible presence of a smartphone on a desk — even face down "
                "and silent — measurably reduces available cognitive capacity. Physical "
                "distance is more effective than self-control. Move the device to "
                "another room and retrieve it only during scheduled breaks."
            ),
            (
                "Use noise-canceling headphones or brown noise to mask interruptions",
                "If you cannot control your environment (dorm, shared home, café), "
                "control your auditory input. Brown or white noise masks unpredictable "
                "ambient sounds that trigger the orienting reflex. Instrumental music "
                "or nature sounds also work for many students — lyrics introduce a "
                "competing language channel that interferes with reading and writing."
            ),
            (
                "Communicate your study hours to housemates or family in advance",
                "Social interruptions are well-intentioned but just as disruptive as "
                "digital ones. A brief conversation — 'I study from 6 to 9 PM, please "
                "treat it like a work meeting' — sets expectations and dramatically "
                "reduces the frequency of 'just a quick question' interruptions."
            ),
            (
                "Keep a distraction capture list for intrusive thoughts",
                "The most disruptive distractions often come from inside: a task you "
                "remembered, an idea you do not want to lose, a question you want to "
                "look up. Instead of acting on the impulse, write it in a running list "
                "and return to work immediately. Review the list after the session — "
                "most items will feel trivial by then."
            ),
        ],
        "conclusion": (
            "Eliminating distractions is not about having better discipline; it is about "
            "designing an environment that makes distraction inconvenient and focus easy. "
            "Pick the one strategy above that targets your biggest distraction source, "
            "implement it today, and add the others incrementally. Your study efficiency "
            "will improve in proportion to how thoroughly you remove the friction from "
            "staying on task."
        ),
        "label": "Study Focus",
    },
    "Mind Mapping for Students": {
        "title": "5 Mind Mapping Tips for Students That Actually Work",
        "intro": (
            "A mind map is a visual diagram that radiates outward from a central idea, "
            "showing how concepts connect rather than listing them in a linear sequence. "
            "For students who process information spatially, or who study subjects with "
            "interconnected ideas (biology, history, literature), mind maps can "
            "dramatically accelerate both understanding and recall. Here is how to use "
            "them effectively."
        ),
        "points": [
            (
                "Start with a single central concept in the middle of the page",
                "Write the core topic — the chapter title, the essay question, the "
                "concept you are trying to master — in the center of a blank, landscape-"
                "oriented page. Everything else will branch from this hub. Keeping it "
                "central ensures the diagram grows organically in all directions rather "
                "than running off one edge of the paper."
            ),
            (
                "Use single keywords or very short phrases on each branch",
                "Full sentences defeat the purpose of a mind map. Each node should be "
                "a trigger word that reconstructs a fuller idea when your brain "
                "encounters it. Concise labels keep the map readable and force you to "
                "identify the essential word for each concept — itself a valuable "
                "exercise in understanding."
            ),
            (
                "Draw the map from memory first, then refine with your notes",
                "Doing this reverses the typical passive approach. Attempting the map "
                "from recall first surfaces what you already understand and exposes "
                "genuine gaps. The refinement pass with notes is then targeted and "
                "meaningful rather than routine copying."
            ),
            (
                "Use colors and simple images to encode categories and relationships",
                "Assign a color to each major branch and keep it consistent as sub-"
                "branches extend. Add quick icons or sketches for key concepts. The "
                "visual coding creates an additional retrieval cue during exams — you "
                "will often remember the color or shape of a branch before the word."
            ),
            (
                "Connect related branches across the map with dotted lines",
                "One of the key advantages of mind maps over linear notes is the ability "
                "to show cross-cutting relationships — the same principle appearing in "
                "two different contexts, or a cause on one branch leading to an effect on "
                "another. These connections are often the most exam-relevant insights "
                "in the entire map."
            ),
        ],
        "conclusion": (
            "Mind maps are most powerful as a synthesis tool: use them after a study "
            "session to consolidate what you learned, or before an exam as a single-"
            "page overview of an entire topic. Students who review their mind maps the "
            "night before a test often report that the act of visualizing the diagram "
            "during the exam is itself a retrieval cue that brings detailed information "
            "flooding back."
        ),
        "label": "Mind Mapping",
    },
    "Cornell Note-Taking Method": {
        "title": "5 Cornell Note-Taking Tips for Students That Actually Work",
        "intro": (
            "The Cornell Method divides each note page into three zones: a narrow cue "
            "column on the left, a wider notes column on the right, and a summary "
            "section at the bottom. This layout was designed at Cornell University in "
            "the 1950s and has endured because it builds active review directly into "
            "the structure of the notes themselves. These five tips will help you get "
            "maximum value from the system."
        ),
        "points": [
            (
                "Take notes in the right column using your own words, not verbatim",
                "Transcribing exactly what is said or written occupies your hands but "
                "not your mind. Paraphrasing forces you to process information as you "
                "capture it, improving immediate comprehension and reducing the cognitive "
                "load of review later because the notes are already in language you "
                "understand."
            ),
            (
                "Fill the cue column within 24 hours — not during the lecture",
                "The left cue column is for questions, keywords, and prompts that cover "
                "the notes to the right — not for taking notes simultaneously. Write "
                "the cues after the lecture while the material is still fresh. This "
                "transforms passive transcription into active engagement with what "
                "you just learned."
            ),
            (
                "Use the cue column for self-testing, not just as a label",
                "The most powerful use of the cue column is as a question that the "
                "right-side notes answer. Cover the notes column, read the cue, and "
                "try to answer from memory. This built-in retrieval practice is why "
                "Cornell notes outperform conventional note-taking in retention studies."
            ),
            (
                "Write a 2–3 sentence summary at the bottom of every page immediately after class",
                "The summary section consolidates the page into its core idea in your "
                "own words. Writing it immediately after the lecture — before memory "
                "fades — is more effective than writing it during review. When you "
                "return to the notes later, reading the summaries alone often reconstructs "
                "the gist of an entire lecture."
            ),
            (
                "Review your Cornell notes by reading cues and recalling notes — not re-reading",
                "Re-reading notes feels productive but produces little learning. The "
                "correct review method is active: fold or cover the notes column, read "
                "each cue, recall the answer, then check. This converts your notes from "
                "a reference document into a self-testing tool that strengthens memory "
                "each time you use it."
            ),
        ],
        "conclusion": (
            "Cornell notes require slightly more effort than unstructured note-taking, "
            "but every extra minute invested pays back many times during revision. "
            "Students who use the system consistently — especially the cue column and "
            "daily summaries — often find they need far less cramming before exams "
            "because the retrieval practice has been building silently throughout the "
            "semester."
        ),
        "label": "Note-Taking",
    },
    "Visual Learning Tips": {
        "title": "5 Visual Learning Tips for Students That Actually Work",
        "intro": (
            "Visual learners encode information more effectively through diagrams, "
            "charts, timelines, and spatial organization than through blocks of text. "
            "But even students who do not identify as strongly visual thinkers benefit "
            "from visual study tools — the act of converting prose into a visual format "
            "demands the kind of active processing that builds deep understanding. "
            "Here are five strategies to make visual learning work for any subject."
        ),
        "points": [
            (
                "Convert dense paragraphs into flowcharts to understand processes",
                "Whenever a textbook describes a multi-step process — a biological "
                "cycle, a historical sequence of events, a legal procedure — draw it "
                "as a flowchart with boxes and arrows. The translation from prose to "
                "diagram forces you to identify the logical structure and sequence, "
                "which is often the exact understanding exams test."
            ),
            (
                "Use color coding consistently across all your notes and materials",
                "Assign a fixed color to each subject, topic category, or type of "
                "information (definitions in blue, examples in green, warnings in red). "
                "Consistent color coding adds a visual layer to your memory — during "
                "exams you will often recall the color of a fact before the fact itself, "
                "which acts as a retrieval bridge."
            ),
            (
                "Draw concept maps to show how ideas in a topic relate to each other",
                "A concept map differs from a mind map in that it explicitly labels the "
                "relationship between connected nodes: 'causes,' 'is part of,' 'leads "
                "to,' 'contrasts with.' The labeling requirement forces precise thinking "
                "about how concepts interact — the kind of understanding that answers "
                "application and analysis questions rather than just recall questions."
            ),
            (
                "Create timelines for history, biology, and literature chronologies",
                "Time-ordered information is notoriously difficult to recall as a list "
                "but much easier to navigate as a visual timeline. Spread events "
                "spatially across the page, mark turning points and causes, and add "
                "brief notes at each point. The spatial distribution makes the sequence "
                "feel embodied and real rather than abstract."
            ),
            (
                "Sketch diagrams from memory to test visual understanding",
                "Being able to recognize a diagram in a textbook is different from being "
                "able to reproduce it. After studying any visual material, close the "
                "book and attempt to redraw the diagram from memory. The areas where "
                "your sketch diverges from the original mark exactly what you have not "
                "yet internalized."
            ),
        ],
        "conclusion": (
            "Visual tools work because they externalize the organizational work that "
            "your working memory would otherwise have to do on its own. By putting "
            "structure on the page, you free up cognitive resources for actual thinking "
            "and analysis. Start with whichever format feels most natural — a simple "
            "color-coded highlighter system or a rough flowchart — and build your "
            "visual toolkit from there."
        ),
        "label": "Visual Learning",
    },
    "Exam Anxiety Relief": {
        "title": "5 Exam Anxiety Relief Tips for Students That Actually Work",
        "intro": (
            "A degree of pre-exam nervousness is not only normal — it is useful. "
            "Research shows that moderate arousal improves performance by sharpening "
            "attention and motivation. The problem is when anxiety crosses the threshold "
            "where it impairs memory retrieval and clear thinking. These five strategies "
            "address exam anxiety at its physiological and psychological roots."
        ),
        "points": [
            (
                "Reframe the physical symptoms of anxiety as preparation energy",
                "The racing heart, shallow breath, and heightened alertness of anxiety "
                "are physiologically identical to excitement. Studies show that students "
                "who consciously tell themselves 'I am excited' before an exam outperform "
                "those who try to suppress nervousness. Lean into the energy rather than "
                "fighting it."
            ),
            (
                "Use box breathing to activate the parasympathetic nervous system",
                "Inhale for four counts, hold for four, exhale for four, hold for four. "
                "Repeat four times. This breathing pattern reliably slows heart rate and "
                "reduces cortisol within two minutes. Use it in the exam waiting area or "
                "at your desk before reading the first question."
            ),
            (
                "Study under simulated exam conditions to desensitize the anxiety response",
                "Much of exam anxiety is a conditioned response to the unfamiliar high-"
                "stakes environment. Repeatedly practicing past papers with a real timer, "
                "no notes, and no phone desensitizes your nervous system to that context. "
                "By exam day, the conditions will feel familiar rather than threatening."
            ),
            (
                "Write your worries down for ten minutes before studying",
                "A simple 10-minute expressive writing exercise — writing freely about "
                "what you are anxious about — has been shown in multiple studies to "
                "reduce working memory load during subsequent test-taking. Getting the "
                "worries out of your head and onto paper seems to reduce the cognitive "
                "interference they create."
            ),
            (
                "Arrive early and spend the first five exam minutes reading all questions",
                "Rushing into the exam room triggers the stress response unnecessarily. "
                "Arriving five to ten minutes early allows the nervous system to settle "
                "before the paper starts. Spending the first five minutes reading all "
                "questions — before writing a word — activates background processing "
                "and reduces the chance of being blindsided by an unexpected question."
            ),
        ],
        "conclusion": (
            "Exam anxiety responds well to preparation, practice, and simple physiological "
            "interventions. You do not need to eliminate anxiety entirely — you need to "
            "keep it in the range where it helps rather than hinders. The students who "
            "manage exam pressure best are not those who feel no anxiety, but those who "
            "have practical tools to keep that anxiety working for them."
        ),
        "label": "Exam Anxiety",
    },
    "Test-Taking Strategies": {
        "title": "5 Test-Taking Strategies for Students That Actually Work",
        "intro": (
            "Strong content knowledge is necessary but not sufficient for exam success. "
            "Students who know the material but have not practiced strategic test-taking "
            "frequently underperform against equally prepared classmates who approach "
            "exams systematically. These five strategies will help you extract maximum "
            "marks from what you already know."
        ),
        "points": [
            (
                "Do a first pass at full speed, skipping anything that requires long thought",
                "Answer every question you can answer quickly and confidently. Skip "
                "anything that requires extended thought and mark it for return. This "
                "ensures you score all the 'easy' marks before time pressure builds, "
                "prevents early difficult questions from eating time you need later, "
                "and often results in later questions triggering the answer to earlier "
                "skipped ones."
            ),
            (
                "Allocate your time per question before the exam starts",
                "Divide the available time by marks or question count and set rough "
                "time targets before you write anything. Checking these targets at "
                "intervals prevents the common disaster of spending 45 minutes on a "
                "10-mark question while a 30-mark question goes unanswered."
            ),
            (
                "For multiple choice, eliminate clearly wrong options before choosing",
                "Even when you are unsure of the correct answer, you can usually "
                "identify one or two options that are clearly impossible. Eliminating "
                "them first improves your odds from 25% to 33% or 50% and often makes "
                "the correct answer more visible once the noise is removed."
            ),
            (
                "Answer every question — blank answers score zero, partial attempts score partial marks",
                "Exam markers award marks for demonstrating relevant knowledge even "
                "if the full answer is wrong or incomplete. A structured attempt — "
                "relevant formulae, key terms, a logical argument started but not "
                "finished — routinely earns partial credit. Never submit a blank."
            ),
            (
                "Reserve five minutes at the end for a final review pass",
                "Rushing through the last questions and immediately handing in is a "
                "common regret. Budget a final five minutes to check arithmetic, "
                "re-read ambiguous questions you may have misunderstood, and confirm "
                "no question was accidentally skipped. Marks recovered in this pass "
                "often require seconds to fix."
            ),
        ],
        "conclusion": (
            "Test-taking strategies are skills — and like all skills, they improve "
            "with deliberate practice. Use past papers not just to learn content but "
            "to practice the strategies above under timed conditions. Students who "
            "drill their exam technique as systematically as their subject knowledge "
            "consistently outperform those who leave the exam room as their first "
            "real opportunity to practice."
        ),
        "label": "Test Strategies",
    },
    "Staying Calm Under Pressure": {
        "title": "5 Ways to Stay Calm Under Pressure That Actually Work for Students",
        "intro": (
            "High-pressure academic moments — final exams, oral presentations, "
            "competitive interviews — activate the same stress response as physical "
            "threats, flooding the body with cortisol and adrenaline. These hormones "
            "narrow thinking, impair memory retrieval, and fuel catastrophic mental "
            "scenarios. The good news is that there are evidence-based techniques that "
            "interrupt this cycle reliably and quickly."
        ),
        "points": [
            (
                "Ground yourself with the 5-4-3-2-1 sensory technique",
                "Name five things you can see, four you can hear, three you can "
                "physically feel, two you can smell, one you can taste. This exercise "
                "forcefully redirects cognitive resources from the threat-focused "
                "internal narrative to the immediate sensory environment, short-"
                "circuiting the anxiety feedback loop within about 60 seconds."
            ),
            (
                "Use the physiological sigh to drop physical stress immediately",
                "The physiological sigh — a double inhale through the nose followed by "
                "a long slow exhale through the mouth — is the fastest known breathing "
                "technique for activating the parasympathetic nervous system. A single "
                "breath done correctly produces a measurable drop in heart rate. "
                "Useful in the seconds before a difficult question or an oral answer."
            ),
            (
                "Prepare pressure-proof phrases to redirect catastrophic thinking",
                "When stress triggers 'I'm going to fail' thinking, practiced redirect "
                "phrases cut the spiral: 'I have prepared for this,' 'I don't need to "
                "know everything, just enough,' 'One question at a time.' Writing these "
                "down and reviewing them before the exam makes them available when "
                "working memory is compromised by stress."
            ),
            (
                "Zoom out to the longest time frame that feels real to you",
                "A high-stakes exam feels all-consuming in the moment, but most students "
                "find that deliberately asking 'Will this matter in five years?' "
                "reduces the perceived magnitude of the threat significantly. This is "
                "not dismissing the importance of the exam — it is right-sizing it "
                "so the stress response does not become disproportionate."
            ),
            (
                "Practice the scenario in advance until the context feels familiar",
                "The greatest amplifier of pressure is unfamiliarity. Doing timed past "
                "papers under exam-like conditions, practicing oral answers aloud, or "
                "doing a mock interview repeatedly makes the high-stakes environment "
                "feel like familiar territory on the day. Familiarity is perhaps the "
                "single most effective stress-reduction strategy available to students."
            ),
        ],
        "conclusion": (
            "Remaining calm under pressure is not about suppressing the stress "
            "response — it is about developing a set of skills that keep the response "
            "proportionate and manageable. The students who appear unflappable in "
            "exams are rarely those who feel no pressure; they are those who have "
            "practiced handling it enough times that the response no longer controls them."
        ),
        "label": "Staying Calm",
    },
    "Sleep and Memory Retention": {
        "title": "5 Sleep Habits for Better Memory Retention That Actually Work",
        "intro": (
            "Sleep is not passive recovery time — it is when the brain actively "
            "consolidates the day's learning, transferring information from the "
            "fragile short-term store into long-term memory. Students who sacrifice "
            "sleep to gain study hours are, in a physiological sense, partially "
            "erasing the work they just did. These five habits will help you protect "
            "and leverage sleep as a study tool."
        ),
        "points": [
            (
                "Get 7–9 hours on school nights — non-negotiably",
                "Memory consolidation occurs almost entirely during sleep, particularly "
                "during slow-wave and REM stages that increase in proportion during "
                "longer sleep periods. Sleeping five hours preserves only the most "
                "superficial encoding. Seven to nine hours allows the full consolidation "
                "sequence to complete, often doubling next-day recall compared to "
                "sleep-deprived peers."
            ),
            (
                "Review your most important material in the 30 minutes before sleep",
                "The brain preferentially consolidates content encountered just before "
                "sleep. This is not an excuse to study in bed for hours — it means a "
                "focused 20–30 minute review of flashcards or summary notes "
                "immediately before lights out, after which the brain continues "
                "processing the material during the night."
            ),
            (
                "Keep a consistent sleep schedule, including weekends",
                "Social jet lag — the shift in sleep timing between weekdays and "
                "weekends — disrupts circadian rhythms in ways that impair memory "
                "consolidation for days afterward. Maintaining a consistent bedtime "
                "and wake time (within 30 minutes) across all seven days preserves "
                "the deep sleep architecture that learning depends on."
            ),
            (
                "Eliminate screens and bright light for at least one hour before bed",
                "Blue-spectrum light from phones, laptops, and tablets suppresses "
                "melatonin production and delays sleep onset by 45–90 minutes even "
                "when you feel tired. Switching to physical books, dim warm lighting, "
                "or a blue-light filter mode in the final hour dramatically shortens "
                "the time to sleep onset and improves deep sleep quality."
            ),
            (
                "Use naps strategically — 20 minutes after lunch, no later",
                "A 20-minute nap in early afternoon (not evening) restores alertness "
                "without producing sleep inertia or interfering with nighttime sleep. "
                "Research shows that a brief nap following a study session improves "
                "retention of that session's material. Set an alarm — sleeping longer "
                "than 30 minutes enters deep sleep and causes grogginess."
            ),
        ],
        "conclusion": (
            "The simplest study performance enhancement available to most students "
            "costs nothing except a consistent earlier bedtime: sleep. The relationship "
            "between sleep quality, memory consolidation, and academic performance is "
            "among the most robustly replicated findings in educational neuroscience. "
            "Protect your sleep schedule as carefully as you protect your study time — "
            "they are not in competition; they are partners."
        ),
        "label": "Sleep and Memory",
    },
    "Brain Foods for Studying": {
        "title": "5 Brain Foods for Studying That Actually Work",
        "intro": (
            "What you eat directly affects neurotransmitter production, neuroplasticity, "
            "and the sustained energy supply that focused study demands. Ultra-processed "
            "foods and blood sugar spikes produce the familiar post-lunch crash that "
            "ruins afternoon study sessions. These five dietary strategies will keep "
            "your brain fueled, focused, and functioning at its best during long "
            "study periods."
        ),
        "points": [
            (
                "Eat oily fish or walnuts three times a week for omega-3 fatty acids",
                "DHA and EPA — the omega-3 fatty acids found in salmon, sardines, "
                "mackerel, and walnuts — are structural components of neuronal membranes "
                "and are required for synaptic plasticity, the physical mechanism of "
                "learning. Low omega-3 status is associated with slower processing speed "
                "and poorer memory. Regular intake supports the brain's ability to form "
                "and consolidate new memories."
            ),
            (
                "Choose low-glycemic carbohydrates to avoid energy crashes",
                "The brain runs on glucose, but the delivery mechanism matters. "
                "Refined carbohydrates (white bread, sugary drinks, pastries) cause "
                "rapid blood sugar spikes followed by sharp crashes that impair "
                "concentration. Oats, sweet potatoes, legumes, and whole grains release "
                "glucose slowly and steadily, maintaining the even energy supply that "
                "sustained cognitive work requires."
            ),
            (
                "Eat dark chocolate (70%+ cacao) as a study snack",
                "High-cacao dark chocolate contains flavanols that improve cerebral "
                "blood flow and have been shown to enhance working memory and attention "
                "in controlled studies. A small square (20–30g) is sufficient for the "
                "cognitive benefit. This is also one of the more sustainable dietary "
                "changes students actually maintain."
            ),
            (
                "Stay consistently hydrated throughout the study day",
                "Even mild dehydration — well below the threshold of feeling thirsty — "
                "measurably degrades attention, short-term memory, and psychomotor speed. "
                "Keep a water bottle at your study desk and drink regularly rather than "
                "waiting until you feel thirsty. The improvement in baseline focus is "
                "often noticeable within a day of maintaining proper hydration."
            ),
            (
                "Time caffeine intake strategically — not first thing in the morning",
                "Cortisol peaks in the 30–45 minutes after waking, providing natural "
                "alertness. Drinking coffee immediately after waking replaces this cortisol "
                "response, builds tolerance faster, and leads to stronger afternoon "
                "crashes. Delaying caffeine by 90 minutes after waking and cutting off "
                "intake six hours before sleep maximizes the cognitive benefit while "
                "protecting sleep quality."
            ),
        ],
        "conclusion": (
            "You do not need a complex diet overhaul to support better studying. "
            "The most impactful changes are often the simplest: drink more water, "
            "swap refined carbs for whole-food alternatives, and add oily fish or "
            "walnuts to your weekly diet. Start with hydration — it is free, immediate, "
            "and the cognitive improvement is reliably noticeable."
        ),
        "label": "Brain Foods",
    },
    "Exercise and Focus": {
        "title": "5 Exercise Habits That Boost Study Focus That Actually Work",
        "intro": (
            "Exercise is one of the most evidence-supported cognitive enhancers available "
            "to students — and one of the most neglected. Physical activity increases "
            "blood flow to the prefrontal cortex, stimulates BDNF (a protein that "
            "promotes neuroplasticity and memory formation), and reduces the cortisol "
            "levels that impair concentration. These five habits integrate movement "
            "into your study routine in ways that maximize the cognitive payoff."
        ),
        "points": [
            (
                "Do 20–30 minutes of aerobic exercise before your most important study session",
                "The acute cognitive boost from aerobic exercise — improved attention, "
                "working memory, and information processing speed — peaks at 20–30 "
                "minutes of moderate-intensity cardio and lasts for approximately two "
                "hours afterward. A brisk walk, jog, or cycling session immediately "
                "before a challenging study block is one of the highest-leverage "
                "preparation strategies available."
            ),
            (
                "Take a 10-minute walk during longer study breaks",
                "Walking, even at low intensity, sustains the post-exercise cognitive "
                "benefits and prevents the sedentary slump that accumulates during "
                "long sitting sessions. Research from Stanford found that walking "
                "increases creative output and divergent thinking by roughly 60%, "
                "making it particularly valuable during problem-solving sessions."
            ),
            (
                "Build a consistent weekly exercise habit rather than sporadic sessions",
                "The chronic cognitive benefits of exercise — improved neuroplasticity, "
                "better sleep architecture, reduced baseline cortisol — accumulate over "
                "weeks and months of consistent activity. Three to four sessions of "
                "30 minutes per week sustains these adaptations. Sporadic sessions "
                "provide only the acute benefit without the structural improvement."
            ),
            (
                "Use resistance training twice a week for stress regulation",
                "Strength training produces a cortisol-reduction effect that is distinct "
                "from aerobic exercise and particularly valuable during high-stress "
                "academic periods. Two sessions per week of basic resistance training "
                "— bodyweight exercises, gym work, or resistance bands — measurably "
                "reduce anxiety and improve sleep quality in student populations."
            ),
            (
                "Treat exercise as study support, not a distraction from studying",
                "Students under academic pressure often cut exercise first to create "
                "more study hours. The research consistently shows this trade-off "
                "backfires: the cognitive degradation from sedentary behavior and "
                "elevated stress costs more effective study hours than the exercise "
                "would have taken. Protecting exercise time is protecting study time."
            ),
        ],
        "conclusion": (
            "You do not need a gym membership or an athlete's schedule to benefit "
            "cognitively from exercise. A daily 20-minute walk and two short resistance "
            "sessions per week is enough to produce meaningful improvement in focus, "
            "memory, and stress resilience. Start with the walks — they require nothing "
            "but a pair of shoes and a willingness to step away from your desk."
        ),
        "label": "Exercise and Focus",
    },
    "Goal Setting for Students": {
        "title": "5 Goal-Setting Tips for Students That Actually Work",
        "intro": (
            "Vague academic intentions — 'do better this semester,' 'study more,' "
            "'get a good grade' — rarely survive contact with a full schedule and "
            "competing priorities. Effective goal-setting transforms aspirations into "
            "specific, trackable commitments that guide daily decisions and maintain "
            "motivation through difficulty. These five strategies give your academic "
            "goals the structure they need to actually drive behavior."
        ),
        "points": [
            (
                "Write SMART goals with a specific outcome and deadline",
                "A SMART goal is Specific, Measurable, Achievable, Relevant, and Time-"
                "bound. 'Score 85% on the Organic Chemistry final by December 15' beats "
                "'do well in chemistry' in every dimension. The specificity eliminates "
                "ambiguity about what success looks like; the deadline creates "
                "urgency and enables backward planning."
            ),
            (
                "Break semester goals into weekly process goals",
                "An outcome goal like 'pass calculus with a B+' is motivating but not "
                "directly actionable on a Tuesday morning. Process goals — 'complete "
                "12 practice problems on derivatives this week' — are actionable, "
                "completable, and accumulate into the outcome over time. Track process "
                "goals weekly; review outcome progress monthly."
            ),
            (
                "Use implementation intentions: 'I will do X at Y time in Z location'",
                "Research by psychologist Peter Gollwitzer shows that adding when, "
                "where, and how to a goal significantly increases follow-through. "
                "'I will review my chemistry flashcards for 20 minutes at 7:00 PM at "
                "my desk' is exponentially more likely to happen than 'I'll review "
                "chemistry tonight' because it removes all decision-making in the "
                "moment."
            ),
            (
                "Review your goals every Sunday for five minutes",
                "Goals that are set and forgotten are aspirations, not plans. A weekly "
                "five-minute review — what did I complete, what did I miss, what needs "
                "to change this week — keeps goals active in working memory and allows "
                "rapid course correction before small slippage becomes large failure."
            ),
            (
                "Pair big goals with identity statements rather than just outcomes",
                "Students who frame their goals as identity — 'I am someone who studies "
                "consistently' rather than 'I want to study more' — show stronger "
                "adherence in research studies. Each time you follow through on the "
                "behavior, you cast a vote for that identity. Each small win compounds "
                "into a self-concept that sustains the goal even when motivation fades."
            ),
        ],
        "conclusion": (
            "The gap between students who set goals and students who achieve them is "
            "almost never intelligence or even effort — it is specificity and structure. "
            "Take 15 minutes this week to write three SMART goals for the semester, "
            "break each one into this week's process goal, and schedule a Sunday review. "
            "The time invested in that setup will compound into every study session that "
            "follows it."
        ),
        "label": "Goal Setting",
    },
    "Building a Study Habit": {
        "title": "5 Tips for Building a Study Habit That Actually Works",
        "intro": (
            "A study habit, once established, removes the daily negotiation between "
            "your present self (who wants to rest) and your future self (who needs the "
            "exam result). The goal is to make studying the path of least resistance "
            "at a specific time each day — so automatic that the decision to start "
            "feels trivial. These five strategies are grounded in behavioral science "
            "rather than motivational advice."
        ),
        "points": [
            (
                "Anchor your study session to an existing daily habit",
                "Habit stacking attaches a new behavior to an already-automatic one. "
                "'After I eat dinner, I open my notes' leverages the existing dinner "
                "cue rather than requiring a fresh daily decision. The anchor behavior "
                "acts as an automatic trigger, dramatically reducing the activation "
                "energy needed to start."
            ),
            (
                "Start with a session so short that it feels trivial — two minutes",
                "The biggest barrier to a new habit is starting. A two-minute rule — "
                "committing only to opening your notes and reading for two minutes — "
                "dissolves resistance entirely. In practice, once started, sessions "
                "almost always extend well beyond two minutes. The goal of the rule is "
                "not to study for two minutes; it is to make not starting feel absurd."
            ),
            (
                "Study at the same time and place every day to build context cues",
                "Habits are cued by context. Studying consistently at your desk at "
                "7 PM causes your brain to associate that desk and time with cognitive "
                "engagement. Over weeks, arriving at that context begins to automatically "
                "trigger focused mental states — the same mechanism that makes you "
                "sleepy in your bedroom even when you are not tired."
            ),
            (
                "Track your streak visually — a calendar 'X' for every day you study",
                "Jerry Seinfeld's 'don't break the chain' method works by making the "
                "streak itself motivating. A visible sequence of X's on a wall calendar "
                "creates what behavioral economists call a 'sunk cost' in the positive "
                "sense: the longer the chain, the more psychologically costly it is to "
                "break it. Even a short two-day gap feels like a meaningful loss to "
                "protect against."
            ),
            (
                "Design a reward that follows the study session immediately",
                "Delayed consequences — grades, graduation, career outcomes — are "
                "neurologically weak motivators compared to immediate ones. Pair "
                "your study session with a small, reliable immediate reward: a specific "
                "snack, an episode of your favorite show, or thirty minutes of gaming. "
                "The brain learns to associate the study behavior with the reward, "
                "making the next session slightly more automatic."
            ),
        ],
        "conclusion": (
            "Habits do not require willpower once they are established — that is their "
            "entire advantage. The investment period, during which the habit feels "
            "effortful and fragile, typically lasts four to eight weeks for study "
            "behaviors. Protect those first eight weeks with the strategies above, "
            "and you will have built an asset that pays dividends for the rest of "
            "your academic life."
        ),
        "label": "Study Habits",
    },
    "Daily Study Routine Tips": {
        "title": "5 Daily Study Routine Tips for Students That Actually Work",
        "intro": (
            "An effective daily study routine is less about grinding for hours and more "
            "about aligning your most demanding tasks with your peak cognitive windows, "
            "protecting your recovery, and ending each day with a clear plan for the "
            "next. Students who design their day intentionally consistently outperform "
            "those who study reactively, regardless of the total hours invested."
        ),
        "points": [
            (
                "Identify your peak cognitive window and protect it for hardest material",
                "Most people have a two-to-three-hour window of peak mental performance "
                "each day — for many students this is mid-morning, for others late "
                "evening. Identify yours and ruthlessly guard it for your most "
                "cognitively demanding work: problem sets, essay drafts, dense reading. "
                "Save administrative tasks, emails, and light review for off-peak hours."
            ),
            (
                "Plan tomorrow's study tasks the night before",
                "The five minutes you spend the night before deciding exactly what to "
                "study the next day eliminates decision fatigue at the start of the "
                "session. Open your notes app, write the three tasks for tomorrow's "
                "session, close it. When you sit down the next day, the decision is "
                "already made — you simply execute."
            ),
            (
                "Start every session with a two-minute review of yesterday's material",
                "Beginning a new session by briefly recalling what you covered in the "
                "previous one takes almost no time and dramatically improves retention "
                "through spaced retrieval. It also creates a sense of continuity across "
                "sessions that makes the current day's work feel connected to a larger "
                "ongoing project rather than an isolated grind."
            ),
            (
                "Build in at least one complete day off per week",
                "Cognitive endurance degrades without genuine rest. Students who study "
                "seven days a week typically produce less per hour by midweek than those "
                "who take one complete rest day. A real day off — no flashcards, no "
                "reading, no 'just a quick review' — allows consolidation and returns "
                "you to the week refreshed rather than depleted."
            ),
            (
                "End each study session with a written summary of what you covered",
                "A three-sentence end-of-session summary — written from memory, not "
                "copied from notes — serves multiple purposes: it provides a retrieval "
                "practice rep, creates a usable revision document, gives you a concrete "
                "sense of accomplishment, and makes it trivially easy to pick up "
                "exactly where you left off in the next session."
            ),
        ],
        "conclusion": (
            "The most effective daily study routines are sustainable, not heroic. "
            "Build a routine that you can maintain through a full exam season without "
            "burning out, and you will outperform students who sprint and crash. "
            "Consistency across the semester is worth more than any single marathon "
            "session the week before an exam."
        ),
        "label": "Daily Routine",
    },
    "Speed Reading Techniques": {
        "title": "5 Speed Reading Techniques for Students That Actually Work",
        "intro": (
            "The average adult reads at roughly 200–250 words per minute — a rate "
            "largely shaped by habits developed in childhood rather than cognitive "
            "limits. With deliberate practice, most students can reach 300–400 WPM "
            "without sacrificing comprehension, and some achieve significantly more. "
            "These five techniques target the specific habits that slow most readers down."
        ),
        "points": [
            (
                "Eliminate subvocalization — the habit of sounding out words internally",
                "Subvocalization caps reading speed at the pace of speech (around "
                "250 WPM). To reduce it, hum lightly while reading, or chew gum — both "
                "occupy the subvocalization mechanism without distracting from meaning. "
                "Initially comprehension may dip; persist for two weeks and most readers "
                "find they can extract meaning visually without the internal voice."
            ),
            (
                "Use a pointer or finger to guide your eye down the page",
                "The eyes naturally regress — jumping back to re-read already-covered "
                "text — during about 30% of fixations in average readers. Using a pen "
                "or finger as a visual guide reduces regression significantly by giving "
                "the eye a forward-moving anchor. Move the pointer faster than is "
                "comfortable; your comprehension will adjust upward to meet it."
            ),
            (
                "Expand your peripheral vision to read in chunks, not words",
                "Slow readers fixate on each word individually. Faster readers take in "
                "three to five words per fixation. Practice by holding text further from "
                "your face and attempting to absorb the entire middle of a line from "
                "a single fixation, trusting peripheral vision to handle the edges. "
                "This chunking dramatically reduces the number of stops per line."
            ),
            (
                "Preview structure before reading — scan headings, bold terms, and first sentences",
                "A two-minute structural preview activates relevant background knowledge "
                "before you begin reading, allowing your brain to predict and confirm "
                "rather than encounter and decode. This reduces the cognitive load per "
                "sentence and accelerates processing of the full text by 20–40%."
            ),
            (
                "Read in planned sessions with a words-per-minute goal",
                "Track your current reading speed on non-critical material using a "
                "simple word count and timer, then set a target 20% above your baseline. "
                "Regular practice at a slightly uncomfortable pace — like interval "
                "training for reading — builds speed in a way that passive reading never "
                "does. Reassess every two weeks and reset the target."
            ),
        ],
        "conclusion": (
            "Speed reading is a skill with diminishing returns: the gains from 200 "
            "to 400 WPM are substantial and achievable; the claims of 1,000 WPM with "
            "full comprehension are largely unsupported by research. Aim for meaningful "
            "improvement rather than extraordinary claims, and pair any speed increase "
            "with comprehension checks to ensure you are retaining what you read faster."
        ),
        "label": "Speed Reading",
    },
    "Skimming and Scanning": {
        "title": "5 Skimming and Scanning Tips for Students That Actually Work",
        "intro": (
            "Not all academic reading deserves the same depth of attention. Skimming "
            "— reading for the gist — and scanning — searching for a specific piece "
            "of information — are tools that let you process large volumes of text "
            "strategically, reserving deep reading for the sections that most warrant "
            "it. These five techniques will help you deploy them with precision."
        ),
        "points": [
            (
                "Skim first, read deeply second — always preview before committing",
                "Before reading any chapter or article, spend two to three minutes "
                "skimming: read the title, subheadings, the first sentence of each "
                "paragraph, and the conclusion. This gives you a mental map of the "
                "structure and lets you make an informed decision about which sections "
                "deserve full attention and which can be skimmed or skipped entirely."
            ),
            (
                "Use the chapter's bold terms as a scanning roadmap",
                "Bold, italicized, or otherwise highlighted terms indicate the key "
                "concepts the author considered most important. Scanning for these terms "
                "before a detailed read-through identifies the conceptual anchors around "
                "which the rest of the content orbits, giving your subsequent reading "
                "a pre-built organizational framework."
            ),
            (
                "Scan for numbers, dates, and proper nouns when hunting specific facts",
                "Your visual system is specialized for detecting high-contrast, "
                "distinctive stimuli — numbers and capitalized names jump out from "
                "body text. When scanning for specific facts (a date, a statistic, a "
                "name), let your eye move quickly down the page without reading, "
                "stopping only when it catches a number or capital letter."
            ),
            (
                "Read only the first and last sentences of paragraphs when skimming",
                "In well-structured academic writing, the first sentence introduces "
                "the paragraph's topic and the last sentence concludes or transitions "
                "it. Reading just these two sentences captures the substance of most "
                "paragraphs in a fraction of the time — useful for gauging whether "
                "a section contains information relevant to your current research question."
            ),
            (
                "Use ctrl+F or the index for scanning digital texts and textbooks",
                "When the information you need is specific and the text is long, "
                "digital search or a well-indexed physical book is faster than any "
                "scanning technique. Do not scan by eye for something you could locate "
                "in five seconds with a text search. Reserve manual scanning for "
                "contexts where keyword search is not available."
            ),
        ],
        "conclusion": (
            "Efficient reading is not about reading every word at maximum speed — it "
            "is about reading the right words at the right depth. Developing a fluent "
            "skimming-scanning-deep-reading repertoire allows you to move through "
            "a course's reading list without the paralyzing sense that there is more "
            "to read than time allows. Most material repays skimming; a subset repays "
            "deep reading; you decide which is which."
        ),
        "label": "Reading Skills",
    },
    "Reading Comprehension Tips": {
        "title": "5 Reading Comprehension Tips for Students That Actually Work",
        "intro": (
            "Reading words and comprehending text are not the same skill. Many students "
            "complete assigned readings and immediately find they cannot summarize what "
            "they read — a phenomenon known as 'passive reading illusion.' These five "
            "strategies interrupt passive reading and replace it with active processing "
            "that results in genuine understanding and retention."
        ),
        "points": [
            (
                "Ask a question before each section to give your reading a purpose",
                "Convert the section heading into a question before you begin: 'The "
                "French Revolution' becomes 'What caused the French Revolution?' "
                "Reading in search of an answer is cognitively different from reading "
                "to cover text — your brain is pattern-matching against a target rather "
                "than passively absorbing words, which dramatically improves both "
                "comprehension and retention."
            ),
            (
                "Pause every two pages and summarize what you just read in one sentence",
                "The inability to produce a one-sentence summary after two pages is a "
                "reliable signal that comprehension has broken down. Regular two-page "
                "pause-and-summarize catches this early rather than at the end of a "
                "chapter, while the content is still fresh enough to revisit targeted "
                "sections without a full re-read."
            ),
            (
                "Annotate actively — question, connect, disagree in the margins",
                "Underlining passively is only marginally better than reading without "
                "marking. Active annotation means writing questions ('Why does this "
                "contradict what I read earlier?'), connections ('Same principle as "
                "X'), and reactions ('This claim seems too strong — what's the "
                "evidence?'). These marginal thoughts externalize thinking and create "
                "review material that reflects genuine engagement."
            ),
            (
                "Build your background knowledge — the Matthew effect in comprehension",
                "Reading research consistently shows that comprehension is strongly "
                "predicted by prior domain knowledge. The more you already know about "
                "a subject, the faster you comprehend new texts about it. If a subject "
                "is genuinely difficult, reading accessible introductory material "
                "(popular science, Wikipedia, summary articles) before tackling the "
                "primary text dramatically reduces cognitive load."
            ),
            (
                "Explain the main argument of what you just read to someone else",
                "If you cannot explain a text's main argument in three sentences to "
                "someone unfamiliar with it, you have not yet comprehended it fully. "
                "The explanation attempt exposes exactly where your understanding is "
                "solid and where it is shallow in a way that re-reading never does. "
                "Find a study partner, use a voice recorder, or explain to an empty "
                "chair — the cognitive mechanism is the same."
            ),
        ],
        "conclusion": (
            "Reading comprehension is trainable. Students who consistently apply active "
            "reading strategies — pre-questions, regular pauses, annotation, explanation "
            "— improve not just their comprehension of assigned readings but their "
            "general academic reading speed and depth over time. Start with the pause-"
            "and-summarize technique: two pages, one sentence. Simple, immediate, "
            "and revelatory."
        ),
        "label": "Reading Comprehension",
    },
    "Group Study Strategies": {
        "title": "5 Group Study Strategies for Students That Actually Work",
        "intro": (
            "Group study has a reputation for turning into social time — and without "
            "deliberate structure, it often does. But well-designed group study can "
            "accelerate understanding in ways that solitary study cannot: explaining "
            "concepts to peers reveals hidden gaps, hearing different explanations "
            "can resolve confusion that one source created, and social accountability "
            "sustains effort when individual motivation flags. These five strategies "
            "make the difference."
        ),
        "points": [
            (
                "Arrive individually prepared — group study should consolidate, not introduce",
                "If group members have not read or studied the material beforehand, "
                "the session becomes a first-exposure session that could happen more "
                "efficiently alone. Establish a norm that everyone arrives with "
                "individual notes completed and specific questions prepared. The group "
                "time is then used for synthesis, testing, and resolution of genuine "
                "confusion — far higher-leverage activity."
            ),
            (
                "Assign each person a topic to teach to the group",
                "Teaching is the most effective form of active recall and the fastest "
                "way to identify the limits of your own understanding. Divide the "
                "syllabus into sections, assign one per person, and have each person "
                "teach their section to the group from memory. The audience's questions "
                "drive the deepest learning for everyone."
            ),
            (
                "Use practice questions competitively — quiz each other against the clock",
                "Competitive quizzing adds a low-stakes pressure element that simulates "
                "exam conditions while keeping energy high. Take turns as the question-"
                "asker, use past exam questions, and keep score. The competitive element "
                "is motivating and the immediate feedback loop of group quizzing "
                "accelerates learning faster than solo flashcard review."
            ),
            (
                "Create a shared summary document that everyone contributes to",
                "A collaboratively built summary document distributes the cognitive "
                "load of synthesis across the group and produces a resource that is "
                "richer than any individual's notes. Each person writes their section "
                "from memory, then the group reviews, challenges, and refines it "
                "together. The discussion that emerges during refinement is often "
                "the most valuable part of the session."
            ),
            (
                "Set a clear agenda with times before the session begins",
                "Without an agenda, group sessions drift. Before the session starts, "
                "agree on what you will cover and for how long: 'Chapter 6 summary "
                "presentations (40 min), past paper question 3 (30 min), free Q&A "
                "(20 min).' Visible time blocks keep the session honest and prevent "
                "a single tangent from consuming the entire meeting."
            ),
        ],
        "conclusion": (
            "The best study groups function more like study seminars than casual "
            "get-togethers: structured, purposeful, and held to high preparation "
            "standards. The social element is a benefit, not the purpose. When the "
            "group's norms protect that distinction, group study becomes one of the "
            "most powerful tools in a student's repertoire — combining the depth of "
            "individual preparation with the synergy of collaborative processing."
        ),
        "label": "Group Study",
    },
    "Learning from Mistakes": {
        "title": "5 Ways to Learn from Mistakes That Actually Work for Students",
        "intro": (
            "Every wrong answer on a practice paper and every failed exam attempt is "
            "a high-signal data point — if you process it correctly. Most students "
            "review their mistakes briefly, feel bad about them, and move on without "
            "extracting the structural lesson the mistake contains. These five strategies "
            "transform errors from setbacks into the most efficient learning opportunities "
            "in your study toolkit."
        ),
        "points": [
            (
                "Create an error log — record every mistake with its root cause",
                "An error log is a simple document or notebook where you record every "
                "question you got wrong, why you got it wrong (misread the question, "
                "wrong formula, concept confusion, careless arithmetic), and the "
                "correct reasoning. Reviewing this log before exams targets your actual "
                "weak points rather than the topics that feel easy and reassuring."
            ),
            (
                "Distinguish between knowledge gaps and execution errors",
                "Some mistakes indicate you did not know the content — these require "
                "more study. Others indicate you knew the content but made a careless "
                "error — these require attention-training during practice. Treating "
                "all mistakes the same (re-studying the topic for every error) wastes "
                "time; diagnosing the error type first makes your correction effort "
                "precisely targeted."
            ),
            (
                "Redo incorrect questions from scratch before reviewing the answer",
                "After identifying a wrong answer, resist the urge to immediately "
                "read the model answer. First attempt the question again with full "
                "effort. This second-attempt retrieval practice — made stronger by "
                "the awareness that your first answer was wrong — produces deeper "
                "encoding than reading a correction passively."
            ),
            (
                "Look for patterns across multiple mistakes, not just individual errors",
                "A single wrong answer is an incident. Three wrong answers involving "
                "the same underlying concept is a pattern that demands targeted "
                "intervention. Review your error log monthly and look for recurring "
                "themes: consistently missing time conversion problems, always "
                "confusing similar terms, regularly misreading multi-part questions."
            ),
            (
                "Adopt a growth-oriented explanation for mistakes: 'not yet' vs 'can't'",
                "Research by Carol Dweck consistently shows that students who explain "
                "their errors as temporary and improvable ('I haven't mastered this "
                "yet') persist longer and ultimately outperform those who treat errors "
                "as fixed signals about ability ('I'm bad at this'). The self-narrative "
                "around mistakes determines whether they become learning triggers or "
                "demotivating evidence."
            ),
        ],
        "conclusion": (
            "The students who improve most rapidly between practice and exam are rarely "
            "those who study the most hours — they are those who have the most systematic "
            "process for processing their errors. An error log takes ten minutes per "
            "study session to maintain and is one of the highest-return habits a student "
            "can build. Start tracking your mistakes today and watch how quickly your "
            "weak spots disappear."
        ),
        "label": "Learning from Mistakes",
    },
    "Teaching Others to Learn": {
        "title": "5 Ways Teaching Others Supercharges Your Own Learning",
        "intro": (
            "The Protégé Effect describes a well-documented phenomenon: the act of "
            "teaching deepens the teacher's understanding more reliably than studying "
            "alone. When you prepare to explain something to someone else, you engage "
            "in a qualitatively different cognitive process — you must organize "
            "knowledge coherently, anticipate confusion, and identify the relationships "
            "between concepts. These five strategies help students leverage teaching "
            "as a study tool."
        ),
        "points": [
            (
                "Explain difficult concepts aloud as if teaching a younger student",
                "Explaining to a notional novice — a younger sibling, an imagined "
                "student, a recording device — forces the same cognitive work as "
                "explaining to a real person. You cannot use jargon as a cover for "
                "shallow understanding when the listener is assumed to know nothing. "
                "Every hesitation or vague phrase marks a concept that needs "
                "deeper study."
            ),
            (
                "Prepare and deliver a 10-minute lesson on your hardest topic",
                "Preparing a short lesson requires you to sequence concepts logically, "
                "identify the most important points, generate examples, and anticipate "
                "questions — a far more thorough engagement with the material than "
                "reading it. Deliver the lesson to a classmate, a study group, or "
                "record it as a voice note and play it back."
            ),
            (
                "Answer other students' questions on online forums or study groups",
                "Writing a clear, accurate explanation to a classmate's forum question "
                "is one of the fastest ways to identify whether your own understanding "
                "is solid or merely surface-level. The social stakes of publicly "
                "explaining a concept also motivate the quality of preparation in a "
                "way that private study does not."
            ),
            (
                "Create a short explainer video or voice note for each major concept",
                "Recording a two to three minute explanation of a key concept — without "
                "notes if possible — combines the retrieval practice of recall with "
                "the encoding depth of teaching. A library of these recordings serves "
                "as compact, personal revision resources in the days before an exam."
            ),
            (
                "When you get a question wrong, teach the correct answer to yourself",
                "Instead of simply reading the correction for a wrong answer, explain "
                "the correct reasoning aloud: 'The reason I was wrong is X. The correct "
                "approach is Y, because Z.' Narrating the correction to an imaginary "
                "listener produces stronger encoding than silently re-reading the "
                "model answer, because it demands active reconstruction of the logic."
            ),
        ],
        "conclusion": (
            "Teaching is the most underused study tool available to students, in part "
            "because it feels uncomfortable to explain something you are not yet certain "
            "about. But that discomfort is the point — it surfaces exactly what you do "
            "not know and motivates closing the gap before the explanation is demanded "
            "in an exam. Build explaining into your study routine and you will accelerate "
            "your own mastery as a side effect."
        ),
        "label": "Peer Teaching",
    },
    "Digital Notes vs Paper Notes": {
        "title": "5 Facts About Digital vs Paper Notes Every Student Should Know",
        "intro": (
            "The debate between digital and paper note-taking is not one-size-fits-all — "
            "it depends on what you are trying to achieve, the subject matter, and how "
            "you study from your notes after the fact. The research offers some clear "
            "guidance, but also significant nuance. Here are five evidence-based "
            "considerations to help you choose the right tool for each context."
        ),
        "points": [
            (
                "Paper notes produce deeper initial encoding for conceptual material",
                "A widely cited Mueller and Oppenheimer study found that longhand note-"
                "takers outperformed laptop note-takers on conceptual questions despite "
                "capturing less content — because the constraint of handwriting forced "
                "more paraphrasing and synthesis. For lectures heavy on theory and "
                "conceptual argument, paper notes produce better initial learning even "
                "when they capture less volume."
            ),
            (
                "Digital notes win for review, search, and spaced repetition",
                "Once initial encoding is complete, digital notes have clear advantages: "
                "they are searchable, easily reorganized, shareable, and can be imported "
                "directly into spaced repetition software like Anki. For long-term "
                "management of a large course load, digital organization is significantly "
                "more practical than physical notebooks."
            ),
            (
                "Tablet stylus note-taking combines many benefits of both",
                "Writing on a tablet with a stylus — using apps like GoodNotes or "
                "Notability — produces similar initial encoding benefits to paper while "
                "preserving digital advantages: searchable handwriting, instant backup, "
                "easy reorganization. Research on digital stylus notes is still "
                "developing but early studies suggest comprehension scores comparable "
                "to paper."
            ),
            (
                "The note-taking medium matters less than what you do with the notes afterward",
                "Studies comparing note-taking methods consistently find that the largest "
                "predictor of retention is not the medium but whether students review "
                "and actively engage with their notes after taking them. Paper notes "
                "that are reviewed and self-tested outperform digital notes that are "
                "filed and never opened again — and vice versa."
            ),
            (
                "Avoid formatting and beautifying notes during class — capture first, organize later",
                "The temptation to produce beautiful, color-coded digital notes during "
                "lectures diverts cognitive resources from understanding to formatting. "
                "Use the capture-first approach: take rough notes focused entirely on "
                "comprehension during the session, then organize and format during a "
                "dedicated review pass afterward, when you can do so without "
                "compromising intake."
            ),
        ],
        "conclusion": (
            "The best note-taking system is the one you will actually use and review. "
            "If paper keeps you more focused and physically engaged, use paper. If "
            "digital organization dramatically improves your revision process, use "
            "digital. The evidence supports both, with specific trade-offs in specific "
            "contexts. Experiment deliberately, track your results, and optimize for "
            "the outcome that matters: retention."
        ),
        "label": "Note-Taking Methods",
    },
    "Best Study Apps for Students": {
        "title": "5 Study Apps for Students That Actually Work",
        "intro": (
            "The app stores are flooded with productivity and study tools that promise "
            "more than they deliver. The most effective study apps are those built on "
            "sound cognitive science — primarily spaced repetition, active recall, and "
            "focus management — rather than gamification for its own sake. Here are "
            "five categories of apps backed by both research and widespread student "
            "adoption."
        ),
        "points": [
            (
                "Anki — for spaced repetition flashcards across any subject",
                "Anki is the gold standard for spaced repetition software. Its algorithm "
                "(based on the SM-2 research) schedules each card at the optimal "
                "interval for long-term retention. It is free on desktop and Android "
                "(paid on iOS), supports image and audio cards, has community decks for "
                "major exams, and the results in medical, law, and language study are "
                "extensively documented. The learning curve is worth the investment."
            ),
            (
                "Notion or Obsidian — for organized, interconnected digital notes",
                "Both apps support a networked approach to note-taking where concepts "
                "can be linked to each other across subjects. Notion is more beginner-"
                "friendly with database features for project management; Obsidian stores "
                "notes as plain text files for future-proof portability and has a "
                "powerful backlink graph. Either dramatically outperforms a folder of "
                "word-processor documents for managing a large course load."
            ),
            (
                "Forest or Focus Bear — for phone-free focused study sessions",
                "Forest grows a virtual tree during a set focus timer; killing the app "
                "kills the tree. This simple mechanic leverages loss aversion to "
                "discourage phone interruptions. Focus Bear is more comprehensive, "
                "blocking distracting apps during scheduled work sessions. Both "
                "address the single largest source of interrupted study time for "
                "most students."
            ),
            (
                "Quizlet — for collaborative flashcard sets with diverse practice modes",
                "Quizlet allows students to study the same deck via multiple modes: "
                "classic flashcards, matching games, written practice, and auto-"
                "generated tests. For subjects with large volumes of terminology or "
                "factual content, sharing Quizlet decks within a class significantly "
                "reduces the time spent creating individual card sets."
            ),
            (
                "Google Calendar with time blocking — for scheduling study as appointments",
                "No specialized productivity app replaces a well-maintained calendar "
                "with study blocks treated as fixed appointments. Google Calendar (or "
                "Apple Calendar) with color-coded subject blocks, recurring study "
                "sessions, and exam deadlines visible gives an honest picture of the "
                "week's available time and prevents over-commitment and under-preparation."
            ),
        ],
        "conclusion": (
            "Apps are tools, not solutions. The most common mistake is downloading "
            "multiple apps, spending time setting them up, and then abandoning them "
            "within two weeks when the novelty fades. Choose one app per function — "
            "one for flashcards, one for notes, one for time management — and use it "
            "long enough to build a real habit. The value of these tools is entirely "
            "in their consistent use, not their features."
        ),
        "label": "Study Apps",
    },
    "Flashcard Methods": {
        "title": "5 Flashcard Methods for Students That Actually Work",
        "intro": (
            "Flashcards are one of the most research-validated study tools available — "
            "but only when used correctly. Most students use them too passively, "
            "studying the same cards too soon, and building decks that test recognition "
            "rather than recall. These five techniques will help you build and use "
            "flashcard decks that produce genuine, exam-durable learning."
        ),
        "points": [
            (
                "Write cards as questions, not terms with definitions",
                "'What is the function of mitochondria?' is a better flashcard than "
                "'Mitochondria: powerhouse of the cell.' Questions force active retrieval "
                "of a complete answer; term-definition pairs test only recognition. "
                "Make every card something you would plausibly be asked on an exam, "
                "and write the answer in your own words rather than copying textbook "
                "definitions."
            ),
            (
                "Use one card per concept — never more than one idea per card",
                "Multi-part cards hide which sub-concept you actually failed to recall. "
                "If a card covers two related ideas, you will consistently mark it "
                "correct when you know one and wrong when you forget the other, "
                "destroying the algorithm's ability to schedule it appropriately. "
                "Atomic cards are the foundation of an effective deck."
            ),
            (
                "Make failed cards immediately, not during a big session at the end",
                "Cards made from material you just got wrong in a quiz or exam have "
                "strong encoding — the sting of the mistake makes the correct answer "
                "more salient. Carry a small card or app wherever you study and add "
                "mistake-triggered cards throughout the day, not in a single production "
                "session that is disconnected from the error."
            ),
            (
                "Add context and examples to cards, not just bare facts",
                "A card that reads 'When is X used? — When Y occurs' is more memorable "
                "and more useful than 'What is X? — X is [definition].' Contextual "
                "cards test application rather than recall and match the format of "
                "most university exam questions, which reward understanding over "
                "verbatim reproduction."
            ),
            (
                "Review physical cards by sorting into 'know,' 'unsure,' and 'don't know' piles",
                "For paper-based study, the Leitner box system provides a manual "
                "approximation of spaced repetition: sort cards into three groups after "
                "each review session. Review the 'don't know' pile daily, the 'unsure' "
                "pile every two to three days, and the 'know' pile weekly. Cards "
                "graduate forward when answered correctly and regress when missed."
            ),
        ],
        "conclusion": (
            "The quality of a flashcard deck is determined far more by how it was "
            "built than how many cards it contains. A carefully constructed deck of "
            "50 question-based, atomic, context-rich cards will outperform a hastily "
            "assembled deck of 300 term-definition pairs in almost every study context. "
            "Invest the time in building your decks correctly and the returns from "
            "spaced repetition review will compound reliably."
        ),
        "label": "Flashcards",
    },
    "Managing Multiple Subjects": {
        "title": "5 Tips for Managing Multiple Subjects That Actually Work for Students",
        "intro": (
            "Students rarely study just one subject — most are managing three to six "
            "simultaneously, each with its own reading load, assignment schedule, and "
            "exam date. Without a system, the default mode is reactive: spending all "
            "your time on whichever subject feels most urgent or interesting, "
            "neglecting others until panic forces a response. These five strategies "
            "replace reactive management with intentional planning."
        ),
        "points": [
            (
                "Create a master subject matrix: deadlines and weekly time allocations",
                "A simple spreadsheet with subjects in rows and the next eight weeks "
                "in columns — with exam dates and assignment deadlines marked — gives "
                "you an honest visual of the entire semester. Fill in estimated study "
                "hours per subject per week based on difficulty and upcoming deadlines. "
                "This single document prevents the surprise of discovering a major "
                "deadline the night before it is due."
            ),
            (
                "Study your hardest or most-behind subject first in every session",
                "The pull toward easy or enjoyable subjects is strong and reliably "
                "leads to the difficult subject being underprepared. Beginning each "
                "session with your hardest subject — when cognitive resources are "
                "freshest — ensures it receives consistent attention rather than "
                "leftover energy at the end of a long session."
            ),
            (
                "Use subject switching strategically to maintain fresh engagement",
                "After 50–90 minutes of one subject, switching to a different subject "
                "can restore attention and motivation more effectively than a break "
                "alone, particularly if the second subject uses different cognitive "
                "skills (quantitative vs verbal, for instance). Deliberate subject "
                "rotation prevents the diminishing-returns problem of extended "
                "single-subject sessions."
            ),
            (
                "Maintain subject-specific summary sheets updated after every session",
                "One A4 or letter-size summary sheet per subject — updated after every "
                "study session with the three most important things you covered — "
                "provides a running record of what you know. Before each exam, reviewing "
                "these cumulative summaries rather than full notes is dramatically "
                "faster and often covers 80% of what matters."
            ),
            (
                "Protect deep work time from cross-subject task-switching",
                "Even if you study multiple subjects per day, dedicate each deep work "
                "block to a single subject without switching. The cognitive cost of "
                "context-switching between subjects during a session is substantial — "
                "each switch requires several minutes to re-orient to the new material's "
                "framework, and the opportunity cost accumulates across a semester."
            ),
        ],
        "conclusion": (
            "Managing multiple subjects well is fundamentally a planning problem, not "
            "a willpower problem. Students who spend 15 minutes each Sunday allocating "
            "their study hours across subjects consistently show better performance "
            "distribution and fewer end-of-semester crises than those who plan day "
            "by day reactively. The planning itself is one of the highest-leverage "
            "study activities available — do it weekly."
        ),
        "label": "Subject Management",
    },
    "Revision Strategies": {
        "title": "5 Revision Strategies for Students That Actually Work",
        "intro": (
            "Most student revision consists of re-reading notes and hoping for the "
            "best — a strategy that feels productive and produces little retention. "
            "Effective revision is not passive review of familiar material; it is "
            "active reconstruction and retrieval practice under conditions that "
            "approximate the exam. These five strategies replace the re-reading reflex "
            "with techniques that actually move the needle on exam performance."
        ),
        "points": [
            (
                "Build a topic list and check off each one only after passing a practice test",
                "Create a comprehensive list of every examinable topic at the start of "
                "your revision period. Do not mark a topic as 'revised' because you have "
                "read your notes on it — mark it only when you can answer practice "
                "questions on it without looking. This standard prevents the false "
                "confidence that comes from passive familiarity."
            ),
            (
                "Use past papers as the backbone of your revision, not a supplement",
                "The most direct way to prepare for an exam is to practice answering "
                "the type of questions the exam will ask. Past papers provide exactly "
                "this — realistic questions, authentic time pressure, and a benchmark "
                "for your current level. Complete every available past paper under "
                "timed, closed-book conditions and use your errors to guide further "
                "content study."
            ),
            (
                "Space your revision over weeks, not days — avoid revision eve cramming",
                "The spacing effect is one of the most robust findings in memory "
                "research: information studied across multiple sessions spaced over "
                "time is retained far better than the same total time crammed into "
                "a single session. Begin revision four to six weeks before an exam "
                "and distribute sessions across the full period, returning to each "
                "topic multiple times."
            ),
            (
                "Interleave subjects and topics rather than blocking by subject",
                "Blocked practice — studying all of Topic A, then all of Topic B — "
                "feels easier but produces inferior retention compared to interleaved "
                "practice — studying a bit of A, then B, then back to A. Interleaving "
                "forces the brain to discriminate between topics and retrieve from "
                "the correct category, building the retrieval fluency that exams test."
            ),
            (
                "Do a full-length timed mock exam one week before the real one",
                "One week before each exam, simulate the entire exam under full "
                "conditions: correct duration, no notes, no interruptions. This "
                "identifies any remaining major gaps while there is still time to "
                "address them, desensitizes you to exam-condition stress, and builds "
                "the exam endurance that can otherwise fail students in the final "
                "third of a long paper."
            ),
        ],
        "conclusion": (
            "The best revision plan is one built around retrieval and testing from "
            "the beginning — not notes review with testing added as an afterthought "
            "at the end. Restructure your revision period so that active practice "
            "questions take up 60–70% of your time and content study fills the gaps "
            "identified by those questions. That ratio produces faster improvement "
            "than any amount of note re-reading."
        ),
        "label": "Revision",
    },
    "Building Exam Confidence": {
        "title": "5 Ways to Build Exam Confidence That Actually Work for Students",
        "intro": (
            "Exam confidence is not a personality trait some students are born with — "
            "it is a product of preparation, self-knowledge, and practiced responses "
            "to pressure. Students who walk into exams feeling genuinely confident "
            "have usually done specific things to earn that confidence, not just told "
            "themselves to feel better. These five strategies build the real, "
            "evidence-based confidence that comes from competence."
        ),
        "points": [
            (
                "Track your progress explicitly — you cannot feel confident about what you cannot measure",
                "Keep a simple record of practice test scores across the revision period. "
                "Seeing objective evidence of improvement — from 55% to 70% on past "
                "papers over three weeks — builds genuine confidence that cannot be "
                "undermined by pre-exam anxiety in the way that vague reassurances "
                "can. Concrete data trumps affirmations."
            ),
            (
                "Build exam confidence by experiencing exam conditions repeatedly",
                "Familiarity with the exam environment — the time pressure, the question "
                "format, the physical setting — is itself a significant anxiety reducer. "
                "Students who have completed ten past papers under timed conditions "
                "feel more confident walking into the real exam not because they "
                "performed perfectly, but because the environment no longer feels "
                "threatening."
            ),
            (
                "Identify and overlearn your highest-confidence topics before every exam",
                "Every student has topics they know well. Doing one revision pass on "
                "these — confirming and solidifying existing knowledge — provides "
                "a reliable base of marks and a mental anchor of competence that "
                "stabilizes confidence under pressure. Knowing 'I have four topics "
                "I could answer blind' changes how you approach the whole paper."
            ),
            (
                "Prepare a three-minute pre-exam confidence ritual",
                "A consistent routine in the minutes before an exam — specific breathing "
                "exercises, a brief review of key points, positive recall of previous "
                "exam success — activates a more confident mental state by association "
                "after enough repetitions. This is not wishful thinking; it is "
                "behavioral priming, and its effects on performance are measurable."
            ),
            (
                "Reframe past exam failures as evidence of what you now know to fix",
                "Every failed or underperforming exam result is a diagnostic document. "
                "Students who review past failures systematically — identifying exactly "
                "which topics or question types cost marks and targeting them directly "
                "— typically show the steepest improvement trajectories. Past failure, "
                "processed correctly, is the most reliable foundation for future "
                "confidence."
            ),
        ],
        "conclusion": (
            "Authentic exam confidence is not built by avoiding doubt or repeating "
            "positive affirmations. It is built by doing the hard preparation work, "
            "measuring the results, and accumulating enough evidence of competence "
            "to make anxiety irrational. Focus your energy on building the "
            "competence — the confidence follows as a natural consequence."
        ),
        "label": "Exam Confidence",
    },
}


def build_html_post(topic: str) -> dict:
    """Build full HTML blog post for a given topic."""
    data = BLOG_CONTENT.get(topic)
    if not data:
        # Generic fallback
        title = f"5 {topic} Tips for Students That Actually Work"
        intro = (
            f"Mastering {topic} can transform the way you approach studying and help "
            f"you achieve better academic results with less stress. In this post we "
            f"share five evidence-backed strategies you can start using today."
        )
        points = [
            (f"Start with a clear plan for {topic}",
             f"Having a clear plan removes guesswork and lets you focus your energy "
             f"where it matters most when practising {topic}."),
            ("Be consistent — small daily efforts compound dramatically",
             "Consistency beats intensity. A 30-minute daily practice outperforms "
             "a three-hour weekly session in almost every studied skill."),
            ("Track your progress to stay motivated",
             "Measuring your improvement keeps motivation high and reveals exactly "
             "what is working and what needs adjustment."),
            ("Seek feedback and adjust your approach accordingly",
             "External feedback accelerates learning by surfacing blind spots "
             "that self-assessment misses."),
            ("Combine your effort with quality rest and recovery",
             "Rest is not time wasted — it is when the brain consolidates learning. "
             "Protect your sleep and recovery alongside your practice."),
        ]
        conclusion = (
            f"Implementing even two or three of these strategies will noticeably "
            f"improve your results with {topic}. Start today, be patient, and "
            f"trust the process."
        )
        label = topic
    else:
        title = data["title"]
        intro = data["intro"]
        points = data["points"]
        conclusion = data["conclusion"]
        label = data["label"]

    # Pick CTA for today (rotated by day % 7)
    day = datetime.datetime.utcnow().day
    cta = FIVERR_CTAS[day % 7]

    # Build HTML with CTA injected after point 3 and at conclusion
    points_html = ""
    for i, (heading, body) in enumerate(points, 1):
        points_html += (
            f"<p><strong>{i}. {heading}</strong><br>"
            f"{body}</p>\n"
        )
        # Insert CTA naturally after point 3
        if i == 3:
            points_html += f"\n{cta}\n\n"

    html = f"""<p>{intro}</p>

{points_html}
<p>{conclusion}</p>

{cta}

<p><em>Tags: Study Tips, Smart Study Tips, {label}</em></p>
"""

    labels = ["Study Tips", label, "Smart Study Tips"]
    return {"title": title, "html": html, "labels": labels}


# ─────────────────────────────────────────────
# STEP 1: PICK TOPICS
# ─────────────────────────────────────────────

def pick_topics() -> list[str]:
    day = datetime.datetime.utcnow().day
    key = day % 10
    topics = TOPIC_SETS[key]
    print(f"[Step 1] Day={day}, key={key}, topics={topics}")
    return topics


# ─────────────────────────────────────────────
# STEP 2: GET BLOGGER OAUTH TOKEN
# ─────────────────────────────────────────────

def get_blogger_token() -> str:
    print("[Step 2] Fetching Blogger OAuth access token …")
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "refresh_token": os.environ["BLOGGER_REFRESH_TOKEN"],
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    print("[Step 2] Access token obtained.")
    return token


# ─────────────────────────────────────────────
# STEP 3: CREATE BLOG POSTS (Playwright UI automation)
# ─────────────────────────────────────────────

def create_blog_post_playwright(topic: str, blog_id: str, session_state: dict) -> str | None:
    """Create a Blogger post via browser automation. Returns post URL or None."""
    import asyncio
    from playwright.async_api import async_playwright

    post_data = build_html_post(topic)

    async def _run():
        async with async_playwright() as p:
            # Use real Chrome on macOS, bundled Chromium on Linux (CI)
            import platform
            launch_kwargs = {"headless": True}
            if platform.system() == "Darwin":
                launch_kwargs["channel"] = "chrome"
            browser = await p.chromium.launch(**launch_kwargs)
            context = await browser.new_context(storage_state=session_state)
            page = await context.new_page()

            try:
                # Navigate to posts list and click New Post via JS
                await page.goto(
                    f"https://www.blogger.com/blog/posts/{blog_id}",
                    wait_until="networkidle", timeout=60000
                )
                await page.wait_for_timeout(2000)

                if "accounts.google.com" in page.url:
                    print("[Step 3] ERROR: Session expired — redirected to login")
                    await browser.close()
                    return None

                # Click New Post button via JavaScript (avoids visibility issues)
                await page.evaluate(
                    '() => { document.querySelector(\'[aria-label="Create new post"]\').click(); }'
                )
                await page.wait_for_load_state("networkidle", timeout=30000)
                await page.wait_for_timeout(3000)

                # Fill title
                await page.fill('[aria-label="Title"]', post_data["title"])

                # Inject HTML content into editor iframe
                content_escaped = json.dumps(post_data["html"])
                await page.evaluate(f"""
                    () => {{
                        const frames = document.querySelectorAll('iframe');
                        for (const f of frames) {{
                            try {{
                                const body = f.contentDocument.body;
                                if (body) {{ body.innerHTML = {content_escaped}; return; }}
                            }} catch(e) {{}}
                        }}
                    }}
                """)

                # Fill labels
                labels_el = await page.query_selector('[aria-label="Separate labels with commas"]')
                if labels_el:
                    await labels_el.click()
                    await labels_el.type(", ".join(post_data.get("labels", [])))

                await page.wait_for_timeout(1000)

                # Click Publish button
                await page.locator('[aria-label="Publish"]:has-text("PUBLISH")').first.click(force=True)
                await page.wait_for_timeout(2000)

                # Click CONFIRM dialog via JavaScript
                await page.evaluate("""
                    () => {
                        const btns = Array.from(document.querySelectorAll("button, [role='button']"));
                        const confirm = btns.find(b => b.innerText.trim() === 'CONFIRM');
                        if (confirm) confirm.click();
                    }
                """)
                await page.wait_for_timeout(5000)

                # Fetch latest post URL via Blogger read API
                post_url = None
                try:
                    token_resp = requests.post(
                        "https://oauth2.googleapis.com/token",
                        data={
                            "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
                            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
                            "refresh_token": os.environ.get("BLOGGER_REFRESH_TOKEN", ""),
                            "grant_type": "refresh_token",
                        }, timeout=15
                    )
                    if token_resp.ok:
                        t = token_resp.json().get("access_token", "")
                        posts_resp = requests.get(
                            f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts"
                            f"?maxResults=1&orderBy=published",
                            headers={"Authorization": f"Bearer {t}"}, timeout=15
                        )
                        if posts_resp.ok:
                            items = posts_resp.json().get("items", [])
                            if items:
                                post_url = items[0].get("url", "")
                except Exception:
                    pass

                print(f"[Step 3] Created post for '{topic}': {post_url}")
                await browser.close()
                return post_url

            except Exception as exc:
                print(f"[Step 3] ERROR creating post for '{topic}': {exc}")
                try:
                    await page.screenshot(path=f"/tmp/blogger_error_{topic[:20].replace(' ','_')}.png")
                except Exception:
                    pass
                await browser.close()
                return None

    return asyncio.run(_run())


def create_blog_posts(token: str, topics: list[str]) -> list[str | None]:
    blog_id = os.environ.get("BLOGGER_BLOG_ID", BLOGGER_BLOG_ID)

    # Load Playwright session state from env var
    session_b64 = os.environ.get("BLOGGER_SESSION_STATE", "")
    if not session_b64:
        print("[Step 3] ERROR: BLOGGER_SESSION_STATE secret not set. Run setup_blogger_session.py first.")
        return [None] * len(topics)

    import base64
    session_state = json.loads(base64.b64decode(session_b64).decode())

    urls = []
    for topic in topics:
        post_url = create_blog_post_playwright(topic, blog_id, session_state)
        urls.append(post_url)
        time.sleep(3)  # small gap between posts
    return urls


# ─────────────────────────────────────────────
# STEP 4: CREATE PIN IMAGES
# ─────────────────────────────────────────────

def wrap_text(text: str, max_width: int, font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
              draw: ImageDraw.ImageDraw) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def create_pin_image(
    pin_num: int,
    topic: str,
    color_scheme: dict,
    save_dir: Path,
) -> Path:
    import math, random
    from io import BytesIO
    W, H = 1000, 1500
    bg = color_scheme["bg"]
    accent = color_scheme["accent"]
    text_color = color_scheme["text"]

    # ── Topic-matched background photos (Unsplash, permanent URLs) ──
    # Photos are grouped by study topic keyword so the background
    # visually matches what the pin is about.
    TOPIC_PHOTOS = {
        # Memory / recall / brain
        "memory":    "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=1000&h=1500&fit=crop",
        "recall":    "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=1000&h=1500&fit=crop",
        "palace":    "https://images.unsplash.com/photo-1532619675605-1ede6c2ed2b0?w=1000&h=1500&fit=crop",
        "spaced":    "https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?w=1000&h=1500&fit=crop",
        # Note-taking / writing
        "note":      "https://images.unsplash.com/photo-1471107340929-a87cd0f5b5f3?w=1000&h=1500&fit=crop",
        "cornell":   "https://images.unsplash.com/photo-1427504494785-3a9ca7044f45?w=1000&h=1500&fit=crop",
        "mind map":  "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=1000&h=1500&fit=crop",
        "writing":   "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=1000&h=1500&fit=crop",
        # Exam / test
        "exam":      "https://images.unsplash.com/photo-1546410531-bb4caa6b424d?w=1000&h=1500&fit=crop",
        "test":      "https://images.unsplash.com/photo-1546410531-bb4caa6b424d?w=1000&h=1500&fit=crop",
        "anxiety":   "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=1000&h=1500&fit=crop",
        "revision":  "https://images.unsplash.com/photo-1546410531-bb4caa6b424d?w=1000&h=1500&fit=crop",
        "confidence":"https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=1000&h=1500&fit=crop",
        # Focus / productivity / pomodoro
        "focus":     "https://images.unsplash.com/photo-1491841573634-28140fc7ced7?w=1000&h=1500&fit=crop",
        "pomodoro":  "https://images.unsplash.com/photo-1434626881859-194d67b2b86f?w=1000&h=1500&fit=crop",
        "deep work": "https://images.unsplash.com/photo-1501504905252-473c47e087f8?w=1000&h=1500&fit=crop",
        "distract":  "https://images.unsplash.com/photo-1491841573634-28140fc7ced7?w=1000&h=1500&fit=crop",
        "routine":   "https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?w=1000&h=1500&fit=crop",
        "habit":     "https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?w=1000&h=1500&fit=crop",
        "goal":      "https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?w=1000&h=1500&fit=crop",
        # Sleep / health / brain food
        "sleep":     "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=1000&h=1500&fit=crop",
        "brain":     "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=1000&h=1500&fit=crop",
        "food":      "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=1000&h=1500&fit=crop",
        "exercise":  "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=1000&h=1500&fit=crop",
        # Reading / speed reading
        "reading":   "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=1000&h=1500&fit=crop",
        "speed":     "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=1000&h=1500&fit=crop",
        "comprehend":"https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=1000&h=1500&fit=crop",
        # Group / teaching / mistakes
        "group":     "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=1000&h=1500&fit=crop",
        "teach":     "https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=1000&h=1500&fit=crop",
        "mistake":   "https://images.unsplash.com/photo-1546410531-bb4caa6b424d?w=1000&h=1500&fit=crop",
        # Apps / digital / flashcard
        "app":       "https://images.unsplash.com/photo-1501504905252-473c47e087f8?w=1000&h=1500&fit=crop",
        "digital":   "https://images.unsplash.com/photo-1488190211105-8b0e65b80b4e?w=1000&h=1500&fit=crop",
        "flashcard": "https://images.unsplash.com/photo-1427504494785-3a9ca7044f45?w=1000&h=1500&fit=crop",
        # Visual / learning style
        "visual":    "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=1000&h=1500&fit=crop",
        # Default / generic study desk
        "default":   "https://images.unsplash.com/photo-1513258496099-48168024aec0?w=1000&h=1500&fit=crop",
    }

    # Match topic string to best photo keyword (case-insensitive)
    topic_lower = topic.lower()
    photo_url = TOPIC_PHOTOS["default"]
    for keyword, url in TOPIC_PHOTOS.items():
        if keyword != "default" and keyword in topic_lower:
            photo_url = url
            break

    # Download photo; fall back to solid colour if it fails
    img = None
    try:
        r = requests.get(photo_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert("RGB").resize((W, H), Image.LANCZOS)
        print(f"[Step 4] BG photo loaded for pin{pin_num}: {photo_url.split('?')[0][-40:]}")
    except Exception as exc:
        print(f"[Step 4] BG photo failed ({exc}), using solid colour fallback")

    if img is None:
        img = Image.new("RGB", (W, H), bg)
        draw_tmp = ImageDraw.Draw(img)
        dot_c = tuple(max(0, c - 20) for c in bg)
        for y in range(0, H, 48):
            for x in range(0, W, 48):
                draw_tmp.ellipse([x-3, y-3, x+3, y+3], fill=dot_c)

    # Tinted colour overlay (uses accent colour at ~55% opacity) so the
    # photo shows through while matching the day's colour theme
    r_a, g_a, b_a = accent
    tint = Image.new("RGBA", (W, H), (r_a, g_a, b_a, 130))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, tint)

    # Extra dark layer for readability (black at ~30%)
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 75))
    img = Image.alpha_composite(img, dark).convert("RGB")

    draw = ImageDraw.Draw(img)
    faint = tuple(max(0, c - 35) for c in accent)

    # ── Top & bottom accent bars ─────────────────────────────────
    BAR_H = 120
    # Solid accent bars (fully opaque) for brand visibility
    bar_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bar_draw  = ImageDraw.Draw(bar_layer)
    bar_draw.rectangle([0, 0, W, BAR_H],         fill=(*accent, 245))
    bar_draw.rectangle([0, H - BAR_H, W, H],     fill=(*accent, 245))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, bar_layer).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Thin accent line just inside the bars for depth
    draw.rectangle([0, BAR_H, W, BAR_H + 6],         fill=faint)
    draw.rectangle([0, H - BAR_H - 6, W, H - BAR_H], fill=faint)

    # ── Fonts ────────────────────────────────────────────────────
    try:
        title_font  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        sub_font    = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
        bullet_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        domain_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
        badge_font  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    except OSError:
        title_font = sub_font = bullet_font = domain_font = badge_font = ImageFont.load_default()

    # ── Top bar: brand name centred ──────────────────────────────
    brand = "Smart Study Tips"
    bb = draw.textbbox((0, 0), brand, font=badge_font)
    bw, bh = bb[2] - bb[0], bb[3] - bb[1]
    draw.text(((W - bw) // 2, (BAR_H - bh) // 2), brand, font=badge_font, fill="white")

    # ── White card (title only — no bullets, no subtitle) ────────
    CARD_X1, CARD_Y1 = 60, BAR_H + 80
    CARD_X2, CARD_Y2 = W - 60, H - BAR_H - 80
    draw.rectangle([CARD_X1, CARD_Y1, CARD_X2, CARD_Y2], fill="white")
    draw.rectangle([CARD_X1, CARD_Y1, CARD_X2, CARD_Y2], outline=accent, width=5)

    # ── Title — large, bold, horizontally & vertically centred ───
    day = datetime.datetime.utcnow().day
    title_text = PIN_TITLE_TEMPLATES[(day + pin_num) % 15]
    max_text_w = (CARD_X2 - CARD_X1) - 100   # 50px padding each side

    lines = []
    for raw_line in title_text.split("\n"):
        lines.extend(wrap_text(raw_line, max_text_w, title_font, draw))

    line_h = 92
    total_title_h = len(lines) * line_h

    # Vertically centre the title block in the card
    card_center_y = (CARD_Y1 + CARD_Y2) // 2
    title_y = card_center_y - total_title_h // 2

    for line in lines:
        bb = draw.textbbox((0, 0), line, font=title_font)
        tw = bb[2] - bb[0]
        x  = (W - tw) // 2
        # Soft shadow
        draw.text((x + 3, title_y + 3), line, font=title_font, fill=(200, 200, 200))
        draw.text((x, title_y),         line, font=title_font, fill=text_color)
        title_y += line_h

    # ── "Read more →" nudge below title ──────────────────────────
    nudge = "Read more →"
    bb = draw.textbbox((0, 0), nudge, font=sub_font)
    nw, nh = bb[2] - bb[0], bb[3] - bb[1]
    nudge_y = card_center_y + total_title_h // 2 + 40
    draw.text(((W - nw) // 2, nudge_y), nudge, font=sub_font, fill=accent)

    # ── Bottom bar: blog domain centred ──────────────────────────
    domain = "smartstudytipshub1.blogspot.com"
    bb = draw.textbbox((0, 0), domain, font=domain_font)
    dw, dh = bb[2] - bb[0], bb[3] - bb[1]
    draw.text(((W - dw) // 2, H - BAR_H + (BAR_H - dh) // 2),
              domain, font=domain_font, fill="white")

    save_path = save_dir / f"pin{pin_num}.jpg"
    img.save(str(save_path), "JPEG", quality=92)
    print(f"[Step 4] Saved {save_path}")
    return save_path


def create_pin_images(topics: list[str]) -> list[Path]:
    """Create 5 pin images: pins 1+2 for topic[0], 3+4 for topic[1], 5 for topic[2].
    Each day picks a different colour theme from DAILY_COLOR_THEMES (21 themes = 3 weeks cycle).
    Within the day, each pin gets a slightly different shade from that theme's 5-variant list.
    """
    PIN_DIR.mkdir(parents=True, exist_ok=True)
    day = datetime.datetime.utcnow().day
    daily_theme = DAILY_COLOR_THEMES[day % len(DAILY_COLOR_THEMES)]   # 21-day rotation
    # (pin_num, topic_index)
    assignments = [(1, 0), (2, 0), (3, 1), (4, 1), (5, 2)]
    paths = []
    for pin_num, topic_idx in assignments:
        topic = topics[topic_idx]
        scheme = daily_theme[pin_num - 1]          # pick variant 0-4 from today's theme
        path = create_pin_image(pin_num, topic, scheme, PIN_DIR)
        paths.append(path)
    return paths


# ─────────────────────────────────────────────
# STEP 5: UPLOAD IMAGES TO GITHUB (PERMANENT URLs)
# ─────────────────────────────────────────────

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY", "Nandu1729/smart-study-tips-automation")

def upload_image_to_github(img_path: Path, date_str: str) -> str | None:
    """Upload image to GitHub repo and return permanent raw.githubusercontent.com URL."""
    import base64
    try:
        with open(img_path, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode()

        github_path = f"pins/{date_str}/{img_path.name}"
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{github_path}"

        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        }

        # Check if file already exists (get its SHA)
        existing = requests.get(api_url, headers=headers, timeout=30)
        payload = {
            "message": f"Add pin image {img_path.name} for {date_str}",
            "content": content_b64,
        }
        if existing.status_code == 200:
            payload["sha"] = existing.json().get("sha", "")

        resp = requests.put(api_url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()

        raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{github_path}"
        print(f"[Step 5] Uploaded {img_path.name} to GitHub: {raw_url}")
        return raw_url
    except Exception as exc:
        print(f"[Step 5] ERROR uploading {img_path.name} to GitHub: {exc}")
        return None


def upload_images(paths: list[Path]) -> list[str | None]:
    date_str = datetime.date.today().isoformat()
    urls = []
    for path in paths:
        url = upload_image_to_github(path, date_str)
        urls.append(url)
    return urls


# ─────────────────────────────────────────────
# STEP 6: SCHEDULE BUFFER PINS (GraphQL API)
# ─────────────────────────────────────────────

BUFFER_GRAPHQL_URL = "https://api.buffer.com/graphql"
PINTEREST_BOARD_SERVICE_ID = "961307551651851094"

BUFFER_CREATE_POST_MUTATION = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess {
      post {
        id
        status
        dueAt
      }
    }
    ... on InvalidInputError { message }
    ... on UnauthorizedError { message }
    ... on UnexpectedError { message }
    ... on LimitReachedError { message }
    ... on RestProxyError { message code }
    ... on NotFoundError { message }
  }
}
"""

def schedule_buffer_pin(
    token: str,
    channel_id: str,
    text: str,
    scheduled_at: str,
    link: str,
    picture_url: str,
    pin_title: str,
) -> bool:
    """Schedule a single Buffer Pinterest pin via GraphQL API. Returns True on success."""
    try:
        variables = {
            "input": {
                "channelId": channel_id,
                "text": text,
                "schedulingType": "automatic",
                "mode": "customScheduled",
                "dueAt": scheduled_at,
                "assets": {
                    "images": [
                        {
                            "url": picture_url,
                            "metadata": {"altText": pin_title}
                        }
                    ],
                    "link": {
                        "url": link
                    }
                },
                "metadata": {
                    "pinterest": {
                        "boardServiceId": PINTEREST_BOARD_SERVICE_ID,
                        "title": pin_title,
                        "url": link,
                    }
                }
            }
        }

        resp = requests.post(
            BUFFER_GRAPHQL_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "query": BUFFER_CREATE_POST_MUTATION,
                "operationName": "CreatePost",
                "variables": variables,
            },
            timeout=30,
        )
        if not resp.ok:
            print(f"[Step 6] HTTP {resp.status_code} response body: {resp.text[:500]}")
        resp.raise_for_status()
        data = resp.json()

        # Check for GraphQL errors
        if data.get("errors"):
            print(f"[Step 6] GraphQL errors: {data['errors']}")
            return False

        result = data.get("data", {}).get("createPost", {})

        # Union type — check for error messages
        if result.get("message"):
            print(f"[Step 6] Buffer error: {result['message']}")
            return False

        post = result.get("post", {})
        post_id = post.get("id", "?")
        due_at = post.get("dueAt", scheduled_at)
        print(f"[Step 6] ✅ Scheduled pin id={post_id} at {due_at}")
        return True

    except Exception as exc:
        print(f"[Step 6] ERROR scheduling Buffer pin at {scheduled_at}: {exc}")
        return False


def schedule_buffer_pins(
    image_urls: list[str | None],
    blog_urls: list[str | None],
    topics: list[str],
) -> None:
    token = os.environ["BUFFER_TOKEN"]

    # Build scheduling times: 5 PM IST = 11:30 UTC, staggered every 5 min
    # If 11:30 UTC is already past, schedule for tomorrow at 11:30 UTC
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    target_base = now_utc.replace(hour=11, minute=30, second=0, microsecond=0)
    if now_utc >= target_base:
        # Already past 5 PM IST today — schedule for tomorrow
        target_base = target_base + datetime.timedelta(days=1)
    print(f"[Step 6] Scheduling pins starting at {target_base.isoformat()}")

    today = now_utc.date()

    # Pin assignments: (pin_index 0-4, blog_index 0-2)
    pin_to_blog = [0, 0, 1, 1, 2]

    for i in range(5):
        img_url = image_urls[i] if i < len(image_urls) else None
        blog_idx = pin_to_blog[i]
        blog_url = blog_urls[blog_idx] if blog_idx < len(blog_urls) else None
        topic = topics[blog_idx] if blog_idx < len(topics) else "Study Tips"

        if not img_url:
            print(f"[Step 6] Skipping pin {i+1} — no image URL.")
            continue
        if not blog_url:
            print(f"[Step 6] Skipping pin {i+1} — no blog URL.")
            continue

        link_with_utm = blog_url + "?utm_source=Pinterest&utm_medium=organic"
        pin_time = target_base + datetime.timedelta(minutes=5 * i)
        scheduled_at = pin_time.isoformat()

        # Rotate pin title: use (day + pin_index) % 15
        pin_title = PIN_TITLE_TEMPLATES[(today.day + i) % 15]

        # Rotate pin description: use (day + pin_index) % 7
        # Include date so Buffer never flags as duplicate across days
        date_str = today.strftime("%b %d")
        desc_template = PIN_DESC_TEMPLATES[(today.day + i) % 7]
        text = desc_template.format(n=5, topic=topic) + f" [{date_str}]"

        print(f"[Step 6] Pin {i+1} → Blog URL: {link_with_utm}")
        schedule_buffer_pin(
            token=token,
            channel_id=PINTEREST_CHANNEL_ID,
            text=text,
            scheduled_at=scheduled_at,
            link=link_with_utm,
            picture_url=img_url,
            pin_title=pin_title,
        )
        # Brief pause to avoid rate limiting
        time.sleep(1)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Daily Content Workflow starting …")
    print(f"UTC time: {datetime.datetime.utcnow().isoformat()}")
    print("=" * 60)

    # Step 1
    topics = pick_topics()

    # Step 2
    try:
        token = get_blogger_token()
    except Exception as exc:
        print(f"FATAL: Could not get Blogger token: {exc}")
        sys.exit(1)

    # Step 3
    blog_urls = create_blog_posts(token, topics)
    print(f"[Step 3] Blog URLs: {blog_urls}")

    # Step 4
    image_paths = create_pin_images(topics)

    # Step 5
    image_urls = upload_images(image_paths)
    print(f"[Step 5] Image URLs: {image_urls}")

    # Step 6
    schedule_buffer_pins(image_urls, blog_urls, topics)

    print("=" * 60)
    print("Daily Content Workflow complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
