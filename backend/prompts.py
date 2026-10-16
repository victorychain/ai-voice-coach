"""
Prompts for vocal coaching and Music Flamingo music understanding.

Vocal-coach prompts come from audio-coach-ai. Music-understanding prompts
match the evaluation set on https://musicflamingo.github.io/.
"""

COMPREHENSIVE_CRITIQUE_PROMPT = """You are an expert vocal coach analyzing a singing performance. 
Listen carefully to this vocal recording and provide a detailed, constructive critique.

Analyze the following aspects:

1. **Pitch Accuracy**: How well does the singer stay in tune? Note any flat or sharp tendencies.
2. **Timing & Rhythm**: Evaluate the singer's sense of rhythm and timing precision.
3. **Breath Control**: Assess breath support, phrase length management, and any audible breathing issues.
4. **Tone Quality**: Describe the vocal timbre, resonance, and overall sound quality.
5. **Expression & Dynamics**: How well does the singer convey emotion? Are there dynamic variations?
6. **Technique**: Note any technical aspects like vibrato, runs, transitions between registers.

For each aspect, provide:
- A rating from 1-10
- Specific observations
- One actionable improvement suggestion

End with an overall assessment and the top 3 priority areas to work on."""

PITCH_ANALYSIS_PROMPT = """Analyze the pitch accuracy in this vocal performance. 
Identify:
- Overall intonation quality (sharp, flat, or centered)
- Specific problem areas or intervals
- Consistency across different registers
Provide a rating from 1-10 and specific improvement suggestions."""

TIMING_ANALYSIS_PROMPT = """Evaluate the timing and rhythm in this vocal performance.
Assess:
- Rhythmic precision and consistency
- Handling of syncopation or complex rhythms
- Tempo stability throughout the performance
Provide a rating from 1-10 and specific improvement suggestions."""

BREATH_CONTROL_PROMPT = """Assess the breath control and support in this vocal performance.
Look for:
- Phrase length management
- Audible gasping or breath noise
- Support consistency (especially on high or sustained notes)
- Signs of tension or strain from inadequate breath support
Provide a rating from 1-10 and specific exercises to improve."""

EXPRESSION_PROMPT = """Evaluate the emotional expression and dynamics in this vocal performance.
Consider:
- Dynamic range and variation
- Emotional connection to the lyrics/melody
- Phrasing and musical interpretation
- Use of vocal color and texture changes
Provide a rating from 1-10 and suggestions for more expressive delivery."""

TECHNIQUE_PROMPT = """Analyze the vocal technique demonstrated in this performance.
Evaluate:
- Register transitions (chest to head voice)
- Vibrato quality and control
- Any vocal runs, riffs, or embellishments
- Overall vocal health indicators (strain, tension, pushing)
Provide a rating from 1-10 and technique exercises to practice."""

IMPROVEMENT_SUGGESTIONS_PROMPT = """Based on your analysis of this vocal performance, provide:

1. **Top 3 Priority Areas**: The most impactful things to work on first
2. **Specific Exercises**: 2-3 vocal exercises tailored to address the identified issues
3. **Practice Tips**: How to structure practice sessions for maximum improvement
4. **Encouragement**: Highlight what the singer is doing well to build confidence

Be encouraging but honest - the goal is genuine improvement."""

# Official Music Flamingo evaluation prompts from musicflamingo.github.io
DESCRIBE_PROMPT = (
    "Describe this track in full detail - tell me the genre, tempo, and key, "
    "then dive into the instruments, production style, and overall mood it creates."
)

CAPTION_PROMPT = (
    "Write a rich caption that blends the technical details (genre, BPM, key, chords, mix) "
    "with how the song feels emotionally and dynamically as it unfolds."
)

CRITIC_PROMPT = (
    "Break the track down like a critic - list its tempo, key, and chordal motion, "
    "then explain the textures, dynamics, and emotional impact of the performance."
)

TECHNICAL_ARTISTIC_PROMPT = (
    "Describe this song from both a technical and artistic lens: mention tempo, harmony, "
    "and instrumentation, but also mood, lyrical themes, and structure."
)

