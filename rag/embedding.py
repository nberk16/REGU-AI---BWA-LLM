"""Embedding: BGE-M3 [KARAR, tur 6] ve testler için bağımlılıksız, deterministik bir yedek."""

import re
import zlib

import numpy as np


class BgeM3Embedder:
    """sentence-transformers ile BAAI/bge-m3 (yoğun vektörler, normalize)."""

    def __init__(self, model: str = "BAAI/bge-m3", batch_size: int = 32, device: str | None = None):
        self.name = model
        self.batch_size = batch_size
        self.device = device
        self._model = None

    def embed(self, texts: list[str]) -> np.ndarray:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.name, device=self.device)
        return np.asarray(self._model.encode(list(texts), batch_size=self.batch_size, normalize_embeddings=True,
                                             show_progress_bar=False), dtype=np.float32)


class HashingEmbedder:
    """Kelime ve kelime başı (ilk 5 harf) karmaları; yalnızca testler ve çevrimdışı deneme için."""

    name = "hashing-512"

    def __init__(self, dims: int = 512):
        self.dims = dims

    def embed(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dims), dtype=np.float32)
        for i, text in enumerate(texts):
            for word in re.findall(r"[a-zäöüß]+", text.lower()):
                for feature in (word, word[:5]):
                    out[i, zlib.crc32(feature.encode()) % self.dims] += 1.0
            norm = np.linalg.norm(out[i])
            if norm:
                out[i] /= norm
        return out


def get_embedder(name: str, cfg: dict):
    if name in ("hashing", HashingEmbedder.name):
        return HashingEmbedder()
    if name in ("bge-m3", cfg["embedding"]["model"]):
        return BgeM3Embedder(cfg["embedding"]["model"], cfg["embedding"]["batch_size"])
    raise ValueError(f"bilinmeyen embedding: {name}")
