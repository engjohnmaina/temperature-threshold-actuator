import gc
import network
import secrets
import time

gc.collect()

USE_ACCESS_POINT_MODE = True 

def initialize_network():
    if USE_ACCESS_POINT_MODE:
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=secrets.AP_SSID, password=secrets.AP_PASS, security=3)
        
        print("\nLocal Node Network Generation Successful!")
        print("SSID Broadcast Name:  ", secrets.AP_SSID)
        print("Node Gateway IP:      ", ap.ifconfig())
        print("Connect your device to this Wi-Fi network!\n")
    else:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        print(f"Scanning for home network router: {secrets.WIFI_SSID}...")
        wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASS)
        
        connection_timeout = 20  
        start_time = time.time()
        while not wlan.isconnected():
            if time.time() - start_time > connection_timeout:
                print("\n[CRITICAL ERROR]: Wi-Fi link authentication timeout.")
                break
            print(".", end="")
            time.sleep(0.5)
            
        if wlan.isconnected():
            print("\n NETWORK INTERFACE PROFILE ACQUIRED SUCCESS")
            print(" Local Target IPv4 Address:", wlan.ifconfig())
            print(" Open your browser and type that IP address in!\n")

initialize_network()
gc.collect()

