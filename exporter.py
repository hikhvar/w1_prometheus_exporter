from prometheus_client import start_http_server, Gauge
import re
import time
import os
import subprocess
import argparse

TEMP_REGEX = re.compile('t=([0-9]+)')
INTERNAL_TEMP_REGEX = re.compile('temp=([0-9]+\.[0-9])')
SENSOR_PATH = "/sys/bus/w1/devices"


def read_command_arguments():
    parser = argparse.ArgumentParser(description="Exporter of connected 1-Wire Sensors to Prometheus.io monitoring.")
    parser.add_argument("--port",
                        metavar="PORT",
                        type=int,
                        default=8001,
                        help="The port used to export the temperatures to prometheus.io. Default is 8001.")
    parser.add_argument("--internal",
                        type=bool,
                        default=False,
                        action="store_true",
                        help="Export the internal CPU Temperature of the Raspberry Pi. Requires the vcgencmd.")
    return parser.parse_args()

def find_sensors():
    ret = []
    for device in os.listdir(SENSOR_PATH):
        if "w1_bus_master" not in device:
            try:
                read_sensor(device)
                ret.append(device)
            except:
                pass
    return ret


def get_callback(device):
    def read():
        return read_sensor(device)
    return read


def read_sensor(device):
    with open("%s/%s/w1_slave" % (SENSOR_PATH, device), "r") as sensor:
        crc = l = None
        try:
            crc = sensor.readline() 
            l = sensor.readline()
            match = TEMP_REGEX.search(l)
            return float(match.group(1))/1000
        except:
            print "Ups something went wrong."
            if crc is not None:
                print "CRC Line: ", crc
            if l is not None:
                print "l Line: ", l


def read_raspberry_pi_temperature():
    p = subprocess.Popen(["/usr/bin/vcgencmd", "measure_temp"], stdout=subprocess.PIPE)
    match = INTERNAL_TEMP_REGEX.search(p.stdout.read())
    return float(match.group(1))


def register_prometheus_gauges(export_internal_raspberry=False):
    g = Gauge("sensor_temperature_in_celsius", "Local room temperature around the raspberry pi", ["sensor"])
    sensors = find_sensors()
    print "Found sensors:", ", ".join(sensors)
    for sensor in sensors:
        g.labels(sensor).set_function(get_callback(sensor))
    if export_internal_raspberry:
        g = Gauge("cpu_temperature_in_celsius", "CPU Temperature of the Raspberry Pi")
        g.set_function(read_raspberry_pi_temperature)
    return sensors


if __name__ == "__main__":
    args = read_command_arguments()
    start_http_server(args.port)
    register_prometheus_gauges(args.internal)
    while True:
        time.sleep(10000)
