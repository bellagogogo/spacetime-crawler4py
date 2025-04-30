import requests
import cbor
import time
from utils.response import Response

def download(url, config, logger=None):
    try:
        host, port = config.cache_server
        resp = requests.get(
            f"http://{host}:{port}/",
            params=[("q", f"{url}"), ("u", f"{config.user_agent}")])
        if resp and resp.content:
            return Response(cbor.loads(resp.content))
    except Exception as e:
        if logger:
            logger.error(f"Download failed for {url}: {e}")
        return Response({
            "error": f"{e}",
            "status": None,
            "url": url
        })
