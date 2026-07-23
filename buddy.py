"""
Vinny — an animated financial buddy for Peace of Mind.

Renders a self-contained animated SVG character (a friendly boy with dark
brown hair) whose expression and motion react to the user's real financial
state, passed in as a simple `mood` string.

Moods:
    "happy"     -> goal reached / on track / positive net worth
    "worried"   -> over budget / declining trend
    "neutral"   -> default idle (breathing, blinking, gentle head tilt)
    "wave"      -> greeting on first load

The SVG uses only CSS animations (no JS) and is rendered through
components.html so the animations reliably run inside Streamlit.
"""

# Palette
_SKIN = "#E8B183"
_SKIN_SHADE = "#D2996A"
_HAIR = "#20150E"        # dark brown, near-black
_HAIR_HI = "#35241A"     # subtle highlight
_JERSEY = "#2F6FED"
_JERSEY_TRIM = "#FFFFFF"
_SHORTS = "#2A3550"
_SHIRT = "#2F6FED"
_SHIRT_DARK = "#255BC7"
_PANTS = "#3C4A63"
_SHOE = "#2A3142"
_MOUTH = "#B5654A"


def _mood_config(mood: str) -> dict:
    """Per-mood visual params: brows, pupil offset, mouth, body animation, speech."""
    configs = {
        "happy": {
            "brow_left": "M44,36 Q50,33 56,35",
            "brow_right": "M64,35 Q70,33 76,36",
            "pupil_dy": 0,
            "mouth": "happy",
            "body_anim": "vinny-bounce",
            "speech": "Looking good! \U0001F389",
            "speech_bg": "#E9F7EF",
            "speech_color": "#1E7A48",
        },
        "worried": {
            "brow_left": "M44,34 Q50,38 56,36",
            "brow_right": "M64,36 Q70,38 76,34",
            "pupil_dy": 2,
            "mouth": "worried",
            "body_anim": "vinny-fret",
            "speech": "Let's watch this one.",
            "speech_bg": "#FCECEC",
            "speech_color": "#B23333",
        },
        "wave": {
            "brow_left": "M44,36 Q50,33 56,35",
            "brow_right": "M64,35 Q70,33 76,36",
            "pupil_dy": 0,
            "mouth": "happy",
            "body_anim": "vinny-breathe",
            "speech": "Hi, I'm Vinny! \U0001F44B",
            "speech_bg": "#EAF1FE",
            "speech_color": "#1E4FB0",
        },
        "neutral": {
            "brow_left": "M44,36 Q50,34 56,36",
            "brow_right": "M64,36 Q70,34 76,36",
            "pupil_dy": 0,
            "mouth": "neutral",
            "body_anim": "vinny-breathe",
            "speech": "",
            "speech_bg": "#F2F3F5",
            "speech_color": "#3C3F45",
        },
    }
    return configs.get(mood, configs["neutral"])


def _mouth_path(kind: str) -> str:
    if kind == "happy":
        return (
            '<path d="M51,53 Q60,65 69,53 Z" fill="#8E3B2C"/>'
            '<path d="M52.5,53 Q60,57.5 67.5,53 Z" fill="#FFFFFF"/>'
        )
    if kind == "worried":
        return (
            f'<path d="M54,58 Q60,53 66,58" fill="none" stroke="{_MOUTH}" '
            'stroke-width="2.2" stroke-linecap="round"/>'
        )
    return (
        f'<line x1="55" y1="56" x2="65" y2="56" stroke="{_MOUTH}" '
        'stroke-width="2.2" stroke-linecap="round"/>'
    )


