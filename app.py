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

# --- MODE 1 : OPTIMISEUR SIMPLE (VERSION VALIDÉE) ---
def mode_simple_valide():
    st.header("📦 Optimiseur de Palettisation Simple")
    # Conserve les paramètres sidebar déjà en place dans votre version précédente
    cl = st.sidebar.number_input("Long. Carton", value=400)
    cw = st.sidebar.number_input("Larg. Carton", value=300)
    ch = st.sidebar.number_input("Haut. Carton", value=250)
    overhang = st.sidebar.slider("Débordement", 0, 50, 0)
    h_max = st.sidebar.number_input("Hauteur Max", value=1800)
    
    W_pal = 800 # Version par défaut validée
    W_max, L_max = W_pal + 2*overhang, 1200 + 2*overhang
    plan = get_mixed_layer_plan(W_max, L_max, cl, cw)
    nb_c = int((h_max - 150) // ch)
    
    col1, col2 = st.columns([2,1])
    with col1:
        fig3d = go.Figure()
        draw_cube(fig3d, [0, 800], [0, 1200], [0, 150], "peru")
        for k in range(nb_c):
            color = "#3498db" if k%2==0 else "#e74c3c"
            for (x, y, dx, dy) in plan:
                z0 = 150 + (k*ch)
                fx, fy = (W_max-x-dx, L_max-y-dy) if k%2==1 else (x, y)
                draw_cube(fig3d, [fx-overhang, fx+dx-overhang], [fy-overhang, fy+dy-overhang], [z0, z0+ch], color)
        st.plotly_chart(fig3d)
    with col2:
        st.metric("Colis / Palette", len(plan)*nb_c)

# --- MODE 2 : CONTAINER (TABLEAU DE BORD PRO) ---
def mode_container_pro():
    st.header("🚢 Tableau de Bord : Dépotage Container")
    
    # 3.2 - Mixité
    mixite = st.sidebar.radio("Autoriser la mixité sur palette ?", ["Non (Mono-référence)", "Oui (Optimisé)"])
    
    uploaded_file = st.file_uploader("Importer Packing List (CSV)", type=['csv'])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.DataFrame([{"Référence": "Ref_A", "Long": 400, "Larg": 300, "Haut": 250, "Poids": 10, "Quantité": 150}])
    
    data = st.data_editor(df, num_rows="dynamic")
    
    h_max = st.sidebar.number_input("Hauteur Max Racks (mm)", value=1800)
    
    # 3.3 - Comparaison automatique 800 vs 1000
    res_800 = 0
    res_1000 = 0
    for _, row in data.iterrows():
        p800 = len(get_mixed_layer_plan(800, 1200, row["Long"], row["Larg"])) * ((h_max-150)//row["Haut"])
        p1000 = len(get_mixed_layer_plan(1000, 1200, row["Long"], row["Larg"])) * ((h_max-150)//row["Haut"])
        if p800 > 0: res_800 += math.ceil(row["Quantité"] / p800)
        if p1000 > 0: res_1000 += math.ceil(row["Quantité"] / p1000)
    
    best_w = 800 if res_800 <= res_1000 else 1000
    st.info(f"💡 Recommandation : Utilisez des palettes **{best_w}x1200** ({min(res_800, res_1000)} palettes au total).")

    st.subheader("📋 Rapport de déchargement")
    for _, row in data.iterrows():
        with st.expander(f"Fiche de déchargement - {row['Référence']}"):
            st.write(f"**Quantité :** {row['Quantité']} | **Palette conseillée :** {best_w}x1200")
            # Ici on génère les visuels 2D de pose (Phase 3.4)
            st.button(f"Générer PDF pour {row['Référence']}", key=row['Référence'])

# --- MAIN ---
def main():
    st.set_page_config(page_title="Hub Logistique", layout="wide")
    menu = st.sidebar.selectbox("Outil", ["Optimiseur Simple", "Déchargement Container"])
    
    if menu == "Optimiseur Simple":
        mode_simple_valide()
    else:
        mode_container_pro()

if __name__ == "__main__":
    main()
