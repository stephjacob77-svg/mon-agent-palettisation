import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math

# --- CONFIGURATION & DESIGN ---
st.set_page_config(page_title="Expert Palettisation Hub", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f1f3f6; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e1e4e8; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION BASE DE DONNEES ---
if 'db_refs' not in st.session_state:
    st.session_state.db_refs = pd.DataFrame(columns=["Référence", "Long", "Larg", "Haut", "Poids"])

# --- FONCTIONS TECHNIQUES ---

def draw_cube(fig, x_min, x_max, y_min, y_max, z_min, z_max, color, opacity=0.8, line_color="white"):
    fig.add_trace(go.Mesh3d(
        x=[x_min, x_max, x_max, x_min, x_min, x_max, x_max, x_min],
        y=[y_min, y_min, y_max, y_max, y_min, y_min, y_max, y_max],
        z=[z_min, z_min, z_min, z_min, z_max, z_max, z_max, z_max],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=opacity, flatshading=True, showlegend=False
    ))

def get_layer_plan(W_max, L_max, cl, cw):
    plan = []
    nx, ny = int(W_max // cl), int(L_max // cw)
    for i in range(nx):
        for j in range(ny): plan.append({'x': i*cl, 'y': j*cw, 'w': cl, 'h': cw})
    reste_x = W_max - (nx * cl)
    if reste_x >= cw:
        for i in range(int(reste_x // cw)):
            for j in range(int(L_max // cl)): plan.append({'x': nx*cl + i*cw, 'y': j*cl, 'w': cw, 'h': cl})
    return plan

def calculate_best_fit(W_pal, l_lisse, h_max, cl, cw, ch, cp, p_max_lisse, overhang):
    nb_pal_sol = int(l_lisse // W_pal)
    poids_max_par_pal = (p_max_lisse / nb_pal_sol) - 25
    plan = get_layer_plan(W_pal + 2*overhang, 1200 + 2*overhang, cl, cw)
    colis_par_couche = len(plan)
    if colis_par_couche == 0: return None
    n_h = int((h_max - 150) // ch)
    n_p = int((poids_max_par_pal // cp) // colis_par_couche) if cp > 0 else 99
    n_final = max(0, min(n_h, n_p))
    return {
        "total": int(n_final * colis_par_couche), "couches": n_final, "plan": plan,
        "nb_pal_sol": nb_pal_sol, "poids": (n_final * colis_par_couche * cp) + 25,
        "cause": "POIDS ⚖️" if n_p < n_h else "HAUTEUR 📏", "colis_couche": colis_par_couche
    }

# --- MODE SIMPLE AMÉLIORÉ ---

def mode_simple():
    st.title("🏭 Expert Palettisation - Module Simple")
    
    # --- SECTION 1 : GESTION DES RÉFÉRENCES ---
    with st.expander("📁 Base de Données Références", expanded=False):
        c1, c2, c3, c4, c5 = st.columns([2,1,1,1,1])
        ref_name = c1.text_input("Nom de la référence", placeholder="ex: TV-SAMSUNG-55")
        ref_l = c2.number_input("Long (mm)", value=400)
        ref_w = c3.number_input("Larg (mm)", value=300)
        ref_h = c4.number_input("Haut (mm)", value=250)
        ref_p = c5.number_input("Poids (kg)", value=12.0)
        
        if st.button("➕ Ajouter/Mettre à jour la référence"):
            new_row = pd.DataFrame([{"Référence": ref_name, "Long": ref_l, "Larg": ref_w, "Haut": ref_h, "Poids": ref_p}])
            st.session_state.db_refs = pd.concat([st.session_state.db_refs, new_row]).drop_duplicates(subset=['Référence'], keep='last')
        
        st.dataframe(st.session_state.db_refs, use_container_width=True, hide_index=True)

    # --- SECTION 2 : CONFIGURATION DU RACK ---
    st.divider()
    with st.sidebar:
        st.subheader("🏗️ Contraintes Logistiques")
        l_lisse = st.selectbox("Longueur de lisse (mm)", [2700, 3600, 1350])
        p_max_lisse = st.number_input("Poids max Lisse (kg)", value=3000)
        h_max_rack = st.number_input("Hauteur Max Rack (mm)", value=1800)
        target_pal = st.selectbox("Type de Palette", ["800x1200", "1000x1200"])
        w_pal = 800 if "800" in target_pal else 1000
        
        selected_ref = st.selectbox("Charger une référence", ["Manuel"] + st.session_state.db_refs["Référence"].tolist())
        
        if selected_ref != "Manuel":
            r_data = st.session_state.db_refs[st.session_state.db_refs["Référence"] == selected_ref].iloc[0]
            cl, cw, ch, cp = r_data["Long"], r_data["Larg"], r_data["Haut"], r_data["Poids"]
        else:
            cl, cw, ch, cp = ref_l, ref_w, ref_h, ref_p

    res = calculate_best_fit(w_pal, l_lisse, h_max_rack, cl, cw, ch, cp, p_max_lisse, 0)

    if res:
        # --- SECTION 3 : INDICATEURS ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Capacité Palette", f"{res['total']} Colis")
        m2.metric("Poids total", f"{round(res['poids'])} kg")
        m3.metric("Occupation Lisse", f"{res['nb_pal_sol']} Palettes")
        m4.metric("Facteur Limitant", res['cause'])

        # --- SECTION 4 : VISUALISATION RACK ---
        st.write("### 🏗️ Vue en situation dans le Rack")
        
        fig_rack = go.Figure()
        # Dessin de la lisse (poutre)
        draw_cube(fig_rack, 0, l_lisse, 0, 100, -100, 0, "orange")
        # Dessin des palettes sur la lisse
        for i in range(res['nb_pal_sol']):
            offset_x = i * (w_pal + 50) + 25
            draw_cube(fig_rack, offset_x, offset_x + w_pal, 0, 1200, 0, 150, "#8D6E63")
            # Dessin d'une boîte symbolique par palette pour la vue rack
            draw_cube(fig_rack, offset_x+10, offset_x+w_pal-10, 10, 1190, 150, res['couches']*ch+150, "#2196F3", opacity=0.3)
        
        fig_rack.update_layout(scene=dict(aspectmode='data'), height=400, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig_rack, use_container_width=True)

        # --- SECTION 5 : DÉTAILS ET EXPORT ---
        t1, t2 = st.tabs(["💎 Vue 3D Détail", "🗺️ Plans 2D & Export"])
        with t1:
            fig3d = go.Figure()
            draw_cube(fig3d, 0, w_pal, 0, 1200, 0, 150, "peru")
            for k in range(res["couches"]):
                color = "#2196F3" if k % 2 == 0 else "#EF5350"
                for p in res["plan"]:
                    z0 = 150 + (k * ch)
                    fx, fy = (w_pal - p['x'] - p['w'], 1200 - p['y'] - p['h']) if k % 2 == 1 else (p['x'], p['y'])
                    draw_cube(fig3d, fx, fx+p['w'], fy, fy+p['h'], z0, z0+ch, color)
            fig3d.update_layout(scene=dict(aspectmode='data'), height=500)
            st.plotly_chart(fig3d, use_container_width=True)
            
        with t2:
            st.button("📄 Exporter la fiche technique (PDF)")
            st.info("L'export génère un plan de chargement incluant les couches impaires (bleues) et paires (rouges).")

def main():
    menu = st.sidebar.radio("SÉLECTION MODULE", ["Optimiseur Simple", "Container"])
    if menu == "Optimiseur Simple": mode_simple()
    else: st.info("Module Container en cours de maintenance")

if __name__ == "__main__":
    main()
