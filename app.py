import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="WMS Master Config v10.6", layout="wide")

# --- INITIALISATION CATALOGUE ---
if 'catalogue' not in st.session_state:
    st.session_state.catalogue = pd.DataFrame([
        {"REF": "PROJET_A", "L": 400, "W": 300, "H": 250, "P": 22.0},
        {"REF": "PROJET_B", "L": 300, "W": 200, "H": 180, "P": 6.5}
    ])

# --- MOTEURS DE CALCUL (Identiques v10.5 pour stabilité) ---
def optimize_tetris(W_pal, L_pal, c_l, c_w):
    def fill_area(W, L, l, w):
        plan = []
        nx, ny = int(W // l), int(L // w)
        for i in range(nx):
            for j in range(ny): plan.append({'x': i * l, 'y': j * w, 'w': l, 'h': w})
        rx = W - (nx * l)
        if rx >= w:
            for i in range(int(rx // w)):
                for j in range(int(L // l)): plan.append({'x': nx*l + i*w, 'y': j*l, 'w': w, 'h': l})
        ry = L - (ny * w)
        if ry >= l:
            for i in range(int((nx*l)//w)):
                for j in range(int(ry // l)): plan.append({'x': i*w, 'y': ny*w + j*l, 'w': w, 'h': l})
        return plan
    p1, p2 = fill_area(W_pal, L_pal, c_l, c_w), fill_area(W_pal, L_pal, c_w, c_l)
    return p1 if len(p1) >= len(p2) else p2

def get_crossed_layer(plan, W_pal, L_pal):
    return [{'x': W_pal - p['x'] - p['w'], 'y': L_pal - p['y'] - p['h'], 'w': p['w'], 'h': p['h']} for p in plan]

# --- NAVIGATION ---
t_config, t_cat, t_sim = st.tabs(["🏗️ 1 - Paramétrage Rack", "📑 2 - Catalogue Articles", "🚀 3 - Simulateur"])

with t_config:
    st.header("Spécifications du Système de Stockage")
    c1, c2, c3 = st.columns(3)
    with c1:
        opts_l = {"950mm (1 pal)": 950, "1850mm (2 pal)": 1850, "2700mm (3 pal)": 2700, "3600mm (4 pal)": 3600}
        st.session_state.l_lisse_sel = st.selectbox("Longueur utile de lisse (L)", list(opts_l.keys()), index=2)
        l_val = opts_l[st.session_state.l_lisse_sel]
    with c2:
        st.session_state.nb_niv = st.number_input("Nombre de niveaux (H)", 1, 6, 3)
        st.session_state.capa = st.number_input("Charge max / niveau (kg)", 500, 6000, 3000)
    with c3:
        st.subheader("Hauteurs d'alvéoles (mm)")
        st.session_state.h_list = [st.number_input(f"H niveau {i}", 1000, 4000, 2000 if i==0 else 1800, key=f"h{i}") for i in range(st.session_state.nb_niv + 1)]

with t_cat:
    st.session_state.catalogue = st.data_editor(st.session_state.catalogue, num_rows="dynamic", use_container_width=True)

with t_sim:
    if len(st.session_state.catalogue) > 0:
        item = st.session_state.catalogue.iloc[0]
        with st.sidebar:
            ref_sel = st.selectbox("Référence", st.session_state.catalogue["REF"].tolist())
            item = st.session_state.catalogue[st.session_state.catalogue["REF"] == ref_sel].iloc[0]
            fmt_pal = st.selectbox("Format Palette", ["800x1200", "1000x1200"])
            w_p = 800 if "800" in fmt_pal else 1000

        # CALCULS
        plan_base = optimize_tetris(w_p, 1200, item['L'], item['W'])
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
            results.append({"c": max_c, "p": p_tot_pal * nb_pal_l, "air": h_max - h_pal, "fill": (h_pal/h_max)*100, "h_tot": h_pal})

        # --- DESSIN TECHNIQUE 2D ---
        st.subheader("📐 Plan d'Élévation Technique (Vue de Face)")
        fig = go.Figure()
        z_acc = 0
        
        # 1. COTATION HORIZONTALE (Largeur Lisse)
        fig.add_annotation(x=l_val/2, y=-150, text=f"↔ LARGEUR UTILE : {l_val} mm", showarrow=False, font=dict(size=12, color="blue"))
        fig.add_shape(type="line", x0=0, y0=-100, x1=l_val, y1=-100, line=dict(color="blue", width=2))

        for i, res in enumerate(results):
            h_niv = st.session_state.h_list[i]
            
            # ÉCHELLES (MONTANTS)
            fig.add_shape(type="rect", x0=-100, x1=0, y0=z_acc, y1=z_acc+h_niv, fillcolor="#37474F", line=dict(color="black"))
            fig.add_shape(type="rect", x0=l_val, x1=l_val+100, y0=z_acc, y1=z_acc+h_niv, fillcolor="#37474F", line=dict(color="black"))
            
            # LISSES
            if i > 0:
                fig.add_shape(type="rect", x0=0, x1=l_val, y0=z_acc-100, y1=z_acc, fillcolor="#FF6D00", line=dict(color="black"))
            
            # PALETTES & COTES DE CHARGE
            gap = (l_val - (nb_pal_l * w_p)) / (nb_pal_l + 1)
            for j in range(nb_pal_l):
                px = gap + j*(w_p + gap)
                # Palette bois
                fig.add_shape(type="rect", x0=px, x1=px+w_p, y0=z_acc, y1=z_acc+150, fillcolor="#8D6E63")
                # Chargement
                fig.add_shape(type="rect", x0=px, x1=px+w_p, y0=z_acc+150, y1=z_acc+res['h_tot'], fillcolor="#CFD8DC", line=dict(color="#546E7A", dash="dot"))
                # Cote hauteur palette
                if j == 0:
                    fig.add_annotation(x=px+w_p/2, y=z_acc + res['h_tot']/2, text=f"H:{res['h_tot']}mm", showarrow=False, font=dict(size=9))

            # COTATION VERTICALE (À GAUCHE)
            fig.add_annotation(x=-250, y=z_acc + h_niv/2, text=f"↕ {h_niv} mm", showarrow=False, textangle=-90)
            fig.add_annotation(x=-450, y=z_acc, text=f"Z={z_acc}", showarrow=False, font=dict(size=10, color="red"))

            # GARDE D'AIR & KPI (À DROITE)
            fig.add_shape(type="line", x0=0, y0=z_acc+res['h_tot'], x1=l_val, y1=z_acc+res['h_tot'], line=dict(color="green", width=1, dash="dash"))
            fig.add_annotation(x=l_val+200, y=z_acc + h_niv - 50, text=f"<b>NIVEAU {i}</b><br>GA: {res['air']}mm<br>Fill: {res['fill']:.2f}%<br>Poids: {int(res['p'])}kg", 
                               align="left", showarrow=False, xanchor="left", bgcolor="rgba(255,255,255,0.8)", bordercolor="black")
            
            z_acc += h_niv

        # Rendu Final
        fig.update_layout(
            xaxis=dict(range=[-600, l_val+800], visible=False),
            yaxis=dict(range=[-300, z_acc+300], visible=False),
            plot_bgcolor="white", height=900, margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
