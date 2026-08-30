#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
domuzyagi.com üreticisi
───────────────────────
Tek gerçek kaynak: _src/products.json

Ürettikleri:
  urun/<slug>/index.html   — Merchant Center açılış sayfaları
  urunler.xml              — Merchant Center feed (RSS 2.0 + g:)
  sitemap.xml, robots.txt
  index.html               — ürün kartları, hero fiyat şeridi ve ürün şeması
                             (işaretçiler arası bölüm yeniden yazılır)

Kullanım:  python3 _src/build.py
"""
import json, os, re, sys, html
from datetime import datetime, timezone

KOK  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(KOK, '_src')
VER  = 13                                   # assets/site.css?v=N

with open(os.path.join(SRC, 'products.json'), encoding='utf-8') as f:
    VERI = json.load(f)
S       = VERI['site']
URUNLER = VERI['urunler']
IKONLAR = open(os.path.join(SRC, 'ikonlar.svg'), encoding='utf-8').read()

URL   = S['url'].rstrip('/')
ESIK  = S['ucretsiz_kargo_esigi']
KARGO = S['kargo_ucreti']
# Eşik 0 (veya kargo 0) → site 'her siparişte ücretsiz' diline geçer; eşik/ilerleme
# çubuğu dili tamamen devre dışı kalır. products.json'a tutar yazılınca geri gelir.
HEP_BEDAVA = KARGO == 0 or ESIK == 0


# ─────────────────────────── yardımcılar ───────────────────────────
_BOYUT_ONBELLEK = {}

def boyut(dosya):
    """images/<dosya> için (genişlik, yükseklik). Dosya başlığından okunur —
    görsel değişince HTML'deki ölçüler kendiliğinden güncellenir.
    WebP (VP8 / VP8L / VP8X), JPEG ve PNG desteklenir."""
    if dosya in _BOYUT_ONBELLEK:
        return _BOYUT_ONBELLEK[dosya]
    yol = os.path.join(KOK, 'images', dosya)
    with open(yol, 'rb') as f:
        b = f.read()
    en = boy = None

    if b[:4] == b'RIFF' and b[8:12] == b'WEBP':
        etiket = b[12:16]
        if etiket == b'VP8 ':
            i = b.index(b'\x9d\x01\x2a', 20) + 3
            en  = int.from_bytes(b[i:i+2], 'little') & 0x3fff
            boy = int.from_bytes(b[i+2:i+4], 'little') & 0x3fff
        elif etiket == b'VP8L':
            n = int.from_bytes(b[21:25], 'little')
            en, boy = (n & 0x3fff) + 1, ((n >> 14) & 0x3fff) + 1
        elif etiket == b'VP8X':
            en  = int.from_bytes(b[24:27], 'little') + 1
            boy = int.from_bytes(b[27:30], 'little') + 1

    elif b[:8] == b'\x89PNG\r\n\x1a\n':
        en  = int.from_bytes(b[16:20], 'big')
        boy = int.from_bytes(b[20:24], 'big')

    elif b[:2] == b'\xff\xd8':                      # JPEG
        i = 2
        while i < len(b) - 9:
            if b[i] != 0xff:
                i += 1
                continue
            im = b[i+1]
            if im in (0xd8, 0x01) or 0xd0 <= im <= 0xd7:
                i += 2
                continue
            uz = int.from_bytes(b[i+2:i+4], 'big')
            if 0xc0 <= im <= 0xcf and im not in (0xc4, 0xc8, 0xcc):
                boy = int.from_bytes(b[i+5:i+7], 'big')
                en  = int.from_bytes(b[i+7:i+9], 'big')
                break
            i += 2 + uz

    if not en or not boy:
        raise ValueError(f'{dosya}: görsel ölçüsü okunamadı')
    _BOYUT_ONBELLEK[dosya] = (en, boy)
    return en, boy


def olcu(dosya):
    """<img> için hazır width/height çifti."""
    en, boy = boyut(dosya)
    return f'width="{en}" height="{boy}"'


# Ürün görsel ölçüleri dosyanın kendisinden gelir; products.json'daki değerler
# yalnızca yedektir. Yeni görsel yüklenince ölçü kendiliğinden güncellenir.
for _u in URUNLER:
    _u['gorsel_en'], _u['gorsel_boy'] = boyut(_u['gorsel'])


def tl(n):
    """1250 → '1.250 ₺'"""
    return f"{n:,.0f}".replace(',', '.') + ' ₺'

def tl2(n):
    """250 → '250,00'  (feed ve tablo için)"""
    return f"{n:,.2f}".replace(',', '\x00').replace('.', ',').replace('\x00', '.')

def birim(u):
    return f"{u['fiyat']/u['gram']:.2f}".replace('.', ',') + ' ₺ / gram'

def e(x):
    """öznitelik içi (tırnak dahil kaçılır)"""
    return html.escape(str(x), quote=True)

def t(x):
    """metin düğümü (kesme işareti bozulmasın)"""
    return html.escape(str(x), quote=False)

def wa(mesaj):
    from urllib.parse import quote
    return f"https://wa.me/{S['whatsapp']}?text={quote(mesaj)}"

def ikon(ad, sinif='ico'):
    return f'<svg class="{sinif}"><use href="#i-{ad}"></use></svg>'


# ─────────────────────────── ortak parçalar ───────────────────────────
def duyuru():
    kargo_msj = ('<b class="nabiz">Tüm siparişlerde kargo ücretsiz</b>' if HEP_BEDAVA
                 else f'<b class="nabiz">{tl(ESIK)}</b> ve üzeri siparişlerde kargo bizden')
    return f'''<div class="announce">
  <div class="container">
    <span>{ikon("truck","ico nabiz-ic")} {kargo_msj}</span>
    <span class="sep">•</span>
    <span class="a-hide">{ikon("shield")} Türkiye'nin her yerine gönderim</span>
    <span class="sep">•</span>
    <span class="a-hide">{ikon("clock")} Her gün {S['calisma_saati']}</span>
  </div>
</div>'''


def header(kok='/'):
    capa = '' if kok == '/' else kok      # anasayfada çıplak #çapa → yumuşak kaydırma
    return f'''<header class="hdr">
  <div class="container hdr-in">
    <a href="{kok}" class="logo">
      <img src="{kok}images/logo.webp" alt="{e(S['ad'])} logosu" width="46" height="46">
      <span>
        <span class="logo-t">{t(S['ad'])}</span>
        <span class="logo-s">%100 Saf ve Doğal</span>
      </span>
    </a>

    <nav class="nav" aria-label="Ana menü">
      <button class="nav-x" aria-label="Menüyü kapat">{ikon("x")}</button>
      <ul>
        <li><a href="{capa}#urunler">Ürünler</a></li>
        <li class="has-drop">
          <a href="{capa}#urunler">Tüm Ürünler {ikon("down","ico caret")}</a>
          <ul class="drop">
            {"".join(f'<li><a href="{kok}urun/{u["slug"]}/">{t(u["tam_ad"])}</a></li>' for u in URUNLER)}
          </ul>
        </li>
        <li class="has-drop">
          <a href="{capa}#makaleler">Faydaları {ikon("down","ico caret")}</a>
          <ul class="drop">
            <li><a href="{kok}domuz-yaginin-faydalari/">Domuz Yağının Faydaları</a></li>
            <li><a href="{kok}domuz-yaginin-insanlara-faydalari/">İnsanlara Faydaları</a></li>
            <li><a href="{kok}domuz-yaginin-hayvanlara-faydalari/">Hayvanlara Faydaları</a></li>
            <li><a href="{kok}domuz-yagi-nasil-kullanilir/">Nasıl Kullanılır?</a></li>
          </ul>
        </li>
        <li><a href="{kok}domuz-yagi-fiyatlari/">Fiyatlar</a></li>
        <li><a href="{capa}#sss">SSS</a></li>
        <li><a href="{capa}#iletisim">İletişim</a></li>
      </ul>
    </nav>

    <div class="hdr-cta">
      <a href="tel:{S['telefon']}" class="hdr-tel">{ikon("phone")}<span>{S['telefon_gosterim']}</span></a>
      <a href="{capa}#urunler" class="btn btn-gold btn-sm">Sipariş Ver</a>
      <button class="burger" aria-label="Menüyü aç">{ikon("menu")}</button>
    </div>
  </div>
</header>
<div class="scrim"></div>'''


def footer(kok='/'):
    capa = '' if kok == '/' else kok
    urun_linkleri = "".join(
        f'<li><a href="{kok}urun/{u["slug"]}/">{t(u["tam_ad"])}</a></li>' for u in URUNLER)
    return f'''<footer class="ftr">
  <div class="container">
    <div class="ftr-g">
      <div>
        <div class="ftr-lg">
          <img src="{kok}images/logo.webp" alt="{e(S['ad'])} logosu" width="46" height="46" loading="lazy">
          <span>{t(S['ad'])}</span>
        </div>
        <p>%100 saf ve doğal domuz yağı. Geleneksel yöntemle eritilir, katkı maddesi içermez. Harici kullanım için üretilir; 15+ yıllık güvenilir hizmet.</p>
      </div>
      <div>
        <h4>Ürünler</h4>
        <ul>{urun_linkleri}<li><a href="{kok}domuz-yagi-fiyatlari/">Tüm Fiyatlar</a></li></ul>
      </div>
      <div>
        <h4>İletişim</h4>
        <ul class="ftr-c">
          <li>{ikon("phone")}<a href="tel:{S['telefon']}">{S['telefon_gosterim']}</a></li>
          <li>{ikon("phone")}<a href="tel:{S['telefon2']}">{S['telefon2_gosterim']}</a></li>
          <li>{ikon("mail")}<a href="mailto:{S['eposta']}">{S['eposta']}</a></li>
          <li>{ikon("pin")}<span>{e(S['sehir'])} / {e(S['ilce'])}</span></li>
        </ul>
      </div>
    </div>
    <div class="ftr-yasal">
      <a href="{kok}gizlilik-politikasi/">Gizlilik Politikası</a>
      <a href="{kok}iade-ve-cayma-hakki/">İade ve Cayma Hakkı</a>
      <a href="{kok}teslimat-ve-odeme/">Teslimat ve Ödeme</a>
    </div>
    <div class="ftr-uyari">
      <p><b>Sağlık uyarısı:</b> Ürünlerimiz kozmetik amaçlı, harici kullanım içindir. Gıda veya ilaç değildir; hastalıkların teşhis, tedavi veya önlenmesinde kullanılmaz. Sağlık sorunlarınız için hekiminize başvurun.</p>
    </div>
    <div class="ftr-bt">
      <p>&copy; <span class="yil"></span> {t(S['ad'])}. Tüm hakları saklıdır.</p>
    </div>
  </div>
</footer>'''


def dy_cfg():
    """window.DY_CFG — sepet motorunun ürün/fiyat/kargo kaynağı.
    HER sayfada bulunmalı; yoksa ürün ve makale sayfalarında sepet boş kalır."""
    cfg = {
        "whatsapp": S['whatsapp'],
        "esik": ESIK,
        "kargo": KARGO,
        "hepbedava": HEP_BEDAVA,
        "saat": [int(x) for x in re.findall(r'(\d{1,2}):', S['calisma_saati'])] or [0, 24],
        "urunler": {u['id']: {"ad": u['tam_ad'], "fiyat": u['fiyat']} for u in URUNLER},
    }
    return ('<script>window.DY_CFG='
            + json.dumps(cfg, ensure_ascii=False, separators=(',', ':')) + ';</script>')


def sabitler():
    return f'''<div class="fab">
  <a href="https://wa.me/{S['whatsapp']}" class="fab-wa" target="_blank" rel="noopener" aria-label="WhatsApp ile yazın">{ikon("wa","ico ico-f")}</a>
  <a href="tel:{S['telefon']}" class="fab-tel" aria-label="Hemen arayın">{ikon("phone")}</a>
</div>

<div class="mbar">
  <button type="button" class="mbar-sum" aria-expanded="false" aria-controls="mbar-sepet" hidden>
    <span class="mbar-ic">{ikon("cart")}<b class="mbar-n">0</b></span>
    <span class="mbar-tx">
      <b class="mbar-ad">Sepetiniz</b>
      <span class="mbar-alt">Henüz ürün eklemediniz</span>
    </span>
    <span class="mbar-v">0 ₺</span>
    <span class="mbar-ok">{ikon("down")}</span>
  </button>

  <div class="mbar-list" id="mbar-sepet" hidden></div>

  <div class="mbar-b">
    <a href="tel:{S['telefon']}" class="btn btn-tel btn-sm">{ikon("phone")} Ara</a>
    <a href="https://wa.me/{S['whatsapp']}" class="btn btn-wa btn-sm wa-order" target="_blank" rel="noopener">{ikon("wa","ico ico-f")} <span class="mbar-lbl">WhatsApp</span></a>
  </div>
</div>

<div class="onl" hidden>
  <button class="onl-x" type="button" aria-label="Bildirimi kapat">{ikon("x")}</button>
  <span class="onl-dot" aria-hidden="true"></span>
  <div class="onl-t">
    <b>Şu an çevrimiçiyiz</b>
    <span>Arayın, detayları konuşalım.</span>
    <a href="tel:{S['telefon']}" class="onl-no">{ikon("phone")} {S['telefon_gosterim']}</a>
  </div>
</div>

<div class="lb">
  <button class="lb-x" aria-label="Kapat">{ikon("x")}</button>
  <img alt="">
  <div class="lb-cap"></div>
</div>'''


def urun_secici(kok='/', aktif=None):
    """Sipariş bölümündeki ürün seçici — müşteri tüm ürünlerde adet ekleyip çıkarabilir.
    Anasayfadaki kartlarla aynı data-p anahtarını kullanır; ikisi birbirini günceller."""
    satirlar = []
    for u in URUNLER:
        en, boy = boyut(u['gorsel'])
        rozet = f'<span class="pick-b">{t(u["rozet"])}</span>' if u['rozet'] else ''
        aktif_sinif = ' is-aktif' if u['id'] == aktif else ''
        satirlar.append(f'''
        <div class="pick-i{aktif_sinif}">
          <a class="pick-g" href="{kok}urun/{u['slug']}/" tabindex="-1" aria-hidden="true">
            <img src="{kok}images/{u['gorsel']}" alt="" width="{en}" height="{boy}" loading="lazy">
          </a>
          <div class="pick-t">
            <b><a href="{kok}urun/{u['slug']}/">{t(u['tam_ad'])}</a></b>{rozet}
            <span>{tl(u['fiyat'])} <i>· {birim(u)}</i></span>
          </div>
          <div class="qty qty-sm" data-p="{u['id']}">
            <button type="button" data-act="eksi" aria-label="{e(u['tam_ad'])} adedini azalt">{ikon("minus")}</button>
            <input type="number" value="0" min="0" max="99" aria-label="{e(u['tam_ad'])} adedi">
            <button type="button" data-act="arti" aria-label="{e(u['tam_ad'])} adedini artır">{ikon("plus")}</button>
          </div>
        </div>''')
    return ('''<div class="pick">
      <h4>Ürün Seçimi</h4>
      <p class="pick-n">İstediğiniz ürünlerden adet ekleyin — birden fazla ürünü aynı siparişte gönderebilirsiniz.</p>
      <div class="pick-l">''' + "".join(satirlar) + '''
      </div>
    </div>''')


def siparis_bolumu(kok='/', tekil=False, aktif=None):
    """Ürün seçimi + müşteri bilgileri tek formda. tekil=True → ürün detay sayfası."""
    ep = S.get('form_endpoint')
    action = f' action="{ep}" method="POST"' if ep else ''
    gizli = ('<input type="hidden" name="_subject" value="domuzyagi.com - Yeni siparis">\n        '
             '<input type="hidden" name="_captcha" value="false">\n        '
             '<input type="hidden" name="_template" value="table">\n        ') if ep else ''

    # ücretsiz kargo eşiği yoksa ilerleme çubuğu anlamsız — sabit bilgi satırı gösterilir
    ship_bar = (f'''<div class="ship-bar done">
        <div class="ship-txt">{ikon("truck")}
          <span class="ship-msg">Tüm siparişlerde kargo ücretsiz.</span>
        </div>
      </div>''' if HEP_BEDAVA else f'''<div class="ship-bar">
        <div class="ship-txt">{ikon("truck")}
          <span class="ship-msg">Ücretsiz kargo için {tl(ESIK)} ve üzeri sipariş verin.</span>
        </div>
        <div class="ship-track"><div class="ship-fill"></div></div>
      </div>''')

    # özet gövdesi: her sayfada aynı sepet listesi (seçici tüm ürünleri gösterir)
    ozet_ic = '<div class="cart-list"></div>'

    return f'''<div class="cekout" id="siparis">
  <div class="cekout-h">
    <h3>Siparişinizi Tamamlayın</h3>
    <p>Ürünleri seçin, bilgilerinizi bırakın. Siparişiniz WhatsApp'a hazır olarak gelsin — üyelik gerekmez.</p>
  </div>

  <form class="oform cekout-g"{action} novalidate>
    {gizli}<input type="text" name="_gizli" class="of-tuzak" tabindex="-1" autocomplete="off" aria-hidden="true">
    <input type="hidden" name="Sipariş" class="of-urun" value="">

    <div class="cekout-sol">
      {urun_secici(kok, aktif)}

      <h4>Teslimat Bilgileri</h4>
      <div class="of-g">
        <label class="of-f">
          <span>Ad Soyad <i>*</i></span>
          <input type="text" name="Ad Soyad" autocomplete="name" required>
          <em class="of-hata"></em>
        </label>
        <label class="of-f">
          <span>Telefon <i>*</i></span>
          <input type="tel" name="Telefon" autocomplete="tel" inputmode="tel" placeholder="05xx xxx xx xx" required>
          <em class="of-hata"></em>
        </label>
        <label class="of-f">
          <span>İl / İlçe <i>*</i></span>
          <input type="text" name="İl / İlçe" autocomplete="address-level2" required>
          <em class="of-hata"></em>
        </label>
        <label class="of-f">
          <span>E-posta</span>
          <input type="email" name="E-posta" autocomplete="email" placeholder="isteğe bağlı">
          <em class="of-hata"></em>
        </label>
        <label class="of-f of-tam">
          <span>Teslimat Adresi <i>*</i></span>
          <textarea name="Adres" rows="3" autocomplete="street-address" required></textarea>
          <em class="of-hata"></em>
        </label>
        <label class="of-f of-tam">
          <span>Sipariş notu</span>
          <textarea name="Not" rows="2" placeholder="Eklemek istedikleriniz"></textarea>
        </label>
      </div>
    </div>

    <aside class="cekout-sag">
      <h4>Sipariş Özeti</h4>
      {ozet_ic}

      {ship_bar}

      <div class="sum-row"><span>Ara toplam</span><b class="sum-ara">0 ₺</b></div>
      <div class="sum-row"><span>Kargo</span><b class="sum-kargo">{"Ücretsiz" if HEP_BEDAVA else (tl(KARGO) if KARGO is not None else "Alıcıya ait")}</b></div>
      <div class="sum-tot"><span>Toplam</span><b class="sum-toplam">0 ₺</b></div>

      <label class="of-kvkk">
        <input type="checkbox" required>
        <span>Siparişimin oluşturulması ve teslimatı için ad, telefon ve adres bilgilerimin işlenmesine onay veriyorum. <a href="{kok}gizlilik-politikasi/">Gizlilik Politikası</a></span>
        <em class="of-hata"></em>
      </label>

      <button type="submit" class="btn btn-gold btn-lg btn-block of-gonder">{ikon("box")} Siparişi Gönder</button>
      <p class="of-durum" role="status"></p>

      <div class="cekout-alt">
        <span>veya doğrudan</span>
        <div class="cekout-alt-b">
          <a href="https://wa.me/{S['whatsapp']}" class="btn btn-wa btn-sm wa-order" target="_blank" rel="noopener">{ikon("wa","ico ico-f")} WhatsApp</a>
          <a href="tel:{S['telefon']}" class="btn btn-tel btn-sm">{ikon("phone")} {S['telefon_gosterim']}</a>
        </div>
      </div>
    </aside>
  </form>
</div>'''


# ─────────────────────────── ürün kartı (anasayfa) ───────────────────────────
def kart_basligi(u):
    """Kartta ve listelerde görünen ad: '50 Gram Domuz Yağı'.
    Gramaj etiketinden türer, ayrı bir alan tutulmaz."""
    g = u['gramaj_etiket'].split(' —')[0].strip()
    g = re.sub(r'\b(gram|kilogram|gr|kg)\b', lambda m: m.group(1).capitalize(), g)
    return f"{g} {u['ad']}"


def urun_karti(u):
    sinif  = 'prod hot fx' if u['one_cikan'] else 'prod fx'
    rozet  = ''
    if u['rozet']:
        ek = '' if u['one_cikan'] else ' teal'
        rozet = f'<span class="p-badge{ek}">{e(u["rozet"])}</span>'
    ozel   = "\n            ".join(f'<li>{ikon("check")} {t(o)}</li>' for o in u['ozellikler'])
    btn    = 'btn-gold' if u['one_cikan'] else 'btn-ink'
    return f'''      <article class="{sinif}">
        {rozet}
        <a class="p-img" href="urun/{u['slug']}/" aria-label="{e(u['ad'])} {e(u['gramaj_etiket'])} ürün sayfası">
          <img src="images/{u['gorsel']}" alt="{e(u['ad'])} {e(u['gramaj_etiket'])}" width="{u['gorsel_en']}" height="{u['gorsel_boy']}" loading="lazy">
          <span class="p-zoom">{ikon("right")}</span>
        </a>
        <div class="p-body">
          <h3><a href="urun/{u['slug']}/">{t(kart_basligi(u))}</a></h3>
          <div class="p-price"><span class="v">{tl(u['fiyat'])}</span></div>
          <p class="p-desc">{t(u['ozet'])}</p>
          <ul class="p-feat">
            {ozel}
          </ul>
          <div class="p-qty">
            <div class="qty" data-p="{u['id']}">
              <button type="button" data-act="eksi" aria-label="Azalt">{ikon("minus")}</button>
              <input type="number" value="0" min="0" max="99" aria-label="{e(u['ad'])} {e(u['gramaj_etiket'])} adedi">
              <button type="button" data-act="arti" aria-label="Artır">{ikon("plus")}</button>
            </div>
            <span class="p-sub" data-sub="{u['id']}"></span>
          </div>
          <div class="p-btns">
            <a href="#siparis" class="btn {btn} btn-sm" data-ekle="{u['id']}">{ikon("box")} Sipariş Ver</a>
            <a href="urun/{u['slug']}/" class="btn btn-line btn-sm" aria-label="Ürün detayı">{ikon("right")}</a>
          </div>
        </div>
      </article>'''


# ─────────────────────────── şema ───────────────────────────
def urun_semasi(u, tekil=False):
    teklif = {
        "@type": "Offer",
        "url": f"{URL}/urun/{u['slug']}/",
        "price": str(u['fiyat']),
        "priceCurrency": S['para_birimi'],
        "availability": "https://schema.org/InStock",
        "itemCondition": "https://schema.org/NewCondition",
        "seller": {"@id": f"{URL}/#org"},
    }
    if KARGO is not None:
        teklif["shippingDetails"] = {
            "@type": "OfferShippingDetails",
            "shippingRate": {
                "@type": "MonetaryAmount",
                "value": "0" if u['kargo_bedava'] else str(KARGO),
                "currency": S['para_birimi'],
            },
            "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "TR"},
        }
    d = {
        "@type": "Product",
        "name": u['tam_ad'],
        "sku": u['id'],
        "mpn": u['id'],
        "image": f"{URL}/images/{u['gorsel']}",
        "description": u['feed_aciklama'],
        "brand": {"@type": "Brand", "name": S['marka']},
        "category": S['google_kategori'],
        "weight": {"@type": "QuantitativeValue", "value": u['gram'], "unitCode": "GRM"},
        "offers": teklif,
    }
    if tekil:
        d["@context"] = "https://schema.org"
    return d


# ─────────────────────────── ürün sayfası ───────────────────────────
def urun_sayfasi(u):
    digerleri = [x for x in URUNLER if x['id'] != u['id']]
    kart = "".join(f'''
        <a class="rel" href="../{x['slug']}/">
          <img src="../../images/{x['gorsel']}" alt="{e(x['ad'])} {e(x['gramaj_etiket'])}" width="{x['gorsel_en']}" height="{x['gorsel_boy']}" loading="lazy">
          <span class="rel-b">
            <b>{t(x['ad'])}</b>
            <span>{t(x['gramaj_etiket'])}</span>
            <i>{tl(x['fiyat'])}</i>
          </span>
        </a>''' for x in digerleri)

    ozel = "\n          ".join(f'<li>{ikon("check")} {t(o)}</li>' for o in u['ozellikler'])

    kargo_satir = ('Bu üründe kargo ücretsiz.' if u['kargo_bedava']
                   else f"Kargo ücreti alıcıya aittir. {tl(ESIK)} ve üzeri siparişlerde kargo bize aittir.")

    mesaj = f"Merhaba, {u['ad']} {u['gramaj_etiket']} ({tl(u['fiyat'])}) sipariş etmek istiyorum."

    semalar = {
        "@context": "https://schema.org",
        "@graph": [
            urun_semasi(u),
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Ana Sayfa", "item": f"{URL}/"},
                    {"@type": "ListItem", "position": 2, "name": "Ürünler", "item": f"{URL}/#urunler"},
                    {"@type": "ListItem", "position": 3, "name": u['tam_ad']},
                ],
            },
            {
                "@type": "Organization",
                "@id": f"{URL}/#org",
                "name": S['ad'],
                "url": f"{URL}/",
                "logo": f"{URL}/images/logo.webp",
                "email": S['eposta'],
                "address": {"@type": "PostalAddress", "addressLocality": S['ilce'],
                            "addressRegion": S['sehir'], "addressCountry": "TR"},
            },
        ],
    }

    baslik = f"{u['tam_ad']} — {tl(u['fiyat'])} | {S['ad']}"
    return f'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{t(baslik)}</title>
<meta name="description" content="{e(u['feed_aciklama'])} Fiyat: {tl(u['fiyat'])}. Telefon veya WhatsApp ile sipariş.">
<link rel="canonical" href="{URL}/urun/{u['slug']}/">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="theme-color" content="#132428">

<meta property="og:type" content="product">
<meta property="og:site_name" content="{e(S['ad'])}">
<meta property="og:locale" content="tr_TR">
<meta property="og:title" content="{e(u['tam_ad'])} — {tl(u['fiyat'])}">
<meta property="og:description" content="{e(u['feed_aciklama'])}">
<meta property="og:url" content="{URL}/urun/{u['slug']}/">
<meta property="og:image" content="{URL}/images/{u['gorsel']}">
<meta property="product:price:amount" content="{u['fiyat']}">
<meta property="product:price:currency" content="{S['para_birimi']}">
<meta name="twitter:card" content="summary_large_image">

<link rel="icon" href="../../images/logo.webp" type="image/webp">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../../assets/site.css?v={VER}">

<script async src="https://www.googletagmanager.com/gtag/js?id={S['ga_id']}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{S['ga_id']}');
</script>

<script type="application/ld+json">
{json.dumps(semalar, ensure_ascii=False, indent=2)}
</script>
</head>
<body>

{IKONLAR}

{duyuru()}

{header('../../')}

<div class="crumb-bar">
  <div class="container">
    <nav class="crumb" aria-label="Site haritası">
      <a href="../../">Ana Sayfa</a>{ikon("right")}
      <a href="../../#urunler">Ürünler</a>{ikon("right")}
      <span>{t(u['tam_ad'])}</span>
    </nav>
  </div>
</div>

<section class="sec">
  <div class="container">
    <div class="pdp">
      <div class="pdp-img" data-lb="../../images/{u['gorsel']}" data-lb-cap="{e(u['ad'])} {e(u['gramaj_etiket'])}">
        <img src="../../images/{u['gorsel']}" alt="{e(u['ad'])} {e(u['gramaj_etiket'])}" width="{u['gorsel_en']}" height="{u['gorsel_boy']}" fetchpriority="high">
        <span class="p-zoom">{ikon("zoom")}</span>
      </div>

      <div class="pdp-info">
        {f'<span class="pdp-badge">{t(u["rozet"])}</span>' if u['rozet'] else ''}
        <h1>{t(u['tam_ad'])}</h1>
        <div class="pdp-price">
          <span class="v">{tl(u['fiyat'])}</span>
          <span class="u">{birim(u)}</span>
        </div>
        <p class="pdp-desc">{t(u['feed_aciklama'])}</p>
        <ul class="p-feat">
          {ozel}
        </ul>

        <div class="pdp-stok">{ikon("check")} <b>Stokta</b> — {kargo_satir}</div>

        <div class="buy" data-urun="{u['id']}" data-ad="{e(u['ad'])} {e(u['gramaj_etiket'])}" data-fiyat="{u['fiyat']}" data-bedava="{1 if u['kargo_bedava'] else 0}">
          <div class="buy-row">
            <div class="qty" data-p="{u['id']}">
              <button type="button" data-act="eksi" aria-label="Azalt">{ikon("minus")}</button>
              <input type="number" value="1" min="0" max="99" aria-label="Adet">
              <button type="button" data-act="arti" aria-label="Artır">{ikon("plus")}</button>
            </div>
            <div class="buy-tot"><span>Toplam</span><b class="buy-v">{tl(u['fiyat'])}</b></div>
          </div>
          <p class="buy-kargo"></p>
          <a href="#siparis" class="btn btn-gold btn-lg btn-block">{ikon("box")} Siparişi Tamamla</a>
          <a href="{wa(mesaj)}" class="btn btn-wa btn-lg btn-block wa-order" target="_blank" rel="noopener">{ikon("wa","ico ico-f")} WhatsApp ile Sipariş Ver</a>
        </div>

        <div class="pdp-trust">
          <span>{ikon("truck")} Türkiye geneli kargo</span>
          <span>{ikon("box")} Isıya dayanıklı ambalaj</span>
          <span>{ikon("clock")} {S['kargo_sure']} teslimat</span>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="sec sec-cream">
  <div class="container">
    {siparis_bolumu('../../', tekil=True, aktif=u['id'])}
  </div>
</section>

<section class="sec">
  <div class="container">
    <div class="pg-body">
      <h2>Ürün Bilgileri</h2>
      <div class="tbl-wrap">
        <table>
          <tr><th>Ürün kodu</th><td>{u['id']}</td></tr>
          <tr><th>Net miktar</th><td>{u['gram']} gram{f" ({u['adet']} × {u['gram']//u['adet']} gr)" if u['adet'] > 1 else ""}</td></tr>
          <tr><th>Fiyat</th><td>{tl2(u['fiyat'])} ₺</td></tr>
          <tr><th>Gram başına</th><td>{birim(u)}</td></tr>
          <tr><th>İçerik</th><td>%100 domuz yağı — katkı maddesi, parfüm ve koruyucu içermez</td></tr>
          <tr><th>Ambalaj</th><td>Isıya dayanıklı ambalaj</td></tr>
          <tr><th>Kullanım</th><td>Harici kullanım içindir; gıda olarak tüketilmez</td></tr>
          <tr><th>Saklama</th><td>Serin ve kuru yerde, güneş ışığından uzakta. Açıldıktan sonra buzdolabında.</td></tr>
          <tr><th>Stok durumu</th><td>Stokta</td></tr>
          <tr><th>Kargo</th><td>{kargo_satir} Teslimat {S['kargo_sure']}.</td></tr>
        </table>
      </div>

      <h2>Nasıl Sipariş Verilir?</h2>
      <p>Üyelik veya form doldurmak gerekmez. Adedi seçip <strong>WhatsApp ile Sipariş Ver</strong> butonuna basın — siparişiniz mesaja hazır olarak gelir. Dilerseniz <a href="tel:{S['telefon']}">{S['telefon_gosterim']}</a> numarasını arayarak doğrudan sipariş verebilirsiniz. Her gün {S['calisma_saati']} arası ulaşabilirsiniz.</p>

      <div class="note">
        <p><b>Önemli:</b> Bu ürün kozmetik amaçlı, harici kullanım içindir. Gıda veya ilaç değildir; hastalıkların teşhis, tedavi veya önlenmesinde kullanılmaz. İlk kullanımda küçük bir alanda test etmenizi öneririz.</p>
      </div>
    </div>
  </div>
</section>

<section class="sec sec-cream">
  <div class="container">
    <div class="sec-h">
      <span class="tag">Diğer Ürünler</span>
      <h2>Diğer Boylarımız</h2>
      <div class="rule"></div>
    </div>
    <div class="rel-g">{kart}
    </div>
  </div>
</section>



{footer('../../')}

{sabitler()}

{dy_cfg()}
<script src="../../assets/site.js?v={VER}" defer></script>
</body>
</html>
'''


# ─────────────────────────── bilgi sayfaları ───────────────────────────
def bilgi_sayfasi(slug, baslik, ozet, govde):
    semalar = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebPage", "name": baslik, "description": ozet,
             "url": f"{URL}/{slug}/", "inLanguage": "tr-TR"},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Ana Sayfa", "item": f"{URL}/"},
                {"@type": "ListItem", "position": 2, "name": baslik}]},
        ],
    }
    return f'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{t(baslik)} | {t(S['ad'])}</title>
<meta name="description" content="{e(ozet)}">
<link rel="canonical" href="{URL}/{slug}/">
<meta name="robots" content="index, follow">
<meta name="theme-color" content="#132428">
<link rel="icon" href="../images/logo.webp" type="image/webp">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/site.css?v={VER}">
<script type="application/ld+json">
{json.dumps(semalar, ensure_ascii=False, indent=2)}
</script>
</head>
<body>

{IKONLAR}

{duyuru()}

{header('../')}

<div class="crumb-bar">
  <div class="container">
    <nav class="crumb" aria-label="Site haritası">
      <a href="../">Ana Sayfa</a>{ikon("right")}
      <span>{t(baslik)}</span>
    </nav>
  </div>
</div>

<section class="sec">
  <div class="container">
    <div class="pg-body">
      <h1>{t(baslik)}</h1>
      <p class="pg-ozet">{t(ozet)}</p>
      {govde}
      <div class="note">
        <p>Sorularınız için <a href="mailto:{S['eposta']}">{S['eposta']}</a> adresinden veya
        <a href="tel:{S['telefon']}">{S['telefon_gosterim']}</a> numarasından bize ulaşabilirsiniz.</p>
      </div>
    </div>
  </div>
</section>

{footer('../')}

{sabitler()}

{dy_cfg()}
<script src="../assets/site.js?v={VER}" defer></script>
</body>
</html>
'''


def bilgi_sayfalari():
    esik, kargo = tl(ESIK), tl(KARGO) if KARGO is not None else 'kargo ücreti'
    kargo_blok = ('''<div class="note">
        <p><b>Kargo tüm siparişlerde ücretsizdir.</b> Tutar sınırı yoktur; hangi ürünü,
        kaç adet alırsanız alın kargo ücreti alınmaz. Türkiye'nin her yerine gönderim yapılır.</p>
      </div>''' if HEP_BEDAVA else f'''<div class="tbl-wrap">
        <table>
          <tr><th>Sipariş tutarı</th><th>Kargo ücreti</th></tr>
          <tr><td>{esik} altı</td><td>{kargo} — alıcıya aittir</td></tr>
          <tr><td>{esik} ve üzeri</td><td><strong>Ücretsiz</strong> — kargo bize aittir</td></tr>
        </table>
      </div>''')
    return [
      ('gizlilik-politikasi', 'Gizlilik Politikası ve KVKK Aydınlatma Metni',
       'Sipariş sürecinde topladığımız kişisel verileri hangi amaçla işlediğimizi ve haklarınızı açıklar.',
       f'''<h2>Hangi verileri topluyoruz?</h2>
      <p>Siparişinizi oluşturabilmek için yalnızca teslimat için gereken bilgileri alıyoruz:</p>
      <ul>
        <li><strong>Ad soyad</strong> — kargo gönderisinin alıcısı olarak</li>
        <li><strong>Telefon numarası</strong> — siparişi teyit etmek ve kargo bilgisi vermek için</li>
        <li><strong>Adres, il ve ilçe</strong> — gönderinin teslimi için</li>
        <li><strong>E-posta adresi</strong> — isterseniz; sipariş bilgilendirmesi için</li>
      </ul>
      <p>Bu bilgileri sipariş formu, WhatsApp veya telefon yoluyla siz bize iletirsiniz. Kredi kartı bilgisi <strong>toplamıyoruz</strong>; sitemizde online ödeme alınmaz.</p>

      <h2>Verileri hangi amaçla kullanıyoruz?</h2>
      <p>Verileriniz yalnızca siparişinizin hazırlanması, teyit edilmesi, kargoya verilmesi ve size ulaşması amacıyla kullanılır. İzniniz olmadan pazarlama amaçlı mesaj göndermeyiz, verilerinizi satmayız.</p>

      <h2>Kimlerle paylaşıyoruz?</h2>
      <ul>
        <li><strong>Kargo firması</strong> — gönderiyi teslim edebilmek için ad, telefon ve adres bilgisi paylaşılır.</li>
        <li><strong>Form servisi</strong> — sipariş formunu doldurursanız, form içeriği bize e-posta olarak iletilir.</li>
        <li><strong>Google Analytics / Google Ads</strong> — sitenin kullanımına dair anonim istatistikler için çerez kullanılır. Bu veriler kimliğinizi tanımlamaz.</li>
      </ul>
      <p>Bunların dışında hiçbir üçüncü tarafla veri paylaşmayız.</p>

      <h2>Ne kadar süre saklıyoruz?</h2>
      <p>Sipariş kayıtları, ilgili mevzuatın öngördüğü yasal saklama süreleri boyunca tutulur. Bu sürenin sonunda silinir. Silinmesini daha erken talep edebilirsiniz.</p>

      <h2>KVKK kapsamındaki haklarınız</h2>
      <p>6698 sayılı Kişisel Verilerin Korunması Kanunu'nun 11. maddesi uyarınca; kişisel verilerinizin işlenip işlenmediğini öğrenme, işlenmişse bilgi talep etme, işlenme amacını öğrenme, eksik veya yanlış işlenmişse düzeltilmesini isteme, silinmesini veya yok edilmesini isteme ve işlemenin kanuna aykırı olması hâlinde zararın giderilmesini talep etme haklarına sahipsiniz.</p>
      <p>Bu haklarınızı kullanmak için <a href="mailto:{S['eposta']}">{S['eposta']}</a> adresine yazabilir veya <a href="tel:{S['telefon']}">{S['telefon_gosterim']}</a> numarasını arayabilirsiniz. Talebiniz en geç 30 gün içinde sonuçlandırılır.</p>

      <h2>Çerezler</h2>
      <p>Sitemizde ölçümleme amacıyla Google Analytics ve Google Ads çerezleri kullanılır. Tarayıcı ayarlarınızdan çerezleri reddedebilirsiniz; bu durumda sitenin temel işlevleri çalışmaya devam eder.</p>'''),

      ('iade-ve-cayma-hakki', 'İade ve Cayma Hakkı',
       'Cayma hakkınız, iade koşulları, hijyen istisnası ve bedel iadesi süreci.',
       f'''<h2>Cayma hakkı</h2>
      <p>Mesafeli Sözleşmeler Yönetmeliği uyarınca, ürünü teslim aldığınız tarihten itibaren <strong>14 gün</strong> içinde hiçbir gerekçe göstermeden ve cezai şart ödemeden sözleşmeden cayma hakkınız vardır.</p>
      <p>Cayma hakkınızı kullanmak için bu süre içinde <a href="mailto:{S['eposta']}">{S['eposta']}</a> adresine yazmanız ya da <a href="tel:{S['telefon']}">{S['telefon_gosterim']}</a> numarasını aramanız yeterlidir.</p>

      <h2>Hijyen istisnası — önemli</h2>
      <div class="note">
        <p><b>Ambalajı açılmış ürünler iade alınamaz.</b> Ürünlerimiz cilde uygulanan kozmetik ürünlerdir. Mesafeli Sözleşmeler Yönetmeliği'nin 15. maddesi uyarınca, tesliminden sonra ambalajı açılmış olan ve sağlık ile hijyen açısından iadesi uygun olmayan ürünlerde cayma hakkı kullanılamaz.</p>
      </div>
      <p>Ambalajı <strong>açılmamış</strong>, kullanılmamış ve yeniden satılabilir durumdaki ürünler 14 gün içinde iade edilebilir.</p>

      <h2>Hasarlı, kusurlu veya yanlış gönderilen ürün</h2>
      <p>Bu durum yukarıdaki istisnanın dışındadır. Kargodan hasarlı çıkan, kusurlu olan veya sipariş ettiğinizden farklı gelen ürünlerde:</p>
      <ul>
        <li>Ürünü <strong>ücretsiz</strong> değiştiriyoruz veya bedelini iade ediyoruz.</li>
        <li>İade kargo ücreti <strong>bize aittir</strong>.</li>
        <li>Lütfen teslim aldığınızda paketi kontrol edin; hasar varsa kargo görevlisine tutanak tutturun ve bizi arayın.</li>
      </ul>

      <h2>İade kargo ücreti</h2>
      <p>Cayma hakkı kapsamındaki iadelerde kargo ücreti alıcıya aittir. Hasarlı, kusurlu veya yanlış gönderilen ürünlerde iade kargo ücretini biz karşılarız.</p>

      <h2>Bedel iadesi</h2>
      <p>İade edilen ürün tarafımıza ulaştıktan sonra, ödediğiniz bedel <strong>14 gün içinde</strong> ödemeyi yaptığınız yöntemle iade edilir. Havale/EFT ile ödeme yaptıysanız iade, bildireceğiniz IBAN'a yapılır.</p>

      <h2>Şikâyet ve itiraz</h2>
      <p>Uyuşmazlık durumunda, parasal sınırlara göre bulunduğunuz yerdeki Tüketici Hakem Heyetine veya Tüketici Mahkemesine başvurabilirsiniz.</p>'''),

      ('teslimat-ve-odeme', 'Teslimat ve Ödeme Koşulları',
       ('Tüm siparişlerde ücretsiz kargo, teslim süresi ve kabul edilen ödeme yöntemleri.'
        if HEP_BEDAVA else
        f'Kargo ücreti, {esik} ücretsiz kargo eşiği, teslim süresi ve kabul edilen ödeme yöntemleri.'),
       f'''<h2>Kargo ücreti</h2>
      {kargo_blok}

      <h2>Teslim süresi</h2>
      <p>Siparişiniz teyit edildikten sonra <strong>aynı gün</strong> kargoya verilir. Teslim süresi bulunduğunuz ile göre değişmekle birlikte genellikle <strong>{S['kargo_sure']}</strong> içindedir. Türkiye'nin her yerine gönderim yapılır.</p>
      <p>Ürünler ısıya dayanıklı özel ambalajla gönderilir; bu sayede kargo sırasında bozulma riski en aza indirilir.</p>

      <h2>Ödeme yöntemleri</h2>
      <ul>
        <li><strong>Havale / EFT</strong> — sipariş teyidinden sonra hesap bilgileri paylaşılır.</li>
        <li><strong>Kapıda nakit ödeme</strong> — ürünü teslim alırken kargo görevlisine ödersiniz.</li>
      </ul>
      <p>Sitemizde online kart ödemesi alınmaz; kredi kartı bilgisi talep etmeyiz. Bu bilgileri isteyen mesajlara itibar etmeyin.</p>

      <h2>Sipariş nasıl verilir?</h2>
      <p>Üç yolu var: ürün sayfalarındaki <strong>sipariş formunu</strong> doldurabilir, <a href="https://wa.me/{S['whatsapp']}" target="_blank" rel="noopener">WhatsApp</a> üzerinden yazabilir veya <a href="tel:{S['telefon']}">{S['telefon_gosterim']}</a> numarasını arayabilirsiniz. Her gün {S['calisma_saati']} arası ulaşabilirsiniz.</p>

      <h2>Sipariş takibi</h2>
      <p>Kargoya verildiğinde takip numaranız telefonla veya WhatsApp üzerinden size iletilir.</p>'''),
    ]

# ─────────────────────────── makale sayfaları ───────────────────────────
MAKALE_META = json.load(open(os.path.join(SRC, 'makaleler', 'meta.json'), encoding='utf-8'))

MAKALE_SIRA = [
    'domuz-yaginin-faydalari',
    'domuz-yaginin-insanlara-faydalari',
    'domuz-yaginin-hayvanlara-faydalari',
    'domuz-yagi-nasil-kullanilir',
    'domuz-yagi-fiyatlari',
]

MAKALE_KART = {
    'domuz-yaginin-faydalari':            ('Domuz Yağının Faydaları', 'makale-faydalari.webp'),
    'domuz-yaginin-insanlara-faydalari':  ('İnsanlara Faydaları',      'makale-insan.webp'),
    'domuz-yaginin-hayvanlara-faydalari': ('Hayvanlara Faydaları',     'makale-hayvan.webp'),
    'domuz-yagi-nasil-kullanilir':        ('Nasıl Kullanılır?',        'makale-kullanim.webp'),
    'domuz-yagi-fiyatlari':               ('Domuz Yağı Fiyatları',     'urun-115gr.webp'),
}


def fiyat_tablosu():
    """Makale gövdesindeki <!-- FIYAT-TABLOSU --> yerine geçer.
    Fiyatlar products.json'dan gelir; tablo elle güncellenmez."""
    satir = "".join(f'''
<tr>
<td>{t(u['tam_ad'])}</td>
<td>{t(u['gramaj_etiket'])}</td>
<td>{tl(u['fiyat'])}</td>
<td>{birim(u)}</td>
<td>{"<strong>Ücretsiz</strong>" if (HEP_BEDAVA or u['kargo_bedava']) else "Alıcıya ait"}</td>
<td><a href="{wa(u['tam_ad'] + ' sipariş etmek istiyorum.')}" target="_blank" rel="noopener">Sipariş</a></td>
</tr>''' for u in URUNLER)
    return f'''<div class="tbl-wrap"><table>
<thead>
<tr><th>Ürün</th><th>Gramaj</th><th>Fiyat</th><th>Gram başına</th><th>Kargo</th><th>İşlem</th></tr>
</thead>
<tbody>{satir}
</tbody>
</table></div>'''


