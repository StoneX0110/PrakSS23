#!/usr/bin/env python
import argparse
import json
import threading
import time

import daemon
import paho.mqtt.client as mqtt_client
import paho.mqtt.publish as mqtt_publish
import requests
from flask import Flask, Response, request

import power_service

app = Flask(__name__)

mqtt_broker = ''
mqtt_port = 0

result = ""
result_received = threading.Event()


def _read_switch_state(client, userdata, message):
    global result
    result = message.payload.decode()
    result_received.set()


@app.route('/<device>/state', methods=['GET'])
def get_state(device):
    global result, result_received

    result = ""
    result_received.clear()

    client = mqtt_client.Client()
    client.on_message = _read_switch_state
    client.connect(mqtt_broker, mqtt_port)

    # Tasmota devices publish their power status on this topic
    topic_subscribe = f"stat/{device}/POWER"
    client.subscribe(topic_subscribe)
    client.loop_start()

    # This triggers the device to publish its current power status
    topic_publish = f'cmnd/{device}/Power'
    client.publish(topic_publish)

    # Waits for the power status to be received
    result_received.wait(timeout=5)

    client.loop_stop()
    client.disconnect()
    return result


@app.route('/<device>/on', methods=['PUT'])
def switch_on(device):
    mqtt_topic = f'cmnd/{device}/Power'
    mqtt_publish.single(mqtt_topic, payload='ON', hostname=mqtt_broker, port=mqtt_port)
    return "Switched ON"


@app.route('/<device>/off', methods=['PUT'])
def switch_off(device):
    mqtt_topic = f'cmnd/{device}/Power'
    mqtt_publish.single(mqtt_topic, payload='OFF', hostname=mqtt_broker, port=mqtt_port)
    return "Switched OFF"


@app.route('/<device>/run', methods=['PUT'])
def run(device):
    seconds = int(request.form.get('seconds'))
    if seconds > 60:
        return Response("The device is not allowed to run longer than 60 seconds.", status=400)

    # This starts a separate thread running the mixer, meanwhile a response is instantly returned to the caller.
    thread = threading.Thread(target=_switch_on_for_duration, args=(device, seconds))
    thread.start()

    return f"Running {device} for {seconds} seconds."


@app.route('/<device>/wait', methods=['PUT'])
def wait(device):
    seconds = int(request.form.get('seconds'))
    if seconds > 60:
        return Response("The device is not allowed to run longer than 60 seconds.", status=400)
    interval = float(request.form.get('interval'))
    callback_url = request.headers.get('Cpee-Callback')

    # This starts a separate thread running the mixer
    thread_run_device = threading.Thread(target=_switch_on_for_duration, args=(device, seconds, callback_url))
    thread_run_device.start()

    # This starts a separate thread measuring the mixer's power consumption
    thread_measure_consumption = threading.Thread(target=power_service.measure_power_consumption,
                                                  args=(mqtt_broker, mqtt_port, device, seconds, interval))
    thread_measure_consumption.start()

    response = Response(f"Running {device} for {seconds} seconds.")
    response.headers[
        "CPEE-CALLBACK"] = "true"  # This tells a CPEE process to await a response returned to its callback URL
    return response


def _switch_on_for_duration(device, seconds, callback_url=None):
    switch_on(device)
    time.sleep(seconds)
    switch_off(device)
    if callback_url:
        requests.put(callback_url, json.dumps(power_service.get_consumptions()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("mqtt_ip", type=str, help="IP of MQTT broker")
    parser.add_argument("mqtt_port", type=int, help="Port of MQTT broker")
    parser.add_argument('-d', '--daemon', action='store_true', help="Run the application as a daemon")
    args = parser.parse_args()

    mqtt_broker = args.mqtt_ip
    mqtt_port = args.mqtt_port

    if args.daemon:
        with daemon.DaemonContext():
            app.run(host='0.0.0.0', port=5000)
    else:
        app.run(host='0.0.0.0', port=5000)
