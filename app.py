import streamlit as st
import numpy as np
import plotly.graph_objects as go

def draw_cube(fig, x_range, y_range, z_range, color='blue'):
    # Fonction pour dessiner un carton 3D propre
    x_min, x_max = x_range
    y_min, y_max = y_range
    z_min, z_max = z_range
    
    fig.add_trace(go.Mesh3d(
        x=[x_min, x_max, x_max, x_min, x_min, x_max, x_max, x_min],
        y=[y_min, y_min, y_max, y_max, y_min, y_min, y_max, y_max],
        z=[z_min, z_min, z_min, z_min, z_max, z_max, z_max, z_max],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
        j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
        k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=0.7, flatshading=True, showlegend=False
    ))

def generate_pallet_plan():
    st.set_page_config(page_title="IA Palettisation Pro", layout="wide")
    st.title("📦 Optimisateur de Palettisation & Stockage")

    # --- SIDEBAR ---
    st.sidebar.header("1. Type de Palette")
    pal_type = st.sidebar.selectbox("Format", ["800x1200 (Europe)", "1000x1200 (VMF)"])
    pal_weight_type = st.sidebar.radio("Type", ["Légère (15kg)", "Lourde (25kg)"])
    
    W_pal = 800 if "800" in pal_type else 1000
    L_pal = 1200
    H_pal = 150 
    P_pal = 15 if "Légère" in pal_weight_type else 25

    st.sidebar.header("2. Contraintes Rack")
    h_lisse = st.sidebar.number_input("Hauteur entre lisses (mm)", value=1800)
    l_lisse = st.sidebar.number_input("Longueur lisse (mm)", value=2700)
    poids_max_lisse = st.sidebar.number_input("Poids max par lisse (kg)", value=3000)

    st.sidebar.header("3. Dimensions Carton")
    c_l = st.sidebar.number_input("Longueur carton (mm)", value=400)
    c_w = st.sidebar.number_input("Largeur carton (mm)", value=300)
    c_h = st.sidebar.number_input("Hauteur carton (mm)", value=250)
    c_p = st.sidebar.number_input("Poids carton (kg)", value=10.0)

    # --- CALCULS ---
    nx, ny = W_pal // c_l, L_pal // c_w
    dim_x, dim_y = c_l, c_w
    
    # Test de l'autre orientation
    if ( (W_pal // c_w) * (L_pal // c_l) ) > (nx * ny):
        nx, ny = W_pal // c_w, L_pal // c_l
        dim_x, dim_y = c_w, c_l

    h_dispo = h_lisse - H_pal - 100 
    nb_couches = int(h_dispo // c_h)
    total_cartons = int(nx * ny * nb_couches)
    poids_total_pal = (total_cartons * c_p) + P_pal

    # --- AFFICHAGE ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Colis / Palette", total_cartons)
    col2.metric("Poids Palette", f"{round(poids_total_pal, 1)} kg")
    
    nb_pal_lisse = int(l_lisse // W_pal)
    poids_lisse = nb_pal_lisse * poids_total_pal
    col3.metric("Charge Lisse", f"{round(poids_lisse, 1)} kg", delta=f"Max {poids_max_lisse}", delta_color="inverse")

    if poids_lisse > poids_max_lisse:
        st.error(f"⚠️ SURCHARGE : {round(poids_lisse - poids_max_lisse, 1)} kg de trop sur la lisse !")

    # --- VISU 3D ---
    fig = go.Figure()
    # Dessin Palette
    draw_cube(fig, [0, W_pal], [0, L_pal], [0, H_pal], color='peru')
    
    # Dessin Cartons (on dessine juste quelques-uns pour la fluidité)
    for k in range(nb_couches):
        for i in range(int(nx)):
            for j in range(int(ny)):
                z0 = H_pal + (k * c_h)
                draw_cube(fig, [i*dim_x, (i+1)*dim_x], [j*dim_y, (j+1)*dim_y], [z0, z0+c_h], color='royalblue')

    fig.update_layout(scene=dict(aspectmode='data', xaxis_title='Largeur (mm)', yaxis_title='Longueur (mm)', zaxis_title='Hauteur (mm)'))
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    generate_pallet_plan()
