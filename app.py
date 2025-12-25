import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import io

# --- FONCTIONS GRAPHIQUES ---
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

# --- MODE 1 : OPTIMISATEUR SIMPLE ---
def mode_calculateur_unique():
    st.header("📦 Optimisateur de Palette Unique")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        cl = st.number_input("Longueur Carton (mm)", value=400)
        cw = st.number_input("Largeur Carton (mm)", value=300)
        ch = st.number_input("Hauteur Carton (mm)", value=250)
        h_max = st.number_input("Hauteur Max (mm)", value=1800)
        overhang = st.slider("Débordement (mm)", 0, 50, 0)
        target_pal = st.selectbox("Format Palette", ["800x1200", "1000x1200"])

    W_pal = 800 if "800" in target_pal else 1000
    L_pal = 1200
    W_max, L_max = W_pal + (2*overhang), L_pal + (2*overhang)
    
    plan = get_mixed_layer_plan(W_max, L_max, cl, cw)
    nb_couches = int((h_max - 150) // ch)
    
    with col2:
        fig = go.Figure()
        draw_cube(fig, [0, W_pal], [0, L_pal], [0, 150], "peru")
        for k in range(nb_couches):
            color = ["#3498db", "#e74c3c"][k % 2]
            for (x, y, dx, dy) in plan:
                z0 = 150 + (k * ch)
                fx, fy = ((W_max-x-dx), (L_max-y-dy)) if k%2==1 else (x,y)
                draw_cube(fig, [fx-overhang, fx+dx-overhang], [fy-overhang, fy+dy-overhang], [z0, z0+ch], color)
        fig.update_layout(scene=dict(aspectmode='data'), height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    st.metric("Total Colis", len(plan) * nb_couches)

# --- MODE 2 : DECHARGEMENT CONTAINER ---
def mode_container():
    st.header("🚢 Déchargement & Import Packing List")
    
    # Upload de fichier
    uploaded_file = st.file_uploader("Importer votre Packing List (Excel ou CSV)", type=['xlsx', 'csv'])
    
    if uploaded_file:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.success("Packing list chargée avec succès !")
    else:
        st.info("Utilisez le tableau ci-dessous ou importez un fichier.")
        df = pd.DataFrame([
            {"Référence": "Ref_001", "Long": 400, "Larg": 300, "Haut": 250, "Poids": 10, "Quantité": 120},
            {"Référence": "Ref_002", "Long": 600, "Larg": 400, "Haut": 300, "Poids": 15, "Quantité": 45}
        ])

    data = st.data_editor(df, num_rows="dynamic")
    
    target_pal = st.sidebar.selectbox("Format Palette", ["800x1200", "1000x1200"])
    W_pal = 800 if "800" in target_pal else 1000
    h_max = st.sidebar.number_input("Hauteur Max Palette (mm)", value=1800)
    
    total_pal = 0
    recap = []

    for _, row in data.iterrows():
        if row["Quantité"] > 0:
            plan = get_mixed_layer_plan(W_pal, 1200, row["Long"], row["Larg"])
            nb_c = int((h_max - 150) // row["Haut"])
            par_pal = len(plan) * nb_c
            nb_pal = -(-row["Quantité"] // par_pal)
            total_pal += nb_pal
            recap.append({"Réf": row["Référence"], "Palettes": nb_pal, "Colis/Pal": par_pal})

    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("Total Palettes Container", int(total_pal))
    c2.metric("Mètres Linéaires estimés", f"{round(total_pal * (W_pal/1000), 1)} m")
    st.table(pd.DataFrame(recap))

# --- MAIN APP ---
def main():
    st.set_page_config(page_title="IA Logistique Hub", layout="wide")
    
    # MENU LATERAL
    st.sidebar.title("🛠️ Menu Principal")
    choice = st.sidebar.radio("Choisir un outil :", 
                              ["Optimiseur Simple", "Déchargement Container"])
    
    if choice == "Optimiseur Simple":
        mode_calculateur_unique()
    else:
        mode_container()

if __name__ == "__main__":
    main()
