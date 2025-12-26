import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert WMS Pro v9.8", layout="wide")

# --- GESTION DU CATALOGUE (ÉTAT SESSION) ---
if 'catalogue' not in st.session_state:
    st.session_state.catalogue = pd.DataFrame([
        {"REF": "CARTON_A", "L": 300, "W": 200, "H": 150, "P": 12.0},
        {"REF": "CARTON_B", "L": 400, "W": 300, "H": 200, "P": 18.5}
    ])

# --- MOTEUR DE CALCUL TETRIS ---
def get_optimal_layer(W_pal, L_pal, cl, cw):
    def strategy(W, L, c_l, c_w):
        plan = []
        nx, ny = int(W // c_l), int(L // c_w)
        for i in range(nx):
            for j in range(ny): plan.append({'x': i * c_l, 'y': j * c_w, 'w': c_l, 'h': c_w})
        rx, ry = W - (nx * c_l), L - (ny * c_w)
        if rx >= c_w:
            for j in range(int(L // c_l)): plan.append({'x': nx * c_l, 'y': j * c_l, 'w': c_w, 'h': c_l})
        if ry >= c_l:
            for i in range(int((nx * c_l) // c_w)): plan.append({'x': i * c_w, 'y': ny * c_w, 'w': c_w, 'h': c_l})
        return plan
    s1, s2 = strategy(W_pal, L_pal, cl, cw), strategy(W_pal, L_pal, cw, cl)
    return s1 if len(s1) >= len(s2) else s2

def get_crossed_layer(plan, W_pal, L_pal):
    return [{'x': W_pal - p['x'] - p['w'], 'y': L_pal - p['y'] - p['h'], 'w': p['w'], 'h': p['h']} for p in plan]

# --- FONCTIONS GRAPHIQUES ---
def draw_box(fig, x0, x1, y0, y1, z0, z1, color, opacity=1.0, line_width=1):
    fig.add_trace(go.Mesh3d(
        x=[x0, x1, x1, x0, x0, x1, x1, x0], y=[y0, y0, y1, y1, y0, y0, y1, y1], z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=opacity, flatshading=True, showlegend=False
    ))
    lx = [x0, x1, x1, x0, x0, None, x0, x1, x1, x0, x0, None, x0, x0, None, x1, x1, None, x1, x1, None, x0, x0]
    ly = [y0, y0, y1, y1, y0, None, y0, y0, y1, y1, y0, None, y0, y0, None, y0, y0, None, y1, y1, None, y1, y1]
    lz = [z0, z0, z0, z0, z0, None, z1, z1, z1, z1, z1, None, z0, z1, None, z0, z1, None, z0, z1, None, z0, z1]
    fig.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode='lines', line=dict(color='black', width=line_width), showlegend=False))

def draw_real_pallet(fig, x_off, w_p, l_p, z_off, color="#8D6E63"):
    for sx in [0, w_p/2-50, w_p-100]: draw_box(fig, x_off+sx, x_off+sx+100, 0, l_p, z_off, z_off+25, color)
    for dx in [0, w_p/2-50, w_p-100]:
        for dy in [0, l_p/2-50, l_p-100]: draw_box(fig, x_off+dx, x_off+dx+100, dy, dy+100, z_off+25, z_off+125, color)
    draw_box(fig, x_off, x_off+w_p, 0, l_p, z_off+125, z_off+150, color)

# --- INTERFACE ---
st.sidebar.title("🚀 WMS Pro v9.8")
menu = st.sidebar.radio("Menu", ["📦 Simulateur", "📑 Catalogue Articles", "⚙️ Paramètres Rack"])

if menu == "📑 Catalogue Articles":
    st.header("Gestion du Référentiel")
    with st.form("add_ref"):
        c1, c2, c3, c4, c5 = st.columns(5)
        new_ref = c1.text_input("Référence")
        new_l = c2.number_input("Longueur (mm)", 100)
        new_w = c3.number_input("Largeur (mm)", 100)
        new_h = c4.number_input("Hauteur (mm)", 50)
        new_p = c5.number_input("Poids (kg)", 0.5)
        if st.form_submit_button("Ajouter au catalogue"):
            new_row = pd.DataFrame([{"REF":new_ref, "L":new_l, "W":new_w, "H":new_h, "P":new_p}])
            st.session_state.catalogue = pd.concat([st.session_state.catalogue, new_row], ignore_index=True)
    st.dataframe(st.session_state.catalogue, use_container_width=True)

elif menu == "⚙️ Paramètres Rack":
    st.header("Configuration de la Structure")
    st.session_state.l_lisse = st.number_input("Longueur Lisse (mm)", 2700)
    st.session_state.capa_lisse = st.number_input("Capacité Max par Niveau (kg)", 3000)
    st.session_state.h_utile = st.number_input("Hauteur Utile Alvéole (mm)", 1800)
    st.session_state.sect_montant = st.slider("Section Montant (mm)", 80, 120, 100)

else:
    # --- SIMULATEUR ---
    if 'l_lisse' not in st.session_state: st.session_state.l_lisse = 2700
    if 'capa_lisse' not in st.session_state: st.session_state.capa_lisse = 3000
    if 'h_utile' not in st.session_state: st.session_state.h_utile = 1800
    if 'sect_montant' not in st.session_state: st.session_state.sect_montant = 100

    with st.sidebar:
        ref_sel = st.selectbox("Sélectionner Article", st.session_state.catalogue["REF"].tolist())
        fmt_pal = st.selectbox("Format Palette", ["1000x1200 (VMF)", "800x1200 (EURO)"])
        w_p = 1000 if "1000" in fmt_pal else 800

    item = st.session_state.catalogue[st.session_state.catalogue["REF"] == ref_sel].iloc[0]

    # CALCULS LOGISTIQUES
    plan_a = get_optimal_layer(w_p, 1200, item['L'], item['W'])
    plan_b = get_crossed_layer(plan_a, w_p, 1200)
    nb_c = int((st.session_state.h_utile - 150) // item['H'])
    poids_pal = int(len(plan_a) * nb_c * item['P'])
    
    # Intelligence de pose
    if w_p == 1000: # Logique 2 palettes extrêmes
        positions_x = [0, st.session_state.l_lisse - w_p]
        nb_pal_lisse = 2
    else: # Logique 3 palettes collées
        positions_x = [0, 850, 1700] if st.session_state.l_lisse >= 2500 else [0]
        nb_pal_lisse = len(positions_x)
    
    poids_total_lisse = poids_pal * nb_pal_lisse
    
    st.header(f"Simulation : {ref_sel} sur {fmt_pal}")
    k1, k2, k3 = st.columns(3)
    k1.metric("Colis / Palette", len(plan_a) * nb_c)
    
    color_poids = "normal" if poids_total_lisse <= st.session_state.capa_lisse else "inverse"
    k2.metric("Charge Lisse Total", f"{poids_total_lisse} kg", f"Capacité: {st.session_state.capa_lisse}", delta_color=color_poids)
    k3.metric("Mode de Pose", f"{nb_pal_lisse} Palettes", "Automatique")

    if poids_total_lisse > st.session_state.capa_lisse:
        st.error(f"⚠️ SURCHARGE LISSE : Dépassement de {poids_total_lisse - st.session_state.capa_lisse} kg")

    v1, v2 = st.columns([1, 2])
    
    with v1:
        st.write("### Plan de Couche")
        f1 = go.Figure()
        draw_real_pallet(f1, 0, w_p, 1200, 0)
        for k in range(nb_c):
            p, col = (plan_a, "#1E88E5") if k % 2 == 0 else (plan_b, "#E53935")
            for b in p: draw_box(f1, b['x'], b['x']+b['w'], b['y'], b['y']+b['h'], 150+(k*item['H']), 150+((k+1)*item['H']), col)
        f1.update_layout(scene=dict(aspectmode='data'), height=500, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(f1, use_container_width=True)

    with v2:
        st.write("### Vue Rack Dynamique")
        f2 = go.Figure()
        # Structure Rack
        lisse_col = "red" if poids_total_lisse > st.session_state.capa_lisse else "orange"
        sm = st.session_state.sect_montant
        for px in [-sm, st.session_state.l_lisse]:
            for py in [0, 1100]: draw_box(f2, px, px+sm, py, py+sm, -150, st.session_state.h_utile+150, "#455A64")
        draw_box(f2, 0, st.session_state.l_lisse, 0, 100, -120, 0, lisse_col) # Lisse AV
        draw_box(f2, 0, st.session_state.l_lisse, 1100, 1200, -120, 0, lisse_col) # Lisse AR

        # Pose des palettes selon la logique
        for x_pos in positions_x:
            draw_real_pallet(f2, x_pos, w_p, 1200, 0)
            draw_box(f2, x_pos+10, x_pos+w_p-10, 10, 1190, 150, 150+(nb_c*item['H']), "rgba(33, 150, 243, 0.4)")
        
        f2.update_layout(scene=dict(aspectmode='data'), height=600, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(f2, use_container_width=True)
