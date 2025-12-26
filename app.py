import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert Palettisation Pro v8.1", layout="wide")

if 'db_refs' not in st.session_state:
    st.session_state.db_refs = pd.DataFrame(columns=["Référence", "L", "W", "H", "P"])

# --- FONCTIONS DE DESSIN ---

def draw_box(fig, x0, x1, y0, y1, z0, z1, color, opacity=1.0, line_width=1):
    """Dessine un élément 3D avec bordures nettes"""
    # Faces du cube
    fig.add_trace(go.Mesh3d(
        x=[x0, x1, x1, x0, x0, x1, x1, x0],
        y=[y0, y0, y1, y1, y0, y0, y1, y1],
        z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=opacity, flatshading=True, showlegend=False
    ))
    # Arêtes (Wireframe) pour le réalisme
    lines_x = [x0, x1, x1, x0, x0, None, x0, x1, x1, x0, x0, None, x0, x0, None, x1, x1, None, x1, x1, None, x0, x0]
    lines_y = [y0, y0, y1, y1, y0, None, y0, y0, y1, y1, y0, None, y0, y0, None, y0, y0, None, y1, y1, None, y1, y1]
    lines_z = [z0, z0, z0, z0, z0, None, z1, z1, z1, z1, z1, None, z0, z1, None, z0, z1, None, z0, z1, None, z0, z1]
    
    fig.add_trace(go.Scatter3d(
        x=lines_x, y=lines_y, z=lines_z,
        mode='lines', line=dict(color='black', width=line_width), showlegend=False
    ))

