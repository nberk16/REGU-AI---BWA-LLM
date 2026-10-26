"""Katman 2: bilgi tabanı ve getirme (docs/09_bilgi_tabani.md).

K-A (BWA satır açıklamaları) ve K-B (çarpıklık rehberi) `knowledge.toml`'dan, K-C (firma bağlam notları)
üreteç koşusunun `model_input/context_notes.jsonl` dosyasından gelir. Embedding BGE-M3, depo Chroma
[KARAR, tur 6]. Katman 2 yalnızca modele görünür dosyaları okur; ground truth'a erişmez.
"""

__version__ = "0.1.0"
