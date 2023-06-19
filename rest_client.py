import argparse
import time

import paho.mqtt.publish as mqtt_publish
from flask import Flask
from flask import request

app = Flask(__name__)

mqtt_broker = ''
mqtt_port = 0


@app.route('/on/<device>', methods=['GET'])
def switch_on(device):
    mqtt_topic = f'cmnd/{device}/Power'
    mqtt_publish.single(mqtt_topic, payload='ON', hostname=mqtt_broker, port=mqtt_port)
    return "Switched ON"


@app.route('/off/<device>', methods=['GET'])
def switch_off(device):
    mqtt_topic = f'cmnd/{device}/Power'
    mqtt_publish.single(mqtt_topic, payload='OFF', hostname=mqtt_broker, port=mqtt_port)
    return "Switched OFF"


@app.route('/run/<device>', methods=['GET'])
def switch_on_for_duration(device):
    seconds = int(request.args.get('seconds'))
    switch_on(device)
    time.sleep(seconds)
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