def draw_2d_layer(plan, w_pal, color, title):
    """Vue 2D avec tracé par nuage de points pour éviter les bugs de 'shapes'"""
    fig = go.Figure()
    # Support Palette
    fig.add_trace(go.Scatter(x=[0, w_pal, w_pal, 0, 0], y=[0, 0, 1200, 1200, 0], fill="toself", fillcolor="#D7CCC8", line=dict(color="#5D4037", width=3), name="Palette"))
    # Colis
    for p in plan:
        fig.add_trace(go.Scatter(x=[p['x'], p['x']+p['w'], p['x']+p['w'], p['x'], p['x']], y=[p['y'], p['y'], p['y']+p['h'], p['y']+p['h'], p['y']], fill="toself", fillcolor=color, line=dict(color="white", width=1), showlegend=False))
    fig.update_layout(title=title, xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"), height=350, margin=dict(l=10,r=10,t=40,b=10), plot_bgcolor='white')
    return fig

# --- CALCULS ---

def get_optimized_plan(W, L, cl, cw):
    plan = []
    nx, ny = int(W // cl), int(L // cw)
    for i in range(nx):
        for j in range(ny): plan.append({'x': i*cl, 'y': j*cw, 'w': cl, 'h': cw})
    rx = W - (nx * cl)
    if rx >= cw:
        for j in range(int(L // cl)): plan.append({'x': nx*cl, 'y': j*cl, 'w': cw, 'h': cl})
    return plan

# --- APPLICATION PRINCIPALE ---

st.sidebar.title("🛠️ Expert WMS v8.1")
mode = st.sidebar.radio("Navigation", ["Base de Données Articles", "Simulateur de Rack"])

if mode == "Base de Données Articles":
    st.header("📋 Référentiel Articles")
    with st.form("add_item"):
        c1, c2, c3, c4, c5 = st.columns([2,1,1,1,1])
        n = c1.text_input("Référence")
        l = c2.number_input("Long (mm)", value=400)
        w = c3.number_input("Larg (mm)", value=300)
        h = c4.number_input("Haut (mm)", value=250)
        p = c5.number_input("Poids (kg)", value=12.0)
        if st.form_submit_button("Enregistrer"):
            new_data = pd.DataFrame([{"Référence":n, "L":l, "W":w, "H":h, "P":p}])
            st.session_state.db_refs = pd.concat([st.session_state.db_refs, new_data]).drop_duplicates(subset='Référence')
    st.dataframe(st.session_state.db_refs, use_container_width=True, hide_index=True)
    
    if not st.session_state.db_refs.empty:
        csv = st.session_state.db_refs.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Télécharger Base (CSV)", csv, "base_refs.csv", "text/csv")

else:
    st.header("🏗️ Optimisation de l'Alvéole")
    
    with st.sidebar:
        if st.session_state.db_refs.empty:
            st.warning("Veuillez ajouter des articles dans la base.")
            st.stop()
        
        ref_sel = st.selectbox("Sélectionner Article", st.session_state.db_refs["Référence"].tolist())
        l_lisse = st.selectbox("Longueur Lisse (mm)", [2700, 3600, 1350])
        h_utile = st.number_input("Hauteur Utile Alvéole (mm)", value=1800)
        w_pal = st.radio("Standard Palette", [800, 1000], horizontal=True)
        p_max_l = st.number_input("Capacité Lisse (kg)", value=3000)

    item = st.session_state.db_refs[st.session_state.db_refs["Référence"] == ref_sel].iloc[0]
    plan = get_optimized_plan(w_pal, 1200, item['L'], item['W'])
    
    # Calculs Logistiques
    nb_pal_sol = l_lisse // w_pal
    p_max_pal = (p_max_l / nb_pal_sol) - 25
    n_h = (h_utile - 150) // item['H']
    n_p = (p_max_pal // item['P']) // len(plan) if item['P'] > 0 else 99
    couches = int(min(n_h, n_p))
    total_colis = couches * len(plan)
    
    # Statistiques
    vol_marchandise = (item['L'] * item['W'] * item['H'] * total_colis) / 1e9
    vol_alveole = (l_lisse * 1200 * h_utile) / 1e9
    taux_remplissage = ((w_pal * 1200 * (150 + couches * item['H']) * nb_pal_sol) / vol_alveole) * 100

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric("Colis / Palette", total_colis)
    col_s2.metric("Poids Palette", f"{round((total_colis * item['P']) + 25)} kg")
    col_s3.metric("Volume Net", f"{round(vol_marchandise, 2)} m³")
    col_s4.metric("Occupation Alvéole", f"{round(taux_remplissage, 1)} %")

    st.write("### 🧊 Visualisations 3D")
    c3da, c3db = st.columns(2)
    
    with c3da:
        st.caption("Détail Palette (Unitaire)")
        fig_pal = go.Figure()
        draw_box(fig_pal, 0, w_pal, 0, 1200, 0, 150, "#8D6E63") # Bois
        for k in range(couches):
            color = "#2196F3" if k % 2 == 0 else "#EF5350"
            for p in plan:
                z0 = 150 + (k * item['H'])
                fx, fy = (w_pal - p['x'] - p['w'], 1200 - p['y'] - p['h']) if k % 2 == 1 else (p['x'], p['y'])
                draw_box(fig_pal, fx, fx+p['w'], fy, fy+p['h'], z0, z0+item['H'], color)
        fig_pal.update_layout(scene=dict(aspectmode='data'), height=550, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig_pal, use_container_width=True)

    with c3db:
        st.caption("Configuration du Rack (Positionnement Extrémités)")
        
        fig_rack = go.Figure()
        # Structure Rack (4 Poteaux)
        for px in [-100, l_lisse]:
            for py in [0, 1100]:
                draw_box(fig_rack, px, px+100, py, py+100, -100, h_utile+200, "royalblue")
        # Lisses
        draw_box(fig_rack, 0, l_lisse, 0, 50, -50, 0, "orange")
        draw_box(fig_rack, 0, l_lisse, 1050, 1100, -50, 0, "orange")
        draw_box(fig_rack, 0, l_lisse, 0, 50, h_utile, h_utile+50, "orange")
        
        # Palettes calées aux extrémités
        for i in range(int(nb_pal_sol)):
            if i == 0: x_start = 5
            elif i == nb_pal_sol - 1: x_start = l_lisse - w_pal - 5
            else: x_start = i * (w_pal + (l_lisse - nb_pal_sol * w_pal)/(nb_pal_sol-1 if nb_pal_sol>1 else 1))
            
            draw_box(fig_rack, x_start, x_start+w_pal, 0, 1200, 0, 150, "#8D6E63")
            draw_box(fig_rack, x_start+20, x_start+w_pal-20, 20, 1180, 150, 150+(couches*item['H']), "rgba(33, 150, 243, 0.5)")
        
        fig_rack.update_layout(scene=dict(aspectmode='data'), height=550, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig_rack, use_container_width=True)

    st.write("### 📋 Plans de préparation")
    c2da, c2db = st.columns(2)
    with c2da:
        st.plotly_chart(draw_2d_layer(plan, w_pal, "#2196F3", "Couches Impaires"), use_container_width=True)
    with c2db:
        plan_b = [{'x': w_pal-p['x']-p['w'], 'y': 1200-p['y']-p['h'], 'w': p['w'], 'h': p['h']} for p in plan]
        st.plotly_chart(draw_2d_layer(plan_b, w_pal, "#EF5350", "Couches Paires"), use_container_width=True)
