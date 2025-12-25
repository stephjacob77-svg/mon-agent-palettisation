import streamlit as st
import plotly.graph_objects as go
import math

# --- FONCTION GRAPHIQUE ---
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
    
    # --- Sidebar : Contraintes ---
    st.sidebar.header("🏢 Contraintes de Stockage")
    l_lisse = st.sidebar.selectbox("Longueur de lisse (mm)", [2700, 3600, 1350])
    p_max_lisse = st.sidebar.number_input("Poids max par niveau (kg)", value=3000)
    h_max = st.sidebar.number_input("Hauteur Max Rack (mm)", value=1800)
    
    st.sidebar.header("📦 Produit")
    cl = st.sidebar.number_input("Long. (mm)", value=400)
    cw = st.sidebar.number_input("Larg. (mm)", value=300)
    ch = st.sidebar.number_input("Haut. (mm)", value=250)
    cp = st.sidebar.number_input("Poids Unitaire (kg)", value=20.0) # Test avec poids lourd
    overhang = st.sidebar.slider("Débordement (mm)", 0, 50, 0)

    # --- Logique de calcul multi-support ---
    options = [800, 1000]
    results = {}

    for W in options:
        plan = get_mixed_layer_plan(W + 2*overhang, 1200 + 2*overhang, cl, cw)
        colis_couche = len(plan)
        nb_pal_sol = int(l_lisse // W)
        
        # 1. Limite Poids
        poids_max_autorise_par_pal = (p_max_lisse / nb_pal_sol) - 25
        colis_max_poids = int(poids_max_autorise_par_pal // cp)
        
        # 2. Limite Hauteur
        nb_couches_geo = int((h_max - 150) // ch)
        colis_max_geo = colis_couche * nb_couches_geo
        
        # 3. Bridage effectif
        total_colis = min(colis_max_geo, colis_max_poids)
        nb_couches_finales = total_colis // colis_couche if colis_couche > 0 else 0
        
        results[W] = {
            "total": nb_couches_finales * colis_couche,
            "couches": nb_couches_finales,
            "plan": plan,
            "nb_pal": nb_pal_sol,
            "poids": (nb_couches_finales * colis_couche * cp) + 25,
            "cause": "POIDS" if (colis_max_poids < colis_max_geo) else "HAUTEUR"
        }

    # Meilleure option (Volume total sur la lisse)
    best_w = 800 if (results[800]["total"] * results[800]["nb_pal"]) >= (results[1000]["total"] * results[1000]["nb_pal"]) else 1000
    
    st.sidebar.header("📏 Support")
    target_pal = st.sidebar.selectbox("Palette", ["800x1200", "1000x1200"], index=0 if best_w==800 else 1)
    W_sel = 800 if "800" in target_pal else 1000
    res = results[W_sel]

    # --- Affichage ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Colis / Palette", res["total"])
    m2.metric("Poids / Palette", f"{round(res['poids'], 1)} kg")
    m3.metric("Palettes / Lisse", res["nb_pal"])
    m4.metric("Cause Limite", res["cause"])

    if res["cause"] == "POIDS":
        st.error(f"🚨 BRIDAGE POIDS ACTIF : La palette est limitée à {res['couches']} couches pour ne pas dépasser la charge de la lisse.")

    col_v, col_d = st.columns([2,1])
    with col_v:
        fig = go.Figure()
        draw_cube(fig, [0, W_sel], [0, 1200], [0, 150], "peru")
        for k in range(res["couches"]):
            color = "#3498db" if k%2==0 else "#e74c3c"
            for (x, y, dx, dy) in res["plan"]:
                z0 = 150 + (k*ch)
                fx, fy = (W_sel+2*overhang-x-dx, 1200+2*overhang-y-dy) if k%2==1 else (x,y)
                draw_cube(fig, [fx-overhang, fx+dx-overhang], [fy-overhang, fy+dy-overhang], [z0, z0+ch], color)
        fig.update_layout(scene=dict(aspectmode='data'), height=600)
        st.plotly_chart(fig, use_container_width=True)

    with col_d:
        st.write("**Récapitulatif Lisse**")
        st.write(f"Charge totale niveau : {round(res['poids'] * res['nb_pal'], 0)} kg / {p_max_lisse} kg")
        st.progress(min((res['poids'] * res['nb_pal']) / p_max_lisse, 1.0))

def main():
    st.set_page_config(page_title="IA Palettisation v5.3", layout="wide")
    menu = st.sidebar.selectbox("Menu", ["Optimiseur Simple", "Container"])
    if menu == "Optimiseur Simple": mode_simple_valide()
    else: st.write("Module Container - Prochaine étape.")

if __name__ == "__main__": main()
