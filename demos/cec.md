# CEC tests

## Connection info

Raspberry Pi host: 10.0.50.128

## Resources

- [cec-utl manpage](https://manpages.debian.org/bookworm/v4l-utils/cec-ctl.1.en.html)
- [cec-client manpage](https://manpages.debian.org/bookworm/cec-utils/cec-client.1.en.html)
- [CEC-O-MATIC](https://www.cec-o-matic.com/)
- [Using HDMI-CEC on a Raspberry Pi](https://pimylifeup.com/raspberrypi-hdmi-cec)
- [A Comprehensive Review of HDMI-CEC and the cec-ctl Command](https://utdream.org/a-comprehensive-review-of-hdmi-cec-and-the-cec-ctl-command/)


## Commands

Connect to the Raspberry Pi via SSH:

```bash
ssh kenneth@comando.adeptweb.dk
```

### cec-ctl

```bash
sudo apt install v4l-utils

# Configure device (RPi)
cec-ctl --playback

# List devices
cec-ctl -s -S
# 2.1.0.0 is Apple TV
# 2.4.0.0 is Raspberry Pi

# Turn on/standby TV
cec-ctl -t0 --image-view-on
cec-ctl -t0 --standby

# Switch to Apple TV
cec-ctl --active-source phys-addr=2.1.0.0

# Switch to Raspberry Pi
cec-ctl --active-source phys-addr=2.4.0.0
```

### cec-client

```bash
sudo apt install libcec-dev

# Perform scan and list devices
echo 'scan' | cec-client -s -d 1

# Turn on device
echo 'on 0.0.0.0' | cec-client -s -d 1
```
