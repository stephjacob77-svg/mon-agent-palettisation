import streamlit as st
import plotly.graph_objects as go

# --- CONFIGURATION ET STYLE ---
st.set_page_config(page_title="Expert Palettisation v6.0", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .css-1r6slb0 { border: 1px solid #e0e0e0; border-radius: 10px; padding: 20px; background: white; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS TECHNIQUES ---
def draw_cube(fig, x_min, x_max, y_min, y_max, z_min, z_max, color, opacity=0.8):
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
        for j in range(ny): plan.append((i*cl, j*cw, cl, cw))
    reste_x = W_max - (nx * cl)
    if reste_x >= cw:
        for i in range(int(reste_x // cw)):
            for j in range(int(L_max // cl)): plan.append((nx*cl + i*cw, j*cl, cw, cl))
    return plan

def create_top_view(plan, w_pal, w_max_c, l_max_c, overhang, mirrored, title, color):
    fig = go.Figure()
    # Palette
    fig.add_shape(type="rect", x0=0, y0=0, x1=w_pal, y1=1200, line=dict(color="#5D4037", width=4))
    # Colis
    for (x, y, dx, dy) in plan:
        fx, fy = (w_max_c - x - dx, l_max_c - y - dy) if mirrored else (x, y)
        fig.add_shape(type="rect", x0=fx-overhang, y0=fy-overhang, x1=fx+dx-overhang, y1=fy+dy-overhang, 
                       fillcolor=color, opacity=0.6, line=dict(color="white", width=1))
    
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=14)),
        xaxis=dict(range=[-100, w_pal+100], visible=False),
        yaxis=dict(range=[-100, 1300], visible=False, scaleanchor="x", scaleratio=1),
        margin=dict(l=10, r=10, t=40, b=10), height=350, plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# --- LOGIQUE PRINCIPALE ---
def main():
    st.title("🏗️ Warehouse Optimization Tool")
    
    with st.sidebar:
        st.header("⚙️ Paramètres")
        with st.expander("Rack & Lisse", expanded=True):
            l_lisse = st.selectbox("Longueur de lisse (mm)", [2700, 3600, 1350])
            p_max_lisse = st.number_input("Poids max Lisse (kg)", value=3000)
            h_max_rack = st.number_input("Hauteur Max Rack (mm)", value=1800)
        
        with st.expander("Dimensions Colis", expanded=True):
            cl = st.number_input("Longueur (mm)", value=400)
            cw = st.number_input("Largeur (mm)", value=300)
            ch = st.number_input("Hauteur (mm)", value=250)
            cp = st.number_input("Poids (kg)", value=12.0)
            overhang = st.slider("Débordement (mm)", 0, 50, 0)
        
        target_pal = st.selectbox("Type de Palette", ["800x1200 (Euro)", "1000x1200 (VMF)"])
        w_pal = 800 if "800" in target_pal else 1000

    # --- CALCULS ---
    nb_pal_sol = int(l_lisse // w_pal)
    poids_max_par_pal = (p_max_lisse / nb_pal_sol) - 25
    colis_max_poids = int(poids_max_par_pal // cp)
    
    w_max_c, l_max_c = w_pal + 2*overhang, 1200 + 2*overhang
    plan = get_layer_plan(w_max_c, l_max_c, cl, cw)
    colis_par_couche = len(plan)
    
    nb_couches_h = int((h_max_rack - 150) // ch)
    nb_couches_p = (colis_max_poids // colis_par_couche) if colis_par_couche > 0 else 0
    
    nb_couches_final = min(nb_couches_h, nb_couches_p)
    colis_total = nb_couches_final * colis_par_couche
    poids_total_pal = (colis_total * cp) + 25

    # --- AFFICHAGE DASHBOARD ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Colis / Palette", colis_total)
    c2.metric("Poids / Palette", f"{round(poids_total_pal, 1)} kg")
    c3.metric("Palettes / Niveau", nb_pal_sol)
    
    charge_perc = (poids_total_pal * nb_pal_sol) / p_max_lisse
    c4.metric("Occupation Lisse", f"{round(charge_perc*100)} %")

    if nb_couches_p < nb_couches_h:
        st.warning(f"⚠️ Limitation par le poids : {nb_couches_final} couches max autorisées.")

    # --- VUES ---
    tab1, tab2 = st.tabs(["📊 Vue 3D Interactive", "📋 Plans de Montage 2D"])
    
    with tab1:
        col_3d, col_info = st.columns([2, 1])
        with col_3d:
            fig3d = go.Figure()
            draw_cube(fig3d, 0, w_pal, 0, 1200, 0, 150, "#8D6E63", 1) # Palette
            for k in range(nb_couches_final):
                color = "#2196F3" if k % 2 == 0 else "#EF5350"
                for (x, y, dx, dy) in plan:
                    z0 = 150 + (k * ch)
                    fx, fy = (w_max_c - x - dx, l_max_c - y - dy) if k % 2 == 1 else (x, y)
                    draw_cube(fig3d, fx-overhang, fx+dx-overhang, fy-overhang, fy+dy-overhang, z0, z0+ch, color)
            fig3d.update_layout(scene=dict(aspectmode='data'), height=600, margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(fig3d, use_container_width=True)
        
        with col_info:
            st.write("### Détails Logistiques")
            st.write(f"**Format :** {target_pal}")
            st.write(f"**Hauteur Totale :** {150 + (nb_couches_final * ch)} mm")
            st.write(f"**Charge Totale Lisse :** {round(poids_total_pal * nb_pal_sol)} kg")
            st.progress(min(charge_perc, 1.0))
            if st.button("Exporter les données"):
                st.toast("Préparation du rapport...")

    with tab2:
        st.write("### Schémas de Pose par Étage")
        v1, v2 = st.columns(2)
        with v1:
            st.plotly_chart(create_top_view(plan, w_pal, w_max_c, l_max_c, overhang, False, "Couches IMPAIRES (1, 3, 5...)", "#2196F3"), use_container_width=True)
        with v2:
            st.plotly_chart(create_top_view(plan, w_pal, w_max_c, l_max_c, overhang, True, "Couches PAIRES (2, 4, 6...)", "#EF5350"), use_container_width=True)

if __name__ == "__main__":
    main()
