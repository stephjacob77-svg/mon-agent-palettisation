import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert WMS Pro v8.6", layout="wide")

if 'db_refs' not in st.session_state:
    st.session_state.db_refs = pd.DataFrame(columns=["Référence", "L", "W", "H", "P"])

# --- FONCTIONS DE DESSIN ---

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

def draw_pro_pallet(fig, x0, w_pal, l_pal, z0, color="#8D6E63"):
    """Palette réaliste avec passage de fourches"""
    for off_x in [0, w_pal/2 - 50, w_pal - 100]: # Semelles
        draw_box(fig, x0+off_x, x0+off_x+100, 0, l_pal, z0, z0+25, color)
    for dx in [0, w_pal/2 - 50, w_pal - 100]: # Dés
        for dy in [0, l_pal/2 - 50, l_pal - 100]:
            draw_box(fig, x0+dx, x0+dx+100, dy, dy+100, z0+25, z0+125, color)
    draw_box(fig, x0, x0+w_pal, 0, l_pal, z0+125, z0+150, color) # Plateau

def draw_2d_layer(plan, w_pal, l_pal, color, title):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, w_pal, w_pal, 0, 0], y=[0, 0, l_pal, l_pal, 0], fill="toself", fillcolor="#D7CCC8", line=dict(color="#5D4037", width=2)))
    for p in plan:
        fig.add_trace(go.Scatter(x=[p['x'], p['x']+p['w'], p['x']+p['w'], p['x'], p['x']], y=[p['y'], p['y'], p['y']+p['h'], p['y']+p['h'], p['y']], fill="toself", fillcolor=color, line=dict(color="white", width=1), showlegend=False))
    fig.update_layout(title=title, xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"), height=300, margin=dict(l=10,r=10,t=40,b=10))
    return fig

# --- CALCULS ---

def get_best_plan(W, L, cl, cw):
    plan = []
    nx, ny = int(W // cl), int(L // cw)
    for i in range(nx):
        for j in range(ny): plan.append({'x': i*cl, 'y': j*cw, 'w': cl, 'h': cw})
    return plan

# --- UI ---

st.sidebar.title("🏭 Expert WMS Pro v8.6")
menu = st.sidebar.radio("Navigation", ["Base Articles", "Optimiseur Rack"])

if menu == "Base Articles":
    st.header("📋 Référentiel Articles")
    with st.form("add"):
        c1, c2, c3, c4, c5 = st.columns([2,1,1,1,1])
        n, l, w, h, p = c1.text_input("Nom"), c2.number_input("L"), c3.number_input("W"), c4.number_input("H"), c5.number_input("P")
        if st.form_submit_button("Ajouter"):
            st.session_state.db_refs = pd.concat([st.session_state.db_refs, pd.DataFrame([{"Référence":n,"L":l,"W":w,"H":h,"P":p}])]).drop_duplicates(subset='Référence')
    st.dataframe(st.session_state.db_refs, use_container_width=True)

else:
    with st.sidebar:
        if st.session_state.db_refs.empty: st.stop()
        ref_sel = st.selectbox("Article", st.session_state.db_refs["Référence"].tolist())
        fmt_pal = st.radio("Format Palette (mm)", ["800 x 1200", "1000 x 1200"])
        type_pal = st.selectbox("Type / Résistance", ["Lourde (Type Europe)", "Semi-Lourde", "Légère (Perdue)"])
        l_lisse = st.selectbox("Longueur Lisse", [2700, 3600, 1350])
        h_utile = st.number_input("Hauteur Utile Rack", value=1800)
        p_max_l = st.number_input("Capacité Lisse (kg)", value=3000)

    # Variables de base
    item = st.session_state.db_refs[st.session_state.db_refs["Référence"] == ref_sel].iloc[0]
    w_pal = 800 if "800" in fmt_pal else 1000
    p_bois = 25 if "Lourde" in type_pal else (20 if "Semi" in type_pal else 12)
    
    # Calcul de palettisation
    plan = get_best_plan(w_pal, 1200, item['L'], item['W'])
    nb_pal_sol = l_lisse // w_pal
    n_h = (h_utile - 150) // item['H']
    n_p = ((p_max_l/nb_pal_sol - p_bois)//item['P']) // len(plan) if item['P'] > 0 else 99
    couches = int(max(0, min(n_h, n_p)))
    total_colis = len(plan) * couches
    p_charge = total_colis * item['P']

    # --- 1. RECOMMANDATION & ALERTES ---
    st.subheader("💡 Analyse Technique & Sécurité")
    c_rec1, c_rec2, c_rec3 = st.columns(3)
    with c_rec1:
        if p_charge > 1000 and "Lourde" not in type_pal:
            st.error(f"🛑 SUPPORT INADAPTÉ : {int(p_charge)}kg nécessite une palette Lourde (Europe).")
        elif p_charge < 400: st.success("✅ Support léger validé.")
        else: st.info("ℹ️ Support standard préconisé.")
    with c_rec2:
        garde = h_utile - (150 + couches * item['H'])
        st.metric("Garde d'Air", f"{int(garde)} mm", delta=f"{int(garde-100)} mm", delta_color="normal" if garde >= 100 else "inverse")
    with c_rec3:
        taux = (nb_pal_sol * w_pal * 1200 * (150+couches*item['H'])) / (l_lisse * 1200 * h_utile) * 100
        st.metric("Occupation Alvéole", f"{taux:.2f} %", delta_color="inverse" if taux > 95 else "normal")

    # --- 2. VUES 3D & 2D ---
    tab1, tab2 = st.tabs(["🏗️ Simulation Rack & Palette", "📋 Schémas de Pose (2D)"])
    with tab1:
        v1, v2 = st.columns(2)
        with v1:
            f1 = go.Figure(); draw_pro_pallet(f1, 0, w_pal, 1200, 0)
            for k in range(couches):
                col = "#2196F3" if k % 2 == 0 else "#EF5350"
                for p in plan:
                    z = 150 + (k*item['H'])
                    # Alternance pour stabilité (croisement)
                    fx, fy = (w_pal-p['x']-p['w'], 1200-p['y']-p['h']) if k%2==1 else (p['x'],p['y'])
                    draw_box(f1, fx, fx+p['w'], fy, fy+p['h'], z, z+item['H'], col)
            f1.update_layout(scene=dict(aspectmode='data'), height=500, margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(f1, use_container_width=True)
        with v2:
            f2 = go.Figure()
            # Structure Rack (Echelle 1:1)
            for px in [-100, l_lisse]:
                for py in [0, 1100]: draw_box(f2, px, px+100, py, py+100, -100, h_utile+200, "royalblue")
            draw_box(f2, 0, l_lisse, 0, 100, -150, 0, "orange") # Lisse AV
            draw_box(f2, 0, l_lisse, 1100, 1200, -150, 0, "orange") # Lisse AR
            for i in range(int(nb_pal_sol)):
                x_st = 10 if i == 0 else (l_lisse - w_pal - 10)
                draw_pro_pallet(f2, x_st, w_pal, 1200, 0)
                draw_box(f2, x_st+20, x_st+w_pal-20, 20, 1180, 150, 150+(couches*item['H']), "rgba(33, 150, 243, 0.4)")
            f2.update_layout(scene=dict(aspectmode='data'), height=500, margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(f2, use_container_width=True)

    with tab2:
        c2d1, c2d2 = st.columns(2)
        c2d1.plotly_chart(draw_2d_layer(plan, w_pal, 1200, "#2196F3", "Couches Impaires (1, 3, 5...)"), use_container_width=True)
        plan_croise = [{'x': w_pal-p['x']-p['w'], 'y': 1200-p['y']-p['h'], 'w': p['w'], 'h': p['h']} for p in plan]
        c2d2.plotly_chart(draw_2d_layer(plan_croise, w_pal, 1200, "#EF5350", "Couches Paires (2, 4, 6...)"), use_container_width=True)

    # --- 3. ÉTIQUETTE ---
    st.divider()
    st.subheader("🏷️ Étiquette Palette Logistique")
    st.markdown(f"""
        <div style="border:3px solid black; padding:20px; background:white; color:black; font-family:monospace;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid black;">
                <div><h1 style="margin:0;">REF: {item['Référence']}</h1></div>
                <div style="text-align:right;"><h2>POIDS: {round(p_charge+p_bois)} KG</h2></div>
            </div>
            <div style="display:flex; margin-top:10px;">
                <div style="flex:1;">
                    <p><b>FORMAT:</b> {fmt_pal} | <b>TYPE:</b> {type_pal}</p>
                    <p><b>COLIS TOTAL:</b> {total_colis} (C: {couches} x {len(plan)})</p>
                    <p><b>EMPLACEMENT:</b> _________________</p>
                </div>
                <div style="flex:1; border:1px solid #ccc; text-align:center; padding:5px;">
                    <small>Schéma Couche 1</small><br>
                    <div style="height:60px; background:#eee; border:1px dashed #666; display:flex; align-items:center; justify-content:center;">
                        [PLAN {len(plan)} COLIS]
                    </div>
                </div>
            </div>
            <div style="background:black; color:white; text-align:center; font-size:24px; padding:5px; margin-top:10px;">
                || ||| || |||| || ||| |||| || |||
            </div>
        </div>
    """, unsafe_allow_html=True)
