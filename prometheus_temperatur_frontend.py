import requests

from flask import Flask
app = Flask(__name__)

SENSOR_NAMING = {
    "10-000802e4e190": "Raspberry Pi",
    "10-000802e42e3f": "Raumtemperatur",
}

BASE_URL = "http://192.168.1.14:9090/api/v1/"


@app.route("/")
def hello():
    res = requests.get(BASE_URL + "query?query=sensor_temperature_in_celsius")
    ret = ""
    ret_values = []
    for sensor in res.json()["data"]["result"]:
        name = SENSOR_NAMING[sensor["metric"]["sensor"]]
        value = sensor["value"][1]
        ret_values.append((name, value))

    ret_values = sorted(ret_values)

    for name, value in ret_values:
        ret += "%s: %s</br>" % (name, value)

    return "Hello World!</br>" + ret

if __name__ == "__main__":
    app.run(debug=True)
