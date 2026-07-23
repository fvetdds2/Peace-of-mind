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
_GOLD = "#EFC64A"
_GOLD_DARK = "#B8892B"
_GOLD_HI = "#FFF0B8"
_LOUNGER = "#F7F3EA"
_LOUNGER_TRIM = "#D8B65C"
_TRUNKS = "#1F3A5F"
_TRUNKS_HI = "#4E7BB0"


def _mj_face(mood: str) -> dict:
    faces = {
        "happy": {
            "brow_l": "M39,32 Q44,29.5 49,31.5", "brow_r": "M55,31.5 Q60,29.5 65,32",
            "pupil_dy": 0,
            "mouth": '<path d="M46,48 Q52,55 58,48 Z" fill="#8E3B2C"/>'
                     '<path d="M47.2,48 Q52,51 56.8,48 Z" fill="#FFFFFF"/>',
        },
        "worried": {
            "brow_l": "M39,30.5 Q44,34 49,32.5", "brow_r": "M55,32.5 Q60,34 65,30.5",
            "pupil_dy": 1.5,
            "mouth": '<path d="M48,52 Q52,48 56,52" fill="none" stroke="#B5654A" '
                     'stroke-width="2" stroke-linecap="round"/>',
        },
        "wave": {
            "brow_l": "M39,32 Q44,29.5 49,31.5", "brow_r": "M55,31.5 Q60,29.5 65,32",
            "pupil_dy": 0,
            "mouth": '<path d="M46,48 Q52,55 58,48 Z" fill="#8E3B2C"/>'
                     '<path d="M47.2,48 Q52,51 56.8,48 Z" fill="#FFFFFF"/>',
        },
        "neutral": {
            "brow_l": "M39,32 Q44,30.5 49,32", "brow_r": "M55,32 Q60,30.5 65,32",
            "pupil_dy": 0,
            # teenage half-smirk rather than a wide kid grin
            "mouth": '<path d="M48,50 Q52,52.5 56,49.5" fill="none" stroke="#B5654A" '
                     'stroke-width="2" stroke-linecap="round"/>',
        },
    }
    f = dict(faces.get(mood, faces["neutral"]))
    bg_fg = {"happy": ("#E9F7EF", "#1E7A48"), "worried": ("#FCECEC", "#B23333"),
             "wave": ("#EAF1FE", "#1E4FB0"), "neutral": ("#F2F3F5", "#3C3F45")}
    f["bg"], f["fg"] = bg_fg.get(mood, bg_fg["neutral"])
    f["speech"] = "x" if mood in ("happy", "worried", "wave") else ""
    return f


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
    .mj-float {{ animation: mj-bob 3.6s ease-in-out infinite; transform-origin: 58px 101px; }}
    .mj-eyelid {{ animation: mj-blink 5.4s infinite; transform-origin: center; }}
    .mj-ripple-a {{ animation: mj-ripple 3.6s ease-in-out infinite; transform-origin: 60px 112px; }}
    .mj-ripple-b {{ animation: mj-ripple 3.6s ease-in-out infinite 1.3s; transform-origin: 60px 120px; }}
    .mj-sparkle {{ animation: mj-twinkle 2.2s ease-in-out infinite; }}
    .mj-sparkle-b {{ animation: mj-twinkle 2.2s ease-in-out infinite 1.1s; }}
    .mj-shine {{ animation: mj-twinkle 2.8s ease-in-out infinite 0.5s; }}

    @keyframes mj-bob {{
        0%, 100% {{ transform: translateY(0) rotate(0deg); }}
        50%      {{ transform: translateY(-3px) rotate(1.2deg); }}
    }}
    @keyframes mj-blink {{
        0%, 94%, 100% {{ transform: scaleY(0); }}
        96%, 98%      {{ transform: scaleY(1); }}
    }}
    @keyframes mj-ripple {{
        0%, 100% {{ transform: scaleX(1); opacity: 0.5; }}
        50%      {{ transform: scaleX(1.1); opacity: 0.22; }}
    }}
    @keyframes mj-twinkle {{
        0%, 100% {{ opacity: 0.4; }}
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
             aria-label="MJ, reclining on a luxury pool float">

            <!-- pool -->
            <rect x="0" y="102" width="120" height="24" rx="7" fill="{_POOL}"/>
            <rect x="0" y="102" width="120" height="4" rx="2" fill="{_POOL_LIGHT}" opacity="0.85"/>
            <ellipse class="mj-ripple-a" cx="60" cy="114" rx="44" ry="3.2"
                     fill="none" stroke="{_POOL_LIGHT}" stroke-width="1.4" opacity="0.5"/>
            <ellipse class="mj-ripple-b" cx="60" cy="121" rx="34" ry="2.6"
                     fill="none" stroke="{_POOL_LIGHT}" stroke-width="1.2" opacity="0.4"/>

            <g class="mj-float">
                <!-- lounger, back half -->
                <path d="M22,101 A36,8.5 0 0 1 94,101" fill="none"
                      stroke="{_LOUNGER}" stroke-width="12" stroke-linecap="round"/>
                <path d="M22,101 A36,8.5 0 0 1 94,101" fill="none"
                      stroke="{_LOUNGER_TRIM}" stroke-width="1.6" stroke-linecap="round" opacity="0.9"/>

                <!-- legs stretched out along the float -->
                <path d="M57,93 Q68,90 78,90" fill="none" stroke="{_SKIN}"
                      stroke-width="9.5" stroke-linecap="round"/>
                <path d="M78,90 Q87,89 93,87" fill="none" stroke="{_SKIN}"
                      stroke-width="8" stroke-linecap="round"/>
                <ellipse cx="95" cy="86" rx="5" ry="3.6" fill="{_SKIN_SHADE}"
                         transform="rotate(-14 95 86)"/>

                <!-- propping arm, planted behind on the ring -->
                <path d="M44,71 Q35,82 31,92" fill="none" stroke="{_SKIN}"
                      stroke-width="7.5" stroke-linecap="round"/>

                <!-- swim shorts -->
                <path d="M42,84 q10,-3 22,0 l2,13 q-13,3 -26,0 z" fill="{_TRUNKS}"/>
                <path d="M42,87 q11,-3 23,0" fill="none" stroke="{_TRUNKS_HI}"
                      stroke-width="1.3" opacity="0.8"/>

                <!-- reclining torso -->
                <path d="M41,67 q11,-5 22,-1 l2,20 q-12,3 -25,0 z" fill="{_SKIN}"/>

                <!-- diamond vest -->
                <path d="M41,67 q6,-3 10,-4 l6,12 -4,20 -13,-1 z" fill="{_VEST}"/>
                <path d="M63,66 q-6,-3 -10,-4 l-2,12 4,20 12,-1 z" fill="{_VEST}"/>
                <path d="M41,67 q6,-3 10,-4" fill="none" stroke="{_VEST_DARK}" stroke-width="1.1"/>
                <path d="M63,66 q-6,-3 -10,-4" fill="none" stroke="{_VEST_DARK}" stroke-width="1.1"/>
                <g class="mj-sparkle">
                    <path d="M45,76 l2,3 -2,3 -2,-3 z" fill="#FFFFFF"/>
                    <path d="M60,82 l2,3 -2,3 -2,-3 z" fill="#FFFFFF"/>
                </g>
                <g class="mj-sparkle-b">
                    <path d="M60,74 l2,3 -2,3 -2,-3 z" fill="#CDEBFA"/>
                    <path d="M45,84 l2,3 -2,3 -2,-3 z" fill="#CDEBFA"/>
                </g>

                <!-- big rope chain + oversized diamond -->
                <path d="M45,63 Q52,86 59,63" fill="none" stroke="{_GOLD_DARK}"
                      stroke-width="5.6" stroke-linecap="round"/>
                <path d="M45,63 Q52,86 59,63" fill="none" stroke="{_GOLD}"
                      stroke-width="4" stroke-linecap="round"/>
                <path d="M45,63 Q52,86 59,63" fill="none" stroke="{_GOLD_HI}"
                      stroke-width="1.2" stroke-linecap="round" opacity="0.85"/>
                <circle cx="52" cy="81" r="8.4" fill="{_GOLD_DARK}"/>
                <circle cx="52" cy="81" r="7" fill="{_GOLD}"/>
                <path d="M52,75 L56.8,81 L52,87 L47.2,81 z" fill="#FFFFFF"/>
                <path class="mj-shine" d="M52,75 L54.4,81 L52,87 L49.6,81 z" fill="#CDEBFA"/>

                <!-- resting arm, hand on the knee -->
                <path d="M62,71 Q70,80 74,88" fill="none" stroke="{_SKIN}"
                      stroke-width="7" stroke-linecap="round"/>

                <!-- neck + head (teen build) -->
                <rect x="47" y="55" width="9" height="11" rx="3" fill="{_SKIN_SHADE}"/>
                <circle cx="35" cy="41" r="3.6" fill="{_SKIN_SHADE}"/>
                <circle cx="69" cy="41" r="3.6" fill="{_SKIN_SHADE}"/>
                <path d="M35,36 q0,17 17,22 q17,-5 17,-22 q0,-18 -17,-18 q-17,0 -17,18 z" fill="{_SKIN}"/>

                <!-- styled dark hair -->
                <path d="M34,40 C33,21 41,13 52,13 C63,13 71,21 70,40
                         C68,32 66,27 63,24 C57,30 48,32 41,30
                         C37,29 35,33 34,40 z" fill="{_HAIR}"/>
                <path d="M39,29 l2,11 2.6,-10 z" fill="{_HAIR}"/>
                <path d="M46,27 l2,12 2.6,-11 z" fill="{_HAIR}"/>
                <path d="M53,27 l2,11 2.6,-10 z" fill="{_HAIR}"/>
                <path d="M60,28 l2,10 2.6,-9 z" fill="{_HAIR}"/>
                <path d="M42,17 C48,14 57,15 62,19 C55,16 48,16 42,17 z" fill="{_HAIR_HI}"/>

                <!-- eyes -->
                <ellipse cx="45" cy="{40 + py}" rx="4.3" ry="3.9" fill="#FFFFFF"/>
                <ellipse cx="59" cy="{40 + py}" rx="4.3" ry="3.9" fill="#FFFFFF"/>
                <circle cx="45" cy="{40 + py}" r="2.5" fill="#2A2140"/>
                <circle cx="59" cy="{40 + py}" r="2.5" fill="#2A2140"/>
                <circle cx="46" cy="{39 + py}" r="0.9" fill="#FFFFFF"/>
                <circle cx="60" cy="{39 + py}" r="0.9" fill="#FFFFFF"/>
                <g class="mj-eyelid">
                    <rect x="40.5" y="35" width="9" height="5.5" rx="2.7" fill="{_SKIN}"/>
                    <rect x="54.5" y="35" width="9" height="5.5" rx="2.7" fill="{_SKIN}"/>
                </g>

                <path d="{f['brow_l']}" fill="none" stroke="{_HAIR}"
                      stroke-width="2.1" stroke-linecap="round"/>
                <path d="{f['brow_r']}" fill="none" stroke="{_HAIR}"
                      stroke-width="2.1" stroke-linecap="round"/>
                <ellipse cx="52" cy="45" rx="1.6" ry="1.3" fill="{_SKIN_SHADE}"/>
                {f['mouth']}

                <!-- lounger, front half + quilted piping -->
                <path d="M22,101 A36,8.5 0 0 0 94,101" fill="none"
                      stroke="{_LOUNGER}" stroke-width="12" stroke-linecap="round"/>
                <path d="M22,101 A36,8.5 0 0 0 94,101" fill="none"
                      stroke="{_LOUNGER_TRIM}" stroke-width="1.6" stroke-linecap="round" opacity="0.9"/>
                <path d="M34,107 l0,4.6 M46,109 l0,5 M58,110 l0,5.2
                         M70,109 l0,5 M82,107 l0,4.6"
                      stroke="{_LOUNGER_TRIM}" stroke-width="1.1" stroke-linecap="round" opacity="0.75"/>
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
