import plotly.express as px
import pandas as pd
import sys

if len(sys.argv) != 2:
    print("USAGE:\python3 plot_csi.py [CSV_FILE]")
    sys.exit(1)

CSI_CSV = sys.argv[1]
csiDF = pd.read_csv(CSI_CSV)
csiDF['Timestamp'] = pd.to_datetime(csiDF['Timestamp'], unit='s')
csiDF.set_index('Timestamp', inplace=True)

subcarriers = csiDF.iloc[:,2:]
fig = px.imshow(subcarriers[subcarriers < 5000].dropna())
fig.show()