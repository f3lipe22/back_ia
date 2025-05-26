"""
Definición de rutas para la API.
"""

def register_routes(app, image_controller, mqtt_controller=None):
    """
    Registra las rutas de la API en la aplicación Flask.

    Args:
        app: Instancia de la aplicación Flask
        image_controller: Controlador de imágenes
        mqtt_controller: Controlador de MQTT (opcional)
    """

    # Endpoint de prueba para verificar que la API está funcionando
    @app.route('/api/test', methods=['GET'])
    def test_api():
        # Obtener información de la base de datos
        db_name = image_controller.image_model.db.name
        connection_info = app.config.get('CONNECTION_INFO', 'No disponible')

        return {
            "status": "success",
            "message": "API funcionando correctamente",
            "database": db_name,
            "connection": connection_info
        }, 200

    # ==================== RUTAS PARA IMÁGENES ====================

    # Subir imagen + datos asociados (JSON)
    @app.route('/api/upload', methods=['POST'])
    def upload():
        return image_controller.upload_image()

    # Obtener imagen por ID
    @app.route('/api/image/<file_id>', methods=['GET'])
    def get_image(file_id):
        return image_controller.get_image(file_id)

    # Listar todas las imágenes y sus metadatos
    @app.route('/api/images', methods=['GET'])
    def list_images():
        return image_controller.list_images()

    # Eliminar una imagen por ID
    @app.route('/api/image/<file_id>', methods=['DELETE'])
    def delete_image(file_id):
        return image_controller.delete_image(file_id)

    # ==================== RUTAS PARA MQTT ====================

    # Registrar rutas de MQTT solo si el controlador está disponible
    if mqtt_controller:
        # Recibir mensaje MQTT
        @app.route('/api/mensaje', methods=['POST'])
        def receive_mqtt_message():
            return mqtt_controller.receive_message()

        # Obtener mensajes MQTT
        @app.route('/api/mensajes', methods=['GET'])
        def get_mqtt_messages():
            return mqtt_controller.get_messages()

        # Obtener predicciones
        @app.route('/api/predicciones', methods=['GET'])
        def get_predictions():
            return mqtt_controller.get_predictions()

        # Procesar datos de temperatura manualmente
        @app.route('/api/procesar-temperaturas', methods=['POST'])
        def process_temperatures_manually():
            return mqtt_controller.process_temperatures_manually()

        # Obtener estado del sistema MQTT
        @app.route('/api/mqtt/status', methods=['GET'])
        def get_mqtt_status():
            return mqtt_controller.get_mqtt_status()
        
        # Endpoint de prueba para enviar temperatura
        @app.route('/api/test/temperatura', methods=['POST'])
        def test_temperature():
            return mqtt_controller.test_temperature()

