import streamlit as st
import plotly.graph_objects as go
import math

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

def mode_simple_valide():
    st.header("📦 Optimiseur de Palettisation Simple")
    
    # --- Sidebar ---
    st.sidebar.header("🏢 Contraintes de Stockage")
    l_lisse = st.sidebar.selectbox("Longueur de lisse (mm)", [2700, 3600, 1350])
    p_max_lisse = st.sidebar.number_input("Poids max par niveau (kg)", value=3000)
    h_max_rack = st.sidebar.number_input("Hauteur Max Rack (mm)", value=1800)
    
    st.sidebar.header("📦 Produit")
    cl = st.sidebar.number_input("Long. (mm)", value=400)
    cw = st.sidebar.number_input("Larg. (mm)", value=300)
    ch = st.sidebar.number_input("Haut. (mm)", value=250)
    cp = st.sidebar.number_input("Poids Unitaire (kg)", value=20.0)
    overhang = st.sidebar.slider("Débordement (mm)", 0, 50, 0)

    # --- CALCULS DE BRIDAGE ---
    options = [800, 1000]
    final_results = {}

    for W in options:
        # 1. Plan d'une couche
        plan = get_mixed_layer_plan(W + 2*overhang, 1200 + 2*overhang, cl, cw)
        colis_par_couche = len(plan)
        nb_pal_sol = int(l_lisse // W)
        
        # 2. Poids max autorisé par palette pour respecter la lisse
        # Formule : (Capacité Lisse / Nb Palettes) - Poids Palette Vide
        poids_autorise_pal = (p_max_lisse / nb_pal_sol) - 25
        
        # 3. Nombre de colis max autorisé par le poids
        colis_max_poids = int(poids_autorise_pal // cp)
        
        # 4. Nombre de couches max autorisé par la hauteur
        nb_couches_hauteur = int((h_max_rack - 150) // ch)
        
        # 5. Conversion du "colis_max_poids" en couches entières
        if colis_par_couche > 0:
            nb_couches_poids = colis_max_poids // colis_par_couche
        else:
            nb_couches_poids = 0
            
        # --- LE BRIDAGE REEL ---
        # On choisit le plus petit nombre de couches entre la limite hauteur et la limite poids
        nb_couches_final = min(nb_couches_hauteur, nb_couches_poids)
        
        # Sécurité : Si le poids d'une seule couche dépasse déjà la limite, nb_couches = 0
        if (colis_par_couche * cp) > poids_autorise_pal:
            nb_couches_final = 0

        final_results[W] = {
            "total_colis": int(nb_couches_final * colis_par_couche),
            "nb_couches": int(nb_couches_final),
            "plan": plan,
            "nb_pal_sol": nb_pal_sol,
            "poids_final_pal": (nb_couches_final * colis_par_couche * cp) + 25,
            "cause": "POIDS" if nb_couches_poids < nb_couches_hauteur else "HAUTEUR"
        }

    # Sélection du meilleur support
    best_w = 800 if (final_results[800]["total_colis"] * final_results[800]["nb_pal_sol"]) >= \
                    (final_results[1000]["total_colis"] * final_results[1000]["nb_pal_sol"]) else 1000
    
    st.sidebar.header("📏 Support")
    target_pal = st.sidebar.selectbox("Palette", ["800x1200", "1000x1200"], index=0 if best_w==800 else 1)
    W_sel = 800 if "800" in target_pal else 1000
    res = final_results[W_sel]

    # --- AFFICHAGE ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Colis / Palette", res["total_colis"])
    m2.metric("Poids / Palette", f"{round(res['poids_final_pal'], 1)} kg")
    m3.metric("Palettes / Lisse", res["nb_pal_sol"])
    
    # Indicateur de limite
    if res["cause"] == "POIDS":
        m4.metric("Limite", "🚨 POIDS", delta="Actif", delta_color="inverse")
    else:
        m4.metric("Limite", "OK (Hauteur)")

    # Affichage 3D
    fig = go.Figure()
    draw_cube(fig, [0, W_sel], [0, 1200], [0, 150], "peru")
    
    if res["nb_couches"] > 0:
        for k in range(res["nb_couches"]):
            color = "#3498db" if k % 2 == 0 else "#e74c3c"
            for (x, y, dx, dy) in res["plan"]:
                z0 = 150 + (k * ch)
                fx, fy = (W_sel + 2*overhang - x - dx, 1200 + 2*overhang - y - dy) if k % 2 == 1 else (x, y)
                draw_cube(fig, [fx - overhang, fx + dx - overhang], [fy - overhang, fy + dy - overhang], [z0, z0 + ch], color)
    else:
        st.error("Impossible de poser même une seule couche sans dépasser le poids max de la lisse !")

    fig.update_layout(scene=dict(aspectmode='data'), height=600)
    st.plotly_chart(fig, use_container_width=True)

    # Barre de charge réelle
    charge_totale = res['poids_final_pal'] * res['nb_pal_sol']
    st.write(f"Charge sur lisse : **{round(charge_totale)} kg** / {p_max_lisse} kg")
    st.progress(min(charge_totale / p_max_lisse, 1.0))

if __name__ == "__main__":
    main_menu = st.sidebar.selectbox("Menu", ["Optimiseur Simple", "Container"])
    if main_menu == "Optimiseur Simple":
        mode_simple_valide()
