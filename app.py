import streamlit as st
import plotly.graph_objects as go

# --- FONCTION GRAPHIQUE ---
def draw_cube(fig, x_min, x_max, y_min, y_max, z_min, z_max, color):
    fig.add_trace(go.Mesh3d(
        x=[x_min, x_max, x_max, x_min, x_min, x_max, x_max, x_min],
        y=[y_min, y_min, y_max, y_max, y_min, y_min, y_max, y_max],
        z=[z_min, z_min, z_min, z_min, z_max, z_max, z_max, z_max],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=0.8, flatshading=True, showlegend=False
    ))

def get_layer_plan(W_max, L_max, cl, cw):
    plan = []
    nx, ny = int(W_max // cl), int(L_max // cw)
    for i in range(nx):
        for j in range(ny): plan.append((i*cl, j*cw, cl, cw))
    reste_x = W_max - (nx * cl)
    if reste_x >= cw:
        for i in range(int(reste_x // cw)):
            for j in range(int(L_max // cl)): plan.append((nx*cl + i*cw, j*cl, cw, cl))
    return plan

def mode_simple_valide():
    st.header("📦 Optimiseur de Palettisation Simple")
    
    # --- INPUTS ---
    with st.sidebar:
        st.header("🏗️ Rack & Lisse")
        l_lisse = st.selectbox("Longueur de lisse (mm)", [2700, 3600, 1350])
        p_max_lisse = st.number_input("Poids max Lisse (kg)", value=3000)
        h_max_rack = st.number_input("Hauteur Max Rack (mm)", value=1800)
        
        st.header("📦 Produit")
        cl = st.number_input("Long. (mm)", value=400)
        cw = st.number_input("Larg. (mm)", value=300)
        ch = st.number_input("Haut. (mm)", value=250)
        cp = st.number_input("Poids (kg)", value=25.0) # Augmentez ceci pour tester le bridage
        overhang = st.slider("Débordement (mm)", 0, 50, 0)
        
        target_pal = st.selectbox("Palette", ["800x1200", "1000x1200"])
        w_pal = 800 if "800" in target_pal else 1000

    # --- CALCULS CRITIQUES (ORDRE INVERSE) ---
    # 1. Combien de palettes sur la lisse ?
    nb_pal_sol = int(l_lisse // w_pal)
    
    # 2. Poids max par palette autorisé
    poids_max_par_pal = (p_max_lisse / nb_pal_sol) - 25 # -25kg palette vide
    
    # 3. Combien de colis max par palette selon le POIDS ?
    colis_max_poids = int(poids_max_par_pal // cp)
    
    # 4. Géométrie de la couche
    w_max_c, l_max_c = w_pal + 2*overhang, 1200 + 2*overhang
    plan = get_layer_plan(w_max_c, l_max_c, cl, cw)
    colis_par_couche = len(plan)
    
    # 5. Nombre de couches max selon la HAUTEUR
    nb_couches_h = int((h_max_rack - 150) // ch)
    
    # 6. Nombre de couches max selon le POIDS
    if colis_par_couche > 0:
        nb_couches_p = colis_max_poids // colis_par_couche
    else:
        nb_couches_p = 0
        
    # --- LE VERROU ---
    nb_couches_final = min(nb_couches_h, nb_couches_p)
    if nb_couches_final < 0: nb_couches_final = 0
    
    # --- DIAGNOSTIC ---
    with st.expander("🔍 Diagnostic du calcul de bridage"):
        st.write(f"Capacité Lisse : {p_max_lisse} kg")
        st.write(f"Poids max autorisé par palette : {round(poids_max_par_pal)} kg")
        st.write(f"Limitation Hauteur : {nb_couches_h} couches")
        st.write(f"Limitation Poids : {nb_couches_p} couches")
        st.write(f"**Décision finale : {nb_couches_final} couches**")

    # --- AFFICHAGE ---
    colis_total = nb_couches_final * colis_par_couche
    poids_total_pal = (colis_total * cp) + 25
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Colis / Palette", colis_total)
    m2.metric("Poids / Palette", f"{round(poids_total_pal, 1)} kg")
    m3.metric("État Lisse", f"{round(poids_total_pal * nb_pal_sol)} / {p_max_lisse} kg")

    if nb_couches_p < nb_couches_h:
        st.error(f"⚠️ BRIDAGE POIDS : Limité à {nb_couches_final} couches au lieu de {nb_couches_h}.")

    # --- 3D ---
    fig = go.Figure()
    # Dessin Palette
    draw_cube(fig, 0, w_pal, 0, 1200, 0, 150, "peru")
    
    # Dessin Colis (seulement si nb_couches_final > 0)
    for k in range(nb_couches_final):
        color = "#3498db" if k % 2 == 0 else "#e74c3c"
        for (x, y, dx, dy) in plan:
            z0 = 150 + (k * ch)
            # Effet miroir
            if k % 2 == 1:
                fx, fy = (w_max_c - x - dx), (l_max_c - y - dy)
            else:
                fx, fy = x, y
            draw_cube(fig, fx-overhang, fx+dx-overhang, fy-overhang, fy+dy-overhang, z0, z0+ch, color)

    fig.update_layout(scene=dict(aspectmode='data'), height=600, margin=dict(l=0,r=0,b=0,t=0))
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    mode_simple_valide()
