# i17 Practical Course 23SS - REST Service for Mixer
## Installation
1. Clone the project
```
git clone https://github.com/StoneX0110/PrakSS23
```
2. Install the required dependencies
```
pip install -r requirements.txt
```
## Usage
1. Start the MQTT broker to which the application and your devices should connect to
2. Run the Python script
```
python rest_client.py <mqtt_ip> <mqtt_port> [-d]
```
- <mqtt_ip>: IP address of the MQTT broker
- <mqtt_port>: Port of the MQTT broker
- -d or --daemon: Optional flag to run the application as a daemon
  
The application now tells you all the IPs it is accessible at after having started.

## Functionality
The REST service provides access to the following endpoints:
- GET `/<device>/state`: Retrieves the current state of the device (e.g., ON or OFF).
- PUT `/<device>/on`: Turns on the device.
- PUT `/<device>/off`: Turns off the device.
- PUT `/<device>/run`: Turns on the device for a specified duration.
  - Requires a JSON body with the following parameters:
      - *seconds* (int), indicating the number of seconds the device should run.
      The device should not run for more than 60 seconds.
- PUT `/<device>/wait`: Turns on the device for a specified duration. Is synchronous, meaning that a CPEE process will wait for the device to complete the run-time before going on with the process.
  Measures power consumption in specified intervals during run-time.
  - Requires a JSON body with the following parameters:
    - *seconds* (int), indicating the number of seconds the device should run.
    The device should not run for more than 60 seconds.
    - *interval* (float), indicating the polling interval for the power consumption in seconds.
  - The application first returns a response with the header `CPEE-CALLBACK = true`. This tells the CPEE process to wait until a final result is returned to its callback-URL by the application.
  - The final result returned to the callback-URL is a list of the power consumption measurements in Watt.

We configured the application to be able to control multiple devices, thus `<device>` represents the name of the remote switch to be accessed, in our case 'mixer'.
