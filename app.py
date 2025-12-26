import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert WMS Pro v9.3", layout="wide")

if 'db_refs' not in st.session_state:
    st.session_state.db_refs = pd.DataFrame([{"Référence":"BOX_300x200", "L":300, "W":200, "H":150, "P":10.0}])

# --- MOTEUR D'OPTIMISATION (CONSERVÉ) ---

def get_optimal_layer(W_pal, L_pal, cl, cw):
    def strategy(W, L, c_l, c_w):
        plan = []
        nx, ny = int(W // c_l), int(L // c_w)
        for i in range(nx):
            for j in range(ny):
                plan.append({'x': i * c_l, 'y': j * c_w, 'w': c_l, 'h': c_w})
        rx = W - (nx * c_l)
        if rx >= c_w:
            for j in range(int(L // c_l)):
                plan.append({'x': nx * c_l, 'y': j * c_l, 'w': c_w, 'h': c_l})
        ry = L - (ny * c_w)
        if ry >= c_l:
            for i in range(int((nx * c_l) // c_w)):
                plan.append({'x': i * c_w, 'y': ny * c_w, 'w': c_w, 'h': c_l})
        return plan
    s1 = strategy(W_pal, L_pal, cl, cw)
    s2 = strategy(W_pal, L_pal, cw, cl)
    return s1 if len(s1) >= len(s2) else s2

def get_crossed_layer(plan, W_pal, L_pal):
    return [{'x': W_pal - p['x'] - p['w'], 'y': L_pal - p['y'] - p['h'], 'w': p['w'], 'h': p['h']} for p in plan]

# --- FONCTIONS GRAPHIQUES AVANCÉES ---

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

def draw_industrial_pallet(fig, x_off, w_p, l_p, z_off):
    """Rendu réaliste d'une palette (Hauteur 150mm)"""
    c_wood = "#8D6E63"
    # Semelles (Bas)
    for sx in [0, w_p/2-50, w_p-100]:
        draw_box(fig, x_off+sx, x_off+sx+100, 0, l_p, z_off, z_off+25, c_wood)
    # Dés (Milieu)
    for dx in [0, w_p/2-50, w_p-100]:
        for dy in [0, l_p/2-50, l_p-100]:
            draw_box(fig, x_off+dx, x_off+dx+100, dy, dy+100, z_off+25, z_off+125, c_wood)
    # Plateau (Haut)
    draw_box(fig, x_off, x_off+w_p, 0, l_p, z_off+125, z_off+150, c_wood)

# --- INTERFACE ---

st.sidebar.title("🏭 Expert WMS v9.3")
ref_sel = st.sidebar.selectbox("Article", st.session_state.db_refs["Référence"].tolist())
fmt_pal = st.sidebar.radio("Format Palette", ["800 x 1200 (EUROPE)", "1000 x 1200 (VMF)"])
h_rack = st.sidebar.number_input("Hauteur Utile Rack (mm)", value=1800)

item = st.session_state.db_refs[st.session_state.db_refs["Référence"] == ref_sel].iloc[0]
w_p = 800 if "800" in fmt_pal else 1000

# Calculs
plan_a = get_optimal_layer(w_p, 1200, item['L'], item['W'])
plan_b = get_crossed_layer(plan_a, w_p, 1200)
nb_c = int((h_rack - 150) // item['H'])
h_totale = 150 + (nb_c * item['H'])

# --- DASHBOARD ---
st.header(f"📦 Simulation Industrielle : {ref_sel}")
c1, c2, c3 = st.columns(3)
c1.metric("Colis / Couche", len(plan_a))
c2.metric("Total Palette", len(plan_a) * nb_c)
c3.metric("Garde d'air", f"{h_rack - h_totale} mm")

tabs = st.tabs(["🏗️ Vue 3D Système", "🏷️ Étiquette & 2D"])

with tabs[0]:
    v1, v2 = st.columns([1, 1])
    with v1:
        st.subheader("Détail Palette")
        f1 = go.Figure()
        draw_industrial_pallet(f1, 0, w_p, 1200, 0)
        for k in range(nb_c):
            p_curr = plan_a if k % 2 == 0 else plan_b
            col = "#1E88E5" if k % 2 == 0 else "#E53935"
            for b in p_curr:
                draw_box(f1, b['x'], b['x']+b['w'], b['y'], b['y']+b['h'], 150+(k*item['H']), 150+((k+1)*item['H']), col)
        f1.update_layout(scene=dict(aspectmode='data'), height=600, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(f1, use_container_width=True)

    with v2:
        st.subheader("Implantation Rack")
        f2 = go.Figure()
        # Rack (Montants 100x100)
        l_lisse = 2700
        for px in [-100, l_lisse]:
            for py in [0, 1100]: draw_box(f2, px, px+100, py, py+100, -100, h_rack+200, "royalblue")
        # Lisses (Hauteur 150mm)
        draw_box(f2, 0, l_lisse, 0, 100, -150, 0, "orange")
        draw_box(f2, 0, l_lisse, 1100, 1200, -150, 0, "orange")
        # Remplissage alvéole
        for i in range(int(l_lisse // w_p)):
            x_st = i * (w_p + 50) + 25
            draw_industrial_pallet(f2, x_st, w_p, 1200, 0)
            draw_box(f2, x_offset := x_st+10, x_offset+w_p-20, 10, 1190, 150, h_totale, "rgba(33, 150, 243, 0.4)")
        f2.update_layout(scene=dict(aspectmode='data'), height=600, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(f2, use_container_width=True)

with tabs[1]:
    st.subheader("Plan de Pose & Étiquette")
    # Schémas 2D
    c2d1, c2d2 = st.columns(2)
    def draw_2d(plan, color, title):
        f = go.Figure()
        f.add_trace(go.Scatter(x=[0,w_p,w_p,0,0], y=[0,0,1200,1200,0], fill="toself", fillcolor="#D7CCC8", line=dict(color="black")))
        for p in plan:
            f.add_trace(go.Scatter(x=[p['x'],p['x']+p['w'],p['x']+p['w'],p['x'],p['x']], y=[p['y'],p['y'],p['y']+p['h'],p['y']+p['h'],p['y']], fill="toself", fillcolor=color, line=dict(color="white")))
        f.update_layout(title=title, yaxis=dict(scaleanchor="x"), showlegend=False, height=350)
        return f
    c2d1.plotly_chart(draw_2d(plan_a, "#1E88E5", "Couche IMPAIRE"), use_container_width=True)
    c2d2.plotly_chart(draw_2d(plan_b, "#E53935", "Couche PAIRE"), use_container_width=True)

    # Étiquette Logistique
    st.markdown(f"""
    <div style="border:3px solid black; padding:20px; background:white; font-family:monospace; color:black;">
        <table style="width:100%">
            <tr><td><h1>REF: {item['Référence']}</h1></td><td style="text-align:right"><h1>{int(len(plan_a)*nb_c*item['P'])} kg</h1></td></tr>
        </table>
        <hr>
        <h3>CONTENU: {len(plan_a)*nb_c} COLIS | COUCHES: {nb_c} x {len(plan_a)}</h3>
        <h3>SUPPORT: {fmt_pal} | HAUTEUR: {h_totale}mm</h3>
    </div>
    """, unsafe_allow_html=True)
