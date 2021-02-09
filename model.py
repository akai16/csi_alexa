import pandas as pd
from pandas.tseries.offsets import DateOffset
import sys

if len(sys.argv) != 2:
    print("USAGE:\python3 extract_csi.py [PCAP_FILE]")
    sys.exit(1)

CSI_DATA_FILEPATH = sys.argv[1]

csiData = pd.read_csv(
    CSI_DATA_FILEPATH,

)

csiData['Timestamp'] = pd.to_datetime(csiData['Timestamp'], unit='s')
csiData.set_index('Timestamp', inplace=True)

# Function that implements aCSI variance metric
def meanACSIVariance(aCSIData, timeWindow=5):

    # Get Standard Deviantion for all subcarriers
    # along a time window
    ACSIVariance = aCSIData.rolling(
        f'{timeWindow}S', 
        closed='both',
    ).std()

    # Get the mean variance of all subcarriers
    meanACSIVariance = CSIVariance.mean(
        axis=1
    )

    return meanACSIVariance

