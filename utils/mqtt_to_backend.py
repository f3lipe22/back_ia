import paho.mqtt.client as mqtt
import requests
import time

BACKEND_URL = "http://localhost:5000/api/mensaje"  # Endpoint backend

# Definición de tópicos
TOPICO_TEMPERATURA = "sensor/temperatura"
TOPICO_NOTIFICACIONES = "sistema/notificaciones"
TOPICO_VENTILADOR = "actuador/ventilador"
TOPICO_BOMBILLO = "actuador/bombillo"

# Lista de todos los tópicos a suscribirse
TOPICOS = [TOPICO_TEMPERATURA, TOPICO_NOTIFICACIONES, TOPICO_VENTILADOR, TOPICO_BOMBILLO]

BROKER = "192.168.196.202"
PUERTO = 9001  # Puerto WebSocket típico para MQTT
WEBSOCKETS_PATH = "/mqtt"  # Ruta WebSocket típica

def enviar_al_backend(topic, valor):
    data = {"topic": topic, "valor": valor}
    try:
        response = requests.post(BACKEND_URL, json=data, timeout=5)
        response.raise_for_status()
        print(f"📤 Enviado al backend con éxito: {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Error enviando al backend: {e}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado al MQTT Broker")
        # Suscribirse a todos los tópicos
        for topico in TOPICOS:
            client.subscribe(topico)
            print(f"📡 Subscrito al tópico: {topico}")
    else:
        print(f"❌ Falló la conexión con código: {rc}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"📨 Mensaje MQTT recibido: {msg.topic} -> {payload}")
    enviar_al_backend(msg.topic, payload)

def main():
    client = mqtt.Client(transport="websockets")
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"🔌 Conectando al broker MQTT por WebSocket {BROKER}:{PUERTO}{WEBSOCKETS_PATH}...")
    while True:
        try:
            client.ws_set_options(path=WEBSOCKETS_PATH)
            client.connect(BROKER, PUERTO, 60)
            client.loop_forever()
        except Exception as e:
            print(f"⚠️ Error de conexión MQTT WebSocket: {e}")
            print("🔄 Reintentando conexión en 5 segundos...")
            time.sleep(5)

if __name__ == "__main__":
    main()
