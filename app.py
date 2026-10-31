


"""Mati-Marga: gravity-filtration + freight-scheduling prototype for Pen, Raigad.
Run:  pip install streamlit plotly pandas numpy google-genai
      streamlit run app.py
Numbers marked 'model' are illustrative simulations calibrated to the field data in the project blueprint."""
import json, os, re, urllib.request
from datetime import datetime, timedelta
from urllib.parse import quote

import numpy as np
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Mati-Marga | Pen", page_icon="🪔", layout="wide")

# ---------- palette ----------
INK, RIVER, PLASTER, MARIGOLD, SILT, ALERT = "#070B1F", "#22D3EE", "#EAF0FF", "#B6F500", "#94A3D6", "#FF4D6D"
PANEL = "#121A3F"


# ---------- persistent JSON storage ----------
# Local JSON persistence. Streamlit Cloud local files can reset on redeploy/restart.
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mati_marga_data.json")

def load_app_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        pass
    return {}

def save_app_data():
    data = {
        "bookings": st.session_state.bookings.to_dict(orient="records") if "bookings" in st.session_state else [],
        "cleaned": {name: value.isoformat() if hasattr(value, "isoformat") else str(value)
                    for name, value in st.session_state.cleaned.items()} if "cleaned" in st.session_state else {},
        "tickets": st.session_state.tickets.assign(Time=st.session_state.tickets["Time"].astype(str)).to_dict(orient="records")
                   if "tickets" in st.session_state else []
    }
    temp_file = DATA_FILE + ".tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        os.replace(temp_file, DATA_FILE)
    except OSError as exc:
        st.warning(f"Could not save data to JSON: {exc}")

if "_mati_marga_db" not in st.session_state:
    st.session_state._mati_marga_db = load_app_data()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@500;700;800&family=Hind:wght@400;500;600&display=swap');
