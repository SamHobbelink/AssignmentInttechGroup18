from websockets.sync.client import connect
import json
import csv
from fractions import Fraction

avg_voltage_V = 3.3
avg_current_A = 0.038

sensor_locations = {}
with open("sensor_locations.csv", newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        eui = row["Sensor_Eui"].replace(":", "").lower()
        if len(eui) == 16:
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
    "device_id", "device_name", "spreading_factor", "bandwidth_kHz", "coding_rate",
    "size_bytes", "bitrate_bps", "toa_ms", "energy_kWh", "energy_euros", "timestamp",
    "sensor_lat", "sensor_lon", "sensor_room"
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
            except:
                msg = None
        print(f"Received {count} messages!")
        output_file.close()

def handle_message(msg):
    print(f"Received packet with rssi: {msg.get('rssi', 'N/A')}")

    sf = get_spreadingfactor(msg.get("datr", ""))
    bw = get_bandwidth(msg.get("datr", ""))
    device_id = msg.get("device_eui", msg.get("device_addr", "unknown")).lower()
    coding_rate = msg.get("codr", "")
    msg_size = msg.get("size", "")
    device_name = msg.get("device_name", "unknown")
    coding_rate_val = float(Fraction(coding_rate))
    bitrate = ((sf) * (bw*1000)/2**sf) * coding_rate_val

    toa_ms = ((msg_size * 8)/float(bitrate)) * 1000
    energy_kWh = estimate_energy_kWh(toa_ms)
    energy_eur = energy_kWh * 0.24 # current price of a kWh in NL is 24 cents

    sensor_info = sensor_locations.get(device_id) if len(device_id) == 16 else "unknown"
    if sensor_info:
        print(f"Sensor Location: lat={sensor_info['lat']}, lon={sensor_info['lon']}, room={sensor_info['room']}")
    else:
        print("Sensor location not found.")

    print(f"Device: {device_name} ({device_id})")
    print(f"Spreading Factor: {sf}")
    print(f"Bandwidth: {bw} kHz")
    print(f"Coding rate: {coding_rate}")
    print(f"Message size: {msg_size} bytes")
    print(f"Bitrate: {bitrate} bps")
    print(f"Time-on-air: {toa_ms} ms")
    print(f"Energy consumed: {energy_kWh} kWh")
    print(f"Estimated transmission energy cost: {energy_eur} euros\n")

    writer.writerow([
        device_id, device_name, sf, bw, coding_rate,
        msg_size, bitrate, toa_ms, energy_kWh, energy_eur, msg['time'],
        sensor_info['lat'] if sensor_info else "unknown",
        sensor_info['lon'] if sensor_info else "unknown",
        sensor_info['room'] if sensor_info else "unknown"
    ])

def get_spreadingfactor(datr):
    if datr.startswith("SF"):
        return int(datr[2:].split("BW")[0])
    else:
        return None
    
def get_bandwidth(datr):
    if "BW" in datr:
        return int(datr.split("BW")[1])
    else:
        return None
    
def estimate_energy_kWh(toa_ms):
    if toa_ms is None:
        return None
    return (avg_voltage_V * avg_current_A * toa_ms) / 3600000000

receive_data()