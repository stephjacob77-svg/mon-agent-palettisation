import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert Palettisation Hub", layout="wide")

# --- FONCTIONS TECHNIQUES ---

def draw_cube(fig, x_min, x_max, y_min, y_max, z_min, z_max, color, opacity=0.8):
    fig.add_trace(go.Mesh3d(
        x=[x_min, x_max, x_max, x_min, x_min, x_max, x_max, x_min],
        y=[y_min, y_min, y_max, y_max, y_min, y_min, y_max, y_max],
        z=[z_min, z_min, z_min, z_min, z_max, z_max, z_max, z_max],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=opacity, flatshading=True, showlegend=False
    ))

def get_layer_plan(W_max, L_max, cl, cw):
    plan = []
    # 1. Remplissage principal
    nx, ny = int(W_max // cl), int(L_max // cw)
    for i in range(nx):
        for j in range(ny): plan.append({'x': i*cl, 'y': j*cw, 'w': cl, 'h': cw})
    
    # 2. Remplissage du reste en X (rotation des colis)
    reste_x = W_max - (nx * cl)
    if reste_x >= cw:
        for i in range(int(reste_x // cw)):
            for j in range(int(L_max // cl)):
                plan.append({'x': nx*cl + i*cw, 'y': j*cl, 'w': cw, 'h': cl})
    
    # 3. Remplissage du reste en Y (rotation des colis)
    reste_y = L_max - (ny * cw)
    if reste_y >= cl:
        for i in range(int((nx * cl) // cw)):
            for j in range(int(reste_y // cl)):
                plan.append({'x': i*cw, 'y': ny*cw + j*cl, 'w': cw, 'h': cl})
    return plan

def create_top_view(plan, w_pal, w_max_c, l_max_c, overhang, mirrored, title, color):
    fig = go.Figure()
    
    # On ajoute un tracé invisible pour "forcer" les limites des axes
    fig.add_trace(go.Scatter(x=[0, w_pal], y=[0, 1200], mode="markers", marker=dict(opacity=0)))

    # Dessin de la palette (Le contour marron)
    fig.add_shape(type="rect", x0=0, y0=0, x1=w_pal, y1=1200, line=dict(color="#5D4037", width=5), fillcolor="rgba(0,0,0,0)")

    # Dessin des colis (Chaque petit rectangle)
    for p in plan:
        # Calcul de l'effet miroir pour les couches paires
        if mirrored:
            fx = w_max_c - p['x'] - p['w']
            fy = l_max_c - p['y'] - p['h']
        else:
            fx, fy = p['x'], p['y']
            
        fig.add_shape(
            type="rect",
            x0=fx - overhang, y0=fy - overhang,
            x1=fx + p['w'] - overhang, y1=fy + p['h'] - overhang,
            fillcolor=color,
            line=dict(color="white", width=2),
            opacity=0.8
        )

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=18)),
        xaxis=dict(range=[-50, w_pal+50], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[-50, 1250], showgrid=False, zeroline=False, visible=False, scaleanchor="x"),
        margin=dict(l=5, r=5, t=50, b=5),
        height=400,
        plot_bgcolor='white'
    )
    return fig

def calculate_best_fit(W_pal, l_lisse, h_max, cl, cw, ch, cp, p_max_lisse, overhang):
    nb_pal_sol = int(l_lisse // W_pal)
    poids_max_par_pal = (p_max_lisse / nb_pal_sol) - 25
    plan = get_layer_plan(W_pal + 2*overhang, 1200 + 2*overhang, cl, cw)
    colis_par_couche = len(plan)
    
    if colis_par_couche == 0: 
        return {"total": 0, "couches": 0, "plan": [], "nb_pal_sol": nb_pal_sol, "poids": 25, "cause": "DIMENSIONS ❌"}
    
    nb_couches_h = int((h_max - 150) // ch)
    nb_couches_p = int((poids_max_par_pal // cp) // colis_par_couche) if cp > 0 else 99
    
    nb_final = max(0, min(nb_couches_h, nb_couches_p))
    cause = "POIDS ⚖️" if nb_couches_p < nb_couches_h else "HAUTEUR 📏"
    
    return {
        "total": int(nb_final * colis_par_couche),
        "couches": int(nb_final),
        "plan": plan,
        "nb_pal_sol": nb_pal_sol,
        "poids": (nb_final * colis_par_couche * cp) + 25,
        "cause": cause
    }

# --- MODE 1 : SIMPLE ---
def mode_simple():
    st.header("📦 Optimiseur de Palettisation Simple")
    with st.sidebar:
        l_lisse = st.selectbox("Longueur de lisse (mm)", [2700, 3600, 1350])
        p_max_lisse = st.number_input("Poids max Lisse (kg)", value=3000)
        h_max_rack = st.number_input("Hauteur Max Rack (mm)", value=1800)
        cl = st.number_input("Long. Colis (mm)", value=400)
        cw = st.number_input("Larg. Colis (mm)", value=300)
        ch = st.number_input("Haut. Colis (mm)", value=250)
        cp = st.number_input("Poids Colis (kg)", value=12.0)
        overhang = st.slider("Débordement (mm)", 0, 50, 0)
        target_pal = st.selectbox("Type de Palette", ["800x1200", "1000x1200"])
        w_pal = 800 if "800" in target_pal else 1000

    res = calculate_best_fit(w_pal, l_lisse, h_max_rack, cl, cw, ch, cp, p_max_lisse, overhang)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Colis / Palette", res["total"])
    c2.metric("Poids / Palette", f"{round(res['poids'], 1)} kg")
    c3.metric("Palettes / Lisse", res["nb_pal_sol"])
    c4.metric("Facteur Limitant", res["cause"])

    tab1, tab2 = st.tabs(["📊 Vue 3D", "📋 Plans 2D"])
    
    with tab1:
        fig3d = go.Figure()
        draw_cube(fig3d, 0, w_pal, 0, 1200, 0, 150, "#8D6E63")
        for k in range(res["couches"]):
            color = "#2196F3" if k % 2 == 0 else "#EF5350"
            for p in res["plan"]:
                z0 = 150 + (k * ch)
                if k % 2 == 1: # Miroir pour couches paires
                    fx = (w_pal + 2*overhang) - p['x'] - p['w']
                    fy = (1200 + 2*overhang) - p['y'] - p['h']
                else:
                    fx, fy = p['x'], p['y']
                draw_cube(fig3d, fx-overhang, fx+p['w']-overhang, fy-overhang, fy+p['h']-overhang, z0, z0+ch, color)
        fig3d.update_layout(scene=dict(aspectmode='data'), height=600)
        st.plotly_chart(fig3d, use_container_width=True)
    
    with tab2:
        v1, v2 = st.columns(2)
        v1.plotly_chart(create_top_view(res["plan"], w_pal, w_pal+2*overhang, 1200+2*overhang, overhang, False, "Couche 1 (Bleue)", "#2196F3"), use_container_width=True)
        v2.plotly_chart(create_top_view(res["plan"], w_pal, w_pal+2*overhang, 1200+2*overhang, overhang, True, "Couche 2 (Rouge)", "#EF5350"), use_container_width=True)

# --- MODE 2 : CONTAINER ---
def mode_container():
    st.header("🚢 Gestion Container")
    with st.sidebar:
        l_lisse = st.selectbox("Lisse (mm)", [2700, 3600, 1350], key="c1")
        p_max = st.number_input("Poids Max (kg)", value=3000, key="c2")
        h_max = st.number_input("Haut Max (mm)", value=1800, key="c3")
        t_w = st.radio("Support", [800, 1000], horizontal=True, key="c4")

    df = pd.DataFrame([
        {"Référence": "REF_A", "Long": 400, "Larg": 300, "Haut": 250, "Poids": 12, "Quantité": 145},
        {"Référence": "REF_B", "Long": 600, "Larg": 400, "Haut": 300, "Poids": 15, "Quantité": 55}
    ])
    df_c = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    # Calcul simple d'occupation
    all_pals = []
    for _, r in df_c.iterrows():
        res = calculate_best_fit(t_w, l_lisse, h_max, r['Long'], r['Larg'], r['Haut'], r['Poids'], p_max, 0)
        if res['total'] > 0:
            nb = math.ceil(r['Quantité'] / res['total'])
            for _ in range(nb): all_pals.append(res['poids'])
    
    st.metric("Total Palettes à stocker", len(all_pals))
    nb_p_lisse = int(l_lisse // t_w)
    st.metric("Lisses nécessaires estimées", math.ceil(len(all_pals) / nb_p_lisse))

def main():
    menu = st.sidebar.radio("Navigation", ["Optimiseur Simple", "Container"])
    if menu == "Optimiseur Simple": mode_simple()
    else: mode_container()

if __name__ == "__main__":
    main()
