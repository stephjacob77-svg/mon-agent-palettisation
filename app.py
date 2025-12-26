import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert WMS Pro v9.1", layout="wide")

if 'db_refs' not in st.session_state:
    st.session_state.db_refs = pd.DataFrame([{"Référence":"Standard Box", "L":300, "W":200, "H":150, "P":10.0}])

# --- MOTEUR D'OPTIMISATION INDUSTRIEL ---

def get_optimal_layer(W_pal, L_pal, cl, cw):
    """Calcule le plan maximal en testant les deux sens de pose"""
    def strategy(W, L, c_l, c_w):
        plan = []
        nx, ny = int(W // c_l), int(L // c_w)
        for i in range(nx):
            for j in range(ny):
                plan.append({'x': i * c_l, 'y': j * c_w, 'w': c_l, 'h': c_w})
        # Remplissage des chutes par rotation (Tetris)
        rx = W - (nx * c_l)
        if rx >= c_w:
            for j in range(int(L // c_l)):
                plan.append({'x': nx * c_l, 'y': j * c_l, 'w': c_w, 'h': c_l})
        ry = L - (ny * c_w)
        if ry >= c_l:
            for i in range(int((nx * c_l) // c_w)):
                plan.append({'x': i * c_w, 'y': ny * c_w, 'w': c_w, 'h': c_l})
        return plan

    s1 = strategy(W_pal, L_pal, cl, cw)
    s2 = strategy(W_pal, L_pal, cw, cl)
    return s1 if len(s1) >= len(s2) else s2

def get_crossed_layer(plan, W_pal, L_pal):
    """Crée l'effet de croisement par inversion des axes (Effet miroir)"""
    return [{'x': W_pal - p['x'] - p['w'], 'y': L_pal - p['y'] - p['h'], 'w': p['w'], 'h': p['h']} for p in plan]

# --- FONCTION DE DESSIN 3D ---

def draw_box(fig, x0, x1, y0, y1, z0, z1, color, line_width=2):
    fig.add_trace(go.Mesh3d(
        x=[x0, x1, x1, x0, x0, x1, x1, x0], y=[y0, y0, y1, y1, y0, y0, y1, y1], z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=1, flatshading=True, showlegend=False
    ))
    lx = [x0, x1, x1, x0, x0, None, x0, x1, x1, x0, x0, None, x0, x0, None, x1, x1, None, x1, x1, None, x0, x0]
    ly = [y0, y0, y1, y1, y0, None, y0, y0, y1, y1, y0, None, y0, y0, None, y0, y0, None, y1, y1, None, y1, y1]
    lz = [z0, z0, z0, z0, z0, None, z1, z1, z1, z1, z1, None, z0, z1, None, z0, z1, None, z0, z1, None, z0, z1]
    fig.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode='lines', line=dict(color='black', width=line_width), showlegend=False))

# --- INTERFACE UTILISATEUR ---

st.sidebar.title("🚀 WMS RENAISSANCE v9.1")
ref_sel = st.sidebar.selectbox("Article", st.session_state.db_refs["Référence"].tolist())
fmt_pal = st.sidebar.radio("Format Palette", ["800 x 1200 (Europe)", "1000 x 1200 (VMF)"])
h_max = st.sidebar.slider("Hauteur de dépose max (mm)", 500, 2500, 1800)

item = st.session_state.db_refs[st.session_state.db_refs["Référence"] == ref_sel].iloc[0]
w_p = 800 if "800" in fmt_pal else 1000

# Calculs
plan_impaire = get_optimal_layer(w_p, 1200, item['L'], item['W'])
plan_paire = get_crossed_layer(plan_impaire, w_p, 1200)
nb_couches = int((h_max - 150) // item['H'])

# --- AFFICHAGE DES MÉTRIQUES ---
st.header(f"Analyse Logistique : {ref_sel} ({item['L']}x{item['W']}x{item['H']})")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Colis / Couche", len(plan_impaire))
m2.metric("Total Colis", len(plan_impaire) * nb_couches)
m3.metric("Poids Charge", f"{len(plan_impaire) * nb_couches * item['P']} kg")
h_fin = 150 + (nb_couches * item['H'])
m4.metric("Garde d'air", f"{h_max - h_fin} mm")

# --- VUES ---
t1, t2 = st.tabs(["📊 Simulation 3D & Rack", "📋 Plans de Pose 2D"])

with t1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Rendu Palette Croisée")
        
        f3 = go.Figure()
        # Palette bois
        draw_box(f3, 0, w_p, 0, 1200, 0, 150, "#8D6E63")
        # Empilage
        for k in range(nb_couches):
            p_actuel = plan_impaire if k % 2 == 0 else plan_paire
            color = "#2196F3" if k % 2 == 0 else "#EF5350"
            z0 = 150 + (k * item['H'])
            for box in p_actuel:
                draw_box(f3, box['x'], box['x']+box['w'], box['y'], box['y']+box['h'], z0, z0+item['H'], color)
        f3.update_layout(scene=dict(aspectmode='data'), height=700, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(f3, use_container_width=True)
    
    with c2:
        st.subheader("Vue Alvéole")
        f_rack = go.Figure()
        # Montants
        for px in [-100, 2700]:
            for py in [0, 1100]: draw_box(f_rack, px, px+100, py, py+100, -100, h_max+200, "royalblue")
        # Lisse
        draw_box(f_rack, 0, 2700, 0, 100, -50, 0, "orange")
        # Palette simplifiée dans le rack
        for i in range(2700 // w_p):
            x_offset = i * (w_p + 50)
            draw_box(f_rack, x_offset, x_offset+w_p, 0, 1200, 0, 150, "#8D6E63")
            draw_box(f_rack, x_offset+20, x_offset+w_p-20, 20, 1180, 150, h_fin, "rgba(33, 150, 243, 0.5)")
        f_rack.update_layout(scene=dict(aspectmode='data'), height=700, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(f_rack, use_container_width=True)

with t2:
    st.subheader("Instructions de Montage")
    c2d1, c2d2 = st.columns(2)
    
    def fig_2d(plan, title, col):
        f = go.Figure()
        f.add_trace(go.Scatter(x=[0,w_p,w_p,0,0], y=[0,0,1200,1200,0], fill="toself", fillcolor="silver", line=dict(color="black")))
        for p in plan:
            f.add_trace(go.Scatter(x=[p['x'],p['x']+p['w'],p['x']+p['w'],p['x'],p['x']], y=[p['y'],p['y'],p['y']+p['h'],p['y']+p['h'],p['y']], fill="toself", fillcolor=col, line=dict(color="white")))
        f.update_layout(title=title, yaxis=dict(scaleanchor="x"), showlegend=False)
        return f

    c2d1.plotly_chart(fig_2d(plan_impaire, "Couches 1, 3, 5...", "#2196F3"), use_container_width=True)
    c2d2.plotly_chart(fig_2d(plan_paire, "Couches 2, 4, 6...", "#EF5350"), use_container_width=True)