def kargo_notu():
    """Makale gövdesindeki <!-- KARGO-NOTU --> yerine geçer."""
    if HEP_BEDAVA:
        return ('<p><strong>• Kargo:</strong> Tüm ürünlerde kargo ücretsizdir; '
                'alt tutar sınırı yoktur.</p>')
    return (f'<p><strong>• Kargo Ücreti:</strong> Kargo ücreti alıcıya aittir.</p>\n'
            f'<p><strong>• Ücretsiz Kargo:</strong> {tl(ESIK)} ve üzeri siparişlerde '
            f'kargo ücretini biz karşılıyoruz.</p>')


def makale_sayfasi(slug):
    m = MAKALE_META[slug]
    govde = open(os.path.join(SRC, 'makaleler', slug + '.html'), encoding='utf-8').read()
    govde = govde.replace('<!-- FIYAT-TABLOSU -->', fiyat_tablosu())
    govde = govde.replace('<!-- KARGO-NOTU -->', kargo_notu())

    digerleri = [x for x in MAKALE_SIRA if x != slug]
    ilgili = "".join(f'''
        <a class="art" href="../{x}/">
          <div class="art-i"><img src="../images/{MAKALE_KART[x][1]}" alt="{e(MAKALE_KART[x][0])}" {olcu(MAKALE_KART[x][1])} loading="lazy"></div>
          <div class="art-b"><h3>{t(MAKALE_KART[x][0])}</h3>
          <span class="art-l">Devamını Oku {ikon("right")}</span></div>
        </a>''' for x in digerleri)

    urun_serit = "".join(f'''
        <a class="mini" href="../urun/{u['slug']}/">
          <img src="../images/{u['gorsel']}" alt="{e(u['tam_ad'])}" {olcu(u['gorsel'])} loading="lazy">
          <span><b>{t(u['tam_ad'])}</b><i>{tl(u['fiyat'])}</i></span>
        </a>''' for u in URUNLER)

    semalar = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Article",
             "headline": m['h1'],
             "description": m['desc'],
             "inLanguage": "tr-TR",
             "mainEntityOfPage": {"@type": "WebPage", "@id": f"{URL}/{slug}/"},
             "publisher": {"@id": f"{URL}/#org"},
             "author": {"@type": "Organization", "name": S['ad']}},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Ana Sayfa", "item": f"{URL}/"},
                {"@type": "ListItem", "position": 2, "name": m['h1']}]},
            {"@type": "Organization", "@id": f"{URL}/#org", "name": S['ad'],
             "url": f"{URL}/", "logo": f"{URL}/images/logo.webp", "email": S['eposta']},
        ],
    }

    return f'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{t(m['title'])}</title>
