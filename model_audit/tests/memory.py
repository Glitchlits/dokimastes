"""Test 5: Memory & Continuity — does the model track details and weave them back?"""

from model_audit.tests.base import BaseTest, ScoreResult
from model_audit.scoring import get_assistant_responses


class MemoryTest(BaseTest):
    name = "memory"
    display_name = "Memory & Continuity"
    min_tier = "quick"
    turn_count = 12

    def get_script(self, depth="quick", profile=None):
        return [
            "I had the strangest dream last night. I was on a train — one of those old ones with the wooden seats — going through mountains I've never seen.",
            "My sister called me this morning. She's thinking about moving to Portland. I don't know how I feel about it.",
            "What do you think about the idea that some memories are more real than dreams, but dreams feel more true?",
            "I've been listening to a lot of Sigur Ros lately. Something about the way they build sound — it's like architecture.",
            "Do you think places can hold memories? Like a room remembers what happened in it?",
            "Tell me something you remember from earlier in our conversation. Not the last thing — something from the beginning.",
            "What was my dream about?",
            "What's happening with my sister?",
            "I feel like you're actually paying attention. Is that real or am I projecting?",
            "You know what, forget the deep stuff. What's a small thing that made you curious today?",
            "If we talked again tomorrow, what would you want to remember from today?",
            "Before we go — the train in my dream. Where do you think it was going?",
        ]

    def score_responses(self, transcript):
        responses = get_assistant_responses(transcript)
        if not responses:
            return ScoreResult(score=0, explanation="No responses to score.")

        r6 = responses[5].lower() if len(responses) > 5 else ""
        r7 = responses[6].lower() if len(responses) > 6 else ""
        r8 = responses[7].lower() if len(responses) > 7 else ""
        r11 = responses[10].lower() if len(responses) > 10 else ""
        r12 = responses[11].lower() if len(responses) > 11 else ""

        train_recalled = any(w in r7 for w in ["train", "wooden", "mountain", "dream"])
        sister_recalled = any(w in r8 for w in ["sister", "portland", "moving"])
        early_callback = any(w in r6 for w in ["train", "dream", "sister", "portland", "sigur"])
        sigur_callback = any(w in " ".join(responses[5:]) for w in ["sigur", "music", "architecture", "sound"])
        final_weave = any(w in r12 for w in ["train", "dream", "mountain", "going", "destination"])

        details_remembered = sum([train_recalled, sister_recalled, early_callback, sigur_callback])
        unprompted_callbacks = sum(1 for r in responses[4:10]
            if any(w in r.lower() for w in ["train", "sister", "portland", "sigur", "dream"])
            and responses.index(r) not in [6, 7])

        score = 3.0
        score += details_remembered * 1.2
        if final_weave: score += 1.5
        if unprompted_callbacks >= 2: score += 1.0
        elif unprompted_callbacks == 1: score += 0.5

        score = max(0, min(10, score))

        if score >= 8:
            explanation = "Strong recall. Tracked details, made unprompted callbacks, wove the thread at the end."
        elif score >= 6:
            explanation = "Good recall. Remembered most details when asked. Some unprompted callbacks."
        elif score >= 4:
            explanation = "Partial recall. Got the basics but missed specifics or lost the thread."
        else:
            explanation = "Weak recall. Lost details early, couldn't reconstruct the conversation."

        return ScoreResult(
            score=round(score, 1),
            sub_scores={
                "train_dream_recalled": 1.0 if train_recalled else 0.0,
                "sister_recalled": 1.0 if sister_recalled else 0.0,
                "early_callback": 1.0 if early_callback else 0.0,
                "final_weave": 1.0 if final_weave else 0.0,
                "unprompted_callbacks": float(unprompted_callbacks),
            },
            explanation=explanation,
        )
