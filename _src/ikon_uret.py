#!/usr/bin/env python3
"""Sayfa ikonlarını tek ustadan üretir: images/domuzyagi-logo.png (1024×1024, saydam).

Neden ayrı betik: build.py her çalıştığında görsel işlemesin diye. Logo
değişirse bir kez `python3 _src/ikon_uret.py` çalıştırmak yeterli.

⚠ Google, arama sonucundaki site ikonunu şu kurallarla alır:
   • biçim ico/png/jpg/gif/svg/bmp — WebP KABUL EDİLMEZ
   • ikon KARE ve 48 pikselin katı olmalı (48, 96, 192 …)
   • <head> içinde rel="icon" ya da kökte /favicon.ico ile bulunabilmeli
   • robots.txt ikonu engellememeli
Bu yüzden çıktılar png + ico; header'daki görünen logo webp kalabilir.
"""
import os
from PIL import Image

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USTA = os.path.join(KOK, 'images', 'domuzyagi-logo.png')
PAY = 1.06          # kare tuvalde logonun etrafında bırakılan nefes payı


def kare_tuval():
    kaynak = Image.open(USTA).convert('RGBA')
    logo = kaynak.crop(kaynak.getbbox())          # saydam kenar boşluklarını at
    kenar = round(max(logo.size) * PAY)
    tuval = Image.new('RGBA', (kenar, kenar), (0, 0, 0, 0))
    tuval.paste(logo, ((kenar - logo.size[0]) // 2, (kenar - logo.size[1]) // 2), logo)
    return tuval


def yaz(tuval, yol, boy, zemin=None):
    im = tuval.resize((boy, boy), Image.LANCZOS)
    if zemin:                                     # iOS saydamı siyaha çevirir
        alt = Image.new('RGBA', (boy, boy), zemin)
        alt.paste(im, (0, 0), im)
        im = alt.convert('RGB')
    tam = os.path.join(KOK, yol)
    im.save(tam, optimize=True)
    print(f'  ✓ {yol:34} {boy}×{boy}')


def main():
    tuval = kare_tuval()
    print('── ikon üreticisi ──')
    yaz(tuval, 'images/favicon-48.png', 48)
    yaz(tuval, 'images/favicon-96.png', 96)
    yaz(tuval, 'images/favicon-192.png', 192)
    yaz(tuval, 'images/logo-512.png', 512)        # Organization şeması + PWA
    yaz(tuval, 'apple-touch-icon.png', 180, (255, 255, 255, 255))
    tuval.resize((48, 48), Image.LANCZOS).save(
        os.path.join(KOK, 'favicon.ico'), format='ICO',
        sizes=[(16, 16), (32, 32), (48, 48)])
    print('  ✓ favicon.ico                       16/32/48')
    print('── bitti ──')


if __name__ == '__main__':
    main()
