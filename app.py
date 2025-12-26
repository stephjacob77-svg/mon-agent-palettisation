import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert WMS Pro v8.4", layout="wide")

if 'db_refs' not in st.session_state:
    st.session_state.db_refs = pd.DataFrame(columns=["Référence", "L", "W", "H", "P"])

# --- FONCTIONS DE DESSIN ---

def draw_real_pallet(fig, x0, w_pal, l_pal, z0, color="#8D6E63"):
    """Dessine une palette avec semelles et dés (passage de fourches)"""
    # Semelles (3 planches au sol)
    for offset_x in [0, w_pal/2 - 50, w_pal - 100]:
        draw_box(fig, x0 + offset_x, x0 + offset_x + 100, 0, l_pal, z0, z0 + 25, color)
    # Dés (blocs)
    for dx in [0, w_pal/2 - 50, w_pal - 100]:
        for dy in [0, l_pal/2 - 50, l_pal - 100]:
            draw_box(fig, x0 + dx, x0 + dx + 100, dy, dy + 100, z0 + 25, z0 + 100, color)
    # Plateau supérieur
    draw_box(fig, x0, x0 + w_pal, 0, l_pal, z0 + 100, z0 + 150, color)

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

def draw_2d_layer(plan, w_pal, color, title):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, w_pal, w_pal, 0, 0], y=[0, 0, 1200, 1200, 0], fill="toself", fillcolor="#D7CCC8", line=dict(color="#5D4037", width=3)))
    for p in plan:
        fig.add_trace(go.Scatter(x=[p['x'], p['x']+p['w'], p['x']+p['w'], p['x'], p['x']], y=[p['y'], p['y'], p['y']+p['h'], p['y']+p['h'], p['y']], fill="toself", fillcolor=color, line=dict(color="white", width=1.5), showlegend=False))
    fig.update_layout(title=title, xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"), height=300, margin=dict(l=10,r=10,t=40,b=10))
    return fig

# --- LOGIQUE MÉTIER ---

def get_optimized_plan(W, L, cl, cw):
    plan = []
    nx, ny = int(W // cl), int(L // cw)
    for i in range(nx):
        for j in range(ny): plan.append({'x': i*cl, 'y': j*cw, 'w': cl, 'h': cw})
    return plan

# --- UI ---

st.sidebar.title("🛠️ Expert WMS Pro v8.4")
mode = st.sidebar.radio("Navigation", ["Base Articles", "Simulateur Rack"])

if mode == "Base Articles":
    st.header("📋 Référentiel Articles")
    with st.form("add"):
        c1, c2, c3, c4, c5 = st.columns([2,1,1,1,1])
        n, l, w, h, p = c1.text_input("Référence"), c2.number_input("L"), c3.number_input("W"), c4.number_input("H"), c5.number_input("P")
        if st.form_submit_button("Ajouter"):
            st.session_state.db_refs = pd.concat([st.session_state.db_refs, pd.DataFrame([{"Référence":n,"L":l,"W":w,"H":h,"P":p}])]).drop_duplicates(subset='Référence')
    st.dataframe(st.session_state.db_refs, use_container_width=True)
else:
    with st.sidebar:
        ref_sel = st.selectbox("Article", st.session_state.db_refs["Référence"].tolist())
        l_lisse = st.selectbox("Lisse (mm)", [2700, 3600, 1350])
        h_utile = st.number_input("Haut. Utile (mm)", value=1800)
        p_type = st.selectbox("Type Palette", ["Europe (EPAL) - 25kg", "Standard - 20kg", "Légère/Perdue - 12kg"])
        p_bois = 25 if "Europe" in p_type else (20 if "Standard" in p_type else 12)
        w_pal = 800 if "800" in p_type or "Europe" in p_type else 1000 # Europe est par défaut 800x1200
        p_max_l = st.number_input("Capacité Lisse (kg)", value=3000)

    item = st.session_state.db_refs[st.session_state.db_refs["Référence"] == ref_sel].iloc[0]
    plan = get_optimized_plan(w_pal, 1200, item['L'], item['W'])
    nb_pal = l_lisse // w_pal
    couches = int(min((h_utile-150)//item['H'], ((p_max_l/nb_pal - p_bois)//item['P'])//len(plan)))
    p_charge = len(plan) * couches * item['P']
    p_total_pal = p_charge + p_bois

    # --- RECOMMANDATION PALETTE ---
    st.subheader("💡 Recommandation Technique")
    if p_charge > 1000 and "Europe" not in p_type:
        st.error(f"⚠️ ATTENTION : Charge de {int(p_charge)}kg trop élevée pour ce support. Utilisez une palette EUROPE (EPAL).")
    elif p_charge < 400:
        st.success(f"✅ Charge légère ({int(p_charge)}kg). Une palette PERDUE est suffisante et plus économique.")
    else:
        st.info(f"ℹ️ Charge modérée ({int(p_charge)}kg). Palette STANDARD ou EUROPE recommandée.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Poids Total Palette", f"{round(p_total_pal)} kg")
    garde_air = h_utile - (150 + couches*item['H'])
    c2.metric("Garde d'Air", f"{int(garde_air)} mm", delta_color="inverse" if garde_air < 100 else "normal")
    c3.metric("Taux d'Alvéole", f"{( (nb_pal*w_pal*1200*(150+couches*item['H'])) / (l_lisse*1200*h_utile) *100):.2f} %")

    # --- VUES 3D ---
    st.write("### 🧊 Modélisation Réaliste")
    v1, v2 = st.columns(2)
    with v1:
        st.caption("Détail Palette & Passage Fourches")
        f1 = go.Figure(); draw_real_pallet(f1, 0, w_pal, 1200, 0)
        for k in range(couches):
            col = "#2196F3" if k % 2 == 0 else "#EF5350"
            for p in plan:
                z = 150 + (k*item['H'])
                fx, fy = (w_pal-p['x']-p['w'], 1200-p['y']-p['h']) if k%2==1 else (p['x'],p['y'])
                draw_box(f1, fx, fx+p['w'], fy, fy+p['h'], z, z+item['H'], col)
        f1.update_layout(scene=dict(aspectmode='data'), height=500, margin=dict(l=0,r=0,b=0,t=0)); st.plotly_chart(f1, use_container_width=True)

    with v2:
        st.caption("Vue Rack avec Montants")
        
        f2 = go.Figure()
        for px in [-100, l_lisse]:
            for py in [0, 1100]: draw_box(f2, px, px+100, py, py+100, -100, h_utile+200, "royalblue")
        draw_box(f2, 0, l_lisse, 0, 50, -50, 0, "orange"); draw_box(f2, 0, l_lisse, 1050, 1100, -50, 0, "orange")
        draw_box(f2, 0, l_lisse, 0, 50, h_utile, h_utile+50, "orange")
        for i in range(int(nb_pal)):
            x_st = 5 if i == 0 else (l_lisse-w_pal-5 if i==nb_pal-1 else i*(w_pal+50))
            draw_real_pallet(f2, x_st, w_pal, 1200, 0)
            draw_box(f2, x_st+15, x_st+w_pal-15, 15, 1185, 150, 150+(couches*item['H']), "rgba(33, 150, 243, 0.4)")
        f2.update_layout(scene=dict(aspectmode='data'), height=500, margin=dict(l=0,r=0,b=0,t=0)); st.plotly_chart(f2, use_container_width=True)

    if st.button("🏷️ Générer l'étiquette Palette (PDF)"):
        st.success("Génération de l'étiquette avec Référence, Poids, et Plan de palettisation...")
