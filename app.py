import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert WMS v8.8 - Tetris Mode", layout="wide")

if 'db_refs' not in st.session_state:
    st.session_state.db_refs = pd.DataFrame(columns=["Référence", "L", "W", "H", "P"])

# --- MOTEUR D'OPTIMISATION TETRIS (Étape validée) ---

def get_complex_plan(W, L, cl, cw):
    """
    Calcule le plan de palettisation optimal en testant les rotations 
    pour remplir les zones résiduelles (Mode Tetris).
    """
    plan = []
    
    # 1. Remplissage principal (Orientation Standard)
    nx = int(W // cl)
    ny = int(L // cw)
    
    for i in range(nx):
        for j in range(ny):
            plan.append({'x': i * cl, 'y': j * cw, 'w': cl, 'h': cw})
    
    # 2. Remplissage résiduel en X (Rotation sur la bande latérale)
    reste_x = W - (nx * cl)
    if reste_x >= cw:
        nb_colis_rot_x = int(L // cl)
        for j in range(nb_colis_rot_x):
            plan.append({'x': nx * cl, 'y': j * cl, 'w': cw, 'h': cl})

    # 3. Remplissage résiduel en Y (Rotation sur la bande supérieure)
    reste_y = L - (ny * cw)
    if reste_y >= cl:
        # On remplit l'espace au-dessus des colis principaux
        nb_colis_rot_y = int((nx * cl) // cw)
        for i in range(nb_colis_rot_y):
            plan.append({'x': i * cw, 'y': ny * cw, 'w': cw, 'h': cl})
            
    return plan

# --- FONCTIONS DE DESSIN ---

def draw_box(fig, x0, x1, y0, y1, z0, z1, color, opacity=1.0):
    fig.add_trace(go.Mesh3d(
        x=[x0, x1, x1, x0, x0, x1, x1, x0], y=[y0, y0, y1, y1, y0, y0, y1, y1], z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=opacity, flatshading=True, showlegend=False
    ))
    lx = [x0, x1, x1, x0, x0, None, x0, x1, x1, x0, x0, None, x0, x0, None, x1, x1, None, x1, x1, None, x0, x0]
    ly = [y0, y0, y1, y1, y0, None, y0, y0, y1, y1, y0, None, y0, y0, None, y0, y0, None, y1, y1, None, y1, y1]
    lz = [z0, z0, z0, z0, z0, None, z1, z1, z1, z1, z1, None, z0, z1, None, z0, z1, None, z0, z1, None, z0, z1]
    fig.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode='lines', line=dict(color='black', width=1), showlegend=False))

def draw_pro_pallet(fig, x0, w_pal, l_pal, z0, color="#8D6E63"):
    """Palette réaliste (150mm de hauteur)"""
    for off_x in [0, w_pal/2 - 50, w_pal - 100]:
        draw_box(fig, x0+off_x, x0+off_x+100, 0, l_pal, z0, z0+25, color)
    for dx in [0, w_pal/2 - 50, w_pal - 100]:
        for dy in [0, l_pal/2 - 50, l_pal - 100]:
            draw_box(fig, x0+dx, x0+dx+100, dy, dy+100, z0+25, z0+125, color)
    draw_box(fig, x0, x0+w_pal, 0, l_pal, z0+125, z0+150, color)

def draw_2d_layer(plan, w_pal, l_pal, color, title):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, w_pal, w_pal, 0, 0], y=[0, 0, l_pal, l_pal, 0], fill="toself", fillcolor="#D7CCC8", line=dict(color="#5D4037", width=2)))
    for p in plan:
        fig.add_trace(go.Scatter(x=[p['x'], p['x']+p['w'], p['x']+p['w'], p['x'], p['x']], y=[p['y'], p['y'], p['y']+p['h'], p['y']+p['h'], p['y']], fill="toself", fillcolor=color, line=dict(color="white", width=1), showlegend=False))
    fig.update_layout(title=title, xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"), height=350)
    return fig

# --- LOGIQUE D'APPLICATION ---

st.sidebar.title("🏭 Expert WMS v8.8")
mode = st.sidebar.radio("Navigation", ["Base Articles", "Optimisation Tetris"])

if mode == "Base Articles":
    st.header("📋 Référentiel Articles")
    with st.form("add_item"):
        c1, c2, c3, c4, c5 = st.columns([2,1,1,1,1])
        n = c1.text_input("Référence")
        l = c2.number_input("Long (mm)", value=400)
        w = c3.number_input("Larg (mm)", value=300)
        h = c4.number_input("Haut (mm)", value=250)
        p = c5.number_input("Poids (kg)", value=10.0)
        if st.form_submit_button("Ajouter"):
            st.session_state.db_refs = pd.concat([st.session_state.db_refs, pd.DataFrame([{"Référence":n,"L":l,"W":w,"H":h,"P":p}])]).drop_duplicates()
    st.dataframe(st.session_state.db_refs, use_container_width=True)

else:
    if st.session_state.db_refs.empty:
        st.warning("Veuillez d'abord ajouter un article.")
        st.stop()

    with st.sidebar:
        ref_sel = st.selectbox("Sélectionner Article", st.session_state.db_refs["Référence"].tolist())
        w_pal = st.radio("Format Palette", [800, 1000], index=0)
        l_lisse = st.selectbox("Longueur Lisse", [2700, 3600, 1350])
        h_utile = st.number_input("Hauteur Utile Rack", value=1800)

    item = st.session_state.db_refs[st.session_state.db_refs["Référence"] == ref_sel].iloc[0]
    
    # Appel du moteur Tetris
    plan_a = get_complex_plan(w_pal, 1200, item['L'], item['W'])
    
    # Calcul des couches
    nb_pal = l_lisse // w_pal
    n_h = (h_utile - 150) // item['H']
    couches = int(max(1, n_h))
    
    st.header(f"📦 Analyse Tetris : {ref_sel}")
    st.info(f"Nombre de colis par couche : **{len(plan_a)}** (Optimisé avec rotations)")

    # Affichage 3D
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Visualisation 3D")
        f1 = go.Figure()
        draw_pro_pallet(f1, 0, w_pal, 1200, 0)
        for k in range(couches):
            color = "#2196F3" if k % 2 == 0 else "#EF5350"
            for p in plan_a:
                z0 = 150 + (k * item['H'])
                # Alternance pour le rendu
                fx, fy = (w_pal-p['x']-p['w'], 1200-p['y']-p['h']) if k % 2 == 1 else (p['x'], p['y'])
                draw_box(f1, fx, fx+p['w'], fy, fy+p['h'], z0, z0+item['H'], color)
        f1.update_layout(scene=dict(aspectmode='data'), height=600, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(f1, use_container_width=True)

    with c2:
        st.subheader("Plan de Pose (2D)")
        st.plotly_chart(draw_2d_layer(plan_a, w_pal, 1200, "#2196F3", "Couche Type"), use_container_width=True)
        st.write(f"**Total Colis par Palette :** {len(plan_a) * couches}")
        st.write(f"**Hauteur Totale :** {150 + (couches * item['H'])} mm")
