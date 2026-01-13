"""
Structured prompts for vocal critique analysis using Music Flamingo.
"""

# Main comprehensive analysis prompt
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

# Individual aspect prompts for multi-turn analysis
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


def get_critique_conversation(audio_path: str, mode: str = "comprehensive") -> list:
    """
    Build the conversation structure for Music Flamingo inference.
    
    Args:
        audio_path: Path or URL to the audio file
        mode: Type of analysis - "comprehensive" or specific aspect
        
    Returns:
        List of conversation turns for the model
    """
    prompts = {
        "comprehensive": COMPREHENSIVE_CRITIQUE_PROMPT,
        "pitch": PITCH_ANALYSIS_PROMPT,
        "timing": TIMING_ANALYSIS_PROMPT,
        "breath": BREATH_CONTROL_PROMPT,
        "expression": EXPRESSION_PROMPT,
        "technique": TECHNIQUE_PROMPT,
        "improvements": IMPROVEMENT_SUGGESTIONS_PROMPT,
    }
    
    prompt_text = prompts.get(mode, COMPREHENSIVE_CRITIQUE_PROMPT)
    
    conversation = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text},
                {"type": "audio", "path": audio_path},
            ],
        }
    ]
    
    return conversation


def get_multi_turn_critique(audio_path: str) -> list:
    """
    Build a multi-turn conversation for detailed analysis.
    Returns list of conversation states for sequential inference.
    """
    aspects = ["pitch", "timing", "breath", "expression", "technique"]
    conversations = []
    
    for aspect in aspects:
        conversations.append({
            "aspect": aspect,
            "conversation": get_critique_conversation(audio_path, mode=aspect)
        })
    
    # Final improvements turn
    conversations.append({
        "aspect": "improvements", 
        "conversation": get_critique_conversation(audio_path, mode="improvements")
    })
    
    return conversations

