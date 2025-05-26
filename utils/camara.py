import requests
from datetime import datetime
import os
import time
import threading
import base64
import logging
from io import BytesIO

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("camara")

# Dirección IP de tu ESP32-CAM (ajusta según tu red)
ESP32_CAM_URL = "http://192.168.211.252/capture"

# Carpeta donde se guardarán las imágenes
SAVE_DIR = "capturas"
os.makedirs(SAVE_DIR, exist_ok=True)

def capture_image():
    """
    Captura una imagen de la cámara ESP32-CAM.
    
    Returns:
        tuple: (success, image_data, filename) donde:
            - success: True si la captura fue exitosa, False en caso contrario
            - image_data: Datos binarios de la imagen o None si hubo error
            - filename: Nombre del archivo generado o None si hubo error
    """
    try:
        response = requests.get(ESP32_CAM_URL)
        if response.status_code == 200:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"imagen_{timestamp}.jpg"
            filepath = os.path.join(SAVE_DIR, filename)
            
            # Guardar la imagen localmente
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            logger.info(f"[✓] Imagen guardada en {filepath}")
            return True, response.content, filename
        else:
            logger.error(f"[✗] Error al capturar imagen: Código {response.status_code}")
            return False, None, None
    except Exception as e:
        logger.error(f"[✗] Error de conexión: {e}")
        return False, None, None

def start_capture_thread(image_model=None, aws_face_model=None, mqtt_client=None, interval=20):
    """
    Inicia un hilo para capturar imágenes periódicamente.
    
    Args:
        image_model: Modelo para guardar imágenes en la base de datos (opcional)
        aws_face_model: Modelo para detectar rostros en AWS (opcional)
        mqtt_client: Cliente MQTT para enviar alertas (opcional)
        interval: Intervalo en segundos entre capturas (por defecto 20)
    """
    def capture_thread():
        logger.info(f"Iniciando captura automática cada {interval} segundos")
        while True:
            try:
                # Capturar imagen
                success, image_data, filename = capture_image()
                
                if success and image_data and image_model and aws_face_model:
                    # Guardar en la base de datos
                    file_obj = BytesIO(image_data)
                    file_obj.name = filename
                    
                    # Metadatos adicionales
                    metadata = {
                        "source": "ESP32-CAM",
                        "capture_time": datetime.now().isoformat()
                    }
                    
                    # Guardar en la base de datos
                    file_id, _ = image_model.save_image_from_bytes(file_obj, metadata)
                    logger.info(f"Imagen guardada en la base de datos con ID: {file_id}")
                    
                    # Enviar al modelo de AWS
                    result = aws_face_model.detect_face(image_data)
                    
                    # Extraer información relevante
                    detection_info = {
                        "face_detection_result": result,
                        "detection_time": datetime.now().isoformat()
                    }
                    
                    # Añadir información específica si la detección fue exitosa
                    if result["status"] == "success":
                        prediction = result["prediction"]
                        detection_info.update({
                            "has_persons": prediction["has_persons"],
                            "total_persons": prediction["total_persons"],
                            "processing_time": prediction["processing_time"]
                        })
                        
                        # Registrar información detallada si se detectaron personas
                        if prediction["has_persons"]:
                            logger.info(f"¡ALERTA! Se detectaron {prediction['total_persons']} personas en la imagen {filename}")
                            
                            # Añadir información de cada persona detectada
                            for i, person in enumerate(prediction["persons"]):
                                logger.info(f"  Persona {i+1}: Confianza {person.get('confidence', 0):.2f}, Bbox: {person.get('bbox')}")
                            
                            # Enviar alerta MQTT si hay un cliente MQTT disponible
                            if mqtt_client:
                                # Crear mensaje para la notificación móvil
                                persons_text = "persona" if prediction["total_persons"] == 1 else "personas"
                                notification_message = f"Se {prediction['total_persons']} {persons_text} en el invernadero"
                                
                                alert_message = {
                                    "type": "person_detection",
                                    "timestamp": datetime.now().isoformat(),
                                    "image_id": str(file_id),
                                    "filename": filename,
                                    "total_persons": prediction["total_persons"],
                                    "persons": prediction["persons"],
                                    "notification": {
                                        "title": "¡Personas detectadas!",
                                        "body": notification_message,
                                        "priority": "high"
                                    }
                                }
                                
                                mqtt_client.publish(
                                    topic="alertas/personas",
                                    message=alert_message
                                )
                                logger.info(f"Alerta de detección de personas enviada por MQTT: {notification_message}")
                        else:
                            logger.info(f"No se detectaron personas en la imagen {filename}")
                    
                    # Actualizar metadatos con el resultado
                    image_model.update_image_metadata(file_id, detection_info)
                    
                    logger.info(f"Metadatos de detección actualizados para la imagen {file_id}")
                
            except Exception as e:
                logger.error(f"Error en el hilo de captura: {e}")
            
            # Esperar para la siguiente captura
            time.sleep(interval)
    
    # Iniciar el hilo
    thread = threading.Thread(target=capture_thread, daemon=True)
    thread.start()
    return thread

# Ejemplo: capturar una imagen
if __name__ == "__main__":
    capture_image()