:root{--ink:#070B1F;--panel:#121A3F;--field:#0E1536;--river:#22D3EE;--plaster:#EAF0FF;--gold:#B6F500;--silt:#94A3D6;--alert:#FF4D6D;--line:rgba(255,255,255,.14);}
html,body,[class*="css"],.stMarkdown,p,label,li,span,div{font-family:'Hind',sans-serif;}
h1,h2,h3,h4{font-family:'Bricolage Grotesque',sans-serif !important;letter-spacing:-.02em;color:var(--plaster) !important;}
.stApp{background:radial-gradient(900px 500px at 90% -5%,rgba(34,211,238,.28),transparent),radial-gradient(700px 500px at -5% 40%,rgba(182,245,0,.10),transparent),var(--ink);}
.stApp p,.stApp span,.stApp label,.stApp li,.stApp small,.stApp [data-testid="stMarkdownContainer"],.stApp [data-testid="stWidgetLabel"] p,.stApp [data-testid="stCaptionContainer"]{color:var(--plaster);}
.stApp [data-testid="stCaptionContainer"],.note{color:#9AA7D6 !important;}
header[data-testid="stHeader"]{background:transparent;}
.block-container{padding-top:2rem;max-width:1250px;}
section[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none !important;}
/* ---- every input, always readable ---- */
input,textarea,[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="textarea"],[data-baseweb="select"]>div{background:var(--field) !important;color:var(--plaster) !important;-webkit-text-fill-color:var(--plaster) !important;border-color:var(--line) !important;border-radius:10px !important;}
input::placeholder,textarea::placeholder{color:#8A97C8 !important;-webkit-text-fill-color:#8A97C8 !important;}
[data-baseweb="select"] *{color:var(--plaster) !important;fill:var(--plaster) !important;}
[data-baseweb="popover"],[data-baseweb="popover"]>div,[data-baseweb="menu"],ul[role="listbox"]{background:var(--field) !important;color:var(--plaster) !important;}
li[role="option"],li[role="option"] *{color:var(--plaster) !important;background:transparent !important;}
li[role="option"]:hover,li[aria-selected="true"]{background:#3B2F9E !important;}
[data-testid="stNumberInput"] button{background:var(--panel) !important;color:var(--plaster) !important;}
[data-testid="stNumberInput"] button svg,input+div svg,[data-testid="stSidebar"] svg{fill:var(--plaster) !important;color:var(--plaster) !important;}
[data-testid="stSliderThumbValue"],[data-testid="stTickBarMin"],[data-testid="stTickBarMax"]{color:var(--gold) !important;}
[data-testid="stRadio"] label,[data-testid="stRadio"] p,[data-testid="stToggle"] p{color:var(--plaster) !important;}
[data-testid="stAlert"]{background:rgba(34,211,238,.16) !important;border:1px solid var(--line);border-radius:12px;}
[data-testid="stAlert"] *{color:var(--plaster) !important;}
[data-testid="stToast"],[data-testid="stToast"] *{background:var(--panel);color:var(--plaster) !important;}
[data-testid="stForm"]{background:rgba(18,26,63,.55);border:1px solid var(--line);border-radius:16px;box-shadow:0 14px 30px -12px #000b, inset 0 1px 0 rgba(255,255,255,.12);}
/* ---- 3D buttons ---- */
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button,[data-testid="stLinkButton"] a{background:linear-gradient(180deg,#D4FF4D,#B6F500) !important;color:#0B1230 !important;font-weight:700;border:0 !important;border-radius:12px;box-shadow:0 5px 0 #6D9400,0 12px 18px -6px #000a;transition:transform .12s,box-shadow .12s;}
.stButton>button *,.stFormSubmitButton>button *,.stDownloadButton>button *,[data-testid="stLinkButton"] a *{color:#0B1230 !important;}
.stButton>button:hover,.stFormSubmitButton>button:hover,[data-testid="stLinkButton"] a:hover{transform:translateY(-2px);box-shadow:0 7px 0 #6D9400,0 16px 22px -6px #000a;}
.stButton>button:active,.stFormSubmitButton>button:active{transform:translateY(5px);box-shadow:0 0 0 #6D9400;}
/* ---- hero with 3D filter stack ---- */
.hero{display:flex;justify-content:space-between;align-items:center;gap:1rem;padding:2.2rem 2.4rem;border-radius:24px;border:1px solid var(--line);background:linear-gradient(135deg,#1E2A6E 0%,#0B1130 65%);box-shadow:0 30px 60px -25px #000,inset 0 1px 0 rgba(255,255,255,.18);overflow:hidden;}
.hero h1{font-size:3.5rem;margin:0;line-height:1;font-weight:800;background:linear-gradient(90deg,#EAF0FF 35%,#B6F500);-webkit-background-clip:text;background-clip:text;color:transparent !important;}
.hero .dev{color:var(--gold);font-weight:600;font-size:1.3rem;margin-bottom:.4rem;}
.hero p{max-width:560px;color:#C9D2F2;font-size:1.06rem;margin:.9rem 0 1.1rem;}
.scene{perspective:900px;width:320px;height:270px;flex:none;}
.stack{position:relative;width:100%;height:100%;transform-style:preserve-3d;transform:rotateX(62deg) rotateZ(-35deg);animation:bob 8s ease-in-out infinite;}
.slab{position:absolute;left:70px;top:50px;width:170px;height:170px;border-radius:16px;box-shadow:0 0 0 2px rgba(255,255,255,.18) inset,0 30px 40px -10px #0008;transition:transform .5s;}
.s1{background:linear-gradient(135deg,#B4C0EA,#7F8FD0);transform:translateZ(150px);}
.s2{background:linear-gradient(135deg,#9F86FF,#5B3FD6);transform:translateZ(100px);}
.s3{background:linear-gradient(135deg,#E1FF8A,#8FC400);transform:translateZ(50px);}
.s4{background:linear-gradient(135deg,#7BE9FA,#0FA3BF);transform:translateZ(0);}
.scene:hover .s1{transform:translateZ(210px);}.scene:hover .s2{transform:translateZ(130px);}.scene:hover .s3{transform:translateZ(65px);}
@keyframes bob{0%,100%{transform:rotateX(62deg) rotateZ(-35deg) translateZ(0);}50%{transform:rotateX(58deg) rotateZ(-22deg) translateZ(14px);}}
.strata-cap{font-size:.84rem;color:#9AA7D6;}
@media (max-width:800px){.scene{display:none;}.hero h1{font-size:2.4rem;}}
/* ---- 3D cards ---- */
.kpi,.task,.stage,.card{background:linear-gradient(160deg,rgba(24,34,92,.92),rgba(10,16,48,.92));border:1px solid var(--line);border-radius:16px;padding:1rem 1.2rem;height:100%;box-shadow:0 16px 30px -14px #000,inset 0 1px 0 rgba(255,255,255,.14);transition:transform .25s,box-shadow .25s;transform-style:preserve-3d;}
.kpi:hover,.task:hover,.stage:hover{transform:perspective(900px) rotateX(4deg) rotateY(-4deg) translateY(-6px);box-shadow:0 28px 40px -16px #000;}
.kpi .l{color:#9AA7D6;font-size:.88rem;}.kpi .v{font-family:'Bricolage Grotesque';font-size:2.1rem;font-weight:700;color:var(--plaster);line-height:1.15;}
.kpi .s{font-size:.85rem;color:#7BE9FA;}.kpi .s.bad{color:#FF9DB0;}
.stage{border-left:4px solid var(--gold);margin-bottom:.8rem;height:auto;}.stage b{font-family:'Bricolage Grotesque';font-size:1.05rem;color:var(--plaster);}.stage span{color:#B8C2EA;font-size:.92rem;}
.task h4{margin:.1rem 0 .4rem;font-size:1.05rem;}.task p{color:#B8C2EA;font-size:.92rem;margin:.5rem 0 0;}
.chip{display:inline-block;padding:.25rem .8rem;border-radius:999px;font-weight:600;font-size:.85rem;}
.chip.ok{background:rgba(34,211,238,.28);color:#9AF0FF;}.chip.warn{background:rgba(182,245,0,.28);color:#E1FF8A;}.chip.bad{background:rgba(255,77,109,.3);color:#FF9DB0;}
.note{font-size:.84rem;}
/* ---- tables ---- */
.tbl{overflow-x:auto;border:1px solid var(--line);border-radius:14px;background:rgba(14,21,54,.8);}
.tbl table{width:100%;border-collapse:collapse;}.tbl th{background:#2B3680;color:var(--gold);text-align:left;padding:.55rem .8rem;font-weight:600;}
.tbl td{color:var(--plaster);padding:.5rem .8rem;border-top:1px solid var(--line);}
.flipc{perspective:900px;height:128px;margin-bottom:.9rem;}
.flipi{position:relative;width:100%;height:100%;transition:transform .7s cubic-bezier(.2,.8,.2,1);transform-style:preserve-3d;}
.flipc:hover .flipi{transform:rotateY(180deg);}
.face{position:absolute;inset:0;backface-visibility:hidden;-webkit-backface-visibility:hidden;border-radius:16px;padding:1rem 1.4rem;display:flex;flex-direction:column;justify-content:center;border:1px solid var(--line);box-shadow:0 18px 30px -14px #000;}
.face.front{background:linear-gradient(160deg,rgba(24,34,92,.95),rgba(10,16,48,.95));}
.face.back{transform:rotateY(180deg);background:linear-gradient(160deg,#D4FF4D,#8FC400);}
.face.back,.face.back *{color:#0B1230 !important;}
.face b{font-family:'Bricolage Grotesque';font-size:1.2rem;}.face span{font-size:.95rem;}
/* ---- tabs ---- */
.stTabs [data-baseweb="tab-list"]{gap:.3rem;border-bottom:1px solid var(--line);flex-wrap:wrap;}
.stTabs [data-baseweb="tab"]{border-radius:12px 12px 0 0;padding:.6rem 1rem;color:#B8C2EA !important;}
.stTabs [aria-selected="true"]{color:var(--gold) !important;background:rgba(182,245,0,.1);}
@media (prefers-reduced-motion:reduce){.stack{animation:none;}.kpi,.task,.stage{transition:none;}}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>
:root{--violet:#7C5CFF;--cyan:#22D3EE;--lime:#B6F500;--pink:#FF4D6D;}
.stApp{isolation:isolate;}
.stApp::before{content:"";position:fixed;inset:-20%;z-index:-1;pointer-events:none;filter:blur(30px);
 background:radial-gradient(40% 40% at 15% 20%,rgba(124,92,255,.42),transparent 60%),radial-gradient(35% 35% at 85% 12%,rgba(34,211,238,.28),transparent 60%),radial-gradient(40% 40% at 70% 92%,rgba(255,77,109,.18),transparent 60%);
 animation:aurora 22s ease-in-out infinite alternate;}
@keyframes aurora{to{transform:translate3d(4%,3%,0) scale(1.08) rotate(3deg);}}
.stApp::after{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;opacity:.35;
 background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);background-size:46px 46px;
 -webkit-mask-image:radial-gradient(ellipse at center,#000 30%,transparent 75%);mask-image:radial-gradient(ellipse at center,#000 30%,transparent 75%);}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a1030,#050818);border-right:1px solid rgba(124,92,255,.35);}
h2,h3{background:linear-gradient(90deg,#EAF0FF,#7BE9FA);-webkit-background-clip:text;background-clip:text;color:transparent !important;}
h4{border-left:4px solid var(--lime);padding-left:.6rem;}
.hero{background:radial-gradient(600px 300px at 92% 8%,rgba(124,92,255,.55),transparent 70%),radial-gradient(500px 320px at 0% 100%,rgba(34,211,238,.25),transparent 70%),linear-gradient(135deg,#131c4a,#0a1030);
 border:1px solid rgba(124,92,255,.55);box-shadow:0 0 70px -12px rgba(124,92,255,.5),0 30px 60px -25px #000,inset 0 1px 0 rgba(255,255,255,.2);}
.hero h1{background:linear-gradient(90deg,#EAF0FF 0%,#7BE9FA 50%,#B6F500 100%);-webkit-background-clip:text;background-clip:text;color:transparent !important;}
.badge{display:inline-block;padding:.28rem .8rem;border-radius:999px;border:1px solid rgba(182,245,0,.55);color:#B6F500;font-size:.74rem;letter-spacing:.09em;font-weight:700;margin:0 .4rem .5rem 0;background:rgba(182,245,0,.08);}
.badge.v{border-color:rgba(124,92,255,.7);color:#b9a8ff;background:rgba(124,92,255,.12);}
.kpi,.task,.card{background:linear-gradient(160deg,#141d52,#0b1236) padding-box,linear-gradient(135deg,rgba(124,92,255,.9),rgba(34,211,238,.55),rgba(182,245,0,.45)) border-box;border:1px solid transparent;}
.kpi .v{background:linear-gradient(90deg,#EAF0FF,#7BE9FA);-webkit-background-clip:text;background-clip:text;color:transparent;}
.kpi:hover,.task:hover,.card:hover{box-shadow:0 0 0 1px rgba(124,92,255,.7),0 26px 50px -14px rgba(124,92,255,.6);}
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button,[data-testid="stLinkButton"] a{background:linear-gradient(180deg,#d4ff4d,#B6F500) !important;box-shadow:0 5px 0 #6d9400,0 0 26px rgba(182,245,0,.35);}
.stButton>button:hover,.stFormSubmitButton>button:hover,[data-testid="stLinkButton"] a:hover{box-shadow:0 7px 0 #6d9400,0 0 36px rgba(182,245,0,.55);}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none;}
.stTabs [data-baseweb="tab-list"]{gap:.45rem;border:0;padding:.3rem 0 .8rem;}
.stTabs [data-baseweb="tab"]{border-radius:999px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.04);padding:.45rem 1.05rem;}
.stTabs [aria-selected="true"]{background:linear-gradient(90deg,#7C5CFF,#22D3EE) !important;border-color:transparent;box-shadow:0 0 24px -2px rgba(124,92,255,.7);}
.stTabs [aria-selected="true"] *{color:#070B1F !important;font-weight:700;}
.stForm,[data-testid="stForm"]{border:1px solid rgba(124,92,255,.4);}
.tbl th{background:linear-gradient(90deg,#2b3680,#3b2f9e);}
.ticker{overflow:hidden;white-space:nowrap;border:1px solid rgba(255,255,255,.14);border-radius:999px;background:rgba(255,255,255,.04);padding:.55rem 0;margin:1.1rem 0 .4rem;}
.ticker div{display:inline-block;padding-left:100%;animation:tick 42s linear infinite;}
.ticker span{margin:0 1.7rem;color:#B8C2EA;font-weight:600;}.ticker b{color:#B6F500;}
@keyframes tick{to{transform:translateX(-100%);}}
.step{font-family:'Bricolage Grotesque';font-size:2.6rem;font-weight:800;line-height:1;background:linear-gradient(90deg,#7C5CFF,#22D3EE);-webkit-background-clip:text;background-clip:text;color:transparent;}
.card h4{border:0;padding:0;margin:.2rem 0 .3rem;}.card p{color:#B8C2EA;font-size:.93rem;margin:0;}
@media (prefers-reduced-motion:reduce){.stApp::before,.ticker div{animation:none;}}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>
[data-testid="stToolbar"],[data-testid="stDecoration"],footer,#MainMenu{display:none !important;}
::selection{background:#7C5CFF;color:#fff;}
::-webkit-scrollbar{width:10px;height:10px;}::-webkit-scrollbar-thumb{background:linear-gradient(#7C5CFF,#22D3EE);border-radius:9px;}::-webkit-scrollbar-track{background:#070B1F;}
/* inputs: one clean dark box, no white corners */
[data-baseweb="input"],[data-baseweb="textarea"]{background:#0E1536 !important;border:1px solid rgba(255,255,255,.18) !important;border-radius:12px !important;overflow:hidden;}
[data-baseweb="input"] *,[data-baseweb="textarea"] *{background:transparent !important;border:0 !important;box-shadow:none !important;}
[data-baseweb="input"]:focus-within,[data-baseweb="textarea"]:focus-within{border-color:#7C5CFF !important;box-shadow:0 0 0 3px rgba(124,92,255,.3) !important;}
[data-baseweb="select"]>div{border:1px solid rgba(255,255,255,.18) !important;border-radius:12px !important;}
/* top nav + sidebar brand */
.topnav{display:flex;justify-content:space-between;align-items:center;margin:-.4rem 0 1rem;}
.brand,.sbrand{font-family:'Bricolage Grotesque';font-weight:800;font-size:1.35rem;display:flex;align-items:center;gap:.6rem;color:#EAF0FF;}
.brand small,.sbrand small{font-family:'Hind';font-weight:500;font-size:.78rem;color:#9AA7D6;margin-left:.4rem;}
.sbrand small{margin:0;}.sbrand b{font-size:1.25rem;}
.logo{display:inline-grid;place-items:center;width:2.3rem;height:2.3rem;border-radius:12px;background:linear-gradient(135deg,#7C5CFF,#22D3EE);box-shadow:0 0 22px rgba(124,92,255,.6);font-size:1.15rem;}
.pill{display:flex;align-items:center;gap:.5rem;padding:.4rem .9rem;border-radius:999px;border:1px solid rgba(182,245,0,.45);background:rgba(182,245,0,.08);color:#B6F500;font-size:.74rem;font-weight:700;letter-spacing:.08em;}
.pill i{width:8px;height:8px;border-radius:50%;background:#B6F500;box-shadow:0 0 0 0 rgba(182,245,0,.7);animation:pulse 1.8s infinite;}
@keyframes pulse{70%{box-shadow:0 0 0 10px rgba(182,245,0,0);}100%{box-shadow:0 0 0 0 rgba(182,245,0,0);}}
/* sticky glass tab bar */
.stTabs [data-baseweb="tab-list"]{position:sticky;top:0;z-index:20;background:rgba(7,11,31,.78);backdrop-filter:blur(14px);border-bottom:1px solid rgba(255,255,255,.08);}
/* spotlight on cards */
.kpi,.task,.card,.stage{position:relative;overflow:hidden;}
.kpi::after,.task::after,.card::after,.stage::after{content:"";position:absolute;inset:0;border-radius:inherit;pointer-events:none;opacity:0;transition:opacity .3s;background:radial-gradient(240px circle at var(--mx,50%) var(--my,50%),rgba(124,92,255,.3),transparent 65%);}
.kpi:hover::after,.task:hover::after,.card:hover::after,.stage:hover::after{opacity:1;}
@media (prefers-reduced-motion:reduce){.pill i{animation:none;}}
</style>
""", unsafe_allow_html=True)


_NEW = tuple(int(x) for x in st.__version__.split(".")[:2] if x.isdigit()) >= (1, 50)


def plot(fig):
    if _NEW: st.plotly_chart(fig, width="stretch")
    else: st.plotly_chart(fig, use_container_width=True)


def table(df):
    st.markdown('<div class="tbl">' + df.to_html(index=False, border=0).replace("\n", "") + "</div>", unsafe_allow_html=True)


MAPTRACE = getattr(go, "Scattermap", None) or go.Scattermapbox
MAPKEY = "map" if hasattr(go, "Scattermap") else "mapbox"


# =====================================================================
# 3D SCENES (Three.js).
# Each scene keeps a mutable width W and a fit() function called by a ResizeObserver,
# because Streamlit renders hidden tabs with width 0.
# The street simulator speed rule is relative to a safe gap, so an empty road gives 100% flow.
# =====================================================================
TRAP3D = """
<div id="w" style="position:relative;height:440px;background:radial-gradient(circle at 50% 25%,#2A2F8F,#070B1F 70%);border-radius:18px;overflow:hidden;font-family:Helvetica,Arial,sans-serif;border:1px solid rgba(255,255,255,.14)">
<div id="hud" style="position:absolute;left:14px;top:12px;color:#EAF0FF;font-size:14px;line-height:1.6;pointer-events:none"></div>
<div style="position:absolute;right:12px;top:12px;display:flex;gap:6px;z-index:5">
<button class="b" id="bx">Explode</button><button class="b" id="bs">Rain surge</button><button class="b" id="bp">Pause</button></div>
<div style="position:absolute;left:14px;bottom:10px;color:#9AA7D6;font-size:12px;pointer-events:none">Drag to rotate · scroll to zoom</div>
</div>
<style>.b{background:#B6F500;color:#0B1230;border:0;border-radius:9px;padding:7px 11px;font-weight:700;cursor:pointer;box-shadow:0 3px 0 #6D9400}.b:active{transform:translateY(3px);box-shadow:none}body{margin:0}</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const E=__EFFS__, w=document.getElementById('w'), H=440; let W=Math.max(w.clientWidth,320);
const sc=new THREE.Scene(), cam=new THREE.PerspectiveCamera(45,W/H,.1,100); cam.position.set(0,.8,14);
const rd=new THREE.WebGLRenderer({antialias:true,alpha:true}); rd.setSize(W,H); rd.setPixelRatio(window.devicePixelRatio); w.appendChild(rd.domElement); rd.domElement.style.display='block';
const fit=()=>{W=Math.max(w.clientWidth,320);rd.setSize(W,H);cam.aspect=W/H;cam.updateProjectionMatrix();};
new ResizeObserver(fit).observe(w); fit();
sc.add(new THREE.AmbientLight(0xffffff,.75)); const dl=new THREE.DirectionalLight(0xffffff,.9); dl.position.set(5,8,6); sc.add(dl);
const g=new THREE.Group(); sc.add(g); g.rotation.x=.4; g.rotation.y=-.6;
const TC=[0x94A3D6,0x7C5CFF,0xB6F500], TY=[2.2,0,-2.2], NM=['Coarse mesh','Gravel bed','Coir sheet'], CY=[...TY], tiers=[];
TY.forEach((y,i)=>{const m=new THREE.Mesh(new THREE.BoxGeometry(4,.5,4),new THREE.MeshStandardMaterial({color:TC[i],transparent:true,opacity:.8,wireframe:i==0}));
 m.add(new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry),new THREE.LineBasicMaterial({color:0xffffff}))); g.add(m); tiers.push(m);});
const wall=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(4.2,9.6,4.2)),new THREE.LineBasicMaterial({color:0x7BE9FA,transparent:true,opacity:.5})); g.add(wall);
const pool=new THREE.Mesh(new THREE.BoxGeometry(4,.8,4),new THREE.MeshStandardMaterial({color:0x22D3EE,transparent:true,opacity:.55})); pool.position.y=-4.3; g.add(pool);
const N=280, pos=new Float32Array(N*3), col=new Float32Array(N*3), P=[], geo=new THREE.BufferGeometry();
geo.setAttribute('position',new THREE.BufferAttribute(pos,3)); geo.setAttribute('color',new THREE.BufferAttribute(col,3));
g.add(new THREE.Points(geo,new THREE.PointsMaterial({size:.16,vertexColors:true})));
let st=[0,0,0,0],tot=0,surge=1,paused=false,ex=0,exT=0,drag=false,lx=0,ly=0;
const fate=()=>{for(let i=0;i<3;i++) if(Math.random()<E[i]) return i; return 3;};
function spawn(p,first){p.x=(Math.random()-.5)*3.4; p.z=(Math.random()-.5)*3.4; p.y=4.6+Math.random()*(first?10:3); p.v=.025+Math.random()*.02; p.f=fate(); p.h=0; p.c=false;}
for(let i=0;i<N;i++){const p={};spawn(p,true);P.push(p);}
const cc=[[.93,.95,.94],[.62,.69,.69],[.73,.59,.42],[.96,.66,.11],[.9,.33,.24]];
function frame(){
 if(!paused){
  ex+=(exT-ex)*.08; TY.forEach((y,i)=>{CY[i]=y*(1+.4*ex); tiers[i].position.y=CY[i];}); pool.position.y=-4.3*(1+.4*ex);
  P.forEach((p,i)=>{
   if(p.h>0){p.h--; if(p.h==0) spawn(p,false);}
   else{p.y-=p.v*surge; const t=p.f<3?CY[p.f]+.35:pool.position.y+.1;
    if(p.y<=t){p.y=t;p.h=100;if(!p.c){st[p.f]++;tot++;p.c=true;}}}
   pos.set([p.x,p.y,p.z],i*3);
   const c=p.h>0?(p.f<3?cc[p.f+1]:cc[4]):cc[0]; col.set(c,i*3);});
  geo.attributes.position.needsUpdate=true; geo.attributes.color.needsUpdate=true;
  if(!drag) g.rotation.y+=.0025;
  if(tot>1500){st=st.map(v=>v/2);tot/=2;}
 }
 rd.render(sc,cam); requestAnimationFrame(frame);
}
setInterval(()=>{const c=tot?100*(st[0]+st[1]+st[2])/tot:0;
 document.getElementById('hud').innerHTML='<b style="font-size:20px">'+c.toFixed(0)+'% trapped</b><br>'+NM.map((n,i)=>n+': '+st[i]).join('<br>')+'<br><span style="color:#FF9DB0">Discharged: '+st[3]+'</span>';},300);
const el=rd.domElement; el.style.touchAction='none';
el.addEventListener('pointerdown',e=>{drag=true;lx=e.clientX;ly=e.clientY;});
addEventListener('pointerup',()=>drag=false);
el.addEventListener('pointermove',e=>{if(!drag)return;g.rotation.y+=(e.clientX-lx)*.008;g.rotation.x=Math.max(-.2,Math.min(1.2,g.rotation.x+(e.clientY-ly)*.006));lx=e.clientX;ly=e.clientY;});
el.addEventListener('wheel',e=>{e.preventDefault();cam.position.z=Math.max(8,Math.min(22,cam.position.z+e.deltaY*.01));},{passive:false});
document.getElementById('bx').onclick=()=>exT=exT?0:1;
document.getElementById('bs').onclick=e=>{surge=surge>1?1:1.9;e.target.textContent=surge>1?'Calm':'Rain surge';};
document.getElementById('bp').onclick=e=>{paused=!paused;e.target.textContent=paused?'Play':'Pause';};
frame();
</script>
"""


STREET3D = """
<div id="w" style="position:relative;height:470px;background:linear-gradient(180deg,#2A2F8F,#070B1F 75%);border-radius:18px;overflow:hidden;font-family:Helvetica,Arial,sans-serif;border:1px solid rgba(255,255,255,.14)">
<div id="hud" style="position:absolute;left:14px;top:12px;color:#EAF0FF;font-size:14px;line-height:1.6;pointer-events:none"></div>
<div style="position:absolute;right:12px;top:12px;display:flex;gap:6px;z-index:5"><button class="b" id="bm">Switch on Mati-Marga</button><button class="b" id="bp">Pause</button></div>
<div style="position:absolute;left:14px;bottom:10px;color:#9AA7D6;font-size:12px;pointer-events:none">Drag to rotate · scroll to zoom · cars are teal, trucks gold, e-carts green</div></div>
<style>.b{background:#B6F500;color:#0B1230;border:0;border-radius:9px;padding:8px 12px;font-weight:700;cursor:pointer;box-shadow:0 3px 0 #6D9400}.b:active{transform:translateY(3px);box-shadow:none}body{margin:0}</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const NT=__N__, L=26, VM=.1, w=document.getElementById('w'), H=470; let W=Math.max(w.clientWidth,320);
const sc=new THREE.Scene(), cam=new THREE.PerspectiveCamera(45,W/H,.1,100); cam.position.set(0,13,15); cam.lookAt(0,0,-2);
const rd=new THREE.WebGLRenderer({antialias:true,alpha:true}); rd.setSize(W,H); rd.setPixelRatio(window.devicePixelRatio); w.appendChild(rd.domElement); rd.domElement.style.display='block';
const fit=()=>{W=Math.max(w.clientWidth,320);rd.setSize(W,H);cam.aspect=W/H;cam.updateProjectionMatrix();};
new ResizeObserver(fit).observe(w); fit();
sc.add(new THREE.AmbientLight(0xffffff,.8)); const dl=new THREE.DirectionalLight(0xffffff,.8); dl.position.set(6,12,8); sc.add(dl);
const g=new THREE.Group(); sc.add(g);
const box=(a,b,c,col,x,y,z,par)=>{const m=new THREE.Mesh(new THREE.BoxGeometry(a,b,c),new THREE.MeshStandardMaterial({color:col}));m.position.set(x,y,z);(par||g).add(m);return m;};
box(40,.04,26,0x0F1B4D,0,-.05,-4); box(28,.06,2.6,0x242B57,0,0,0);
for(let i=-6;i<=6;i++) box(1,.07,.1,0xEAF0FF,i*2.2,0,0);
for(let i=0;i<7;i++){box(2,1.2,1.6,0xEAF0FF,-9+i*3,.6,-3.4); box(2.3,.2,1.9,0xB6F500,-9+i*3,1.3,-3.4);}
box(9,.06,5,0x2B3570,9.5,.03,-8.5); box(20,.04,.7,0x3B2F9E,0,.02,-5.8);
const edge=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(9,.06,5)),new THREE.LineBasicMaterial({color:0xB6F500})); edge.position.set(9.5,.07,-8.5); g.add(edge);
const trucks=[],cars=[],eca=[];
for(let i=0;i<NT;i++){const m=new THREE.Group(); box(2.2,.9,1.1,i%2?0xB6F500:0x9AC900,0,.55,0,m); box(.7,.7,1,0x0B1230,1.45,.45,0,m); g.add(m);
 const lx=-10+i*(18/Math.max(NT,1)), yx=6.5+(i%5)*1.7, yz=-9.4+Math.floor(i/5)*1.8; m.position.set(lx,0,0);
 trucks.push({m,lx,lz:0,yx,yz,inLane:true});}
for(let i=0;i<14;i++){const m=box(1,.45,.7,i%3?0x7BE9FA:0x9fe7ff,0,.3,0); const x=-13+i*(L/14); cars.push({m,x,v:VM}); m.position.x=x;}
for(let i=0;i<4;i++){const m=box(.9,.4,.6,0xB6F500,0,.25,-5.8); m.visible=false; eca.push(m);}
let mm=false,paused=false,t=0,flow=1,drag=false,lx0=0;
function frame(){
 if(!paused){ t+=.016;
  trucks.forEach(k=>{const tx=mm?k.yx:k.lx, tz=mm?k.yz:k.lz; k.m.position.x+=(tx-k.m.position.x)*.04; k.m.position.z+=(tz-k.m.position.z)*.04; k.inLane=Math.abs(k.m.position.z)<1.7;});
  let sum=0;
  cars.forEach(c=>{let best=1e9;
   trucks.forEach(k=>{if(!k.inLane)return; const d=(k.m.position.x-c.x+L)%L-1.8; if(d<best)best=d;});
   cars.forEach(o=>{if(o===c)return; const d=(o.x-c.x+L)%L-1.0; if(d<best)best=d;});
   const tg=VM*Math.max(0,Math.min(1,(best-.25)/.6)); c.v+=(tg-c.v)*.15; c.x+=c.v; if(c.x>L/2)c.x-=L; c.m.position.x=c.x; sum+=c.v;});
  flow+=((sum/cars.length)/VM-flow)*.05;
  eca.forEach((e,i)=>{e.visible=mm; e.position.x=-9+(Math.sin(t*.9+i*1.6)*.5+.5)*19;});
  if(!drag) g.rotation.y=Math.sin(t*.15)*.12;
 }
 rd.render(sc,cam); requestAnimationFrame(frame);
}
setInterval(()=>{const m=Math.round(10/Math.max(flow,.12));
 document.getElementById('hud').innerHTML='<b style="font-size:20px;color:'+(mm?'#9AF0FF':'#FF9DB0')+'">'+(mm?'With Mati-Marga':'Today')+'</b><br>Traffic flow: '+Math.round(flow*100)+'%<br>Crossing time: ~'+m+' min';},300);
const el=rd.domElement; el.style.touchAction='none';
el.addEventListener('pointerdown',e=>{drag=true;lx0=e.clientX;}); addEventListener('pointerup',()=>drag=false);
el.addEventListener('pointermove',e=>{if(drag){g.rotation.y=Math.max(-.9,Math.min(.9,g.rotation.y+(e.clientX-lx0)*.006));lx0=e.clientX;}});
el.addEventListener('wheel',e=>{e.preventDefault();cam.position.z=Math.max(9,Math.min(24,cam.position.z+e.deltaY*.01));cam.lookAt(0,0,-2);},{passive:false});
document.getElementById('bm').onclick=e=>{mm=!mm;e.target.textContent=mm?'Back to today':'Switch on Mati-Marga';};
document.getElementById('bp').onclick=e=>{paused=!paused;e.target.textContent=paused?'Play':'Pause';};
frame();
</script>
"""


HERO3D = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@700;800&family=Hind:wght@400;600&display=swap');
*{box-sizing:border-box}body{margin:0;font-family:'Hind',sans-serif}
#h{position:relative;height:600px;border-radius:26px;overflow:hidden;border:1px solid rgba(124,92,255,.55);background:radial-gradient(700px 400px at 85% 8%,rgba(124,92,255,.55),transparent 70%),radial-gradient(600px 400px at 0% 100%,rgba(34,211,238,.28),transparent 70%),linear-gradient(135deg,#131c4a,#070B1F);box-shadow:0 0 80px -14px rgba(124,92,255,.55)}
canvas{position:absolute;left:0;top:0}
.t{position:absolute;left:44px;top:38px;max-width:560px;color:#EAF0FF;pointer-events:none}
.bd{display:inline-block;padding:5px 12px;border-radius:99px;font-size:11px;letter-spacing:.1em;font-weight:700;margin:0 6px 8px 0;border:1px solid rgba(182,245,0,.55);color:#B6F500;background:rgba(182,245,0,.08)}
.bd.v{border-color:rgba(124,92,255,.7);color:#b9a8ff;background:rgba(124,92,255,.14)}
.dv{color:#B6F500;font-size:22px;font-weight:600;margin:6px 0 2px}
h1{font-family:'Bricolage Grotesque';font-size:64px;line-height:1;margin:0;font-weight:800;background:linear-gradient(90deg,#EAF0FF,#7BE9FA 55%,#B6F500);-webkit-background-clip:text;background-clip:text;color:transparent}
.sub{margin:16px 0 8px;color:#C9D2F2;font-size:17px;line-height:1.55;max-width:500px}
.rot{display:inline-block;color:#7BE9FA;font-weight:600;transition:opacity .4s,transform .4s}
.st{position:absolute;left:44px;right:44px;bottom:26px;display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.s{padding:14px 16px;border-radius:16px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.16);backdrop-filter:blur(10px)}
.s b{display:block;font-family:'Bricolage Grotesque';font-size:30px;color:#EAF0FF}.s span{font-size:13px;color:#9AA7D6}
@media(max-width:820px){h1{font-size:40px}.st{grid-template-columns:repeat(2,1fr)}.t{left:20px;right:20px}.st{left:20px;right:20px}}
</style>
<div id="h">
<div class="t"><div><span class="bd">SEVA FIRST INNOVATION CHALLENGE</span><span class="bd v">PEN · RAIGAD</span></div>
<div class="dv">माती-मार्ग</div><h1>Clean drains.<br>Clear streets.</h1>
<div class="sub">A drain trap and freight yard system made <span class="rot" id="rot">for workshop owners</span>. Catch plaster sludge at the source, move heavy trucks out of the lanes.</div></div>
<div class="st">
<div class="s"><b data-f="0" data-t="82" data-u="%">0</b><span>of PoP solids trapped</span></div>
<div class="s"><b data-f="75" data-t="10" data-u=" min">75</b><span>August crossing time</span></div>
<div class="s"><b data-f="45" data-t="8" data-u=" kg">45</b><span>sludge per drain, daily</span></div>
<div class="s"><b data-f="0" data-t="25000" data-u="">0</b><span>residents helped in Pen</span></div></div></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const h=document.getElementById('h'),H=600; let W=Math.max(h.clientWidth,320);
document.querySelectorAll('.s b').forEach(b=>{const f=+b.dataset.f,t=+b.dataset.t,u=b.dataset.u,t0=performance.now();
 (function k(n){const p=Math.min(1,(n-t0)/1800),e=1-Math.pow(1-p,3);b.textContent=Math.round(f+(t-f)*e).toLocaleString('en-IN')+u;if(p<1)requestAnimationFrame(k);})(t0);});
const R=['for workshop owners','for commuters','for the Bhogavati river','for Pen Nagar Parishad'];let ri=0;const rot=document.getElementById('rot');
setInterval(()=>{rot.style.opacity=0;rot.style.transform='translateY(6px)';setTimeout(()=>{ri=(ri+1)%R.length;rot.textContent=R[ri];rot.style.opacity=1;rot.style.transform='none';},400);},2600);
if(window.THREE){
const sc=new THREE.Scene(),cam=new THREE.PerspectiveCamera(45,W/H,.1,100);cam.position.set(0,1.2,11);cam.lookAt(0,.2,0);
const rd=new THREE.WebGLRenderer({antialias:true,alpha:true});rd.setSize(W,H);rd.setPixelRatio(window.devicePixelRatio);h.insertBefore(rd.domElement,h.firstChild);
const fit=()=>{W=Math.max(h.clientWidth,320);rd.setSize(W,H);cam.aspect=W/H;cam.updateProjectionMatrix();};
new ResizeObserver(fit).observe(h); fit();
sc.add(new THREE.AmbientLight(0xffffff,.8));const dl=new THREE.DirectionalLight(0xffffff,.9);dl.position.set(5,8,6);sc.add(dl);
const g=new THREE.Group();sc.add(g);g.position.x=W>820?3.6:0;g.rotation.x=.35;
const SY=[2.2,.6,-1],SC=[0x94A3D6,0x7C5CFF,0xB6F500];
SY.forEach((y,i)=>{const m=new THREE.Mesh(new THREE.BoxGeometry(4.2,.22,4.2),new THREE.MeshStandardMaterial({color:SC[i],transparent:true,opacity:.85}));m.position.y=y;
 m.add(new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry),new THREE.LineBasicMaterial({color:0xffffff,transparent:true,opacity:.5})));g.add(m);});
const pool=new THREE.Mesh(new THREE.BoxGeometry(4.2,.5,4.2),new THREE.MeshStandardMaterial({color:0x22D3EE,transparent:true,opacity:.6}));pool.position.y=-2.7;g.add(pool);
const N=260,pos=new Float32Array(N*3),col=new Float32Array(N*3),P=[],geo=new THREE.BufferGeometry(),E=[.45,.4,.45];
geo.setAttribute('position',new THREE.BufferAttribute(pos,3));geo.setAttribute('color',new THREE.BufferAttribute(col,3));
g.add(new THREE.Points(geo,new THREE.PointsMaterial({size:.11,vertexColors:true,transparent:true,depthWrite:false,blending:THREE.AdditiveBlending})));
const fate=()=>{for(let i=0;i<3;i++)if(Math.random()<E[i])return i;return 3;};
const sp=(p,f)=>{p.x=(Math.random()-.5)*3.8;p.z=(Math.random()-.5)*3.8;p.y=4.8+Math.random()*(f?9:2);p.v=.02+Math.random()*.02;p.f=fate();p.h=0;};
for(let i=0;i<N;i++){const p={};sp(p,true);P.push(p);}
const S=new Float32Array(400*3);for(let i=0;i<S.length;i++)S[i]=(Math.random()-.5)*40;
const sg=new THREE.BufferGeometry();sg.setAttribute('position',new THREE.BufferAttribute(S,3));const stars=new THREE.Points(sg,new THREE.PointsMaterial({size:.05,color:0x9AA7D6,transparent:true,opacity:.6}));sc.add(stars);
let mx=0,my=0,tx=0,ty=0,t=0;h.addEventListener('pointermove',e=>{const r=h.getBoundingClientRect();tx=((e.clientX-r.left)/r.width-.5)*2;ty=((e.clientY-r.top)/r.height-.5)*2;});
const pink=new THREE.Color(0xFF4D6D),cy=new THREE.Color(0x22D3EE),c=new THREE.Color();
(function f(){t+=.016;mx+=(tx-mx)*.05;my+=(ty-my)*.05;
 g.position.x=W>820?3.6:0;
 P.forEach((p,i)=>{if(p.h>0){p.h--;if(!p.h)sp(p,false);}else{p.y-=p.v;const ty_=p.f<3?SY[p.f]+.25:pool.position.y+.3;if(p.y<=ty_){p.y=ty_;p.h=70;}}
  pos.set([p.x,p.y,p.z],i*3);
  if(p.h>0&&p.f<3)c.set(0xB6F500);else c.copy(pink).lerp(cy,Math.max(0,Math.min(1,(2.4-p.y)/5)));col.set([c.r,c.g,c.b],i*3);});
 geo.attributes.position.needsUpdate=true;geo.attributes.color.needsUpdate=true;
 g.rotation.y=t*.18+mx*.5;g.rotation.x=.35+my*.15;stars.rotation.y=t*.01;cam.position.x=mx*.8;cam.lookAt(0,.2,0);
 rd.render(sc,cam);requestAnimationFrame(f);})();}
</script>"""


def kpi(label, value, sub="", bad=False):
    st.markdown(f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div>'
                f'<div class="s {"bad" if bad else ""}">{sub}</div></div>', unsafe_allow_html=True)


def style(fig, h=380):
    fig.update_layout(height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=PLASTER, family="Hind"), margin=dict(l=10, r=10, t=40, b=10),
                      legend=dict(orientation="h", y=-0.2))
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)"); fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)")
    return fig


# ---------- core models ----------
TIERS = [("Coarse metal mesh", 0.45, 40), ("Medium gravel bed", 0.40, 25), ("Fine coir sheet", 0.45, 18)]


def trap_model(inflow, effs, caps, interval_h, work_h=10):
    """Sequential capture; returns stage loads, hours to saturation, effective capture."""
    loads, rem, sat = [inflow], inflow, []
    for e, c in zip(effs, caps):
        sat.append(c / max(rem / work_h, 1e-6))
        rem *= (1 - e)
        loads.append(rem)
    s = min(sat)
    uptime = min(1.0, s / interval_h)  # remainder of time the bypass valve is open
    captured = (1 - loads[-1] / inflow) * uptime
    return loads, sat, captured, uptime


def transit(trucks):  # congestion curve calibrated so 14 trucks in lane ~ 75 min (observed, Antora)
    return 10 * (1 + 0.15 * (0.55 + 0.144 * trucks) ** 4)


HOURS = list(range(6, 22))
RESTRICTED = {7, 8, 15, 16}  # school bus windows
SLOT_CAP = 4

if "bookings" not in st.session_state:
    saved_bookings = st.session_state._mati_marga_db.get("bookings", [])
    if saved_bookings:
        st.session_state.bookings = pd.DataFrame(saved_bookings, columns=["Workshop", "Truck", "Idols", "Hour"])
        st.session_state.bookings["Idols"] = pd.to_numeric(st.session_state.bookings["Idols"], errors="coerce").fillna(0).astype(int)
        st.session_state.bookings["Hour"] = pd.to_numeric(st.session_state.bookings["Hour"], errors="coerce").fillna(0).astype(int)
    else:
        st.session_state.bookings = pd.DataFrame([
            ["Hamrapur Kala Kendra", "MH-06-AB-1123", 220, 10], ["Kasar Ali Shilp", "MH-43-CD-4521", 180, 10],
            ["Antora Murti Ghar", "MH-06-EF-9087", 300, 11], ["Hamrapur Kala Kendra", "MH-46-GH-3310", 150, 11],
            ["Chinchpada Studio", "MH-06-JK-7765", 260, 13], ["Kasar Ali Shilp", "MH-04-LM-2201", 210, 18],
        ], columns=["Workshop", "Truck", "Idols", "Hour"])


# =====================================================================
# GOOGLE GEMINI SETTINGS
# =====================================================================
def _secret_key():
    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""

MODEL_NAME = "gemini-3.8-flash"
# API credentials are loaded privately from Streamlit Secrets or environment.
# No API-key/settings controls are shown in the judges' interface.
api_key = os.getenv("GEMINI_API_KEY", "") or _secret_key()
lang = "Bilingual"  # Keep the app's previous default language without showing settings.
model = MODEL_NAME

# ---------- hero ----------
st.markdown("""<div class="topnav"><div class="brand"><span class="logo">🪔</span>Mati-Marga<small>Soil &amp; Street</small></div>
<div class="pill"><i></i>LIVE PROTOTYPE · PEN, RAIGAD</div></div>""", unsafe_allow_html=True)
components.html(HERO3D, height=620)
st.write("")

tabs = st.tabs(["Vendor day-planner", "Citizen desk", "Officer console", "Drain trap lab", "Freight scheduler", "Pen map", "AI assistant", "Money & scale", "Roadmap", "3D Studio"])

# ===== TAB: trap lab =====
with tabs[3]:
    st.subheader("Three-stage drain trap lab")
    l, r = st.columns([1, 2])
    with l:
        inflow = st.slider("Sludge entering the drain (kg/day)", 5, 120, 45)
        n_ws = st.slider("Workshops fitted with traps", 1, 3000, 10)
        interval = st.slider("Hours between cleanings", 2, 48, 24)
        st.markdown("**Stage efficiency**")
        effs = [st.slider(t[0], 10, 80, int(t[1] * 100), key=f"e{i}") / 100 for i, t in enumerate(TIERS)]
        single = st.toggle("Show the failed single tight-coir design instead", False)
    if single:
        loads, sat, cap, up = trap_model(inflow, [0.9], [18], interval)
        names = ["Raw sludge", "After single coir"]
    else:
        loads, sat, cap, up = trap_model(inflow, effs, [t[2] for t in TIERS], interval)
        names = ["Raw sludge", "After coarse mesh", "After gravel bed", "After coir sheet"]
    with r:
        fig = go.Figure(go.Funnel(y=names, x=[round(v, 1) for v in loads], textinfo="value",
                                  marker=dict(color=[SILT, "#7C5CFF", MARIGOLD, RIVER][:len(names)])))
        plot(style(fig.update_layout(title="Sludge load at each stage (kg/day)"), 330))
    m = st.columns(4)
    with m[0]: kpi("Solids trapped", f"{cap*100:.0f}%", "bypass open " + f"{(1-up)*100:.0f}% of the time", bad=up < 1)
    with m[1]: kpi("Discharge per drain", f"{inflow*(1-cap):.1f} kg/day", f"was {inflow} kg")
    with m[2]: kpi("First stage to fill", f"{min(sat):.1f} h", "clean before this", bad=min(sat) < interval)
    with m[3]: kpi(f"River relief ({n_ws} sites)", f"{n_ws*inflow*cap/1000:.2f} t/day", "kept out of Bhogavati")
    if single:
        st.error(f"A single fine coir layer fills in about {min(sat):.1f} hours. That matches the 4-hour clog in the first trial, "
                 "when graywater backed up into the courtyard.")
    elif min(sat) < interval:
        st.warning(f"The cleaning interval is longer than the {min(sat):.1f} hours the first full stage lasts. "
                   "The overflow bypass will open and let sludge through. Shorten the interval.")
    else:
        st.success("Cleaning interval is inside the safe window. The bypass valve stays closed.")
    st.markdown("#### Live 3D trap")
    st.caption("Each dot is a lump of sludge. It is caught at a stage with the efficiency you set above. Red dots escape into the drain.")
    components.html(TRAP3D.replace("__EFFS__", json.dumps(list(effs) if not single else [0.9, 0.0, 0.0])), height=460)
    st.markdown("#### 3D capture surface")
    iv, inf_ = np.arange(2, 49, 3), np.arange(10, 121, 10)
    Z = [[trap_model(i_, effs, [t_[2] for t_ in TIERS], h_)[2] * 100 for h_ in iv] for i_ in inf_]
    f3 = go.Figure(go.Surface(x=iv, y=inf_, z=Z, colorscale=[[0, ALERT], [.5, MARIGOLD], [1, RIVER]], showscale=False))
    ax = dict(gridcolor="rgba(255,255,255,0.15)", color=PLASTER, backgroundcolor="rgba(0,0,0,0)")
    f3.update_layout(scene=dict(xaxis=dict(title="Hours between cleanings", **ax), yaxis=dict(title="Sludge kg/day", **ax),
                                zaxis=dict(title="% trapped", **ax), camera=dict(eye=dict(x=1.6, y=-1.6, z=0.9))))
    plot(style(f3, 460))
    st.caption("Drag to rotate. Capture falls off the green ridge when cleaning is too infrequent or the load is too high.")
    st.markdown(f"**Trapped sludge becomes paving.** At 2.5 kg per block and ₹8 each, {n_ws} sites earn about "
                f"₹{n_ws*inflow*cap/2.5*8*30:,.0f} a month from PWD sub-base block sales.")

# ===== TAB: scheduler =====
with tabs[4]:
    st.subheader("Freight slot scheduler")
    left, right = st.columns([1, 1.6])
    df = st.session_state.bookings
    load = df.groupby("Hour").size().reindex(HOURS, fill_value=0)
    with left:
        free = [h for h in HOURS if h not in RESTRICTED and load[h] < SLOT_CAP]
        best = min(free, key=lambda h: (load[h], h)) if free else None
        st.markdown(f"Best open slot right now: **{best:02d}:00**" if best else "All slots are full.")
        with st.form("book"):
            ws = st.selectbox("Workshop", ["Hamrapur Kala Kendra", "Kasar Ali Shilp", "Antora Murti Ghar", "Chinchpada Studio"])
            truck = st.text_input("Truck number", "MH-06-XX-0000")
            idols = st.number_input("Idols to ship", 10, 800, 200, step=10)
            hour = st.selectbox("Pickup slot at peripheral yard", free, format_func=lambda h: f"{h:02d}:00 – {h+1:02d}:00")
            go_ = st.form_submit_button("Book slot")
        if go_ and hour is not None:
            st.session_state.bookings = pd.concat([df, pd.DataFrame([[ws, truck, idols, hour]], columns=df.columns)], ignore_index=True)
            save_app_data()
            st.toast(f"Booked {hour:02d}:00 for {truck}. An e-cart will bring the load to the yard."); st.rerun()
        st.caption("7–9 am and 3–5 pm are blocked for school buses. Each slot holds 4 trucks.")
    with right:
        colors = [ALERT if h in RESTRICTED else (MARIGOLD if load[h] >= SLOT_CAP else RIVER) for h in HOURS]
        fig = go.Figure(go.Bar(x=[f"{h:02d}:00" for h in HOURS], y=load.values, marker_color=colors))
        fig.add_hline(y=SLOT_CAP, line_dash="dot", line_color=PLASTER, annotation_text="slot capacity")
        plot(style(fig.update_layout(title="Bookings per hour (red = school window, amber = full)"), 300))
        table(df.assign(Slot=df.Hour.map(lambda h: f"{h:02d}:00")).drop(columns="Hour").tail(8))
    st.markdown("#### What happens to the lanes")
    n_peak = st.slider("Trucks loading in lanes today without scheduling", 0, 20, 14)
    prof = np.exp(-((np.array(HOURS) - 11) ** 2) / 8) + 0.8 * np.exp(-((np.array(HOURS) - 18) ** 2) / 6)
    trucks = prof / prof.max() * n_peak
    fig = go.Figure()
    fig.add_scatter(x=[f"{h:02d}:00" for h in HOURS], y=[transit(t) for t in trucks], name="Today", line=dict(color=ALERT, width=3), fill="tozeroy")
    fig.add_scatter(x=[f"{h:02d}:00" for h in HOURS], y=[transit(0)] * len(HOURS), name="With Mati-Marga", line=dict(color=RIVER, width=3))
    plot(style(fig.update_layout(title="Cross-town transit (minutes)"), 320))
    st.markdown("#### Live street simulator (3D)")
    st.caption("Same road, same cars. Press the button to move loading out of the lane and watch the queue clear. Uses the truck count from the slider above.")
    components.html(STREET3D.replace("__N__", str(max(3, min(int(n_peak), 12)))), height=490)
    st.markdown("#### Play the day")
    spots_, wts = ["Antora", "Chinchpada", "Kasar Ali", "Hamrapur", "NH-66 exit"], [1, .85, .6, .5, .95]
    frs = [go.Frame(name=str(h), data=[go.Bar(x=spots_, y=[trucks[i] * w_ for w_ in wts], marker_color=ALERT)]) for i, h in enumerate(HOURS)]
    fa = go.Figure(data=frs[0].data, frames=frs)
    fa.update_layout(updatemenus=[dict(type="buttons", showactive=False, x=0, y=1.28, buttons=[
        dict(label="▶ Play", method="animate", args=[None, {"frame": {"duration": 500, "redraw": True}, "fromcurrent": True}]),
        dict(label="❚❚ Pause", method="animate", args=[[None], {"mode": "immediate", "frame": {"duration": 0}}])])],
        sliders=[dict(steps=[dict(method="animate", label=f"{h}:00", args=[[str(h)], {"mode": "immediate", "frame": {"duration": 0, "redraw": True}}]) for h in HOURS],
                      currentvalue=dict(prefix="Hour ", font=dict(color=PLASTER)), font=dict(color=PLASTER))])
    fa.update_yaxes(range=[0, 16], title="Trucks parked in lane")
    plot(style(fa, 420))
    st.caption("Model: congestion curve calibrated to the observed 75-minute crossing with 14 trucks parked in lanes.")

# ===== TAB: map =====
with tabs[5]:
    st.subheader("Pen at a glance")
    pts = pd.DataFrame([
        ["Kasar Ali: trial drains", 18.7335, 73.0985, "Trap pilot", RIVER], ["Hamrapur: 10-site cluster", 18.7215, 73.1105, "Stage 2", RIVER],
        ["Antora junction", 18.7450, 73.0870, "Gridlock point", ALERT], ["Chinchpada junction", 18.7290, 73.0830, "Gridlock point", ALERT],
        ["Peripheral freight yard (2 acre)", 18.7520, 73.1050, "Proposed", MARIGOLD]],
        columns=["name", "lat", "lon", "role", "color"])
    fig = go.Figure(MAPTRACE(lat=pts.lat, lon=pts.lon, text=pts.name + " · " + pts.role, hoverinfo="text",
                                     mode="markers+text", textposition="top right", textfont=dict(color=PLASTER),
                                     marker=dict(size=16, color=pts.color)))
    fig.update_layout(**{MAPKEY: dict(style="carto-darkmatter", center=dict(lat=18.7375, lon=73.0950), zoom=12.3)})
    plot(style(fig, 520))
    st.caption("Positions are approximate. Replace with surveyed GPS points.")

# ===== TAB: AI assistant =====
SYSTEM = ("You are the Mati-Marga assistant for Pen, Raigad. Facts: 3-stage drain trap (coarse mesh, gravel, coir) traps 82% of PoP sludge, "
          "45 kg to under 8 kg per drain daily; 3 workshops trialled in Kasar Ali/Hamrapur; first single coir layer clogged in 4 hours; "
          "overflow bypass valve added; peripheral 2-acre freight yard, 15 e-carts, slot-booking app; August transit 75 min vs 10 normal; "
          "PWD buys PoP blocks at Rs 8; Stage 3 cost Rs 4.5 lakh, benefit Rs 8.8 lakh/month. Be concrete, short, and never invent data.")

TEMPLATES = {
    "Marathi operating manual for artisans": (
        "**मातीमार्ग ट्रॅप: कारागिरांसाठी सूचना**\n1. रोज सकाळी आणि संध्याकाळी जाळी तपासा.\n2. पहिली जाडी जाळी (कोअर्स मेश) भरली की काढून पीओपी गाळ पिशवीत भरा.\n"
        "3. पाणी तुंबल्यास बायपास व्हॉल्व्ह उघडा, मग जाळी साफ करा.\n4. गाळ गटारात किंवा नदीत टाकू नका. नगर परिषदेच्या गाडीला द्या.\n5. ट्रक फक्त बुक केलेल्या वेळेतच यार्डकडे पाठवा."),
    "Letter to Chief Officer, Pen Nagar Parishad": (
        "To,\nThe Chief Officer, Pen Nagar Parishad\n\nSubject: Proposal for a Zero-Clog Festive Zone in Pen\n\nRespected Sir/Madam,\nIn a trial with 3 workshops, our three-stage drain trap cut daily PoP sludge from 45 kg to under 8 kg per drain. "
        "We request approval for a 2-acre peripheral freight yard near the highway bypass and 15 e-carts for the July to September season. "
        "Estimated one-time cost is Rs 4,50,000 with a monthly saving of about Rs 8,80,000 in desilting and fuel.\n\nYours sincerely,\n[Name]"),
    "Press note": ("Pen students' Mati-Marga trial keeps 82% of plaster sludge out of drains. With a freight yard outside the old lanes, "
                   "August crossings that took 75 minutes can return to about 10."),
}

# ---------- English -> Marathi translation ----------
TR_SYSTEM = ("You are a professional English-to-Marathi translator for a civic project in Pen, Raigad. "
             "Write natural Devanagari Marathi that a workshop owner or municipal clerk would understand. "
             "Keep numbers, units (kg, min, ₹), vehicle numbers, phone numbers, URLs and proper names unchanged. "
             "Use common spoken terms where they are clearer than formal Sanskritised words "
             "(e.g. ट्रक, ड्रेन, पीओपी). Output only the translation, with no commentary.")

GLOSSARY = {  # offline fallback: key project terms only
    "drain trap": "ड्रेन ट्रॅप", "drain": "गटार", "sludge": "गाळ", "plaster of paris": "प्लास्टर ऑफ पॅरिस",
    "workshop": "कारखाना", "workshops": "कारखाने", "truck": "ट्रक", "trucks": "ट्रक", "freight yard": "मालवाहतूक यार्ड",
    "yard": "यार्ड", "slot": "वेळ", "booking": "नोंदणी", "river": "नदी", "school": "शाळा", "bus": "बस",
    "rain": "पाऊस", "clean": "स्वच्छ करा", "cleaning": "स्वच्छता", "report": "तक्रार", "road": "रस्ता",
    "lane": "गल्ली", "idols": "मूर्ती", "idol": "मूर्ती", "coarse mesh": "जाडी जाळी", "gravel": "खडी",
    "coir": "नारळाचा काथ्या", "bypass valve": "बायपास व्हॉल्व्ह", "festival": "उत्सव", "traffic": "वाहतूक",
    "municipal council": "नगर परिषद", "pen nagar parishad": "पेण नगर परिषद", "daily": "रोज", "morning": "सकाळ",
    "evening": "संध्याकाळ", "please": "कृपया", "thank you": "धन्यवाद",
}


def glossary_translate(text):
    out = text
    for en in sorted(GLOSSARY, key=len, reverse=True):
        out = re.sub(rf"\b{re.escape(en)}\b", f"{en} ({GLOSSARY[en]})", out, flags=re.I)
    return out


def translate_text(text, mode):
    """mode: 'Marathi' or 'Bilingual'. Returns (result, used_ai)."""
    if not text.strip():
        return "", False
    if api_key:
        try:
            from google import genai
            if mode == "Marathi":
                ask = f"Translate this English text into Marathi:\n\n{text}"
            else:
                ask = ("Produce a bilingual version of this English text. For each sentence or list item, "
                       "write the English line, then the Marathi translation on the next line. "
                       f"Preserve the original order and numbering:\n\n{text}")
            client = genai.Client(api_key=api_key)
            r = client.models.generate_content(
                model=model,
                contents=ask,
                config={"system_instruction": TR_SYSTEM, "max_output_tokens": 1500},
            )
            return r.text, True
        except Exception as e:
            return f"The translation call failed: {e}", False
    return glossary_translate(text), False


def _load_last_output():
    st.session_state.tr_src = st.session_state.get("ai_out", "")


with tabs[6]:
    st.subheader("AI assistant")
    st.caption("🟢 Live: answers come from Google Gemini." if api_key else "⚪ Offline: built-in templates. Gemini AI is configured by the app administrator.")
    task = st.selectbox("What do you need?", list(TEMPLATES) + ["Ask anything about the project"])
    extra = st.text_area("Extra context or your question", placeholder="e.g. Write it for workshop owners in Hamrapur who cannot read English.")
    if st.button("Generate"):
        prompt = f"Task: {task}. Language: {lang}. {extra}"
        st.session_state.ai_offline = False
        if api_key:
            try:
                from google import genai
                with st.spinner("Writing..."):
                    client = genai.Client(api_key=api_key)
                    resp = client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config={"system_instruction": SYSTEM, "max_output_tokens": 1200},
                    )
                out = resp.text
            except Exception as e:
                out = f"The model call failed: {e}"
        else:
            out = TEMPLATES.get(task, "Gemini AI is configured by the app administrator.")
            st.session_state.ai_offline = True
        st.session_state.ai_out = out
    if "ai_out" in st.session_state:
        if st.session_state.get("ai_offline"):
            st.info("Showing a built-in template. Add an API key for tailored output.")
        st.markdown(f'<div class="kpi">{st.session_state.ai_out}</div>'.replace("\n", "<br>"), unsafe_allow_html=True)
        st.download_button("Download as text", st.session_state.ai_out, file_name="mati_marga.txt", key="ai_dl")

    # ---------- Translator ----------
    st.markdown("#### Translate English → Marathi")
    st.caption("Paste any English text, or load the last generated output. Choose Marathi only, or a bilingual version with English and Marathi line by line.")
    tcol1, tcol2 = st.columns([2, 1])
    with tcol2:
        tmode = st.radio("Translate to", ["Marathi", "Bilingual"], key="tmode")
        st.button("Load last generated output", on_click=_load_last_output,
                  disabled="ai_out" not in st.session_state, key="tr_load")
    with tcol1:
        src = st.text_area("English text", height=160, key="tr_src",
                           placeholder="e.g. Please send your truck to the yard at 11:00. Do not park in the lane.")
    if st.button("Translate", key="tr_go"):
        if not src.strip():
            st.warning("Enter some English text first.")
        else:
            with st.spinner("Translating..."):
                res, used_ai = translate_text(src, tmode)
            st.session_state.tr_out = res
            st.session_state.tr_mode = tmode
            st.session_state.tr_offline = not used_ai and not api_key
    if st.session_state.get("tr_out"):
        if st.session_state.get("tr_offline"):
            st.info("No API key: glossary mode only. Project terms are shown with Marathi in brackets. "
                    "Gemini AI is configured by the app administrator.")
        st.markdown(f'<div class="kpi">{st.session_state.tr_out}</div>'.replace("\n", "<br>"), unsafe_allow_html=True)
        st.download_button("Download translation", st.session_state.tr_out,
                           file_name=f"mati_marga_{st.session_state.get('tr_mode', 'marathi').lower()}.txt", key="tr_dl")
        st.link_button("Share on WhatsApp", "https://wa.me/?text=" + quote(st.session_state.tr_out))

# ===== TAB: finance =====
with tabs[7]:
    st.subheader("Money and scale")
    stages = pd.DataFrame({"Stage": ["Pilot (1–2)", "Town (3)", "State (4)"], "Setup": [8500, 450000, 1800000],
                           "Running": [1200, 65000, 210000], "Benefit": [14000, 880000, 4500000]})
    pick = st.radio("Stage", stages.Stage, horizontal=True, index=1)
    s = stages[stages.Stage == pick].iloc[0]
    net = s.Benefit - s.Running
    months = np.arange(0, 13)
    cum = -s.Setup + net * months
    k = st.columns(3)
    with k[0]: kpi("One-time setup", f"₹{s.Setup:,.0f}")
    with k[1]: kpi("Net monthly gain", f"₹{net:,.0f}", f"benefit ₹{s.Benefit:,.0f} less running ₹{s.Running:,.0f}")
    with k[2]: kpi("Payback", f"{s.Setup/net:.1f} months" if net > 0 else "n/a")
    fig = go.Figure(go.Scatter(x=months, y=cum, fill="tozeroy", line=dict(color=MARIGOLD, width=3)))
    fig.add_hline(y=0, line_color=PLASTER, line_dash="dot")
    plot(style(fig.update_layout(title="Cumulative net position over 12 months (₹)", xaxis_title="Month"), 330))
    st.caption("Benefits are the blueprint's estimates and have not been independently audited.")

# ===== TAB: roadmap =====
with tabs[8]:
    st.subheader("Scaling roadmap")
    st.caption("Hover a card to flip it.")
    rc = st.columns(2)
    for i_, (t, d) in enumerate([("Stage 1 · Prove it", "Month 1: 3 workshops in Kasar Ali, 2 weeks. Target: zero overflow, lanes clear."),
                 ("Stage 2 · Repeat it", "Month 3: 10 units in Hamrapur with a one-page Marathi manual. Owners run it without us."),
                 ("Stage 3 · Town scale", "Month 6: Zero-Clog Festive Zone with Pen Nagar Parishad, 2-acre yard, 15 e-carts."),
                 ("Stage 4 · State scale", "Month 12: evidence to BMC and KDMC for procession traffic and immersion tanks.")]):
        with rc[i_ % 2]:
            st.markdown(f'<div class="flipc"><div class="flipi"><div class="face front"><b>{t}</b><span>Hover to see the plan</span></div>'
                        f'<div class="face back"><span>{d}</span></div></div></div>', unsafe_allow_html=True)
    st.caption(f"Department: Urban Development · Pen Nagar Parishad. Built {datetime.now():%d %b %Y}.")


# =====================================================================
# DAY-TO-DAY TOOLS: vendor planner, citizen desk, officer console
# =====================================================================
VENDORS = ["Hamrapur Kala Kendra", "Kasar Ali Shilp", "Antora Murti Ghar", "Chinchpada Studio"]
SPOTS = ["Antora junction", "Chinchpada junction", "Kasar Ali lane", "Hamrapur lane", "NH-66 town exit"]
now = datetime.now()
if "cleaned" not in st.session_state:
    saved_cleaned = st.session_state._mati_marga_db.get("cleaned", {})
    if saved_cleaned:
        st.session_state.cleaned = {v: datetime.fromisoformat(saved_cleaned[v]) if v in saved_cleaned else now - timedelta(hours=h)
                                    for v, h in zip(VENDORS, [3, 11, 6, 20])}
    else:
        st.session_state.cleaned = {v: now - timedelta(hours=h) for v, h in zip(VENDORS, [3, 11, 6, 20])}
if "tickets" not in st.session_state:
    saved_tickets = st.session_state._mati_marga_db.get("tickets", [])
    if saved_tickets:
        st.session_state.tickets = pd.DataFrame(saved_tickets, columns=["ID", "Type", "Place", "Note", "Status", "Time"])
        st.session_state.tickets["Time"] = pd.to_datetime(st.session_state.tickets["Time"], errors="coerce")
    else:
        st.session_state.tickets = pd.DataFrame([
            ["MM-101", "Clogged drain", "Kasar Ali lane", "White slurry overflowing near school gate", "Open", now - timedelta(hours=5)],
            ["MM-102", "Truck blocking lane", "Antora junction", "16-wheeler loading since morning", "In progress", now - timedelta(hours=3)],
            ["MM-103", "PoP dumping", "Hamrapur lane", "Wash water going straight into gutter", "Resolved", now - timedelta(hours=26)],
        ], columns=["ID", "Type", "Place", "Note", "Status", "Time"])

if not os.path.exists(DATA_FILE):
    save_app_data()


@st.cache_data(ttl=1800)
def pen_weather():
    try:
        u = ("https://api.open-meteo.com/v1/forecast?latitude=18.7378&longitude=73.0937"
             "&hourly=precipitation_probability,temperature_2m&forecast_days=1&timezone=Asia%2FKolkata")
        d = json.load(urllib.request.urlopen(u, timeout=5))["hourly"]
        return d["precipitation_probability"], d["temperature_2m"]
    except Exception:
        return None


def ask_ai(prompt, fallback):
    if not api_key:
        return fallback
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        r = client.models.generate_content(
            model=model,
            contents=prompt,
            config={"system_instruction": SYSTEM, "max_output_tokens": 900},
        )
        return r.text
    except Exception as e:
        return f"The model call failed: {e}"


def lane_trucks(h, peak=14):
    p = lambda x: np.exp(-((x - 11) ** 2) / 8) + 0.8 * np.exp(-((x - 18) ** 2) / 6)
    return peak * p(h) / max(p(11), p(18), 1e-9) if 6 <= h <= 21 else 1


def chip(minutes):
    if minutes < 15: return '<span class="chip ok">Clear</span>'
    if minutes < 35: return '<span class="chip warn">Slow</span>'
    return '<span class="chip bad">Jammed</span>'


W = pen_weather()
rain_now = max(W[0][now.hour:min(now.hour + 6, 24)]) if W else 40
temp_now = W[1][now.hour] if W else None

# ===== Vendor day-planner =====
with tabs[0]:
    st.subheader("My workshop today")
    st.caption("Everything a workshop owner needs before the first truck arrives.")
    v = st.selectbox("Workshop", VENDORS, key="vend")
    since = (now - st.session_state.cleaned[v]).total_seconds() / 3600
    safe = min(trap_model(45, [.45, .40, .45], [40, 25, 18], 24)[1]) * (0.5 if rain_now > 60 else 1)
    status = "bad" if since > safe else ("warn" if since > safe * 0.7 else "ok")
    label = {"ok": "On track", "warn": "Clean soon", "bad": "Clean now"}[status]
    mine = st.session_state.bookings[st.session_state.bookings.Workshop == v]
    a, b, c_, d = st.columns(4)
    with a:
        st.markdown(f'<div class="task"><h4>Drain trap</h4><span class="chip {status}">{label}</span>'
                    f'<p>Cleaned {since:.0f} h ago. Safe window today is {safe:.1f} h.</p></div>', unsafe_allow_html=True)
    with b:
        rc = "bad" if rain_now > 70 else ("warn" if rain_now > 40 else "ok")
        st.markdown(f'<div class="task"><h4>Rain, next 6 hours</h4><span class="chip {rc}">{rain_now}% chance</span>'
                    f'<p>{"Cover finished idols. Rain doubles slurry wash-off, so the safe window is halved." if rain_now > 60 else "Normal day. Standard cleaning schedule applies."}'
                    f'{"" if W else " (Offline: showing an assumed value.)"}</p></div>', unsafe_allow_html=True)
    with c_:
        slot = f"{int(mine.Hour.iloc[0]):02d}:00 · {mine.Truck.iloc[0]}" if len(mine) else "No slot booked"
        st.markdown(f'<div class="task"><h4>Truck slot</h4><span class="chip {"ok" if len(mine) else "warn"}">{slot}</span>'
                    f'<p>{"Send the e-cart to the yard 30 minutes earlier." if len(mine) else "Book one in the Freight scheduler tab."}</p></div>', unsafe_allow_html=True)
    with d:
        st.markdown(f'<div class="task"><h4>Weather</h4><span class="chip ok">{f"{temp_now:.0f} °C" if temp_now is not None else "n/a"}</span>'
                    f'<p>Live from Open-Meteo for Pen.</p></div>', unsafe_allow_html=True)
    if st.button("Mark trap cleaned now", key="clean"):
        st.session_state.cleaned[v] = datetime.now(); save_app_data(); st.toast("Cleaning logged."); st.rerun()

    st.markdown("#### Daily ledger")
    l1, l2 = st.columns([1, 1.4])
    with l1:
        sold = st.number_input("Idols sold today", 0, 500, 12)
        price = st.number_input("Average price (₹)", 100, 50000, 1800, step=100)
        cost = st.number_input("Clay, paint and labour per idol (₹)", 50, 30000, 1100, step=50)
        sludge = st.number_input("Sludge collected today (kg)", 0, 200, 38)
    block_income = sludge / 2.5 * 8
    revenue, spend = sold * price, sold * cost
    profit = revenue - spend + block_income
    with l2:
        k = st.columns(3)
        with k[0]: kpi("Revenue", f"₹{revenue:,.0f}")
        with k[1]: kpi("Profit", f"₹{profit:,.0f}", f"incl. ₹{block_income:,.0f} from sludge blocks")
        with k[2]: kpi("Month at this pace", f"₹{profit*30:,.0f}")
        fig = go.Figure(go.Bar(x=["Revenue", "Costs", "Block sales", "Profit"], y=[revenue, spend, block_income, profit],
                               marker_color=[RIVER, ALERT, MARIGOLD, PLASTER]))
        plot(style(fig, 240))

    st.markdown("#### Message the truck operator")
    hrs = [h for h in HOURS if h not in RESTRICTED]
    m1, m2 = st.columns(2)
    with m1:
        h_pick = st.selectbox("Pickup hour", hrs, format_func=lambda h: f"{h:02d}:00", key="wa_h")
        who = st.text_input("Operator name", "Ramesh bhau")
    msg = (f"नमस्कार {who}, {v} कडून {h_pick:02d}:00 वाजता पेण बाहेरील यार्डवर लोड आहे. "
           f"कृपया वेळेत या, गल्लीत ट्रक उभा करू नका. / Hello {who}, pickup at the Pen yard at {h_pick:02d}:00. Please do not park in the lane.")
    with m2:
        st.text_area("Message", msg, height=120)
        st.link_button("Send on WhatsApp", "https://wa.me/?text=" + quote(msg))

# ===== Citizen desk =====
with tabs[1]:
    st.subheader("Citizen desk")
    st.caption("Check the road before you leave. Report problems in one tap.")
    x, y = st.columns([1, 1.2])
    with x:
        spot = st.selectbox("Where are you going through?", SPOTS)
        hour = st.slider("Time of travel", 6, 21, min(max(now.hour, 6), 21), format="%d:00")
        mm_on = st.toggle("Mati-Marga active in this zone", True)
        tr = 0 if mm_on else lane_trucks(hour)
        mins = transit(tr) + (SPOTS.index(spot) * 1.3 if not mm_on else 0)
        st.markdown(f"### {mins:.0f} min {chip(mins)}", unsafe_allow_html=True)
        st.caption(f"About {tr:.0f} trucks loading in the lane at this hour.")
    with y:
        hrs_ = list(range(6, 22))
        fig = go.Figure()
        fig.add_scatter(x=[f"{h}:00" for h in hrs_], y=[transit(lane_trucks(h)) for h in hrs_], name="Without Mati-Marga", line=dict(color=ALERT, width=3))
        fig.add_scatter(x=[f"{h}:00" for h in hrs_], y=[transit(0)] * len(hrs_), name="With Mati-Marga", line=dict(color=RIVER, width=3))
        plot(style(fig.update_layout(title="Best time to travel (minutes)"), 280))

    st.markdown("#### Pen traffic landscape (drag to rotate)")
    H_ = list(range(6, 22))
    Zt = [[transit(lane_trucks(h)) + j * 1.3 for h in H_] for j in range(len(SPOTS))]
    f3 = go.Figure()
    f3.add_surface(x=H_, y=list(range(len(SPOTS))), z=Zt, colorscale=[[0, RIVER], [.4, MARIGOLD], [1, ALERT]], name="Today", showscale=False)
    f3.add_surface(x=H_, y=list(range(len(SPOTS))), z=[[transit(0)] * len(H_)] * len(SPOTS), colorscale=[[0, RIVER], [1, RIVER]], opacity=.55, showscale=False)
    ax_ = dict(gridcolor="rgba(255,255,255,0.15)", color=PLASTER, backgroundcolor="rgba(0,0,0,0)")
    f3.update_layout(scene=dict(xaxis=dict(title="Hour", **ax_), zaxis=dict(title="Minutes", **ax_),
                                yaxis=dict(title="", tickvals=list(range(len(SPOTS))), ticktext=[x_.split()[0] for x_ in SPOTS], **ax_),
                                camera=dict(eye=dict(x=1.7, y=-1.7, z=.8))))
    plot(style(f3, 460))
    st.caption("Tall red ridge: today's jams. Flat teal sheet: the same roads with freight moved to the yard.")
    st.markdown("#### Report a problem")
    with st.form("report"):
        r1, r2 = st.columns(2)
        kind = r1.selectbox("What is wrong?", ["Clogged drain", "PoP dumping", "Truck blocking lane", "Overflow near school", "Other"])
        where = r2.selectbox("Where?", SPOTS)
        note = st.text_input("Details", placeholder="One line is enough")
        sent = st.form_submit_button("Send to Pen Nagar Parishad")
    if sent:
        tid = f"MM-{101 + len(st.session_state.tickets)}"
        st.session_state.tickets.loc[len(st.session_state.tickets)] = [tid, kind, where, note or "-", "Open", datetime.now()]
        save_app_data()
        st.success(f"Report {tid} received. Track it below.")
    t = st.session_state.tickets.copy(); t["Time"] = t.Time.dt.strftime("%d %b, %H:%M")
    table(t.iloc[::-1])

# ===== Officer console =====
with tabs[2]:
    st.subheader("Officer console")
    st.caption("For the Chief Officer, sanitation supervisor and Traffic Police.")
    T = st.session_state.tickets
    o = st.columns(4)
    with o[0]: kpi("Open reports", int((T.Status == "Open").sum()), "need a crew", bad=(T.Status == "Open").sum() > 0)
    with o[1]: kpi("In progress", int((T.Status == "In progress").sum()))
    with o[2]: kpi("Resolved", int((T.Status == "Resolved").sum()))
    overdue = sum((now - st.session_state.cleaned[w]).total_seconds() / 3600 > 9 for w in VENDORS)
    with o[3]: kpi("Traps overdue", f"{overdue} of {len(VENDORS)}", "workshops past safe window", bad=overdue > 0)
    p1, p2 = st.columns(2)
    with p1:
        st.markdown("#### Dispatch a crew")
        pending = T[T.Status != "Resolved"].ID.tolist()
        if pending:
            tid = st.selectbox("Report", pending)
            ns = st.radio("Set status", ["In progress", "Resolved"], horizontal=True)
            if st.button("Update report"):
                st.session_state.tickets.loc[st.session_state.tickets.ID == tid, "Status"] = ns
                save_app_data()
                st.toast(f"{tid} marked {ns}."); st.rerun()
        else:
            st.success("No open reports.")
    with p2:
        st.markdown("#### Workshop trap compliance")
        comp = pd.DataFrame({"Workshop": VENDORS, "Hours since cleaning": [round((now - st.session_state.cleaned[w]).total_seconds() / 3600, 1) for w in VENDORS]})
        fig = go.Figure(go.Bar(x=comp["Hours since cleaning"], y=comp.Workshop, orientation="h",
                               marker_color=[ALERT if h > 9 else RIVER for h in comp["Hours since cleaning"]]))
        fig.add_vline(x=9, line_dash="dot", line_color=PLASTER, annotation_text="safe window")
        plot(style(fig, 240))
    brief_fb = (f"Weekly brief: {len(T)} reports logged, {(T.Status=='Resolved').sum()} resolved, {overdue} traps overdue. "
                "Priority: clear the Kasar Ali drain near the school and enforce the yard slots at Antora junction.")
    if st.button("Write weekly brief"):
        st.info(ask_ai(f"Write a 5-line weekly brief for the Chief Officer from these tickets: {T.to_dict('records')}. Language: {lang}.", brief_fb))


# =====================================================================
# 3D STUDIO: river health + scale skyline (Three.js)
# These two are f-strings, so every JS brace is doubled.
# =====================================================================
_BTN = "<style>.b{background:#B6F500;color:#0B1230;border:0;border-radius:9px;padding:8px 12px;font-weight:700;cursor:pointer;box-shadow:0 3px 0 #6D9400}.b:active{transform:translateY(3px);box-shadow:none}body{margin:0}input[type=range]{accent-color:#B6F500;width:260px}</style>"
_THREE = '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>'
_BOX = 'style="position:relative;height:450px;background:linear-gradient(180deg,#2A2F8F,#070B1F 80%);border-radius:18px;overflow:hidden;font-family:Helvetica,Arial,sans-serif;border:1px solid rgba(255,255,255,.14)"'

RIVER3D = f"""
<div id="w" {_BOX}>
<div id="hud" style="position:absolute;left:14px;top:12px;color:#EAF0FF;font-size:14px;line-height:1.6;pointer-events:none"></div>
<div style="position:absolute;left:0;right:0;bottom:12px;text-align:center;color:#EAF0FF;font-size:13px">Workshops with a trap fitted: <b id="av">0%</b><br><input type="range" id="ad" min="0" max="100" value="0"></div>
</div>{_BTN}{_THREE}
<script>
const w=document.getElementById('w'),H=450;let W=Math.max(w.clientWidth,320);
const sc=new THREE.Scene(),cam=new THREE.PerspectiveCamera(45,W/H,.1,100);cam.position.set(0,9,14);cam.lookAt(0,0,0);
const rd=new THREE.WebGLRenderer({{antialias:true,alpha:true}});rd.setSize(W,H);rd.setPixelRatio(window.devicePixelRatio);w.appendChild(rd.domElement);rd.domElement.style.display='block';
const fit=()=>{{W=Math.max(w.clientWidth,320);rd.setSize(W,H);cam.aspect=W/H;cam.updateProjectionMatrix();}};
new ResizeObserver(fit).observe(w);fit();
sc.add(new THREE.AmbientLight(0xffffff,.8));const dl=new THREE.DirectionalLight(0xffffff,.8);dl.position.set(5,10,6);sc.add(dl);
const g=new THREE.Group();sc.add(g);
const box=(a,b,c,col,x,y,z)=>{{const m=new THREE.Mesh(new THREE.BoxGeometry(a,b,c),new THREE.MeshStandardMaterial({{color:col}}));m.position.set(x,y,z);g.add(m);return m;}};
box(30,.8,4,0x1F3A7A,0,-.3,6.6);box(30,.8,3.4,0x2A2F66,0,-.3,-6.6);
const OX=[];for(let i=0;i<6;i++){{const x=-10+i*4;OX.push(x);box(2,1.3,1.6,0xEAF0FF,x,.55,-7.2);box(2.3,.2,1.9,0xB6F500,x,1.3,-7.2);
 const c=new THREE.Mesh(new THREE.CylinderGeometry(.18,.18,1.2,10),new THREE.MeshStandardMaterial({{color:0x4A5590}}));c.rotation.x=Math.PI/2;c.position.set(x,.1,-5.9);g.add(c);}}
const geo=new THREE.PlaneGeometry(30,9.4,60,20);geo.rotateX(-Math.PI/2);const base=geo.attributes.position.array.slice();
const rmat=new THREE.MeshStandardMaterial({{color:0x22D3EE,transparent:true,opacity:.92,flatShading:true}});const river=new THREE.Mesh(geo,rmat);river.position.y=-.1;g.add(river);
const N=200,pos=new Float32Array(N*3),PA=[],pg=new THREE.BufferGeometry();pg.setAttribute('position',new THREE.BufferAttribute(pos,3));
g.add(new THREE.Points(pg,new THREE.PointsMaterial({{size:.2,color:0xffffff}})));
const rs=p=>{{p.o=OX[Math.floor(Math.random()*6)];p.x=p.o;p.z=-5.6;p.vx=.01+Math.random()*.03;p.vz=.015+Math.random()*.03;p.k=Math.random();}};
for(let i=0;i<N;i++){{const p={{}};rs(p);p.x+=Math.random()*8;p.z+=Math.random()*6;PA.push(p);}}
const fish=[];for(let i=0;i<8;i++){{const f=new THREE.Group();const b=new THREE.Mesh(new THREE.SphereGeometry(.28,10,8),new THREE.MeshStandardMaterial({{color:0xB6F500}}));b.scale.set(1.8,.7,.7);f.add(b);
 const t=new THREE.Mesh(new THREE.ConeGeometry(.2,.4,6),new THREE.MeshStandardMaterial({{color:0x9AC900}}));t.rotation.z=Math.PI/2;t.position.x=-.6;f.add(t);g.add(f);fish.push({{f,ph:i*.9,z:-3+i*.8,s:.015+Math.random()*.01,x:-12+i*3}});}}
const teal=new THREE.Color(0x22D3EE),milk=new THREE.Color(0xd9d3c4);let t=0,a=0,drag=false,lx=0;
const ad=document.getElementById('ad');ad.oninput=()=>{{a=ad.value/100;document.getElementById('av').textContent=ad.value+'%';}};
function frame(){{t+=.016;const P=1-.82*a,v=geo.attributes.position.array;
 for(let i=0;i<v.length;i+=3){{v[i+1]=Math.sin(base[i]*.6+t*1.5)*.12+Math.cos(base[i+2]*.8+t)*.08;}}geo.attributes.position.needsUpdate=true;geo.computeVertexNormals();
 rmat.color.copy(teal).lerp(milk,P);
 PA.forEach((p,i)=>{{if(p.k>P){{pos.set([0,-50,0],i*3);return;}}p.x+=p.vx;p.z+=p.vz;if(p.x>15||p.z>4)rs(p);pos.set([p.x,.05,p.z],i*3);}});pg.attributes.position.needsUpdate=true;
 let n=0;
 fish.forEach((k,i)=>{{const want=i<Math.round(a*8)?1:0;k.f.scale.setScalar(k.f.scale.x+(want-k.f.scale.x)*.05);if(want)n++;k.x+=k.s*2;if(k.x>13)k.x=-13;k.f.position.set(k.x,-.35,k.z+Math.sin(t+k.ph)*.5);k.f.rotation.y=Math.cos(t+k.ph)*.2;}});
 if(!drag)g.rotation.y=Math.sin(t*.15)*.12;
 document.getElementById('hud').innerHTML='<b style="font-size:20px;color:'+(P>.6?'#FF9DB0':'#9AF0FF')+'">River health: '+Math.round((1-P)*100)+'%</b><br>Sludge reaching river: '+(3000*45*P/1000).toFixed(0)+' t/day<br>Fish alive: '+n+' / 8<br><span style="font-size:11px;color:#9AA7D6">Basis: 3,000 workshops x 45 kg/day (blueprint)</span>';
 rd.render(sc,cam);requestAnimationFrame(frame);}}
const el=rd.domElement;el.style.touchAction='none';el.addEventListener('pointerdown',e=>{{drag=true;lx=e.clientX;}});addEventListener('pointerup',()=>drag=false);
el.addEventListener('pointermove',e=>{{if(drag){{g.rotation.y=Math.max(-1,Math.min(1,g.rotation.y+(e.clientX-lx)*.006));lx=e.clientX;}}}});
frame();
</script>"""

SKY3D = f"""
<div id="w" {_BOX}>
<div style="position:absolute;left:14px;top:12px;color:#EAF0FF;font-size:14px;pointer-events:none"><b style="font-size:18px">Setup cost vs monthly benefit</b><br><span style="color:#9AA7D6">Gold = setup (one-time) · Teal = monthly benefit · Hover a tower</span></div>
<div style="position:absolute;right:12px;top:12px;z-index:5"><button class="b" id="rp">Replay growth</button></div>
<div id="tip" style="position:absolute;display:none;background:#070B1F;color:#EAF0FF;border:1px solid #B6F500;border-radius:8px;padding:6px 10px;font-size:13px;pointer-events:none"></div>
</div>{_BTN}{_THREE}
<script>
const D=[['Pilot',8500,14000],['Town scale',450000,880000],['State scale',1800000,4500000]];
const w=document.getElementById('w'),H=450,tip=document.getElementById('tip');let W=Math.max(w.clientWidth,320);
const sc=new THREE.Scene(),cam=new THREE.PerspectiveCamera(42,W/H,.1,100);cam.position.set(0,6.5,13);cam.lookAt(0,1.6,0);
const rd=new THREE.WebGLRenderer({{antialias:true,alpha:true}});rd.setSize(W,H);rd.setPixelRatio(window.devicePixelRatio);w.appendChild(rd.domElement);rd.domElement.style.display='block';
const fit=()=>{{W=Math.max(w.clientWidth,320);rd.setSize(W,H);cam.aspect=W/H;cam.updateProjectionMatrix();}};
new ResizeObserver(fit).observe(w);fit();
sc.add(new THREE.AmbientLight(0xffffff,.75));const dl=new THREE.DirectionalLight(0xffffff,.9);dl.position.set(5,10,7);sc.add(dl);
const g=new THREE.Group();sc.add(g);
const plat=new THREE.Mesh(new THREE.CylinderGeometry(8.5,8.8,.4,48),new THREE.MeshStandardMaterial({{color:0x121A3F}}));plat.position.y=-.2;g.add(plat);
const hf=v=>Math.max(.4,(Math.log10(v)-3)*1.25),T=[],L=[];
D.forEach((d,i)=>{{[[1,0xB6F500,-.95],[2,0x22D3EE,.95]].forEach(([k,c,dx])=>{{const h=hf(d[k]);const m=new THREE.Mesh(new THREE.BoxGeometry(1.5,h,1.5),new THREE.MeshStandardMaterial({{color:c}}));
 m.userData={{h,txt:d[0]+(k==1?' setup: ':' benefit/month: ')+'₹'+d[k].toLocaleString('en-IN')}};m.position.set((i-1)*5.2+dx,0,0);m.scale.y=.01;g.add(m);T.push(m);
 const e=new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry),new THREE.LineBasicMaterial({{color:0xffffff,transparent:true,opacity:.35}}));m.add(e);}});
 const l=document.createElement('div');l.textContent=d[0];l.style.cssText='position:absolute;color:#EAF0FF;font-weight:700;font-size:14px;transform:translate(-50%,0);pointer-events:none';w.appendChild(l);L.push([l,new THREE.Vector3((i-1)*5.2,-.7,2)]);}});
let t=0,drag=false,lx=0,gs=0;
const ray=new THREE.Raycaster(),mv=new THREE.Vector2(9,9);
function frame(){{t+=.016;gs=Math.min(1,gs+.012);const e=1-Math.pow(1-gs,3);
 T.forEach((m,i)=>{{m.scale.y=Math.max(.01,e);m.position.y=m.userData.h*m.scale.y/2;}});
 if(!drag)g.rotation.y=Math.sin(t*.2)*.35;
 L.forEach(([l,p])=>{{const v=p.clone();g.localToWorld(v);v.project(cam);l.style.left=((v.x+1)/2*W)+'px';l.style.top=((1-v.y)/2*H)+'px';}});
 ray.setFromCamera(mv,cam);const hit=ray.intersectObjects(T)[0];T.forEach(m=>m.material.emissive&&m.material.emissive.setHex(0));
 if(hit){{hit.object.material.emissive.setHex(0x333333);tip.style.display='block';tip.textContent=hit.object.userData.txt;}}else tip.style.display='none';
 rd.render(sc,cam);requestAnimationFrame(frame);}}
const el=rd.domElement;el.style.touchAction='none';
el.addEventListener('pointerdown',e=>{{drag=true;lx=e.clientX;}});addEventListener('pointerup',()=>drag=false);
el.addEventListener('pointermove',e=>{{const r=el.getBoundingClientRect();mv.set(((e.clientX-r.left)/r.width)*2-1,-((e.clientY-r.top)/r.height)*2+1);tip.style.left=(e.clientX-r.left+12)+'px';tip.style.top=(e.clientY-r.top+12)+'px';
 if(drag){{g.rotation.y+=(e.clientX-lx)*.008;lx=e.clientX;}}}});
document.getElementById('rp').onclick=()=>gs=0;
frame();
</script>"""

with tabs[9]:
    st.subheader("3D Studio")
    st.markdown("#### Bhogavati river: what trap adoption does")
    st.caption("Slide the adoption bar inside the scene. Watch the water clear and the fish return.")
    components.html(RIVER3D, height=470)
    st.markdown("#### Scale skyline: cost against benefit")
    st.caption("Heights use a log scale because the stages differ by hundreds of times. Figures are from the blueprint's finance table.")
    components.html(SKY3D, height=470)


components.html("""<script>
try{const d=window.parent.document;
if(!d.getElementById('mm-glow')){
 const g=d.createElement('div');g.id='mm-glow';g.style.cssText='position:fixed;left:0;top:0;width:420px;height:420px;border-radius:50%;pointer-events:none;z-index:0;background:radial-gradient(circle,rgba(124,92,255,.16),transparent 65%);transform:translate(-999px,-999px);';d.body.appendChild(g);
 const S='.kpi,.task,.card,.stage';
 d.addEventListener('mousemove',e=>{g.style.transform='translate('+(e.clientX-210)+'px,'+(e.clientY-210)+'px)';const el=e.target.closest&&e.target.closest(S);
  if(el){const r=el.getBoundingClientRect();el.style.setProperty('--mx',(e.clientX-r.left)+'px');el.style.setProperty('--my',(e.clientY-r.top)+'px');
   const rx=((e.clientY-r.top)/r.height-.5)*-9,ry=((e.clientX-r.left)/r.width-.5)*9;el.style.transform='perspective(900px) rotateX('+rx+'deg) rotateY('+ry+'deg) translateY(-4px)';}});
 d.addEventListener('mouseout',e=>{const el=e.target.closest&&e.target.closest(S);if(el&&!el.contains(e.relatedTarget))el.style.transform='';});
}}catch(e){}
</script>""", height=0)
