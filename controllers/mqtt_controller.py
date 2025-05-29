"""
Controlador para manejar los mensajes recibidos del cliente MQTT.
"""

from flask import request, jsonify
import datetime
import logging
from utils.aws_model import AWSModel
import threading

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mqtt_controller")

class MQTTController:
    """
    Controlador para manejar los mensajes recibidos del cliente MQTT.
    """

    def __init__(self, db, api_url=None, api_key=None, mqtt_client=None):
        """
        Inicializa el controlador con la base de datos y la conexión al modelo AWS.

        Args:
            db: Instancia de la base de datos MongoDB
            api_url: URL de la API de AWS (opcional)
            api_key: Clave de la API de AWS (opcional)
            mqtt_client: Cliente MQTT para enviar alertas (opcional)
        """
        self.db = db
        # Crear colección para los mensajes MQTT si no existe
        if "mqtt_messages" not in self.db.list_collection_names():
            self.db.create_collection("mqtt_messages")

        # Crear colección para las predicciones si no existe
        if "predicciones" not in self.db.list_collection_names():
            self.db.create_collection("predicciones")

        # Inicializar el modelo de AWS
        self.aws_model = AWSModel(api_url, api_key)
        
        # Cliente MQTT para enviar alertas
        self.mqtt_client = mqtt_client

        logger.info("Controlador MQTT inicializado")

    def receive_message(self):
        """
        Maneja la solicitud para recibir un mensaje MQTT a través del endpoint HTTP.

        Returns:
            tuple: (response, status_code)
        """
        try:
            # Obtener datos de la solicitud
            data = request.get_json()

            if not data:
                return jsonify({
                    "status": "error",
                    "message": "No se proporcionaron datos"
                }), 400

            # Validar datos
            if "topic" not in data or "valor" not in data:
                return jsonify({
                    "status": "error",
                    "message": "Se requieren los campos 'topic' y 'valor'"
                }), 400

            # Crear documento para guardar en la base de datos
            document = {
                "topic": data["topic"],
                "valor": data["valor"],
                "timestamp": datetime.datetime.now(datetime.timezone.utc),
                "source": "http_endpoint"
            }

            # Si el topic es sensor/temperatura, procesar el valor
            if data["topic"] == "sensor/temperatura":
                try:
                    # El valor puede ser una cadena o un número
                    if isinstance(data["valor"], str):
                        temperatura = float(data["valor"])
                    else:
                        temperatura = float(data["valor"])
                    
                    # Obtener fecha y hora actual
                    now = datetime.datetime.now()
                    current_date = now.strftime("%Y-%m-%d")
                    current_time = now.strftime("%H:%M:%S")
                    
                    # Crear el nuevo formato de mensaje
                    transformed_message = {
                        "sensor": "sensor",
                        "date": current_date,
                        "time": current_time,
                        "location": "ia",
                        "value": str(temperatura),
                        "isNew": "true"
                    }
                    
                    # Guardar el mensaje transformado en el documento
                    document["valor_original"] = data["valor"]
                    document["valor_transformado"] = transformed_message
                    document["valor"] = temperatura
                    
                    # Enviar el mensaje transformado al tópico sistema/notificaciones
                    if self.mqtt_client:
                        self.mqtt_client.publish(
                            topic="sistema/notificaciones",
                            message=transformed_message
                        )
                        logger.info(f"Mensaje transformado enviado a sistema/notificaciones: {transformed_message}")
                    
                except ValueError as e:
                    logger.warning(f"Error al procesar el valor de temperatura: {str(e)}")
                    document["error_procesamiento"] = str(e)

            # Guardar en la base de datos
            result = self.db.mqtt_messages.insert_one(document)

            # Registrar en el log
            logger.info(f"Mensaje MQTT recibido y guardado: {data['topic']} -> {data['valor']}")
            
            # Verificar si hay suficientes datos de temperatura para procesar
            if data["topic"] == "sensor/temperatura":
                self._check_and_process_temperatures()

            return jsonify({
                "status": "success",
                "message": "Mensaje recibido y guardado correctamente",
                "document_id": str(result.inserted_id)
            }), 201

        except Exception as e:
            logger.error(f"Error al procesar mensaje MQTT: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Error al procesar mensaje: {str(e)}"
            }), 500

    def get_messages(self):
        """
        Maneja la solicitud para obtener los mensajes MQTT.

        Returns:
            tuple: (response, status_code)
        """
        try:
            # Obtener parámetros de consulta
            limit = int(request.args.get('limit', 10))
            skip = int(request.args.get('skip', 0))
            topic = request.args.get('topic', None)

            # Validar parámetros
            if limit < 1 or limit > 100:
                limit = 10
            if skip < 0:
                skip = 0

            # Crear filtro
            filter_query = {}
            if topic:
                filter_query["topic"] = topic

            # Obtener mensajes
            cursor = self.db.mqtt_messages.find(filter_query).sort("timestamp", -1).skip(skip).limit(limit)
            total = self.db.mqtt_messages.count_documents(filter_query)

            # Convertir cursor a lista
            messages = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                doc["timestamp"] = doc["timestamp"].isoformat() if hasattr(doc["timestamp"], "isoformat") else str(doc["timestamp"])
                messages.append(doc)

            return jsonify({
                "status": "success",
                "total": total,
                "limit": limit,
                "skip": skip,
                "data": messages
            }), 200

        except Exception as e:
            logger.error(f"Error al obtener mensajes MQTT: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Error al obtener mensajes: {str(e)}"
            }), 500

    def _check_and_process_temperatures(self):
        """
        Verifica si hay 60 datos de temperatura no procesados y los envía al modelo AWS.
        """
        try:
            # Contar cuántos datos de temperatura no procesados hay
            count = self.db.mqtt_messages.count_documents({
                "topic": "sensor/temperatura",
                "processed": False
            })

            logger.info(f"Datos de temperatura no procesados: {count}")

            # Si hay al menos 60 datos, procesarlos
            if count >= 60:
                logger.info("Se han acumulado 60 datos de temperatura, enviando al modelo AWS...")
                self._process_temperatures()

        except Exception as e:
            logger.error(f"Error al verificar datos de temperatura: {str(e)}")

    def _process_temperatures(self):
        """
        Procesa los datos de temperatura y los envía al modelo AWS.
        """
        try:
            # Obtener los 60 datos de temperatura más antiguos no procesados
            cursor = self.db.mqtt_messages.find({
                "topic": "sensor/temperatura",
                "processed": False
            }).sort("timestamp", 1).limit(60)

            # Convertir cursor a lista
            temperature_docs = list(cursor)

            # Verificar si hay suficientes datos
            if len(temperature_docs) < 60:
                logger.warning(f"No hay suficientes datos de temperatura para procesar: {len(temperature_docs)}/60")
                return

            # Extraer los valores de temperatura
            temperatures = [doc["valor"] for doc in temperature_docs]

            # Guardar los IDs de los documentos para marcarlos como procesados después
            doc_ids = [doc["_id"] for doc in temperature_docs]

            # Enviar los datos al modelo AWS
            logger.info(f"Enviando {len(temperatures)} valores de temperatura al modelo AWS")
            result = self.aws_model.predict(temperatures)

            # Guardar la predicción en la base de datos
            prediction_doc = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc),
                "temperatures": temperatures,
                "result": result,
                "temperature_doc_ids": [str(doc_id) for doc_id in doc_ids]
            }

            self.db.predicciones.insert_one(prediction_doc)

            # Marcar los datos como procesados
            for doc_id in doc_ids:
                self.db.mqtt_messages.update_one(
                    {"_id": doc_id},
                    {"$set": {"processed": True}}
                )

            logger.info(f"Predicción completada y guardada: {result}")
            
            # Enviar alerta MQTT si hay un cliente MQTT disponible
            if self.mqtt_client and result.get("status") == "success":
                # Obtener la predicción de temperatura
                prediction_value = None
                if "prediction" in result and "prediccion" in result["prediction"]:
                    prediction_value = result["prediction"]["prediccion"]
                
                # Determinar el mensaje según el valor de temperatura
                temperature_status = "normal"
                temperature_message = "La temperatura del invernadero es normal"
                
                if prediction_value is not None:
                    try:
                        temp_value = float(prediction_value)
                        if temp_value < 20:
                            temperature_status = "baja"
                            temperature_message = "¡ALERTA! La temperatura del invernadero es BAJA"
                        elif temp_value > 37:
                            temperature_status = "alta"
                            temperature_message = "¡ALERTA! La temperatura del invernadero es ALTA"
                    except (ValueError, TypeError):
                        logger.warning(f"No se pudo convertir la predicción a número: {prediction_value}")
                
                # Crear mensaje para la notificación móvil
                alert_message = {
                    "type": "temperature_prediction",
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "temperature_value": prediction_value,
                    "temperature_status": temperature_status,
                    "message": temperature_message,
                    "notification": {
                        "title": f"Temperatura {temperature_status.upper()}",
                        "body": temperature_message,
                        "priority": "high" if temperature_status != "normal" else "normal"
                    }
                }
                
                self.mqtt_client.publish(
                    topic="alertas/temperatura",
                    message=alert_message
                )
                logger.info(f"Alerta de temperatura enviada por MQTT: {temperature_message}")

        except Exception as e:
            logger.error(f"Error al procesar datos de temperatura: {str(e)}")

    def get_predictions(self):
        """
        Maneja la solicitud para obtener las predicciones.

        Returns:
            tuple: (response, status_code)
        """
        try:
            # Obtener parámetros de consulta
            limit = int(request.args.get('limit', 10))
            skip = int(request.args.get('skip', 0))

            # Validar parámetros
            if limit < 1 or limit > 100:
                limit = 10
            if skip < 0:
                skip = 0

            # Obtener predicciones
            cursor = self.db.predicciones.find().sort("timestamp", -1).skip(skip).limit(limit)
            total = self.db.predicciones.count_documents({})

            # Convertir cursor a lista
            predictions = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                doc["timestamp"] = doc["timestamp"].isoformat() if hasattr(doc["timestamp"], "isoformat") else str(doc["timestamp"])
                predictions.append(doc)

            return jsonify({
                "status": "success",
                "total": total,
                "limit": limit,
                "skip": skip,
                "data": predictions
            }), 200

        except Exception as e:
            logger.error(f"Error al obtener predicciones: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Error al obtener predicciones: {str(e)}"
            }), 500

    def process_temperatures_manually(self):
        """
        Maneja la solicitud para procesar los datos de temperatura manualmente.

        Returns:
            tuple: (response, status_code)
        """
        try:
            # Contar cuántos datos de temperatura no procesados hay
            count = self.db.mqtt_messages.count_documents({
                "topic": "sensor/temperatura",
                "processed": False
            })

            if count < 60:
                return jsonify({
                    "status": "error",
                    "message": f"No hay suficientes datos de temperatura para procesar: {count}/60"
                }), 400

            # Procesar los datos
            self._process_temperatures()

            return jsonify({
                "status": "success",
                "message": "Datos de temperatura procesados correctamente"
            }), 200

        except Exception as e:
            logger.error(f"Error al procesar datos de temperatura manualmente: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Error al procesar datos de temperatura: {str(e)}"
            }), 500

    def get_mqtt_status(self):
        """
        Obtiene el estado del sistema MQTT.

        Returns:
            tuple: (response, status_code)
        """
        try:
            # Contar mensajes recibidos en las últimas 24 horas
            from datetime import datetime, timedelta

            last_24h = datetime.now(datetime.timezone.utc) - timedelta(hours=24)

            recent_messages = self.db.mqtt_messages.count_documents({
                "timestamp": {"$gte": last_24h}
            })

            # Contar mensajes de temperatura no procesados
            unprocessed_temp = self.db.mqtt_messages.count_documents({
                "topic": "sensor/temperatura",
                "processed": False
            })

            # Obtener el último mensaje recibido
            last_message = self.db.mqtt_messages.find().sort("timestamp", -1).limit(1)
            last_message_data = None
            for msg in last_message:
                last_message_data = {
                    "topic": msg["topic"],
                    "valor": msg["valor"],
                    "timestamp": msg["timestamp"].isoformat() if hasattr(msg["timestamp"], "isoformat") else str(msg["timestamp"])
                }
                break

            # Contar predicciones
            total_predictions = self.db.predicciones.count_documents({})

            return jsonify({
                "status": "success",
                "mqtt_system": {
                    "backend_endpoint": "/api/mensaje",
                    "external_subscriber": {
                        "expected_broker": "192.168.196.202:1883",
                        "expected_topic": "sensor/temperatura",
                        "note": "El backend recibe datos del subscriber externo vía HTTP"
                    },
                    "statistics": {
                        "messages_last_24h": recent_messages,
                        "unprocessed_temperatures": unprocessed_temp,
                        "total_predictions": total_predictions,
                        "last_message": last_message_data
                    }
                }
            }), 200

        except Exception as e:
            logger.error(f"Error al obtener estado MQTT: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Error al obtener estado MQTT: {str(e)}"
            }), 500

    def test_temperature(self):
        """
        Maneja la solicitud para probar el envío de una temperatura.
        
        Returns:
            tuple: (response, status_code)
        """
        try:
            # Obtener datos de la solicitud
            data = request.get_json()
            
            if not data:
                return jsonify({
                    "status": "error",
                    "message": "No se proporcionaron datos"
                }), 400
            
            # Validar datos
            if "valor" not in data:
                return jsonify({
                    "status": "error",
                    "message": "Se requiere el campo 'valor'"
                }), 400
            
            # Intentar convertir el valor a float
            try:
                temperatura = float(data["valor"])
            except ValueError:
                return jsonify({
                    "status": "error",
                    "message": f"El valor '{data['valor']}' no es un número válido"
                }), 400
            
            # Obtener fecha y hora actual
            now = datetime.datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M:%S")
            
            # Crear el mensaje transformado
            transformed_message = {
                "sensor": "sensor",
                "date": current_date,
                "time": current_time,
                "location": "ia",
                "value": str(temperatura),
                "isNew": "true"
            }
            
            # Crear documento para guardar en la base de datos
            document = {
                "topic": "sensor/temperatura",
                "valor": temperatura,
                "valor_original": str(temperatura),
                "valor_transformado": transformed_message,
                "timestamp": datetime.datetime.now(datetime.timezone.utc),
                "source": "test_endpoint"
            }
            
            # Guardar en la base de datos
            result = self.db.mqtt_messages.insert_one(document)
            
            # Enviar el mensaje transformado al tópico sistema/notificaciones
            if self.mqtt_client:
                self.mqtt_client.publish(
                    topic="sistema/notificaciones",
                    message=transformed_message
                )
                logger.info(f"Mensaje transformado enviado a sistema/notificaciones: {transformed_message}")
            
            # Registrar en el log
            logger.info(f"Temperatura de prueba recibida y guardada: {temperatura}")
            
            return jsonify({
                "status": "success",
                "message": "Temperatura guardada y transformada correctamente",
                "document_id": str(result.inserted_id),
                "temperatura_original": temperatura,
                "mensaje_transformado": transformed_message
            }), 201
            
        except Exception as e:
            logger.error(f"Error al procesar temperatura de prueba: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Error al procesar temperatura: {str(e)}"
            }), 500

    def test_intrusion(self):
        """
        Maneja la solicitud para probar la detección de intrusos.
        
        Returns:
            tuple: (response, status_code)
        """
        try:
            # Obtener datos de la solicitud
            data = request.get_json()
            
            if not data:
                return jsonify({
                    "status": "error",
                    "message": "No se proporcionaron datos"
                }), 400
            
            # Validar datos
            if "total_persons" not in data:
                # Usar valor predeterminado si no se proporciona
                total_persons = 1
            else:
                try:
                    total_persons = int(data["total_persons"])
                    if total_persons <= 0:
                        return jsonify({
                            "status": "error",
                            "message": "El número de personas debe ser mayor que 0"
                        }), 400
                except ValueError:
                    return jsonify({
                        "status": "error",
                        "message": f"El valor '{data['total_persons']}' no es un número válido"
                    }), 400
            
            # Obtener fecha y hora actual
            now = datetime.datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M:%S")
            
            # Crear mensaje para la notificación
            persons_text = "persona" if total_persons == 1 else "personas"
            notification_message = f"Se detectaron {total_persons} {persons_text} en el invernadero"
            
            # Crear el mensaje en el formato requerido para sistema/notificaciones
            transformed_message = {
                "sensor": "camara",
                "date": current_date,
                "time": current_time,
                "location": "invernadero",
                "value": notification_message,
                "isNew": "true",
                "type": "intrusion",
                "total_persons": total_persons,
                "image_id": "test_image_id",
                "confidence": data.get("confidence", 0.95)  # Usar valor predeterminado si no se proporciona
            }
            
            # Enviar al tópico sistema/notificaciones
            if self.mqtt_client:
                self.mqtt_client.publish(
                    topic="sistema/notificaciones",
                    message=transformed_message
                )
                logger.info(f"Alerta de prueba de intrusión enviada a sistema/notificaciones: {notification_message}")
            
            # Crear documento para guardar en la base de datos (opcional)
            document = {
                "topic": "sistema/notificaciones",
                "valor": transformed_message,
                "timestamp": datetime.datetime.now(datetime.timezone.utc),
                "source": "test_intrusion_endpoint"
            }
            
            # Guardar en la base de datos
            result = self.db.mqtt_messages.insert_one(document)
            
            return jsonify({
                "status": "success",
                "message": "Alerta de intrusión enviada correctamente",
                "document_id": str(result.inserted_id),
                "notification_message": notification_message,
                "transformed_message": transformed_message
            }), 201
            
        except Exception as e:
            logger.error(f"Error al procesar prueba de intrusión: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Error al procesar prueba de intrusión: {str(e)}"
            }), 500


