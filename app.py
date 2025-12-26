import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert WMS Pro v9.9.1", layout="wide")

# --- INITIALISATION ÉTATS ---
if 'catalogue' not in st.session_state:
    st.session_state.catalogue = pd.DataFrame([
        {"REF": "PROD_LOURD_A", "L": 400, "W": 300, "H": 250, "P": 22.0},
        {"REF": "PROD_LIGHT_B", "L": 300, "W": 200, "H": 150, "P": 4.5}
    ])

# --- MOTEUR TETRIS ---
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

# --- FONCTIONS GRAPHIQUES 3D ---
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

def draw_real_pallet(fig, x_off, w_p, l_p, z_off):
    c_wood = "#8D6E63"
    # Structure simplifiée mais propre : Plateau + Pieds
    draw_box(fig, x_off, x_off+w_p, 0, l_p, z_off+125, z_off+150, c_wood) # Plateau
    for dx in [0, w_p/2-50, w_p-100]:
        for dy in [0, l_p-100]: draw_box(fig, x_off+dx, x_off+dx+100, dy, dy+100, z_off, z_off+125, c_wood)

# --- INTERFACE ---
st.sidebar.title("📦 WMS Pro Expert v9.9.1")
menu = st.sidebar.radio("Navigation", ["Simulateur", "Catalogue", "Configuration Rack"])

if menu == "Catalogue":
    st.header("Gestion Catalogue")
    st.session_state.catalogue = st.data_editor(st.session_state.catalogue, num_rows="dynamic")

elif menu == "Configuration Rack":
    st.header("Structure du Rack")
    c1, c2 = st.columns(2)
    st.session_state.l_lisse = c1.number_input("Longueur Lisse (mm)", 2700)
    st.session_state.capa_lisse = c2.number_input("Charge Max / Niveau (kg)", 3000)
    st.session_state.h_utile = st.number_input("Hauteur Utile Alvéole (mm)", 1800)

else:
    # --- SIMULATEUR ---
    if 'l_lisse' not in st.session_state: 
        st.session_state.l_lisse, st.session_state.capa_lisse, st.session_state.h_utile = 2700, 3000, 1800
    
    with st.sidebar:
        ref = st.selectbox("Article", st.session_state.catalogue["REF"].tolist())
        fmt_pal = st.selectbox("Palette", ["1000x1200", "800x1200"])
        w_p = 1000 if "1000" in fmt_pal else 800

    item = st.session_state.catalogue[st.session_state.catalogue["REF"] == ref].iloc[0]
    
    # 1. OPTIMISATION COUCHES (Contraintes Poids/Hauteur)
    plan_layer = get_optimal_layer(w_p, 1200, item['L'], item['W'])
    nb_pal_lisse = 3 if w_p == 800 and st.session_state.l_lisse >= 2400 else 2
    
    max_h_layers = int((st.session_state.h_utile - 150) // item['H'])
    nb_couches = max_h_layers
    while nb_couches > 0:
        poids_niveau = (nb_couches * len(plan_layer) * item['P']) * nb_pal_lisse
        if poids_niveau <= st.session_state.capa_lisse: break
        nb_couches -= 1
    
    # 2. AFFICHAGE DES SCORES
    st.header(f"Analyse de Charge : {ref}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Colis / Palette", len(plan_layer) * nb_couches)
    m2.metric("Poids / Palette", f"{int(len(plan_layer)*nb_couches*item['P'])} kg")
    m3.metric("Poids Total Lisse", f"{int(poids_niveau)} kg", f"Capacité {st.session_state.capa_lisse}")
    m4.metric("Mode de pose", f"{nb_pal_lisse} palettes")

    # 3. LES VUES
    tab1, tab2, tab3 = st.tabs(["🏗️ Vue Rack 3D", "📦 Détail Palette 3D", "📋 Plans 2D"])

    with tab1:
        st.subheader("Implantation dans l'Alvéole")
        f_rack = go.Figure()
        # Structure
        for px in [-100, st.session_state.l_lisse]: # Montants
            draw_box(f_rack, px, px+100, 0, 1200, -150, st.session_state.h_utile + 200, "#455A64")
        draw_box(f_rack, 0, st.session_state.l_lisse, 0, 100, -120, 0, "orange") # Lisse AV
        
        # Logique de pose
        if nb_pal_lisse == 2:
            positions = [0, st.session_state.l_lisse - w_p]
        else:
            positions = [0, 950, 1900] # 800 + 150mm de jeu

        for x in positions:
            draw_real_pallet(f_rack, x, w_p, 1200, 0)
            for k in range(nb_couches):
                p = plan_layer if k % 2 == 0 else get_crossed_layer(plan_layer, w_p, 1200)
                col = "#1E88E5" if k % 2 == 0 else "#E53935"
                for b in p:
                    draw_box(f_rack, x+b['x'], x+b['x']+b['w'], b['y'], b['y']+b['h'], 150+(k*item['H']), 150+((k+1)*item['H']), col, opacity=0.7)
        
        f_rack.update_layout(scene=dict(aspectmode='data'), height=700, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(f_rack, use_container_width=True)

    with tab2:
        st.subheader("Gerbage Palette Individuelle")
        f_pal = go.Figure()
        draw_real_pallet(f_pal, 0, w_p, 1200, 0)
        for k in range(nb_couches):
            p = plan_layer if k % 2 == 0 else get_crossed_layer(plan_layer, w_p, 1200)
            col = "#1E88E5" if k % 2 == 0 else "#E53935"
            for b in p:
                draw_box(f_pal, b['x'], b['x']+b['w'], b['y'], b['y']+b['h'], 150+(k*item['H']), 150+((k+1)*item['H']), col)
        f_pal.update_layout(scene=dict(aspectmode='data'), height=700)
        st.plotly_chart(f_pal, use_container_width=True)

    with tab3:
        st.subheader("Schémas de Pose par Couche")
        c2d1, c2d2 = st.columns(2)
        def plot_2d(plan, title, color):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=[0,w_p,w_p,0,0], y=[0,0,1200,1200,0], fill="toself", fillcolor="#D7CCC8", name="Pal"))
            for b in plan:
                fig.add_trace(go.Scatter(x=[b['x'], b['x']+b['w'], b['x']+b['w'], b['x'], b['x']], 
                                         y=[b['y'], b['y'], b['y']+b['h'], b['y']+b['h'], b['y']], 
                                         fill="toself", fillcolor=color, line=dict(color="white")))
            fig.update_layout(title=title, xaxis=dict(range=[-50, w_p+50]), yaxis=dict(range=[-50, 1250], scaleanchor="x"), height=500)
            return fig
        c2d1.plotly_chart(plot_2d(plan_layer, "Impaire (Bleue)", "#1E88E5"), use_container_width=True)
        c2d2.plotly_chart(plot_2d(get_crossed_layer(plan_layer, w_p, 1200), "Paire (Rouge)", "#E53935"), use_container_width=True)