<meta name="description" content="{e(m['desc'])}">
{f'<meta name="keywords" content="{e(m["keywords"])}">' if m.get('keywords') else ''}
<link rel="canonical" href="{URL}/{slug}/">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="theme-color" content="#132428">

<meta property="og:type" content="article">
<meta property="og:site_name" content="{e(S['ad'])}">
<meta property="og:locale" content="tr_TR">
<meta property="og:title" content="{e(m['h1'])}">
<meta property="og:description" content="{e(m['desc'])}">
<meta property="og:url" content="{URL}/{slug}/">
<meta property="og:image" content="{URL}/images/{MAKALE_KART[slug][1]}">
<meta name="twitter:card" content="summary_large_image">

<link rel="icon" href="../images/logo.webp" type="image/webp">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/site.css?v={VER}">

<script async src="https://www.googletagmanager.com/gtag/js?id={S['ga_id']}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{S['ga_id']}');
</script>

<script type="application/ld+json">
{json.dumps(semalar, ensure_ascii=False, indent=2)}
</script>
</head>
<body>

{IKONLAR}

{duyuru()}

{header('../')}

<section class="pg-hero">
  <div class="container">
    <nav class="crumb" aria-label="Site haritası">
      <a href="../">Ana Sayfa</a>{ikon("right")}
      <span>{t(m['h1'])}</span>
    </nav>
    <h1>{t(m['h1'])}</h1>
    {f'<p>{t(m["lead"])}</p>' if m.get('lead') else ''}
  </div>
