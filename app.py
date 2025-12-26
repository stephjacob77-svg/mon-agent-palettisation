import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math

# --- CONFIGURATION ET STYLE ---
st.set_page_config(page_title="Expert Palettisation Hub", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .css-1r6slb0 { border: 1px solid #e0e0e0; border-radius: 10px; padding: 20px; background: white; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS TECHNIQUES (MOTEUR DE CALCUL) ---

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
    nx, ny = int(W_max // cl), int(L_max // cw)
    for i in range(nx):
        for j in range(ny): plan.append((i*cl, j*cw, cl, cw))
    reste_x = W_max - (nx * cl)
    if reste_x >= cw:
        for i in range(int(reste_x // cw)):
            for j in range(int(L_max // cl)): plan.append((nx*cl + i*cw, j*cl, cw, cl))
    return plan

def create_top_view(plan, w_pal, w_max_c, l_max_c, overhang, mirrored, title, color):
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, y0=0, x1=w_pal, y1=1200, line=dict(color="#5D4037", width=4))
    for (x, y, dx, dy) in plan:
        fx, fy = (w_max_c - x - dx, l_max_c - y - dy) if mirrored else (x, y)
        fig.add_shape(type="rect", x0=fx-overhang, y0=fy-overhang, x1=fx+dx-overhang, y1=fy+dy-overhang, 
                       fillcolor=color, opacity=0.6, line=dict(color="white", width=1))
    fig.update_layout(title=dict(text=title, x=0.5), xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"), margin=dict(l=10,r=10,t=40,b=10), height=300, plot_bgcolor='rgba(0,0,0,0)')
    return fig

def calculate_best_fit(W_pal, l_lisse, h_max, cl, cw, ch, cp, p_max_lisse, overhang):
    """Calcule le bridage réel poids/hauteur"""
    nb_pal_sol = int(l_lisse // W_pal)
    poids_max_par_pal = (p_max_lisse / nb_pal_sol) - 25
    plan = get_layer_plan(W_pal + 2*overhang, 1200 + 2*overhang, cl, cw)
    colis_par_couche = len(plan)
    
    if colis_par_couche == 0: return {"total": 0, "couches": 0, "plan": [], "nb_pal_sol": nb_pal_sol, "poids": 25, "cause": "DIM"}
    
    nb_couches_h = int((h_max - 150) // ch)
    nb_couches_p = int((poids_max_par_pal // cp) // colis_par_couche) if cp > 0 else 99
    
    nb_final = min(nb_couches_h, nb_couches_p)
    if (colis_par_couche * cp) > poids_max_par_pal: nb_final = 0
    
    return {
        "total": int(nb_final * colis_par_couche),
        "couches": int(nb_final),
        "plan": plan,
        "nb_pal_sol": nb_pal_sol,
        "poids": (nb_final * colis_par_couche * cp) + 25,
        "cause": "POIDS" if nb_couches_p < nb_couches_h else "HAUTEUR"
    }

# --- MODE 1 : OPTIMISEUR SIMPLE ---

def mode_simple():
    st.header("📦 Optimiseur de Palettisation Simple")
    
    with st.sidebar:
        st.subheader("⚙️ Paramètres")
        l_lisse = st.selectbox("Longueur de lisse (mm)", [2700, 3600, 1350])
        p_max_lisse = st.number_input("Poids max Lisse (kg)", value=3000)
        h_max_rack = st.number_input("Hauteur Max Rack (mm)", value=1800)
        cl = st.number_input("Long. (mm)", value=400)
        cw = st.number_input("Larg. (mm)", value=300)
        ch = st.number_input("Haut. (mm)", value=250)
        cp = st.number_input("Poids (kg)", value=12.0)
        overhang = st.slider("Débordement (mm)", 0, 50, 0)
        target_pal = st.selectbox("Type de Palette", ["800x1200", "1000x1200"])
        w_pal = 800 if "800" in target_pal else 1000

    res = calculate_best_fit(w_pal, l_lisse, h_max_rack, cl, cw, ch, cp, p_max_lisse, overhang)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Colis / Palette", res["total"])
    c2.metric("Poids / Palette", f"{round(res['poids'], 1)} kg")
    c3.metric("Palettes / Lisse", res["nb_pal_sol"])
    c4.metric("Limite", res["cause"])

    tab1, tab2 = st.tabs(["📊 Vue 3D", "📋 Plans 2D"])
    with tab1:
        fig = go.Figure()
        draw_cube(fig, 0, w_pal, 0, 1200, 0, 150, "#8D6E63")
        for k in range(res["couches"]):
            color = "#2196F3" if k % 2 == 0 else "#EF5350"
            for (x, y, dx, dy) in res["plan"]:
                z0 = 150 + (k * ch)
                fx, fy = (w_pal + 2*overhang - x - dx, 1200 + 2*overhang - y - dy) if k % 2 == 1 else (x, y)
                draw_cube(fig, fx-overhang, fx+dx-overhang, fy-overhang, fy+dy-overhang, z0, z0+ch, color)
        fig.update_layout(scene=dict(aspectmode='data'), height=600)
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        v1, v2 = st.columns(2)
        v1.plotly_chart(create_top_view(res["plan"], w_pal, w_pal+2*overhang, 1200+2*overhang, overhang, False, "Impair", "#2196F3"))
        v2.plotly_chart(create_top_view(res["plan"], w_pal, w_pal+2*overhang, 1200+2*overhang, overhang, True, "Pair", "#EF5350"))

# --- MODE 2 : CONTAINER ---

def mode_container():
    st.header("🚢 Gestion de Déchargement Container")
    
    with st.sidebar:
        l_lisse = st.selectbox("Lisse Stockage (mm)", [2700, 3600, 1350])
        p_max_lisse = st.number_input("Capacité Lisse (kg)", value=3000)
        h_max_rack = st.number_input("Haut. Max (mm)", value=1800)

    st.write("### 📥 Import Packing List")
    uploaded = st.file_uploader("Fichier CSV", type=['csv'])
    if uploaded:
        df = pd.read_csv(uploaded)
    else:
        df = pd.DataFrame([
            {"Référence": "REF_A", "Long": 400, "Larg": 300, "Haut": 250, "Poids": 12, "Quantité": 100},
            {"Référence": "REF_B", "Long": 600, "Larg": 400, "Haut": 300, "Poids": 15, "Quantité": 50}
        ])
    
    df_c = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    # Comparaison Stratégique
    p800 = 0
    p1000 = 0
    for _, r in df_c.iterrows():
        res8 = calculate_best_fit(800, l_lisse, h_max_rack, r['Long'], r['Larg'], r['Haut'], r['Poids'], p_max_lisse, 0)
        res1 = calculate_best_fit(1000, l_lisse, h_max_rack, r['Long'], r['Larg'], r['Haut'], r['Poids'], p_max_lisse, 0)
        if res8['total'] > 0: p800 += math.ceil(r['Quantité'] / res8['total'])
        if res1['total'] > 0: p1000 += math.ceil(r['Quantité'] / res1['total'])

    st.info(f"💡 Analyse : 800x1200 = {p800} pals | 1000x1200 = {p1000} pals")
    
    st.write("### 📋 Fiches de Déchargement")
    for _, row in df_c.iterrows():
        with st.expander(f"Référence {row['Référence']}"):
            st.write(f"Quantité totale : {row['Quantité']} colis")
            # Ici on pourra ajouter les boutons PDF et plans spécifiques

# --- MAIN NAVIGATION ---

def main():
    menu = st.sidebar.radio("Navigation", ["Optimiseur Simple", "Container"])
    if menu == "Optimiseur Simple":
        mode_simple()
    else:
        mode_container()

if __name__ == "__main__":
    main()
