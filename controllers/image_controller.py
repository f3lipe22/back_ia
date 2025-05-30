"""
Controlador para manejar las operaciones relacionadas con imágenes.
"""

from flask import request, jsonify, send_file
from io import BytesIO
import json

class ImageController:
    """
    Controlador para manejar las operaciones relacionadas con imágenes.
    """
    
    def __init__(self, image_model):
        """
        Inicializa el controlador con el modelo de imágenes.
        
        Args:
            image_model: Instancia del modelo de imágenes
        """
        self.image_model = image_model
    
    def upload_image(self):
        """
        Maneja la solicitud para subir una imagen.
        
        Returns:
            tuple: (response, status_code)
        """
        try:
            # Verificar si se envió una imagen
            if 'image' not in request.files:
                return jsonify({
                    "status": "error",
                    "message": "No se envió ninguna imagen",
                    "help": "Envía un archivo con el nombre 'image'"
                }), 400
            
            image = request.files['image']
            
            # Verificar si el archivo tiene nombre
            if image.filename == '':
                return jsonify({
                    "status": "error",
                    "message": "El archivo no tiene nombre"
                }), 400
            
            # Obtener metadatos adicionales si se proporcionaron
            additional_metadata = {}
            if 'metadata' in request.form:
                try:
                    additional_metadata = json.loads(request.form['metadata'])
                except json.JSONDecodeError:
                    return jsonify({
                        "status": "error",
                        "message": "El formato del JSON de metadatos es inválido"
                    }), 400
            
            # Guardar la imagen
            file_id, metadata = self.image_model.save_image(image, additional_metadata)
            
            return jsonify({
                "status": "success",
                "message": "Imagen almacenada exitosamente",
                "file_id": file_id,
                "filename": image.filename,
                "content_type": metadata.get("content_type"),
                "metadata": metadata
            }), 201
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error al guardar la imagen: {str(e)}"
            }), 500
    
    def get_image(self, file_id):
        """
        Maneja la solicitud para obtener una imagen por su ID.
        
        Args:
            file_id: ID del archivo a obtener
            
        Returns:
            tuple: (response, status_code)
        """
        try:
            # Obtener la imagen
            file, content_type = self.image_model.get_image(file_id)
            
            # Enviar el archivo
            return send_file(
                BytesIO(file.read()),
                mimetype=content_type,
                download_name=file.filename,
                as_attachment=False
            )
            
        except ValueError as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 400
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error al obtener la imagen: {str(e)}"
            }), 404
    
    def list_images(self):
        """
        Maneja la solicitud para listar todas las imágenes.
        
        Returns:
            tuple: (response, status_code)
        """
        try:
            # Obtener parámetros de paginación
            limit = int(request.args.get('limit', 10))
            skip = int(request.args.get('skip', 0))
            
            # Obtener la lista de imágenes
            total, images = self.image_model.list_images(limit, skip)
            
            return jsonify({
                "status": "success",
                "total": total,
                "limit": limit,
                "skip": skip,
                "data": images
            }), 200
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error al listar las imágenes: {str(e)}"
            }), 500
    
    def delete_image(self, file_id):
        """
        Maneja la solicitud para eliminar una imagen por su ID.
        
        Args:
            file_id: ID del archivo a eliminar
            
        Returns:
            tuple: (response, status_code)
        """
        try:
            # Eliminar la imagen
            self.image_model.delete_image(file_id)
            
            return jsonify({
                "status": "success",
                "message": "Imagen eliminada exitosamente",
                "file_id": file_id
            }), 200
            
        except ValueError as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 400
            
        except FileNotFoundError as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 404
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error al eliminar la imagen: {str(e)}"
            }), 500

    def get_person_detections(self):
        """
        Maneja la solicitud para obtener imágenes donde se detectaron personas.
        
        Returns:
            tuple: (response, status_code)
        """
        try:
            # Obtener parámetros de paginación
            limit = int(request.args.get('limit', 10))
            skip = int(request.args.get('skip', 0))
            min_confidence = float(request.args.get('min_confidence', 0.5))
            
            # Validar parámetros
            if limit < 1 or limit > 100:
                limit = 10
            if skip < 0:
                skip = 0
            if min_confidence < 0 or min_confidence > 1:
                min_confidence = 0.5
            
            # Crear filtro para buscar imágenes con personas detectadas
            filter_query = {
                "metadata.has_persons": True
            }
            
            # Obtener imágenes
            cursor = self.image_model.db.fs.files.find(filter_query).sort("uploadDate", -1).skip(skip).limit(limit)
            total = self.image_model.db.fs.files.count_documents(filter_query)
            
            # Procesar resultados
            detections = []
            for file in cursor:
                # Filtrar personas por confianza mínima
                persons = []
                if "metadata" in file and "face_detection_result" in file["metadata"]:
                    result = file["metadata"]["face_detection_result"]
                    if "prediction" in result and "persons" in result["prediction"]:
                        for person in result["prediction"]["persons"]:
                            if person.get("confidence", 0) >= min_confidence:
                                persons.append(person)
            
                # Solo incluir si hay personas que cumplan con la confianza mínima
                if persons:
                    detections.append({
                        "file_id": str(file["_id"]),
                        "filename": file["filename"],
                        "upload_date": file["uploadDate"].isoformat() if hasattr(file, "uploadDate") else None,
                        "total_persons": len(persons),
                        "persons": persons,
                        "image_url": f"/api/image/{str(file['_id'])}"
                    })
            
            return jsonify({
                "status": "success",
                "total": total,
                "filtered_total": len(detections),
                "limit": limit,
                "skip": skip,
                "min_confidence": min_confidence,
                "data": detections
            }), 200
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error al obtener detecciones de personas: {str(e)}"
            }), 500

