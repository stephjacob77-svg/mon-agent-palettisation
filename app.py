import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Expert Palettisation Hub", layout="wide")

# --- 2. FONCTIONS TECHNIQUES ---
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
    reste_y = L_max - (ny * cw)
    if reste_y >= cl:
        for i in range(int((nx * cl) // cw)):
            for j in range(int(reste_y // cl)): plan.append((i*cw, ny*cw + j*cl, cw, cl))
    return plan

def calculate_best_fit(W_pal, l_lisse, h_max, cl, cw, ch, cp, p_max_lisse, overhang):
    nb_pal_sol = int(l_lisse // W_pal)
    poids_max_par_pal = (p_max_lisse / nb_pal_sol) - 25
    plan = get_layer_plan(W_pal + 2*overhang, 1200 + 2*overhang, cl, cw)
    col_par_c = len(plan)
    if col_par_c == 0: return {"total": 0, "couches": 0, "plan": [], "nb_pal_sol": nb_pal_sol, "poids": 25, "cause": "DIM"}
    n_h = int((h_max - 150) // ch)
    n_p = int((poids_max_par_pal // cp) // col_par_c) if cp > 0 else 99
    n_final = max(0, min(n_h, n_p))
    return {
        "total": int(n_final * col_par_c), "couches": n_final, "plan": plan,
        "nb_pal_sol": nb_pal_sol, "poids": (n_final * col_par_c * cp) + 25,
        "cause": "POIDS" if n_p < n_h else "HAUTEUR"
    }

# --- 3. MODES ---
def mode_simple():
    st.header("📦 Optimiseur Simple")
    with st.sidebar:
        l_lisse = st.selectbox("Lisse (mm)", [2700, 3600, 1350])
        p_max = st.number_input("Poids Max Lisse (kg)", value=3000)
        h_max = st.number_input("Haut. Max (mm)", value=1800)
        cl, cw, ch = st.number_input("Long.", value=400), st.number_input("Larg.", value=300), st.number_input("Haut.", value=250)
        cp = st.number_input("Poids Unit (kg)", value=12.0)
        target_pal = st.selectbox("Palette", ["800x1200", "1000x1200"])
        w_pal = 800 if "800" in target_pal else 1000
    
    res = calculate_best_fit(w_pal, l_lisse, h_max, cl, cw, ch, cp, p_max, 0)
    st.metric("Colis Total", res["total"])
    
    fig = go.Figure()
    draw_cube(fig, 0, w_pal, 0, 1200, 0, 150, "peru")
    for k in range(res["couches"]):
        color = "#2196F3" if k % 2 == 0 else "#EF5350"
        for (x, y, dx, dy) in res["plan"]:
            z0 = 150 + (k * ch)
            draw_cube(fig, x, x+dx, y, y+dy, z0, z0+ch, color)
    fig.update_layout(scene=dict(aspectmode='data'), height=600)
    st.plotly_chart(fig, use_container_width=True)

def mode_container():
    st.header("🚢 Mode Container")
    with st.sidebar:
        l_l = st.selectbox("Lisse Stockage", [2700, 3600, 1350], key="cll")
        p_m = st.number_input("Capacité Lisse", value=3000, key="cpm")
        h_m = st.number_input("Haut. Max", value=1800, key="chm")
        t_w = st.radio("Palette", [800, 1000], horizontal=True)

    df = pd.DataFrame([
        {"Référence": "REF_A", "Long": 400, "Larg": 300, "Haut": 250, "Poids": 12, "Quantité": 145},
        {"Référence": "REF_B", "Long": 600, "Larg": 400, "Haut": 300, "Poids": 15, "Quantité": 55}
    ])
    df_c = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    # Calculs simplifiés pour débloquer l'affichage
    pals_data = []
    reliquats = []
    for _, r in df_c.iterrows():
        res = calculate_best_fit(t_w, l_l, h_m, r['Long'], r['Larg'], r['Haut'], r['Poids'], p_m, 0)
        if res['total'] > 0:
            nb_p = r['Quantité'] // res['total']
            reste = r['Quantité'] % res['total']
            if nb_p > 0: pals_data.append({"Réf": r['Référence'], "Pals": int(nb_p), "Poids": res['poids']})
            if reste > 0: reliquats.append({"Réf": r['Référence'], "Qte": reste, "Poids": reste*r['Poids']})

    st.write("### 🏢 Analyse des Lisses")
    if pals_data:
        st.table(pals_data)
        all_weights = []
        for p in pals_data:
            for _ in range(p['Pals']): all_weights.append(p['Poids'])
        if reliquats: all_weights.append(sum(r['Poids'] for r in reliquats) + 25)
        
        # Affichage occupation
        nb_p_lisse = int(l_l // t_w)
        nb_lisses = math.ceil(len(all_weights) / nb_p_lisse)
        st.metric("Nombre de lisses nécessaires", nb_lisses)

# --- 4. NAVIGATION ---
def main():
    choice = st.sidebar.radio("Navigation", ["Optimiseur Simple", "Container"])
    if choice == "Optimiseur Simple": mode_simple()
    else: mode_container()

if __name__ == "__main__":
    main()
