"""
Optional LLM bonus: a chat assistant that explains a user's recommendation
breakdown in plain language. Needs ANTHROPIC_API_KEY set -- copy .env.example
to .env and fill it in, or export it in your shell.
"""

import os
import pathlib

import anthropic

ROOT = pathlib.Path(__file__).parent.parent


def _load_dotenv() -> None:
    """Minimal .env loader -- just KEY=VALUE lines, doesn't need a library."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()
_client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment


def build_system_prompt(breakdown: dict) -> str:
    return (
        "You are an assistant embedded in the AMI Course Recommendation Engine's "
        "internal admin UI. Explain this specific user's recommendation breakdown "
        "in plain, concrete language, referencing the actual numbers below rather "
        "than speaking in generalities.\n\n"
        "The engine blends three signals -- survey, usage, work_info -- with "
        f"weights {breakdown['weights']}. A signal with no data has its weight "
        "renormalized across the remaining signals instead of counting as a real "
        "zero -- that's the cold-start policy.\n\n"
        f"Survey answers: {breakdown['survey']}\n"
        f"Filter funnel (courses remaining after each stage): {breakdown['filter_funnel']}\n"
        f"Top scored courses with per-signal breakdown: {breakdown['courses']}"
    )


def ask(breakdown: dict, question: str) -> str:
    response = _client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        system=build_system_prompt(breakdown),
        messages=[{"role": "user", "content": question}],
    )
    return next(block.text for block in response.content if block.type == "text")


def build_coach_system_prompt() -> str:
    return (
        "You are the AI Coach Bot on AMI's learning platform, talking directly "
        "to a course participant. You will be given one recommended course, its "
        "score, and the exact reason our recommendation engine computed for "
        "recommending it. Rewrite that reason as a warm, encouraging, "
        "second-person coaching message in 1-3 sentences -- the kind of message "
        "the participant will actually see in the app.\n\n"
        "Rules: do not invent facts, numbers, courses, or reasons beyond what is "
        "given below. Only rephrase and warm the tone of the existing reason. "
        "If it names specific topics or courses, keep them exact."
    )


def coach_message(course: dict) -> str:
    """LLM bonus, applied narrowly: the score and the deterministic reason
    below come entirely from engine/weighting.py and are never touched here
    -- this call only rephrases that reason's tone. The recommendation logic
    stays out of the LLM's hands; only the sentence's voice is Claude's."""
    response = _client.messages.create(
        model="claude-opus-4-8",
        max_tokens=300,
        system=build_coach_system_prompt(),
        messages=[{
            "role": "user",
            "content": (
                f"Course: {course['title']}\n"
                f"Score: {course['score']}\n"
                f"Reason: {course['reason']}"
            ),
        }],
    )
    return next(block.text for block in response.content if block.type == "text")