def character_svg(mood: str = "neutral") -> str:
    cfg = _mood_config(mood)
    if mood == "wave":
        arm_anim, forearm_anim, fa_dur = "vinny-arm-raise", "vinny-forearm-wave", "0.9s"
    else:
        arm_anim, forearm_anim, fa_dur = "vinny-arm-idle", "vinny-forearm-still", "2.5s"
    py = cfg["pupil_dy"]

    speech_html = ""
    if cfg["speech"]:
        speech_html = (
            f'<div class="vinny-speech" style="background:{cfg["speech_bg"]};'
            f' color:{cfg["speech_color"]};">{cfg["speech"]}</div>'
        )

    return f"""
    <style>
    .vinny-wrap {{
        position: relative;
        width: 130px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        font-family: 'Inter', -apple-system, sans-serif;
    }}
    .vinny-speech {{
        font-size: 12px;
        font-weight: 600;
        padding: 6px 10px;
        border-radius: 12px;
        white-space: nowrap;
        animation: vinny-pop 0.4s ease-out;
    }}
    .vinny-svg {{ animation: {cfg['body_anim']} 3s ease-in-out infinite; transform-origin: 60px 112px; }}
    .vinny-eyelid {{ animation: vinny-blink 4.5s infinite; transform-origin: center; }}
    .vinny-arm-l {{ animation: {arm_anim} 2.5s ease-in-out infinite; transform-origin: 39px 79px; }}
    .vinny-forearm-l {{ animation: {forearm_anim} {fa_dur} ease-in-out infinite; transform-origin: 39px 88px; }}
    .vinny-head {{ animation: vinny-tilt 6s ease-in-out infinite; transform-origin: 60px 62px; }}
    .vinny-leg-r {{ animation: vinny-kick 1.4s ease-in-out infinite; transform-origin: 65.5px 104px; }}
    .vinny-ball {{ animation: vinny-juggle 1.4s ease-in-out infinite; transform-origin: 86px 112px; }}
    .vinny-ball-shadow {{ animation: vinny-ball-shadow 1.4s ease-in-out infinite; transform-origin: 86px 120px; }}

    @keyframes vinny-breathe {{
        0%, 100% {{ transform: scale(1); }}
        50%      {{ transform: scale(1.03); }}
    }}
    @keyframes vinny-bounce {{
        0%, 100% {{ transform: translateY(0); }}
        30%      {{ transform: translateY(-6px); }}
        50%      {{ transform: translateY(0); }}
        70%      {{ transform: translateY(-3px); }}
    }}
    @keyframes vinny-fret {{
        0%, 100% {{ transform: rotate(0deg); }}
        25%      {{ transform: rotate(-2deg); }}
        75%      {{ transform: rotate(2deg); }}
    }}
    @keyframes vinny-blink {{
        0%, 92%, 100% {{ transform: scaleY(0); }}
        95%, 97%      {{ transform: scaleY(1); }}
    }}
    @keyframes vinny-tilt {{
        0%, 100% {{ transform: rotate(0deg); }}
        40%      {{ transform: rotate(-4deg); }}
        60%      {{ transform: rotate(4deg); }}
    }}
    @keyframes vinny-arm-idle {{
        0%, 100% {{ transform: rotate(0deg); }}
        50%      {{ transform: rotate(5deg); }}
    }}
    @keyframes vinny-arm-raise {{
        0%, 100% {{ transform: rotate(135deg); }}
    }}
    @keyframes vinny-forearm-still {{
        0%, 100% {{ transform: rotate(0deg); }}
    }}
    @keyframes vinny-forearm-wave {{
        0%, 100% {{ transform: rotate(-15deg); }}
        50%      {{ transform: rotate(15deg); }}
    }}
    @keyframes vinny-kick {{
        0%, 100% {{ transform: rotate(0deg); }}
        15%      {{ transform: rotate(-26deg); }}
        55%      {{ transform: rotate(-3deg); }}
    }}
    @keyframes vinny-juggle {{
        0%, 100% {{ transform: translateY(0) rotate(0deg); }}
        50%      {{ transform: translateY(-16px) rotate(180deg); }}
    }}
    @keyframes vinny-ball-shadow {{
        0%, 100% {{ transform: scale(1); opacity: 0.18; }}
        50%      {{ transform: scale(0.6); opacity: 0.08; }}
    }}
    @keyframes vinny-pop {{
        0%   {{ transform: scale(0.6); opacity: 0; }}
        100% {{ transform: scale(1); opacity: 1; }}
    }}
    </style>
    <div class="vinny-wrap">
        {speech_html}
        <svg class="vinny-svg" width="130" height="130" viewBox="0 0 120 126"
             xmlns="http://www.w3.org/2000/svg" role="img"
             aria-label="Vinny, your money buddy">
            <ellipse cx="60" cy="120" rx="24" ry="3.5" fill="#00000012"/>

            <ellipse class="vinny-ball-shadow" cx="86" cy="120" rx="7" ry="2.2" fill="#000000" opacity="0.18"/>

            <rect x="51" y="104" width="7" height="13" rx="3.5" fill="{_SKIN}"/>
            <rect x="45" y="116" width="14" height="6" rx="3" fill="#FFFFFF" stroke="#CBD1DA" stroke-width="0.8"/>

            <g class="vinny-leg-r">
                <rect x="62" y="104" width="7" height="13" rx="3.5" fill="{_SKIN}"/>
                <rect x="61" y="116" width="14" height="6" rx="3" fill="#FFFFFF" stroke="#CBD1DA" stroke-width="0.8"/>
            </g>


            <rect x="43" y="94" width="34" height="9" rx="2.5" fill="{_SHORTS}"/>
            <path d="M44,101 h13 v6 q0,2.5 -2.5,2.5 h-8 q-2.5,0 -2.5,-2.5 z" fill="{_SHORTS}"/>
            <path d="M63,101 h13 v6 q0,2.5 -2.5,2.5 h-8 q-2.5,0 -2.5,-2.5 z" fill="{_SHORTS}"/>

            <path d="M42,76 q18,-6 36,0 l3,21 q-21,5 -42,0 z" fill="{_JERSEY}"/>
            <path d="M54,74 q6,7 12,0 l-2,-3 q-4,4 -8,0 z" fill="{_JERSEY_TRIM}"/>
            <text x="60" y="93" text-anchor="middle" font-family="Inter, sans-serif"
                  font-size="13" font-weight="700" fill="{_JERSEY_TRIM}">7</text>

            <g class="vinny-arm-l">
                <g class="vinny-forearm-l">
                    <rect x="35" y="85" width="8" height="16" rx="4" fill="{_SKIN}"/>
                    <circle cx="39" cy="101" r="4.6" fill="{_SKIN}"/>
                </g>
                <rect x="33" y="76" width="11" height="12" rx="4" fill="{_JERSEY}"/>
                <rect x="34.8" y="78" width="1.5" height="8" rx="0.7" fill="{_JERSEY_TRIM}"/>
                <rect x="37.2" y="78" width="1.5" height="8" rx="0.7" fill="{_JERSEY_TRIM}"/>
                <rect x="39.6" y="78" width="1.5" height="8" rx="0.7" fill="{_JERSEY_TRIM}"/>
            </g>
            <rect x="76" y="76" width="11" height="12" rx="4" fill="{_JERSEY}"/>
            <rect x="78.9" y="78" width="1.5" height="8" rx="0.7" fill="{_JERSEY_TRIM}"/>
            <rect x="81.3" y="78" width="1.5" height="8" rx="0.7" fill="{_JERSEY_TRIM}"/>
            <rect x="83.7" y="78" width="1.5" height="8" rx="0.7" fill="{_JERSEY_TRIM}"/>
            <rect x="77" y="85" width="8" height="16" rx="4" fill="{_SKIN}"/>
            <circle cx="81" cy="101" r="4.6" fill="{_SKIN}"/>


            <g class="vinny-ball">
                <circle cx="86" cy="112" r="7" fill="#FFFFFF" stroke="#2A3142" stroke-width="1"/>
                <path d="M86,107.8 L89.0,110.0 L87.9,113.6 L84.1,113.6 L83.0,110.0 Z" fill="#2A3142"/>
                <path d="M86,105 L88.3,106.6 L89.0,110.0 L86,107.8 L83.0,110.0 L83.7,106.6 Z" fill="#2A3142" opacity="0.55"/>
                <path d="M79.6,111.4 L83.0,110.0 L84.1,113.6 L81.4,115.2 Z" fill="#2A3142" opacity="0.55"/>
                <path d="M92.4,111.4 L89.0,110.0 L87.9,113.6 L90.6,115.2 Z" fill="#2A3142" opacity="0.55"/>
            </g>
            <rect x="55" y="66" width="10" height="10" rx="3" fill="{_SKIN_SHADE}"/>

            <g class="vinny-head">
                <circle cx="34" cy="45" r="5" fill="{_SKIN_SHADE}"/>
                <circle cx="86" cy="45" r="5" fill="{_SKIN_SHADE}"/>

                <ellipse cx="60" cy="42" rx="25" ry="26" fill="{_SKIN}"/>

                <path d="M33,51 C31,26 43,13 60,13 C77,13 89,26 87,51
                         C85,41 83,34 79,28 C74,34 64,38 54,36
                         C46,35 41,37 37,43 C35,46 34,48 33,51 z" fill="{_HAIR}"/>
                <path d="M33,49 C33,53 33.6,55 35,57 C36.4,53 36.8,51 37.4,48 z" fill="{_HAIR}"/>
                <path d="M87,49 C87,53 86.4,55 85,57 C83.6,53 83.2,51 82.6,48 z" fill="{_HAIR}"/>
                <path d="M47,19 C55,15 68,16 74,22 C65,19 55,19 47,19 z" fill="{_HAIR_HI}"/>

                <circle cx="50" cy="{44 + py}" r="5.6" fill="#FFFFFF"/>
                <circle cx="70" cy="{44 + py}" r="5.6" fill="#FFFFFF"/>
                <circle cx="50" cy="{44 + py}" r="3.4" fill="#2A2140"/>
                <circle cx="70" cy="{44 + py}" r="3.4" fill="#2A2140"/>
                <circle cx="51.4" cy="{42.6 + py}" r="1.2" fill="#FFFFFF"/>
                <circle cx="71.4" cy="{42.6 + py}" r="1.2" fill="#FFFFFF"/>

                <g class="vinny-eyelid">
                    <rect x="43" y="37" width="14" height="8" rx="4" fill="{_SKIN}"/>
                    <rect x="63" y="37" width="14" height="8" rx="4" fill="{_SKIN}"/>
                </g>

                <path d="{cfg['brow_left']}" fill="none" stroke="{_HAIR}"
                      stroke-width="2.4" stroke-linecap="round"/>
                <path d="{cfg['brow_right']}" fill="none" stroke="{_HAIR}"
                      stroke-width="2.4" stroke-linecap="round"/>

                <ellipse cx="60" cy="50" rx="2" ry="1.6" fill="{_SKIN_SHADE}"/>
                {_mouth_path(cfg['mouth'])}
            </g>
        </svg>
    </div>"""


def render(mood: str = "neutral", height: int = 190) -> None:
    """
    Render Vinny into the Streamlit app via components.html (an iframe),
    which reliably runs the SVG's CSS animations. st.markdown with
    unsafe_allow_html strips <style>/animation in many Streamlit versions,
    so we avoid it for the animated character.
    """
    import streamlit.components.v1 as components
    html = f"""
    <div style="display:flex; justify-content:center; align-items:flex-start;
                background:transparent; font-family:'Inter',sans-serif;">
        {character_svg(mood)}
    </div>"""
    components.html(html, height=height)


def compute_mood(summary: dict, goals_df, over_budget: bool, first_load: bool) -> str:
    """
    Decide Vinny's mood from real financial state.
    Priority: greeting -> any goal reached -> over budget -> positive net worth -> neutral.
    """
    if first_load:
        return "wave"

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


# Backwards-compatible alias so older calls keep working.
owl_svg = character_svg
