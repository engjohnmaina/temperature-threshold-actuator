import network
import time
import secrets

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Initializing Network station configuration link...")
        wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASS)
        
        # Connection timeout handler loop
        timeout = 0
        while not wlan.isconnected() and timeout < 20:
            time.sleep(0.5)
            print(".", end="")
            timeout += 1
            
    if wlan.isconnected():
        print("\nWi-Fi network connection successfully established.")
        print("Node IP Designation Setup Matrix:", wlan.ifconfig()[0])
    else:
        print("\nNetwork Fault: Timeout connection limit breached.")

connect_wifi()
