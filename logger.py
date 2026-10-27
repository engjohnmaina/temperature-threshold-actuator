import machine
import dht
import time

dht_sensor = dht.DHT11(machine.Pin(4))

LOG_FILE = "data.log"
INTERVAL_FILE = "interval.txt"

# Default interval config state
LOG_INTERVAL = 60

def load_interval():
    global LOG_INTERVAL
    try:
        with open(INTERVAL_FILE, "r") as f:
            LOG_INTERVAL = int(f.read().strip())
        print(f"📁 Loaded logging interval: {LOG_INTERVAL}s")
    except Exception:
        print("📁 Using default interval baseline: 60s")
    return LOG_INTERVAL

def save_interval(new_seconds):
    global LOG_INTERVAL
    if new_seconds < 5:
        new_seconds = 5  # Protect flash memory from aggressive wear
    LOG_INTERVAL = new_seconds
    with open(INTERVAL_FILE, "w") as f:
        f.write(str(LOG_INTERVAL))
    return LOG_INTERVAL

def execute_background_log():
    """Reads sensor measurements and appends directly to the flash storage log file."""
    try:
        dht_sensor.measure()
        t = dht_sensor.temperature()
        h = dht_sensor.humidity()
        
        uptime_m, uptime_s = divmod(time.time(), 60)
        uptime_h, uptime_m = divmod(uptime_m, 60)
        timestamp = f"{uptime_h:02d}:{uptime_m:02d}:{uptime_s:02d}"
        
        log_entry = f"{timestamp},{t:.1f},{h:0.0f}\n"
        
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
        print(f"📍 Automated background log saved: {log_entry.strip()}")
        return t, h
    except Exception as e:
        print("Storage logging error skipped:", e)
        return None, None

