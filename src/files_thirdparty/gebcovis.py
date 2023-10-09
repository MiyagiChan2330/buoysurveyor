import plotly.graph_objects as go
import pandas as pd
import numpy as np
# Read data from a csv
z_data = pd.read_csv('elevation.csv')
z = z_data.values
sh_0, sh_1 = z.shape
x, y = np.linspace(12, 120, sh_0), np.linspace(15, 125, sh_1)
fig = go.Figure(data=[go.Surface(z=z, x=x, y=y)])
fig.update_traces(contours_z=dict(show=True, usecolormap=True,
                                  highlightcolor="limegreen", project_z=True))
fig.update_layout(title='Balayan Bay Depth',xaxis_title="Latitude", 
                  yaxis_title="Longitude",autosize=False,
                  width=1920, height=1080, 
                  margin=dict(l=65, r=50, b=65, t=90))
fig.update_layout(scene = dict(
                    xaxis_title='Latitude',
                    yaxis_title='Longitude',
                    zaxis_title='Elevation'),
                    margin=dict(r=20, b=10, l=10, t=10))  
# fig.update_layout(color='Elevation')
fig.update_layout(coloraxis_colorbar=dict(
    title="Elevation",
    thicknessmode="pixels", thickness=50,
    lenmode="pixels", len=200,
    yanchor="top", y=1,
    ticks="outside", ticksuffix="",
    dtick=5
))
fig.show()