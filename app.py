import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert WMS Pro v9.7.1 - FINAL ALIGN", layout="wide")

# Versionning ultra-visible pour éviter les erreurs de cache
st.markdown("<h1 style='color: #FF4B4B;'>VERSION 9.7.1 - ALIGNEMENT EXTRÉMITÉS FIXE</h1>", unsafe_allow_html=True)

if 'db_refs' not in st.session_state:
    st.session_state.db_refs = pd.DataFrame([{"Référence":"BOX_STANDARD", "L":300, "W":200, "H":150, "P":15.0}])

# --- MOTEUR D'OPTIMISATION ---
def get_optimal_layer(W_pal, L_pal, cl, cw):
    def strategy(W, L, c_l, c_w):
        plan = []
        nx, ny = int(W // c_l), int(L // c_w)
        for i in range(nx):
            for j in range(ny): plan.append({'x': i * c_l, 'y': j * c_w, 'w': c_l, 'h': c_w})
        rx, ry = W - (nx * c_l), L - (ny * c_w)
        if rx >= c_w:
            for j in range(int(L // c_l)): plan.append({'x': nx * c_l, 'y': j * c_l, 'w': c_w, 'h': c_l})
        if ry >= c_l:
            for i in range(int((nx * c_l) // c_w)): plan.append({'x': i * c_w, 'y': ny * c_w, 'w': c_w, 'h': c_l})
        return plan
    s1, s2 = strategy(W_pal, L_pal, cl, cw), strategy(W_pal, L_pal, cw, cl)
    return s1 if len(s1) >= len(s2) else s2

def get_crossed_layer(plan, W_pal, L_pal):
    return [{'x': W_pal - p['x'] - p['w'], 'y': L_pal - p['y'] - p['h'], 'w': p['w'], 'h': p['h']} for p in plan]

# --- FONCTIONS GRAPHIQUES ---
def draw_box(fig, x0, x1, y0, y1, z0, z1, color, opacity=1.0, line_width=1):
    fig.add_trace(go.Mesh3d(
        x=[x0, x1, x1, x0, x0, x1, x1, x0], y=[y0, y0, y1, y1, y0, y0, y1, y1], z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=opacity, flatshading=True, showlegend=False
    ))
    lx = [x0, x1, x1, x0, x0, None, x0, x1, x1, x0, x0, None, x0, x0, None, x1, x1, None, x1, x1, None, x0, x0]
    ly = [y0, y0, y1, y1, y0, None, y0, y0, y1, y1, y0, None, y0, y0, None, y0, y0, None, y1, y1, None, y1, y1]
    lz = [z0, z0, z0, z0, z0, None, z1, z1, z1, z1, z1, None, z0, z1, None, z0, z1, None, z0, z1, None, z0, z1]
    fig.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode='lines', line=dict(color='black', width=line_width), showlegend=False))

def draw_real_pallet(fig, x_off, w_p, l_p, z_off, color="#8D6E63"):
    for sx in [0, w_p/2-50, w_p-100]: draw_box(fig, x_off+sx, x_off+sx+100, 0, l_p, z_off, z_off+25, color)
    for dx in [0, w_p/2-50, w_p-100]:
        for dy in [0, l_p/2-50, l_p-100]: draw_box(fig, x_off+dx, x_off+dx+100, dy, dy+100, z_off+25, z_off+125, color)
    draw_box(fig, x_off, x_off+w_p, 0, l_p, z_off+125, z_off+150, color)

# --- INTERFACE ---
with st.sidebar:
    st.header("Paramètres")
    fmt = st.selectbox("Format Palette", ["1000x1200 (VMF)", "800x1200 (EURO)"])
    w_p = 1000 if "1000" in fmt else 800
    l_lisse = st.selectbox("Longueur de Lisse (mm)", [2700, 3300, 3600], index=0)
    h_max = st.number_input("Hauteur Rack (mm)", value=1800)
    ref = st.selectbox("Article", st.session_state.db_refs["Référence"].tolist())

item = st.session_state.db_refs[st.session_state.db_refs["Référence"] == ref].iloc[0]

# Calculs de charge
plan_a = get_optimal_layer(w_p, 1200, item['L'], item['W'])
plan_b = get_crossed_layer(plan_a, w_p, 1200)
nb_c = int((h_max - 150) // item['H'])
h_charge = 150 + (nb_c * item['H'])

# --- AFFICHAGE ---
st.subheader("Visualisation de l'espace vide central")


col1, col2 = st.columns([1, 2])

with col1:
    st.write("### Détail Palette Unique")
    f1 = go.Figure()
    draw_real_pallet(f1, 0, w_p, 1200, 0)
    for k in range(nb_c):
        p, col = (plan_a, "#1E88E5") if k % 2 == 0 else (plan_b, "#E53935")
        for b in p: draw_box(f1, b['x'], b['x']+b['w'], b['y'], b['y']+b['h'], 150+(k*item['H']), 150+((k+1)*item['H']), col)
    f1.update_layout(scene=dict(aspectmode='data'), height=500, margin=dict(l=0,r=0,b=0,t=0))
    st.plotly_chart(f1, use_container_width=True)

with col2:
    st.write(f"### Implantation Lisse {l_lisse} mm")
    f2 = go.Figure()
    # Structure Rack (Montants et Lisses)
    for px in [-100, l_lisse]:
        for py in [0, 1100]: draw_box(f2, px, px+100, py, py+100, -150, h_max+150, "#455A64")
    draw_box(f2, 0, l_lisse, 0, 100, -120, 0, "orange")
    draw_box(f2, 0, l_lisse, 1100, 1200, -120, 0, "orange")

    # PALETTE GAUCHE (Ancrée à 0)
    draw_real_pallet(f2, 0, w_p, 1200, 0)
    draw_box(f2, 5, w_p-5, 5, 1195, 150, h_charge, "rgba(30, 136, 229, 0.4)")
    
    # PALETTE DROITE (Ancrée à l'extrémité de la lisse)
    x_droite = l_lisse - w_p
    draw_real_pallet(f2, x_droite, w_p, 1200, 0)
    draw_box(f2, x_droite+5, l_lisse-5, 5, 1195, 150, h_charge, "rgba(30, 136, 229, 0.4)")
    
    # MESURE DU VIDE CENTRAL
    vide_central = l_lisse - (2 * w_p)
    if vide_central > 0:
        f2.add_trace(go.Scatter3d(
            x=[w_p, l_lisse-w_p], y=[600, 600], z=[h_charge+100, h_charge+100],
            mode='lines+text', text=[f"VIDE CENTRAL : {vide_central} mm"],
            line=dict(color='black', width=6)
        ))

    f2.update_layout(scene=dict(aspectmode='data'), height=600, margin=dict(l=0,r=0,b=0,t=0))
    st.plotly_chart(f2, use_container_width=True)
