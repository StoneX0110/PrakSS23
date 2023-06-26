#!/usr/bin/env python
import argparse
import threading
import time
import asyncio

import paho.mqtt.publish as mqtt_publish
import paho.mqtt.client as mqtt_client
import requests
from flask import Flask, Response, request, jsonify

app = Flask(__name__)

mqtt_broker = ''
mqtt_port = 0

result = ""
result_received = threading.Event()


def _on_message(client, userdata, message):
    global result
    result = message.payload.decode()
    result_received.set()


@app.route('/<device>/state', methods=['GET'])
def get_state(device):
    global result, result_received

    result = ""
    result_received.clear()

    client = mqtt_client.Client()
    client.on_message = _on_message
    client.connect(mqtt_broker, mqtt_port)

    topic_subscribe = f"stat/{device}/POWER"
    client.subscribe(topic_subscribe)
    client.loop_start()

    topic_publish = f'cmnd/{device}/Power'
    client.publish(topic_publish)

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

    thread = threading.Thread(target=_switch_on_for_duration, args=(device, seconds))
    thread.start()

    return f"Running {device} for {seconds} seconds."


@app.route('/<device>/wait', methods=['PUT'])
def wait(device):
    seconds = int(request.form.get('seconds'))
    if seconds > 60:
        return Response("The device is not allowed to run longer than 60 seconds.", status=400)

    callback_url = request.headers.get('Cpee-Callback')
    thread = threading.Thread(target=_switch_on_for_duration, args=(device, seconds, callback_url))
    thread.start()

    response = Response( f"Running {device} for {seconds} seconds.")
    response.headers["CPEE-CALLBACK"] = "true"
    return response


def _switch_on_for_duration(device, seconds, callback_url=None):
    switch_on(device)
    time.sleep(seconds)
    switch_off(device)
    if callback_url:
        requests.put(callback_url, f"Ran {device} for {seconds} seconds.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("mqtt_ip", type=str, help="IP of MQTT broker")
    parser.add_argument("mqtt_port", type=int, help="Port of MQTT broker")
    args = parser.parse_args()

    mqtt_broker = args.mqtt_ip
    mqtt_port = args.mqtt_port

    app.run(host='0.0.0.0', port=5000)
