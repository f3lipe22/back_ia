"""
Aplicación principal para el almacenamiento de imágenes con MongoDB GridFS.
Implementa el patrón Modelo-Vista-Controlador (MVC).
"""

from flask import Flask
from flask_cors import CORS
import atexit

# Importar configuración
from config.database import get_database_connection, close_connection

# Importar utilidades
from utils.mime_types import configure_mime_types

# Importar modelo
from models.image_model import ImageModel

# Importar controladores
from controllers.image_controller import ImageController
from controllers.mqtt_controller import MQTTController

# Importar vistas
from views.routes import register_routes

def create_app():
    """
    Crea y configura la aplicación Flask.

    Returns:
        app: Instancia de la aplicación Flask configurada
    """
    # Crear la aplicación Flask
    app = Flask(__name__)

    # Habilitar CORS para todas las rutas
    CORS(app)

    # Configurar tipos MIME adicionales
    configure_mime_types()

    # Establecer conexión a la base de datos
    client, db, fs = get_database_connection()

    # Registrar función para cerrar la conexión al finalizar la aplicación
    atexit.register(close_connection, client)

    # Guardar información de conexión en la configuración de la aplicación
    connection_info = f"{client.address[0]}:{client.address[1]}"
    app.config['CONNECTION_INFO'] = connection_info

    # Crear instancia del modelo
    image_model = ImageModel(db, fs)

    # Crear instancias de los controladores
    image_controller = ImageController(image_model)
    mqtt_controller = MQTTController(db)

    # Registrar rutas
    register_routes(app, image_controller, mqtt_controller)

    return app

# Crear la aplicación
app = create_app()

if __name__ == '__main__':
    # Ejecutar la aplicación
    app.run(host="0.0.0.0", port=5000, debug=True)
