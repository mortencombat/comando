import time

from comando.helpers.itach import iTach

dev = iTach("10.0.30.61")

# It seems either the Flex or (most likely) the SC-LX71 is very particular/erratic about responding to commands sent via TCP. For example, ?P does not seem to work when the device is in standby.

# power status
print(dev.send("?P"))

# power off
# print(dev.send("PF"))

# power on
# print(dev.send(["PO"] * 3))


# s.send(b"PF\r")
# s.send(b"PO\r" * 10)
# for i in range(2):
#     s.send(b"PO\r")
#     print(f"sent {i}")
#     time.sleep(0.1)

# import time

# import httpx

# NOTE: it seems that the REST API only supports sending commands, not receiving responses
# This is okay for my use case, as it will just be used to power the SC-LX71 on and off.

# Consider if TCP API implementation is easy enough, and consider using that instead:
# https://www.globalcache.com/files/docs/api-gc-unifiedtcp.pdf

# To power on the SC-LX71, the power on command needs to be sent multiple times in quick succession
# for i in range(10):
#     r = httpx.post("http://10.0.30.61/api/host/modules/1/ports/1/data", content=b"PO\r")
#     time.sleep(0.1)

# r = httpx.post("http://10.0.30.61/api/host/modules/1/ports/1/data", content=b"PF\r")
# r = httpx.post("http://10.0.30.61/api/host/modules/1/ports/1/data", content=b"?V\r")

# print(r)
# print(r)
