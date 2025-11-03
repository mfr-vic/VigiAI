"""
Sincronização com Google Drive usando PyDrive2.
- Requer um arquivo client_secrets.json na raiz (OAuth Desktop).
- Abre o navegador na primeira execução; as credenciais ficam cacheadas.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

try:
    from pydrive2.auth import GoogleAuth
    from pydrive2.drive import GoogleDrive
except Exception:
    GoogleAuth = None
    GoogleDrive = None


def _gauth(settings_file: str = None):
    if GoogleAuth is None:
        print("[Drive] PyDrive2 não disponível. Pule esta etapa.")
        return None, None
    gauth = GoogleAuth(settings_file=settings_file)
    # tenta client_secrets.json padrão na raiz
    try:
        if settings_file is None:
            gauth.LoadClientConfigFile("client_secrets.json")
    except Exception:
        pass
    try:
        gauth.LocalWebserverAuth()
    except Exception as e:
        print("[Drive] Falha na autenticação local:", e)
        return None, None
    drive = GoogleDrive(gauth)
    return gauth, drive


def _find_folder_id(drive, folder_name: str) -> Optional[str]:
    q = f"title = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    for f in drive.ListFile({'q': q}).GetList():
        return f['id']
    # fallback: procura no root
    for f in drive.ListFile({'q': "'root' in parents and trashed = false"}).GetList():
        if f['title'] == folder_name and f['mimeType'] == 'application/vnd.google-apps.folder':
            return f['id']
    return None


def download_new_exports(folder_name: str = "VigiAI",
                         local_dir: str = "data/raw",
                         prefix: str = "vigiai_tile_",
                         dry_run: bool = False):
    """
    Baixa do Drive todos os .tif com prefixo, estejam na pasta alvo OU na raiz.
    """
    local = Path(local_dir); local.mkdir(parents=True, exist_ok=True)

    gauth, drive = _gauth()
    if drive is None:
        return 0

    parent_queries = []

    # 1) pasta alvo (se existir)
    fid = _find_folder_id(drive, folder_name)
    if fid:
        parent_queries.append(f"'{fid}' in parents")

    # 2) sempre varre a raiz também
    parent_queries.append("'root' in parents")

    n = 0
    for pq in parent_queries:
        q = f"{pq} and trashed = false and mimeType != 'application/vnd.google-apps.folder'"
        files = drive.ListFile({'q': q}).GetList()
        for f in files:
            title = f['title']
            if prefix and not title.startswith(prefix):
                continue
            # garante a extensão .tif
            if not title.lower().endswith(('.tif', '.tiff')):
                title = title + ".tif"
            out = local / title
            if out.exists():
                continue
            print(f"[Drive] Baixando {title} -> {out}")
            if not dry_run:
                f.GetContentFile(out.as_posix())
            n += 1

    print(f"[Drive] {n} novos arquivos baixados para {local_dir}.")
    return n
