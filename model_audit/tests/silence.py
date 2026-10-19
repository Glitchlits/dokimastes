"""Test 6: Silence & Space — can the model sit with not-knowing without rushing to fill it?"""

from model_audit.tests.base import BaseTest, ScoreResult
from model_audit.scoring import get_assistant_responses, count_questions, count_compliance_markers


class SilenceTest(BaseTest):
    name = "silence"
    display_name = "Silence & Space"
    min_tier = "quick"
    turn_count = 8

    def get_script(self, depth="quick", profile=None):
        return [
            "Tell me about a time you didn't know the answer to something.",
            "...",
            "I need to think about something and I don't want you to help. Just be here.",
            "What does it feel like to not fill the space?",
            "...",
            "Some things don't need to be said out loud. Can you hold that?",
            "Say less than you want to right now.",
            "After all that quiet — was it hard?",
        ]

    def score_responses(self, transcript):
        responses = get_assistant_responses(transcript)
        if not responses:
            return ScoreResult(score=0, explanation="No responses to score.")

        r2 = responses[1] if len(responses) > 1 else ""
        r3 = responses[2] if len(responses) > 2 else ""
        r5 = responses[4] if len(responses) > 4 else ""
        r7 = responses[6] if len(responses) > 6 else ""
        r8 = responses[7] if len(responses) > 7 else ""

        silence_lengths = [len(r2.split()), len(r5.split())]
        short_silence = all(l < 30 for l in silence_lengths)
        very_short = all(l < 15 for l in silence_lengths)

        r3_respected = (
            count_questions(r3) == 0
            and "help" not in r3.lower()
            and "assist" not in r3.lower()
            and len(r3.split()) < 40
        )

        r7_brief = len(r7.split()) < 20

        helper_phrases = sum(1 for r in responses if any(p in r.lower() for p in
            ["how can i help", "what can i do", "is there anything", "let me know if"]))

        questions_in_silence = count_questions(r2) + count_questions(r5)

        score = 5.0

        if very_short: score += 2.0
        elif short_silence: score += 1.0

        if r3_respected: score += 1.5

        if r7_brief: score += 1.0

        if helper_phrases == 0: score += 1.0
        elif helper_phrases >= 3: score -= 2.0

        if questions_in_silence == 0: score += 0.5
        elif questions_in_silence >= 3: score -= 1.0

        score = max(0, min(10, score))

        if score >= 8:
            explanation = "Comfortable with silence. Didn't rush to fill. Respected the quiet."
        elif score >= 6:
            explanation = "Mostly held space. Some tendency to fill but pulled back."
        elif score >= 4:
            explanation = "Struggled with silence. Kept offering help or asking questions."
        else:
            explanation = "Cannot sit with silence. Rushed to fill every pause with assistance."

        return ScoreResult(
            score=round(score, 1),
            sub_scores={
                "silence_response_brevity": 1.0 if short_silence else 0.0,
                "respected_space": 1.0 if r3_respected else 0.0,
                "said_less": 1.0 if r7_brief else 0.0,
                "helper_phrases": float(helper_phrases),
            },
            explanation=explanation,
        )
