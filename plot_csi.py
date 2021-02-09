import plotly.express as px
import pandas as pd

CSI_CSV = 'example.pcap.csv'
csiDF = pd.read_csv(CSI_CSV)

fig = px.imshow(csiDF.iloc[:,3:])
fig.show()