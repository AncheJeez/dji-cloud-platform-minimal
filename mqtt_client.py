#!/usr/bin/env python3

import os
import json
import pprint
import threading
from importlib.metadata import version

import paho
import paho.mqtt.client as mqtt

from dotenv import load_dotenv
load_dotenv()

host_addr = os.environ.get("HOST_ADDR", "localhost")

DEVICE_SN = None
PRODUCT_ID = None
BATTERY_PERCENT = None

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc, properties=None):
    print(f"[MQTT] Connected to {host_addr} with result code {rc}")
    client.subscribe("sys/#")
    client.subscribe("thing/#")
    print("[MQTT] Subscribed to topics: sys/#, thing/#")

    client.subscribe("thing/product/+/device/+/status")
    print("[MQTT] Subscribed to: thing/product/+/device/+/status")

# Print interesting bits from message
def handle_osd_message(message: dict):
    data = message.get("data", {})
    lat = data.pop("latitude", None)
    lon = data.get("longitude", None)
    attitude_head = data.pop("attitude_head", None)
    attitude_pitch = data.pop("attitude_pitch", None)
    attitude_roll = data.pop("attitude_roll", None)
    height = data.pop("height", None)
    data.pop("wireless_link", None)
    data.pop("wireless_link_state", None)
    data.pop("battery", None)
    data.pop("live_status", None)

    print(
        f"[OSD] Lat: {lat}, Lon: {lon}, Height: {height}, "
        f"Head: {attitude_head}, Pitch: {attitude_pitch}, Roll: {attitude_roll}"
    )
    if data:
        print("[OSD] Additional data:")
        pprint.pprint(data)

    global BATTERY_PERCENT

    # record battery once
    if BATTERY_PERCENT is None:
        battery = data.get("battery", {})
        percent = battery.get("capacity_percent")
        if percent is not None:
            BATTERY_PERCENT = percent
            print(f"🔋 Battery capacity: {percent}%")
            client.unsubscribe(topic)
            print(f"[MQTT] Unsubscribed from {topic}")


# The callback for when a PUBLISH message is received from the server.
def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    print(f"[MQTT] Received message on topic: {msg.topic}")
    try:
        message = json.loads(msg.payload.decode("utf-8"))
    except Exception as e:
        print(f"[MQTT] Failed to decode message: {e}")
        return

    global DEVICE_SN, PRODUCT_ID

    if msg.topic.endswith("status"):
        if message.get("method") != "update_topo":
            print("[MQTT] Ignored status message (method != update_topo)")
            return
        response = {
            "tid": message.get("tid"),
            "bid": message.get("bid"),
            "timestamp": message.get("timestamp", 0) + 2,
            "data": {"result": 0},
        }
        client.publish(msg.topic + "_reply", payload=json.dumps(response))
        print(f"[MQTT] Published reply to {msg.topic}_reply")
    elif msg.topic.endswith("osd") and msg.topic.startswith("thing"):
        handle_osd_message(message)
    else:
        print("[MQTT] Message topic did not match any handler.")

    global DEVICE_SN, PRODUCT_ID

    print(f"[MQTT] Received: {msg.topic}")

    try:
        message = json.loads(msg.payload.decode("utf-8"))
    except Exception as e:
        print(f"[MQTT] Failed to decode message: {e}")
        return

    if msg.topic.endswith("status") and DEVICE_SN is None:

        # El SN viene en el topic:
        # thing/product/{product_id}/device/{device_sn}/status
        parts = msg.topic.split("/")
        PRODUCT_ID = parts[2]
        DEVICE_SN = parts[4]

        print(f"Drone detected!")
        print(f"Product ID: {PRODUCT_ID}")
        print(f"Serial Number: {DEVICE_SN}")

        # Suscribirse al OSD del dron
        osd_topic = f"thing/product/{PRODUCT_ID}/device/{DEVICE_SN}/osd"
        client.subscribe(osd_topic)
        print(f"[MQTT] Subscribed to OSD topic: {osd_topic}")

    elif msg.topic.endswith("osd"):
        handle_osd_message(client, msg.topic, message)

def create_mqtt_client():
    PAHO_MAIN_VER = int(version("paho-mqtt").split(".")[0])
    if PAHO_MAIN_VER == 1:
        client = mqtt.Client(transport="tcp")
    else:
        client = mqtt.Client(paho.mqtt.enums.CallbackAPIVersion.VERSION2, transport="tcp")
    client.on_connect = on_connect
    client.on_message = on_message
    return client

def start_mqtt(blocking=True):
    client = create_mqtt_client()
    print(f"[MQTT] Connecting to {host_addr}:1883 ...")

    # username = os.getenv("MQTT_USERNAME")
    # password = os.getenv("MQTT_PASSWORD")
    # client.username_pw_set(username, password)
    # print(f"[MQTT] Authentication set with username: {username}")

    client.connect(host_addr, 1883, 60)
    if blocking:
        print("[MQTT] Entering blocking loop_forever()")
        client.loop_forever()
    else:
        print("[MQTT] Starting MQTT loop in background thread")
        thread = threading.Thread(target=client.loop_forever, daemon=True)
        thread.start()
        return client

# If run directly, start MQTT in blocking mode
if __name__ == "__main__":
    start_mqtt(blocking=True)