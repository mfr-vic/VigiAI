from __future__ import annotations
from pathlib import Path
import json, os, time, logging
import ee

log = logging.getLogger(__name__)


def _init_ee():
    """Inicializa o EE usando a variável EE_PROJECT_ID."""
    proj = os.environ.get("EE_PROJECT_ID", None)
    ee.Initialize(project=proj)
    log.info("[EE] Initialize(project='%s') OK", proj)


def _geometry_from_inputs(aoi_geojson=None, bbox=None):
    """
    Constrói ee.Geometry a partir de um arquivo GeoJSON OU bbox [minLon, minLat, maxLon, maxLat].
    Usa 'geodesic=False' no Rectangle para evitar 'crs: False'.
    """
    if aoi_geojson:
        p = Path(aoi_geojson)
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            geom = ee.Geometry(data["features"][0]["geometry"])
            return geom
        try:
            data = json.loads(str(aoi_geojson))
            geom = ee.Geometry(data["features"][0]["geometry"])
            return geom
        except Exception:
            pass

    if bbox and len(bbox) == 4:
        # geodesic=False evita bugs de 'crs' booleano
        return ee.Geometry.Rectangle(bbox, None, False)

    raise ValueError("Forneça 'aoi_geojson' válido ou 'bbox' [minLon, minLat, maxLon, maxLat].")


def _make_export_task(img, geom, description: str, folder: str, scale: int):
    """
    Gera tarefa de Export.image.toDrive com GEO_TIFF + cloudOptimized.
    (Sem 'compress', pois não é aceito em toDrive → evita erro 'Unknown file format options'.)
    """
    params = {
        "image": img.toInt16(),
        "description": description,
        "folder": folder,
        "fileNamePrefix": description,
        "scale": int(scale),
        "region": geom,
        "crs": "EPSG:4326",
        "maxPixels": 1_000_000_000_000,
        "fileFormat": "GEO_TIFF",
        "formatOptions": {"cloudOptimized": True},
    }
    return ee.batch.Export.image.toDrive(**params)


def _wait_for(tasks):
    """Espera tarefas do EE finalizarem."""
    states_done = {"COMPLETED", "FAILED", "CANCELLED"}
    while True:
        done = 0
        for t in tasks:
            s = t.status()
            st = s.get("state")
            if st in states_done:
                done += 1
        log.info("[EE] Progresso: %d/%d finalizadas.", done, len(tasks))
        if done == len(tasks):
            break
        time.sleep(5)


# ---------- Export: tiles ----------

def download_sentinel_tiles_via_drive(
    aoi_geojson=None,
    bbox=None,
    start_date=None,
    end_date=None,
    collection="COPERNICUS/S2_SR_HARMONIZED",
    cloud_filter=50,
    drive_folder="VigiAI",
    max_tiles=6,
    export_scale=20,
    out_dir="data/raw",
    wait_for_tasks=True,
):
    """
    Filtra coleção Sentinel-2, ordena por nuvem, limita em 'max_tiles' e exporta cada imagem.
    Baixa B4/B8 (int16) recortadas ao AOI. Se 'wait_for_tasks' True, fica aguardando.
    """
    _init_ee()
    geom = _geometry_from_inputs(aoi_geojson, bbox)

    col = (ee.ImageCollection(collection)
           .filterDate(start_date, end_date)
           .filterBounds(geom)
           .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", int(cloud_filter)))
           .sort("CLOUDY_PIXEL_PERCENTAGE"))

    # Deixa para o export (mais leve).
    imgs = col.limit(int(max_tiles))
    count = imgs.size().getInfo()
    log.info("[EE] Imagens candidatas (após filtros/ordenação): %s", count)

    tasks = []
    for i in range(int(count)):
        img = ee.Image(imgs.toList(count).get(i)).select(["B4", "B8"]).clip(geom).toInt16()
        desc = f"vigiai_tile_{i:04d}"
        task = _make_export_task(img, geom, desc, drive_folder, int(export_scale))
        task.start()
        tasks.append(task)

    log.info("[EE] %d tarefas submetidas para a pasta do Drive: '%s' (scale=%s m)", len(tasks), drive_folder, export_scale)

    if wait_for_tasks and tasks:
        _wait_for(tasks)

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    return int(count)


# ---------- Export: mosaico ----------

def download_mosaic_via_drive(
    aoi_geojson=None,
    bbox=None,
    start_date=None,
    end_date=None,
    collection="COPERNICUS/S2_SR_HARMONIZED",
    cloud_filter=20,
    drive_folder="VigiAI",
    export_scale=30,
    description="vigiai_tile_mosaic",
    wait_for_task=False,
):
    """
    Baixa 1 mosaico (median) com bandas B4/B8 (demonstração rápida).
    """
    _init_ee()
    geom = _geometry_from_inputs(aoi_geojson, bbox)

    col = (ee.ImageCollection(collection)
           .filterDate(start_date, end_date)
           .filterBounds(geom)
           .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", int(cloud_filter))))

    img = col.select(["B4", "B8"]).median().clip(geom).toInt16()
    task = _make_export_task(img, geom, description, drive_folder, int(export_scale))
    task.start()
    log.info("[EE] 1 tarefa (mosaico) submetida para o Drive: '%s' (scale=%s m)", drive_folder, export_scale)

    if wait_for_task:
        _wait_for([task])

    return 1