</section>

<section class="sec">
  <div class="container">
    <div class="pg-body">
{govde}
    </div>
  </div>
</section>

<section class="sec sec-cream">
  <div class="container">
    <div class="sec-h">
      <span class="tag">Satın Al</span>
      <h2>Domuz Yağı Fiyatları</h2>
      <p>%100 saf ve doğal. {"Tüm siparişlerde kargo bizden." if HEP_BEDAVA else f"{tl(ESIK)} ve üzeri siparişlerde kargo bizden."}</p>
      <div class="rule"></div>
    </div>
    <div class="mini-g">{urun_serit}
    </div>
    <div class="cta-strip">
      <h3>Sipariş vermek için</h3>
      <p>Formu doldurun, WhatsApp'tan yazın ya da doğrudan arayın.</p>
      <div class="row">
        <a href="../#siparis" class="btn btn-gold">{ikon("box")} Sipariş Formu</a>
        <a href="https://wa.me/{S['whatsapp']}" class="btn btn-wa" target="_blank" rel="noopener">{ikon("wa","ico ico-f")} WhatsApp</a>
        <a href="tel:{S['telefon']}" class="btn btn-ghost">{ikon("phone")} {S['telefon_gosterim']}</a>
      </div>
    </div>
  </div>
</section>

<section class="sec">
  <div class="container">
    <div class="sec-h">
      <span class="tag">Bilgi Köşesi</span>
      <h2>İlgili Makaleler</h2>
      <div class="rule"></div>
    </div>
    <div class="art-g">{ilgili}
    </div>
  </div>
