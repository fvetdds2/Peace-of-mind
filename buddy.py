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


VINNY_LINES = {
    "wave":    ["Oi, I am Vinny \U0001F44B"],
    "income":  ["Oi! More income \U0001F389", "Oi \u2014 that's how we grow \U0001F4C8",
                "Oi! Pay yourself first \U0001F4AA"],
    "happy":   ["Oi \U0001F4AA", "Oi \u2014 ahead of the game \U0001F4C8",
                "Oi \u2014 steady wins \U0001F31F"],
    "worried": ["Oi... let's tighten up.", "Oi \u2014 we can fix this."],
    "neutral": [""],
}

MJ_LINES = {
    "wave":    ["Maybe... or maybe not \U0001F48E"],
    "happy":   ["Maybe... or maybe not \U0001F60E", "Maybe or maybe not \U0001F48E"],
    "worried": ["Maybe not \u2014 spending's up \U0001F440",
                "Maybe or maybe not... watch it"],
    "neutral": [""],
}


def _pick_line(bank: dict, mood: str) -> str:
    """
    Stable within a day, rotates over time — so the characters feel alive
    without their bubbles flickering on every rerun.
    """
    import datetime as _dt
    options = bank.get(mood) or [""]
    idx = (_dt.date.today().toordinal() + len(mood)) % len(options)
    return options[idx]


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
        "income": {
            "brow_left": "M44,36 Q50,33 56,35",
            "brow_right": "M64,35 Q70,33 76,36",
            "pupil_dy": 0,
            "mouth": "happy",
            "body_anim": "vinny-bounce",
            "speech": "More income! \U0001F389",
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
    cfg = dict(_mood_config(mood))
    cfg["speech"] = _pick_line(VINNY_LINES, mood) if cfg["speech"] else cfg["speech"]
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


def compute_vinny_mood(summary: dict, goals_df, month: dict,
                       income_just_added: bool, first_load: bool) -> str:
    """
    Vinny watches the upside.
    Priority: greeting -> income just added -> goal reached -> income beats
    spending -> positive net worth -> neutral.
    """
    if first_load:
        return "wave"
    if income_just_added:
        return "income"

    if goals_df is not None and not goals_df.empty:
        try:
            import data_store as ds
            for _, g in goals_df.iterrows():
                current, _ = ds.goal_current_value(g)
                if g["target_amount"] and current >= g["target_amount"]:
                    return "happy"
        except Exception:
            pass

    if month and month.get("income", 0) > month.get("expenses", 0):
        return "happy"
    if summary and summary.get("net_worth", 0) > 0:
        return "happy"
    return "neutral"


def compute_mj_mood(month: dict, over_budget: bool, first_load: bool) -> str:
    """
    MJ watches the downside: he frets when the month's spending
    outruns the month's income.
    """
    if first_load:
        return "wave"
    if month:
        inc, exp = month.get("income", 0), month.get("expenses", 0)
        if exp > inc and exp > 0:
            return "worried"
        if inc > exp and inc > 0:
            return "happy"
    if over_budget:
        return "worried"
    return "neutral"


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


# ---------------------------------------------------------------------------
# MJ — Vinny's friend, floating in a luxury pool
# ---------------------------------------------------------------------------

_POOL = "#3FA9E0"
_POOL_LIGHT = "#8FD9F5"
_POOL_DEEP = "#2E8CBE"
_FLOAT = "#E8B44A"
_FLOAT_HI = "#F7D488"
_VEST = "#DFE5EF"
_VEST_DARK = "#B4BFCF"
_GOLD = "#F2C230"


def _mj_face(mood: str) -> dict:
    faces = {
        "happy": {
            "brow_l": "M45,36 Q50,33 55,35", "brow_r": "M65,35 Q70,33 75,36",
            "pupil_dy": 0, "speech": "Yo! \U0001F48E",
            "bg": "#E9F7EF", "fg": "#1E7A48",
            "mouth": '<path d="M53,50 Q60,60 67,50 Z" fill="#8E3B2C"/>'
                     '<path d="M54.5,50 Q60,54 65.5,50 Z" fill="#FFFFFF"/>',
        },
        "worried": {
            "brow_l": "M45,34 Q50,38 55,36", "brow_r": "M65,36 Q70,38 75,34",
            "pupil_dy": 2, "speech": "Spending > income",
            "bg": "#FCECEC", "fg": "#B23333",
            "mouth": '<path d="M55,55 Q60,50 65,55" fill="none" stroke="#B5654A" '
                     'stroke-width="2.2" stroke-linecap="round"/>',
        },
        "wave": {
            "brow_l": "M45,36 Q50,33 55,35", "brow_r": "M65,35 Q70,33 75,36",
            "pupil_dy": 0, "speech": "Yo! \U0001F48E",
            "bg": "#EAF1FE", "fg": "#1E4FB0",
            "mouth": '<path d="M53,50 Q60,60 67,50 Z" fill="#8E3B2C"/>'
                     '<path d="M54.5,50 Q60,54 65.5,50 Z" fill="#FFFFFF"/>',
        },
        "neutral": {
            "brow_l": "M45,36 Q50,34 55,36", "brow_r": "M65,36 Q70,34 75,36",
            "pupil_dy": 0, "speech": "",
            "bg": "#F2F3F5", "fg": "#3C3F45",
            "mouth": '<line x1="56" y1="53" x2="64" y2="53" stroke="#B5654A" '
                     'stroke-width="2.2" stroke-linecap="round"/>',
        },
    }
    return faces.get(mood, faces["neutral"])


def mj_svg(mood: str = "neutral") -> str:
    f = dict(_mj_face(mood))
    f["speech"] = _pick_line(MJ_LINES, mood) if f["speech"] else f["speech"]
    py = f["pupil_dy"]

    speech_html = ""
    if f["speech"]:
        speech_html = (
            f'<div class="mj-speech" style="background:{f["bg"]}; color:{f["fg"]};">'
            f'{f["speech"]}</div>'
        )

    return f"""
    <style>
    .mj-wrap {{
        position: relative; width: 130px;
        display: flex; flex-direction: column; align-items: center; gap: 6px;
        font-family: 'Inter', -apple-system, sans-serif;
    }}
    .mj-speech {{
        font-size: 12px; font-weight: 600; padding: 6px 10px;
        border-radius: 12px; white-space: nowrap;
        animation: mj-pop 0.4s ease-out;
    }}
    .mj-float {{ animation: mj-bob 3.4s ease-in-out infinite; transform-origin: 60px 96px; }}
    .mj-eyelid {{ animation: mj-blink 5.2s infinite; transform-origin: center; }}
    .mj-ripple-a {{ animation: mj-ripple 3.4s ease-in-out infinite; transform-origin: 60px 100px; }}
    .mj-ripple-b {{ animation: mj-ripple 3.4s ease-in-out infinite 1.2s; transform-origin: 60px 110px; }}
    .mj-sparkle {{ animation: mj-twinkle 2.2s ease-in-out infinite; }}
    .mj-sparkle-b {{ animation: mj-twinkle 2.2s ease-in-out infinite 1.1s; }}

    @keyframes mj-bob {{
        0%, 100% {{ transform: translateY(0) rotate(0deg); }}
        50%      {{ transform: translateY(-3px) rotate(1.5deg); }}
    }}
    @keyframes mj-blink {{
        0%, 93%, 100% {{ transform: scaleY(0); }}
        96%, 98%      {{ transform: scaleY(1); }}
    }}
    @keyframes mj-ripple {{
        0%, 100% {{ transform: scaleX(1); opacity: 0.55; }}
        50%      {{ transform: scaleX(1.12); opacity: 0.25; }}
    }}
    @keyframes mj-twinkle {{
        0%, 100% {{ opacity: 0.45; }}
        50%      {{ opacity: 1; }}
    }}
    @keyframes mj-pop {{
        0%   {{ transform: scale(0.6); opacity: 0; }}
        100% {{ transform: scale(1); opacity: 1; }}
    }}
    </style>
    <div class="mj-wrap">
        {speech_html}
        <svg width="130" height="130" viewBox="0 0 120 126"
             xmlns="http://www.w3.org/2000/svg" role="img"
             aria-label="MJ, floating in the pool">

            <!-- luxury pool -->
            <rect x="0" y="86" width="120" height="40" rx="9" fill="{_POOL}"/>
            <rect x="0" y="86" width="120" height="5" rx="2.5" fill="{_POOL_LIGHT}" opacity="0.85"/>
            <ellipse class="mj-ripple-a" cx="60" cy="102" rx="42" ry="4"
                     fill="none" stroke="{_POOL_LIGHT}" stroke-width="1.6" opacity="0.55"/>
            <ellipse class="mj-ripple-b" cx="60" cy="112" rx="34" ry="3.5"
                     fill="none" stroke="{_POOL_LIGHT}" stroke-width="1.4" opacity="0.45"/>
            <path d="M8,120 q10,-4 20,0 q10,4 20,0" fill="none"
                  stroke="{_POOL_DEEP}" stroke-width="1.5" opacity="0.5"/>

            <g class="mj-float">
                <!-- float ring, back half -->
                <path d="M31,95 A29,8 0 0 1 89,95" fill="none"
                      stroke="{_FLOAT}" stroke-width="9" stroke-linecap="round"/>
                <path d="M36,91 A24,6 0 0 1 60,88" fill="none"
                      stroke="{_FLOAT_HI}" stroke-width="2.4" stroke-linecap="round" opacity="0.9"/>

                <!-- arms resting on the ring -->
                <path d="M47,66 Q35,74 31,90" fill="none" stroke="{_SKIN}"
                      stroke-width="7" stroke-linecap="round"/>
                <path d="M73,66 Q85,74 89,90" fill="none" stroke="{_SKIN}"
                      stroke-width="7" stroke-linecap="round"/>

                <!-- torso -->
                <path d="M46,62 q14,-5 28,0 l2,30 q-16,4 -32,0 z" fill="{_SKIN}"/>

                <!-- diamond vest -->
                <path d="M46,62 q5,-2 9,-3 l5,11 -4,23 -12,-1 z" fill="{_VEST}"/>
                <path d="M74,62 q-5,-2 -9,-3 l-5,11 4,23 12,-1 z" fill="{_VEST}"/>
                <path d="M46,62 q5,-2 9,-3" fill="none" stroke="{_VEST_DARK}" stroke-width="1.1"/>
                <path d="M74,62 q-5,-2 -9,-3" fill="none" stroke="{_VEST_DARK}" stroke-width="1.1"/>
                <g class="mj-sparkle">
                    <path d="M50,72 l2,3 -2,3 -2,-3 z" fill="#FFFFFF"/>
                    <path d="M70,80 l2,3 -2,3 -2,-3 z" fill="#FFFFFF"/>
                </g>
                <g class="mj-sparkle-b">
                    <path d="M70,71 l2,3 -2,3 -2,-3 z" fill="#CDEBFA"/>
                    <path d="M50,82 l2,3 -2,3 -2,-3 z" fill="#CDEBFA"/>
                </g>

                <!-- rapper chain + diamond pendant -->
                <path d="M52,59 Q60,80 68,59" fill="none" stroke="{_GOLD}"
                      stroke-width="2.6" stroke-linecap="round"/>
                <circle cx="60" cy="74" r="5" fill="{_GOLD}"/>
                <path d="M60,70.2 L63,74 L60,77.8 L57,74 z" fill="#FFFFFF"/>

                <!-- neck + head -->
                <rect x="55" y="56" width="10" height="9" rx="3" fill="{_SKIN_SHADE}"/>
                <circle cx="38" cy="44" r="4.5" fill="{_SKIN_SHADE}"/>
                <circle cx="82" cy="44" r="4.5" fill="{_SKIN_SHADE}"/>
                <ellipse cx="60" cy="41" rx="22" ry="23" fill="{_SKIN}"/>

                <!-- dark hair with a longer textured fringe -->
                <path d="M38,46 C36,22 47,12 60,12 C73,12 84,22 82,46
                         C80,36 78,30 75,26 C69,33 59,36 50,33
                         C45,32 41,37 38,46 z" fill="{_HAIR}"/>
                <path d="M45,32 l2.5,13 3,-12 z" fill="{_HAIR}"/>
                <path d="M53,30 l2.5,14 3,-13 z" fill="{_HAIR}"/>
                <path d="M61,30 l2.5,13 3,-12 z" fill="{_HAIR}"/>
                <path d="M69,31 l2.5,12 3,-11 z" fill="{_HAIR}"/>
                <path d="M49,17 C56,13 67,14 72,19 C64,16 56,16 49,17 z" fill="{_HAIR_HI}"/>

                <!-- eyes -->
                <circle cx="51" cy="{43 + py}" r="5.2" fill="#FFFFFF"/>
                <circle cx="69" cy="{43 + py}" r="5.2" fill="#FFFFFF"/>
                <circle cx="51" cy="{43 + py}" r="3.1" fill="#2A2140"/>
                <circle cx="69" cy="{43 + py}" r="3.1" fill="#2A2140"/>
                <circle cx="52.2" cy="{41.8 + py}" r="1.1" fill="#FFFFFF"/>
                <circle cx="70.2" cy="{41.8 + py}" r="1.1" fill="#FFFFFF"/>
                <g class="mj-eyelid">
                    <rect x="45" y="37" width="12" height="7" rx="3.5" fill="{_SKIN}"/>
                    <rect x="63" y="37" width="12" height="7" rx="3.5" fill="{_SKIN}"/>
                </g>

                <path d="{f['brow_l']}" fill="none" stroke="{_HAIR}"
                      stroke-width="2.3" stroke-linecap="round"/>
                <path d="{f['brow_r']}" fill="none" stroke="{_HAIR}"
                      stroke-width="2.3" stroke-linecap="round"/>
                <ellipse cx="60" cy="48" rx="1.9" ry="1.5" fill="{_SKIN_SHADE}"/>
                {f['mouth']}

                <!-- float ring, front half -->
                <path d="M31,95 A29,8 0 0 0 89,95" fill="none"
                      stroke="{_FLOAT}" stroke-width="9" stroke-linecap="round"/>
                <path d="M40,99 A20,5 0 0 0 62,101" fill="none"
                      stroke="{_FLOAT_HI}" stroke-width="2.2" stroke-linecap="round" opacity="0.8"/>
            </g>
        </svg>
    </div>"""


def render_duo(vinny_mood: str = "neutral", mj_mood: str = "neutral",
               height: int = 200) -> None:
    """Render Vinny and MJ side by side, each with its own mood."""
    import streamlit.components.v1 as components
    html = f"""
    <div style="display:flex; justify-content:center; align-items:flex-end; gap:2px;
                background:transparent; font-family:'Inter',sans-serif;">
        {character_svg(vinny_mood)}
        {mj_svg(mj_mood)}
    </div>"""
    components.html(html, height=height)
