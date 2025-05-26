import requests
from datetime import datetime
import os

# Dirección IP de tu ESP32-CAM (ajusta según tu red)
ESP32_CAM_URL = "http://192.168.211.252/capture"

# Carpeta donde se guardarán las imágenes
SAVE_DIR = "capturas"
os.makedirs(SAVE_DIR, exist_ok=True)

def capture_image():
    try:
        response = requests.get(ESP32_CAM_URL)
        if response.status_code == 200:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(SAVE_DIR, f"imagen_{timestamp}.jpg")
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"[✓] Imagen guardada en {filename}")
        else:
            print(f"[✗] Error al capturar imagen: Código {response.status_code}")
    except Exception as e:
        print(f"[✗] Error de conexión: {e}")

# Ejemplo: capturar una imagen
if __name__ == "__main__":
    capture_image()
