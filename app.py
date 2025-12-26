import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math

# --- CONFIGURATION ---
st.set_page_config(page_title="PalletRack Expert Pro", layout="wide")

# Initialisation de la base de données de session
if 'db_produits' not in st.session_state:
    st.session_state.db_produits = {}

# --- FONCTIONS DE DESSIN ---

def draw_cube(fig, x_min, x_max, y_min, y_max, z_min, z_max, color, name="", opacity=1.0):
    fig.add_trace(go.Mesh3d(
        x=[x_min, x_max, x_max, x_min, x_min, x_max, x_max, x_min],
        y=[y_min, y_min, y_max, y_max, y_min, y_min, y_max, y_max],
        z=[z_min, z_min, z_min, z_min, z_max, z_max, z_max, z_max],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color, opacity=opacity, flatshading=True, name=name, showlegend=False
    ))

def create_top_view(plan, w_pal, color, title):
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, y0=0, x1=w_pal, y1=1200, line=dict(color="#5D4037", width=4))
    for p in plan:
        fig.add_shape(type="rect", x0=p['x'], y0=p['y'], x1=p['x']+p['w'], y1=p['y']+p['h'],
                       fillcolor=color, line=dict(color="white", width=1))
    fig.update_layout(title=title, xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"), 
                      height=300, margin=dict(l=20,r=20,t=40,b=20), plot_bgcolor='white')
    return fig

# --- MOTEUR DE CALCUL ---

def get_layer_plan(W_max, L_max, cl, cw):
    plan = []
    nx, ny = int(W_max // cl), int(L_max // cw)
    for i in range(nx):
        for j in range(ny): plan.append({'x': i*cl, 'y': j*cw, 'w': cl, 'h': cw})
    # Remplissage bordures (rotation)
    rx = W_max - (nx * cl)
    if rx >= cw:
        for i in range(int(rx // cw)):
            for j in range(int(L_max // cl)): plan.append({'x': nx*cl + i*cw, 'y': j*cl, 'w': cw, 'h': cl})
    return plan

def calculate_fit(w_pal, l_lisse, h_max, cl, cw, ch, cp, p_max_lisse):
    nb_pal_sol = int(l_lisse // w_pal)
    poids_admis_pal = (p_max_lisse / nb_pal_sol) - 25
    plan = get_layer_plan(w_pal, 1200, cl, cw)
    if not plan: return None
    
    n_h = int((h_max - 150) // ch)
    n_p = int((poids_admis_pal // cp) // len(plan)) if cp > 0 else 99
    n_final = max(0, min(n_h, n_p))
    
    return {
        "total": n_final * len(plan), "couches": n_final, "plan": plan,
        "poids": (n_final * len(plan) * cp) + 25, "nb_pal": nb_pal_sol,
        "limit": "POIDS" if n_p < n_h else "HAUTEUR"
    }

# --- INTERFACE ---

def main():
    st.sidebar.title("🏢 Warehouse Manager Pro")
    menu = st.sidebar.selectbox("Module", ["Gestion de Références", "Optimiseur de Rack"])

    if menu == "Gestion de Références":
        st.header("📋 Base de Données Produits")
        with st.form("new_ref"):
            col1, col2, col3 = st.columns(3)
            nom = col1.text_input("Nom de la référence")
            l = col2.number_input("Longueur (mm)", value=400)
            w = col3.number_input("Largeur (mm)", value=300)
            h = col1.number_input("Hauteur (mm)", value=250)
            p = col2.number_input("Poids (kg)", value=12.0)
            if st.form_submit_button("Enregistrer la fiche"):
                st.session_state.db_produits[nom] = {"l":l, "w":w, "h":h, "p":p}
                st.success(f"Référence {nom} sauvegardée.")
        
        if st.session_state.db_produits:
            st.write("### Fiches enregistrées")
            st.table(pd.DataFrame(st.session_state.db_produits).T)

    else:
        st.header("🏗️ Optimisation du Rack")
        
        with st.sidebar:
            ref_sel = st.selectbox("Choisir une référence", list(st.session_state.db_produits.keys()))
            st.divider()
            l_lisse = st.selectbox("Longueur de Lisse", [2700, 3600, 1350])
            p_max_lisse = st.number_input("Charge Max Lisse (kg)", value=3000)
            h_dispo = st.number_input("Hauteur utile rack (mm)", value=1800)
            w_pal = st.radio("Type Palette", [800, 1000], horizontal=True)

        if ref_sel:
            prod = st.session_state.db_produits[ref_sel]
            res = calculate_fit(w_pal, l_lisse, h_dispo, prod['l'], prod['w'], prod['h'], prod['p'], p_max_lisse)

            # METRIQUES
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Colis / Palette", res['total'])
            c2.metric("Poids Palette", f"{round(res['poids'])} kg")
            c3.metric("Charge Lisse", f"{round(res['poids']*res['nb_pal'])} / {p_max_lisse}kg")
            c4.metric("Limité par", res['limit'])

            # VUE RACK COMPLET
            st.write("### 🛰️ Visualisation en Rack (Alvéole)")
            fig_rack = go.Figure()
            
            # Poteaux (Montants)
            draw_cube(fig_rack, -100, 0, 0, 1200, -100, h_dispo + 200, "royalblue")
            draw_cube(fig_rack, l_lisse, l_lisse+100, 0, 1200, -100, h_dispo + 200, "royalblue")
            
            # Lisses (Inférieure et Supérieure)
            draw_cube(fig_rack, 0, l_lisse, 0, 50, -50, 0, "orange") # Lisse bas
            draw_cube(fig_rack, 0, l_lisse, 0, 50, h_dispo, h_dispo+50, "orange") # Lisse haut
            
            # Palettes et Chargement
            for i in range(res['nb_pal']):
                x_off = i * (w_pal + 50) + 20
                draw_cube(fig_rack, x_off, x_off+w_pal, 0, 1200, 0, 150, "peru") # Palette
                # Bloc de charge simplifié pour le rack
                draw_cube(fig_rack, x_off+5, x_off+w_pal-5, 5, 1195, 150, 150+(res['couches']*prod['h']), "rgba(33, 150, 243, 0.5)")
            
            fig_rack.update_layout(scene=dict(aspectmode='data'), height=500, margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(fig_rack, use_container_width=True)

            # VUE 2D ET PLANS
            st.write("### 📋 Instructions de Montage")
            col_a, col_b = st.columns(2)
            with col_a:
                st.plotly_chart(create_top_view(res['plan'], w_pal, "#2196F3", "Couche A (Impaire)"), use_container_width=True)
            with col_b:
                # Calcul du miroir pour la couche B
                plan_b = [{'x': w_pal-p['x']-p['w'], 'y': 1200-p['y']-p['h'], 'w': p['w'], 'h': p['h']} for p in res['plan']]
                st.plotly_chart(create_top_view(plan_b, w_pal, "#EF5350", "Couche B (Paire)"), use_container_width=True)

            # EXPORT
            st.write("### 📥 Exportation")
            if st.button("Générer Fiche PDF (Impression)"):
                st.info("Utilisez 'Imprimer' (Ctrl+P) sur cette page. La mise en page est optimisée pour inclure les plans 2D et le rack.")

if __name__ == "__main__":
    main()
