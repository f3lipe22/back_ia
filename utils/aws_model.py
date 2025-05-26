"""
Utilidad para comunicarse con el modelo desplegado en AWS.
"""

import requests
import logging
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("aws_model")

class AWSModel:
    """
    Clase para comunicarse con el modelo desplegado en AWS.
    """
    
    def __init__(self, api_url=None, api_key=None):
        """
        Inicializa la clase con la URL y la clave de la API.
        
        Args:
            api_url: URL de la API de AWS (opcional)
            api_key: Clave de la API de AWS (opcional)
        """
        self.api_url = api_url or "https://smhdxgp506.execute-api.us-east-1.amazonaws.com/prod"
        self.api_key = api_key or "JpFbj5x3uXaVVVP6XJwlz7WzLbbf54Do206KJ8bw"
        
        logger.info(f"AWSModel inicializado con URL: {self.api_url}")
    
    def predict(self, temperatures):
        """
        Envía los datos de temperatura al modelo y obtiene la predicción.
        
        Args:
            temperatures: Lista de 60 valores de temperatura
            
        Returns:
            dict: Respuesta del modelo con la predicción
        """
        try:
            # Validar que hay exactamente 60 valores
            if len(temperatures) != 60:
                raise ValueError(f"Se requieren exactamente 60 valores de temperatura, se proporcionaron {len(temperatures)}")
            
            # Preparar los datos para enviar al modelo
            data = {
                "temperaturas": temperatures
            }
            
            # Preparar los headers
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Enviar la solicitud al modelo
            logger.info(f"Enviando solicitud al modelo con {len(temperatures)} valores de temperatura")
            response = requests.post(self.api_url, json=data, headers=headers)
            
            # Verificar si la solicitud fue exitosa
            response.raise_for_status()
            
            # Obtener la respuesta
            result = response.json()
            
            # Verificar si la respuesta contiene la predicción
            if "body" in result and "prediccion" in result["body"]:
                prediction = result["body"]["prediccion"]
                logger.info(f"Predicción recibida: {prediction}")
                return {
                    "status": "success",
                    "prediction": prediction,
                    "raw_response": result
                }
            else:
                logger.error(f"La respuesta no contiene la predicción esperada: {result}")
                return {
                    "status": "error",
                    "message": "La respuesta no contiene la predicción esperada",
                    "raw_response": result
                }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al comunicarse con el modelo: {str(e)}")
            return {
                "status": "error",
                "message": f"Error al comunicarse con el modelo: {str(e)}"
            }
        except ValueError as e:
            logger.error(str(e))
            return {
                "status": "error",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return {
                "status": "error",
                "message": f"Error inesperado: {str(e)}"
            }
