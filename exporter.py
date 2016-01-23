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
                        default=False,
                        action="store_true",
                        help="Export the internal CPU Temperature of the Raspberry Pi. Requires the vcgencmd.")
    parser.add_argument("--rediscover",
                        default=600,
                        type=int,
                        metavar="REDISCOVER",
                        help="Seconds between two sensor discovery runs.")
    return parser.parse_args()


def find_sensors():
    ret = []
    for device in os.listdir(SENSOR_PATH):
        if "w1_bus_master" not in device:
            sensor_under_test = Sensor(device)
            test_value = sensor_under_test.read_sensor()
            if test_value is not None:
                ret.append(sensor_under_test)
    return ret


class Sensor (object):

    def __init__(self, id):
        self.id = id
        self.last_value = 0
        self.miss_reads = 0
        self.error_gauge = None

    def set_error_gauge(self, gauge):
        self.error_gauge = gauge
        self.unset_missread()

    def set_missread(self):
        if self.error_gauge is not None:
            self.error_gauge.set(1)

    def unset_missread(self):
        if self.error_gauge is not None:
            self.error_gauge.set(0)

    def __call__(self, *args, **kwargs):
        value = self.read_sensor()
        if value is None:
            self.miss_reads +=1
            if self.miss_reads > 5:
                return 85
            return self.last_value
        else:
            self.miss_reads = 0
            self.last_value = value
            return value

    def __repr__(self):
        return "Sensor ID: " + self.__str__()

    def __str__(self):
        return self.id

    def read_sensor(self):
        try:
            with open("%s/%s/w1_slave" % (SENSOR_PATH, self.id), "r") as sensor:
                crc = l = None
                try:
                    crc = sensor.readline()
                    if "YES" not in crc:
                        raise Exception("Could not read sensor. Wrong CRC.")
                    l = sensor.readline()
                    match = TEMP_REGEX.search(l)
                    ret_val = float(match.group(1))/1000
                    if ret_val == 85:
                        raise Exception("Could not read sensor. Sensor returned default value.")
                    else:
                        self.unset_missread()
                        return ret_val
                except Exception, e:
                    print self.id, "Ups something went wrong.", e.message
                    if crc is not None:
                        print "CRC Line: ", crc
                    if l is not None:
                        print "l Line: ", l
                    self.set_missread()
                    return None
        except IOError, e:
            print e.message
            self.set_missread()
            return None


def read_raspberry_pi_temperature():
    p = subprocess.Popen(["/usr/bin/vcgencmd", "measure_temp"], stdout=subprocess.PIPE)
    match = INTERNAL_TEMP_REGEX.search(p.stdout.read())
    return float(match.group(1))

def register_new_sensors(new_sensors, old_sensors, gauge, error_gauge):
    for sensor in new_sensors:
        if sensor not in old_sensors:
            gauge.labels(str(sensor)).set_function(sensor)
            sensor.set_error_gauge(error_gauge.labels(str(sensor)))

def register_prometheus_gauges(export_internal_raspberry=False):
    gauge = Gauge("sensor_temperature_in_celsius", "Local room temperature around the raspberry pi", ["sensor"])
    error_gauge = Gauge("faulty_sensor_read", "Is 1 if the sensor could not be read.", ["sensor"])
    if export_internal_raspberry:
        g = Gauge("cpu_temperature_in_celsius", "CPU Temperature of the Raspberry Pi")
        g.set_function(read_raspberry_pi_temperature)
    return gauge, error_gauge


if __name__ == "__main__":
    args = read_command_arguments()
    start_http_server(args.port)
    gauge, error_gauge = register_prometheus_gauges(args.internal)
    sensors = set(find_sensors())
    register_new_sensors(sensors,set([]), gauge, error_gauge)
    while True:
        time.sleep(args.rediscover)
        new_sensors = set(find_sensors())
        register_new_sensors(new_sensors, sensors, gauge, error_gauge)
        sensors = sensors.union(new_sensors)
