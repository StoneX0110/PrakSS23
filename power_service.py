import json
import time

_consumptions = []


def get_consumptions():
    return _consumptions


def _read_power_consumption(client, userdata, message):
    global _consumptions
    power_data = json.loads(message.payload.decode())
    _consumptions.append(
        power_data['StatusSNS']['ENERGY']['Power'])  # This gets the value of the current consumption in Watt


def measure_power_consumption(mqtt_client, mqtt_broker, mqtt_port, device, runtime, interval):
    global _consumptions
    _consumptions.clear()

    client = mqtt_client.Client()
    client.on_message = _read_power_consumption
    client.connect(mqtt_broker, mqtt_port)

    # Tasmota devices publish their power consumption on this topic
    client.subscribe(f'stat/{device}/STATUS8')
    client.loop_start()

    time.sleep(1.5)
    # This is due to an internal delay in the remote switch until its power consumption is correctly published.
    # If we omitted this, the first values in the power consumptions list would always be multiple zeros.

    max_counter = round(runtime / interval)
    for counter in range(max_counter):
        # This triggers the device to publish its current power consumption
        client.publish(f'cmnd/{device}/Status', payload=8)
        counter += 1
        time.sleep(interval)
