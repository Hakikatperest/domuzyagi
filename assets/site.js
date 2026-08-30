/* ============================================================
   Doğal Domuz Yağı — ortak script
   ============================================================ */
(function(){
'use strict';

/* Yapılandırma sayfadan gelir (_src/build.py yazar). */
var CFG     = window.DY_CFG || {};
var WA_NO   = CFG.whatsapp || '905516412065';
var ESIK    = CFG.esik     || 2500;
var HEPBEDAVA = CFG.hepbedava === true;   // eşiksiz ücretsiz kargo
var KARGO   = (CFG.kargo === 0 || CFG.kargo) ? CFG.kargo : null;
var URUNLER = CFG.urunler  || {};

function tl(n){ return n.toLocaleString('tr-TR') + ' ₺'; }
function $(s,c){ return (c||document).querySelector(s); }
function $$(s,c){ return Array.prototype.slice.call((c||document).querySelectorAll(s)); }


/* ══════════ arayüz ══════════ */

$$('.yil').forEach(function(e){ e.textContent = new Date().getFullYear(); });

var hdr = $('.hdr');
if(hdr){
  var golge = function(){ hdr.classList.toggle('stuck', window.scrollY > 8); };
  golge(); window.addEventListener('scroll', golge, {passive:true});
}

/* Duyuru şeridi ve başlık birlikte yapışkan duruyor. Şeridin yüksekliği
   satır kaymasıyla değiştiği için ölçülüp CSS değişkenine yazılır; başlık
   da çıpa kaydırmaları da bu değere göre hizalanır.                      */
var duyuru = $('.announce');
try{
  if(window.CSS && CSS.supports &&
     (CSS.supports('backdrop-filter','blur(1px)') || CSS.supports('-webkit-backdrop-filter','blur(1px)'))){
    document.documentElement.classList.add('bf');
  }
}catch(e){}
function yapiskanOlc(){
  var d = duyuru ? duyuru.offsetHeight : 0;
  var h = hdr ? hdr.offsetHeight : 0;
  var k = document.documentElement.style;
  k.setProperty('--duyuru-h', d + 'px');
  k.setProperty('--yapiskan-h', (d + h + 14) + 'px');
}
yapiskanOlc();
window.addEventListener('resize', yapiskanOlc, {passive:true});
window.addEventListener('load', yapiskanOlc);

/* ══════════ gövde kaydırma kilidi ══════════
   Sayfa köküne overflow-x:hidden yazılı. Böyle bir durumda tarayıcı taşma
   değerini KÖKTEN görüntü alanına yayar ve body'nin overflow'unu artık
   dikkate almaz — eski kilit body'ye yazdığı için menü açıkken sayfa arkada
   kaymaya devam ediyordu. Kilit artık kökte kuruluyor; iOS'ta tek başına kök
   yetmediğinden panel dışındaki dokunma hareketi ayrıca iptal ediliyor.
   Gövde SABİTLENMİYOR — sabitlenirse yapışkan başlık referansını kaybeder.
   Menü ve galeri aynı kilidi paylaşır: biri kapanınca öteki hâlâ açıksa
   kilit çözülmez.                                                          */
var kilitler = {}, kilitY = 0;

function kilitSayisi(){
  var n = 0, a;
  for(a in kilitler){ if(Object.prototype.hasOwnProperty.call(kilitler, a)) n++; }
  return n;
}
/* Kökteki overflow:hidden iOS'ta bazen yetmiyor. Gövdeyi position:fixed
   yapmak kesin çözüm ama yapışkan başlığın referansını bozuyor; onun yerine
   panel dışındaki parmak hareketini doğrudan iptal ediyoruz. */
function dokunmaEngeli(ev){
  var panel = document.querySelector('.nav.on');
  if(panel && panel.contains(ev.target)) return;   /* açık menü kendi içinde kaysın */
  if(ev.cancelable) ev.preventDefault();
}
function kilidiKur(){
  var k = document.documentElement, b = document.body;
  kilitY = window.pageYOffset || k.scrollTop || 0;
  var bosluk = window.innerWidth - k.clientWidth;   /* kaybolan kaydırma çubuğu */
  if(bosluk > 0) b.style.paddingRight = bosluk + 'px';
  k.classList.add('kilit');
  document.addEventListener('touchmove', dokunmaEngeli, {passive:false});
}
function kilidiCoz(){
  var k = document.documentElement, b = document.body;
  document.removeEventListener('touchmove', dokunmaEngeli, {passive:false});
  k.classList.remove('kilit');
  b.style.paddingRight = '';
  if(Math.abs((window.pageYOffset || 0) - kilitY) > 1){
    var akis = k.style.scrollBehavior;
    k.style.scrollBehavior = 'auto';   /* html{scroll-behavior:smooth} geri dönüşü animasyona çevirmesin */
    window.scrollTo(0, kilitY);
    k.style.scrollBehavior = akis;
  }
}
function govdeKilit(ad, ac){
  ac = !!ac;
  if(ac === !!kilitler[ad]) return;
  if(ac) kilitler[ad] = 1; else delete kilitler[ad];
  var n = kilitSayisi();
  if(ac && n === 1) kilidiKur();
  else if(!ac && n === 0) kilidiCoz();
}


/* ══════════ mobil menü ══════════ */
var nav = $('.nav'), burger = $('.burger'), navX = $('.nav-x'), scrim = $('.scrim');
function menuAcik(){ return !!nav && nav.classList.contains('on'); }
function menu(ac){
  if(!nav) return;
  ac = !!ac;
  if(ac === menuAcik()) return;                    /* durum değişmiyorsa kilide dokunma */
  nav.classList.toggle('on', ac);
  if(scrim) scrim.classList.toggle('on', ac);
  if(burger) burger.setAttribute('aria-expanded', ac ? 'true' : 'false');
  govdeKilit('menu', ac);
  try{
    if(ac){ if(navX) navX.focus({preventScroll:true}); }
    else if(burger && nav.contains(document.activeElement)) burger.focus({preventScroll:true});
  }catch(e){}
}
if(burger){
  burger.setAttribute('aria-expanded', 'false');
  burger.addEventListener('click', function(){ menu(!menuAcik()); });
}
if(navX)   navX.addEventListener('click', function(){ menu(false); });
if(scrim)  scrim.addEventListener('click', function(){ menu(false); });
if(nav) $$('.nav a').forEach(function(a){ a.addEventListener('click', function(){ menu(false); }); });

/* Esc kapatsın; masaüstü genişliğine geçilince menü açık kalmasın. */
document.addEventListener('keydown', function(ev){ if(ev.key === 'Escape') menu(false); });
window.addEventListener('resize', function(){
  if(window.innerWidth > 1040) menu(false);
}, {passive:true});

function oz(v){
  return String(v).replace(/&/g,'&amp;').replace(/</g,'&lt;')
                  .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

/* Alt şeridin yüksekliği sepet doldukça değişir; gövde payı ve çevrimiçi
   balonu bu ölçüyü takip etsin diye CSS değişkenine yazılır. */
function olcMbar(){
  var m = $('.mbar');
  var y = m ? m.offsetHeight : 0;
  document.documentElement.style.setProperty('--mbar-h', (y || 74) + 'px');
}
window.addEventListener('resize', olcMbar, {passive:true});
window.addEventListener('load', olcMbar);

function kaydir(hedef){
  var pay = parseInt(getComputedStyle(document.documentElement)
              .getPropertyValue('--yapiskan-h'), 10) || 110;
  window.scrollTo({ top: hedef.getBoundingClientRect().top + window.scrollY - pay, behavior:'smooth' });
}
$$('a[href^="#"]').forEach(function(a){
  a.addEventListener('click', function(ev){
    var h = a.getAttribute('href');
    if(h === '#' || h.length < 2) return;
    var t = document.getElementById(h.slice(1));
    if(!t) return;
    ev.preventDefault();
    kaydir(t);
  });
});

$$('.faq-q').forEach(function(q){
  q.addEventListener('click', function(){
    var madde = q.closest('.faq'), cevap = $('.faq-a', madde), acik = madde.classList.contains('open');
    $$('.faq').forEach(function(f){
      f.classList.remove('open');
      $('.faq-a', f).style.maxHeight = null;
      $('.faq-q', f).setAttribute('aria-expanded','false');
    });
    if(!acik){
      madde.classList.add('open');
      cevap.style.maxHeight = cevap.scrollHeight + 'px';
      q.setAttribute('aria-expanded','true');
    }
  });
});

var fx = $$('.fx');
if(fx.length){
  if(!('IntersectionObserver' in window)){
    fx.forEach(function(e){ e.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function(girisler){
      girisler.forEach(function(g){
        if(!g.isIntersecting) return;
        var kardes = Array.prototype.slice.call(g.target.parentElement.children)
                       .filter(function(c){ return c.classList.contains('fx'); });
        setTimeout(function(){ g.target.classList.add('in'); }, kardes.indexOf(g.target) * 70);
        io.unobserve(g.target);
      });
    }, { threshold:.08, rootMargin:'0px 0px -40px 0px' });
    fx.forEach(function(e){ io.observe(e); });
  }
}

var lb = $('.lb');
if(lb){
  var lbImg = $('img', lb), lbCap = $('.lb-cap', lb);
  $$('[data-lb]').forEach(function(el){
    el.addEventListener('click', function(){
      lbImg.src = el.getAttribute('data-lb');
      lbCap.textContent = el.getAttribute('data-lb-cap') || '';
      lb.classList.add('on');
      govdeKilit('lb', true);
    });
  });
  var kapat = function(){ lb.classList.remove('on'); govdeKilit('lb', false); };
  lb.addEventListener('click', kapat);
  document.addEventListener('keydown', function(e){ if(e.key === 'Escape') kapat(); });
}


/* ══════════ sipariş özeti — tek kaynak ══════════
   Hem anasayfadaki sepet hem ürün sayfasındaki adet kutusu buraya yazar.
   Ekranda ne varsa onu günceller; olmayan öğeyi sessizce atlar.        */

var waMesaji = 'Merhaba, domuz yağı hakkında bilgi almak istiyorum.';
var sonAra   = 0;

function ozetiCiz(satirlar, ara){
  sonAra = ara;
  var bedava = HEPBEDAVA || ara >= ESIK || satirlar.bedava === true;

  var el;
  if((el = $('.sum-ara')))    el.textContent = tl(ara);
  if((el = $('.sum-toplam'))) el.textContent = tl(ara);
  if((el = $('.sum-kargo'))){
    el.textContent = bedava ? 'Ücretsiz' : (KARGO !== null ? tl(KARGO) : 'Alıcıya ait');
    var satir = el.closest('.sum-row');
    if(satir) satir.classList.toggle('free', bedava);
  }

  var fill = $('.ship-fill'), txt = $('.ship-txt'), msg = $('.ship-msg');
  if(fill){
    fill.style.width = (HEPBEDAVA ? 100 : Math.min(100, (ara / ESIK) * 100)) + '%';
    fill.classList.toggle('done', bedava);
  }
  if(txt) txt.classList.toggle('done', bedava);
  if(msg){
    msg.textContent = HEPBEDAVA ? 'Tüm siparişlerde kargo ücretsiz.'
      : bedava ? 'Tebrikler, kargo bizden!'
      : (ara === 0 ? 'Ücretsiz kargo için ' + tl(ESIK) + ' ve üzeri sipariş verin.'
                   : 'Ücretsiz kargoya ' + tl(ESIK - ara) + ' kaldı.');
  }

  /* form için düz metin */
  var duz = satirlar.metin.join(' · ');
  if((el = $('.of-urun')))   el.value = duz ? duz + '  —  Toplam: ' + tl(ara) : '';
  if((el = $('.of-ozet-v'))) el.textContent = duz || 'Henüz ürün seçilmedi';

  /* WhatsApp kısayolu */
  waMesaji = satirlar.metin.length
    ? 'Merhaba, sipariş vermek istiyorum:\n' + satirlar.metin.map(function(m){ return '• ' + m; }).join('\n') +
      '\n\nAra toplam: ' + tl(ara) +
      '\nKargo: ' + (HEPBEDAVA ? 'Ücretsiz' : bedava ? 'Ücretsiz (' + tl(ESIK) + ' üzeri)' : (KARGO !== null ? tl(KARGO) : 'Alıcıya ait'))
    : 'Merhaba, domuz yağı hakkında bilgi almak istiyorum.';
  $$('.wa-order').forEach(function(b){
    b.href = 'https://wa.me/' + WA_NO + '?text=' + encodeURIComponent(waMesaji);
  });

  /* mobil alt şerit: sepet satırı ayrı, çağrı butonları kendi satırında.
     Toplam yazısı butonları daraltmaz; kullanıcı listeden ürün çıkarabilir. */
  var mSum = $('.mbar-sum'), mList = $('.mbar-list');
  if(mSum){
    var kalem = satirlar.kalem || [];
    var adet  = 0;
    kalem.forEach(function(x){ adet += x.adet; });

    /* Şerit sepet boşken de durur; müşteri oku açıp listeden ürün ekleyebilsin. */
    var m;
    if((m = $('.mbar-n')))  { m.textContent = adet; m.hidden = (adet === 0); }
    if((m = $('.mbar-v')))  m.textContent = tl(ara);
    if((m = $('.mbar-ad'))) m.textContent = !adet ? 'Sepetiniz boş'
                                          : kalem.length === 1 ? kalem[0].ad
                                          : adet + ' ürün seçildi';
    if((m = $('.mbar-alt'))){
      m.textContent = !adet ? 'Ürün eklemek için dokunun'
        : kalem.length === 1 ? kalem[0].adet + ' adet · ' + tl(kalem[0].tutar)
        : kalem.map(function(x){ return x.ad + ' ×' + x.adet; }).join('  ·  ');
    }
    if((m = $('.mbar-lbl'))) m.textContent = adet ? 'Siparişi Gönder' : 'WhatsApp';

    if(mList){
      /* Liste TÜM ürünleri gösterir — sepette olmayanlar 0 adetle durur ki
         müşteri şeridi açıp doğrudan buradan ekleyebilsin. Sepette olan satır
         .dolu sınıfını alır: adı koyulaşır, tutarı vurgulanır, çöp kutusu çıkar. */
      var secili = {};
      kalem.forEach(function(x){ secili[x.k] = x; });

      mList.innerHTML = Object.keys(URUNLER).map(function(k){
        var u = URUNLER[k], x = secili[k], n = x ? x.adet : 0;
        return '<div class="mrow' + (n ? ' dolu' : '') + '">' +
          '<span class="mrow-n">' + oz(u.ad) + '</span>' +
          '<div class="qty-xs">' +
            '<button type="button" data-mact="eksi" data-k="' + oz(k) + '"' + (n ? '' : ' disabled') +
              ' aria-label="' + oz(u.ad) + ' adedini azalt">' +
              '<svg class="ico"><use href="#i-minus"></use></svg></button>' +
            '<b>' + n + '</b>' +
            '<button type="button" data-mact="arti" data-k="' + oz(k) + '"' +
              ' aria-label="' + oz(u.ad) + ' adedini artır">' +
              '<svg class="ico"><use href="#i-plus"></use></svg></button>' +
          '</div>' +
          '<span class="mrow-p">' + tl(n ? u.fiyat * n : u.fiyat) + '</span>' +
          (n ? '<button type="button" class="mrow-x" data-mrm="' + oz(k) + '" ' +
                 'aria-label="' + oz(u.ad) + ' ürününü sepetten çıkar">' +
                 '<svg class="ico"><use href="#i-trash"></use></svg></button>'
             : '<span class="mrow-bos" aria-hidden="true"></span>') +
        '</div>';
      }).join('') + (adet
        ? '<button type="button" class="mbar-bosalt">' +
          '<svg class="ico"><use href="#i-trash"></use></svg> Sepeti boşalt</button>'
        : '');
    }
  }
  olcMbar();
}


/* ══════════ sepet — tüm sayfalarda ortak, sayfa değişince korunur ══════════
   Anasayfadaki ürün kartları, sipariş bölümündeki seçici ve ürün sayfasındaki
   adet kutusu aynı sepete yazar. Sepet tarayıcıda saklanır; müşteri ürün
   sayfasına geçtiğinde seçimini baştan yapmak zorunda kalmaz.              */

var SEPET_ANAHTAR = 'dy_sepet_v1';
/* Sepet ömrü 1 saat: 3 gündü, ertesi gün siteyi açan müşteri hero kutularını
   seçili görüp "butonlar kendiliğinden tıklanmış" sanıyordu. Damga her yazmada
   tazelendiği için aynı ziyaret boyunca (sayfa gezintisi, yenileme) sepet durur;
   ara verilip geri dönülünce temiz açılır. */
var SEPET_OMUR    = 3600 * 1000;               /* 1 saat */

function sepetOku(){
  try{
    var v = JSON.parse(localStorage.getItem(SEPET_ANAHTAR) || 'null');
    if(!v || !v.t || Date.now() - v.t > SEPET_OMUR) return {};
    var temiz = {};
    Object.keys(v.s || {}).forEach(function(k){
      if(!URUNLER[k]) return;                  /* listeden kalkmış ürünü düşür */
      var n = parseInt(v.s[k], 10) || 0;
      if(n > 0) temiz[k] = Math.min(99, n);
    });
    return temiz;
  }catch(e){ return {}; }
}

function sepetYaz(s){
  try{ localStorage.setItem(SEPET_ANAHTAR, JSON.stringify({ t: Date.now(), s: s })); }catch(e){}
}

var qtyKutulari = $$('.qty[data-p]');
/* Motor, ürün listesi geldiği HER sayfada çalışır — adet kutusu olup olmaması
   şart değil. Makale ve politika sayfalarında kutu yok ama alt şeritteki sepet
   yine görünmeli; aksi hâlde kullanıcı sepeti sıfırlanmış sanıyor. Liste
   içindeki adet/çıkar düğmeleri olay delegasyonuyla çalıştığı için statik
   kutuya ihtiyaç duymaz. */
if(Object.keys(URUNLER).length){
  var sepet   = sepetOku();
  var cartList = $('.cart-list');
  var buyEl   = $('.buy');
  var buyId   = buyEl && buyEl.getAttribute('data-urun');
  var buyAd   = buyEl && buyEl.getAttribute('data-ad');
  var buyFiyat = buyEl ? (parseFloat(buyEl.getAttribute('data-fiyat')) || 0) : 0;

  /* ürün sayfasına sepet boşken girildiyse o ürün 1 adet önseçili gelsin */
  if(buyId && !Object.keys(sepet).length) sepet[buyId] = 1;

  /* Hero fiyat şeridindeki kutular: sepette adedi olan altın çerçeveli görünür,
     sağ üstte adet rozeti çıkar. Kutular <button>, ekleme aşağıda bağlanıyor. */
  var hpKutulari = $$('[data-hp]');
  function hpEsitle(){
    hpKutulari.forEach(function(b){
      var k = b.getAttribute('data-hp'), v = sepet[k] || 0;
      b.classList.toggle('is-secili', v > 0);
      b.setAttribute('aria-pressed', v > 0 ? 'true' : 'false');
      var rz = $('[data-hp-ad="' + k + '"]', b);
      if(rz) rz.textContent = v ? String(v) : '';
    });
  }

  function kutulariEsitle(){
    qtyKutulari.forEach(function(q){
      var k = q.getAttribute('data-p'), v = sepet[k] || 0;
      var inp = $('input', q);
      if(inp && document.activeElement !== inp) inp.value = v;
      var eksi = $('[data-act="eksi"]', q);
      if(eksi) eksi.disabled = (v === 0);
      var kutu = q.closest('.pick-i');
      if(kutu) kutu.classList.toggle('is-secili', v > 0);
    });
  }

  function sepetiCiz(){
    var ara = 0, kutular = [], metin = [], kalemler = [];

    Object.keys(URUNLER).forEach(function(k){
      var ad = sepet[k] || 0;
      if(!ad) return;
      var u = URUNLER[k], tutar = u.fiyat * ad;
      ara += tutar;
      kutular.push(
        '<div class="cart-row"><span class="n">' + oz(u.ad) + ' <i>× ' + ad + '</i></span>' +
        '<span class="p">' + tl(tutar) + '</span>' +
        '<button type="button" class="rm" data-rm="' + k + '" aria-label="Kaldır">' +
        '<svg class="ico"><use href="#i-x"></use></svg></button></div>'
      );
      metin.push(u.ad + ' × ' + ad + ' = ' + tl(tutar));
      kalemler.push({ k: k, ad: u.ad, adet: ad, tutar: tutar });
    });

    if(cartList){
      cartList.innerHTML = kutular.length ? kutular.join('')
        : '<div class="cart-empty">Henüz ürün seçmediniz — yandaki listeden adet ekleyin.</div>';
    }

    Object.keys(URUNLER).forEach(function(k){
      var deger = sepet[k] ? 'Ara toplam: <b>' + tl(URUNLER[k].fiyat * sepet[k]) + '</b>' : '';
      $$('.p-sub[data-sub="' + k + '"]').forEach(function(el){ el.innerHTML = deger; });
    });

    /* ürün sayfasındaki tekil toplam kutusu */
    if(buyEl){
      var bAd = sepet[buyId] || 0;
      var bv = $('.buy-v'); if(bv) bv.textContent = tl(buyFiyat * bAd);
      var kEl = $('.buy-kargo');
      if(kEl){
        var bedavaB = HEPBEDAVA || buyEl.getAttribute('data-bedava') === '1' || (buyFiyat * bAd) >= ESIK;
        kEl.textContent = !bAd ? 'Adet seçin.'
          : bedavaB ? 'Bu siparişte kargo ücretsiz.'
                    : 'Ücretsiz kargoya ' + tl(ESIK - buyFiyat * bAd) + ' kaldı.';
        kEl.classList.toggle('done', bedavaB && bAd > 0);
      }
    }

    kutulariEsitle();
    hpEsitle();
    sepetYaz(sepet);
    ozetiCiz({ metin: metin, kalem: kalemler }, ara);
  }

  function uygula(k, v){
    v = Math.max(0, Math.min(99, v | 0));
    if(v) sepet[k] = v; else delete sepet[k];
    sepetiCiz();
  }

  qtyKutulari.forEach(function(q){
    var k = q.getAttribute('data-p'), inp = $('input', q);
    $('[data-act="eksi"]', q).addEventListener('click', function(){ uygula(k, (sepet[k] || 0) - 1); });
    $('[data-act="arti"]', q).addEventListener('click', function(){ uygula(k, (sepet[k] || 0) + 1); });
    inp.addEventListener('input', function(){ uygula(k, parseInt(inp.value, 10) || 0); });
    inp.addEventListener('blur',  function(){ inp.value = sepet[k] || 0; });
  });

  if(cartList){
    cartList.addEventListener('click', function(ev){
      var b = ev.target.closest('[data-rm]');
      if(b) uygula(b.getAttribute('data-rm'), 0);
    });
  }

  /* Hero fiyat kutusu: her dokunuş sepete 1 adet ekler. Sayfa kaydırılmaz —
     kutu seçili hâle geçer ve alt şeritteki sepet özeti kendiliğinden güncellenir. */
  hpKutulari.forEach(function(b){
    b.addEventListener('click', function(){
      /* Aç/kapa: ilk tık sepete 1 adet ekler, ikinci tık ürünü tamamen çıkarır.
         Adet artırma sepette ve ürün kartında yapılıyor, burada değil. */
      var k = b.getAttribute('data-hp');
      uygula(k, sepet[k] ? 0 : 1);
    });
  });

  /* kart üzerindeki "Sepete Ekle" → yoksa 1 adet ekle + forma in */
  $$('[data-ekle]').forEach(function(b){
    b.addEventListener('click', function(ev){
      ev.preventDefault();
      var k = b.getAttribute('data-ekle');
      if(!sepet[k]) uygula(k, 1);
      var t = $('#siparis'); if(t) kaydir(t);
    });
  });

  /* alt şerit: özeti aç/kapa, listeden adet değiştir veya ürünü çıkar */
  var mSumBtn = $('.mbar-sum'), mListEl = $('.mbar-list');
  if(mSumBtn && mListEl){
    mSumBtn.addEventListener('click', function(){
      var acik = mSumBtn.getAttribute('aria-expanded') === 'true';
      mSumBtn.setAttribute('aria-expanded', acik ? 'false' : 'true');
      mListEl.hidden = acik;
      olcMbar();
    });

    mListEl.addEventListener('click', function(ev){
      var b = ev.target.closest('.mbar-bosalt,[data-mrm],[data-mact]');
      if(!b) return;
      if(b.classList.contains('mbar-bosalt')){
        Object.keys(sepet).forEach(function(k){ delete sepet[k]; });
        sepetiCiz();
        return;
      }
      if(b.hasAttribute('data-mrm')){ uygula(b.getAttribute('data-mrm'), 0); return; }
      var k = b.getAttribute('data-k');
      uygula(k, (sepet[k] || 0) + (b.getAttribute('data-mact') === 'arti' ? 1 : -1));
    });
  }

  /* başka sekmede sepet değişirse burada da güncellensin */
  window.addEventListener('storage', function(ev){
    if(ev.key === SEPET_ANAHTAR){ sepet = sepetOku(); sepetiCiz(); }
  });

  sepetiCiz();
}


/* ══════════ çevrimiçi bildirim balonu ══════════
   Sayfanın yarısı geçilince açılır. Kapatılırsa o oturumda bir daha çıkmaz.
   Çalışma saati dışında hiç gösterilmez — "çevrimiçiyiz" yanlış olmasın.   */

var onl = $('.onl');
if(onl){
  var saat    = CFG.saat || [0, 24];
  var simdi   = new Date().getHours();
  var acikmi  = saat.length === 2 ? (simdi >= saat[0] && simdi < saat[1]) : true;
  var kapandi = false;
  try{ kapandi = sessionStorage.getItem('dy_onl_kapali') === '1'; }catch(e){}

  var onlKapat = function(){
    onl.classList.remove('on');
    setTimeout(function(){ onl.hidden = true; }, 400);
    try{ sessionStorage.setItem('dy_onl_kapali', '1'); }catch(e){}
  };
  $('.onl-x', onl).addEventListener('click', onlKapat);

  if(acikmi && !kapandi){
    var onlBak = function(){
      var yol = document.documentElement.scrollHeight - window.innerHeight;
      if(yol <= 0 || (window.scrollY / yol) < 0.5) return;
      window.removeEventListener('scroll', onlBak);
      onl.hidden = false;
      requestAnimationFrame(function(){
        requestAnimationFrame(function(){ onl.classList.add('on'); });
      });
    };
    window.addEventListener('scroll', onlBak, {passive:true});
    onlBak();
  }
}


/* ══════════ sipariş formu ══════════ */

var form = $('.oform');
if(form){
  var durum  = $('.of-durum', form);
  var gonder = $('.of-gonder', form);
  var kvkk   = $('.of-kvkk', form);
  var uzak   = form.getAttribute('action');
  var alanlar = $$('.of-f', form);

  var dogrula = function(){
    var ilk = null;
    alanlar.forEach(function(f){
      var g = $('input', f) || $('textarea', f);
      if(!g) return;
      if(!g.required && !g.value.trim()){ f.classList.remove('err'); return; }

      var bos    = g.required && !g.value.trim();
      var eposta = g.type === 'email' && g.value.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(g.value.trim());
      var tel    = g.type === 'tel'   && g.value.replace(/\D/g,'').length < 10;
      var kotu   = bos || eposta || tel;

      f.classList.toggle('err', kotu);
      if(kotu){
        var h = $('.of-hata', f);
        if(h) h.textContent = bos ? 'Bu alan zorunlu.'
              : (eposta ? 'Geçerli bir e-posta yazın.' : 'Telefon numarası eksik görünüyor.');
        if(!ilk) ilk = g;
      }
    });

    var onay = $('input', kvkk);
    kvkk.classList.toggle('err', !onay.checked);
    if(!onay.checked){
      var hk = $('.of-hata', kvkk);
      if(hk) hk.textContent = 'Devam etmek için onay vermelisiniz.';
      if(!ilk) ilk = onay;
    }

    if(!ilk && !sonAra){
      durum.className = 'of-durum on no';
      durum.textContent = 'Önce yukarıdan ürün ve adet seçin.';
      var u = $('#urunler'); if(u) kaydir(u);
      return false;
    }

    if(ilk){
      ilk.focus({preventScroll:true});
      window.scrollTo({ top: ilk.getBoundingClientRect().top + window.scrollY - 120, behavior:'smooth' });
    }
    return !ilk;
  };

  alanlar.forEach(function(f){
    var g = $('input', f) || $('textarea', f);
    if(g) g.addEventListener('input', function(){ f.classList.remove('err'); });
  });
  $('input', kvkk).addEventListener('change', function(){ kvkk.classList.remove('err'); });

  form.addEventListener('submit', function(ev){
    if($('.of-tuzak', form).value){ ev.preventDefault(); return; }
    if(!dogrula()){ ev.preventDefault(); return; }

    if(uzak){
      gonder.disabled = true;
      durum.className = 'of-durum on';
      durum.textContent = 'Gönderiliyor…';
      return;
    }

    ev.preventDefault();
    var al = function(n){ var g = form.querySelector('[name="' + n + '"]'); return g ? g.value.trim() : ''; };
    var metin = [
      waMesaji, '',
      '── Teslimat bilgileri ──',
      'Ad Soyad: '  + al('Ad Soyad'),
      'Telefon: '   + al('Telefon'),
      'İl / İlçe: ' + al('İl / İlçe'),
      al('E-posta') ? 'E-posta: ' + al('E-posta') : null,
      'Adres: '     + al('Adres'),
      al('Not') ? 'Not: ' + al('Not') : null
    ].filter(function(x){ return x !== null; }).join('\n');

    durum.className = 'of-durum on ok';
    durum.textContent = 'Siparişiniz WhatsApp’a aktarılıyor — açılan pencereden gönder’e basmanız yeterli.';
    window.open('https://wa.me/' + WA_NO + '?text=' + encodeURIComponent(metin), '_blank', 'noopener');
  });
}

})();
