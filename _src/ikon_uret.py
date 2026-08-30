#!/usr/bin/env python3
"""Sayfa ikonlarını ve başlıktaki logoyu iki ustadan üretir.

Ustalar `_src/ustalar/` içinde durur — alt çizgiyle başlayan dizini Jekyll
yayına almadığı için 1–2 MB'lık kaynak dosyalar siteyle birlikte servis edilmez:

  ikon.png  → sekme / arama sonucu / iOS ikonu   (yuvarlak altın çerçeveli rozet)
  logo.png  → başlık ve alt bilgideki marka logosu (yeşil amblem, saydam zemin)

Neden ayrı betik: build.py her çalıştığında görsel işlemesin diye. Usta
değişirse bir kez `python3 _src/ikon_uret.py` çalıştırmak yeterli.

⚠ Google, arama sonucundaki site ikonunu şu kurallarla alır:
   • biçim ico/png/jpg/gif/svg/bmp — WebP KABUL EDİLMEZ
   • ikon KARE ve 48 pikselin katı olmalı (48, 96, 192 …)
   • <head> içinde rel="icon" ya da kökte /favicon.ico ile bulunabilmeli
   • robots.txt ikonu engellememeli
Bu yüzden ikon çıktıları png + ico; yalnız başlıktaki görünen logo webp.
"""
import os
from PIL import Image

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USTA_IKON = os.path.join(KOK, '_src', 'ustalar', 'ikon.png')
USTA_LOGO = os.path.join(KOK, '_src', 'ustalar', 'logo.png')
PAY = 1.06          # kare tuvalde görselin etrafında bırakılan nefes payı


def kare_tuval(yol):
    kaynak = Image.open(yol).convert('RGBA')
    icerik = kaynak.crop(kaynak.getbbox())        # saydam kenar boşluklarını at
    kenar = round(max(icerik.size) * PAY)
    tuval = Image.new('RGBA', (kenar, kenar), (0, 0, 0, 0))
    tuval.paste(icerik, ((kenar - icerik.size[0]) // 2,
                         (kenar - icerik.size[1]) // 2), icerik)
    return tuval


def yaz(tuval, yol, boy, zemin=None):
    im = tuval.resize((boy, boy), Image.LANCZOS)
    if zemin:                                     # iOS saydamı siyaha çevirir
        alt = Image.new('RGBA', (boy, boy), zemin)
        alt.paste(im, (0, 0), im)
        im = alt.convert('RGB')
    im.save(os.path.join(KOK, yol), optimize=True)
    print(f'  ✓ {yol:34} {boy}×{boy}')


def main():
    ikon = kare_tuval(USTA_IKON)
    print('── sayfa ikonları (usta: ustalar/ikon.png) ──')
    yaz(ikon, 'images/favicon-48.png', 48)
    yaz(ikon, 'images/favicon-96.png', 96)
    yaz(ikon, 'images/favicon-192.png', 192)
    yaz(ikon, 'images/favicon-512.png', 512)      # PWA / manifest
    yaz(ikon, 'apple-touch-icon.png', 180, (255, 255, 255, 255))
    ikon.resize((48, 48), Image.LANCZOS).save(
        os.path.join(KOK, 'favicon.ico'), format='ICO',
        sizes=[(16, 16), (32, 32), (48, 48)])
    print('  ✓ favicon.ico                       16/32/48')

    print('── marka logosu (usta: ustalar/logo.png) ──')
    # Organization şeması logo alanı: kare, en az 112 px, saydam zemin.
    yaz(kare_tuval(USTA_LOGO), 'images/logo-512.png', 512)
    # Başlık/alt bilgi logosu 46 px kutuda duruyor; 4× çözünürlük retina için.
    logo = Image.open(USTA_LOGO).convert('RGBA')
    logo = logo.crop(logo.getbbox())
    en = 184
    boy = round(logo.size[1] * en / logo.size[0])
    logo.resize((en, boy), Image.LANCZOS).save(
        os.path.join(KOK, 'images', 'logo.webp'), format='WEBP',
        quality=88, method=6)
    print(f'  ✓ images/logo.webp                  {en}×{boy}')
    print('── bitti ──')


if __name__ == '__main__':
    main()
