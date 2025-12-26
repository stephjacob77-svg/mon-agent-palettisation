import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert WMS Pro v9.9 - Optimisation Sous Contraintes", layout="wide")

# --- INITIALISATION CATALOGUE ---
if 'catalogue' not in st.session_state:
    st.session_state.catalogue = pd.DataFrame([
        {"REF": "BOITE_LOURDE", "L": 400, "W": 300, "H": 250, "P": 25.0},
        {"REF": "BOITE_LEGERE", "L": 300, "W": 200, "H": 150, "P": 5.0}
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
        return plan
    s1, s2 = strategy(W_pal, L_pal, cl, cw), strategy(W_pal, L_pal, cw, cl)
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
    draw_box(fig, x_off, x_off+w_p, 0, l_p, z_off+125, z_off+150, c_wood) # Plateau
    for dx in [0, w_p-100]: # Dés
        for dy in [0, l_p-100]: draw_box(fig, x_off+dx, x_off+dx+100, dy, dy+100, z_off, z_off+125, c_wood)

# --- INTERFACE ---
st.sidebar.title("🛠️ WMS Control v9.9")
menu = st.sidebar.radio("Navigation", ["📦 Optimiseur", "📑 Catalogue", "⚙️ Config Rack"])

if menu == "📑 Catalogue":
    st.header("Catalogue Articles")
    edited_df = st.data_editor(st.session_state.catalogue, num_rows="dynamic")
    st.session_state.catalogue = edited_df

elif menu == "⚙️ Config Rack":
    st.header("Dimensions & Capacités du Rack")
    st.session_state.l_lisse = st.number_input("Longueur Lisse (mm)", 2700)
    st.session_state.capa_lisse = st.number_input("Charge Max Lisse (kg)", 3000)
    st.session_state.h_max = st.number_input("Hauteur Max Alvéole (mm)", 1800)

else:
    # --- OPTIMISEUR ---
    if 'l_lisse' not in st.session_state: st.session_state.l_lisse, st.session_state.capa_lisse, st.session_state.h_max = 2700, 3000, 1800
    
    with st.sidebar:
        ref_sel = st.selectbox("Article", st.session_state.catalogue["REF"].tolist())
        fmt_pal = st.selectbox("Format Palette", ["1000x1200 (VMF)", "800x1200 (EURO)"])
        w_p = 1000 if "1000" in fmt_pal else 800

    item = st.session_state.catalogue[st.session_state.catalogue["REF"] == ref_sel].iloc[0]
    nb_pal_lisse = st.session_state.l_lisse // w_p
    if w_p == 1000: nb_pal_lisse = 2 # Forcer 2 si 1000 sur 2700

    # ALGORITHME D'AJUSTEMENT STRICT
    plan_layer = get_optimal_layer(w_p, 1200, item['L'], item['W'])
    nb_colis_layer = len(plan_layer)
    
    # Calcul du nombre de couches max théorique (Hauteur)
    max_layers_h = int((st.session_state.h_max - 150) // item['H'])
    
    # Ajustement par le poids
    nb_couches = max_layers_h
    while nb_couches > 0:
        poids_palette = nb_couches * nb_colis_layer * item['P']
        if (poids_palette * nb_pal_lisse) <= st.session_state.capa_lisse:
            break
        nb_couches -= 1

    h_totale = 150 + (nb_couches * item['H'])
    poids_total_lisse = (nb_couches * nb_colis_layer * item['P']) * nb_pal_lisse

    # --- AFFICHAGE ---
    st.header(f"Résultat d'Optimisation : {ref_sel}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Couches Autorisées", f"{nb_couches} / {max_layers_h}")
    c2.metric("Poids / Palette", f"{int(poids_palette)} kg")
    c3.metric("Charge Lisse", f"{int(poids_total_lisse)} kg", f"{int(st.session_state.capa_lisse - poids_total_lisse)} kg dispo")
    c4.metric("Hauteur Totale", f"{h_totale} mm")

    t1, t2 = st.tabs(["🏗️ Simulation 3D", "📋 Plans de Pose 2D"])

    with t1:
        f3d = go.Figure()
        # Rack
        for px in [-100, st.session_state.l_lisse]:
            draw_box(f3d, px, px+100, 0, 1200, -150, st.session_state.h_max, "#455A64")
        draw_box(f3d, 0, st.session_state.l_lisse, 0, 100, -120, 0, "orange")
        
        # Palettes
        pos_x = [0, st.session_state.l_lisse-w_p] if w_p == 1000 else [0, 900, 1800]
        for x in pos_x:
            draw_real_pallet(f3d, x, w_p, 1200, 0)
            for k in range(nb_couches):
                p = plan_layer if k % 2 == 0 else get_crossed_layer(plan_layer, w_p, 1200)
                col = "#1E88E5" if k % 2 == 0 else "#E53935"
                for b in p:
                    draw_box(f3d, x+b['x'], x+b['x']+b['w'], b['y'], b['y']+b['h'], 150+(k*item['H']), 150+((k+1)*item['H']), col)
        
        f3d.update_layout(scene=dict(aspectmode='data'), height=700)
        st.plotly_chart(f3d, use_container_width=True)

    with t2:
        st.subheader("Instructions de Palettisation")
        c2d1, c2d2 = st.columns(2)
        def draw_2d(plan, title, color):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=[0,w_p,w_p,0,0], y=[0,0,1200,1200,0], fill="toself", fillcolor="#D7CCC8", name="Palette"))
            for b in plan:
                fig.add_trace(go.Scatter(x=[b['x'], b['x']+b['w'], b['x']+b['w'], b['x'], b['x']], 
                                         y=[b['y'], b['y'], b['y']+b['h'], b['y']+b['h'], b['y']], 
                                         fill="toself", fillcolor=color, line=dict(color="white")))
            fig.update_layout(title=title, xaxis=dict(range=[-100, w_p+100]), yaxis=dict(range=[-100, 1300], scaleanchor="x"), showlegend=False)
            return fig
        
        c2d1.plotly_chart(draw_2d(plan_layer, "Couches Impaires (Base)", "#1E88E5"), use_container_width=True)
        c2d2.plotly_chart(draw_2d(get_crossed_layer(plan_layer, w_p, 1200), "Couches Paires (Verrouillage)", "#E53935"), use_container_width=True)
