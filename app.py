import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="WMS Engineering Blueprint", layout="wide")

# --- CALCULS TETRIS (Stabilité v10.6) ---
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
        return plan
    p1, p2 = fill_area(W_pal, L_pal, c_l, c_w), fill_area(W_pal, L_pal, c_w, c_l)
    return p1 if len(p1) >= len(p2) else p2

# --- INTERFACE UTILISATEUR ---
t_config, t_cat, t_sim = st.tabs(["🏗️ Configuration Rack", "📑 Catalogue", "🚀 Plan Technique"])

with t_config:
    c1, c2, c3 = st.columns(3)
    with c1:
        opts_l = {"950mm (1 pal)": 950, "1850mm (2 pal)": 1850, "2700mm (3 pal)": 2700, "3600mm (4 pal)": 3600}
        st.session_state.l_lisse_sel = st.selectbox("Longueur utile (L)", list(opts_l.keys()), index=2)
        l_val = opts_l[st.session_state.l_lisse_sel]
    with c2:
        st.session_state.nb_niv = st.number_input("Nombre d'étages (hors sol)", 1, 6, 3)
        st.session_state.capa = st.number_input("Capacité / niveau (kg)", 500, 6000, 3000)
    with c3:
        st.session_state.h_list = [st.number_input(f"H alvéole {i}", 1000, 4000, 1800 if i>0 else 2000, key=f"hx{i}") for i in range(st.session_state.nb_niv + 1)]

with t_cat:
    st.session_state.catalogue = st.data_editor(pd.DataFrame([{"REF": "BOX_01", "L": 400, "W": 300, "H": 250, "P": 20.0}]), num_rows="dynamic", use_container_width=True)

with t_sim:
    if len(st.session_state.catalogue) > 0:
        item = st.session_state.catalogue.iloc[0]
        w_p = 800 if "800" in st.sidebar.selectbox("Palette", ["800x1200", "1000x1200"]) else 1000
        
        # Calculs
        plan_base = optimize_tetris(w_p, 1200, item['L'], item['W'])
        nb_pal_l = l_val // (w_p + 50)
        if w_p == 1000 and l_val == 2700: nb_pal_l = 2
        
        results = []
        for h_max in st.session_state.h_list:
            max_c = int((h_max - 170) // item['H'])
            while max_c > 0:
                p_tot = ((max_c * len(plan_base) * item['P']) + 25) * nb_pal_l
                if p_tot <= st.session_state.capa: break
                max_c -= 1
            h_pal = 150 + (max_c * item['H'])
            results.append({"c": max_c, "p": p_tot, "air": h_max - h_pal, "h_pal": h_pal, "fill": (h_pal/h_max)*100})

        # --- DESSIN TECHNIQUE ---
        fig = go.Figure()
        z_acc = 0
        h_total_rack = sum(st.session_state.h_list)

        for i, res in enumerate(results):
            h_niv = st.session_state.h_list[i]
            
            # 1. STRUCTURE : Échelles & Lisses
            # Montants avec détail de perforation (symbolique)
            for x_m in [-100, l_val]:
                fig.add_shape(type="rect", x0=x_m, x1=x_m+100, y0=z_acc, y1=z_acc+h_niv, fillcolor="#ECEFF1", line=dict(color="black", width=2))
            
            # Lisses (épaisseur 100mm avec platines)
            if i > 0:
                fig.add_shape(type="rect", x0=-20, x1=l_val+20, y0=z_acc-100, y1=z_acc, fillcolor="#FF9800", line=dict(color="#E65100", width=2))

            # 2. CONTENU : Palettes
            gap = (l_val - (nb_pal_l * w_p)) / (nb_pal_l + 1)
            for j in range(nb_pal_l):
                px = gap + j*(w_p + gap)
                # Palette bois
                fig.add_shape(type="rect", x0=px, x1=px+w_p, y0=z_acc, y1=z_acc+150, fillcolor="#8D6E63", line=dict(color="black", width=1))
                # Chargement hachuré (gris clair)
                fig.add_shape(type="rect", x0=px, x1=px+w_p, y0=z_acc+150, y1=z_acc+res['h_pal'], fillcolor="rgba(200,200,200,0.3)", line=dict(color="#37474F", width=1, dash="dot"))
                
            # 3. COTATIONS TECHNIQUES (Norme ISO)
            # Flèche de hauteur alvéole (à gauche)
            fig.add_annotation(x=-200, y=z_acc + h_niv/2, text=f"{h_niv}", showarrow=False, textangle=-90, font=dict(size=12, weight="bold"))
            fig.add_shape(type="line", x0=-180, y0=z_acc, x1=-180, y1=z_acc+h_niv, line=dict(color="black", width=1))
            fig.add_shape(type="line", x0=-200, y0=z_acc, x1=-160, y1=z_acc, line=dict(color="black", width=1)) # Pied de cote

            # Cote de Garde d'air (à l'intérieur)
            if res['air'] > 0:
                fig.add_shape(type="line", x0=l_val/2, y0=z_acc+res['h_pal'], x1=l_val/2, y1=z_acc+h_niv-100, line=dict(color="green", width=2))
                fig.add_annotation(x=l_val/2 + 50, y=z_acc+res['h_pal'] + res['air']/2, text=f"GA:{res['air']}", showarrow=False, font=dict(color="green", size=10))

            # 4. CARTOUCHE DE DONNÉES (À droite)
            data_text = f"<b>NIVEAU {i}</b><br>Poids: {int(res['p'])} kg<br>Rempl: {res['fill']:.2f}%<br>Colis: {res['c']*len(plan_base)*nb_pal_l}"
            fig.add_annotation(x=l_val + 250, y=z_acc + h_niv/2, text=data_text, align="left", showarrow=False, bordercolor="black", borderpad=10, bgcolor="white")

            z_acc += h_niv

        # Cote Hors-tout (Hauteur totale)
        fig.add_shape(type="line", x0=-400, y0=0, x1=-400, y1=h_total_rack, line=dict(color="red", width=3))
        fig.add_annotation(x=-450, y=h_total_rack/2, text=f"H. TOTALE : {h_total_rack} mm", textangle=-90, font=dict(color="red", size=14))

        fig.update_layout(xaxis=dict(visible=False, range=[-600, l_val+1000]), yaxis=dict(visible=False, range=[-200, h_total_rack+200]), 
                          plot_bgcolor="white", height=1000, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

        

        # 5. RÉCAPITULATIF TOTAL
        st.subheader("📊 Bilan du projet")
        c_tot1, c_tot2, c_tot3 = st.columns(3)
        total_colis = sum([r['c']*len(plan_base)*nb_pal_l for r in results])
        c_tot1.metric("Stockage Total (Colis)", total_colis)
        c_tot2.metric("Poids total marchandises", f"{sum([r['p'] for r in results]):,} kg")
        c_tot3.info(f"Configuration : {nb_pal_l} palettes par niveau sur {l_val}mm")
