import streamlit as st
import pandas as pd
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Configuración de página
st.set_page_config(page_title="Domino's Cloud Tracker", layout="centered")

# Cargar variables de entorno
load_dotenv()

# Conexión a MongoDB (Capa de Datos)
@st.cache_resource
def init_connection():
    try:
        client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
        client.admin.command('ping') # Validar conexión
        return client["s11-dominos"]["dominos"] # Base de datos: dominos_db, Colección: pedidos
    except Exception as e:
        st.error(f"Error conectando a Atlas: Revise su MONGO_URI. Detalle: {e}")
        return None

collection = init_connection()

# Lógica principal
def main():
    st.title("🍕 Domino's Pizza Tracker (Cloud MVP)")
    st.markdown("---")

    # Separar en dos pestañas para simular las dos aplicaciones (Microservicios)
    tab_cliente, tab_cocina = st.tabs(["📱 Vista Cliente", "👨‍🍳 Vista Cocina"])

    # ----------------------------------------
    # VISTA CLIENTE
    # ----------------------------------------
    with tab_cliente:
        st.subheader("Rastrea tu pedido en tiempo real")
        pedido_id = st.text_input("Ingresa el ID de tu pedido (Ej: 101)", "101")
        
        if st.button("Consultar Estado"):
            if collection is not None:
                pedido = collection.find_one({"_id": pedido_id})
                
                if pedido:
                    estado_actual = pedido.get("estado", "Recibido")
                    
                    # Lógica de la barra de progreso
                    estados = ["Recibido", "Preparando", "Horneando", "En Camino", "Entregado"]
                    progreso = estados.index(estado_actual) * 25
                    
                    st.progress(progreso)
                    st.success(f"**Estado actual:** {estado_actual}")
                    
                    # Simulación de Integración con Google APIs (Geolocalización)
                    if estado_actual == "En Camino":
                        st.info("📍 Conectando con Google Maps API para ubicación del repartidor...")
                        # Coordenadas estáticas simulando un repartidor en Lima (Santa Anita)
                        data_mapa = pd.DataFrame({'lat': [-12.043], 'lon': [-76.972]})
                        st.map(data_mapa, zoom=14)
                else:
                    st.warning("Pedido no encontrado. ¿Ya lo registraste en la cocina?")
            else:
                st.error("No hay conexión a la base de datos.")

    # ----------------------------------------
    # VISTA COCINA
    # ----------------------------------------
    with tab_cocina:
        st.subheader("Panel de Control de Franquicia")
        st.caption("Seguridad: Acceso restringido por IAM / Red Interna")
        
        nuevo_id = st.text_input("ID del Pedido a gestionar", "101", key="id_cocina")
        nuevo_estado = st.selectbox(
            "Actualizar estado a:", 
            ["Recibido", "Preparando", "Horneando", "En Camino", "Entregado"]
        )
        
        if st.button("Actualizar Base de Datos Cloud"):
            if collection is not None:
                # Upsert: Si el pedido no existe, lo crea. Si existe, lo actualiza.
                collection.update_one(
                    {"_id": nuevo_id},
                    {"$set": {"estado": nuevo_estado, "cliente": "Cliente MVP"}},
                    upsert=True
                )
                st.success(f"✅ Pedido {nuevo_id} actualizado a '{nuevo_estado}' en MongoDB Atlas.")
            else:
                st.error("No hay conexión a la base de datos.")

if __name__ == "__main__":
    main()
