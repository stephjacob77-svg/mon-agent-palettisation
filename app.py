import streamlit as st
import numpy as np
import plotly.graph_objects as go

def generate_pallet_plan():
    st.set_page_config(page_title="IA Palettisation Pro", layout="wide")
    st.title("📦 Optimisateur de Palettisation & Stockage")

    # --- SIDEBAR : CONTRAINTES ---
    st.sidebar.header("1. Type de Palette")
    pal_type = st.sidebar.selectbox("Format", ["800x1200 (Europe)", "1000x1200 (UK/VMF)"])
    pal_weight_type = st.sidebar.radio("Type", ["Légère (15kg)", "Lourde (25kg)"])
    
    W_pal = 800 if "800" in pal_type else 1000
    L_pal = 1200
    H_pal = 150 # Hauteur standard palette
    P_pal = 15 if "Légère" in pal_weight_type else 25

    st.sidebar.header("2. Contraintes Rack")
    h_lisse = st.sidebar.number_input("Hauteur entre lisses (mm)", value=1800)
    l_lisse = st.sidebar.number_input("Longueur lisse entre poteaux (mm)", value=2700)
    poids_max_lisse = st.sidebar.number_input("Poids max par lisse (kg)", value=3000)

    st.sidebar.header("3. Dimensions Carton")
    c_l = st.sidebar.number_input("Longueur carton (mm)", value=400)
    c_w = st.sidebar.number_input("Largeur carton (mm)", value=300)
    c_h = st.sidebar.number_input("Hauteur carton (mm)", value=250)
    c_p = st.sidebar.number_input("Poids carton (kg)", value=10.0)

    # --- CALCULS ---
    # Calcul nombre de cartons par couche (optimisation basique 2 directions)
    nx1 = W_pal // c_l
    ny1 = L_pal // c_w
    total_c1 = nx1 * ny1

    nx2 = W_pal // c_w
    ny2 = L_pal // c_l
    total_c2 = nx2 * ny2

    # On choisit la meilleure orientation
    if total_c1 >= total_c2:
        nx, ny = nx1, ny1
        dim_x, dim_y = c_l, c_w
    else:
        nx, ny = nx2, ny2
        dim_x, dim_y = c_w, c_l

    # Calcul hauteur max
    h_dispo = h_lisse - H_pal - 100 # 100mm de marge de sécurité
    nb_couches = int(h_dispo // c_h)
    
    total_cartons = int(nx * ny * nb_couches)
    poids_marchandise = total_cartons * c_p
    poids_total_pal = poids_marchandise + P_pal

    # --- AFFICHAGE RESULTATS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Cartons / Palette", total_cartons)
    col2.metric("Poids Total Palette", f"{poids_total_pal} kg")
    
    nb_pal_par_lisse = int(l_lisse // W_pal)
    poids_sur_lisse = nb_pal_par_lisse * poids_total_pal
    
    if poids_sur_lisse > poids_max_lisse:
        st.error(f"⚠️ Alerte Poids : {poids_sur_lisse}kg sur la lisse (Max: {poids_max_lisse}kg)")
    else:
        col3.metric("Charge sur Lisse", f"{poids_sur_lisse} kg", "OK")

    # --- VISUALISATION 3D ---
    fig = go.Figure()
    # Dessin de la palette
    fig.add_trace(go.Mesh3d(x=[0,W_pal,W_pal,0,0,W_pal,W_pal,0], y=[0,0,L_pal,L_pal,0,0,L_pal,L_pal], z=[0,0,0,0,H_pal,H_pal,H_pal,H_pal], color='peru', opacity=0.5))
    
    # Dessin des cartons (simplifié pour la v1)
    for k in range(nb_couches):
        for i in range(int(nx)):
            for j in range(int(ny)):
                z0 = H_pal + (k * c_h)
                fig.add_trace(go.Box(x=[i*dim_x, (i+1)*dim_x], y=[j*dim_y, (j+1)*dim_y], z=[z0, z0+c_h], name="Carton"))

    fig.update_layout(scene=dict(aspectmode='data'), title="Plan de chargement 3D")
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    generate_pallet_plan()
