import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert WMS Pro v9.2", layout="wide")

# Initialisation de la base si vide
if 'db_refs' not in st.session_state:
    st.session_state.db_refs = pd.DataFrame([
        {"Référence": "CARTON_STD_A", "L": 300, "W": 200, "H": 150, "P": 8.5},
        {"Référence": "CARTON_LOURD_B", "L": 400, "W": 300, "H": 250, "P": 15.0}
    ])

# --- MOTEUR D'OPTIMISATION ---

def get_optimal_layer(W_pal, L_pal, cl, cw):
    def strategy(W, L, c_l, c_w):
        plan = []
        nx, ny = int(W // c_l), int(L // c_w)
        for i in range(nx):
            for j in range(ny):
                plan.append({'x': i * c_l, 'y': j * c_w, 'w': c_l, 'h': c_w})
        # Remplissage Tetris des zones mortes
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
    return [{'x': W_pal - p['x'] - p['w'], 'y': L_pal - p['y'] - p['h'], 'w': p['w'], 'h': p['h']} for p in plan]

# --- DESSIN 3D ---

def draw_box(fig, x0, x1, y0, y1, z0, z1, color, line_width=1):
    fig.add_trace(go.Mesh3d(
        x=[x0, x1, x1, x0, x0, x1, x1, x0], y=[y0, y0, y1, y1, y0, y0, y1, y1], z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=1, flatshading=True, showlegend=False
    ))
    lx = [x0, x1, x1, x0, x0, None, x0, x1, x1, x0, x0, None, x0, x0, None, x1, x1, None, x1, x1, None, x0, x0]
    ly = [y0, y0, y1, y1, y0, None, y0, y0, y1, y1, y0, None, y0, y0, None, y0, y0, None, y1, y1, None, y1, y1]
    lz = [z0, z0, z0, z0, z0, None, z1, z1, z1, z1, z1, None, z0, z1, None, z0, z1, None, z0, z1, None, z0, z1]
    fig.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode='lines', line=dict(color='black', width=line_width), showlegend=False))

# --- INTERFACE ---

st.sidebar.title("📦 Expert WMS v9.2")
tab_nav = st.sidebar.radio("Navigation", ["Simulateur", "Base Articles"])

if tab_nav == "Base Articles":
    st.header("📋 Gestion du Référentiel")
    with st.form("new_item"):
        c1, c2, c3, c4, c5 = st.columns(5)
        n = c1.text_input("Nom")
        l = c2.number_input("Long (mm)", 100)
        w = c3.number_input("Larg (mm)", 100)
        h = c4.number_input("Haut (mm)", 50)
        p = c5.number_input("Poids (kg)", 0.5)
        if st.form_submit_button("Enregistrer"):
            st.session_state.db_refs = pd.concat([st.session_state.db_refs, pd.DataFrame([{"Référence":n,"L":l,"W":w,"H":h,"P":p}])]).drop_duplicates()
    st.dataframe(st.session_state.db_refs, use_container_width=True)

else:
    # --- PANNEAU DE CONTRÔLE ---
    with st.sidebar:
        ref = st.selectbox("Sélectionner l'article", st.session_state.db_refs["Référence"].tolist())
        item = st.session_state.db_refs[st.session_state.db_refs["Référence"] == ref].iloc[0]
        
        st.divider()
        type_pal = st.selectbox("Type de support", ["Palette Europe (800x1200)", "Palette VMF (1000x1200)"])
        w_p = 800 if "800" in type_pal else 1000
        l_p = 1200
        
        h_max = st.number_input("Hauteur Max Rack (mm)", 500, 2500, 1800)
        poids_max_pal = 1000 # Limite standard kg

    # CALCULS
    plan_a = get_optimal_layer(w_p, l_p, item['L'], item['W'])
    plan_b = get_crossed_layer(plan_a, w_p, l_p)
    nb_couches = int((h_max - 150) // item['H'])
    total_colis = len(plan_a) * nb_couches
    poids_total = total_colis * item['P']
    h_finale = 150 + (nb_couches * item['H'])
    vol_colis = (item['L']*item['W']*item['H']) * total_colis / 1e9
    
    # --- DASHBOARD ---
    st.header(f"Rapport de Palettisation : {ref}")
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Colis / Couche", len(plan_a))
    col_m2.metric("Total Colis", total_colis)
    
    poids_color = "normal" if poids_total <= poids_max_pal else "inverse"
    col_m3.metric("Poids Estimé", f"{poids_total} kg", delta=f"{poids_max_pal - poids_total} kg restants", delta_color=poids_color)
    col_m4.metric("Volume Utile", f"{vol_colis:.2f} m³")

    if poids_total > poids_max_pal:
        st.error(f"⚠️ Alerte : Le poids total ({poids_total}kg) dépasse la capacité du support !")

    t1, t2 = st.tabs(["🏗️ Simulation Industrielle", "📝 Fiche d'Instruction"])

    with t1:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("Visualisation de l'Empilage")
            f3 = go.Figure()
            draw_box(f3, 0, w_p, 0, l_p, 0, 150, "#5D4037") # Palette
            for k in range(nb_couches):
                p_current = plan_a if k % 2 == 0 else plan_b
                color = "#1E88E5" if k % 2 == 0 else "#E53935"
                z0 = 150 + (k * item['H'])
                for b in p_current:
                    draw_box(f3, b['x'], b['x']+b['w'], b['y'], b['y']+b['h'], z0, z0+item['H'], color)
            f3.update_layout(scene=dict(aspectmode='data'), height=700, margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(f3, use_container_width=True)
        
        with c2:
            st.subheader("Informations Rack")
            st.write(f"**Hauteur de pose :** {h_finale} mm")
            st.write(f"**Garde d'air résiduelle :** {h_max - h_finale} mm")
            
            # Petit graphique de remplissage de surface
            surface_pal = w_p * l_p
            surface_occupee = len(plan_a) * (item['L'] * item['W'])
            taux = (surface_occupee / surface_pal) * 100
            st.progress(int(taux))
            st.caption(f"Taux d'occupation de la surface : {taux:.1f}%")

    with t2:
        st.subheader("Plan de montage des couches")
        sc1, sc2 = st.columns(2)
        
        def draw_2d(plan, color, label):
            f = go.Figure()
            f.add_trace(go.Scatter(x=[0,w_p,w_p,0,0], y=[0,0,1200,1200,0], fill="toself", fillcolor="#EEEEEE", line=dict(color="black")))
            for p in plan:
                f.add_trace(go.Scatter(x=[p['x'],p['x']+p['w'],p['x']+p['w'],p['x'],p['x']], y=[p['y'],p['y'],p['y']+p['h'],p['y']+p['h'],p['y']], fill="toself", fillcolor=color, line=dict(color="white", width=2)))
            f.update_layout(title=label, yaxis=dict(scaleanchor="x"), showlegend=False)
            return f

        sc1.plotly_chart(draw_2d(plan_a, "#1E88E5", "Couches IMPAIRES (Base)"), use_container_width=True)
        sc2.plotly_chart(draw_2d(plan_b, "#E53935", "Couches PAIRES (Croisées)"), use_container_width=True)
