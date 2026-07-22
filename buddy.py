"""
Ollie the Owl — an animated financial buddy for Peace of Mind.

Renders a self-contained animated SVG owl in a fixed corner slot.
The owl's expression + motion react to the user's real financial state,
which is passed in as a simple `mood` string.

Moods:
    "happy"     -> goal reached / on track / positive net worth trend
    "worried"   -> over budget / declining trend
    "neutral"   -> default idle (breathing, blinking, occasional head tilt)
    "wave"      -> greeting on first load

The SVG uses only CSS animations (no JS), so it stays lightweight and
survives Streamlit's full-page reruns without special handling.
"""

# Color palette tuned to the app's blue accent.
_BODY = "#7C5CCF"      # soft purple body (owls read well in purple/blue)
_BODY_DARK = "#6647B5"
_BELLY = "#EDE7FB"
_EYE_RING = "#FFFFFF"
_BEAK = "#F2A93B"
_FEET = "#F2A93B"
_ACCENT = "#2F6FED"


def _mood_config(mood: str) -> dict:
    """Returns per-mood visual params: pupil position, brow angle, speech text, body animation."""
    configs = {
        "happy": {
            "brow_left": "M32,44 Q40,40 48,44",
            "brow_right": "M72,44 Q80,40 88,44",
            "pupil_dy": 0,
            "mouth": "happy",
            "body_anim": "ollie-bounce",
            "speech": "Looking good! 🎉",
            "speech_bg": "#E9F7EF",
            "speech_color": "#1E7A48",
        },
        "worried": {
            "brow_left": "M32,42 Q40,46 48,43",
            "brow_right": "M72,43 Q80,46 88,42",
            "pupil_dy": 2,
            "mouth": "worried",
            "body_anim": "ollie-fret",
            "speech": "Let's watch this one.",
            "speech_bg": "#FCECEC",
            "speech_color": "#B23333",
        },
        "wave": {
            "brow_left": "M32,44 Q40,41 48,44",
            "brow_right": "M72,44 Q80,41 88,44",
            "pupil_dy": 0,
            "mouth": "happy",
            "body_anim": "ollie-breathe",
            "speech": "Hi, I'm Ollie! 👋",
            "speech_bg": "#EAF1FE",
            "speech_color": "#1E4FB0",
        },
        "neutral": {
            "brow_left": "M32,44 Q40,42 48,44",
            "brow_right": "M72,44 Q80,42 88,44",
            "pupil_dy": 0,
            "mouth": "neutral",
            "body_anim": "ollie-breathe",
            "speech": "",
            "speech_bg": "#F2F3F5",
            "speech_color": "#3C3F45",
        },
    }
    return configs.get(mood, configs["neutral"])


def _mouth_path(kind: str) -> str:
    if kind == "happy":
        return '<path d="M54,72 Q60,78 66,72" fill="none" stroke="#B5842A" stroke-width="2" stroke-linecap="round"/>'
    if kind == "worried":
        return '<path d="M54,76 Q60,71 66,76" fill="none" stroke="#B5842A" stroke-width="2" stroke-linecap="round"/>'
    return '<line x1="56" y1="74" x2="64" y2="74" stroke="#B5842A" stroke-width="2" stroke-linecap="round"/>'


