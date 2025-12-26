import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="WMS Master Config v10.5.1", layout="wide")

# --- INITIALISATION ---
if 'catalogue' not in st.session_state:
    st.session_state.catalogue = pd.DataFrame([
        {"REF": "COLIS_A", "L": 400, "W": 300, "H": 250, "P": 22.0},
        {"REF": "COLIS_B", "L": 300, "W": 200, "H": 180, "P": 6.5}
    ])

# --- MOTEUR TETRIS ---
def optimize_tetris(W_pal, L_pal, c_l, c_w):
    def fill_area(W, L, l, w):
        plan = []
        nx, ny = int(W // l), int(L // w)
        for i in range(nx):
            for j in range(ny):
                plan.append({'x': i * l, 'y': j * w, 'w': l, 'h': w})
        rx = W - (nx * l)
        if rx >= w:
            for i in range(int(rx // w)):
                for j in range(int(L // l)): plan.append({'x': nx*l + i*w, 'y': j*l, 'w': w, 'h': l})
        ry = L - (ny * w)
        if ry >= l:
            for i in range(int((nx*l)//w)):
                for j in range(int(ry // l)): plan.append({'x': i*w, 'y': ny*w + j*l, 'w': w, 'h': l})
        return plan
    p1 = fill_area(W_pal, L_pal, c_l, c_w)
    p2 = fill_area(W_pal, L_pal, c_w, c_l)
    return p1 if len(p1) >= len(p2) else p2

def get_crossed_layer(plan, W_pal, L_pal):
    return [{'x': W_pal - p['x'] - p['w'], 'y': L_pal - p['y'] - p['h'], 'w': p['w'], 'h': p['h']} for p in plan]

# --- FONCTION GRAPHIQUE 3D ---
def draw_box_3d(fig, x0, x1, y0, y1, z0, z1, color, opacity=0.8):
    fig.add_trace(go.Mesh3d(
        x=[x0, x1, x1, x0, x0, x1, x1, x0], y=[y0, y0, y1, y1, y0, y0, y1, y1], z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
        color=color, opacity=opacity, flatshading=True, showlegend=False
    ))

# --- INTERFACE ---
t_config, t_cat, t_sim = st.tabs(["🏗️ 1 - Paramétrage Rack", "📑 2 - Catalogue Articles", "🚀 3 - Simulateur"])

with t_config:
    st.header("Structure du Rayonnage")
    c1, c2, c3 = st.columns(3)
    with c1:
        opts_l = {"950mm (1 pal)": 950, "1850mm (2 pal)": 1850, "2700mm (3 pal)": 2700, "3600mm (4 pal)": 3600}
        st.session_state.l_lisse_sel = st.selectbox("Longueur des lisses", list(opts_l.keys()), index=2)
        l_val = opts_l[st.session_state.l_lisse_sel]
    with c2:
        st.session_state.nb_niv = st.number_input("Nombre d'étages (hors sol)", 1, 6, 3)
        st.session_state.capa = st.number_input("Capacité par niveau (kg)", 500, 6000, 3000)
    with c3:
        st.subheader("Hauteurs utiles (mm)")
        st.session_state.h_list = [st.number_input(f"Niveau {i} (0=Sol)", 1000, 4000, 2000 if i==0 else 1800, key=f"h_r_{i}") for i in range(st.session_state.nb_niv + 1)]

with t_cat:
    st.session_state.catalogue = st.data_editor(st.session_state.catalogue, num_rows="dynamic", use_container_width=True)

with t_sim:
    if len(st.session_state.catalogue) > 0:
        with st.sidebar:
            ref_sel = st.selectbox("Article", st.session_state.catalogue["REF"].tolist())
            item = st.session_state.catalogue[st.session_state.catalogue["REF"] == ref_sel].iloc[0]
            w_p = 800 if "800" in st.selectbox("Type Palette", ["800x1200 (EURO)", "1000x1200 (VMF)"]) else 1000

        # CALCULS
        plan_base = optimize_tetris(w_p, 1200, item['L'], item['W'])
        plan_cross = get_crossed_layer(plan_base, w_p, 1200)
        nb_pal_l = l_val // (w_p + 50)
        if w_p == 1000 and l_val == 2700: nb_pal_l = 2

        results = []
        for h_max in st.session_state.h_list:
            max_c = int((h_max - 170) // item['H'])
            while max_c > 0:
                p_tot_pal = (max_c * len(plan_base) * item['P']) + 25
                if (p_tot_pal * nb_pal_l) <= st.session_state.capa: break
                max_c -= 1
            h_pal = 150 + (max_c * item['H'])
            results.append({"c": max_c, "p": p_tot_pal * nb_pal_l, "air": h_max - h_pal, "fill": (h_pal/h_max)*100, "h_pal": h_pal})

        col_l, col_r = st.columns([1, 2])
        with col_l:
            st.subheader("📦 Focus Palette 3D")
            fig_3d = go.Figure()
            draw_box_3d(fig_3d, 0, w_p, 0, 1200, 0, 150, "#8D6E63")
            for k in range(results[0]['c']):
                p = plan_base if k % 2 == 0 else plan_cross
                for b in p: draw_box_3d(fig_3d, b['x'], b['x']+b['w'], b['y'], b['y']+b['h'], 150+(k*item['H']), 150+((k+1)*item['H']), "#1E88E5" if k%2==0 else "#E53935")
            fig_3d.update_layout(scene=dict(aspectmode='data'), height=400, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig_3d, use_container_width=True)

        with col_r:
            st.subheader("📐 Élévation Face (Rack)")
            fig_2d = go.Figure()
            z_acc = 0
            for i, res in enumerate(results):
                h_niv = st.session_state.h_list[i]
                fig_2d.add_shape(type="rect", x0=-80, x1=0, y0=z_acc, y1=z_acc + h_niv, fillcolor="#455A64")
                fig_2d.add_shape(type="rect", x0=l_val, x1=l_val+80, y0=z_acc, y1=z_acc + h_niv, fillcolor="#455A64")
                if i > 0: fig_2d.add_shape(type="rect", x0=0, x1=l_val, y0=z_acc-100, y1=z_acc, fillcolor="orange")
                gap = (l_val - (nb_pal_l * w_p)) / (nb_pal_l + 1)
                for j in range(nb_pal_l):
                    px = gap + j*(w_p + gap)
                    fig_2d.add_shape(type="rect", x0=px, x1=px+w_p, y0=z_acc, y1=z_acc + res['h_pal'], fillcolor="#90CAF9", opacity=0.7, line=dict(color="blue"))
                    fig_2d.add_shape(type="rect", x0=px, x1=px+w_p, y0=z_acc, y1=z_acc + 150, fillcolor="#8D6E63")
                fig_2d.add_annotation(x=l_val/2, y=z_acc+res['h_pal']+(res['air']/2), text=f"GA: {res['air']}mm", showarrow=False, font=dict(color="green"))
                fig_2d.add_annotation(x=l_val+120, y=z_acc+(h_niv/2), text=f"<b>NIVEAU {i}</b><br>{res['fill']:.2f}%<br>{int(res['p'])}kg", align="left", showarrow=False, xanchor="left")
                z_acc += h_niv
            fig_2d.update_layout(xaxis=dict(range=[-150, l_val+600], visible=False), yaxis=dict(visible=False), plot_bgcolor="white", height=700)
            st.plotly_chart(fig_2d, use_container_width=True)
