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

## Politika şeması ve editör desteği

Sürüm 1 JSON Schema dosyası [`schemas/kepenk-policy-v1.schema.json`](schemas/kepenk-policy-v1.schema.json) konumundadır. YAML dil sunucusunu destekleyen editörlerde doğrulama ve otomatik tamamlama için politika dosyasının başına şu satırı ekleyebilirsiniz:

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/bilgi-ship-it/kepenk/main/schemas/kepenk-policy-v1.schema.json
version: 1
```

Şema, yapısal hataları daha kod çalışmadan gösterir. Kepenk ayrıca çalışma anında kendi deterministik ve hata durumunda kapalı kalan doğrulamasını uygular.

Ana dokümantasyon için [README.md](README.md) dosyasına bakın.
