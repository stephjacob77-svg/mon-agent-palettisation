import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert WMS v9.0 - Croisement Master", layout="wide")

if 'db_refs' not in st.session_state:
    st.session_state.db_refs = pd.DataFrame(columns=["Référence", "L", "W", "H"])

# --- MOTEUR D'OPTIMISATION & CROISEMENT ---

def compute_layer(W_pal, L_pal, c_L, c_W):
    """Calcule la meilleure disposition possible (Tetris)"""
    def fill(W, L, cl, cw):
        plan = []
        nx, ny = int(W // cl), int(L // cw)
        for i in range(nx):
            for j in range(ny):
                plan.append({'x': i * cl, 'y': j * cw, 'w': cl, 'h': cw})
        # Remplissage résiduel X
        rx = W - (nx * cl)
        if rx >= cw:
            for j in range(int(L // cl)):
                plan.append({'x': nx * cl, 'y': j * cl, 'w': cw, 'h': cl})
        # Remplissage résiduel Y
        ry = L - (ny * cw)
        if ry >= cl:
            for i in range(int((nx * cl) // cw)):
                plan.append({'x': i * cw, 'y': ny * cw, 'w': cw, 'h': cl})
        return plan

    # Test des deux orientations de base
    p1 = fill(W_pal, L_pal, c_L, c_W)
    p2 = fill(W_pal, L_pal, c_W, c_L)
    return p1 if len(p1) >= len(p2) else p2

def get_mirrored_plan(plan, W_pal, L_pal):
    """Génère la couche croisée par symétrie centrale"""
    mirrored = []
    for p in plan:
        mirrored.append({
            'x': W_pal - p['x'] - p['w'],
            'y': L_pal - p['y'] - p['h'],
            'w': p['w'],
            'h': p['h']
        })
    return mirrored

# --- DESSIN 3D ---

def draw_box(fig, x0, x1, y0, y1, z0, z1, color, line_color="black"):
    fig.add_trace(go.Mesh3d(
        x=[x0, x1, x1, x0, x0, x1, x1, x0], y=[y0, y0, y1, y1, y0, y0, y1, y1], z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=1, flatshading=True, showlegend=False
    ))
    # Arêtes pour bien voir le croisement
    lx = [x0, x1, x1, x0, x0, None, x0, x1, x1, x0, x0, None, x0, x0, None, x1, x1, None, x1, x1, None, x0, x0]
    ly = [y0, y0, y1, y1, y0, None, y0, y0, y1, y1, y0, None, y0, y0, None, y0, y0, None, y1, y1, None, y1, y1]
    lz = [z0, z0, z0, z0, z0, None, z1, z1, z1, z1, z1, None, z0, z1, None, z0, z1, None, z0, z1, None, z0, z1]
    fig.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode='lines', line=dict(color=line_color, width=2), showlegend=False))

# --- INTERFACE ---

st.sidebar.title("🏭 Expert WMS v9.0")
if st.sidebar.button("➕ Ajouter Colis 300x200x150"):
    new_item = pd.DataFrame([{"Référence":"Test 300x200", "L":300, "W":200, "H":150}])
    st.session_state.db_refs = pd.concat([st.session_state.db_refs, new_item]).drop_duplicates()

if st.session_state.db_refs.empty:
    st.info("Utilisez le bouton à gauche pour charger le format test.")
    st.stop()

ref = st.sidebar.selectbox("Article", st.session_state.db_refs["Référence"].tolist())
w_p = st.sidebar.selectbox("Largeur Palette", [800, 1000])
h_m = st.sidebar.number_input("Hauteur Max", value=1000)

item = st.session_state.db_refs[st.session_state.db_refs["Référence"] == ref].iloc[0]

# CALCUL DES DEUX PLANS (A et B)
plan_a = compute_layer(w_p, 1200, item['L'], item['W'])
plan_b = get_mirrored_plan(plan_a, w_p, 1200)
nb_c = int((h_m - 150) // item['H'])

st.header(f"📦 Schéma de Croisement : {len(plan_a)} colis/couche")

c1, c2 = st.columns(2)

with c1:
    st.subheader("Vues 2D : Alternance")
    # Couche A
    f2a = go.Figure()
    f2a.add_trace(go.Scatter(x=[0,w_p,w_p,0,0], y=[0,0,1200,1200,0], fill="toself", fillcolor="silver"))
    for p in plan_a:
        f2a.add_trace(go.Scatter(x=[p['x'],p['x']+p['w'],p['x']+p['w'],p['x'],p['x']], y=[p['y'],p['y'],p['y']+p['h'],p['y']+p['h'],p['y']], fill="toself", line=dict(color="white")))
    f2a.update_layout(title="Couche IMPAIRE (A)", yaxis=dict(scaleanchor="x"), showlegend=False, height=400)
    st.plotly_chart(f2a)

    # Couche B
    f2b = go.Figure()
    f2b.add_trace(go.Scatter(x=[0,w_p,w_p,0,0], y=[0,0,1200,1200,0], fill="toself", fillcolor="silver"))
    for p in plan_b:
        f2b.add_trace(go.Scatter(x=[p['x'],p['x']+p['w'],p['x']+p['w'],p['x'],p['x']], y=[p['y'],p['y'],p['y']+p['h'],p['y']+p['h'],p['y']], fill="toself", line=dict(color="white")))
    f2b.update_layout(title="Couche PAIRE (B) - Inversée", yaxis=dict(scaleanchor="x"), showlegend=False, height=400)
    st.plotly_chart(f2b)

with c2:
    st.subheader("Rendu 3D Croisé")
    f3 = go.Figure()
    # Support bois
    draw_box(f3, 0, w_p, 0, 1200, 0, 150, "peru")
    # Empilage alterné
    for k in range(nb_c):
        current_plan = plan_a if k % 2 == 0 else plan_b
        color = "royalblue" if k % 2 == 0 else "crimson"
        z0 = 150 + (k * item['H'])
        for p in current_plan:
            draw_box(f3, p['x'], p['x']+p['w'], p['y'], p['y']+p['h'], z0, z0+item['H'], color)
    f3.update_layout(scene=dict(aspectmode='data'), height=800, margin=dict(l=0,r=0,b=0,t=0))
    st.plotly_chart(f3, use_container_width=True)
