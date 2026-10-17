"""Chroma deposu (gömülü) [KARAR, tur 6].

İki koleksiyon: genel bilgi (K-A, K-B) ve bağlam notları (K-C). Embedding'ler dışarıda hesaplanır ve
Chroma'ya verilir; böylece depo ile embedding modeli bağımsız kalır. Koleksiyon meta verisi, hangi
embedding modeliyle doldurulduğunu kaydeder; farklı bir modelle sorgulamak hata verir.
"""

import tomllib
import uuid
from pathlib import Path

from .documents import Doc

CONFIG_PATH = Path(__file__).parent / "config.toml"


def load_config(path: Path | None = None) -> dict:
    with open(path or CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def _to_doc(doc_id: str, text: str, meta: dict) -> Doc:
    meta = dict(meta)
    return Doc(doc_id, meta.pop("source_id"), meta.pop("kind"), text, meta)


class KnowledgeBase:
    def __init__(self, embedder, cfg: dict | None = None, path: Path | None = None):
        import chromadb

        self.cfg = cfg or load_config()
        self.embedder = embedder
        if path is None:
            client = chromadb.EphemeralClient()
            suffix = "-" + uuid.uuid4().hex[:8]          # bellek içi istemci süreç içinde paylaşılır
        else:
            Path(path).mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(path))
            suffix = ""
        names = self.cfg["chroma"]
        self._cols = {}
        for key in ("general", "notes"):
            col = client.get_or_create_collection(
                names[key] + suffix, configuration={"hnsw": {"space": "cosine"}},
                metadata={"embedding": embedder.name})
            stored = (col.metadata or {}).get("embedding")
            if stored and stored != embedder.name:
                raise ValueError(f"Koleksiyon {col.name} '{stored}' ile doldurulmuş; '{embedder.name}' ile kullanılamaz.")
            self._cols[key] = col

    # --- doldurma ---------------------------------------------------------------------------------

    def add(self, docs: list[Doc], batch: int = 256) -> int:
        """Henüz depoda olmayan parçaları ekler; eklenen sayıyı döner."""
        added = 0
        for key, group in (("general", [d for d in docs if d.kind != "K-C"]),
                           ("notes", [d for d in docs if d.kind == "K-C"])):
            if not group:
                continue
            col = self._cols[key]
            existing = set(col.get(ids=[d.doc_id for d in group], include=[])["ids"])
            new = [d for d in group if d.doc_id not in existing]
            for i in range(0, len(new), batch):
                part = new[i:i + batch]
                vectors = self.embedder.embed([d.text for d in part])
                col.add(ids=[d.doc_id for d in part], documents=[d.text for d in part],
                        embeddings=vectors.tolist(),
                        metadatas=[{**d.meta, "source_id": d.source_id, "kind": d.kind} for d in part])
            added += len(new)
        return added

    def count(self) -> dict:
        return {key: col.count() for key, col in self._cols.items()}

    # --- okuma ------------------------------------------------------------------------------------

    def general(self, keys: list[str]) -> list[Doc]:
        """K-A/K-B parçaları, verilen anahtar sırasıyla (satır anahtarı, oran adı veya bayrak kuralı)."""
        if not keys:
            return []
        res = self._cols["general"].get(where={"key": {"$in": list(keys)}}, include=["documents", "metadatas"])
        docs = {m["key"]: _to_doc(i, t, m) for i, t, m in zip(res["ids"], res["documents"], res["metadatas"])}
        return [docs[k] for k in keys if k in docs]

    def _note_filter(self, firm_id: str, start: int, end: int) -> dict:
        return {"$and": [{"firm_id": firm_id}, {"period_index": {"$gte": start}}, {"period_index": {"$lte": end}}]}

    def window_notes(self, firm_id: str, start: int, end: int) -> list[Doc]:
        res = self._cols["notes"].get(where=self._note_filter(firm_id, start, end), include=["documents", "metadatas"])
        return [_to_doc(i, t, m) for i, t, m in zip(res["ids"], res["documents"], res["metadatas"])]

    def profile(self, firm_id: str) -> list[Doc]:
        res = self._cols["notes"].get(where={"$and": [{"firm_id": firm_id}, {"profile": True}]},
                                      include=["documents", "metadatas"])
        return [_to_doc(i, t, m) for i, t, m in zip(res["ids"], res["documents"], res["metadatas"])]

    def rank_notes(self, firm_id: str, start: int, end: int, queries: list[str], limit: int = 200) -> list[list[tuple[str, float]]]:
        """Her sorgu için penceredeki notların sıralaması: [(doc_id, benzerlik)], en benzer önce."""
        if not queries:
            return []
        vectors = self.embedder.embed(queries)
        res = self._cols["notes"].query(query_embeddings=vectors.tolist(), n_results=limit,
                                        where=self._note_filter(firm_id, start, end), include=["distances"])
        return [[(i, 1.0 - d) for i, d in zip(ids, dists)] for ids, dists in zip(res["ids"], res["distances"])]
