import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert Palettisation Pro v7", layout="wide")

if 'db_refs' not in st.session_state:
    st.session_state.db_refs = pd.DataFrame(columns=["Référence", "L", "W", "H", "P"])

# --- MOTEUR DE DESSIN ---

def draw_cube(fig, x0, x1, y0, y1, z0, z1, color, opacity=1.0, showlegend=False):
    """Génère un cube 3D propre"""
    fig.add_trace(go.Mesh3d(
        x=[x0, x1, x1, x0, x0, x1, x1, x0],
        y=[y0, y0, y1, y1, y0, y0, y1, y1],
        z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=opacity, flatshading=True, showlegend=showlegend
    ))

def draw_2d_layer(plan, w_pal, color, title):
    """Vue 2D robuste avec Scatter traces"""
    fig = go.Figure()
    # Palette support
    fig.add_trace(go.Scatter(x=[0, w_pal, w_pal, 0, 0], y=[0, 0, 1200, 1200, 0], fill="toself", fillcolor="#F5F5F5", line=dict(color="#5D4037", width=3), name="Palette"))
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
    # Optionnel: remplissage du reliquat par rotation (logiciel pro)
    rx = W - (nx * cl)
    if rx >= cw:
        for j in range(int(L // cl)): plan.append({'x': nx*cl, 'y': j*cl, 'w': cw, 'h': cl})
    return plan

# --- INTERFACE ---

st.sidebar.title("🛠️ Administration WMS")
mode = st.sidebar.radio("Navigation", ["Base de Données", "Optimiseur Rack"])

if mode == "Base de Données":
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

    st.dataframe(st.session_state.db_refs, use_container_width=True)
    
    # Export Excel
    if not st.session_state.db_refs.empty:
        csv = st.session_state.db_refs.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Exporter la base en CSV", data=csv, file_name="base_references.csv", mime="text/csv")

else:
    st.header("🏗️ Simulation & Optimisation du Rack")
    
    with st.sidebar:
        ref_sel = st.selectbox("Charger Référence", st.session_state.db_refs["Référence"].tolist())
        l_lisse = st.selectbox("Lisse (mm)", [2700, 3600, 1350])
        h_utile = st.number_input("Hauteur Utile (mm)", value=1800)
        w_pal = st.radio("Support", [800, 1000], horizontal=True)
        p_max_l = st.number_input("Poids Max Lisse (kg)", value=3000)

    if ref_sel:
        item = st.session_state.db_refs[st.session_state.db_refs["Référence"] == ref_sel].iloc[0]
        plan = get_optimized_plan(w_pal, 1200, item['L'], item['W'])
        
        # Calcul des limites
        nb_pal_sol = l_lisse // w_pal
        p_max_pal = (p_max_l / nb_pal_sol) - 25
        n_h = (h_utile - 150) // item['H']
        n_p = (p_max_pal // item['P']) // len(plan) if item['P'] > 0 else 99
        couches = int(min(n_h, n_p))
        
        # --- AFFICHAGE 3D ---
        st.write("### 🧊 Visualisations 3D")
        col_3da, col_3db = st.columns(2)
        
        with col_3da:
            st.caption("Détail Palette Individuelle")
            fig_pal = go.Figure()
            draw_cube(fig_pal, 0, w_pal, 0, 1200, 0, 150, "#8D6E63") # Palette
            for k in range(couches):
                c_color = "#2196F3" if k % 2 == 0 else "#EF5350"
                for p in plan:
                    z0 = 150 + (k * item['H'])
                    draw_cube(fig_pal, p['x'], p['x']+p['w'], p['y'], p['y']+p['h'], z0, z0+item['H'], c_color)
            fig_pal.update_layout(scene=dict(aspectmode='data'), height=500, margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(fig_pal, use_container_width=True)

        with col_3db:
            st.caption("Mise en situation Rack (Proportions réelles)")
            
            fig_rack = go.Figure()
            # Poteaux (Montants bleus - 100mm)
            draw_cube(fig_rack, -100, 0, 0, 1200, -100, h_utile+200, "royalblue")
            draw_cube(fig_rack, l_lisse, l_lisse+100, 0, 1200, -100, h_utile+200, "royalblue")
            # Lisses (Orange - 150mm hauteur)
            draw_cube(fig_rack, 0, l_lisse, 0, 100, -150, 0, "orange")
            draw_cube(fig_rack, 0, l_lisse, 0, 100, h_utile, h_utile+150, "orange")
            # Palettes stockées
            for i in range(int(nb_pal_sol)):
                x_start = i * (w_pal + 50) + 25
                draw_cube(fig_rack, x_start, x_start+w_pal, 0, 1200, 0, 150, "#8D6E63")
                draw_cube(fig_rack, x_start+10, x_start+w_pal-10, 10, 1190, 150, 150+(couches*item['H']), "rgba(33, 150, 243, 0.4)")
            fig_rack.update_layout(scene=dict(aspectmode='data'), height=500, margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(fig_rack, use_container_width=True)

        # --- PLANS 2D ---
        st.write("### 📋 Schémas de Montage")
        c2da, c2db = st.columns(2)
        c2da.plotly_chart(draw_2d_layer(plan, w_pal, "#2196F3", "Couche IMPAIRE"), use_container_width=True)
        # Miroir pour la couche B
        plan_b = [{'x': w_pal-p['x']-p['w'], 'y': 1200-p['y']-p['h'], 'w': p['w'], 'h': p['h']} for p in plan]
        c2db.plotly_chart(draw_2d_layer(plan_b, w_pal, "#EF5350", "Couche PAIRE"), use_container_width=True)

        # METRIQUES FINALES
        st.sidebar.divider()
        st.sidebar.metric("Total Colis", couches * len(plan))
        st.sidebar.metric("Poids Palette", f"{round((couches * len(plan) * item['P']) + 25)} kg")
        st.sidebar.info(f"Limitation : {'POIDS' if n_p < n_h else 'HAUTEUR'}")
