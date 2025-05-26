"""
Utilidad para comunicarse con el modelo de detección de rostros en AWS.
"""

import requests
import logging
import json
import base64

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("aws_face_model")

class AWSFaceModel:
    """
    Clase para comunicarse con el modelo de detección de rostros en AWS.
    """
    
    def __init__(self, api_url=None, api_key=None):
        """
        Inicializa la clase con la URL y la clave de la API.
        
        Args:
            api_url: URL de la API de AWS (opcional)
            api_key: Clave de la API de AWS (opcional)
        """
        self.api_url = api_url or "https://npdvcvx4o8.execute-api.us-east-1.amazonaws.com/prodfaces"
        self.api_key = api_key
        
        logger.info(f"AWSFaceModel inicializado con URL: {self.api_url}")
    
    def detect_face(self, image_data):
        """
        Envía una imagen al modelo y obtiene la predicción de detección de rostros.
        
        Args:
            image_data: Datos binarios de la imagen
        
        Returns:
            dict: Respuesta del modelo con la predicción
        """
        try:
            # Convertir imagen a base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Preparar los datos para enviar al modelo
            data = {
                "body": {
                    "image": image_base64
                }
            }
            
            # Preparar los headers
            headers = {
                "Content-Type": "application/json"
            }
            
            # Añadir API key si está disponible
            if self.api_key:
                headers["x-api-key"] = self.api_key
            
            # Enviar la solicitud al modelo
            logger.info("Enviando imagen al modelo de detección de rostros")
            response = requests.post(self.api_url, json=data, headers=headers)
            
            # Verificar si la solicitud fue exitosa
            response.raise_for_status()
            
            # Obtener la respuesta
            result = response.json()
            logger.info(f"Respuesta recibida del modelo: {result}")
            
            # Procesar la respuesta para extraer información relevante
            processed_result = self._process_detection_result(result)
            
            return {
                "status": "success",
                "prediction": processed_result,
                "raw_response": result
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al comunicarse con el modelo: {str(e)}")
            return {
                "status": "error",
                "message": f"Error al comunicarse con el modelo: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return {
                "status": "error",
                "message": f"Error inesperado: {str(e)}"
            }

    def _process_detection_result(self, result):
        """
        Procesa el resultado de la detección para extraer información relevante.
        
        Args:
            result: Respuesta del modelo
        
        Returns:
            dict: Información procesada de la detección
        """
        processed = {
            "has_persons": False,
            "total_persons": 0,
            "persons": [],
            "image_size": None,
            "processing_time": None
        }
        
        # Verificar si la respuesta tiene el formato esperado
        if not isinstance(result, dict) or "statusCode" not in result:
            return processed
        
        # Verificar si la respuesta fue exitosa
        if result.get("statusCode") != 200 or "body" not in result:
            return processed
        
        # Extraer el cuerpo de la respuesta
        body = result["body"]
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                return processed
        
        # Extraer información de detecciones
        detections = body.get("detections", [])
        persons = [d for d in detections if d.get("class") == "person"]
        
        processed["has_persons"] = len(persons) > 0
        processed["total_persons"] = len(persons)
        processed["persons"] = persons
        processed["image_size"] = body.get("image_size")
        processed["processing_time"] = body.get("processing_time")
        
        return processed
