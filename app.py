import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="WMS Master Config v10.3", layout="wide")

# --- INITIALISATION ---
if 'catalogue' not in st.session_state:
    st.session_state.catalogue = pd.DataFrame([
        {"REF": "BOX_INDUS", "L": 400, "W": 300, "H": 250, "P": 22.0},
        {"REF": "BOX_ECOM", "L": 300, "W": 200, "H": 180, "P": 6.5}
    ])

# --- MOTEUR TETRIS AVANCÉ ---
def optimize_tetris(W_pal, L_pal, c_l, c_w):
    def fill_area(W, L, l, w):
        plan = []
        nx, ny = int(W // l), int(L // w)
        for i in range(nx):
            for j in range(ny): plan.append({'x': i * l, 'y': j * w, 'w': l, 'h': w})
        rem_x = W - (nx * l)
        if rem_x >= w:
            nx_r, ny_r = int(rem_x // w), int(L // l)
            for i in range(nx_r):
                for j in range(ny_r): plan.append({'x': nx * l + i * w, 'y': j * l, 'w': w, 'h': l})
        rem_y = L - (ny * w)
        if rem_y >= l:
            ny_r, nx_r = int(rem_y // l), int((nx * l) // w)
            for i in range(nx_r):
                for j in range(ny_r): plan.append({'x': i * w, 'y': ny * w + j * l, 'w': w, 'h': l})
        return plan
    p1, p2 = fill_area(W_pal, L_pal, c_l, c_w), fill_area(W_pal, L_pal, c_w, c_l)
    return p1 if len(p1) >= len(p2) else p2

def get_crossed_layer(plan, W_pal, L_pal):
    return [{'x': W_pal-p['x']-p['w'], 'y': L_pal-p['y']-p['h'], 'w': p['w'], 'h': p['h']} for p in plan]

# --- FONCTIONS GRAPHIQUES ---
def draw_box(fig, x0, x1, y0, y1, z0, z1, color, opacity=1.0, line_width=1):
    fig.add_trace(go.Mesh3d(x=[x0, x1, x1, x0, x0, x1, x1, x0], y=[y0, y0, y1, y1, y0, y0, y1, y1], z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6], color=color, opacity=opacity, flatshading=True, showlegend=False))
    if line_width > 0:
        lx = [x0,x1,x1,x0,x0,None,x0,x1,x1,x0,x0,None,x0,x0,None,x1,x1,None,x1,x1,None,x0,x0]
        ly = [y0,y0,y1,y1,y0,None,y0,y0,y1,y1,y0,None,y0,y0,None,y0,y0,None,y1,y1,None,y1,y1]
        lz = [z0,z0,z0,z0,z0,None,z1,z1,z1,z1,z1,None,z0,z1,None,z0,z1,None,z0,z1,None,z0,z1]
        fig.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode='lines', line=dict(color='black', width=line_width), showlegend=False))

# --- INTERFACE ---
t_config, t_cat, t_sim = st.tabs(["🏗️ 1 - Paramétrage Rack", "📑 2 - Catalogue Articles", "🚀 3 - Simulateur"])

with t_config:
    st.header("Configuration Précise du Meuble")
    c1, c2 = st.columns(2)
    with c1:
        opts_l = {"950mm (1 pal)": 950, "1850mm (2 pal)": 1850, "2700mm (3 pal)": 2700, "3600mm (4 pal)": 3600}
        st.session_state.l_lisse_sel = st.selectbox("Longueur des lisses (fixe)", list(opts_l.keys()), index=2)
        l_val = opts_l[st.session_state.l_lisse_sel]
        st.session_state.capa = st.number_input("Capacité par paire de lisses (kg)", 500, 6000, 3000)
    with c2:
        st.session_state.nb_niv = st.number_input("Nombre d'étages (hors sol)", 1, 6, 3)
    
    st.subheader("Hauteurs par niveau (mm)")
    h_list = []
    cols = st.columns(st.session_state.nb_niv + 1)
    h_list.append(cols[0].number_input("Niv 0 (Sol)", 1000, 4000, 2000))
    for i in range(1, st.session_state.nb_niv + 1):
        h_list.append(cols[i].number_input(f"Niv {i}", 1000, 4000, 1800))
    st.session_state.h_list = h_list

with t_cat:
    st.session_state.catalogue = st.data_editor(st.session_state.catalogue, num_rows="dynamic", use_container_width=True)

