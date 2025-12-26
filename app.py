import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert WMS Pro v9.5", layout="wide")

if 'db_refs' not in st.session_state:
    st.session_state.db_refs = pd.DataFrame([{"Référence":"BOX_300x200", "L":300, "W":200, "H":150, "P":25.0}])

# --- MOTEUR D'OPTIMISATION ---
def get_optimal_layer(W_pal, L_pal, cl, cw):
    def strategy(W, L, c_l, c_w):
        plan = []
        nx, ny = int(W // c_l), int(L // c_w)
        for i in range(nx):
            for j in range(ny): plan.append({'x': i * c_l, 'y': j * c_w, 'w': c_l, 'h': c_w})
        rx, ry = W - (nx * c_l), L - (ny * c_w)
        if rx >= c_w:
            for j in range(int(L // c_l)): plan.append({'x': nx * c_l, 'y': j * c_l, 'w': c_w, 'h': c_l})
        if ry >= c_l:
            for i in range(int((nx * c_l) // c_w)): plan.append({'x': i * c_w, 'y': ny * c_w, 'w': c_w, 'h': c_l})
        return plan
    s1, s2 = strategy(W_pal, L_pal, cl, cw), strategy(W_pal, L_pal, cw, cl)
    return s1 if len(s1) >= len(s2) else s2

def get_crossed_layer(plan, W_pal, L_pal):
    return [{'x': W_pal - p['x'] - p['w'], 'y': L_pal - p['y'] - p['h'], 'w': p['w'], 'h': p['h']} for p in plan]

# --- FONCTIONS GRAPHIQUES ---
def draw_box(fig, x0, x1, y0, y1, z0, z1, color, opacity=1.0, line_width=1):
    fig.add_trace(go.Mesh3d(
        x=[x0, x1, x1, x0, x0, x1, x1, x0], y=[y0, y0, y1, y1, y0, y0, y1, y1], z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=opacity, flatshading=True, showlegend=False
    ))
    lx = [x0, x1, x1, x0, x0, None, x0, x1, x1, x0, x0, None, x0, x0, None, x1, x1, None, x1, x1, None, x0, x0]
    ly = [y0, y0, y1, y1, y0, None, y0, y0, y1, y1, y0, None, y0, y0, None, y0, y0, None, y1, y1, None, y1, y1]
    lz = [z0, z0, z0, z0, z0, None, z1, z1, z1, z1, z1, None, z0, z1, None, z0, z1, None, z0, z1, None, z0, z1]
    fig.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode='lines', line=dict(color='black', width=line_width), showlegend=False))

def draw_real_pallet(fig, x_off, w_p, l_p, z_off, color="#8D6E63"):
    for sx in [0, w_p/2-50, w_p-100]: draw_box(fig, x_off+sx, x_off+sx+100, 0, l_p, z_off, z_off+25, color)
    for dx in [0, w_p/2-50, w_p-100]:
        for dy in [0, l_p/2-50, l_p-100]: draw_box(fig, x_off+dx, x_off+dx+100, dy, dy+100, z_off+25, z_off+125, color)
    draw_box(fig, x_off, x_off+w_p, 0, l_p, z_off+125, z_off+150, color)

# --- UI & LOGIQUE MÉTIER ---
st.sidebar.title("🏭 Expert WMS v9.5")

# 1. Sélection Format et Type
fmt_pal = st.sidebar.selectbox("Format Palette", ["800x1200 (EURO)", "1000x1200 (VMF/STD)"])
w_p = 800 if "800" in fmt_pal else 1000

if w_p == 800:
    type_p = st.sidebar.selectbox("Type", ["EUROPE (Lourd)", "LÉGÈRE (800)"])
    p_critique = 600
else:
    type_p = st.sidebar.selectbox("Type", ["VMF (Lourd)", "LÉGÈRE (1000)"])
    p_critique = 800

ref_sel = st.sidebar.selectbox("Article", st.session_state.db_refs["Référence"].tolist())
capa_lisse = st.sidebar.number_input("Capacité Lisse (kg)", value=3000)
h_rack_max = st.sidebar.number_input("Hauteur Max (mm)", value=1800)

item = st.session_state.db_refs[st.session_state.db_refs["Référence"] == ref_sel].iloc[0]

# Calculs
plan_a = get_optimal_layer(w_p, 1200, item['L'], item['W'])
plan_b = get_crossed_layer(plan_a, w_p, 1200)
nb_c = int((h_rack_max - 150) // item['H'])
poids_pal = int(len(plan_a) * nb_c * item['P'])
nb_pal_lisse = 2700 // w_p
poids_total_lisse = poids_pal * nb_pal_lisse

# --- ALERTES SÉCURITÉ ---
st.header(f"📦 Analyse Technique : {ref_sel}")
c_kpi1, c_kpi2, c_kpi3 = st.columns(3)

with c_kpi1:
    if poids_pal > p_critique and "LÉGÈRE" in type_p:
        st.error(f"🛑 SUPPORT INSUFFISANT : {poids_pal}kg nécessite une palette Lourde.")
    else:
        st.success(f"✅ Support {type_p} validé.")

with c_kpi2:
    if poids_total_lisse > capa_lisse:
        st.error(f"⚠️ SURCHARGE LISSE : {poids_total_lisse}kg / {capa_lisse}kg")
    else:
        st.metric("Charge Lisse", f"{poids_total_lisse} kg", f"{capa_lisse - poids_total_lisse} kg marge")

with c_kpi3:
    st.metric("Colis / Palette", len(plan_a) * nb_c, f"{len(plan_a)} par couche")

tabs = st.tabs(["🏗️ Rendu 3D Avancé", "📋 Plans 2D & Étiquette"])

with tabs[0]:
    v1, v2 = st.columns(2)
    with v1:
        st.subheader(f"Pose sur {w_p}x1200")
        f1 = go.Figure()
        draw_real_pallet(f1, 0, w_p, 1200, 0)
        for k in range(nb_c):
            p, col = (plan_a, "#1E88E5") if k % 2 == 0 else (plan_b, "#E53935")
            for b in p: draw_box(f1, b['x'], b['x']+b['w'], b['y'], b['y']+b['h'], 150+(k*item['H']), 150+((k+1)*item['H']), col)
        f1.update_layout(scene=dict(aspectmode='data'), height=600, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(f1, use_container_width=True)
        
    with v2:
        st.subheader("Contrôle Alvéole")
        f2 = go.Figure()
        # Rack
        lisse_col = "red" if poids_total_lisse > capa_lisse else "orange"
        for px in [-100, 2700]:
            for py in [0, 1100]: draw_box(f2, px, px+100, py, py+100, -150, h_rack_max+150, "royalblue")
        draw_box(f2, 0, 2700, 0, 100, -150, 0, lisse_col) # Lisse
        for i in range(int(nb_pal_lisse)):
            x_pos = i * (w_p + 50) + 25
            draw_real_pallet(f2, x_pos, w_p, 1200, 0)
            draw_box(f2, x_pos+10, x_pos+w_p-10, 10, 1190, 150, 150+(nb_c*item['H']), "rgba(33, 150, 243, 0.4)")
        f2.update_layout(scene=dict(aspectmode='data'), height=600, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(f2, use_container_width=True)

with tabs[1]:
    st.subheader("Plans de Pose & Étiquette")
    
    c2d1, c2d2 = st.columns(2)
    def fig2d(plan, col, title):
        f = go.Figure()
        f.add_trace(go.Scatter(x=[0,w_p,w_p,0,0], y=[0,0,1200,1200,0], fill="toself", fillcolor="#D7CCC8", line=dict(color="black")))
        for p in plan: f.add_trace(go.Scatter(x=[p['x'],p['x']+p['w'],p['x']+p['w'],p['x'],p['x']], y=[p['y'],p['y'],p['y']+p['h'],p['y']+p['h'],p['y']], fill="toself", fillcolor=col, line=dict(color="white")))
        f.update_layout(title=title, yaxis=dict(scaleanchor="x"), showlegend=False, height=350)
        return f
    c2d1.plotly_chart(fig2d(plan_a, "#1E88E5", "Couche A (Impaire)"), use_container_width=True)
    c2d2.plotly_chart(fig2d(plan_b, "#E53935", "Couche B (Paire)"), use_container_width=True)
    
    st.markdown(f"""<div style="border:4px solid black; padding:15px; background:white; color:black; font-family:monospace;">
        <table style="width:100%"><tr><td><h2>PALETTE : {ref_sel}</h2></td><td style="text-align:right"><h2>POIDS : {poids_pal} KG</h2></td></tr></table>
        <hr>
        <b>FORMAT : {fmt_pal} | TYPE : {type_p}</b><br>
        <b>COLIS : {len(plan_a)*nb_c} (Couches: {nb_c} x {len(plan_a)})</b><br>
        <b>HAUTEUR TOTALE : {150+(nb_c*item['H'])} mm</b></div>""", unsafe_allow_html=True)
