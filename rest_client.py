import os.path
import argparse

from flask import Flask, render_template
from flask import request
import paho.mqtt.publish as mqtt_publish
import time

app = Flask(__name__, template_folder=os.path.normpath('templates'))

mqtt_broker = ''
mqtt_port = 0
mqtt_topic = 'cmnd/tasmota/Power'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/on', methods=['GET'])
def switch_on():
    mqtt_publish.single(mqtt_topic, payload='ON', hostname=mqtt_broker, port=mqtt_port)
    return index()


@app.route('/off', methods=['GET'])
def switch_off():
    mqtt_publish.single(mqtt_topic, payload='OFF', hostname=mqtt_broker, port=mqtt_port)
    return index()


@app.route('/run', methods=['POST'])
def turn_on_timed():
    seconds = int(request.args.get('seconds'))
    switch_on()
    time.sleep(seconds)
    switch_off()
    return index()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("mqtt_ip", type=str, help="IP of MQTT broker")
    parser.add_argument("mqtt_port", type=int, help="Port of MQTT broker")
    args = parser.parse_args()

    mqtt_broker = args.mqtt_ip
    mqtt_port = args.mqtt_port

    app.run(host='0.0.0.0', port=5000)
