import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="WMS Expert Pro v10.0", layout="wide")

# --- INITIALISATION ---
if 'catalogue' not in st.session_state:
    st.session_state.catalogue = pd.DataFrame([
        {"REF": "COLIS_A", "L": 400, "W": 300, "H": 250, "P": 20.0},
        {"REF": "COLIS_B", "L": 300, "W": 200, "H": 150, "P": 8.0}
    ])

# --- FONCTIONS LOGISTIQUES ---
def get_optimal_layer(W_pal, L_pal, cl, cw):
    def strategy(W, L, c_l, c_w):
        plan = []
        nx, ny = int(W // c_l), int(L // c_w)
        for i in range(nx):
            for j in range(ny): plan.append({'x': i * c_l, 'y': j * c_w, 'w': c_l, 'h': c_w})
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
    draw_box(fig, x_off, x_off+w_p, 0, l_p, z_off+125, z_off+150, c_wood)
    for dx in [0, w_p-100]:
        for dy in [0, l_p-100]: draw_box(fig, x_off+dx, x_off+dx+100, dy, dy+100, z_off, z_off+125, c_wood)

# --- NAVIGATION ---
tab_config, tab_cat, tab_sim = st.tabs(["🏗️ 1 - Paramétrage Rack", "📑 2 - Catalogue Articles", "🚀 3 - Simulateur"])

# --- 1. PARAMÉTRAGE RACK ---
with tab_config:
    st.header("Définition de la Structure")
    c1, c2, c3 = st.columns(3)
    with c1:
        opts_l = {"950mm (1 pal)": 950, "1850mm (2 pal)": 1850, "2700mm (3 pal)": 2700, "3600mm (4 pal)": 3600}
        st.session_state.l_lisse = st.selectbox("Longueur des lisses", list(opts_l.keys()), index=2)
        l_val = opts_l[st.session_state.l_lisse]
    with c2:
        st.session_state.nb_niveaux = st.number_input("Nombre de niveaux (H)", 1, 6, 3)
        st.session_state.h_entre_lisse = st.number_input("Hauteur entre lisses (mm)", 1000, 2500, 1800)
    with c3:
        st.session_state.capa_lisse = st.number_input("Charge max par niveau (kg)", 500, 5000, 3000)
    
    st.info(f"Capacité totale du meuble : {st.session_state.nb_niveaux * st.session_state.capa_lisse} kg")

# --- 2. CATALOGUE ---
with tab_cat:
    st.header("Référentiel Articles")
    col_up1, col_up2 = st.columns([2, 1])
    with col_up1:
        st.session_state.catalogue = st.data_editor(st.session_state.catalogue, num_rows="dynamic", use_container_width=True)
    with col_up2:
        st.subheader("Import CSV")
        uploaded_file = st.file_uploader("Charger un fichier (Colonnes: REF, L, W, H, P)", type="csv")
        if uploaded_file:
            df_import = pd.read_csv(uploaded_file)
            st.session_state.catalogue = pd.concat([st.session_state.catalogue, df_import]).drop_duplicates(subset="REF")
            st.success("Import réussi !")

# --- 3. SIMULATEUR ---
with tab_sim:
    if len(st.session_state.catalogue) == 0:
        st.warning("Veuillez remplir le catalogue.")
    else:
        with st.sidebar:
            st.header("Options de simulation")
            ref_sel = st.selectbox("Article à simuler", st.session_state.catalogue["REF"].tolist())
            fmt_pal = st.selectbox("Type palette", ["1000x1200 (VMF)", "800x1200 (EURO)"])
            w_p = 1000 if "1000" in fmt_pal else 800
        
        item = st.session_state.catalogue[st.session_state.catalogue["REF"] == ref_sel].iloc[0]
        l_val = opts_l[st.session_state.l_lisse]
        
        # Calcul capacité par niveau
        nb_pal_l = l_val // (w_p + 50)
        if w_p == 1000 and l_val == 2700: nb_pal_l = 2 # Règle spécifique 100x120
        
        plan_layer = get_optimal_layer(w_p, 1200, item['L'], item['W'])
        max_couches = int((st.session_state.h_entre_lisse - 170) // item['H'])
        
        # Ajustement poids
        while max_couches > 0:
            poids_pal = (max_couches * len(plan_layer) * item['P']) + 25
            if (poids_pal * nb_pal_l) <= st.session_state.capa_lisse: break
            max_couches -= 1

        # VUES
        sub1, sub2, sub3 = st.tabs(["📦 Palettisation 3D", "📋 Plans 2D", "🏗️ Visualisation Rack"])
        
        with sub1:
            f_pal = go.Figure()
            draw_real_pallet(f_pal, 0, w_p, 1200, 0)
            for k in range(max_couches):
                p = plan_layer if k % 2 == 0 else get_crossed_layer(plan_layer, w_p, 1200)
                col = "#1E88E5" if k % 2 == 0 else "#E53935"
                for b in p: draw_box(f_pal, b['x'], b['x']+b['w'], b['y'], b['y']+b['h'], 150+(k*item['H']), 150+((k+1)*item['H']), col)
            f_pal.update_layout(scene=dict(aspectmode='data'), height=600)
            st.plotly_chart(f_pal, use_container_width=True)

        with sub2:
            st.subheader("Schémas de pose")
            
            c2d1, c2d2 = st.columns(2)
            def draw_2d(plan, title, col):
                f = go.Figure()
                f.add_trace(go.Scatter(x=[0,w_p,w_p,0,0], y=[0,0,1200,1200,0], fill="toself", fillcolor="#D7CCC8"))
                for b in plan: f.add_trace(go.Scatter(x=[b['x'],b['x']+b['w'],b['x']+b['w'],b['x'],b['x']], y=[b['y'],b['y'],b['y']+b['h'],b['y']+b['h'],b['y']], fill="toself", fillcolor=col, line=dict(color="white")))
                f.update_layout(title=title, xaxis=dict(scaleanchor="y"), height=400, showlegend=False)
                return f
            c2d1.plotly_chart(draw_2d(plan_layer, "Couche Impaire", "#1E88E5"), use_container_width=True)
            c2d2.plotly_chart(draw_2d(get_crossed_layer(plan_layer, w_p, 1200), "Couche Paire", "#E53935"), use_container_width=True)

        with sub3:
            st.subheader("Rendu du Meuble Complet")
            f_rack = go.Figure()
            # Montants
            for px in [-100, l_val]:
                for py in [0, 1100]: draw_box(f_rack, px, px+100, py, py+100, -150, st.session_state.nb_niveaux * st.session_state.h_entre_lisse, "#455A64")
            # Niveaux
            for n in range(st.session_state.nb_niveaux):
                z_niv = n * st.session_state.h_entre_lisse
                draw_box(f_rack, 0, l_val, 0, 80, z_niv-100, z_niv, "orange")
                draw_box(f_rack, 0, l_val, 1120, 1200, z_niv-100, z_niv, "orange")
                
                # Palettes par niveau
                pos_x = [0, l_val-w_p] if (w_p==1000 and l_val==2700) else [i*(w_p+50) for i in range(nb_pal_l)]
                for x in pos_x:
                    draw_real_pallet(f_rack, x, w_p, 1200, z_niv)
                    for k in range(max_couches):
                        draw_box(f_rack, x+5, x+w_p-5, 5, 1195, z_niv+150+(k*item['H']), z_niv+150+((k+1)*item['H']), "#1E88E5", opacity=0.4)
            
            f_rack.update_layout(scene=dict(aspectmode='data'), height=800)
            st.plotly_chart(f_rack, use_container_width=True)
