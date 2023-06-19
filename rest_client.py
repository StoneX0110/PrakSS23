#!/usr/bin/env python
import argparse
import threading
import time
import asyncio

import paho.mqtt.publish as mqtt_publish
from flask import Flask
from flask import request

app = Flask(__name__)

mqtt_broker = ''
mqtt_port = 0


@app.route('/<device>/state', methods=['GET'])
def get_state(device):
    #TODO
    mqtt_topic = f'???/{device}/???'
    mqtt_publish.single(mqtt_topic, payload='???', hostname=mqtt_broker, port=mqtt_port)
    return f"Ran for {seconds} seconds, then turned OFF"


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
    seconds = int(request.args.get('seconds'))
    switch_on(device)
    time.sleep(seconds)
    switch_off(device)
    return f"Ran for {seconds} seconds, then turned OFF"


@app.route('/<device>/wait', methods=['PUT'])
def wait(device):
    seconds = int(request.args.get('seconds'))
    thread = threading.Thread(target=_run_async_task, args=(seconds, device))
    thread.start()
    print("Returning wait")
    return f"Started running for {seconds} seconds..."


def _run_async_task(seconds, device):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_switch_on_for_duration(seconds, device))
    loop.close()


async def _switch_on_for_duration(seconds, device):
    switch_on(device)
    await asyncio.sleep(seconds)
    switch_off(device)
    return f"Ran for {seconds} seconds, then turned OFF"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("mqtt_ip", type=str, help="IP of MQTT broker")
    parser.add_argument("mqtt_port", type=int, help="Port of MQTT broker")
    args = parser.parse_args()

    mqtt_broker = args.mqtt_ip
    mqtt_port = args.mqtt_port

    app.run(host='0.0.0.0', port=5000)
