import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="WMS Master Config v10.5", layout="wide")

# --- INITIALISATION CATALOGUE ---
if 'catalogue' not in st.session_state:
    st.session_state.catalogue = pd.DataFrame([
        {"REF": "COLIS_A", "L": 400, "W": 300, "H": 250, "P": 22.0},
        {"REF": "COLIS_B", "L": 300, "W": 200, "H": 180, "P": 6.5}
    ])

# --- MOTEUR TETRIS AVANCÉ (Optimisation des rotations) ---
def optimize_tetris(W_pal, L_pal, c_l, c_w):
    def fill_area(W, L, l, w):
        plan = []
        nx, ny = int(W // l), int(L // w)
        for i in range(nx):
            for j in range(ny):
                plan.append({'x': i * l, 'y': j * w, 'w': l, 'h': w})
        # Remplissage des zones résiduelles (Tetris)
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
    
    p1 = fill_area(W_pal, L_pal, c_l, c_w)
    p2 = fill_area(W_pal, L_pal, c_w, c_l)
    return p1 if len(p1) >= len(p2) else p2

def get_crossed_layer(plan, W_pal, L_pal):
    return [{'x': W_pal - p['x'] - p['w'], 'y': L_pal - p['y'] - p['h'], 'w': p['w'], 'h': p['h']} for p in plan]

# --- FONCTION GRAPHIQUE 3D (Palette isolée) ---
def draw_box_3d(fig, x0, x1, y0, y1, z0, z1, color, opacity=0.8):
    fig.add_trace(go.Mesh3d(
        x=[x0, x1, x1, x0, x0, x1, x1, x0], y=[y0, y0, y1, y1, y0, y0, y1, y1], z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
        color=color, opacity=opacity, flatshading=True, showlegend=False
    ))

# --- NAVIGATION ---
t_config, t_cat, t_sim = st.tabs(["🏗️ 1 - Paramétrage Rack", "📑 2 - Catalogue Articles", "🚀 3 - Simulateur"])

# --- 1. CONFIGURATION RACK ---
with t_config:
    st.header("Configuration Technique du Rayonnage")
    c1, c2, c3 = st.columns(3)
    with c1:
        opts_l = {"950mm (1 pal)": 950, "1850mm (2 pal)": 1850, "2700mm (3 pal EURO / 2 VMF)": 2700, "3600mm (4 pal)": 3600}
        st.session_state.l_lisse_sel = st.selectbox("Longueur des lisses", list(opts_l.keys()), index=2)
        l_val = opts_l[st.session_state.l_lisse_sel]
    with c2:
        st.session_state.nb_niv = st.number_input("Nombre d'étages (hors sol)", 1, 6, 3)
        st.session_state.capa = st.number_input("Capacité par niveau (kg)", 500, 6000, 3000)
    with c3:
        st.subheader("Hauteurs utiles (mm)")
        h_list = []
        for i in range(st.session_state.nb_niv + 1):
            h_list.append(st.number_input(f"Niveau {i} (0=Sol)", 1000, 4000, 2000 if i==0 else 1800, key=f"h_in_{i}"))
        st.session_state.h_list = h_list

# --- 2. CATALOGUE ---
with t_cat:
    st.header("Référentiel Articles")
    st.session_state.catalogue = st.data_editor(st.session_state.catalogue, num_rows="dynamic", use_container_width=True)

# --- 3. SIMULATEUR ---
with t_sim:
    if len(st.session_state.catalogue) > 0:
        with st.sidebar:
            st.header("Simulation")
            ref_sel = st.selectbox("Article", st.session_state.catalogue["REF"].tolist())
            item = st.session_state.catalogue[st.session_state.catalogue["REF"] == ref_sel].iloc[0]
            fmt_pal = st.selectbox("Type Palette", ["800x1200 (EURO)", "1000x1200 (VMF)"])
            w_p = 800 if "800" in fmt_pal else 1000
            p_pal_vide = 25 if item['P'] > 15 else 15
            type_pal_txt = "LOURDE (25kg)" if p_pal_vide == 25 else "LÉGÈRE (15kg)"

        # CALCULS DE PALETTISATION
        plan_base = optimize_tetris(w_p, 1200, item['L'], item['W'])
        plan_cross = get_crossed_layer(plan_base, w_p, 1200)
        nb_pal_l = l_val // (w_p + 50)
        if w_p == 1000 and l_val == 2700: nb_pal_l = 2

        results = []
        for h_max in st.session_state.h_list:
            max_c = int((h_max - 170) // item['H'])
            raison = "Hauteur"
            while max_c > 0:
                p_tot_pal = (max_c * len(plan_base) * item['P']) + p_pal_vide
                if (p_tot_pal * nb_pal_l) <= st.session_state.capa: break
                max_c -= 1
                raison = "Poids"
            
            h_charge = 150 + (max_c * item['H'])
            results.append({
                "couches": max_c, 
                "poids_pal": p_tot_pal, 
                "poids_niv": p_tot_pal * nb_pal_l,
                "air": h_max - h_charge, 
                "fill": (h_charge / h_max) * 100,
                "limite": raison
            })

        col_visu_left, col_visu_right = st.columns([1, 2])

        with col_visu_left:
            st.subheader("📦 Focus Palette 3D")
            fig_p3d = go.Figure()
            draw_box_3d(fig_p3d, 0, w_p, 0, 1200, 0, 150, "#8D6E63") # Socle
            for k in range(results[0]['couches']):
                p_draw = plan_base if k % 2 == 0 else plan_cross
                for b in p_draw:
                    draw_box_3d(fig_p3d, b['x'], b['x']+b['w'], b['y'], b['y']+b['h'], 
                                150+(k*item['H']), 150+((k+1)*item['H']), 
                                "#1E88E5" if k % 2 == 0 else "#E53935")
            fig_p3d.update_layout(scene=dict(aspectmode='data'), height=400, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig_p3d, use_container_width=True)

            st.subheader("📋 Plans de Couche")
            c2d1, c2d2 = st.columns(2)
            def plot_2d(plan, title, color):
                f = go.Figure()
                f.add_trace(go.Scatter(x=[0,w_p,w_p,0,0], y=[0,0,1200,1200,0], fill="toself", fillcolor="#D7CCC8"))
                for b in plan: f.add_trace(go.Scatter(x=[b['x'],b['x']+b['w'],b['x']+b['w'],b['x'],b['x']], y=[b['y'],b['y'],b['y']+b['h'],b['y']+b['h'],b['y']], fill="toself", fillcolor=color, line=dict(color="white")))
                f.update_layout(title=title, xaxis=dict(scaleanchor="y"), height=300, showlegend=False, margin=dict(l=5,r=5,t=30,b=5))
                return f
            c2d1.plotly_chart(plot_2d(plan_base, "Impaire", "#1E88E5"), use_container_width=True)
            c2d2.plotly_chart(plot_2d(plan_cross, "Paire", "#E53935"), use_container_width=True)

        with col_visu_right:
            st.subheader("📐 Élévation Face (Plan Technique)")
            fig_2d = go.Figure()
            z_accum = 0
            
            for i, res in enumerate(results):
                h_niv_actuel = st.session_state.h_list[i]
                
                # Montants
                fig_2d.add_shape(type="rect", x0=-80, x1=0, y0=z_accum, y1=z_accum + h_niv_actuel, fillcolor="#455A64")
                fig_2d.add_shape(type="rect", x0=l_val, x1=l_val+80, y0=z_accum, y1=z_accum + h_niv_actuel, fillcolor="#455A64")
                
                # Lisses (Sauf sol)
                if i > 0:
                    fig_2d.add_shape(type="rect", x0=0, x1=l_val, y0=z_accum-100, y1=z_accum, fillcolor="orange")

                # Palettes
                gap = (l_val - (nb_pal_l * w_p)) / (nb_pal_l + 1)
                for j in range(nb_pal_l):
                    px = gap + j*(w_p + gap)
                    h_charge_tot = 150 + (res['couches'] * item['H'])
                    # Charge
                    fig_2d.add_shape(type="rect", x0=px, x1=px+w_p, y0=z_accum, y1=z_accum + h_charge_tot, fillcolor="#90CAF9", opacity=0.7, line=dict(color="blue"))
                    # Palette bois
                    fig_2d.add_shape(type="rect", x0=px, x1=px+w_p, y0=z_accum, y1=z_accum + 150, fillcolor="#8D6E63")

                # Annotations
                fig_2d.add_annotation(x=l_val/2, y=z_accum + h_charge_tot + (res['air']/2), text=f"GA: {res['air']}mm", showarrow=False, font=dict(color="green", size=10))
                fig_2d.add_annotation(x=l_val+120, y=z_accum + (h_niv_actuel/2), text=f"<b>NIVEAU {i}</b><br>{res['fill']:.2f}% remp.<br>{int(res['poids_niv'])}kg / {st.session_state.capa}kg<br>Limite: {res['limite']}", align="left", showarrow=False, xanchor="left")
                
                z_accum += h_niv_actuel

            fig_2d.update_layout(xaxis=dict(range=[-150, l_val+600], title="Largeur (mm)"), yaxis=dict(range=[-100, z_accum+200], title="Hauteur (mm)"), plot_bgcolor="white", height=800)
            st.plotly_chart(fig_2d, use_container_width=True)

            # --- CONSEILS D'OPTIMISATION ---
            st.info(f"💡 **Conseil Expert :** Palette préconisée : **{type_pal_txt}**. " + 
                    (f"Vous avez plus de {int(results[0]['air'])}mm de vide au Niveau 0, essayez de densifier vos alvéoles." if results[0]['air'] > 200 else "Le remplissage est optimal."))
