import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# --- CONFIGURATION ET STYLE ---
st.set_page_config(page_title="WMS Expert Pro v9.9.4", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION SESSION STATE ---
if 'catalogue' not in st.session_state:
    st.session_state.catalogue = pd.DataFrame([
        {"REF": "BOITE_LOURDE_A", "L": 400, "W": 300, "H": 200, "P": 25.0, "COLOR": "#1E88E5"},
        {"REF": "BOITE_LEGERE_B", "L": 300, "W": 200, "H": 150, "P": 5.0, "COLOR": "#E53935"}
    ])

# --- MOTEUR DE CALCULS ---

def calculer_capacite_lisse(L_lisse, W_pal):
    """Calcule combien de palettes rentrent avec un jeu de 50mm min entre chaque."""
    nb_pal = int(L_lisse // (W_pal + 50))
    if nb_pal == 0 and L_lisse >= W_pal: nb_pal = 1
    return nb_pal

def get_optimal_layer(W_pal, L_pal, cl, cw):
    """Stratégie Tetris pour optimiser le nombre de colis par couche."""
    def strategy(W, L, c_l, c_w):
        plan = []
        nx, ny = int(W // c_l), int(L // c_w)
        for i in range(nx):
            for j in range(ny):
                plan.append({'x': i * c_l, 'y': j * c_w, 'w': c_l, 'h': c_w})
        return plan
    s1 = strategy(W_pal, L_pal, cl, cw)
    s2 = strategy(W_pal, L_pal, cw, cl)
    return s1 if len(s1) >= len(s2) else s2

def get_crossed_layer(plan, W_pal, L_pal):
    """Inverse les coordonnées pour le gerbage croisé (stabilité)."""
    return [{'x': W_pal - p['x'] - p['w'], 'y': L_pal - p['y'] - p['h'], 'w': p['w'], 'h': p['h']} for p in plan]

# --- FONCTIONS GRAPHIQUES ---

def draw_box(fig, x0, x1, y0, y1, z0, z1, color, opacity=1.0, line_color="black"):
    """Dessine un parallélépipède 3D."""
    fig.add_trace(go.Mesh3d(
        x=[x0, x1, x1, x0, x0, x1, x1, x0],
        y=[y0, y0, y1, y1, y0, y0, y1, y1],
        z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
        j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
        k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=opacity, flatshading=True, showlegend=False
    ))

def draw_real_pallet(fig, x_off, w_p, l_p, z_off):
    """Dessine la structure bois d'une palette."""
    c_wood = "#8D6E63"
    # Plateau
    draw_box(fig, x_off, x_off+w_p, 0, l_p, z_off+125, z_off+150, c_wood)
    # Plots
    for dx in [0, w_p-100]:
        for dy in [0, l_p-100]:
            draw_box(fig, x_off+dx, x_off+dx+100, dy, dy+100, z_off, z_off+125, c_wood)

# --- INTERFACE UTILISATEUR (ONGLETS) ---

st.sidebar.title("🏗️ WMS Expert Pro")
st.sidebar.info("Système d'aide à la décision Stockage")

tab1, tab2, tab3 = st.tabs(["📊 Simulateur de Rack", "📖 Catalogue Articles", "⚙️ Paramètres Rack"])

# --- ONGLET 3 : PARAMÈTRES RACK (Définit les constantes) ---
with tab3:
    st.header("Configuration du Rayonnage")
    col1, col2 = st.columns(2)
    with col1:
        options_lisses = {
            "950 mm (1 Palette EURO/VMF)": 950,
            "1850 mm (2 Palettes EURO)": 1850,
            "2250 mm (2 Palettes VMF)": 2250,
            "2700 mm (3 Palettes EURO / 2 VMF)": 2700,
            "3600 mm (4 Palettes EURO / 3 VMF)": 3600
        }
        choix_l = st.selectbox("Longueur de lisse (mm)", list(options_lisses.keys()), index=3)
        l_lisse = options_lisses[choix_l]
        h_utile = st.number_input("Hauteur utile de l'alvéole (mm)", value=1800)
    with col2:
        capa_lisse = st.number_input("Charge maximum admissible par paire de lisses (kg)", value=3000)
        poids_palette_vide = st.number_input("Poids palette bois vide (kg)", value=25)

# --- ONGLET 2 : CATALOGUE ---
with tab2:
    st.header("Gestion des Références")
    st.session_state.catalogue = st.data_editor(st.session_state.catalogue, num_rows="dynamic")

# --- ONGLET 1 : SIMULATEUR ---
with tab1:
    with st.sidebar:
        st.divider()
        ref = st.selectbox("Sélectionner l'article", st.session_state.catalogue["REF"].tolist())
        fmt_pal = st.selectbox("Format Palette cible", ["800x1200 (EURO)", "1000x1200 (VMF/STD)"])
        w_p = 800 if "800" in fmt_pal else 1000
    
    item = st.session_state.catalogue[st.session_state.catalogue["REF"] == ref].iloc[0]
    
    # CALCULS
    nb_pal_possibles = calculer_capacite_lisse(l_lisse, w_p)
    plan_layer = get_optimal_layer(w_p, 1200, item['L'], item['W'])
    
    # Optimisation couches vs Poids
    max_h_theo = int((h_utile - 150) // item['H'])
    nb_couches = max_h_theo
    alerte_poids = False
    
    while nb_couches > 0:
        poids_total_niveau = ( (nb_couches * len(plan_layer) * item['P']) + poids_palette_vide ) * nb_pal_possibles
        if poids_total_niveau <= capa_lisse:
            break
        nb_couches -= 1
        alerte_poids = True

    # KPI
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Palettes / Niveau", nb_pal_possibles)
    c2.metric("Colis / Palette", len(plan_layer) * nb_couches)
    c3.metric("Poids Total Niveau", f"{int(poids_total_niveau)} kg")
    if alerte_poids:
        c4.error(f"⚠️ Limité par le poids ({capa_lisse}kg)")
    else:
        c4.success("✅ Limité par la hauteur")

    # DESSIN 3D
    fig = go.Figure()

    # Dessin des Montants (Échelles)
    for px in [-100, l_lisse]:
        for py in [0, 1100]:
            draw_box(fig, px, px+100, py, py+100, -150, h_utile + 100, "#455A64", opacity=0.8)

    # Dessin des Lisses
    draw_box(fig, 0, l_lisse, 0, 80, -100, 0, "orange")
    draw_box(fig, 0, l_lisse, 1120, 1200, -100, 0, "orange")

    # Logique de répartition des palettes sur la lisse
    if nb_pal_possibles == 1:
        positions = [(l_lisse - w_p) / 2]
    elif w_p == 1000 and l_lisse == 2700:
        # Cas spécifique demandé : Pose de part et d'autre (aux extrémités)
        positions = [0, l_lisse - w_p]
    else:
        # Répartition standard équilibrée
        gap = (l_lisse - (nb_pal_possibles * w_p)) / (nb_pal_possibles + 1)
        positions = [gap + i*(w_p + gap) for i in range(nb_pal_possibles)]

    # Affichage des palettes et colis
    for x_off in positions:
        draw_real_pallet(fig, x_off, w_p, 1200, 0)
        for k in range(nb_couches):
            # Alternance des couches pour le gerbage croisé
            current_plan = plan_layer if k % 2 == 0 else get_crossed_layer(plan_layer, w_p, 1200)
            for b in current_plan:
                draw_box(fig, 
                         x_off + b['x'], x_off + b['x'] + b['w'], 
                         b['y'], b['y'] + b['h'], 
                         150 + (k * item['H']), 150 + ((k+1) * item['H']), 
                         item['COLOR'], opacity=0.9)

    fig.update_layout(
        scene=dict(
            aspectmode='data',
            xaxis_title="Longueur Lisse (X)",
            yaxis_title="Profondeur (Y)",
            zaxis_title="Hauteur (Z)"
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        height=800
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption(f"Note technique : Alvéole paramétrée pour une longueur de {l_lisse}mm. "
               f"Jeu de sécurité calculé entre palettes : 50mm.")
