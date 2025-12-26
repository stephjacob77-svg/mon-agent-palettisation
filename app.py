import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert WMS v8.9 - Tetris Fix", layout="wide")

if 'db_refs' not in st.session_state:
    st.session_state.db_refs = pd.DataFrame(columns=["Référence", "L", "W", "H", "P"])

# --- MOTEUR D'OPTIMISATION TETRIS RÉVISÉ ---

def get_best_plan(W_pal, L_pal, c_L, c_W):
    """
    Teste différentes combinaisons pour trouver le maximum de colis.
    """
    def scenario_tetris(W, L, cl, cw):
        plan = []
        # Bloc principal
        nx = int(W // cl)
        ny = int(L // cw)
        for i in range(nx):
            for j in range(ny):
                plan.append({'x': i * cl, 'y': j * cw, 'w': cl, 'h': cw})
        
        # Remplissage de la bande vide sur la droite (Rotation)
        reste_x = W - (nx * cl)
        if reste_x >= cw:
            ny_rot = int(L // cl)
            for j in range(ny_rot):
                plan.append({'x': nx * cl, 'y': j * cl, 'w': cw, 'h': cl})
        
        # Remplissage de la bande vide sur le haut (Rotation)
        reste_y = L - (ny * cw)
        if reste_y >= cl:
            nx_rot = int((nx * cl) // cw)
            for i in range(nx_rot):
                plan.append({'x': i * cw, 'y': ny * cw, 'w': cw, 'h': cl})
        return plan

    # On teste les deux orientations de départ de la palette
    p1 = scenario_tetris(W_pal, L_pal, c_L, c_W)
    p2 = scenario_tetris(W_pal, L_pal, c_W, c_L)
    
    return p1 if len(p1) >= len(p2) else p2

# --- FONCTIONS DE DESSIN ---

def draw_box(fig, x0, x1, y0, y1, z0, z1, color):
    fig.add_trace(go.Mesh3d(
        x=[x0, x1, x1, x0, x0, x1, x1, x0], y=[y0, y0, y1, y1, y0, y0, y1, y1], z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=1, flatshading=True, showlegend=False
    ))
    # Contours noirs pour la visibilité
    lx = [x0, x1, x1, x0, x0, None, x0, x1, x1, x0, x0, None, x0, x0, None, x1, x1, None, x1, x1, None, x0, x0]
    ly = [y0, y0, y1, y1, y0, None, y0, y0, y1, y1, y0, None, y0, y0, None, y0, y0, None, y1, y1, None, y1, y1]
    lz = [z0, z0, z0, z0, z0, None, z1, z1, z1, z1, z1, None, z0, z1, None, z0, z1, None, z0, z1, None, z0, z1]
    fig.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode='lines', line=dict(color='black', width=2), showlegend=False))

# --- INTERFACE ---

st.sidebar.title("🏭 Expert WMS v8.9")
menu = st.sidebar.radio("Navigation", ["Base Articles", "Optimisation"])

if menu == "Base Articles":
    st.header("📋 Référentiel Articles")
    with st.form("add"):
        c1, c2, c3, c4 = st.columns(4)
        n = c1.text_input("Référence")
        l = c2.number_input("L (mm)", value=400)
        w = c3.number_input("W (mm)", value=300)
        h = c4.number_input("H (mm)", value=250)
        if st.form_submit_button("Ajouter"):
            st.session_state.db_refs = pd.concat([st.session_state.db_refs, pd.DataFrame([{"Référence":n,"L":l,"W":w,"H":h}])]).drop_duplicates()
    st.dataframe(st.session_state.db_refs)

else:
    if st.session_state.db_refs.empty:
        st.warning("Ajoutez un article."); st.stop()
    
    with st.sidebar:
        ref = st.selectbox("Article", st.session_state.db_refs["Référence"].tolist())
        w_pal = st.selectbox("Largeur Palette", [800, 1000])
        l_pal = 1200
        h_max = st.number_input("Hauteur Max (mm)", value=1800)

    item = st.session_state.db_refs[st.session_state.db_refs["Référence"] == ref].iloc[0]
    
    # Calcul Tetris
    plan = get_best_plan(w_pal, l_pal, item['L'], item['W'])
    nb_couches = int((h_max - 150) // item['H'])
    
    st.header(f"Résultat pour {ref} : {len(plan)} colis/couche")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Plan de Pose 2D")
        fig2d = go.Figure()
        fig2d.add_trace(go.Scatter(x=[0, w_pal, w_pal, 0, 0], y=[0, 0, l_pal, l_pal, 0], fill="toself", fillcolor="lightgray", name="Palette"))
        for p in plan:
            fig2d.add_trace(go.Scatter(x=[p['x'], p['x']+p['w'], p['x']+p['w'], p['x'], p['x']], y=[p['y'], p['y'], p['y']+p['h'], p['y']+p['h'], p['y']], fill="toself", line=dict(color="white")))
        fig2d.update_layout(yaxis=dict(scaleanchor="x"), showlegend=False)
        st.plotly_chart(fig2d)

    with col2:
        st.subheader("Rendu 3D")
        fig3d = go.Figure()
        # Palette (Base)
        draw_box(fig3d, 0, w_pal, 0, l_pal, 0, 150, "peru")
        # Colis (Couche 1)
        for p in plan:
            draw_box(fig3d, p['x'], p['x']+p['w'], p['y'], p['y']+p['h'], 150, 150+item['H'], "royalblue")
        fig3d.update_layout(scene=dict(aspectmode='data'), margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig3d)
