# coin_flip_app_streamlit.py
import random
import streamlit as st

# ========= Live viewport + orientation (auto-rerun on rotate) =========
def get_viewport_live():
    """Returns (width, height). Uses a JS resize listener to trigger reruns."""
    try:
        from streamlit_javascript import st_javascript  # lazy import
        js = """
        // return current size immediately
        const w = window.innerWidth, h = window.innerHeight;

        // install a one-time resize listener that pushes width back to Streamlit
        if (!window._st_resize_installed) {
          window._st_resize_installed = true;
          window.addEventListener('resize', () => {
            const w2 = window.innerWidth;
            window.parent.postMessage(
              { isStreamlitMessage: true,
                type: 'streamlit:setComponentValue',
                value: [w2, window.innerHeight] }, '*');
          });
        }
        return [w, h];
        """
        wh = st_javascript(js)
        if isinstance(wh, (list, tuple)) and len(wh) == 2:
            return int(wh[0]), int(wh[1])
    except Exception:
        pass
    # Fallback to query params (?w=390&h=844)
    qp = st.query_params
    w = int(qp.get("w", [0])[0]) if "w" in qp else 0
    h = int(qp.get("h", [0])[0]) if "h" in qp else 0
    return w, h

def flags_from_viewport():
    w, h = get_viewport_live()
    # Mobile if width < 800 (override with ?mobile=1 if desired)
    is_mobile = (w and w < 800) or st.query_params.get("mobile", ["0"])[0].lower() in ("1","true","yes")
    is_landscape = (w and h and w > h)
    return w, h, is_mobile, is_landscape

# ========= Core state & logic =========
class Stats:
    def __init__(self):
        self.total = 0; self.wins = 0; self.losses = 0
        self.longest = 0; self.current = 0
    def record(self, win: bool):
        self.total += 1
        if win:
            self.wins += 1; self.current += 1
            self.longest = max(self.longest, self.current)
        else:
            self.losses += 1; self.current = 0
    def win_rate(self):
        return (self.wins/self.total*100) if self.total else 0.0

if "thumb" not in st.session_state:
    st.session_state.update(thumb=0, okaun=0, zndr=0, base=3,
                            turn_wins=0, stats=Stats(), log=[])

def log(msg): st.session_state.log.append(msg)
def flip_coin(): return random.random() < 0.5
def flip_with_thumbs(n:int):
    trials = min(2**max(0,int(n)), 256)
    for _ in range(trials):
        if flip_coin(): return True
    return False
def do_flip():
    win = flip_with_thumbs(st.session_state.thumb) if st.session_state.thumb>0 else flip_coin()
    st.session_state.stats.record(win); return win
def sequence_until_lose():
    wins = 0
    while True:
        if do_flip(): wins += 1
        else: break
    st.session_state.turn_wins += wins
    return wins
def begin_combat():
    z_wins = [sequence_until_lose() for _ in range(st.session_state.zndr)]
    o_wins = [sequence_until_lose() for _ in range(st.session_state.okaun)]
    tw = st.session_state.turn_wins
    cards = st.session_state.zndr * tw
    power = (st.session_state.base * (2**tw)) if st.session_state.okaun>0 else None
    return z_wins, o_wins, tw, cards, power

# ========= Page + responsive style =========
st.set_page_config(page_title="Coin Flip Tracker", page_icon="🪙",
                   layout="wide", initial_sidebar_state="collapsed")
W, H, IS_MOBILE, IS_LANDSCAPE = flags_from_viewport()

