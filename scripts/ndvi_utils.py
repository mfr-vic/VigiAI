from __future__ import annotations
from pathlib import Path
import numpy as np, rasterio as rio
from skimage.filters import gaussian
from tqdm import tqdm


def _ensure_dir(p: str|Path) -> Path:
    p = Path(p); p.mkdir(parents=True, exist_ok=True); return p


def _auto_scale_reflectance(band: np.ndarray) -> np.ndarray:
    if np.nanmax(band) > 2:
        band = band.astype("float32") * 1e-4
    return np.clip(band, 0.0, 1.0)


def compute_ndvi_from_tif(tif_path: Path, out_tif: Path) -> None:
    with rio.open(tif_path) as ds:
        b4 = ds.read(1).astype("float32")
        b8 = ds.read(2).astype("float32")
        transform, crs = ds.transform, ds.crs
    b4 = _auto_scale_reflectance(b4)
    b8 = _auto_scale_reflectance(b8)
    ndvi = (b8 - b4) / (b8 + b4 + 1e-6)
    ndvi = np.clip(gaussian(ndvi, sigma=0.6, preserve_range=True), -1.0, 1.0).astype("float32")
    profile = {"driver":"GTiff","height":ndvi.shape[0],"width":ndvi.shape[1],"count":1,"dtype":"float32","crs":crs,"transform":transform,"compress":"lzw"}
    with rio.open(out_tif, "w", **profile) as dst: dst.write(ndvi, 1)


def batch_compute_ndvi(raw_dir: str|Path, ndvi_dir: str|Path, processed_dir: str|Path) -> int:
    raw_dir = Path(raw_dir); ndvi_dir = _ensure_dir(ndvi_dir); _ensure_dir(processed_dir)
    tifs = sorted(list(raw_dir.glob("*.tif")) + list(raw_dir.glob("*.tiff")))
    for tif in tqdm(tifs, desc="NDVI"):
        out = ndvi_dir / (tif.stem + "_ndvi.tif")
        compute_ndvi_from_tif(tif, out)
    return len(tifs)
