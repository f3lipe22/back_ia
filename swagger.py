"""
Configuración de Swagger para la documentación de la API.
"""

def get_swagger_config():
    """
    Retorna la configuración de Swagger para la API.
    
    Returns:
        dict: Configuración de Swagger
    """
    return {
        "swagger": "2.0",
        "info": {
            "title": "API de Invernadero Inteligente",
            "description": "API para el sistema de monitoreo de invernadero inteligente con procesamiento de imágenes y datos de sensores.",
            "version": "1.0.0",
            "contact": {
                "email": "contacto@invernadero.com"
            }
        },
        "basePath": "/",
        "schemes": [
            "http",
            "https"
        ],
        "tags": [
            {
                "name": "general",
                "description": "Operaciones generales"
            },
            {
                "name": "imágenes",
                "description": "Operaciones relacionadas con imágenes"
            },
            {
                "name": "mqtt",
                "description": "Operaciones relacionadas con MQTT y sensores"
            }
        ],
        "paths": {
            "/api/test": {
                "get": {
                    "tags": ["general"],
                    "summary": "Probar la API",
                    "description": "Verifica que la API está funcionando correctamente",
                    "produces": ["application/json"],
                    "responses": {
                        "200": {
                            "description": "Operación exitosa",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "success"},
                                    "message": {"type": "string", "example": "API funcionando correctamente"},
                                    "database": {"type": "string", "example": "invernadero_db"},
                                    "connection": {"type": "string", "example": "mongodb://localhost:27017"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/upload": {
                "post": {
                    "tags": ["imágenes"],
                    "summary": "Subir imagen",
                    "description": "Sube una nueva imagen con metadatos asociados",
                    "consumes": ["multipart/form-data"],
                    "produces": ["application/json"],
                    "parameters": [
                        {
                            "name": "image",
                            "in": "formData",
                            "description": "Archivo de imagen a subir",
                            "required": True,
                            "type": "file"
                        },
                        {
                            "name": "metadata",
                            "in": "formData",
                            "description": "Metadatos asociados a la imagen (JSON)",
                            "required": False,
                            "type": "string"
                        }
                    ],
                    "responses": {
                        "201": {
                            "description": "Imagen subida correctamente",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "success"},
                                    "message": {"type": "string", "example": "Imagen subida correctamente"},
                                    "file_id": {"type": "string", "example": "60f8a1b2c3d4e5f6a7b8c9d0"}
                                }
                            }
                        },
                        "400": {
                            "description": "Solicitud inválida"
                        },
                        "500": {
                            "description": "Error interno del servidor"
                        }
                    }
                }
            },
            "/api/images": {
                "get": {
                    "tags": ["imágenes"],
                    "summary": "Listar imágenes",
                    "description": "Obtiene una lista de todas las imágenes almacenadas con sus metadatos",
                    "produces": ["application/json"],
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "description": "Número máximo de imágenes a retornar",
                            "required": False,
                            "type": "integer",
                            "default": 10
                        },
                        {
                            "name": "skip",
                            "in": "query",
                            "description": "Número de imágenes a omitir (para paginación)",
                            "required": False,
                            "type": "integer",
                            "default": 0
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Operación exitosa",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "success"},
                                    "total": {"type": "integer", "example": 42},
                                    "limit": {"type": "integer", "example": 10},
                                    "skip": {"type": "integer", "example": 0},
                                    "data": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "file_id": {"type": "string"},
                                                "filename": {"type": "string"},
                                                "content_type": {"type": "string"},
                                                "size": {"type": "integer"},
                                                "upload_date": {"type": "string"},
                                                "metadata": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Error interno del servidor"
                        }
                    }
                }
            },
            "/api/image/{file_id}": {
                "get": {
                    "tags": ["imágenes"],
                    "summary": "Obtener imagen",
                    "description": "Obtiene una imagen específica por su ID",
                    "produces": ["image/*"],
                    "parameters": [
                        {
                            "name": "file_id",
                            "in": "path",
                            "description": "ID de la imagen a obtener",
                            "required": True,
                            "type": "string"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Imagen encontrada"
                        },
                        "404": {
                            "description": "Imagen no encontrada"
                        },
                        "500": {
                            "description": "Error interno del servidor"
                        }
                    }
                },
                "delete": {
                    "tags": ["imágenes"],
                    "summary": "Eliminar imagen",
                    "description": "Elimina una imagen específica por su ID",
                    "produces": ["application/json"],
                    "parameters": [
                        {
                            "name": "file_id",
                            "in": "path",
                            "description": "ID de la imagen a eliminar",
                            "required": True,
                            "type": "string"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Imagen eliminada correctamente",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "success"},
                                    "message": {"type": "string", "example": "Imagen eliminada correctamente"}
                                }
                            }
                        },
                        "404": {
                            "description": "Imagen no encontrada"
                        },
                        "500": {
                            "description": "Error interno del servidor"
                        }
                    }
                }
            },
            "/api/mensaje": {
                "post": {
                    "tags": ["mqtt"],
                    "summary": "Recibir mensaje MQTT",
                    "description": "Recibe un mensaje MQTT desde un cliente externo",
                    "consumes": ["application/json"],
                    "produces": ["application/json"],
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "description": "Datos del mensaje MQTT",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "required": ["topic", "valor"],
                                "properties": {
                                    "topic": {"type": "string", "example": "sensor/temperatura"},
                                    "valor": {"type": "string", "example": "25.5"}
                                }
                            }
                        }
                    ],
                    "responses": {
                        "201": {
                            "description": "Mensaje recibido correctamente",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "success"},
                                    "message": {"type": "string", "example": "Mensaje recibido y guardado correctamente"},
                                    "document_id": {"type": "string", "example": "60f8a1b2c3d4e5f6a7b8c9d0"}
                                }
                            }
                        },
                        "400": {
                            "description": "Solicitud inválida"
                        },
                        "500": {
                            "description": "Error interno del servidor"
                        }
                    }
                }
            },
            "/api/mensajes": {
                "get": {
                    "tags": ["mqtt"],
                    "summary": "Obtener mensajes MQTT",
                    "description": "Obtiene todos los mensajes MQTT almacenados",
                    "produces": ["application/json"],
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "description": "Número máximo de mensajes a retornar",
                            "required": False,
                            "type": "integer",
                            "default": 10
                        },
                        {
                            "name": "skip",
                            "in": "query",
                            "description": "Número de mensajes a omitir (para paginación)",
                            "required": False,
                            "type": "integer",
                            "default": 0
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Operación exitosa",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "success"},
                                    "total": {"type": "integer", "example": 100},
                                    "limit": {"type": "integer", "example": 10},
                                    "skip": {"type": "integer", "example": 0},
                                    "data": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "_id": {"type": "string"},
                                                "topic": {"type": "string"},
                                                "valor": {"type": "string"},
                                                "timestamp": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Error interno del servidor"
                        }
                    }
                }
            },
            "/api/mqtt/status": {
                "get": {
                    "tags": ["mqtt"],
                    "summary": "Estado del sistema MQTT",
                    "description": "Obtiene el estado actual del sistema MQTT",
                    "produces": ["application/json"],
                    "responses": {
                        "200": {
                            "description": "Operación exitosa",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "success"},
                                    "mqtt_system": {
                                        "type": "object",
                                        "properties": {
                                            "backend_endpoint": {"type": "string"},
                                            "external_subscriber": {"type": "object"},
                                            "statistics": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        },
                        "500": {
                            "description": "Error interno del servidor"
                        }
                    }
                }
            },
            "/api/test/temperatura": {
                "post": {
                    "tags": ["mqtt"],
                    "summary": "Probar envío de temperatura",
                    "description": "Endpoint de prueba para simular el envío de una temperatura",
                    "consumes": ["application/json"],
                    "produces": ["application/json"],
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "description": "Datos de temperatura",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "required": ["valor"],
                                "properties": {
                                    "valor": {"type": "number", "example": 25.5}
                                }
                            }
                        }
                    ],
                    "responses": {
                        "201": {
                            "description": "Temperatura enviada correctamente",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "success"},
                                    "message": {"type": "string", "example": "Temperatura guardada y transformada correctamente"},
                                    "document_id": {"type": "string", "example": "60f8a1b2c3d4e5f6a7b8c9d0"},
                                    "temperatura_original": {"type": "number", "example": 25.5},
                                    "mensaje_transformado": {"type": "object"}
                                }
                            }
                        },
                        "400": {
                            "description": "Solicitud inválida"
                        },
                        "500": {
                            "description": "Error interno del servidor"
                        }
                    }
                }
            },
            "/api/test/intrusion": {
                "post": {
                    "tags": ["mqtt"],
                    "summary": "Probar detección de intrusos",
                    "description": "Endpoint de prueba para simular la detección de intrusos (personas)",
                    "consumes": ["application/json"],
                    "produces": ["application/json"],
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "description": "Datos de la detección de intrusos",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "total_persons": {"type": "integer", "example": 1, "description": "Número de personas detectadas"},
                                    "confidence": {"type": "number", "example": 0.95, "description": "Nivel de confianza de la detección (0-1)"}
                                }
                            }
                        }
                    ],
                    "responses": {
                        "201": {
                            "description": "Alerta de intrusión enviada correctamente",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "success"},
                                    "message": {"type": "string", "example": "Alerta de intrusión enviada correctamente"},
                                    "document_id": {"type": "string", "example": "60f8a1b2c3d4e5f6a7b8c9d0"},
                                    "notification_message": {"type": "string", "example": "Se detectaron 1 persona en el invernadero"},
                                    "transformed_message": {"type": "object"}
                                }
                            }
                        },
                        "400": {
                            "description": "Solicitud inválida"
                        },
                        "500": {
                            "description": "Error interno del servidor"
                        }
                    }
                }
            }
        },
        "definitions": {
            "Error": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "example": "error"
                    },
                    "message": {
                        "type": "string"
                    }
                }
            }
        }
    }