if IS_MOBILE:
    # Global mobile styles; tighten padding
    st.markdown("""
    <style>
      [data-testid="stSidebar"]{display:none !important;}
      .block-container{padding:0.5rem 0.6rem !important; max-width:96vw !important;}
      button, input, select, textarea{font-size:20px !important;}
      .stMetric{font-size:18px !important;}
      [data-testid="stHeader"]{display:none;}
    </style>
    """, unsafe_allow_html=True)
    if IS_LANDSCAPE:
        # Slightly smaller text in landscape so 3 columns fit comfortably
        st.markdown("""
        <style>
          .stMetric label, .stMetric span, button { font-size:16px !important; }
          .block-container{padding:0.4rem 0.5rem !important;}
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown("<style>.block-container{max-width:1200px;}</style>", unsafe_allow_html=True)

st.title("🪙 Coin Flip Tracker — Okaun / Zndrsplt / Krark’s Thumb")
st.caption("Z cards = copies × wins this turn • Okaun power = base × 2^(wins this turn)")

def settings_block():
    st.session_state.thumb = st.number_input("Krark’s Thumb copies", 0, 8, st.session_state.thumb)
    st.session_state.okaun = st.number_input("Okaun copies", 0, 12, st.session_state.okaun)
    st.session_state.zndr  = st.number_input("Zndrsplt copies", 0, 12, st.session_state.zndr)
    st.session_state.base  = st.number_input("Okaun base power", 1, 99, st.session_state.base)

# ========= Layouts =========
if IS_MOBILE and not IS_LANDSCAPE:
    # ---- PORTRAIT: Tabs view (compact) ----
    with st.expander("Settings", expanded=False):
        settings_block()

    tabs = st.tabs(["⚡ Actions", "🎯 This Turn", "📊 Session"])
    with tabs[0]:
        c1, c2 = st.columns(2)
        if c1.button("Single Flip"):
            w = do_flip()
            if w: st.session_state.turn_wins += 1
            log(f"Single Flip → {'WIN' if w else 'LOSS'}")
        if c2.button("Begin Combat"):
            z_wins, o_wins, tw, cards, power = begin_combat()
            log("=== Begin Combat ===")
            if st.session_state.zndr>0: log(f"Z wins/copy: {z_wins} | Cards: {cards}")
            if st.session_state.okaun>0: log(f"O wins/copy: {o_wins} | Power(each): {power}")
            log(f"Total wins this turn: {tw}")
        c3, c4 = st.columns(2)
        if c3.button("New Turn"): st.session_state.turn_wins = 0; log("— New turn —")
        if c4.button("Reset"): st.session_state.stats = Stats(); st.session_state.turn_wins=0; st.session_state.log=[]; log("**Session reset**")
        m1, m2 = st.columns(2)
        if m1.button("Manual Win"): st.session_state.stats.record(True); st.session_state.turn_wins += 1; log("Manual → WIN")
        if m2.button("Manual Loss"): st.session_state.stats.record(False); log("Manual → LOSS")

    with tabs[1]:
        tw = st.session_state.turn_wins
        st.metric("Wins this turn", tw)
        st.metric("Zndrsplt cards (this turn)", st.session_state.zndr * tw)
        st.metric("Okaun power (each, this turn)", (st.session_state.base * (2**tw)) if st.session_state.okaun>0 else "-")

    with tabs[2]:
        S = st.session_state.stats
        st.metric("Total flips", S.total)
        st.metric("W / L", f"{S.wins} / {S.losses}")
        st.metric("Win rate", f"{S.win_rate():.1f}%")
        st.metric("Streak / Longest", f"{S.current} / {S.longest}")

else:
    # ---- LANDSCAPE (mobile) or DESKTOP: 3 columns ----
    if IS_MOBILE:
        with st.expander("Settings", expanded=False): settings_block()
    else:
        with st.sidebar:
            st.header("Battlefield / Settings")
            settings_block()
            if st.button("New Turn"): st.session_state.turn_wins = 0; log("— New turn —")
            if st.button("Reset Session"): st.session_state.stats = Stats(); st.session_state.turn_wins=0; st.session_state.log=[]; log("**Session reset**")

    a, b, c = st.columns(3, gap="large")

    with a:
        st.subheader("Actions")
        if st.button("Single Flip"):
            w = do_flip()
            if w: st.session_state.turn_wins += 1
            log(f"Single Flip → {'WIN' if w else 'LOSS'}")
        col = st.columns(2)
        if col[0].button("Manual Win"): st.session_state.stats.record(True); st.session_state.turn_wins += 1; log("Manual → WIN")
        if col[1].button("Manual Loss"): st.session_state.stats.record(False); log("Manual → LOSS")
        if st.button("Begin Combat"):
            z_wins, o_wins, tw, cards, power = begin_combat()
            log("=== Begin Combat ===")
            if st.session_state.zndr>0: log(f"Z wins/copy: {z_wins} | Cards: {cards}")
            if st.session_state.okaun>0: log(f"O wins/copy: {o_wins} | Power(each): {power}")
            log(f"Total wins this turn: {tw}")

    with b:
        st.subheader("This Turn")
        tw = st.session_state.turn_wins
        st.metric("Wins this turn", tw)
        st.metric("Zndrsplt cards (this turn)", st.session_state.zndr * tw)
        st.metric("Okaun power (this turn)", (st.session_state.base * (2**tw)) if st.session_state.okaun>0 else "-")

    with c:
        st.subheader("Session Stats")
        S = st.session_state.stats
        st.metric("Total flips", S.total)
        st.metric("W / L", f"{S.wins} / {S.losses}")
        st.metric("Win rate", f"{S.win_rate():.1f}%")
        st.metric("Streak / Longest", f"{S.current} / {S.longest}")

# ---- Log ----
st.divider()
st.subheader("Log")
st.write("\n".join(st.session_state.log[-200:]) or "_(empty)_")

