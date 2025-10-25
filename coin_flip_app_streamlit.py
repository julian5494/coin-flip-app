# coin_flip_app_streamlit.py
import random
import streamlit as st

st.markdown("""
<style>
html, body, [class*="css"]  {
    font-size: 18px !important;
}
[data-testid="stHeader"] {display: none;}
.block-container {
    max-width: 95vw;
}
</style>
""", unsafe_allow_html=True)

# --- simple in-page state ---
class Stats:
    def __init__(self): self.total=0; self.wins=0; self.losses=0; self.longest=0; self.current=0
    def record(self, win):
        self.total += 1
        if win:
            self.wins += 1; self.current += 1; self.longest = max(self.longest, self.current)
        else:
            self.losses += 1; self.current = 0
    def win_rate(self): return (self.wins/self.total*100) if self.total else 0.0

if "thumb" not in st.session_state:
    st.session_state.update(thumb=0, okaun=0, zndr=0, base=3, turn_wins=0, stats=Stats(), log=[])

st.set_page_config(page_title="Coin Flip Tracker", page_icon="🪙", layout="wide")

# Detect if screen is narrow (like a phone)
is_mobile = st.experimental_get_query_params().get("mobile", ["0"])[0] == "1"

if is_mobile:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {display: none;}
        .block-container {padding-top: 0.5rem; padding-left: 0.5rem; padding-right: 0.5rem;}
        button, input, select {font-size: 20px !important;}
        </style>
    """, unsafe_allow_html=True)


def flip_coin(): return random.random() < 0.5

def flip_with_thumbs(n):
    trials = min(2**max(0,int(n)), 256)
    for _ in range(trials):
        if flip_coin(): return True
    return False

def do_flip():
    win = flip_with_thumbs(st.session_state.thumb) if st.session_state.thumb>0 else flip_coin()
    st.session_state.stats.record(win); 
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

def log(msg): st.session_state.log.append(msg)

st.set_page_config(page_title="Coin Flip Tracker", page_icon="🪙", layout="wide")
st.title("🪙 Coin Flip Tracker — Okaun / Zndrsplt / Krark’s Thumb")

with st.sidebar:
    st.header("Battlefield / Settings")
    st.session_state.thumb = st.number_input("Krark’s Thumb copies", 0, 8, st.session_state.thumb)
    st.session_state.okaun = st.number_input("Okaun copies", 0, 12, st.session_state.okaun)
    st.session_state.zndr  = st.number_input("Zndrsplt copies", 0, 12, st.session_state.zndr)
    st.session_state.base  = st.number_input("Okaun base power", 1, 99, st.session_state.base)

    col = st.columns(2)
    if col[0].button("New Turn"): st.session_state.turn_wins = 0; log("— New turn —")
    if col[1].button("Reset Session"): st.session_state.stats = Stats(); st.session_state.turn_wins=0; st.session_state.log=[]; log("**Session reset**")

if is_mobile:
    # Stack vertically on phones
    a = st.container()
    b = st.container()
    c = st.container()
else:
    # Three columns on desktop
    a, b, c = st.columns(3)

with a:
    st.subheader("Actions")
    if st.button("Single Flip"):
        win = do_flip()
        if win: st.session_state.turn_wins += 1
        log(f"Single Flip → {'WIN' if win else 'LOSS'}")
    c1,c2 = st.columns(2)
    if c1.button("Manual Win"): st.session_state.stats.record(True); st.session_state.turn_wins += 1; log("Manual → WIN")
    if c2.button("Manual Loss"): st.session_state.stats.record(False); log("Manual → LOSS")
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
