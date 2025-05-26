"""
Utilidades para manejar tipos MIME.
"""

import mimetypes

def configure_mime_types():
    """
    Configura tipos MIME adicionales para la aplicación.
    """
    mimetypes.add_type('image/webp', '.webp')
    mimetypes.add_type('image/png', '.png')
    mimetypes.add_type('image/jpeg', '.jpg')
    mimetypes.add_type('image/jpeg', '.jpeg')
