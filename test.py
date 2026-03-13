from mqtt_client import start_mqtt, TELEMETRY_DATA

start_mqtt(blocking=False)
import time

while True:
    print(TELEMETRY_DATA)
    time.sleep(1)