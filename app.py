import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math

# --- FONCTION GRAPHIQUE COMMUNE ---
def draw_cube(fig, x_range, y_range, z_range, color, opacity=0.8):
    x_min, x_max = x_range
    y_min, y_max = y_range
    z_min, z_max = z_range
    fig.add_trace(go.Mesh3d(
        x=[x_min, x_max, x_max, x_min, x_min, x_max, x_max, x_min],
        y=[y_min, y_min, y_max, y_max, y_min, y_min, y_max, y_max],
        z=[z_min, z_min, z_min, z_min, z_max, z_max, z_max, z_max],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=opacity, flatshading=True, showlegend=False
    ))

def get_mixed_layer_plan(W_max, L_max, cl, cw):
    plan = []
    nx, ny = int(W_max // cl), int(L_max // cw)
    for i in range(nx):
        for j in range(ny): plan.append((i*cl, j*cw, cl, cw))
    reste_x = W_max - (nx * cl)
    if reste_x >= cw:
        for i in range(int(reste_x // cw)):
            for j in range(int(L_max // cl)): plan.append((nx*cl + i*cw, j*cl, cw, cl))
    reste_y = L_max - (ny * cw)
    if reste_y >= cl:
        for i in range(int((nx * cl) // cw)):
            for j in range(int(reste_y // cl)): plan.append((i*cw, ny*cw + j*cl, cw, cl))
    return plan

# --- MODE 1 : OPTIMISEUR SIMPLE (RESTRICTIONS STOCKAGE RÉACTIVÉES) ---
def mode_simple_valide():
    st.header("📦 Optimiseur de Palettisation Simple")
    
    # --- Sidebar : Contraintes de Stockage (Priorité 1) ---
    st.sidebar.header("🏢 Contraintes de Stockage")
    l_lisse = st.sidebar.selectbox("Longueur de lisse (mm)", [2700, 3600, 1350], index=0)
    poids_max_lisse = st.sidebar.number_input("Poids max par niveau (kg)", value=3000)
    h_max = st.sidebar.number_input("Hauteur Max Rack (mm)", value=1800)
    
    st.sidebar.header("📏 Choix du Support")
    target_pal = st.sidebar.selectbox("Type de Palette", ["800x1200 (Euro)", "1000x1200 (VMF)"])
    W_pal = 800 if "800" in target_pal else 1000
    
    # --- Sidebar : Produit ---
    st.sidebar.header("📦 Dimensions Produit")
    cl = st.sidebar.number_input("Long. Carton (mm)", value=400)
    cw = st.sidebar.number_input("Larg. Carton (mm)", value=300)
    ch = st.sidebar.number_input("Haut. Carton (mm)", value=250)
    cp = st.sidebar.number_input("Poids Carton (kg)", value=10.0)
    overhang = st.sidebar.slider("Débordement autorisé (mm)", 0, 50, 0)
    
    # --- Calculs ---
    W_max, L_max = W_pal + 2*overhang, 1200 + 2*overhang
    plan = get_mixed_layer_plan(W_max, L_max, cl, cw)
    nb_c = int((h_max - 150) // ch)
    colis_par_pal = len(plan) * nb_c
    poids_pal = (colis_par_pal * cp) + 25 # +25kg pour la palette vide
    
    pal_par_lisse = int(l_lisse // W_pal)
    poids_total_lisse = poids_pal * pal_par_lisse
    
    # --- Affichage des Métriques ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Colis / Palette", colis_par_pal)
    m2.metric("Poids / Palette", f"{round(poids_pal, 1)} kg")
    m3.metric("Palettes / Lisse", pal_par_lisse)
    
    # Alerte Poids Lisse
    if poids_total_lisse > poids_max_lisse:
        m4.metric("Poids / Lisse", f"{round(poids_total_lisse, 0)} kg", delta="OVERLOAD", delta_color="inverse")
        st.error(f"⚠️ ATTENTION : Le poids total sur la lisse ({round(poids_total_lisse,0)}kg) dépasse la capacité de {poids_max_lisse}kg.")
    else:
        m4.metric("Poids / Lisse", f"{round(poids_total_lisse, 0)} kg")

    # --- Visuels ---
    col1, col2 = st.columns([2,1])
    with col1:
        fig3d = go.Figure()
        draw_cube(fig3d, [0, W_pal], [0, 1200], [0, 150], "peru")
        for k in range(nb_c):
            color = "#3498db" if k%2==0 else "#e74c3c"
            for (x, y, dx, dy) in plan:
                z0 = 150 + (k*ch)
                fx, fy = (W_max-x-dx, L_max-y-dy) if k%2==1 else (x, y)
                draw_cube(fig3d, [fx-overhang, fx+dx-overhang], [fy-overhang, fy+dy-overhang], [z0, z0+ch], color)
        fig3d.update_layout(scene=dict(aspectmode='data'), height=600, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig3d, use_container_width=True)
    
    with col2:
        st.write("**Plan de chargement**")
        st.info(f"Occupation sol : {W_pal} x 1200 mm")
        st.write(f"- Couches : {nb_c}")
        st.write(f"- Colis par couche : {len(plan)}")
        if overhang > 0:
            st.warning(f"Débordement actif : +{overhang}mm")

# --- MODE 2 : CONTAINER (INCHANGÉ) ---
def mode_container_pro():
    st.header("🚢 Tableau de Bord : Dépotage Container")
    # ... (le code précédent pour le container reste ici) ...
    st.info("Partie Container en cours de développement - Les fonctions d'import CSV et PDF seront ici.")

# --- MAIN ---
def main():
    st.set_page_config(page_title="Hub Logistique Expert", layout="wide")
    menu = st.sidebar.selectbox("Outil", ["Optimiseur Simple", "Déchargement Container"])
    
    if menu == "Optimiseur Simple":
        mode_simple_valide()
    else:
        mode_container_pro()

if __name__ == "__main__":
    main()
