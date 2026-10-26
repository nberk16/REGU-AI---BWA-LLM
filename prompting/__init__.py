"""Model girdisi: facts.json + Katman 2 bağlamı → sohbet mesajları (Katman 3'ün girdisi).

Baseline'lar, ideal yorumlar ve fine-tuning aynı istem biçimini kullanır; her değişiklik PROMPT_VERSION'ı
artırır (docs/10_istem.md). Sürüm 1.0 deneme turunda kullanıldı ve `v1_0` modülünde dondurulmuştur.
Çıktı yapısı: CLAUDE.md 6.3 ve docs/07, Bölüm 2.
"""

from .templates import (
    PROMPT_VERSION,
    build_messages,
    model_facts,
    render_knowledge,
    render_notes,
    system_prompt,
)

__all__ = ["PROMPT_VERSION", "build_messages", "model_facts", "render_knowledge", "render_notes", "system_prompt"]