with t_sim:
    if len(st.session_state.catalogue) > 0:
        with st.sidebar:
            ref_sel = st.selectbox("Article", st.session_state.catalogue["REF"].tolist())
            item = st.session_state.catalogue[st.session_state.catalogue["REF"] == ref_sel].iloc[0]
            fmt_pal = st.selectbox("Type Palette", ["800x1200 (EURO)", "1000x1200 (VMF)"])
            w_p = 800 if "800" in fmt_pal else 1000
            p_pal_vide = 25 if item['P'] > 15 else 15
            type_pal = "LOURDE (25kg)" if item['P'] > 15 else "LÉGÈRE (15kg)"

        # 1. Calcul Tetris & Optimisation
        plan_base = optimize_tetris(w_p, 1200, item['L'], item['W'])
        plan_cross = get_crossed_layer(plan_base, w_p, 1200)
        nb_pal_l = l_val // (w_p + 50)
        if w_p == 1000 and l_val == 2700: nb_pal_l = 2

        # Calcul par niveau
        results = []
        for h_disp in st.session_state.h_list:
            max_c = int((h_disp - 170) // item['H'])
            raison = "Hauteur"
            while max_c > 0:
                p_tot = ((max_c * len(plan_base) * item['P']) + p_pal_vide) * nb_pal_l
                if p_tot <= st.session_state.capa: break
                max_c -= 1
                raison = "Poids"
            
            h_charge = 150 + (max_c * item['H'])
            remplissage = ((max_c * len(plan_base) * (item['L']*item['W']*item['H'])) / (w_p * 1200 * h_disp)) * 100
            results.append({"couches": max_c, "poids": p_tot, "limite": raison, "air": h_disp - h_charge, "fill": remplissage})

        # --- DASHBOARD ---
        st.subheader(f"Analyse Logistique : {ref_sel} | Palette {type_pal}")
        c_kpi = st.columns(len(results))
        for i, res in enumerate(results):
            c_kpi[i].metric(f"Niveau {i}", f"{res['couches']} Couches", f"{res['fill']:.2f}% remp.")
            c_kpi[i].caption(f"Limite: {res['limite']} | Air: {res['air']}mm")

        sub_3d, sub_2d = st.tabs(["🏗️ Vue 3D Rack", "📋 Plans de Pose 2D"])
        
        with sub_3d:
            fig = go.Figure()
            z_curr = 0
            # Montants
            h_tot_rack = sum(st.session_state.h_list)
            for px in [-100, l_val]:
                for py in [0, 1100]: draw_box(fig, px, px+100, py, py+100, 0, h_tot_rack, "#455A64")
            
            # Niveaux
            for n, res in enumerate(results):
                # Lisses (uniquement si n > 0 car n=0 est au sol)
                if n > 0:
                    draw_box(fig, 0, l_val, 0, 80, z_curr-100, z_curr, "orange")
                    draw_box(fig, 0, l_val, 1120, 1200, z_curr-100, z_curr, "orange")
                
                pos_x = [0, l_val - w_p] if (w_p==1000 and l_val==2700) else [((l_val - (nb_pal_l*w_p))/(nb_pal_l+1)) + i*(w_p+((l_val - (nb_pal_l*w_p))/(nb_pal_l+1))) for i in range(nb_pal_l)]
                
                for x in pos_x:
                    draw_box(fig, x, x+w_p, 0, 1200, z_curr+125, z_curr+150, "#8D6E63") # Palette simple pour fluidité
                    for k in range(res['couches']):
                        p = plan_base if k % 2 == 0 else plan_cross
                        col = "#1E88E5" if k % 2 == 0 else "#E53935"
                        for b in p:
                            draw_box(fig, x+b['x'], x+b['x']+b['w'], b['y'], b['y']+b['h'], z_curr+150+(k*item['H']), z_curr+150+((k+1)*item['H']), col, opacity=0.7, line_width=0)
                z_curr += st.session_state.h_list[n]

            fig.update_layout(scene=dict(aspectmode='data'), height=850, margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(fig, use_container_width=True)

        with sub_2d:
            c2d1, c2d2 = st.columns(2)
            def plot_2d(plan, title, color):
                f = go.Figure()
                f.add_trace(go.Scatter(x=[0,w_p,w_p,0,0], y=[0,0,1200,1200,0], fill="toself", fillcolor="#D7CCC8"))
                for b in plan: f.add_trace(go.Scatter(x=[b['x'],b['x']+b['w'],b['x']+b['w'],b['x'],b['x']], y=[b['y'],b['y'],b['y']+b['h'],b['y']+b['h'],b['y']], fill="toself", fillcolor=color, line=dict(color="white")))
                f.update_layout(title=title, xaxis=dict(scaleanchor="y"), height=500, showlegend=False)
                return f
            c2d1.plotly_chart(plot_2d(plan_base, "Couche Impaire (Base)", "#1E88E5"), use_container_width=True)
            c2d2.plotly_chart(plot_2d(plan_cross, "Couche Paire (Croisée)", "#E53935"), use_container_width=True)
