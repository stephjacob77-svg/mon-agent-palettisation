import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- FONCTIONS TECHNIQUES ---
def draw_cube(fig, x_range, y_range, z_range, color, opacity=0.8):
    x_min, x_max = x_range
    y_min, y_max = y_range
    z_min, z_max = z_range
    fig.add_trace(go.Mesh3d(
        x=[x_min, x_max, x_max, x_min, x_min, x_max, x_max, x_min],
        y=[y_min, y_min, y_max, y_max, y_min, y_min, y_max, y_max],
        z=[z_min, z_min, z_min, z_min, z_max, z_max, z_max, z_max],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=opacity, flatshading=True, showlegend=False
    ))

def get_mixed_layer_plan(W_max, L_max, cl, cw):
    plan = []
    nx, ny = int(W_max // cl), int(L_max // cw)
    for i in range(nx):
        for j in range(ny): plan.append((i*cl, j*cw, cl, cw))
    reste_x = W_max - (nx * cl)
    if reste_x >= cw:
        for i in range(int(reste_x // cw)):
            for j in range(int(L_max // cl)): plan.append((nx*cl + i*cw, j*cl, cw, cl))
    reste_y = L_max - (ny * cw)
    if reste_y >= cl:
        for i in range(int((nx * cl) // cw)):
            for j in range(int(reste_y // cl)): plan.append((i*cw, ny*cw + j*cl, cw, cl))
    return plan

def top_view(plan, W_pal, L_pal, W_max, L_max, overhang, mirrored, color):
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, y0=0, x1=W_pal, y1=L_pal, line=dict(color="brown", width=3))
    for (x, y, dx, dy) in plan:
        fx, fy = (W_max-x-dx, L_max-y-dy) if mirrored else (x, y)
        fig.add_shape(type="rect", x0=fx-overhang, y0=fy-overhang, x1=fx+dx-overhang, y1=fy+dy-overhang, 
                       fillcolor=color, opacity=0.5, line=dict(color="white", width=2))
    fig.update_layout(xaxis=dict(range=[-50, W_pal+50]), yaxis=dict(range=[-50, L_pal+50], scaleanchor="x", scaleratio=1), margin=dict(l=0,r=0,t=0,b=0), height=300)
    return fig

# --- MODE 1 : OPTIMISEUR SIMPLE ---
def mode_simple():
    st.subheader("📋 Configuration du Colis Unique")
    col1, col2, col3 = st.columns(3)
    cl = col1.number_input("Longueur (mm)", value=400)
    cw = col2.number_input("Largeur (mm)", value=300)
    ch = col3.number_input("Hauteur (mm)", value=250)
    
    st.divider()
    
    W_pal = 800 if "800" in st.session_state.target_pal else 1000
    L_pal = 1200
    overhang = st.session_state.overhang
    h_max = st.session_state.h_max
    
    W_max, L_max = W_pal + (2*overhang), L_pal + (2*overhang)
    plan = get_mixed_layer_plan(W_max, L_max, cl, cw)
    nb_c = int((h_max - 150) // ch)
    
    c1, c2 = st.columns([2, 1])
    with c1:
        fig3d = go.Figure()
        draw_cube(fig3d, [0, W_pal], [0, L_pal], [0, 150], "peru")
        for k in range(nb_c):
            color = "#3498db" if k%2==0 else "#e74c3c"
            for (x, y, dx, dy) in plan:
                z0 = 150 + (k*ch)
                fx, fy = (W_max-x-dx, L_max-y-dy) if k%2==1 else (x,y)
                draw_cube(fig3d, [fx-overhang, fx+dx-overhang], [fy-overhang, fy+dy-overhang], [z0, z0+ch], color)
        fig3d.update_layout(scene=dict(aspectmode='data'), height=500)
        st.plotly_chart(fig3d, use_container_width=True)
    
    with c2:
        st.metric("Colis / Palette", len(plan)*nb_c)
        st.write("**Plans de pose**")
        st.plotly_chart(top_view(plan, W_pal, L_pal, W_max, L_max, overhang, False, "#3498db"), use_container_width=True)
        st.plotly_chart(top_view(plan, W_pal, L_pal, W_max, L_max, overhang, True, "#e74c3c"), use_container_width=True)

# --- MODE 2 : CONTAINER ---
def mode_container():
    st.subheader("🚢 Rapport de Déchargement")
    up = st.file_uploader("Importer Packing List (Excel/CSV)")
    df = pd.read_csv(up) if up else pd.DataFrame([{"Référence": "Ref_A", "Long": 400, "Larg": 300, "Haut": 250, "Poids": 10, "Quantité": 100}])
    data = st.data_editor(df, num_rows="dynamic")

    W_pal = 800 if "800" in st.session_state.target_pal else 1000
    h_max = st.session_state.h_max
    
    total_p = 0
    st.write("### Détail par Référence")
    for _, row in data.iterrows():
        if row["Quantité"] > 0:
            plan = get_mixed_layer_plan(W_pal, 1200, row["Long"], row["Larg"])
            nb_c = int((h_max - 150) // row["Haut"])
            par_p = len(plan) * nb_c
            nb_p = -(-row["Quantité"] // par_p)
            total_p += nb_p
            
            with st.expander(f"📖 Fiche de montage : {row['Référence']} ({nb_p} palettes)"):
                st.write(f"Utiliser des palettes {W_pal}x1200. Monter {nb_c} couches.")
                v1, v2 = st.columns(2)
                v1.plotly_chart(top_view(plan, W_pal, 1200, W_pal, 1200, 0, False, "#3498db"))
                v2.plotly_chart(top_view(plan, W_pal, 1200, W_pal, 1200, 0, True, "#e74c3c"))

    st.sidebar.metric("TOTAL PALETTES", int(total_p))

def main():
    st.set_page_config(page_title="IA Palettisation Pro", layout="wide")
    st.sidebar.title("MENU")
    mode = st.sidebar.radio("Outil", ["Optimiseur Simple", "Rapport Déchargement"])
    
    st.sidebar.divider()
    st.session_state.target_pal = st.sidebar.selectbox("Palette", ["800x1200", "1000x1200"])
    st.session_state.h_max = st.sidebar.number_input("Hauteur Max (mm)", value=1800)
    st.session_state.overhang = st.sidebar.slider("Débordement (mm)", 0, 50, 0)
    
    if mode == "Optimiseur Simple": mode_simple()
    else: mode_container()

if __name__ == "__main__": main()
