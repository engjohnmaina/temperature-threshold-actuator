import machine
import dht
import socket
import json
import time

# Hardware GPIO Architecture Pin Configuration Matrices
dht_sensor = dht.DHT11(machine.Pin(4)) # DHT11 Sensor Data pin connected to GPIO 4
relay_pin = machine.Pin(5, machine.Pin.OUT) # Relay Control signal routed to GPIO 5

# Failsafe baseline boot state: Always make sure the relay is initialized off
relay_pin.value(0)

# Load the single-file HTML Dashboard layout directly into RAM buffer memory
try:
    with open("index.html", "r") as f:
        html_dashboard = f.read()
except Exception as e:
    print("Fatal Storage Interrupt: index.html file not found on local root filesystem.")
    html_dashboard = "<h1>Dashboard File Not Found</h1>"

# Configure local network socket channel listening architecture
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)
print("Socket background worker server initialized on port 80...")

while True:
    try:
        conn, addr = s.accept()
        request = conn.recv(1024).decode('utf-8')
        
        # Prevent completely blank browser polling request loops from crashing socket processing
        if not request:
            conn.close()
            continue
            
        request_line = request.split('\r\n')[0]
        method, url, _ = request_line.split(' ')

        # --- Endpoint 1: Stream Static HTML Dashboard Frontend UI Layout ---
        if method == "GET" and url == "/":
            conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n')
            conn.sendall(html_dashboard)
            
        # --- Endpoint 2: Telemetry Sensor JSON API Interface Data Array ---
        elif method == "GET" and url == "/api/sensors":
            try:
                dht_sensor.measure()
                t = dht_sensor.temperature()
                h = dht_sensor.humidity()
                
                payload = {"temperature": f"{t:.1f}", "humidity": f"{h:0.0f}"}
                response_data = json.dumps(payload)
                conn.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n')
                conn.send(response_data)
            except Exception as dht_error:
                print("Hardware Fault read warning: ", dht_error)
                conn.send('HTTP/1.1 500 Internal Server Error\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n')
                conn.send(json.dumps({"error": "Sensor processing read module failed"}))

        # --- Endpoint 3: Handle Incoming Closed-Loop Relay Commands via POST ---
        elif method == "POST" and url == "/api/relay":
            try:
                # Find the location where the JSON body begins inside the HTTP string request package
                body_start = request.find('\r\n\r\n') + 4
                json_body = request[body_start:]
                
                data = json.loads(json_body)
                relay_state = data.get("relayState", False)
                
                # Update physical hardware GPIO register voltage channel state directly
                relay_pin.value(1 if relay_state else 0)
                print(f"Closed-loop automation execution payload parsed. Driving GPIO 5: {relay_pin.value()}")
                
                conn.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n')
                conn.send(json.dumps({"status": "Success"}))
            except Exception as json_err:
                conn.send('HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n')

        # Fallback 404 Route handling invalid address routes smoothly
        else:
            conn.send('HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\nRoute undefined.')
            
        conn.close()
        
    except Exception as server_loop_error:
        print("Network Socket Stream processing fault dropped:", server_loop_error)
