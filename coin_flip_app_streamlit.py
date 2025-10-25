# coin_flip_app_streamlit.py
import random
import streamlit as st

# ----------------- responsive detection -----------------
def detect_is_mobile(default=False) -> bool:
    """True if viewport width < 800px. Falls back to query param ?mobile=1."""
    try:
        from streamlit_javascript import st_javascript  # lazy import
        width = st_javascript("window.innerWidth")
        if isinstance(width, (int, float)) and width > 0:
            return width < 800
    except Exception:
        pass
    # Fallback: query param ?mobile=1
    qp = st.query_params
    if "mobile" in qp:
        v = str(qp.get("mobile")).strip("[]' ")
        return v.lower() in ("1", "true", "yes")
    return default

# ----------------- core state & logic -----------------
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
    st.session_state.update(
        thumb=0, okaun=0, zndr=0, base=3,
        turn_wins=0, stats=Stats(), log=[]
    )

def log(msg: str): st.session_state.log.append(msg)

def flip_coin(): return random.random() < 0.5

def flip_with_thumbs(n: int):
    trials = min(2**max(0, int(n)), 256)  # safety cap
    for _ in range(trials):
        if flip_coin(): return True
    return False

def do_flip():
    win = flip_with_thumbs(st.session_state.thumb) if st.session_state.thumb>0 else flip_coin()
    st.session_state.stats.record(win)
    return win

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

# ----------------- page setup -----------------
st.set_page_config(
    page_title="Coin Flip Tracker",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="collapsed",
)
IS_MOBILE = detect_is_mobile(default=False)

# global styles
if IS_MOBILE:
    st.markdown("""
    <style>
      [data-testid="stSidebar"]{display:none !important;}
      .block-container{padding:0.6rem 0.7rem !important; max-width:96vw !important;}
      button, input, select, textarea{font-size:20px !important;}
      .stMetric{font-size:18px !important;}
      [data-testid="stHeader"]{display:none;} /* more vertical space */
      /* sticky toolbar container: first top block */
      .mobile-toolbar{position:sticky; top:0; z-index:999; background:#0e1117; padding:8px 4px; border-bottom:1px solid #2d3748;}
      @media (prefers-color-scheme: light){
        .mobile-toolbar{background:#ffffff; border-bottom:1px solid #e2e8f0;}
      }
      .toolbar-row > div{padding:0 4px;}
      .stButton>button{width:100%; height:48px;}
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>.block-container{max-width:1200px;}</style>
    """, unsafe_allow_html=True)

st.title("🪙 Coin Flip Tracker — Okaun / Zndrsplt / Krark’s Thumb")
st.caption("Z cards = copies × wins this turn • Okaun power = base × 2^(wins this turn)")

# ----------------- SETTINGS -----------------
if IS_MOBILE:
    with st.expander("Settings", expanded=False):
        st.session_state.thumb = st.number_input("Krark’s Thumb copies", 0, 8, st.session_state.thumb)
        st.session_state.okaun = st.number_input("Okaun copies", 0, 12, st.session_state.okaun)
        st.session_state.zndr  = st.number_input("Zndrsplt copies", 0, 12, st.session_state.zndr)
        st.session_state.base  = st.number_input("Okaun base power", 1, 99, st.session_state.base)
else:
    with st.sidebar:
        st.header("Battlefield / Settings")
        st.session_state.thumb = st.number_input("Krark’s Thumb copies", 0, 8, st.session_state.thumb)
        st.session_state.okaun = st.number_input("Okaun copies", 0, 12, st.session_state.okaun)
        st.session_state.zndr  = st.number_input("Zndrsplt copies", 0, 12, st.session_state.zndr)
        st.session_state.base  = st.number_input("Okaun base power", 1, 99, st.session_state.base)
        if st.button("New Turn"): st.session_state.turn_wins = 0; log("— New turn —")
        if st.button("Reset Session"): st.session_state.stats = Stats(); st.session_state.turn_wins=0; st.session_state.log=[]; log("**Session reset**")

# ----------------- MOBILE STICKY TOOLBAR -----------------
if IS_MOBILE:
    toolbar = st.container()
    with toolbar:
        st.markdown('<div class="mobile-toolbar">', unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4, gap="small")
        with c1:
            if st.button("Single Flip"):
                w = do_flip()
                if w: st.session_state.turn_wins += 1
                log(f"Single Flip → {'WIN' if w else 'LOSS'}")
        with c2:
            if st.button("Begin Combat"):
                z_wins, o_wins, tw, cards, power = begin_combat()
                log("=== Begin Combat ===")
                if st.session_state.zndr>0: log(f"Z wins/copy: {z_wins} | Cards: {cards}")
                if st.session_state.okaun>0: log(f"O wins/copy: {o_wins} | Power(each): {power}")
                log(f"Total wins this turn: {tw}")
        with c3:
            if st.button("New Turn"):
                st.session_state.turn_wins = 0; log("— New turn —")
        with c4:
            if st.button("Reset"):
                st.session_state.stats = Stats(); st.session_state.turn_wins=0; st.session_state.log=[]; log("**Session reset**")
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MAIN COLUMNS -----------------
if IS_MOBILE:
    a = st.container(); b = st.container(); c = st.container()
else:
    a,b,c = st.columns(3, gap="large")

with a:
    st.subheader("Actions")
    if not IS_MOBILE:
        # desktop buttons (mobile uses toolbar)
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
    else:
        # mobile manual buttons (kept here for completeness)
        col = st.columns(2)
        if col[0].button("Manual Win"): st.session_state.stats.record(True); st.session_state.turn_wins += 1; log("Manual → WIN")
        if col[1].button("Manual Loss"): st.session_state.stats.record(False); log("Manual → LOSS")

with b:
    st.subheader("This Turn")
    tw = st.session_state.turn_wins
    st.metric("Wins this turn", tw)
    st.metric("Zndrsplt cards (this turn)", st.session_state.zndr * tw)
    st.metric("Okaun power (each, this turn)", (st.session_state.base * (2**tw)) if st.session_state.okaun>0 else "-")

with c:
    st.subheader("Session Stats")
    S = st.session_state.stats
    st.metric("Total flips", S.total)
    st.metric("W / L", f"{S.wins} / {S.losses}")
    st.metric("Win rate", f"{S.win_rate():.1f}%")
    st.metric("Streak / Longest", f"{S.current} / {S.longest}")

st.divider()
st.subheader("Log")
st.write("\n".join(st.session_state.log[-200:]) or "_(empty)_")
