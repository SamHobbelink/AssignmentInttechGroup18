from websockets.sync.client import connect
import json
import csv

gateway_info = {
    'a840411ee4c44150': ("dragino-alpha", 52.216327, 6.900825, 105),
    'a840411eadfc4150': ("dragino-meander", 52.236887101823, 6.859867572784425, 4),
    'a840411ee8904150': ("dragino-ub", 52.243762, 6.853425, 3),
    '0000024b080301bf': ("kerlink-awm", 52.23989, 6.85014, 54),
    '1dee039aac75c307': ("utwente-enschede-macrocell", 52.2165, 6.9007, 105),
    'a840411eae004150': ("utwente-lg308-02", 52.23923592912191, 6.855506300926209, 4),
    'a840411da56c4150': ("utwente-rav-rooftop", 52.23913, 6.85565, 6),
}

toa_estimates_ms = {
    7: 50,
    8: 100,
    9: 200,
    10: 400,
    11: 800,
    12: 1600
}

bandwidth = 0 ## symbol duration? 2^SF/BW -> Misschien kunnen we daar iets mee.

sensor_locations = {}
with open("sensor_locations.csv", newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        eui = row["Sensor_Eui"].replace(":", "").lower()
        if len(eui) == 16:  # only full EUI-64
            lat = row["St_Y"].strip()
            lon = row["St_X"].strip()
            room = row["Roomname"]
            sensor_locations[eui] = {
                "lat": lat,
                "lon": lon,
                "room": room
            }

output_file = open("device_log.csv", "w", newline="")
writer = csv.writer(output_file)
writer.writerow([
    "device_id", "device_name", "sf", "toa_ms",
    "gateway_name", "gw_lat", "gw_lon", "timestamp",
    "sensor_lat", "sensor_lon", "room"
])

def receive_data():
    max_msg = 10  # Adjust as needed
    with connect("ws://192.87.172.71:1337") as websocket:
        count = 0
        while count < max_msg:
            msg = websocket.recv()
            try:
                msg = json.loads(msg)
                handle_message(msg)
                count += 1
            except json.JSONDecodeError:
                print("Failed to decode JSON, skipping packet.")
            except Exception as e:
                print("Error while handling message:", e)
                break
        print(f"Received {count} messages!")
        output_file.close()

def handle_message(msg):
    print(f"Received packet with rssi: {msg['rssi']}")

    sf = get_spreadingfactor(msg.get("datr", ""))
    gateway = msg.get("gateway", "").replace(":", "").lower()
    device_id = msg.get("device_eui", msg.get("device_addr", "unknown")).lower()
    device_name = msg.get("device_name", "unknown")
    
    gw_info = gateway_info.get(gateway, ("unknown", None, None, None))
    energy_ms = toa_estimates_ms.get(sf, None)

    sensor_info = sensor_locations.get(device_id) if len(device_id) == 16 else "unknown"
    if sensor_info:
        print(f"Sensor Location: lat={sensor_info['lat']}, lon={sensor_info['lon']}, room={sensor_info['room']}")
    else:
        print("Sensor location not found.")

    print(f"Device: {device_name} ({device_id})")
    print(f"Spreading Factor: {sf}")
    print(f"Gateway: {gw_info[0]} at lat={gw_info[1]}, lon={gw_info[2]}")
    print(f"Estimated TOA: {energy_ms} ms\n")

    writer.writerow([
        device_id, device_name, sf, energy_ms,
        gw_info[0], gw_info[1], gw_info[2], msg['time'],
        sensor_info['lat'] if sensor_info else "unknown",
        sensor_info['lon'] if sensor_info else "unknown",
        sensor_info['room'] if sensor_info else "unknown"
    ])

def get_spreadingfactor(datr):
    if datr.startswith("SF"):
        return int(datr[2:].split("BW")[0])
    else:
        return None

receive_data()