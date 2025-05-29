"""
Cliente MQTT para enviar mensajes al broker Mosquitto.
"""

import paho.mqtt.client as mqtt
import json
import logging
import time
import threading
import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mqtt_client")

class MQTTClient:
    """
    Cliente MQTT para enviar mensajes al broker Mosquitto.
    """
    
    def __init__(self, broker_host="192.168.45.221", broker_port=1883, client_id="backend_publisher", use_websockets=False):
        """
        Inicializa el cliente MQTT.
        
        Args:
            broker_host: Dirección IP del broker MQTT
            broker_port: Puerto del broker MQTT
            client_id: Identificador del cliente
            use_websockets: Si se debe usar WebSockets para la conexión
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.use_websockets = use_websockets
        
        # Crear cliente MQTT con o sin WebSockets
        if use_websockets:
            self.client = mqtt.Client(client_id=client_id, transport="websockets")
            logger.info(f"Cliente MQTT configurado para usar WebSockets en {broker_host}:{broker_port}")
        else:
            self.client = mqtt.Client(client_id=client_id)
            logger.info(f"Cliente MQTT configurado para usar TCP en {broker_host}:{broker_port}")
            
        self.connected = False
        
        # Configurar callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        
        # Iniciar conexión en un hilo separado
        self._start_connection_thread()
    
    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback que se ejecuta cuando el cliente se conecta al broker.
        """
        if rc == 0:
            self.connected = True
            logger.info(f"✅ Conectado al broker MQTT en {self.broker_host}:{self.broker_port}")
        else:
            self.connected = False
            error_messages = {
                1: "Protocolo incorrecto",
                2: "ID de cliente rechazado",
                3: "Servidor no disponible",
                4: "Usuario/contraseña incorrectos",
                5: "No autorizado"
            }
            error_msg = error_messages.get(rc, f"Error desconocido: {rc}")
            logger.error(f"❌ Error al conectar al broker MQTT: {error_msg}")
    
    def _on_disconnect(self, client, userdata, flags, rc):
        """
        Callback que se ejecuta cuando el cliente se desconecta del broker.
        """
        self.connected = False
        if rc == 0:
            logger.info("Desconexión normal del broker MQTT")
        else:
            logger.warning(f"⚠️ Desconectado inesperadamente del broker MQTT: {rc}")
            
            # Intentar reconectar
            logger.info("🔄 Intentando reconectar...")
            self._start_connection_thread()
    
    def _connect(self):
        """
        Intenta conectar al broker MQTT.
        """
        try:
            # Configurar opciones de WebSocket si es necesario
            if self.use_websockets:
                self.client.ws_set_options(path="/mqtt")
            
            # Intentar conectar
            logger.info(f"🔌 Intentando conectar a {self.broker_host}:{self.broker_port} {'(WebSockets)' if self.use_websockets else '(TCP)'}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
        except Exception as e:
            self.connected = False
            logger.error(f"⚠️ Error al conectar al broker MQTT: {e}")
            time.sleep(5)  # Esperar antes de reintentar
    
    def _start_connection_thread(self):
        """
        Inicia un hilo para conectar al broker MQTT.
        """
        thread = threading.Thread(target=self._connect)
        thread.daemon = True
        thread.start()
    
    def publish(self, topic, message):
        """
        Publica un mensaje en un tópico MQTT.
        
        Args:
            topic: Tópico MQTT
            message: Mensaje a publicar (puede ser un diccionario o una cadena)
        
        Returns:
            bool: True si el mensaje se publicó correctamente, False en caso contrario
        """
        # Si no está conectado, intentar reconectar
        if not self.connected:
            logger.warning("No conectado al broker MQTT. Intentando reconectar antes de publicar...")
            self._connect()
            time.sleep(2)  # Esperar un poco para que se establezca la conexión
            
            # Si sigue sin estar conectado, devolver False
            if not self.connected:
                logger.error("No se pudo conectar al broker MQTT. No se puede publicar el mensaje.")
                return False
        
        try:
            # Convertir el mensaje a JSON si es un diccionario
            if isinstance(message, dict):
                # Si el tópico es sistema/notificaciones, asegurarse de que tenga el formato correcto
                if topic == "sistema/notificaciones":
                    # Verificar que el mensaje tenga los campos requeridos
                    required_fields = ["sensor", "date", "time", "location", "value", "isNew"]
                    for field in required_fields:
                        if field not in message:
                            logger.warning(f"El mensaje para sistema/notificaciones no tiene el campo requerido: {field}")
                            # Añadir campos faltantes con valores predeterminados
                            if field == "sensor" and "sensor" not in message:
                                message["sensor"] = "camara"
                            elif field == "date" and "date" not in message:
                                message["date"] = datetime.datetime.now().strftime("%Y-%m-%d")
                            elif field == "time" and "time" not in message:
                                message["time"] = datetime.datetime.now().strftime("%H:%M:%S")
                            elif field == "location" and "location" not in message:
                                message["location"] = "invernadero"
                            elif field == "value" and "value" not in message:
                                message["value"] = "Alerta de detección"
                            elif field == "isNew" and "isNew" not in message:
                                message["isNew"] = "true"
            
                # Convertir a JSON
                message_json = json.dumps(message)
            else:
                message_json = message
        
            # Publicar el mensaje
            result = self.client.publish(topic, message_json)
            
            # Verificar si el mensaje se publicó correctamente
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"📤 Mensaje publicado en {topic}: {message_json}")
                return True
            else:
                logger.error(f"❌ Error al publicar mensaje en {topic}: {result.rc}")
                return False
    
        except Exception as e:
            logger.error(f"❌ Error al publicar mensaje MQTT: {str(e)}")
            return False
    
    def close(self):
        """
        Cierra la conexión con el broker MQTT.
        """
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Conexión MQTT cerrada")
        except Exception as e:
            logger.error(f"Error al cerrar conexión MQTT: {e}")



