"""Model girdisi: facts.json + bağlam notları → sohbet mesajları (Katman 3'ün girdisi).

Deneme turu (paket 6), baseline'lar ve fine-tuning aynı istem biçimini kullanır; her değişiklik
PROMPT_VERSION'ı artırır. Çıktı yapısı: CLAUDE.md 6.3 ve docs/07, Bölüm 2.
"""

from .templates import PROMPT_VERSION, build_messages, render_notes, system_prompt

__all__ = ["PROMPT_VERSION", "build_messages", "render_notes", "system_prompt"]
