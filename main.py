import machine
import socket
import json
import time
import gc
import os
import logger 

relay_pin = machine.Pin(5, machine.Pin.OUT)
relay_pin.value(0)  

last_log_time = 0
current_interval = logger.load_interval()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 80))
s.listen(2)

print("Modular Web Server fully operational on port 80...")

while True:
    conn = None
    try:
        gc.collect()
        s.settimeout(1.0) 
        
        if time.time() - last_log_time >= current_interval:
            logger.execute_background_log()
            last_log_time = time.time()
            
        try:
            conn, addr = s.accept()
        except OSError:
            continue  
            
        conn.settimeout(2.5)
        
        request_bytes = b""
        while b"\r\n\r\n" not in request_bytes and len(request_bytes) < 2048:
            chunk = conn.recv(512)
            if not chunk: break
            request_bytes += chunk
            
        if not request_bytes:
            conn.close()
            continue

        request_text = request_bytes.decode('utf-8', 'ignore')
        request_lines = request_text.split('\r\n')
        parts = request_lines[0].split(' ')
        if len(parts) < 2:
            conn.close()
            continue
        method, url = parts[0], parts[1]

        if method == "GET" and url == "/":
            conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n')
            try:
                with open("index.html", "r") as f:
                    html_content = f.read()
                
                with open("styles.css", "r") as f:
                    css_content = f.read()
                html_content = html_content.replace('<link rel="stylesheet" href="styles.css" />', f'<style>{css_content}</style>')
                
                with open("dashboard.js", "r") as f:
                    js_content = f.read()
                html_content = html_content.replace('<script src="dashboard.js"></script>', f'<script>{js_content}</script>')
                
                for i in range(0, len(html_content), 256):
                    conn.send(html_content[i:i+256])
                    
            except Exception as stream_err:
                print("Modular frontend assembly compilation error:", stream_err)
                conn.send("<h1>Dashboard Component Compilation Error</h1>")

        elif method == "GET" and url == "/api/sensors":
            try:
                logger.dht_sensor.measure()
                payload = {
                    "temperature": f"{logger.dht_sensor.temperature():.1f}", 
                    "humidity": f"{logger.dht_sensor.humidity():0.0f}",
                    "currentInterval": current_interval
                }
                conn.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n')
                conn.send(json.dumps(payload))
            except Exception:
                conn.send('HTTP/1.1 500 Internal Server Error\r\n\r\n')

        elif method == "GET" and url == "/api/history":
            conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n')
            try:
                with open(logger.LOG_FILE, "r") as f:
                    while True:
                        chunk = f.read(256)
                        if not chunk: break
                        conn.send(chunk)
            except OSError:
                conn.send("")

        elif method == "GET" and url == "/api/download":
            conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/csv\r\nContent-Disposition: attachment; filename=esp32_data.csv\r\nConnection: close\r\n\r\n')
            conn.send("Timestamp,Temperature_C,Humidity_Percent\n")
            try:
                with open(logger.LOG_FILE, "r") as f:
                    while True:
                        chunk = f.read(256)
                        if not chunk: break
                        conn.send(chunk)
            except OSError:
                pass

        elif method == "POST" and url == "/api/relay":
            try:
                content_length = 0
                for line in request_lines:
                    if line.lower().startswith("content-length:"):
                        content_length = int(line.split(":")[1].strip())
                        break
                body = request_text.split('\r\n\r\n')[1] if len(request_text.split('\r\n\r\n')) > 1 else ""
                while len(body) < content_length:
                    body += conn.recv(256).decode('utf-8', 'ignore')
                
                data = json.loads(body)
                relay_state = data.get("relayState", False)
                relay_pin.value(1 if relay_state else 0)
                
                conn.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n')
                conn.send(json.dumps({"status": "Success", "relayState": relay_state}))
            except Exception:
                conn.send('HTTP/1.1 400 Bad Request\r\n\r\n')

        elif method == "POST" and url == "/api/interval":
            try:
                content_length = 0
                for line in request_lines:
                    if line.lower().startswith("content-length:"):
                        content_length = int(line.split(":")[1].strip())
                        break
                body = request_text.split('\r\n\r\n')[1] if len(request_text.split('\r\n\r\n')) > 1 else ""
                while len(body) < content_length:
                    body += conn.recv(256).decode('utf-8', 'ignore')
                
                data = json.loads(body)
                current_interval = logger.save_interval(int(data.get("interval", 60)))
                
                conn.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n')
                conn.send(json.dumps({"status": "Success", "interval": current_interval}))
            except Exception:
                conn.send('HTTP/1.1 400 Bad Request\r\n\r\n')

        elif method == "POST" and url == "/api/sync-time":
            try:
                content_length = 0
                for line in request_lines:
                    if line.lower().startswith("content-length:"):
                        content_length = int(line.split(":")[1].strip())
                        break
                body = request_text.split('\r\n\r\n')[1] if len(request_text.split('\r\n\r\n')) > 1 else ""
                while len(body) < content_length:
                    body += conn.recv(256).decode('utf-8', 'ignore')
                
                payload = json.loads(body)
                epoch_sec = int(payload.get("epoch", 0))
                
                if epoch_sec > 0:
                    t = time.localtime(epoch_sec)
                    rtc = machine.RTC()
                    rtc.init((t[0], t[1], t[2], t[3], t[4], t[5], 0, 0))
                    last_log_time = time.time()
                
                conn.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n')
                conn.send(json.dumps({"status": "Success", "synced": True}))
            except Exception as time_err:
                print("Time sync parsing error:", time_err)
                conn.send('HTTP/1.1 400 Bad Request\r\n\r\n')

        elif method == "POST" and url == "/api/clear":
            try: 
                with open(logger.LOG_FILE, "w") as f:
                    f.write("")
            except OSError: 
                pass
            conn.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n')
            conn.send(json.dumps({"status": "Log Wiped Clean"}))

        else:
            conn.send('HTTP/1.1 404 Not Found\r\n\r\n')
        
        conn.close()

    except Exception as e:
        print("Server execution reset tick:", e)
        if conn:
            try: conn.close()
            except: pass

