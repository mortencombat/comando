
# Raspberyy Pi Zero 2 W

## Setup

1. Use Raspberry Pi Imager to flash SD card with Raspberry Pi OS Lite 64-bit

## WLAN troubleshooting

Run WLAN configuration: `sudo nmtui`
Ping AP: `ping -c 100 10.0.50.1`
WLAN information: `iwconfig`
Show WLAN log: `journalctl -b | grep wlan0`
Prevent package/firmware update: `sudo apt-mark hold firmware-brcm80211`
Disable power management: `sudo iw wlan0 set power_save off`

https://forums.raspberrypi.com/viewtopic.php?p=2155599#p2155599
https://forums.raspberrypi.com/viewtopic.php?p=2155599#p2155599
