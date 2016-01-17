# 1-Wire Prometheus Exporter

This simple python script exports the temperature values of arbitrary many DS18S20 sensors connected to a Raspberry Pi 
to the monitoring framework Prometheus.io. An tutorial how to connect one or more DS18S20 sensors to your Raspberry Pi 
can be found [here](https://iada.nl/en/blog/article/temperature-monitoring-raspberry-pi). The temperature_sensor.service 
file is an example file for a service managed by SystemD. You can use the service file to autostart the exporter on boot. 

One remark: Since the DS18S20 needs 750ms to measure the temperature and convert it into a digital representation, you
should set your Prometheus scrape_interval to at least *n* * 750ms. *n* is the number of DS18S20 sensors on your 1-wire
 bus.

# Installation

First checkout this git repository:

```
    git clone https://github.com/hikhvar/w1_prometheus_exporter.git
    cd w1_prometheus_exporter
```

If you don't have pip install it via:

```
    sudo apt-get install python-pip
```

Then install the python prometheus client:

```
    sudo pip install prometheus_client
```

Then copy the exporter.py file to /opt/prometheus_temperature and the temperature_sensor.service to /etc/systemd/system:

```
    sudo mkdir -p /opt/prometheus_temperature
    sudo cp exporter.py /opt/prometheus_temperature
    sudo cp temperature_sensor.service /etc/systemd/system
``` 

Register the service and start it:

```
    sudo systemctl enable temperature_sensor.service
    sudo systemctl start temperature_sensor.service
```
    
Now you are done and can check your sensor values via:

```
    curl localhost:8001
```

Have fun!