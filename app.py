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
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=opacity, flatshading=True, showlegend=False
    ))

def get_mixed_layer_plan(W_max, L_max, cl, cw):
    """Calcule une couche avec mélange d'orientations"""
    plan = []
    # Bloc principal
    nx = W_max // cl
    ny = L_max // cw
    for i in range(int(nx)):
        for j in range(int(ny)):
            plan.append((i*cl, j*cw, cl, cw))
    
    # Remplissage de la bande résiduelle en Largeur (X)
    reste_x = W_max - (nx * cl)
    if reste_x >= cw:
        ny_reste = L_max // cl
        nx_reste = reste_x // cw
        for i in range(int(nx_reste)):
            for j in range(int(ny_reste)):
                plan.append((nx*cl + i*cw, j*cl, cw, cl))
                
    # Remplissage de la bande résiduelle en Longueur (Y) si vide
    reste_y = L_max - (ny * cw)
    if reste_y >= cl:
        nx_reste_y = (nx * cl) // cw
        ny_reste_y = reste_y // cl
        for i in range(int(nx_reste_y)):
            for j in range(int(ny_reste_y)):
                plan.append((i*cw, ny*cw + j*cl, cw, cl))
    
    return plan

def generate_pallet_plan():
    st.set_page_config(page_title="IA Palettisation Mixed", layout="wide")
    st.sidebar.header("📦 Dimensions Colis")
    cl = st.sidebar.number_input("Long. (mm)", value=400)
    cw = st.sidebar.number_input("Larg. (mm)", value=300)
    ch = st.sidebar.number_input("Haut. (mm)", value=250)
    overhang = st.sidebar.slider("Débordement (mm)", 0, 50, 0)
    h_lisse = st.sidebar.number_input("Hauteur Rack (mm)", value=1800)
    
    st.sidebar.header("🏗️ Type Palette")
    target_pal = st.sidebar.selectbox("Format", ["800x1200", "1000x1200"])
    W_pal = 800 if "800" in target_pal else 1000
    L_pal = 1200
    
    # Calculs
    plan_couche = get_mixed_layer_plan(W_pal + 2*overhang, L_pal + 2*overhang, cl, cw)
    nb_couches = int((h_lisse - 250) // ch) # 150 palette + 100 marge
    colors = ["#3498db", "#e74c3c", "#2ecc71", "#f1c40f", "#9b59b6", "#e67e22"]

    st.title(f"Plan d'optimisation : {len(plan_couche) * nb_couches} colis")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Visualisation 3D (Couleurs par étage)")
        fig = go.Figure()
        draw_cube(fig, [0, W_pal], [0, L_pal], [0, 150], "peru") # Palette
        
        for k in range(nb_couches):
            color = colors[k % len(colors)]
            # On applique une rotation de 180° ou un décalage une couche sur deux pour croiser
            for (x, y, dx, dy) in plan_couche:
                z0 = 150 + (k * ch)
                # Inversion simple pour le croisement de stabilité
                if k % 2 == 1:
                    final_x, final_y = (W_pal + 2*overhang - x - dx), (L_pal + 2*overhang - y - dy)
                else:
                    final_x, final_y = x, y
                
                draw_cube(fig, [final_x-overhang, final_x+dx-overhang], 
                               [final_y-overhang, final_y+dy-overhang], 
                               [z0, z0+ch], color)
        
        fig.update_layout(scene=dict(aspectmode='data'), margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Plan de pose (Vue de dessus)")
        fig2 = go.Figure()
        fig2.add_shape(type="rect", x0=0, y0=0, x1=W_pal, y1=L_pal, line=dict(color="brown", width=4))
        for (x, y, dx, dy) in plan_couche:
            fig2.add_shape(type="rect", x0=x-overhang, y0=y-overhang, x1=x+dx-overhang, y1=y+dy-overhang, 
                           fillcolor="royalblue", line=dict(color="white", width=2))
        fig2.update_layout(xaxis_range=[-100, W_pal+100], yaxis_range=[-100, L_pal+100])
        st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    generate_pallet_plan()
        fig2d.update_layout(xaxis_range=[-50, 1050], yaxis_range=[-50, 1250], height=500)
        st.plotly_chart(fig2d, use_container_width=True)

if __name__ == "__main__":
    generate_pallet_plan()
