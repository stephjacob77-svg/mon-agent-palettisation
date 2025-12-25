import streamlit as st
import plotly.graph_objects as go
import pandas as pd
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

def calculate_best_fit(W_pal, l_lisse, h_max, cl, cw, ch, cp, p_max_lisse, overhang):
    W_max, L_max = W_pal + 2*overhang, 1200 + 2*overhang
    plan = get_mixed_layer_plan(W_max, L_max, cl, cw)
    colis_par_couche = len(plan)
    nb_pal_sol = int(l_lisse // W_pal)
    
    # Capacité poids autorisée par palette
    poids_max_par_pal = (p_max_lisse / nb_pal_sol) - 25 # On retire le poids propre de la palette
    colis_max_poids = int(poids_max_par_pal // cp)
    
    # Capacité hauteur autorisée (géométrique)
    nb_couches_geo = int((h_max - 150) // ch)
    colis_max_geo = colis_par_couche * nb_couches_geo
    
    # Arbitrage : On prend le plus petit des deux
    total_colis = min(colis_max_geo, colis_max_poids)
    nb_couches_finales = total_colis // colis_par_couche
    
    return {
        "total": int(nb_couches_finales * colis_par_couche),
        "couches": int(nb_couches_finales),
        "poids_pal": (int(nb_couches_finales * colis_par_couche) * cp) + 25,
        "nb_pal_sol": nb_pal_sol,
        "plan": plan,
        "limit_cause": "POIDS" if colis_max_poids < colis_max_geo else "HAUTEUR"
    }

def mode_simple_valide():
    st.header("📦 Optimiseur de Palettisation Simple")
    
    # --- Sidebar : Contraintes de Stockage ---
    st.sidebar.header("🏢 Contraintes de Stockage")
    l_lisse = st.sidebar.selectbox("Longueur de lisse (mm)", [2700, 3600, 1350], index=0)
    p_max_lisse = st.sidebar.number_input("Poids max par niveau (kg)", value=3000)
    h_max = st.sidebar.number_input("Hauteur Max Rack (mm)", value=1800)
    
    st.sidebar.header("📦 Dimensions Produit")
    cl = st.sidebar.number_input("Long. Carton (mm)", value=400)
    cw = st.sidebar.number_input("Larg. Carton (mm)", value=300)
    ch = st.sidebar.number_input("Haut. Carton (mm)", value=250)
    cp = st.sidebar.number_input("Poids (kg)", value=10.0)
    overhang = st.sidebar.slider("Débordement (mm)", 0, 50, 0)

    # --- Comparaison automatique ---
    res800 = calculate_best_fit(800, l_lisse, h_max, cl, cw, ch, cp, p_max_lisse, overhang)
    res1000 = calculate_best_fit(1000, l_lisse, h_max, cl, cw, ch, cp, p_max_lisse, overhang)
    
    # Choix par défaut basé sur le nombre de colis total par niveau (lisse)
    best_option = "800x1200 (Euro)" if (res800["total"] * res800["nb_pal_sol"]) >= (res1000["total"] * res1000["nb_pal_sol"]) else "1000x1200 (VMF)"
    
    st.sidebar.header("📏 Support")
    target_pal = st.sidebar.selectbox("Type de Palette", ["800x1200 (Euro)", "1000x1200 (VMF)"], 
                                      index=0 if "800" in best_option else 1)
    
    current_res = res800 if "800" in target_pal else res1000
    W_pal = 800 if "800" in target_pal else 1000

    # --- Affichage Métriques ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Colis / Palette", current_res["total"])
    m2.metric("Poids / Palette", f"{round(current_res['poids_pal'], 1)} kg")
    
    charge_lisse = current_res['poids_pal'] * current_res['nb_pal_sol']
    m3.metric("Charge Lisse Total", f"{round(charge_lisse, 0)} kg")
    
    limit_color = "normal" if current_res["limit_cause"] == "HAUTEUR" else "off"
    m4.metric("Facteur Limitant", current_res["limit_cause"])

    if current_res["limit_cause"] == "POIDS":
        st.warning(f"⚠️ Le nombre de couches a été réduit car le poids max par lisse ({p_max_lisse}kg) est atteint.")

    # --- Visuels ---
    col1, col2 = st.columns([2,1])
    with col1:
        fig3d = go.Figure()
        draw_cube(fig3d, [0, W_pal], [0, 1200], [0, 150], "peru")
        for k in range(current_res["couches"]):
            color = "#3498db" if k%2==0 else "#e74c3c"
            for (x, y, dx, dy) in current_res["plan"]:
                z0 = 150 + (k*ch)
                fx, fy = (W_pal+2*overhang-x-dx, 1200+2*overhang-y-dy) if k%2==1 else (x, y)
                draw_cube(fig3d, [fx-overhang, fx+dx-overhang], [fy-overhang, fy+dy-overhang], [z0, z0+ch], color)
        fig3d.update_layout(scene=dict(aspectmode='data'), height=600)
        st.plotly_chart(fig3d, use_container_width=True)
    
    with col2:
        st.write("**Détails du niveau de lisse**")
        st.info(f"Capacité au sol : {current_res['nb_pal_sol']} palettes")
        st.write(f"- Capacité totale niveau : {current_res['total'] * current_res['nb_pal_sol']} colis")
        st.write(f"- Rendement : {round((current_res['total']*cl*cw*ch)/(W_pal*1200*h_max)*100,1)}%")

def main():
    st.set_page_config(page_title="Hub Logistique Expert", layout="wide")
    menu = st.sidebar.selectbox("Outil", ["Optimiseur Simple", "Déchargement Container"])
    if menu == "Optimiseur Simple": mode_simple_valide()
    else: st.info("Module Container en attente de vos instructions de mixité.")

if __name__ == "__main__": main()
