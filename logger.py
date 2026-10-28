import machine
import dht
import time
import gc

dht_sensor = dht.DHT11(machine.Pin(4))

LOG_FILE = "data.log"
INTERVAL_FILE = "interval.txt"
LOG_INTERVAL = 60

def load_interval():
    global LOG_INTERVAL
    try:
        with open(INTERVAL_FILE, "r") as f:
            LOG_INTERVAL = int(f.read().strip())
        print(f"File: Loaded logging interval: {LOG_INTERVAL}s")
    except Exception:
        print("File: Using default interval baseline: 60s")
    return LOG_INTERVAL

def save_interval(new_seconds):
    global LOG_INTERVAL
    if new_seconds < 5:
        new_seconds = 5  
    LOG_INTERVAL = new_seconds
    try:
        with open(INTERVAL_FILE, "w") as f:
            f.write(str(LOG_INTERVAL))
    except OSError:
        pass
    return LOG_INTERVAL

def execute_background_log():
    try:
        gc.collect()
        dht_sensor.measure()
        t = dht_sensor.temperature()
        h = dht_sensor.humidity()
        
        current_time_struct = time.localtime()
        
        hour = current_time_struct[3]
        minute = current_time_struct[4]
        second = current_time_struct[5]
        
        timestamp = f"{hour:02d}:{minute:02d}:{second:02d}"
        log_entry = f"{timestamp},{t:.1f},{h:0.0f}\n"
        
        f = open(LOG_FILE, "a")
        f.write(log_entry)
        f.flush()
        f.close()
        
        print(f" Automated background log saved: {log_entry.strip()}")
        return t, h
    except Exception as e:
        print("Storage logging error skipped:", e)
        return None, None
