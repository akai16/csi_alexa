import dpkt
import pandas as pd
import numpy as np
import sys

if len(sys.argv) != 2:
    print("USAGE:\python3 extract_csi.py [PCAP_FILE]")
    sys.exit(1)

# Open PCAP file and read
PCAP_FILE = sys.argv[1]
pcapFile = open(PCAP_FILE, 'rb')
csiFile = dpkt.pcap.Reader(pcapFile)

csiNumbers = []
aCSIList = []
# Parse data
for timestamp, buf in csiFile:

    eth = dpkt.ethernet.Ethernet(buf) # Ethernet Packet
    ip = eth.data # IP Packet
    udp = ip.data # UDP Packet

    # Parse Payload
    magicBytes = udp.data[0:4]
    srcMac = udp.data[4:10].hex()
    frameSeq = udp.data[10:12]
    core = udp.data[12:13]
    nss = udp.data [13:14]
    chanspec = udp.data[14:16]
    chipVersion = udp.data[16:18]

    csiData = udp.data[18: (64 * 4) + 18]   # For 20 MHz wide channels
    # csiData = udp.data[18: (128 * 4) + 18] # For 40 MHz wide channels
    # csiData = udp.data[18: (256 * 4) + 18] # For 80 MHz wide channels

    csiData = [ csiData[i:i+4] for i in range(0, len(csiData), 4) ]
    csi = [ 
        np.frombuffer(
            data, 
            dtype=np.int16,
            count=2
        )
        for data in csiData
    ]

    aCSI = [ 
        r + 1j * i
        for r, i in csi 
    ]

    aCSI = np.abs(np.fft.fftshift(aCSI))

    aCSIList.append([timestamp, srcMac, frameSeq] + list(aCSI))
    csiNumbers.append(csi)


# aCSI = np.abs(np.fft.fftshift(csiDF, axes=(1,)))

csiDF = pd.DataFrame(
    aCSIList,
    columns=[
        'Timestamp', 
        'MAC', 
        'Frame', 
        *[ i - 32 for i in range(64) ]
    ]
)


# Drop pilot carriers and null carriers
# Those have arbitrary values and should be put away
null_carriers = [-32, -31, -30, -29, 0, 29, 30, 31]
pilot_carriers = [-21, -7, 7, 21]

csiDF.drop(null_carriers, axis=1, inplace=True)
csiDF.drop(pilot_carriers, axis=1, inplace=True)

csiDF.to_csv(f'{PCAP_FILE}.csv', index=False)
pcapFile.close() 