"""Cliente HTTP com cache em disco, retentativas e pausa entre chamadas.

O cache evita baixar de novo o que já foi baixado (fontes gratuitas têm limites
e merecem ser tratadas com educação). Arquivos de temporadas em andamento devem
ser baixados com `refresh=True`.
"""

from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path

import requests

from .config import RAW_DIR

log = logging.getLogger(__name__)

USER_AGENT = "futstats/0.1 (projeto pessoal de análise; github.com/Broettogodinho/performance_analyst)"


class Fetcher:
    def __init__(self, fonte: str, pausa_s: float = 1.0, headers: dict | None = None, max_tentativas: int = 3):
        self.fonte = fonte
        self.pausa_s = pausa_s
        self.max_tentativas = max_tentativas
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, **(headers or {})})
        self._ultima = 0.0

    def _cache_path(self, url: str, params: dict | None, ext: str) -> Path:
        chave = url + ("?" + "&".join(f"{k}={v}" for k, v in sorted(params.items())) if params else "")
        nome = hashlib.sha1(chave.encode()).hexdigest()[:16]
        return RAW_DIR / self.fonte / f"{nome}.{ext}"

    def get(self, url: str, params: dict | None = None, ext: str = "json", refresh: bool = False) -> bytes | None:
        """Baixa o conteúdo (ou lê do cache). Retorna None se o recurso não existe (404)."""
        destino = self._cache_path(url, params, ext)
        if destino.exists() and not refresh:
            return destino.read_bytes()

        for tentativa in range(1, self.max_tentativas + 1):
            espera = self.pausa_s - (time.monotonic() - self._ultima)
            if espera > 0:
                time.sleep(espera)
            self._ultima = time.monotonic()
            try:
                resp = self.session.get(url, params=params, timeout=60)
            except requests.RequestException as exc:
                if tentativa == self.max_tentativas:
                    raise RuntimeError(f"[{self.fonte}] falha de rede em {url}: {exc}") from exc
                time.sleep(2 ** tentativa)
                continue

            if resp.status_code == 404:
                log.info("[%s] não encontrado: %s", self.fonte, url)
                return None
            if resp.status_code == 429:
                retry = int(resp.headers.get("Retry-After", 2 ** (tentativa + 2)))
                log.warning("[%s] limite de requisições; aguardando %ss", self.fonte, retry)
                time.sleep(retry)
                continue
            if resp.status_code >= 400:
                if tentativa == self.max_tentativas:
                    raise RuntimeError(f"[{self.fonte}] HTTP {resp.status_code} em {url}: {resp.text[:200]}")
                time.sleep(2 ** tentativa)
                continue

            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(resp.content)
            return resp.content
        raise RuntimeError(f"[{self.fonte}] esgotadas as tentativas para {url}")