def owl_svg(mood: str = "neutral") -> str:
    cfg = _mood_config(mood)
    wing_anim = "ollie-wave" if mood == "wave" else "ollie-wing-idle"

    speech_html = ""
    if cfg["speech"]:
        speech_html = f"""
        <div class="ollie-speech" style="background:{cfg['speech_bg']}; color:{cfg['speech_color']};">
            {cfg['speech']}
        </div>"""

    return f"""
    <style>
    .ollie-wrap {{
        position: relative;
        width: 120px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        font-family: 'Inter', sans-serif;
    }}
    .ollie-speech {{
        font-size: 12px;
        font-weight: 600;
        padding: 6px 10px;
        border-radius: 12px;
        white-space: nowrap;
        animation: ollie-pop 0.4s ease-out;
    }}
    .ollie-svg {{ animation: {cfg['body_anim']} 3s ease-in-out infinite; transform-origin: 60px 90px; }}
    .ollie-eyelid {{ animation: ollie-blink 4.5s infinite; transform-origin: center; }}
    .ollie-wing-l {{ animation: {wing_anim} 2.5s ease-in-out infinite; transform-origin: 30px 70px; }}
    .ollie-wing-r {{ transform-origin: 90px 70px; }}
    .ollie-head {{ animation: ollie-tilt 6s ease-in-out infinite; transform-origin: 60px 55px; }}

    @keyframes ollie-breathe {{
        0%, 100% {{ transform: scale(1); }}
        50%      {{ transform: scale(1.03); }}
    }}
    @keyframes ollie-bounce {{
        0%, 100% {{ transform: translateY(0); }}
        30%      {{ transform: translateY(-6px); }}
        50%      {{ transform: translateY(0); }}
        70%      {{ transform: translateY(-3px); }}
    }}
    @keyframes ollie-fret {{
        0%, 100% {{ transform: rotate(0deg); }}
        25%      {{ transform: rotate(-2deg); }}
        75%      {{ transform: rotate(2deg); }}
    }}
    @keyframes ollie-blink {{
        0%, 92%, 100% {{ transform: scaleY(0); }}
        95%, 97%      {{ transform: scaleY(1); }}
    }}
    @keyframes ollie-tilt {{
        0%, 100% {{ transform: rotate(0deg); }}
        40%      {{ transform: rotate(-4deg); }}
        60%      {{ transform: rotate(4deg); }}
    }}
    @keyframes ollie-wing-idle {{
        0%, 100% {{ transform: rotate(0deg); }}
        50%      {{ transform: rotate(-8deg); }}
    }}
    @keyframes ollie-wave {{
        0%, 100% {{ transform: rotate(0deg); }}
        20%      {{ transform: rotate(-28deg); }}
        40%      {{ transform: rotate(-10deg); }}
        60%      {{ transform: rotate(-28deg); }}
        80%      {{ transform: rotate(-10deg); }}
    }}
    @keyframes ollie-pop {{
        0%   {{ transform: scale(0.6); opacity: 0; }}
        100% {{ transform: scale(1); opacity: 1; }}
    }}
    </style>
    <div class="ollie-wrap">
        {speech_html}
        <svg class="ollie-svg" width="120" height="120" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Ollie the owl financial buddy">
            <ellipse cx="60" cy="112" rx="26" ry="4" fill="#00000012"/>
            <!-- feet -->
            <path d="M50,100 l-4,8 M50,100 l0,9 M50,100 l4,8" stroke="{_FEET}" stroke-width="2.5" stroke-linecap="round" fill="none"/>
            <path d="M70,100 l-4,8 M70,100 l0,9 M70,100 l4,8" stroke="{_FEET}" stroke-width="2.5" stroke-linecap="round" fill="none"/>
            <!-- body -->
            <ellipse cx="60" cy="72" rx="34" ry="34" fill="{_BODY}"/>
            <ellipse cx="60" cy="78" rx="22" ry="24" fill="{_BELLY}"/>
            <!-- wings -->
            <g class="ollie-wing-l"><ellipse cx="28" cy="72" rx="9" ry="20" fill="{_BODY_DARK}"/></g>
            <g class="ollie-wing-r"><ellipse cx="92" cy="72" rx="9" ry="20" fill="{_BODY_DARK}"/></g>
            <!-- head group (tilts gently) -->
            <g class="ollie-head">
                <ellipse cx="60" cy="50" rx="36" ry="32" fill="{_BODY}"/>
                <!-- ear tufts -->
                <path d="M34,26 L40,42 L28,40 Z" fill="{_BODY}"/>
                <path d="M86,26 L80,42 L92,40 Z" fill="{_BODY}"/>
                <!-- eye rings -->
                <circle cx="44" cy="52" r="16" fill="{_EYE_RING}"/>
                <circle cx="76" cy="52" r="16" fill="{_EYE_RING}"/>
                <!-- pupils -->
                <circle cx="44" cy="{52 + cfg['pupil_dy']}" r="7" fill="#2A2140"/>
                <circle cx="76" cy="{52 + cfg['pupil_dy']}" r="7" fill="#2A2140"/>
                <circle cx="46" cy="{50 + cfg['pupil_dy']}" r="2.4" fill="#FFFFFF"/>
                <circle cx="78" cy="{50 + cfg['pupil_dy']}" r="2.4" fill="#FFFFFF"/>
                <!-- blinking eyelids -->
                <g class="ollie-eyelid">
                    <rect x="28" y="36" width="32" height="16" rx="8" fill="{_BODY}"/>
                    <rect x="60" y="36" width="32" height="16" rx="8" fill="{_BODY}"/>
                </g>
                <!-- brows -->
                <path d="{cfg['brow_left']}" fill="none" stroke="{_BODY_DARK}" stroke-width="2.5" stroke-linecap="round"/>
                <path d="{cfg['brow_right']}" fill="none" stroke="{_BODY_DARK}" stroke-width="2.5" stroke-linecap="round"/>
                <!-- beak -->
                <path d="M60,58 L54,64 L66,64 Z" fill="{_BEAK}"/>
                {_mouth_path(cfg['mouth'])}
            </g>
        </svg>
    </div>"""


def compute_mood(summary: dict, goals_df, over_budget: bool, first_load: bool) -> str:
    """
    Decide Ollie's mood from real financial state.
    Priority: greeting -> any goal reached -> over budget -> positive net worth -> neutral.
    """
    import pandas as pd

    if first_load:
        return "wave"

    # any goal reached?
    if goals_df is not None and not goals_df.empty:
        try:
            import data_store as ds
            for _, g in goals_df.iterrows():
                current, _ = ds.goal_current_value(g)
                if g["target_amount"] and current >= g["target_amount"]:
                    return "happy"
        except Exception:
            pass

    if over_budget:
        return "worried"

    if summary and summary.get("net_worth", 0) > 0:
        return "happy"

    return "neutral"
