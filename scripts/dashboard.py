from pathlib import Path
import folium, rasterio as rio, numpy as np, pandas as pd, plotly.express as px

def build_dashboard(ndvi_dir: str, results_csv: str, out_html: str):
    ndvi_dir = Path(ndvi_dir); out = Path(out_html); out.parent.mkdir(parents=True, exist_ok=True)
    m = folium.Map(location=[-3.1,-60.0], zoom_start=6, tiles="CartoDB positron")

    # Overlays NDVI (até 6 para ficar leve)
    for tif in sorted(ndvi_dir.glob("*_ndvi.tif"))[:6]:
        with rio.open(tif) as ds:
            bounds = [[ds.bounds.bottom, ds.bounds.left],[ds.bounds.top, ds.bounds.right]]
            arr = ds.read(1).astype("float32")
            vis = (np.clip((arr + 0.2)/1.1, 0, 1)*255).astype("uint8")
            folium.raster_layers.ImageOverlay(vis, bounds=bounds, opacity=0.6, name=tif.stem).add_to(m)
    rcsv = Path(results_csv)
    if rcsv.exists():
        df = pd.read_csv(rcsv)
        if "prob" in df.columns:
            fig = px.histogram(df, x="prob", nbins=20, title="Distribuição de probabilidades (CNN)")
            folium.Marker(location=[-2.5,-59.5], tooltip="Distribuição de probabilidades",
                          popup=folium.IFrame(fig.to_html(include_plotlyjs='cdn'), width=500, height=350)).add_to(m)
    folium.LayerControl().add_to(m)
    m.save(out)
