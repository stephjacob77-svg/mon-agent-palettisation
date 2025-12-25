import streamlit as st
import plotly.graph_objects as go

def draw_cube(fig, x_range, y_range, z_range, color, opacity=0.8):
    x_min, x_max = x_range
    y_min, y_max = y_range
    z_min, z_max = z_range
    fig.add_trace(go.Mesh3d(
        x=[x_min, x_max, x_max, x_min, x_min, x_max, x_max, x_min],
        y=[y_min, y_min, y_max, y_max, y_min, y_min, y_max, y_max],
        z=[z_min, z_min, z_min, z_min, z_max, z_max, z_max, z_max],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], 
        j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], 
        k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=opacity, flatshading=True, showlegend=False
    ))

def get_mixed_layer_plan(W_max, L_max, cl, cw):
    plan = []
    nx = int(W_max // cl)
    ny = int(L_max // cw)
    for i in range(nx):
        for j in range(ny):
            plan.append((i*cl, j*cw, cl, cw))
    reste_x = W_max - (nx * cl)
    if reste_x >= cw:
        nx_reste = int(reste_x // cw)
        ny_reste = int(L_max // cl)
        for i in range(nx_reste):
            for j in range(ny_reste):
                plan.append((nx*cl + i*cw, j*cl, cw, cl))
    reste_y = L_max - (ny * cw)
    if reste_y >= cl:
        nx_reste_y = int((nx * cl) // cw)
        ny_reste_y = int(reste_y // cl)
        for i in range(nx_reste_y):
            for j in range(ny_reste_y):
                plan.append((i*cw, ny*cw + j*cl, cw, cl))
    return plan

def create_top_view(plan, W_pal, L_pal, W_max, L_max, overhang, is_mirrored, title, color):
    fig = go.Figure()
    # Palette
    fig.add_shape(type="rect", x0=0, y0=0, x1=W_pal, y1=L_pal, line=dict(color="brown", width=3))
    for (x, y, dx, dy) in plan:
        if is_mirrored:
            fx, fy = (W_max - x - dx), (L_max - y - dy)
        else:
            fx, fy = x, y
        fig.add_shape(type="rect", x0=fx-overhang, y0=fy-overhang, x1=fx+dx-overhang, y1=fy+dy-overhang, 
                       fillcolor=color, opacity=0.7, line=dict(color="white", width=2))
    
    fig.update_layout(
        title=title,
        xaxis=dict(range=[-100, W_pal+100], constrain='domain'),
        yaxis=dict(range=[-100, L_pal+100], scaleanchor="x", scaleratio=1),
        width=400, height=500, margin=dict(l=10, r=10, t=40, b=10)
    )
    return fig

def generate_pallet_plan():
    st.set_page_config(page_title="IA Palettisation", layout="wide")
    
    # --- Sidebar ---
    st.sidebar.header("📦 Colis")
    cl = st.sidebar.number_input("Longueur (mm)", value=400)
    cw = st.sidebar.number_input("Largeur (mm)", value=300)
    ch = st.sidebar.number_input("Hauteur (mm)", value=250)
    cp = st.sidebar.number_input("Poids (kg)", value=10.0)
    overhang = st.sidebar.slider("Débordement (mm)", 0, 50, 0)
    
    st.sidebar.header("🏗️ Rack")
    h_lisse = st.sidebar.number_input("Hauteur entre lisses (mm)", value=1800)
    
    st.sidebar.header("📏 Palette")
    target_pal = st.sidebar.selectbox("Format", ["800x1200", "1000x1200"])
    W_pal = 800 if "800" in target_pal else 1000
    L_pal = 1200
    
    # --- Calculs ---
    W_max, L_max = W_pal + (2 * overhang), L_pal + (2 * overhang)
    plan_couche = get_mixed_layer_plan(W_max, L_max, cl, cw)
    nb_couches = int((h_lisse - 250) // ch) 
    
    st.title(f"Plan de Palettisation Expert : {len(plan_couche) * nb_couches} colis")

    # --- Rendu 3D ---
    fig3d = go.Figure()
    draw_cube(fig3d, [0, W_pal], [0, L_pal], [0, 150], "peru")
    colors = ["#3498db", "#e74c3c", "#2ecc71", "#f1c40f", "#9b59b6"]
    
    for k in range(nb_couches):
        color = colors[k % len(colors)]
        for (x, y, dx, dy) in plan_couche:
            z0 = 150 + (k * ch)
            is_mirrored = (k % 2 == 1)
            if is_mirrored:
                fx, fy = (W_max - x - dx), (L_max - y - dy)
            else:
                fx, fy = x, y
            draw_cube(fig3d, [fx-overhang, fx+dx-overhang], [fy-overhang, fy+dy-overhang], [z0, z0+ch], color)
    
    fig3d.update_layout(scene=dict(aspectmode='data'), height=600, margin=dict(l=0,r=0,b=0,t=0))
    st.plotly_chart(fig3d, use_container_width=True)

    # --- Vues de dessus côte à côte ---
    st.divider()
    st.subheader("Plans de pose par étage (Echelle 1:1)")
    c1, c2 = st.columns(2)
    
    with c1:
        fig_layer1 = create_top_view(plan_couche, W_pal, L_pal, W_max, L_max, overhang, False, "Étages Impairs (1, 3, 5...)", "#3498db")
        st.plotly_chart(fig_layer1)
        
    with c2:
        if nb_couches > 1:
            fig_layer2 = create_top_view(plan_couche, W_pal, L_pal, W_max, L_max, overhang, True, "Étages Pairs (2, 4, 6...)", "#e74c3c")
            st.plotly_chart(fig_layer2)
        else:
            st.info("Une seule couche prévue.")

if __name__ == "__main__":
    generate_pallet_plan()
