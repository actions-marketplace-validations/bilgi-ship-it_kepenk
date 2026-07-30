# Kepenk — Türkçe

**Yapay zekâ kodlama ajanları için deterministik onay ve denetim kapısı.**

Kepenk, bir ajan ile yan etkili işlem arasına girer. Yerel YAML politikasını değerlendirir ve üç sonuçtan birini üretir:

- `allow`: otomatik devam et
- `approval`: insan onayı iste
- `deny`: işlemi durdur

Kepenk modelden ve sağlayıcıdan bağımsızdır. Codex, başka kodlama ajanları, terminal otomasyonları ve CI süreçleriyle kullanılabilir.

Kepenk bir sanal alan veya işletim sistemi güvenlik ürünü değildir. En az yetki, konteyner/sandbox, ayrı kimlik bilgileri ve standart güvenlik önlemleriyle birlikte kullanılmalıdır.

## Kurulum

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

kepenk init
kepenk check --action shell --command "git push origin main"
kepenk run -- python -m pytest
```

Ana dokümantasyon için [README.md](README.md) dosyasına bakın.
