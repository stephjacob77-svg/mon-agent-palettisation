import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert Palettisation Pro v8", layout="wide")

if 'db_refs' not in st.session_state:
    st.session_state.db_refs = pd.DataFrame(columns=["Référence", "L", "W", "H", "P"])

# --- FONCTIONS DE DESSIN ---

def draw_box(fig, x0, x1, y0, y1, z0, z1, color, opacity=1.0, line_width=1):
    """Dessine un colis ou un élément de structure avec des arêtes visibles"""
    # Faces
    fig.add_trace(go.Mesh3d(
        x=[x0, x1, x1, x0, x0, x1, x1, x0],
        y=[y0, y0, y1, y1, y0, y0, y1, y1],
        z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=opacity, flatshading=True, showlegend=False
    ))
    # Arêtes pour le réalisme (filaire)
    lines = [
        ([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], [z0, z0, z0, z0, z0]),
        ([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], [z1, z1, z1, z1, z1]),
        ([x0, x0], [y0, y0], [z0, z1]), ([x1, x1], [y0, y0], [z0, z1]),
        ([x1, x1], [y1, y1], [z0, z1]), ([x0, x0], [y1, y1], [z0, z1])
    ]
    for lx, ly, lz in lines:
        fig.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode='lines', line=dict(color='black', width=line_width), showlegend=False))

def draw_2d_layer(plan, w_pal, color, title):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, w_pal, w_pal, 0, 0], y=[0, 0, 1200, 1200, 0], fill="toself", fillcolor="#E0E0E0", line=dict(color="#5D4037", width=3), name="Palette"))
    for p in plan:
        fig.add_trace(go.Scatter(x=[p['x'], p['x']+p['w'], p['x']+p['w'], p['x'], p['x']], y=[p['y'], p['y'], p['y']+p['h'], p['y']+p['h'], p['y']], fill="toself", fillcolor=color, line=dict(color="white", width=2), showlegend=False))
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

# --- INTERFACE ---

st.sidebar.title("📦 WMS Optimiseur v8")
mode = st.sidebar.radio("Navigation", ["Base de Données Articles", "Simulateur de Rack"])

if mode == "Base de Données Articles":
    st.header("📋 Référentiel Articles")
    with st.form("add_item"):
        c1, c2, c3, c4, c5 = st.columns([2,1,1,1,1])
        n = c1.text_input("Nom de la référence (Ex: Moteur_V6)")
        l = c2.number_input("Long (mm)", value=400)
        w = c3.number_input("Larg (mm)", value=300)
        h = c4.number_input("Haut (mm)", value=250)
        p = c5.number_input("Poids (kg)", value=12.0)
        if st.form_submit_button("Sauvegarder dans la base"):
            new_data = pd.DataFrame([{"Référence":n, "L":l, "W":w, "H":h, "P":p}])
            st.session_state.db_refs = pd.concat([st.session_state.db_refs, new_data]).drop_duplicates(subset='Référence')
    st.dataframe(st.session_state.db_refs, use_container_width=True, hide_index=True)

else:
    st.header("🏗️ Simulation d'Alvéole Rack")
    
    with st.sidebar:
        ref_sel = st.selectbox("Sélectionner Article", st.session_state.db_refs["Référence"].tolist())
        l_lisse = st.selectbox("Longueur Lisse (mm)", [2700, 3600, 1350])
        h_utile = st.number_input("Hauteur Utile Alvéole (mm)", value=1800)
        w_pal = st.radio("Standard Palette", [800, 1000], horizontal=True)
        p_max_l = st.number_input("Capacité Lisse (kg)", value=3000)

    if ref_sel:
        item = st.session_state.db_refs[st.session_state.db_refs["Référence"] == ref_sel].iloc[0]
        plan = get_optimized_plan(w_pal, 1200, item['L'], item['W'])
        
        # Calculs logistiques
        nb_pal_sol = l_lisse // w_pal
        p_max_pal = (p_max_l / nb_pal_sol) - 25
        n_h = (h_utile - 150) // item['H']
        n_p = (p_max_pal // item['P']) // len(plan) if item['P'] > 0 else 99
        couches = int(min(n_h, n_p))
        total_colis = couches * len(plan)
        
        # STATISTIQUES PRO
        vol_colis = (item['L'] * item['W'] * item['H'] * total_colis) / 1e9
        vol_total_pal = (w_pal * 1200 * (150 + couches * item['H'])) / 1e9
        vol_alveole = (l_lisse * 1200 * h_utile) / 1e9
        taux_remplissage = (vol_total_pal * nb_pal_sol / vol_alveole) * 100

        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("Colis / Palette", total_colis)
        col_s2.metric("Poids Palette", f"{round((total_colis * item['P']) + 25)} kg")
        col_s3.metric("Volume Marchandise", f"{round(vol_colis, 2)} m³")
        col_s4.metric("Taux d'Alvéole", f"{round(taux_remplissage, 1)} %")

        # --- VUES 3D ---
        st.write("### 🧊 Rendu 3D Haute Fidélité")
        c3da, c3db = st.columns(2)
        
        with c3da:
            st.caption("Détail Palette (Colis individuels)")
            fig_pal = go.Figure()
            draw_box(fig_pal, 0, w_pal, 0, 1200, 0, 150, "#8D6E63") # Palette
            for k in range(couches):
                color = "#2196F3" if k % 2 == 0 else "#EF5350"
                for p in plan:
                    z0 = 150 + (k * item['H'])
                    # Alternance de couche pour la stabilité
                    if k % 2 == 1:
                        fx, fy = w_pal - p['x'] - p['w'], 1200 - p['y'] - p['h']
                    else:
                        fx, fy = p['x'], p['y']
                    draw_box(fig_pal, fx, fx+p['w'], fy, fy+p['h'], z0, z0+item['H'], color, line_width=1)
            fig_pal.update_layout(scene=dict(aspectmode='data'), height=550, margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(fig_pal, use_container_width=True)

        with c3db:
            st.caption("Structure Rack & Calage Extrémités")
            fig_rack = go.Figure()
            # Montants (4 poteaux distincts pour le réalisme)
            p_size = 100
            posts = [( -p_size, 0), ( -p_size, 1100), (l_lisse, 0), (l_lisse, 1100)]
            for px, py in posts:
                draw_box(fig_rack, px, px+p_size, py, py+p_size, -100, h_utile+300, "royalblue")
            
            # Lisses (Profilés horizontaux)
            draw_box(fig_rack, 0, l_lisse, 0, 50, -100, 0, "orange")
            draw_box(fig_rack, 0, l_lisse, 1050, 1100, -100, 0, "orange")
            draw_box(fig_rack, 0, l_lisse, 0, 50, h_utile, h_utile+100, "orange")
            
            # Palettes calées aux extrémités
            for i in range(int(nb_pal_sol)):
                # Positionnement : si 2 palettes, une à 0, une à la fin de la lisse
                if i == 0: x_start = 5 
                elif i == nb_pal_sol - 1: x_start = l_lisse - w_pal - 5
                else: x_start = i * (w_pal + 50) # Pour les cas à 3 palettes
                
                draw_box(fig_rack, x_start, x_start+w_pal, 0, 1200, 0, 150, "#8D6E63") # Bois
                draw_box(fig_rack, x_start+20, x_start+w_pal-20, 20, 1180, 150, 150+(couches*item['H']), "rgba(33, 150, 243,