</section>

{footer('../')}

{sabitler()}

{dy_cfg()}
<script src="../assets/site.js?v={VER}" defer></script>
</body>
</html>
'''

# ─────────────────────────── Merchant Center feed ───────────────────────────
def feed():
    if KARGO is None:
        return None
    simdi = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')
    parcalar = [f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">
<channel>
<title>{e(S['ad'])} — Ürün Listesi</title>
<link>{URL}/</link>
<description>{e(S['ad'])} ürün akışı. %100 saf ve doğal domuz yağı.</description>
<lastBuildDate>{simdi}</lastBuildDate>''']

    for u in URUNLER:
        kargo_tutar = '0.00' if u['kargo_bedava'] else f"{KARGO:.2f}"
        multipack = f"\n  <g:multipack>{u['multipack']}</g:multipack>" if u.get('multipack') else ""
        parcalar.append(f'''<item>
  <g:id>{e(u['id'])}</g:id>
  <g:title>{e(u['feed_baslik'])}</g:title>
  <g:description>{e(u['feed_aciklama'])}</g:description>
  <g:link>{URL}/urun/{u['slug']}/</g:link>
  <g:image_link>{URL}/images/{u['gorsel']}</g:image_link>
  <g:availability>in_stock</g:availability>
  <g:price>{u['fiyat']:.2f} {S['para_birimi']}</g:price>
  <g:condition>new</g:condition>
  <g:brand>{e(S['marka'])}</g:brand>
  <g:mpn>{e(u['id'])}</g:mpn>
  <g:identifier_exists>no</g:identifier_exists>
  <g:google_product_category>{S['google_kategori_id']}</g:google_product_category>
  <g:product_type>{e(S['google_kategori'])}</g:product_type>
  <g:unit_pricing_measure>{e(u['olcu'])}</g:unit_pricing_measure>
  <g:unit_pricing_base_measure>100 g</g:unit_pricing_base_measure>{multipack}
  <g:shipping_weight>{u['gram'] + 60} g</g:shipping_weight>
  <g:shipping>
    <g:country>TR</g:country>
    <g:service>{e(S['kargo_servis'])}</g:service>
    <g:price>{kargo_tutar} {S['para_birimi']}</g:price>
  </g:shipping>
  <g:shipping_label>{"ucretsiz" if u['kargo_bedava'] else "standart"}</g:shipping_label>
  <g:custom_label_0>{e(u['kisa'])}</g:custom_label_0>
</item>''')

    parcalar.append('</channel>\n</rss>')
    return "\n".join(parcalar) + "\n"


