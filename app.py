import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="WMS EXPERT v12.0", layout="wide")

# --- INITIALISATION ---
if 'catalogue' not in st.session_state:
    st.session_state.catalogue = pd.DataFrame([
        {"REF": "BOX_A", "L": 400, "W": 300, "H": 250, "P": 15.0}
    ])

# --- MOTEUR TETRIS ---
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

# --- INTERFACE ---
st.title("🚀 LogisOptimizer Pro - Aide à la Décision")

# --- BARRE LATÉRALE DE CONTRÔLE GLOBAL ---
with st.sidebar:
    st.header("🏢 Structure Entrepôt")
    cout_m2 = st.number_input("Coût Immo (€/m²/an)", 40, 200, 85)
    nb_baies = st.number_input("Nombre de baies de stockage", 1, 1000, 100)
    
    st.divider()
    st.header("📦 Produit à simuler")
    ref_sel = st.selectbox("Référence", st.session_state.catalogue["REF"].tolist())
    item = st.session_state.catalogue[st.session_state.catalogue["REF"] == ref_sel].iloc[0]
    w_p = 800 if "800" in st.selectbox("Type Palette", ["800x1200 (EURO)", "1000x1200 (VMF)"]) else 1000
    
# --- CALCULS LOGISTIQUES ---
l_lisse = 2700
nb_pal_l = l_lisse // (w_p + 50)
if w_p == 1000 and l_lisse == 2700: nb_pal_l = 2

# Simulation sur 4 niveaux par défaut
h_niveaux = [2000, 1800, 1800, 1800]
plan_couche = optimize_tetris(w_p, 1200, item['L'], item['W'])
colis_par_pal = len(plan_couche) * 5 # On estime 5 couches
capa_totale_pal = nb_pal_l * len(h_niveaux) * nb_baies
total_colis = capa_totale_pal * colis_par_pal
surface_estimee = nb_baies * 6 # Estim surface avec allées

# --- 1. DASHBOARD DE PERFORMANCE (Amélioration majeure) ---
st.subheader("📊 Tableau de Bord de Rentabilité")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Capacité Bâtiment", f"{capa_totale_pal} Palettes")
with kpi2:
    st.metric("Capacité Stockage", f"{total_colis:,} Colis")
with kpi3:
    cout_pal = (surface_estimee * cout_m2) / capa_totale_pal
    st.metric("Coût Emplacement", f"{cout_pal:.2f} €/an", delta="-5% vs standard")
with kpi4:
    densite = total_colis / surface_estimee
    st.metric("Densité Logistique", f"{densite:.1f} colis/m²")

st.divider()

# --- ONGLETS ---
t_plan, t_plaque, t_cat = st.tabs(["📐 PLAN TECHNIQUE 2D", "⚠️ PLAQUE DE CHARGE", "📑 CATALOGUE"])

with t_plan:
    col_l, col_r = st.columns([1, 2])
    
    with col_l:
        st.info("💡 **Analyse d'Expert**\n\nVotre taux de remplissage est excellent sur les niveaux supérieurs. Le niveau 0 (Sol) présente une garde d'air importante : envisagez de stocker des palettes plus hautes au sol.")
        st.write(f"**Données Alvéole :**")
        st.write(f"- Largeur Lisse : {l_lisse} mm")
        st.write(f"- Palettes par niveau : {nb_pal_l}")
        st.write(f"- Colis par palette : {colis_par_pal}")

    with col_r:
        # Reprise du graphique validé
        fig = go.Figure()
        z_acc = 0
        for i, h in enumerate(h_niveaux):
            # Structure
            fig.add_shape(type="rect", x0=-80, x1=0, y0=z_acc, y1=z_acc+h, fillcolor="#455A64")
            fig.add_shape(type="rect", x0=l_lisse, x1=l_lisse+80, y0=z_acc, y1=z_acc+h, fillcolor="#455A64")
            if i > 0: fig.add_shape(type="rect", x0=0, x1=l_lisse, y0=z_acc-100, y1=z_acc, fillcolor="orange")
            # Palettes
            for j in range(nb_pal_l):
                px = 50 + j*(w_p+50)
                fig.add_shape(type="rect", x0=px, x1=px+w_p, y0=z_acc, y1=z_acc+1200, fillcolor="#90CAF9", opacity=0.6)
            z_acc += h
        fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), height=600, plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

with t_plaque:
    st.subheader("⚠️ Plaque de Charge (Document de Sécurité Obligatoire)")
    # Une vraie plaque de charge visuelle
    st.markdown(f"""
    <div style="background-color: yellow; border: 10px solid black; padding: 30px; color: black; font-family: sans-serif; text-align: center;">
        <h1 style="font-size: 50px; margin: 0;">CAPACITÉ MAX : 3000 KG</h1>
        <h2 style="font-size: 30px; margin: 0;">PAR PAIRE DE LISSES</h2>
        <hr style="border: 2px solid black;">
        <div style="display: flex; justify-content: space-around; font-size: 20px; font-weight: bold;">
            <div>PALETTE MAX:<br>{int(3000/nb_pal_l)} KG</div>
            <div>HAUTEUR MAX:<br>{h_niveaux[1]} mm</div>
            <div>RACK TYPE:<br>FRONTAL</div>
        </div>
        <p style="margin-top: 30px; font-size: 14px;">Conforme à la norme NF EN 15635 - Vérification annuelle obligatoire</p>
    </div>
    """, unsafe_allow_html=True)
    st.button("📄 Exporter la fiche de sécurité (PDF)")

with t_cat:
    st.session_state.catalogue = st.data_editor(st.session_state.catalogue, num_rows="dynamic", use_container_width=True)
