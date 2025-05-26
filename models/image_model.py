"""
Modelo para manejar las operaciones relacionadas con imágenes en GridFS.
"""

from bson.objectid import ObjectId
import datetime
import mimetypes
from io import BytesIO

class ImageModel:
    """
    Clase para manejar las operaciones CRUD de imágenes en GridFS.
    """
    
    def __init__(self, db, fs):
        """
        Inicializa el modelo con la base de datos y GridFS.
        
        Args:
            db: Instancia de la base de datos MongoDB
            fs: Instancia de GridFS para manejar archivos
        """
        self.db = db
        self.fs = fs
    
    def save_image(self, image_file, additional_metadata=None):
        """
        Guarda una imagen en GridFS.
        
        Args:
            image_file: Archivo de imagen a guardar
            additional_metadata: Metadatos adicionales para la imagen (opcional)
            
        Returns:
            str: ID del archivo guardado
            dict: Metadatos del archivo
        """
        # Determinar el tipo MIME de la imagen
        content_type = image_file.content_type
        if not content_type or content_type == 'application/octet-stream':
            # Intentar determinar el tipo MIME por la extensión
            content_type = mimetypes.guess_type(image_file.filename)[0] or 'application/octet-stream'
        
        # Crear metadatos base
        metadata = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "content_type": content_type
        }
        
        # Añadir metadatos adicionales si se proporcionaron
        if additional_metadata:
            metadata.update(additional_metadata)
        
        # Guardar la imagen en GridFS
        file_id = self.fs.put(
            image_file,
            filename=image_file.filename,
            content_type=content_type,
            metadata=metadata
        )
        
        return str(file_id), metadata
    
    def get_image(self, file_id):
        """
        Obtiene una imagen de GridFS por su ID.
        
        Args:
            file_id: ID del archivo a obtener
            
        Returns:
            tuple: (file, content_type) donde:
                - file: Objeto de archivo de GridFS
                - content_type: Tipo MIME del archivo
        """
        # Validar el formato del ID
        if not ObjectId.is_valid(file_id):
            raise ValueError("ID de archivo inválido")
        
        # Obtener el archivo
        file = self.fs.get(ObjectId(file_id))
        
        # Determinar el tipo MIME
        content_type = file.content_type
        if not content_type or content_type == 'application/octet-stream':
            content_type = mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
        
        return file, content_type
    
    def list_images(self, limit=10, skip=0):
        """
        Lista todas las imágenes almacenadas en GridFS.
        
        Args:
            limit: Número máximo de imágenes a devolver
            skip: Número de imágenes a omitir
            
        Returns:
            tuple: (total, images) donde:
                - total: Número total de imágenes
                - images: Lista de imágenes con sus metadatos
        """
        # Validar parámetros
        if limit < 1 or limit > 100:
            limit = 10
        if skip < 0:
            skip = 0
        
        # Obtener archivos con paginación
        files = self.fs.find().sort("uploadDate", -1).skip(skip).limit(limit)
        total = self.db.fs.files.count_documents({})
        
        images = []
        for file in files:
            images.append({
                "file_id": str(file._id),
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file.length,
                "upload_date": file.upload_date.isoformat() if hasattr(file, 'upload_date') else None,
                "metadata": file.metadata
            })
        
        return total, images
    
    def delete_image(self, file_id):
        """
        Elimina una imagen de GridFS por su ID.
        
        Args:
            file_id: ID del archivo a eliminar
            
        Returns:
            bool: True si se eliminó correctamente, False en caso contrario
        """
        # Validar el formato del ID
        if not ObjectId.is_valid(file_id):
            raise ValueError("ID de archivo inválido")
        
        # Verificar si el archivo existe
        if not self.fs.exists(ObjectId(file_id)):
            raise FileNotFoundError("No se encontró la imagen")
        
        # Eliminar el archivo
        self.fs.delete(ObjectId(file_id))
        
        return True

    def save_image_from_bytes(self, file_obj, additional_metadata=None):
        """
        Guarda una imagen en GridFS desde un objeto BytesIO.
        
        Args:
            file_obj: Objeto BytesIO con los datos de la imagen
            additional_metadata: Metadatos adicionales para la imagen (opcional)
            
        Returns:
            str: ID del archivo guardado
            dict: Metadatos del archivo
        """
        # Determinar el tipo MIME de la imagen
        content_type = mimetypes.guess_type(file_obj.name)[0] or 'image/jpeg'
        
        # Crear metadatos base
        metadata = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "content_type": content_type
        }
        
        # Añadir metadatos adicionales si se proporcionaron
        if additional_metadata:
            metadata.update(additional_metadata)
        
        # Guardar la imagen en GridFS
        file_id = self.fs.put(
            file_obj,
            filename=file_obj.name,
            content_type=content_type,
            metadata=metadata
        )
        
        return str(file_id), metadata

    def update_image_metadata(self, file_id, new_metadata):
        """
        Actualiza los metadatos de una imagen en GridFS.
        
        Args:
            file_id: ID del archivo a actualizar
            new_metadata: Nuevos metadatos a añadir/actualizar
        
        Returns:
            bool: True si se actualizó correctamente
        """
        # Validar el formato del ID
        if not ObjectId.is_valid(file_id):
            raise ValueError("ID de archivo inválido")
        
        # Obtener metadatos actuales
        file_info = self.db.fs.files.find_one({"_id": ObjectId(file_id)})
        if not file_info:
            raise FileNotFoundError("No se encontró la imagen")
        
        # Obtener metadatos actuales o crear un diccionario vacío
        current_metadata = file_info.get("metadata", {})
        
        # Actualizar metadatos
        current_metadata.update(new_metadata)
        
        # Guardar metadatos actualizados
        self.db.fs.files.update_one(
            {"_id": ObjectId(file_id)},
            {"$set": {"metadata": current_metadata}}
        )
        
        return True

