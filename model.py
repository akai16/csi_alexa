import pandas as pd
from itertools import combinations
import plotly.express as px
from plotly.io import write_image
import plotly.graph_objects as go
import numpy as np
import pywt
import sys

if len(sys.argv) != 2:
    print("USAGE:\python3 extract_csi.py [PCAP_FILE]")
    sys.exit(1)

CSI_DATA_FILEPATH = sys.argv[1]

csiData = pd.read_csv(CSI_DATA_FILEPATH)

csiData['Timestamp'] = pd.to_datetime(csiData['Timestamp'], unit='s')
csiData.set_index('Timestamp', inplace=True)

def calculateACSIVariance(aCSIData, timeWindow=5):
    """
    Function that implements aCSI variance metric
    """

    # Get Standard Deviation for all subcarriers along a time window
    aCSIVariance = aCSIData.rolling(
        f'{timeWindow}S', 
        closed='both',
    ).std()

    return aCSIVariance.dropna()


def outlierFiltering(aCSIDataVariance):
    """
    Function for removing outliers by only including
    subcarriers whose aCSI variance sequences are highly correlated.
    The set of subcarriers used are the top 50% most correlated pairs.
    """

    # Make a list of combination pairs of all subcarriers
    combinationList = list(combinations(aCSIDataVariance.columns, 2))

    correlationPairs = []
    for combination in combinationList:

        correlation = np.corrcoef(
            aCSIDataVariance[combination[0]],
            aCSIDataVariance[combination[1]]
        )

        correlationPairs.append((combination, correlation[0][1]))
    
    correlationPairs = sorted(correlationPairs, key=lambda x: x[1], reverse=True)

    # Get Top 50% most highly correlated
    subcarriers = set()
    for pair, correlation in correlationPairs[:len(correlationPairs)//2]:
        subcarriers.add(pair[0])
        subcarriers.add(pair[1])

    return aCSIDataVariance[list(subcarriers)].copy()


def dwtDenoising(csiData):
    """
    Denoise CSI reported by the firmaware using DWT (Discrete Wavelet Transform)
    """
    # Number of decomposition levels
    W = 3

    decompositionCoef = []
    for i in range(W): 
        
        if i == 0:
            csi = csiData.iloc[:, 2:]
        else:
            csi = approximationCoef

        # Apply DWT to subcarriers
        approximationCoef, detailCoef = pywt.dwt(csi, 'db8', mode='constant')
        detailCoef = pd.DataFrame(detailCoef)
        approximationCoef = pd.DataFrame(approximationCoef)
        
        # For the first decomposition level, we estimate threshold value
        if i == 0:
            # Noise standard deveiation
            noiseStd = np.median(np.abs(detailCoef), axis=1) / 0.6745
            
            # Universal threshold
            threshold = noiseStd * np.sqrt(2 * np.log10(len(detailCoef)))

        # Apply threshold
        thresholdSmallerMask = detailCoef.transform(lambda x: np.abs(x) < threshold)
        thresholdGreaterMask = detailCoef.transform(lambda x: np.abs(x) >= threshold)
        isPositiveMask = detailCoef.transform(lambda x: x >= 0)
        isNegativeMask = detailCoef.transform(lambda x: x < 0)

        detailCoef[thresholdSmallerMask] = 0
        detailCoef[thresholdGreaterMask & isPositiveMask] = detailCoef[thresholdGreaterMask & isPositiveMask].sub(threshold, axis=0)
        detailCoef[thresholdGreaterMask & isNegativeMask] = detailCoef[thresholdGreaterMask & isNegativeMask].add(threshold, axis=0)

        decompositionCoef.append((approximationCoef, detailCoef))

    for i in range(W):
        aC, dC = decompositionCoef.pop()
        if i == 0:
            signal = aC
        signal = pywt.idwt(signal, dC, 'db8', mode='constant')

    return signal

# Denoise CSI with DWT
# denoisedCSIData = dwtDenoising(csiData)

# Get aCSI variance along a time window
aCSIDataVariance = calculateACSIVariance(csiData)

# Apply outlier filtering
aCSIDataVariance = outlierFiltering(aCSIDataVariance)


meanACSIDataVariance = aCSIDataVariance.mean(axis=1)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=aCSIDataVariance.index,
    y=meanACSIDataVariance.values,
))
fig.update_layout(
    title=CSI_DATA_FILEPATH,
    xaxis_title="Time",
    yaxis_title="aCSI",
    font=dict(
        size=18,
    )
)

fig.show()