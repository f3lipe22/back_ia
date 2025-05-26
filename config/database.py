"""
Módulo para manejar la conexión a la base de datos MongoDB.
Este módulo se encarga de cargar las variables de entorno,
establecer la conexión a MongoDB y configurar GridFS.
"""

from pymongo import MongoClient
import gridfs
import os
from dotenv import load_dotenv
import sys

# Cargar variables de entorno desde el archivo .env
load_dotenv()

def get_database_connection():
    """
    Establece la conexión a la base de datos MongoDB utilizando
    las variables de entorno del archivo .env.
    
    Returns:
        tuple: (client, db, fs) donde:
            - client: Instancia de MongoClient
            - db: Base de datos MongoDB
            - fs: Instancia de GridFS para manejar archivos
    """
    # Obtener variables de entorno
    database_url = os.getenv("DATABASE_URL")
    database_name = os.getenv("MONGODB_DB")
    
    # Verificar que las variables de entorno se cargaron correctamente
    if not database_url:
        print("Error: La variable de entorno DATABASE_URL no está configurada en el archivo .env")
        sys.exit(1)
    if not database_name:
        print("Error: La variable de entorno MONGODB_DB no está configurada en el archivo .env")
        sys.exit(1)
    
    try:
        # Establecer conexión a MongoDB
        print(f"Conectando a la base de datos: {database_url}, DB: {database_name}")
        client = MongoClient(database_url)
        
        # Verificar la conexión
        client.admin.command('ping')
        print("Conexión a MongoDB establecida correctamente")
        
        # Obtener la base de datos
        db = client[database_name]
        
        # Configurar GridFS
        fs = gridfs.GridFS(db)
        
        return client, db, fs
    
    except Exception as e:
        print(f"Error al conectar a la base de datos: {str(e)}")
        sys.exit(1)

# Función para cerrar la conexión a la base de datos
def close_connection(client):
    """
    Cierra la conexión a la base de datos MongoDB.
    
    Args:
        client: Instancia de MongoClient a cerrar
    """
    if client:
        client.close()
        print("Conexión a MongoDB cerrada correctamente")
