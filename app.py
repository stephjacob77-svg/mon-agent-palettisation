import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="WMS Expert Pro v9.9.3", layout="wide")

# --- CATALOGUE ---
if 'catalogue' not in st.session_state:
    st.session_state.catalogue = pd.DataFrame([
        {"REF": "COLIS_PRO_A", "L": 400, "W": 300, "H": 200, "P": 20.0},
        {"REF": "COLIS_PRO_B", "L": 300, "W": 200, "H": 150, "P": 5.0}
    ])

# --- LOGIQUE DE CALCUL DES PALETTES PAR LISSE ---
def calculer_capacite_lisse(L_lisse, W_pal):
    # On garde un jeu de sécurité de 50mm entre palettes et montants
    nb_pal = int(L_lisse // (W_pal + 50))
    if nb_pal == 0 and L_lisse >= W_pal: nb_pal = 1 # Cas 900mm
    return nb_pal

# --- MOTEUR TETRIS ---
def get_optimal_layer(W_pal, L_pal, cl, cw):
    def strategy(W, L, c_l, c_w):
        plan = []
        nx, ny = int(W // c_l), int(L // c_w)
        for i in range(nx):
            for j in range(ny): plan.append({'x': i * c_l, 'y': j * c_w, 'w': c_l, 'h': c_w})
        return plan
    s1 = strategy(W_pal, L_pal, cl, cw)
    s2 = strategy(W_pal, L_pal, cw, cl)
    return s1 if len(s1) >= len(s2) else s2

def get_crossed_layer(plan, W_pal, L_pal):
    return [{'x': W_pal - p['x'] - p['w'], 'y': L_pal - p['y'] - p['h'], 'w': p['w'], 'h': p['h']} for p in plan]

# --- FONCTIONS GRAPHIQUES ---
def draw_box(fig, x0, x1, y0, y1, z0, z1, color, opacity=1.0):
    fig.add_trace(go.Mesh3d(
        x=[x0, x1, x1, x0, x0, x1, x1, x0], y=[y0, y0, y1, y1, y0, y0, y1, y1], z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=opacity, flatshading=True, showlegend=False
    ))

def draw_real_pallet(fig, x_off, w_p, l_p, z_off):
    c_wood = "#8D6E63"
    draw_box(fig, x_off, x_off+w_p, 0, l_p, z_off+125, z_off+150, c_wood)
    for dx in [0, w_p-100]:
        for dy in [0, l_p-100]: draw_box(fig, x_off+dx, x_off+dx+100, dy, dy+100, z_off, z_off+125, c_wood)

# --- INTERFACE ---
st.sidebar.title("🏗️ WMS Pro v9.9.3")
menu = st.sidebar.radio("Navigation", ["Simulateur", "Catalogue Articles", "Paramètres Rack"])

if menu == "Catalogue Articles":
    st.header("Gestion du Catalogue")
    st.session_state.catalogue = st.data_editor(st.session_state.catalogue, num_rows="dynamic")

elif menu == "Paramètres Rack":
    st.header("Dimensions des Lisses Standards")
    # Menu déroulant basé sur les standards du marché
    options_lisses = {
        "950 mm (1 Palette EURO/VMF)": 950,
        "1850 mm (2 Palettes EURO)": 1850,
        "2250 mm (2 Palettes VMF)": 2250,
        "2700 mm (3 Palettes EURO / 2 VMF)": 2700,
        "3600 mm (4 Palettes EURO / 3 VMF)": 3600
    }
    choix = st.selectbox("Sélectionnez la longueur de lisse réelle", list(options_lisses.keys()), index=3)
    st.session_state.l_lisse = options_lisses[choix]
    st.session_state.capa_lisse = st.number_input("Charge Max / Niveau (kg)", value=3000)
    st.session_state.h_utile = st.number_input("Hauteur Utile Alvéole (mm)", value=1800)

else:
    # Initialisation par défaut si besoin
    if 'l_lisse' not in st.session_state: 
        st.session_state.l_lisse, st.session_state.capa_lisse, st.session_state.h_utile = 2700, 3000, 1800
    
    with st.sidebar:
        ref = st.selectbox("Article", st.session_state.catalogue["REF"].tolist())
        fmt_pal = st.selectbox("Type de Palette", ["800x1200 (EURO)", "1000x1200 (VMF/STD)"])
        w_p = 800 if "800" in fmt_pal else 1000

    item = st.session_state.catalogue[st.session_state.catalogue["REF"] == ref].iloc[0]
    
    # 1. CALCUL CAPACITÉ ET POSE
    nb_pal_possibles = calculer_capacite_lisse(st.session_state.l_lisse, w_p)
    plan_layer = get_optimal_layer(w_p, 1200, item['L'], item['W'])
    
    # 2. OPTIMISATION HAUTEUR / POIDS
    max_h_theoretical = int((st.session_state.h_utile - 150) // item['H'])
    nb_couches = max_h_theoretical
    limite = "Hauteur"

    while nb_couches > 0:
        poids_niveau = (nb_couches * len(plan_layer) * item['P']) * nb_pal_possibles
        if poids_niveau <= st.session_state.capa_lisse: break
        nb_couches -= 1
        limite = "Poids"

    # 3. KPI
    st.header(f"Simulation : {ref} sur Lisse {st.session_state.l_lisse}mm")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nombre de Palettes", nb_pal_possibles)
    c2.metric("Couches / Palette", nb_couches)
    c3.metric("Poids Total Niveau", f"{int(poids_niveau)} kg")
    c4.warning(f"Limité par : {limite}")

    # 4. VUE 3D RACK
    f_rack = go.Figure()
    # 4 Montants
    for px in [-100, st.session_state.l_lisse]:
        for py in [0, 1100]: draw_box(f_rack, px, px+100, py, py+100, -150, st.session_state.h_utile + 50, "#455A64")
    # Lisses
    draw_box(f_rack, 0, st.session_state.l_lisse, 0, 80, -100, 0, "orange")
    draw_box(f_rack, 0, st.session_state.l_lisse, 1120, 1200, -100, 0, "orange")

    # LOGIQUE DE POSITIONNEMENT
    if nb_pal_possibles == 1:
        positions = [(st.session_state.l_lisse - w_p) / 2] # Centrée
    elif w_p == 1000 and st.session_state.l_lisse == 2700:
        positions = [0, st.session_state.l_lisse - w_p] # Extrémités pour 100x120
    else:
        # Répartition équilibrée
        gap = (st.session_state.l_lisse - (nb_pal_possibles * w_p)) / (nb_pal_possibles + 1)
        positions = [gap + i*(w_p + gap) for i in range(nb_pal_possibles)]

    for x in positions:
        draw_real_pallet(f_rack, x, w_p, 1200, 0)
        for k in range(nb_couches):
            p = plan_layer if k % 2 == 0 else get_crossed_layer(plan_layer, w_p, 1200)
            col = "#1E88E5" if k % 2 == 0 else "#E53935"
            for b in p:
                draw_box(f_rack, x+b['x'], x+b['x']+b['w'], b['y'], b['y']+b['h'], 150+(k*item['H']), 150+((k+1)*item['H']), col)
    
    f_rack.update_layout(scene=dict(aspectmode='data'), height=750)
    st.plotly_chart(f_rack, use_container_width=True)
