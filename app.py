import streamlit as st
import pandas as pd
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
from datetime import datetime

# ----------------------------------------
# 1. CONFIGURACIÓN E INICIALIZACIÓN
# ----------------------------------------
st.set_page_config(page_title="Domino's Cloud Tracker", page_icon="🍕", layout="wide")
load_dotenv()

# Conexión Robusta a MongoDB (Capa de Datos)
@st.cache_resource(show_spinner=False)
def init_connection():
    try:
        client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
        client.admin.command('ping') 
        # Usamos corchetes para evitar errores con los guiones en el nombre
        return client["s11-dominos"]["dominos"] 
    except ConnectionFailure:
        st.error("🚨 Error crítico: No se pudo conectar a la base de datos Cloud (Atlas).")
        return None
    except Exception as e:
        st.error(f"🚨 Error inesperado: {e}")
        return None

collection = init_connection()

# ----------------------------------------
# 2. LÓGICA DE BASE DE DATOS (Mini-Repositorio)
# ----------------------------------------
def obtener_pedidos_activos():
    if collection is not None:
        # Trae pedidos que no estén entregados
        cursor = collection.find({"estado": {"$ne": "Entregado"}})
        return list(cursor)
    return []

def obtener_metricas():
    if collection is not None:
        total = collection.count_documents({})
        entregados = collection.count_documents({"estado": "Entregado"})
        en_proceso = total - entregados
        return total, en_proceso, entregados
    return 0, 0, 0

# ----------------------------------------
# 3. INTERFAZ DE USUARIO (UI)
# ----------------------------------------
def main():
    st.title("🍕 Domino's AnyWare - Sistema Central (Cloud)")
    st.markdown("Arquitectura basada en Microservicios y Base de Datos NoSQL")
    
    # Separación clara de los entornos
    tab_cocina, tab_cliente = st.tabs(["👨‍🍳 Panel Operativo (Franquicia)", "📱 App Cliente (Pizza Tracker)"])

    # ==========================================
    # VISTA COCINA (DASHBOARD)
    # ==========================================
    with tab_cocina:
        st.subheader("Dashboard de Operaciones")
        
        # Panel de Métricas (Arriba)
        total, en_proceso, entregados = obtener_metricas()
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total Pedidos Históricos", total)
        col_m2.metric("Pedidos en Proceso 🔥", en_proceso, delta="-1 si se entrega", delta_color="inverse")
        col_m3.metric("Pedidos Entregados ✅", entregados)
        
        st.divider()
        
        # Panel de Control dividido en dos columnas
        col_izq, col_der = st.columns([1, 2])
        
        # Columna Izquierda: Ingreso de Nuevos Pedidos
        with col_izq:
            st.markdown("### 📝 Nuevo Pedido")
            with st.form("form_nuevo_pedido"):
                nuevo_id = st.text_input("ID del Pedido (Ej: ORD-001)")
                cliente_nombre = st.text_input("Nombre del Cliente")
                tipo_pizza = st.selectbox("Tipo de Pizza", ["Pepperoni", "Margarita", "Hawaiana", "Meat Lovers", "Vegetariana"])
                
                submitted = st.form_submit_button("Registrar en Nube", use_container_width=True)
                
                if submitted and nuevo_id and cliente_nombre:
                    if collection is not None:
                        nuevo_doc = {
                            "_id": nuevo_id,
                            "cliente": cliente_nombre,
                            "pizza": tipo_pizza,
                            "estado": "Recibido",
                            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        collection.insert_one(nuevo_doc)
                        st.success("Pedido registrado exitosamente.")
                        st.rerun() # Recarga la app para actualizar métricas
                    
        # Columna Derecha: Gestión de Estados
        with col_der:
            st.markdown("### ⚙️ Gestión de Estados en Tiempo Real")
            pedidos_activos = obtener_pedidos_activos()
            
            if pedidos_activos:
                # Convertimos a DataFrame para mostrarlo como una tabla bonita
                df_pedidos = pd.DataFrame(pedidos_activos)
                st.dataframe(df_pedidos, use_container_width=True, hide_index=True)
                
                st.markdown("**Actualizar estado de un pedido activo:**")
                col_up1, col_up2, col_up3 = st.columns([1, 1, 1])
                
                with col_up1:
                    id_a_actualizar = st.selectbox("Seleccionar ID", [p["_id"] for p in pedidos_activos])
                with col_up2:
                    nuevo_estado = st.selectbox("Nuevo Estado", ["Preparando", "Horneando", "En Camino", "Entregado"])
                with col_up3:
                    st.write("") # Espaciador
                    st.write("") # Espaciador
                    if st.button("Actualizar", type="primary", use_container_width=True):
                        collection.update_one({"_id": id_a_actualizar}, {"$set": {"estado": nuevo_estado}})
                        st.toast(f"Pedido {id_a_actualizar} actualizado a {nuevo_estado}")
                        st.rerun()
            else:
                st.info("No hay pedidos en proceso actualmente.")

    # ==========================================
    # VISTA CLIENTE (TRACKER)
    # ==========================================
    with tab_cliente:
        # Usamos columnas para centrar el buscador
        _, col_centro, _ = st.columns([1, 2, 1])
        
        with col_centro:
            st.markdown("<h2 style='text-align: center;'>Sigue tu Pizza 🍕</h2>", unsafe_allow_html=True)
            pedido_id_cliente = st.text_input("Ingresa tu ID de pedido (Ej: ORD-001)", key="search_cliente")
            
            if st.button("Consultar Mi Pedido", use_container_width=True):
                if collection is not None:
                    pedido = collection.find_one({"_id": pedido_id_cliente})
                    
                    if pedido:
                        estado_actual = pedido.get("estado", "Recibido")
                        cliente = pedido.get("cliente", "Cliente")
                        pizza = pedido.get("pizza", "Pizza")
                        
                        st.success(f"Hola **{cliente}**, tu **{pizza}** está: **{estado_actual.upper()}**")
                        
                        estados = ["Recibido", "Preparando", "Horneando", "En Camino", "Entregado"]
                        progreso = estados.index(estado_actual) * 25
                        st.progress(progreso)
                        
                        # Simulación de entrega en la vida real (Por Santa Anita / Lima Este)
                        if estado_actual == "En Camino":
                            st.info("📍 Repartidor en ruta. Tiempo estimado: 15 min.")
                            data_mapa = pd.DataFrame({
                                'lat': [-12.043, -12.045], 
                                'lon': [-76.972, -76.975]
                            })
                            st.map(data_mapa, zoom=14, color="#FF0000")
                            
                        elif estado_actual == "Entregado":
                            st.balloons()
                            st.success("¡Disfruta tu pizza!")
                    else:
                        st.error("No encontramos ese pedido. Verifica el ID.")

if __name__ == "__main__":
    main()
