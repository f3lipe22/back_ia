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
    
    def __init__(self, broker_host="192.168.196.202", broker_port=1883, client_id="backend_publisher"):
        """
        Inicializa el cliente MQTT.
        
        Args:
            broker_host: Dirección IP del broker MQTT
            broker_port: Puerto del broker MQTT
            client_id: Identificador del cliente
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.client = mqtt.Client(client_id=client_id)
        self.connected = False
        
        # Configurar callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        
        # Iniciar conexión en un hilo separado
        self._start_connection_thread()
        
        logger.info(f"Cliente MQTT inicializado para {broker_host}:{broker_port}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback que se ejecuta cuando el cliente se conecta al broker.
        """
        if rc == 0:
            self.connected = True
            logger.info(f"Conectado al broker MQTT en {self.broker_host}:{self.broker_port}")
        else:
            self.connected = False
            logger.error(f"Error al conectar al broker MQTT: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """
        Callback que se ejecuta cuando el cliente se desconecta del broker.
        """
        self.connected = False
        logger.warning(f"Desconectado del broker MQTT: {rc}")
        
        # Intentar reconectar
        if rc != 0:
            logger.info("Intentando reconectar...")
            self._start_connection_thread()
    
    def _connect(self):
        """
        Intenta conectar al broker MQTT.
        """
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Error al conectar al broker MQTT: {e}")
            time.sleep(5)  # Esperar antes de reintentar
            self._connect()
    
    def _start_connection_thread(self):
        """
        Inicia un hilo para conectar al broker MQTT.
        """
        thread = threading.Thread(target=self._connect)
        thread.daemon = True
        thread.start()
    
    def publish(self, topic, message, qos=1, retain=False):
        """
        Publica un mensaje en el broker MQTT.
        
        Args:
            topic: Tema donde publicar el mensaje
            message: Mensaje a publicar (puede ser un diccionario que se convertirá a JSON)
            qos: Calidad de servicio (0, 1 o 2)
            retain: Si el mensaje debe ser retenido por el broker
        
        Returns:
            bool: True si el mensaje se publicó correctamente, False en caso contrario
        """
        try:
            # Si no está conectado, intentar reconectar
            if not self.connected:
                logger.warning("No conectado al broker MQTT, intentando reconectar...")
                self._connect()
                time.sleep(1)  # Dar tiempo para conectar
            
            # Asegurar que el mensaje tenga un formato adecuado para dispositivos móviles
            if isinstance(message, dict):
                # Asegurar que el mensaje tenga un timestamp si no lo tiene
                if "timestamp" not in message:
                    message["timestamp"] = datetime.datetime.now().isoformat()
                
                # Asegurar que el mensaje tenga un campo de notificación si no lo tiene
                if "notification" not in message and "type" in message:
                    if message["type"] == "temperature_prediction":
                        message["notification"] = {
                            "title": "Actualización de temperatura",
                            "body": "Nueva predicción de temperatura disponible",
                            "priority": "normal"
                        }
                    elif message["type"] == "person_detection":
                        message["notification"] = {
                            "title": "Detección de personas",
                            "body": "Se han detectado personas en el invernadero",
                            "priority": "high"
                        }
            
            # Convertir a JSON
            message = json.dumps(message)
        
            # Publicar mensaje con QoS 1 por defecto para garantizar la entrega
            result = self.client.publish(topic, message, qos, retain)
            
            # Verificar resultado
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Mensaje publicado en {topic}")
                return True
            else:
                logger.error(f"Error al publicar mensaje en {topic}: {result.rc}")
                return False
        
        except Exception as e:
            logger.error(f"Error al publicar mensaje: {e}")
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
