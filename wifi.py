import network
import time

ap_ssid = "iot_device"
ap_password = "i0tdevice"
ap_authmode = 3  # WPA2

NETWORK_PROFILES = 'wifi.dat'
wlan = network.WLAN(network.STA_IF)    

def do_connect(ssid, password):
    
    wlan.active(True)
    if wlan.isconnected():
        return None    
    wlan.config(dhcp_hostname="iot-controller")
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(ssid, password)
        for retry in range(100):
            connected = wlan.isconnected()
            if connected:
                break
            time.sleep(0.1)
            print('.', end='')
        if connected:
            print('\nConnected. Network config: ', wlan.ifconfig())
        else:
            print('\nFailed. Not Connected to: ' + ssid)        
        return connected

def setup_AP():    
  wlan_ap = network.WLAN(network.AP_IF)
  wlan_ap.active(True)
  wlan_ap.config(essid=ap_ssid, password=ap_password, authmode=ap_authmode)
  print('Connection successful')
  print(wlan_ap.ifconfig())



def read_profiles():
    with open(NETWORK_PROFILES) as f:
        lines = f.readlines()
    profiles = {}
    for line in lines:
        ssid, password = line.strip("\n").split(";")
        profiles[ssid] = password
    return profiles


def write_profiles(profiles):
    print("write config")
    print(profiles)
    lines = []
    for ssid, password in profiles.items():
        lines.append("%s;%s\n" % (ssid, password))
    with open(NETWORK_PROFILES, "w") as f:
        f.write(''.join(lines))


def setup_wifi():
  try:
    profiles = read_profiles()
  except OSError:
    profiles = {}
  if len(profiles) > 0 :
     print(profiles)
     connected = False
     time.sleep(3)
     if wlan.isconnected() :
        return
     # Search WiFis in range
     wlan.active(True)
     networks = wlan.scan()
     AUTHMODE = {0: "open", 1: "WEP", 2: "WPA-PSK", 3: "WPA2-PSK", 4: "WPA/WPA2-PSK"}
     for ssid, bssid, channel, rssi, authmode, hidden in sorted(networks, key=lambda x: x[3], reverse=True):
        ssid = ssid.decode('utf-8')
        encrypted = authmode > 0
        print("ssid: %s chan: %d rssi: %d authmode: %s" % (ssid, channel, rssi, AUTHMODE.get(authmode, '?')))
        if encrypted:
          if ssid in profiles:
            password = profiles[ssid]
            connected = do_connect(ssid, password)
          else:
            print("skipping unknown encrypted network")
        else:  # open
          connected = do_connect(ssid, None)
        if connected:
          break
  else:
    print("no config, setup AP")
    setup_AP()

  
