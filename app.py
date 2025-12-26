import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert Palettisation Pro v8.7", layout="wide")

if 'db_refs' not in st.session_state:
    st.session_state.db_refs = pd.DataFrame(columns=["Référence", "L", "W", "H", "P"])

# --- MOTEUR D'OPTIMISATION (ROTATION & REMPLISSAGE) ---

def get_complex_plan(W, L, cl, cw):
    """Calcule le meilleur plan avec rotation pour maximiser l'espace"""
    plan = []
    # 1. Orientation Standard
    nx, ny = int(W // cl), int(L // cw)
    for i in range(nx):
        for j in range(ny):
            plan.append({'x': i*cl, 'y': j*cw, 'w': cl, 'h': cw})
    
    # 2. Remplissage du reliquat en X (Rotation)
    rx = W - (nx * cl)
    if rx >= cw:
        for j in range(int(L // cl)):
            plan.append({'x': nx*cl, 'y': j*cl, 'w': cw, 'h': cl})
            
    # 3. Remplissage du reliquat en Y (si possible)
    ry = L - (ny * cw)
    if ry >= cl:
        for i in range(int(W // cw)):
            plan.append({'x': i*cw, 'y': ny*cw, 'w': cw, 'h': cl})
            
    return plan

# --- FONCTIONS DE DESSIN ---

def draw_box(fig, x0, x1, y0, y1, z0, z1, color, opacity=1.0):
    fig.add_trace(go.Mesh3d(
        x=[x0, x1, x1, x0, x0, x1, x1, x0], y=[y0, y0, y1, y1, y0, y0, y1, y1], z=[z0, z0, z0, z0, z1, z1, z1, z1],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=opacity, flatshading=True, showlegend=False
    ))
    # Arêtes
    lx = [x0, x1, x1, x0, x0, None, x0, x1, x1, x0, x0, None, x0, x0, None, x1, x1, None, x1, x1, None, x0, x0]
    ly = [y0, y0, y1, y1, y0, None, y0, y0, y1, y1, y0, None, y0, y0, None, y0, y0, None, y1, y1, None, y1, y1]
    lz = [z0, z0, z0, z0, z0, None, z1, z1, z1, z1, z1, None, z0, z1, None, z0, z1, None, z0, z1, None, z0, z1]
    fig.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode='lines', line=dict(color='black', width=1), showlegend=False))

def draw_real_pallet(fig, x0, w_pal, l_pal, z0, color="#8D6E63"):
    """Modèle réaliste 150mm : Semelles + Dés + Plateau"""
    for off_x in [0, w_pal/2 - 50, w_pal - 100]:
        draw_box(fig, x0+off_x, x0+off_x+100, 0, l_pal, z0, z0+25, color)
    for dx in [0, w_pal/2 - 50, w_pal - 100]:
        for dy in [0, l_pal/2 - 50, l_pal - 100]:
            draw_box(fig, x0+dx, x0+dx+100, dy, dy+100, z0+25, z0+125, color)
    draw_box(fig, x0, x0+w_pal, 0, l_pal, z0+125, z0+150, color)

def draw_2d_layer(plan, w_pal, l_pal, color, title):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, w_pal, w_pal, 0, 0], y=[0, 0, l_pal, l_pal, 0], fill="toself", fillcolor="#E0E0E0", line=dict(color="#5D4037", width=3)))
    for p in plan:
        fig.add_trace(go.Scatter(x=[p['x'], p['x']+p['w'], p['x']+p['w'], p['x'], p['x']], y=[p['y'], p['y'], p['y']+p['h'], p['y']+p['h'], p['y']], fill="toself", fillcolor=color, line=dict(color="white", width=2), showlegend=False))
    fig.update_layout(title=title, xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"), height=300, margin=dict(l=10,r=10,t=40,b=10))
    return fig

# --- LOGIQUE D'INTERFACE ---

st.sidebar.title("📦 WMS EXPERT v8.7")
mode = st.sidebar.radio("Navigation", ["Articles", "Simulation"])

if mode == "Articles":
    st.header("📋 Référentiel")
    with st.form("add"):
        c1, c2, c3, c4, c5 = st.columns([2,1,1,1,1])
        n, l, w, h, p = c1.text_input("Référence"), c2.number_input("L"), c3.number_input("W"), c4.number_input("H"), c5.number_input("P")
        if st.form_submit_button("Ajouter"):
            st.session_state.db_refs = pd.concat([st.session_state.db_refs, pd.DataFrame([{"Référence":n,"L":l,"W":w,"H":h,"P":p}])]).drop_duplicates()
    st.dataframe(st.session_state.db_refs)
else:
    if st.session_state.db_refs.empty: st.warning("Ajoutez des articles."); st.stop()
    
    with st.sidebar:
        ref_sel = st.selectbox("Article", st.session_state.db_refs["Référence"].tolist())
        fmt_pal = st.radio("Format Palette", ["800 x 1200", "1000 x 1200"])
        
        # Filtre dynamique des types de palettes
        if "800" in fmt_pal:
            type_pal = st.selectbox("Modèle", ["EUROPE (Lourde)", "LÉGÈRE (800)"])
            w_pal = 800
        else:
            type_pal = st.selectbox("Modèle", ["VMF (Lourde)", "LÉGÈRE (1000)"])
            w_pal = 1000
            
        l_lisse = st.selectbox("Lisse", [2700, 3600, 1350])
        h_utile = st.number_input("Hauteur Utile", value=1800)
        p_max_l = st.number_input("Poids Max Lisse", value=3000)

    # Calculs
    item = st.session_state.db_refs[st.session_state.db_refs["Référence"] == ref_sel].iloc[0]
    p_bois = 25 if ("EUROPE" in type_pal or "VMF" in type_pal) else 12
    plan_a = get_complex_plan(w_pal, 1200, item['L'], item['W'])
    
    nb_pal_sol = l_lisse // w_pal
    n_h = (h_utile - 150) // item['H']
    n_p = ((p_max_l/nb_pal_sol - p_bois)//item['P']) // len(plan_a) if item['P'] > 0 else 99
    couches = int(max(0, min(n_h, n_p)))
    
    p_charge = len(plan_a) * couches * item['P']
    h_totale = 150 + (couches * item['H'])
    garde = h_utile - h_totale

    # --- ALERTES SÉCURITÉ ---
    st.subheader("💡 Recommandation & Sécurité")
    a1, a2, a3 = st.columns(3)
    with a1:
        if p_charge > 600 and "LÉGÈRE" in type_pal:
            st.error(f"🛑 DANGER : Charge de {int(p_charge)}kg trop lourde pour une palette légère. Changez pour EUROPE/VMF.")
        elif p_charge > 1000: st.info("👍 Support Lourd (EPAL/VMF) requis et sélectionné.")
        else: st.success("✅ Support adapté.")
    with a2:
        st.metric("Garde d'Air (Vide)", f"{int(garde)} mm", delta=f"{int(garde-100)} mm", delta_color="normal" if garde >= 100 else "inverse")
    with a3:
        taux = (nb_pal_sol * w_pal * 1200 * h_totale) / (l_lisse * 1200 * h_utile) * 100
        st.metric("Occupation Alvéole", f"{taux:.2f} %")

    # --- AFFICHAGE GRAPHIQUE ---
    st.write("### 🧊 Vues 3D (Palette & Rack)")
    c3d1, c3d2 = st.columns(2)
    with c3d1:
        f1 = go.Figure(); draw_real_pallet(f1, 0, w_pal, 1200, 0)
        for k in range(couches):
            col = "#2196F3" if k % 2 == 0 else "#EF5350"
            for p in plan_a:
                z = 150 + (k*item['H'])
                # Rotation alternée pour la stabilité
                fx, fy = (w_pal-p['x']-p['w'], 1200-p['y']-p['h']) if k%2==1 else (p['x'],p['y'])
                draw_box(f1, fx, fx+p['w'], fy, fy+p['h'], z, z+item['H'], col)
        f1.update_layout(scene=dict(aspectmode='data'), height=450, margin=dict(l=0,r=0,b=0,t=0)); st.plotly_chart(f1)
    
    with c3d2:
        
        f2 = go.Figure()
        # Rack structure
        for px in [-100, l_lisse]:
            for py in [0, 1100]: draw_box(f2, px, px+100, py, py+100, -100, h_utile+200, "royalblue")
        draw_box(f2, 0, l_lisse, 0, 100, -150, 0, "orange")
        for i in range(int(nb_pal_sol)):
            x_st = 20 if i == 0 else (l_lisse - w_pal - 20)
            draw_real_pallet(f2, x_st, w_pal, 1200, 0)
            draw_box(f2, x_st+20, x_st+w_pal-20, 20, 1180, 150, h_totale, "rgba(33,150,243,0.3)")
        f2.update_layout(scene=dict(aspectmode='data'), height=450, margin=dict(l=0,r=0,b=0,t=0)); st.plotly_chart(f2)

    st.write("### 📋 Vues 2D (Schémas de pose)")
    c2d1, c2d2 = st.columns(2)
    c2d1.plotly_chart(draw_2d_layer(plan_a, w_pal, 1200, "#2196F3", "Couche A (Impaire)"), use_container_width=True)
    plan_b = [{'x': w_pal-p['x']-p['w'], 'y': 1200-p['y']-p['h'], 'w': p['w'], 'h': p['h']} for p in plan_a]
    c2d2.plotly_chart(draw_2d_layer(plan_b, w_pal, 1200, "#EF5350", "Couche B (Paire)"), use_container_width=True)

    # --- ÉTIQUETTE ---
    st.divider()
    st.subheader("🏷️ Étiquette Générée")
    st.markdown(f"""
    <div style="border:4px solid black; padding:15px; background:white; color:black; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between; border-bottom:3px solid black;">
            <div><h2 style="margin:0;">REF: {item['Référence']}</h2></div>
            <div><h2 style="margin:0;">{round(p_charge+p_bois)} KG</h2></div>
        </div>
        <div style="margin-top:10px;">
            <p><b>PALETTE:</b> {fmt_pal} {type_pal}</p>
            <p><b>CONTENU:</b> {total_colis} COLIS ({couches} COUCHES)</p>
            <p><b>GARDE D'AIR RACK:</b> {int(garde)} mm</p>
        </div>
        <div style="background:black; color:white; text-align:center; padding:5px; font-weight:bold; letter-spacing:5px;">
            CODE-A-{item['Référence'][:3].upper()}
        </div>
    </div>
    """, unsafe_allow_html=True)