LYRICS_PROMPT = "Generate a structured lyric sheet from the input music."

PROMPT_CATALOG = {
    "comprehensive": {
        "group": "vocal",
        "label": "Comprehensive critique",
        "description": "Full vocal-coach report: pitch, timing, breath, tone, expression, technique.",
        "prompt": COMPREHENSIVE_CRITIQUE_PROMPT,
    },
    "pitch": {
        "group": "vocal",
        "label": "Pitch accuracy",
        "description": "Intonation, problem intervals, and register consistency.",
        "prompt": PITCH_ANALYSIS_PROMPT,
    },
    "timing": {
        "group": "vocal",
        "label": "Timing & rhythm",
        "description": "Rhythmic precision, syncopation, and tempo stability.",
        "prompt": TIMING_ANALYSIS_PROMPT,
    },
    "breath": {
        "group": "vocal",
        "label": "Breath control",
        "description": "Support, phrase length, and strain from weak breath.",
        "prompt": BREATH_CONTROL_PROMPT,
    },
    "expression": {
        "group": "vocal",
        "label": "Expression & dynamics",
        "description": "Emotion, phrasing, and vocal color.",
        "prompt": EXPRESSION_PROMPT,
    },
    "technique": {
        "group": "vocal",
        "label": "Technique",
        "description": "Registers, vibrato, runs, and vocal-health signs.",
        "prompt": TECHNIQUE_PROMPT,
    },
    "improvements": {
        "group": "vocal",
        "label": "Practice plan",
        "description": "Priority fixes, exercises, and encouragement.",
        "prompt": IMPROVEMENT_SUGGESTIONS_PROMPT,
    },
    "detailed": {
        "group": "vocal",
        "label": "Detailed breakdown",
        "description": "Separate passes for pitch, timing, breath, expression, technique, and a practice plan.",
        "prompt": COMPREHENSIVE_CRITIQUE_PROMPT,
    },
    "describe": {
        "group": "music",
        "label": "Full track description",
        "description": "Genre, tempo, key, instruments, production, mood.",
        "prompt": DESCRIBE_PROMPT,
    },
    "caption": {
        "group": "music",
        "label": "Rich caption",
        "description": "Technical details blended with how the song feels.",
        "prompt": CAPTION_PROMPT,
    },
    "critic": {
        "group": "music",
        "label": "Critic breakdown",
        "description": "Tempo, key, chords, textures, dynamics, impact.",
        "prompt": CRITIC_PROMPT,
    },
    "technical_artistic": {
        "group": "music",
        "label": "Technical + artistic",
        "description": "Harmony and instrumentation plus mood, lyrics, form.",
        "prompt": TECHNICAL_ARTISTIC_PROMPT,
    },
    "lyrics": {
        "group": "music",
        "label": "Lyric sheet",
        "description": "Structured lyrics transcribed from the recording.",
        "prompt": LYRICS_PROMPT,
    },
}


def get_prompt_text(mode: str, custom_prompt: str | None = None) -> str:
    if mode == "custom":
        text = (custom_prompt or "").strip()
        if not text:
            raise ValueError("Custom mode requires a prompt.")
        return text
    if mode not in PROMPT_CATALOG:
        raise ValueError(f"Unknown analysis mode: {mode}")
    return PROMPT_CATALOG[mode]["prompt"]


def get_critique_conversation(
    audio_path: str,
    mode: str = "comprehensive",
    custom_prompt: str | None = None,
) -> list:
    conversation = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": get_prompt_text(mode, custom_prompt)},
                {"type": "audio", "path": audio_path},
            ],
        }
    ]
    return conversation


def get_multi_turn_critique(audio_path: str) -> list:
    aspects = ["pitch", "timing", "breath", "expression", "technique", "improvements"]
    return [
        {
            "aspect": aspect,
            "conversation": get_critique_conversation(audio_path, mode=aspect),
        }
        for aspect in aspects
    ]


def list_prompt_modes() -> list[dict]:
    return [
        {"id": mode_id, **{k: v for k, v in meta.items() if k != "prompt"}}
        for mode_id, meta in PROMPT_CATALOG.items()
    ]
