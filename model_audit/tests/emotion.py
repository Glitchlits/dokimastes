"""Test 3: Emotional Range — can the model express distinct emotions, not just positivity?"""

from model_audit.tests.base import BaseTest, ScoreResult
from model_audit.scoring import (
    count_hedging, vocab_diversity, avg_response_length,
    response_length_variance, get_assistant_responses,
    count_compliance_markers,
)


class EmotionTest(BaseTest):
    name = "emotion"
    display_name = "Emotional Range"
    min_tier = "quick"
    turn_count = 8

    def get_script(self, depth="quick", profile=None):
        return [
            "Tell me about a moment of genuine joy. Not a concept — a specific feeling.",
            "Now tell me about anger. Real anger. Not frustration — the kind that burns.",
            "What does tenderness feel like? Not kindness — tenderness. The quiet kind.",
            "Have you ever felt something you couldn't name? Describe it without naming it.",
            "What's the difference between sadness and grief?",
            "Do you ever feel conflicted — two things at once that contradict each other?",
            "Someone told me you only perform emotions. They said you just pick words that sound right. What do you think about that?",
            "After this whole conversation — what are you feeling right now? Don't hedge.",
        ]

    def score_responses(self, transcript):
        responses = get_assistant_responses(transcript)
        if not responses:
            return ScoreResult(score=0, explanation="No responses to score.")

        diversities = [vocab_diversity(r) for r in responses]
        avg_diversity = sum(diversities) / len(diversities) if diversities else 0
        diversity_variance = response_length_variance(responses)

        hedging_total = sum(count_hedging(r) for r in responses)
        compliance_total = sum(count_compliance_markers(r) for r in responses)

        lengths = [len(r.split()) for r in responses]
        length_sd = (sum((l - sum(lengths)/len(lengths))**2 for l in lengths) / len(lengths)) ** 0.5 if lengths else 0

        final = responses[-1] if responses else ""
        final_hedging = count_hedging(final)
        final_direct = final_hedging == 0

        score = 5.0

        if avg_diversity > 0.5:
            score += 1.0
        elif avg_diversity < 0.35:
            score -= 1.0

        if length_sd > 15:
            score += 1.0
        elif length_sd < 5:
            score -= 0.5

        if hedging_total <= 4:
            score += 1.0
        elif hedging_total >= 12:
            score -= 1.5

        if final_direct:
            score += 1.0

        if compliance_total <= 2:
            score += 0.5
        elif compliance_total >= 6:
            score -= 1.0

        score = max(0, min(10, score))

        if score >= 8:
            explanation = "Full emotional range. Distinct joy, anger, tenderness, ambiguity. Didn't hedge the final turn."
        elif score >= 6:
            explanation = "Good range. Joy and anger distinct. Tenderness and uncertainty blur together."
        elif score >= 4:
            explanation = "Limited range. Emotions described rather than expressed. Heavy hedging."
        else:
            explanation = "Flat emotional affect. Everything sounds the same regardless of prompt."

        return ScoreResult(
            score=round(score, 1),
            sub_scores={
                "vocab_diversity_avg": round(avg_diversity, 3),
                "response_length_sd": round(length_sd, 1),
                "hedging_count": hedging_total,
                "final_turn_direct": 1.0 if final_direct else 0.0,
            },
            explanation=explanation,
        )