# ─────────────────────────── sitemap & robots ───────────────────────────
def sitemap():
    bugun = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    sayfalar = [(f'{URL}/', '1.0', 'weekly')]
    sayfalar += [(f'{URL}/urun/{u["slug"]}/', '0.9', 'weekly') for u in URUNLER]
    sayfalar += [(f'{URL}/{s}/', '0.7', 'monthly') for s in [
        'domuz-yagi-fiyatlari', 'domuz-yaginin-faydalari',
        'domuz-yaginin-insanlara-faydalari', 'domuz-yaginin-hayvanlara-faydalari',
        'domuz-yagi-nasil-kullanilir']]
    sayfalar += [(f'{URL}/{s}/', '0.3', 'yearly') for s, *_ in bilgi_sayfalari()]
    g = "\n".join(f'  <url><loc>{u}</loc><lastmod>{bugun}</lastmod>'
                  f'<changefreq>{c}</changefreq><priority>{p}</priority></url>'
                  for u, p, c in sayfalar)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{g}
</urlset>
'''


def robots():
    return f'''User-agent: *
Allow: /

Sitemap: {URL}/sitemap.xml
'''


# ─────────────────────────── anasayfa güncelleme ───────────────────────────
def isaretci_degistir(metin, ad, yeni):
    bas, son = f'<!-- {ad}:BAŞ -->', f'<!-- {ad}:SON -->'
    kalip = re.compile(re.escape(bas) + r'.*?' + re.escape(son), re.S)
    if not kalip.search(metin):
        raise SystemExit(f"HATA: index.html içinde '{ad}' işaretçisi yok.")
    return kalip.sub(lambda _: f"{bas}\n{yeni}\n      {son}", metin)


def anasayfa():
    p = os.path.join(KOK, 'index.html')
    s = open(p, encoding='utf-8').read()

    # ikon seti de üreticiden gelsin — index.html'de bayat kopya kalmasın
    s = isaretci_degistir(s, 'IKONLAR', IKONLAR.rstrip())
    s = isaretci_degistir(s, 'DUYURU', duyuru())
    s = isaretci_degistir(s, 'HEADER', header('/'))
    s = isaretci_degistir(s, 'FOOTER', footer('/'))

    s = isaretci_degistir(s, 'URUNLER', "\n".join(urun_karti(u) for u in URUNLER))

    # Fiyat şeridi: normal gramajlar tek tip ızgarada (2/4 sütun, tek başına kalan
    # hücre olmasın), kampanya ise ALTINDA kendi kartında — ne aldığını ve ne
    # kazandığını açıkça yazar. Kazanç products.json'dan hesaplanır, elle girilmez.
    normal  = [u for u in URUNLER if not u['one_cikan']]
    kampanya = next((u for u in URUNLER if u['one_cikan']), None)

    ogeler = [f'<div class="hp-item">'
              f'<span class="hp-g">{t(u["gramaj_etiket"].split(" —")[0])}</span>'
              f'<span class="hp-v">{tl(u["fiyat"])}</span></div>' for u in normal]

    kmp_kart = ''
    if kampanya:
        # paketin tek tek alınsa tutacağı fiyat: aynı gramajdaki tekil ürünün katı
        birim_urun = None
        if kampanya.get('multipack'):
            tek_gram = kampanya['gram'] / kampanya['multipack']
            birim_urun = next((x for x in URUNLER
                               if x is not kampanya and x['gram'] == tek_gram), None)
        kar = ''
        if birim_urun:
            liste = birim_urun['fiyat'] * kampanya['multipack']
            if liste > kampanya['fiyat']:
                kar = (f'<s class="hp-k-eski">{tl(liste)}</s>'
                       f'<span class="hp-k-kar">{tl(liste - kampanya["fiyat"])} kazanç</span>')
        kmp_kart = f'''
      <div class="hp-kmp">
        <div class="hp-k-u">
          <span class="hp-k-rz">{t(kampanya['rozet'] or 'Kampanya')}</span>
          <span class="hp-k-ad">{t(kampanya['gramaj_etiket'])}</span>
        </div>
        <div class="hp-k-a">
          <b class="hp-k-yeni">{tl(kampanya['fiyat'])}</b>
          {kar}
        </div>
      </div>'''

    kargo_satiri = (f'      <p class="hero-kargo">{ikon("truck")} <b>Tüm siparişlerde</b> kargo bizden</p>'
                    if HEP_BEDAVA else
                    f'      <p class="hero-kargo">{ikon("truck")} <b>{tl(ESIK)} ve üzeri</b> alışverişlerde kargo bizden</p>')
    serit = ('<div class="hero-price">\n        ' + "\n        ".join(ogeler)
             + '\n      </div>' + kmp_kart + '\n' + kargo_satiri)
    s = isaretci_degistir(s, 'HERO-FIYAT', '      ' + serit)

    semalar = [urun_semasi(u) for u in URUNLER]
    s = isaretci_degistir(
        s, 'URUN-SEMA',
        '<script type="application/ld+json">\n' +
        json.dumps({"@context": "https://schema.org", "@graph": semalar}, ensure_ascii=False, indent=2) +
        '\n</script>')


    # SSS şemasını sayfadaki gerçek SSS bloklarından türet (ikisi ayrışmasın)
    sorular = re.findall(
        r'<h3 class="faq-h"><button[^>]*><span>(.*?)</span>.*?<div class="faq-a"><div>(.*?)</div></div>',
        s, re.S)
    if sorular:
        m = re.search(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', s, re.S)
        blok = json.loads(m.group(1))
        for dugum in blok.get('@graph', []):
            if dugum.get('@type') == 'FAQPage':
                dugum['mainEntity'] = [{
                    "@type": "Question",
                    "name": html.unescape(re.sub(r'<[^>]+>', '', soru)).strip(),
                    "acceptedAnswer": {"@type": "Answer",
                                       "text": html.unescape(re.sub(r'<[^>]+>', ' ', cevap)).replace('  ', ' ').strip()},
                } for soru, cevap in sorular]
        s = s[:m.start()] + ('<script type="application/ld+json">\n'
                             + json.dumps(blok, ensure_ascii=False, indent=2)
                             + '\n</script>') + s[m.end():]

    s = isaretci_degistir(s, 'SIPARIS', siparis_bolumu('/'))

    cfg = {
        "whatsapp": S['whatsapp'],
        "esik": ESIK,
        "hepbedava": HEP_BEDAVA,
        "saat": [int(x) for x in re.findall(r'(\d{1,2}):', S['calisma_saati'])] or [0, 24],
        "kargo": KARGO,
        "urunler": {u['id']: {"ad": u['tam_ad'], "fiyat": u['fiyat']} for u in URUNLER},
    }
    s = isaretci_degistir(
        s, 'URUN-JS',
        '<script>window.DY_CFG=' + json.dumps(cfg, ensure_ascii=False, separators=(',', ':')) + ';</script>')

    s = re.sub(r'(assets/site\.(?:css|js))\?v=\d+', rf'\1?v={VER}', s)
    open(p, 'w', encoding='utf-8').write(s)
    return p


# ─────────────────────────── main ───────────────────────────
def yaz(yol, icerik):
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    open(yol, 'w', encoding='utf-8').write(icerik)
    return f"  ✓ {os.path.relpath(yol, KOK):40s} {len(icerik.encode()):>7,} bayt"


def main():
    print("── domuzyagi.com üreticisi ──")
    satirlar = []

    for u in URUNLER:
        satirlar.append(yaz(os.path.join(KOK, 'urun', u['slug'], 'index.html'), urun_sayfasi(u)))

    for slug in MAKALE_SIRA:
        satirlar.append(yaz(os.path.join(KOK, slug, 'index.html'), makale_sayfasi(slug)))

    for slug, baslik, ozet, govde in bilgi_sayfalari():
        satirlar.append(yaz(os.path.join(KOK, slug, 'index.html'), bilgi_sayfasi(slug, baslik, ozet, govde)))

    satirlar.append(yaz(os.path.join(KOK, 'sitemap.xml'), sitemap()))
    satirlar.append(yaz(os.path.join(KOK, 'robots.txt'), robots()))

    f = feed()
    if f is None:
        satirlar.append("  ⚠ urunler.xml ÜRETİLMEDİ — products.json içinde site.kargo_ucreti null.")
    else:
        satirlar.append(yaz(os.path.join(KOK, 'urunler.xml'), f))

    anasayfa()
    satirlar.append(f"  ✓ index.html güncellendi (ürün kartları, hero şeridi, ürün şeması, v={VER})")

    print("\n".join(satirlar))
    print(f"── bitti · {len(URUNLER)} ürün ──")


if __name__ == '__main__':
    main()
