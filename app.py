import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="WMS Expert Pro v10.2 - True Tetris", layout="wide")

# --- INITIALISATION CATALOGUE ---
if 'catalogue' not in st.session_state:
    st.session_state.catalogue = pd.DataFrame([
        {"REF": "COLIS_A", "L": 400, "W": 300, "H": 250, "P": 20.0},
        {"REF": "COLIS_B", "L": 350, "W": 220, "H": 150, "P": 10.0}
    ])

# --- MOTEUR TRUE TETRIS (Calcul des rotations pour combler les vides) ---
def optimize_tetris(W_pal, L_pal, c_l, c_w):
    def fill_area(W, L, l, w):
        plan = []
        nx = int(W // l)
        ny = int(L // w)
        # Bloc principal
        for i in range(nx):
            for j in range(ny):
                plan.append({'x': i * l, 'y': j * w, 'w': l, 'h': w})
        
        # Tentative de remplissage sur le côté droit (Rotation 90°)
        rem_x = W - (nx * l)
        if rem_x >= w:
            nx_r = int(rem_x // w)
            ny_r = int(L // l)
            for i in range(nx_r):
                for j in range(ny_r):
                    plan.append({'x': nx * l + i * w, 'y': j * l, 'w': w, 'h': l})
        
        # Tentative de remplissage sur le haut (Rotation 90°)
        rem_y = L - (ny * w)
        if rem_y >= l:
            ny_r = int(rem_y // l)
            nx_r = int((nx * l) // w)
            for i in range(nx_r):
                for j in range(ny_r):
                    plan.append({'x': i * w, 'y': ny * w + j * l, 'w': w, 'h': l})
        return plan

    # On teste les deux sens de départ et on garde le meilleur
    p1 = fill_area(W_pal, L_pal, c_l, c_w)
    p2 = fill_area(W_pal, L_pal, c_w, c_l)
    return p1 if len(p1) >= len(p2) else p2

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

def draw_real_pallet(fig, x_off, w_p, l_p, z_off):
    c_wood = "#8D6E63"
    draw_box(fig, x_off, x_off+w_p, 0, l_p, z_off+125, z_off+150, c_wood)
    for dx in [0, w_p/2-50, w_p-100]:
        for dy in [0, l_p-100]: draw_box(fig, x_off+dx, x_off+dx+100, dy, dy+100, z_off, z_off+125, c_wood)

# --- NAVIGATION ---
t_config, t_cat, t_sim = st.tabs(["🏗️ 1 - Paramétrage Rack", "📑 2 - Catalogue Articles", "🚀 3 - Simulateur"])

with t_config:
    st.header("Structure du Meuble")
    c1, c2, c3 = st.columns(3)
    with c1:
        opts_l = {"950mm (1 pal)": 950, "1850mm (2 pal)": 1850, "2700mm (3 pal)": 2700, "3600mm (4 pal)": 3600}
        st.session_state.l_lisse_sel = st.selectbox("Longueur des lisses", list(opts_l.keys()), index=2)
        l_val = opts_l[st.session_state.l_lisse_sel]
    with c2:
        st.session_state.nb_niv = st.number_input("Nombre de niveaux (H)", 1, 8, 3)
        st.session_state.h_niv = st.number_input("Hauteur entre lisses (mm)", 800, 3000, 1800)
    with c3:
        st.session_state.capa = st.number_input("Charge max par niveau (kg)", 500, 6000, 3000)

with t_cat:
    st.header("Référentiel")
    st.session_state.catalogue = st.data_editor(st.session_state.catalogue, num_rows="dynamic", use_container_width=True)

with t_sim:
    if len(st.session_state.catalogue) > 0:
        with st.sidebar:
            ref_sel = st.selectbox("Article", st.session_state.catalogue["REF"].tolist())
            item = st.session_state.catalogue[st.session_state.catalogue["REF"] == ref_sel].iloc[0]
            fmt_pal = st.selectbox("Palette", ["800x1200 (EURO)", "1000x1200 (VMF)"])
            w_p = 800 if "800" in fmt_pal else 1000
        
        # 1. Calcul Tetris
        plan_base = optimize_tetris(w_p, 1200, item['L'], item['W'])
        plan_cross = get_crossed_layer(plan_base, w_p, 1200)
        
        # 2. Calcul limites
        nb_pal_l = l_val // (w_p + 50)
        if w_p == 1000 and l_val == 2700: nb_pal_l = 2
        
        max_c = int((st.session_state.h_niv - 170) // item['H'])
        while max_c > 0:
            p_tot = ((max_c * len(plan_base) * item['P']) + 25) * nb_pal_l
            if p_tot <= st.session_state.capa: break
            max_c -= 1

        # 3. Affichage
        st.metric("Total Colis par Niveau", len(plan_base) * max_c * nb_pal_l)
        
        sub_3d, sub_2d = st.tabs(["🏗️ Rendu Meuble Complet", "📋 Plans 2D de pose"])
        
        with sub_3d:
            fig = go.Figure()
            # Montants
            for px in [-100, l_val]:
                for py in [0, 1100]:
                    draw_box(fig, px, px+100, py, py+100, -100, st.session_state.nb_niv * st.session_state.h_niv, "#455A64")
            # Niveaux
            for n in range(st.session_state.nb_niv):
                z_b = n * st.session_state.h_niv
                draw_box(fig, 0, l_val, 0, 80, z_b-100, z_b, "orange")
                draw_box(fig, 0, l_val, 1120, 1200, z_b-100, z_b, "orange")
                
                if w_p == 1000 and l_val == 2700: pos_x = [0, l_val - w_p]
                else: 
                    gap = (l_val - (nb_pal_l * w_p)) / (nb_pal_l + 1)
                    pos_x = [gap + i*(w_p + gap) for i in range(nb_pal_l)]
                
                for x in pos_x:
                    draw_real_pallet(fig, x, w_p, 1200, z_b)
                    for k in range(max_c):
                        p = plan_base if k % 2 == 0 else plan_cross
                        col = "#1E88E5" if k % 2 == 0 else "#E53935"
                        for b in p:
                            draw_box(fig, x+b['x'], x+b['x']+b['w'], b['y'], b['y']+b['h'], z_b+150+(k*item['H']), z_b+150+((k+1)*item['H']), col, opacity=0.8)

            fig.update_layout(scene=dict(aspectmode='data'), height=800, margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(fig, use_container_width=True)

        with sub_2d:
            
            c1, c2 = st.columns(2)
            def plot_2d(plan, title, color):
                f = go.Figure()
                f.add_trace(go.Scatter(x=[0,w_p,w_p,0,0], y=[0,0,1200,1200,0], fill="toself", fillcolor="#D7CCC8"))
                for b in plan: f.add_trace(go.Scatter(x=[b['x'],b['x']+b['w'],b['x']+b['w'],b['x'],b['x']], y=[b['y'],b['y'],b['y']+b['h'],b['y']+b['h'],b['y']], fill="toself", fillcolor=color, line=dict(color="white")))
                f.update_layout(title=title, xaxis=dict(scaleanchor="y"), height=500, showlegend=False)
                return f
            c1.plotly_chart(plot_2d(plan_base, "Couche Impaire", "#1E88E5"), use_container_width=True)
            c2.plotly_chart(plot_2d(plan_cross, "Couche Paire", "#E53935"), use_container_width=True)
