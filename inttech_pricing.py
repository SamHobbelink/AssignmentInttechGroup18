from websockets.sync.client import connect
import json

def receive_data():
    max_msg = 10 # Feel free to change this or just let it loop forever. Maybe best to keep it low while testing...
    with connect("ws://192.87.172.71:1337") as websocket:
        count = 0
        while count < max_msg:
            msg = websocket.recv()
            try:
                msg = json.loads(msg)
                handle_message(msg)
            except json.JSONDecodeError:
                print("Failed to decode json, assuming next packet will be ok...")
                pass
            except Exception as e:
                print("Something went horribly wrong!")
                print("Error:", e)
                break
            
            count += 1
        print("Received %d messages!" % count)

def handle_message(msg):
    print("Received packet with rssi: %d." % msg['rssi'])
    print(msg)
    if 'device_eui' in msg:
        print("This is a known device!")
        print("Device name: ", msg['device_name'])
    print()

receive_data()