import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="WMS Expert Pro v10.1", layout="wide")

# --- INITIALISATION ---
if 'catalogue' not in st.session_state:
    st.session_state.catalogue = pd.DataFrame([
        {"REF": "COLIS_A", "L": 400, "W": 300, "H": 250, "P": 20.0},
        {"REF": "COLIS_B", "L": 300, "W": 200, "H": 150, "P": 8.0}
    ])

# --- MOTEUR TETRIS AVANCÉ ---
def get_optimal_layer(W_pal, L_pal, cl, cw):
    def strategy(W, L, c_l, c_w):
        plan = []
        nx, ny = int(W // c_l), int(L // c_w)
        for i in range(nx):
            for j in range(ny):
                plan.append({'x': i * c_l, 'y': j * c_w, 'w': c_l, 'h': c_w})
        # Remplissage des zones résiduelles (Tetris)
        rx, ry = W - (nx * c_l), L - (ny * c_w)
        if rx >= c_w:
            for j in range(int(L // c_l)):
                plan.append({'x': nx * c_l, 'y': j * c_l, 'w': c_w, 'h': c_l})
        elif ry >= c_l:
            for i in range(int(W // c_w)):
                plan.append({'x': i * c_w, 'y': ny * c_w, 'w': c_w, 'h': c_l})
        return plan
    s1 = strategy(W_pal, L_pal, cl, cw)
    s2 = strategy(W_pal, L_pal, cw, cl)
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

def draw_real_pallet(fig, x_off, w_p, l_p, z_off):
    c_wood = "#8D6E63"
    draw_box(fig, x_off, x_off+w_p, 0, l_p, z_off+125, z_off+150, c_wood) # Plateau
    for dx in [0, w_p-100]: # Dés
        for dy in [0, l_p-100]:
            draw_box(fig, x_off+dx, x_off+dx+100, dy, dy+100, z_off, z_off+125, c_wood)

# --- NAVIGATION ---
tab_config, tab_cat, tab_sim = st.tabs(["🏗️ 1 - Paramétrage Rack", "📑 2 - Catalogue Articles", "🚀 3 - Simulateur"])

with tab_config:
    st.header("Configuration du Meuble")
    c1, c2, c3 = st.columns(3)
    with c1:
        opts_l = {"950mm (1 pal)": 950, "1850mm (2 pal)": 1850, "2250mm (2 pal VMF)": 2250, "2700mm (3 pal)": 2700, "3600mm (4 pal)": 3600}
        st.session_state.l_lisse_sel = st.selectbox("Longueur des lisses", list(opts_l.keys()), index=3)
        l_val = opts_l[st.session_state.l_lisse_sel]
    with c2:
        st.session_state.nb_niv = st.number_input("Nombre de niveaux", 1, 10, 3)
        st.session_state.h_niv = st.number_input("Hauteur entre lisses (mm)", 800, 3000, 1800)
    with c3:
        st.session_state.capa = st.number_input("Charge max par niveau (kg)", 500, 6000, 3000)

with tab_cat:
    st.header("Référentiel")
    st.session_state.catalogue = st.data_editor(st.session_state.catalogue, num_rows="dynamic", use_container_width=True)
    st.info("Astuce : Vous pouvez copier/coller des données depuis Excel directement dans ce tableau.")

with tab_sim:
    # Récupération des données
    item = st.session_state.catalogue.iloc[0] if len(st.session_state.catalogue)>0 else None
    if item is not None:
        with st.sidebar:
            ref_sel = st.selectbox("Article", st.session_state.catalogue["REF"].tolist())
            item = st.session_state.catalogue[st.session_state.catalogue["REF"] == ref_sel].iloc[0]
            fmt_pal = st.selectbox("Palette", ["800x1200 (EURO)", "1000x1200 (VMF)"])
            w_p = 800 if "800" in fmt_pal else 1000
        
        # Logique de capacité
        l_val = opts_l[st.session_state.l_lisse_sel]
        nb_pal_l = l_val // (w_p + 50)
        if w_p == 1000 and l_val == 2700: nb_pal_l = 2 # Règle spécifique 100x120

        # Optimisation Tetris
        plan_base = get_optimal_layer(w_p, 1200, item['L'], item['W'])
        plan_cross = get_crossed_layer(plan_base, w_p, 1200)
        
        # Ajustement par le poids et hauteur
        max_c = int((st.session_state.h_niv - 170) // item['H'])
        while max_c > 0:
            p_total = ((max_c * len(plan_base) * item['P']) + 25) * nb_pal_l
            if p_total <= st.session_state.capa: break
            max_c -= 1

        # AFFICHAGE
        col_res1, col_res2 = st.columns([1, 2])
        
        with col_res1:
            st.metric("Colis / Palette", len(plan_base) * max_c)
            st.metric("Poids Niveau", f"{int(p_total)} kg / {st.session_state.capa} kg")
            st.subheader("Plans de Couche")
            
            # Ici on pourrait remettre les graphiques 2D Scatter

        with col_res2:
            st.subheader("Visualisation du Meuble Complet")
            fig = go.Figure()
            # 4 Montants par alvéole
            for px in [-100, l_val]:
                for py in [0, 1100]:
                    draw_box(fig, px, px+100, py, py+100, -100, st.session_state.nb_niv * st.session_state.h_niv, "#455A64")
            
            # Pour chaque niveau
            for n in range(st.session_state.nb_niv):
                z_base = n * st.session_state.h_niv
                # Lisses
                draw_box(fig, 0, l_val, 0, 80, z_base-100, z_base, "orange")
                draw_box(fig, 0, l_val, 1120, 1200, z_base-100, z_base, "orange")
                
                # Placement Palettes (Ancrage Extrémités si 100x120 sur 2700)
                if w_p == 1000 and l_val == 2700:
                    pos_x = [0, l_val - w_p]
                else:
                    gap = (l_val - (nb_pal_l * w_p)) / (nb_pal_l + 1)
                    pos_x = [gap + i*(w_p + gap) for i in range(nb_pal_l)]
                
                for x in pos_x:
                    draw_real_pallet(fig, x, w_p, 1200, z_base)
                    # Chargement des colis
                    for k in range(max_c):
                        p_to_draw = plan_base if k % 2 == 0 else plan_cross
                        c_box = "#1E88E5" if k % 2 == 0 else "#E53935"
                        for b in p_to_draw:
                            draw_box(fig, x+b['x'], x+b['x']+b['w'], b['y'], b['y']+b['h'], 
                                     z_base+150+(k*item['H']), z_base+150+((k+1)*item['H']), c_box, opacity=0.8)

            fig.update_layout(scene=dict(aspectmode='data'), height=800, margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(fig, use_container_width=True)
