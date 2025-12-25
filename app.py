import streamlit as st
import plotly.graph_objects as go

def draw_cube(fig, x_range, y_range, z_range, color='royalblue', opacity=0.7):
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

def optimize_layer(W_pal, L_pal, c_l, c_w, overhang):
    # Ajout du débordement autorisé
    W_max = W_pal + (2 * overhang)
    L_max = L_pal + (2 * overhang)
    
    # Test Sens A (Standard)
    nx_a, ny_a = W_max // c_l, L_max // c_w
    # Test Sens B (Tourné)
    nx_b, ny_b = W_max // c_w, L_max // c_l
    
    if (nx_a * ny_a) >= (nx_b * ny_b):
        return nx_a, ny_a, c_l, c_w
    else:
        return nx_b, ny_b, c_w, c_l

def generate_pallet_plan():
    st.set_page_config(page_title="IA Palettisation Expert", layout="wide")
    st.title("📦 Optimiseur de Palettisation V2")

    # --- SIDEBAR ---
    st.sidebar.header("⚙️ Paramètres")
    c_l = st.sidebar.number_input("Longueur carton (mm)", value=400)
    c_w = st.sidebar.number_input("Largeur carton (mm)", value=300)
    c_h = st.sidebar.number_input("Hauteur carton (mm)", value=250)
    c_p = st.sidebar.number_input("Poids carton (kg)", value=10.0)
    
    overhang = st.sidebar.slider("Débordement autorisé (mm)", 0, 50, 0)
    h_lisse = st.sidebar.number_input("Hauteur entre lisses (mm)", value=1800)
    
    st.sidebar.subheader("Choix Palette")
    auto_pal = st.sidebar.toggle("Optimisation automatique du format", True)
    manual_pal = st.sidebar.selectbox("Format forcé", ["800x1200", "1000x1200"])

    # --- LOGIQUE DE COMPARAISON ---
    results = []
    formats = [800, 1000] if auto_pal else ([800] if "800" in manual_pal else [1000])
    
    for W in formats:
        nx, ny, dx, dy = optimize_layer(W, 1200, c_l, c_w, overhang)
        nb_couches = int((h_lisse - 150 - 100) // c_h)
        total = int(nx * ny * nb_couches)
        results.append({"W": W, "nx": nx, "ny": ny, "dx": dx, "dy": dy, "total": total, "couches": nb_couches})

    # Sélection de la meilleure
    best = max(results, key=lambda x: x['total'])
    
    # --- AFFICHAGE ---
    st.success(f"Format optimal détecté : {best['W']}x1200 mm ({best['total']} colis)")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Vue 3D Interactive")
        fig = go.Figure()
        draw_cube(fig, [0, best['W']], [0, 1200], [0, 150], color='peru') # Palette
        
        for k in range(best['couches']):
            # Logique de croisement : on inverse dx et dy une couche sur deux
            curr_dx, curr_dy = (best['dx'], best['dy']) if k % 2 == 0 else (best['dy'], best['dx'])
            curr_nx = (best['W'] + 2*overhang) // curr_dx
            curr_ny = (1200 + 2*overhang) // curr_dy
            
            for i in range(int(curr_nx)):
                for j in range(int(curr_ny)):
                    z0 = 150 + (k * c_h)
                    # Décalage pour centrer si débordement
                    x_start = (i * curr_dx) - overhang
                    y_start = (j * curr_dy) - overhang
                    draw_cube(fig, [x_start, x_start + curr_dx], [y_start, y_start + curr_dy], [z0, z0+c_h])
        
        fig.update_layout(margin=dict(l=0,r=0,b=0,t=0), scene=dict(aspectmode='data'))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Plan de couche (Vue de dessus)")
        # Schéma 2D simplifié avec Plotly
        fig2d = go.Figure()
        # Contour palette
        fig2d.add_shape(type="rect", x0=0, y0=0, x1=best['W'], y1=1200, line=dict(color="Brown", width=3))
        # Cartons couche 1
        for i in range(int(best['nx'])):
            for j in range(int(best['ny'])):
                x_s = (i * best['dx']) - overhang
                y_s = (j * best['dy']) - overhang
                fig2d.add_shape(type="rect", x0=x_s, y0=y_s, x1=x_s+best['dx'], y1=y_s+best['dy'], 
                               fillcolor="royalblue", line=dict(color="white", width=1))
        
        fig2d.update_layout(xaxis_range=[-50, 1050], yaxis_range=[-50, 1250], height=500)
        st.plotly_chart(fig2d, use_container_width=True)

if __name__ == "__main__":
    generate_pallet_plan()
