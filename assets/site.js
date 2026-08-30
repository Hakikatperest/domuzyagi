/* ============================================================
   Doğal Domuz Yağı — ortak script
   ============================================================ */
(function(){
'use strict';

/* Yapılandırma sayfadan gelir (_src/build.py yazar). */
var CFG     = window.DY_CFG || {};
var WA_NO   = CFG.whatsapp || '905516412065';
var ESIK    = CFG.esik     || 2500;
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

var nav = $('.nav'), burger = $('.burger'), navX = $('.nav-x'), scrim = $('.scrim');
function menu(ac){
  if(!nav) return;
  nav.classList.toggle('on', ac);
  if(scrim) scrim.classList.toggle('on', ac);
  document.body.style.overflow = ac ? 'hidden' : '';
}
if(burger) burger.addEventListener('click', function(){ menu(!nav.classList.contains('on')); });
if(navX)   navX.addEventListener('click', function(){ menu(false); });
if(scrim)  scrim.addEventListener('click', function(){ menu(false); });
if(nav) $$('.nav a').forEach(function(a){ a.addEventListener('click', function(){ menu(false); }); });

function kaydir(hedef){
  window.scrollTo({ top: hedef.getBoundingClientRect().top + window.scrollY - 84, behavior:'smooth' });
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
      document.body.style.overflow = 'hidden';
    });
  });
  var kapat = function(){ lb.classList.remove('on'); document.body.style.overflow = ''; };
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
  var bedava = ara >= ESIK || satirlar.bedava === true;

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
    fill.style.width = Math.min(100, (ara / ESIK) * 100) + '%';
    fill.classList.toggle('done', bedava);
  }
  if(txt) txt.classList.toggle('done', bedava);
  if(msg){
    msg.textContent = bedava ? 'Tebrikler, kargo bizden!'
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
      '\nKargo: ' + (bedava ? 'Ücretsiz (' + tl(ESIK) + ' üzeri)' : (KARGO !== null ? tl(KARGO) : 'Alıcıya ait'))
    : 'Merhaba, domuz yağı hakkında bilgi almak istiyorum.';
  $$('.wa-order').forEach(function(b){
    b.href = 'https://wa.me/' + WA_NO + '?text=' + encodeURIComponent(waMesaji);
  });

  /* mobil alt çubuk */
  var mt = $('.mbar-tot');
  if(mt){
    mt.style.display = ara ? 'flex' : 'none';
    var mv = $('.mbar-tot b'); if(mv) mv.textContent = tl(ara);
    var ml = $('.mbar-lbl');   if(ml) ml.textContent = ara ? 'Siparişi Gönder' : 'WhatsApp';
  }
}


/* ══════════ anasayfa: çoklu ürün sepeti ══════════ */

var cartList = $('.cart-list');
if(cartList){
  var sepet = {};

  function sepetiCiz(){
    var ara = 0, kutular = [], metin = [];

    Object.keys(URUNLER).forEach(function(k){
      var ad = sepet[k] || 0;
      if(!ad) return;
      var u = URUNLER[k], tutar = u.fiyat * ad;
      ara += tutar;
      kutular.push(
        '<div class="cart-row"><span class="n">' + u.ad + ' <i>× ' + ad + '</i></span>' +
        '<span class="p">' + tl(tutar) + '</span>' +
        '<button type="button" class="rm" data-rm="' + k + '" aria-label="Kaldır">' +
        '<svg class="ico"><use href="#i-x"></use></svg></button></div>'
      );
      metin.push(u.ad + ' × ' + ad + ' = ' + tl(tutar));
    });

    cartList.innerHTML = kutular.length ? kutular.join('')
      : '<div class="cart-empty">Henüz ürün seçmediniz — yukarıdaki ürünlerden adet ekleyin.</div>';

    Object.keys(URUNLER).forEach(function(k){
      var el = $('.p-sub[data-sub="' + k + '"]');
      if(el) el.innerHTML = sepet[k] ? 'Ara toplam: <b>' + tl(URUNLER[k].fiyat * sepet[k]) + '</b>' : '';
    });

    ozetiCiz({ metin: metin }, ara);
  }

  $$('.qty[data-p]').forEach(function(q){
    var k = q.getAttribute('data-p'), inp = $('input', q), eksi = $('[data-act="eksi"]', q);
    var uygula = function(v){
      v = Math.max(0, Math.min(99, v | 0));
      sepet[k] = v; inp.value = v; eksi.disabled = (v === 0);
      sepetiCiz();
    };
    eksi.addEventListener('click', function(){ uygula((sepet[k] || 0) - 1); });
    $('[data-act="arti"]', q).addEventListener('click', function(){ uygula((sepet[k] || 0) + 1); });
    inp.addEventListener('input', function(){ uygula(parseInt(inp.value, 10) || 0); });
    inp.addEventListener('blur',  function(){ inp.value = sepet[k] || 0; });
    uygula(0);
  });

  cartList.addEventListener('click', function(ev){
    var b = ev.target.closest('[data-rm]');
    if(!b) return;
    var k = b.getAttribute('data-rm');
    sepet[k] = 0;
    var inp = $('.qty[data-p="' + k + '"] input'); if(inp) inp.value = 0;
    var eksi = $('.qty[data-p="' + k + '"] [data-act="eksi"]'); if(eksi) eksi.disabled = true;
    sepetiCiz();
  });

  /* kart üzerindeki "Sipariş Ver" → 1 adet ekle + forma in */
  $$('[data-ekle]').forEach(function(b){
    b.addEventListener('click', function(ev){
      ev.preventDefault();
      var k = b.getAttribute('data-ekle');
      if(!sepet[k]){
        sepet[k] = 1;
        var inp = $('.qty[data-p="' + k + '"] input'); if(inp) inp.value = 1;
        var eksi = $('.qty[data-p="' + k + '"] [data-act="eksi"]'); if(eksi) eksi.disabled = false;
        sepetiCiz();
      }
      var t = $('#siparis'); if(t) kaydir(t);
    });
  });

  sepetiCiz();
}


/* ══════════ ürün sayfası: tek ürün adet kutusu ══════════ */

var buy = $('.buy');
if(buy){
  var bAd     = buy.getAttribute('data-ad');
  var bFiyat  = parseFloat(buy.getAttribute('data-fiyat')) || 0;
  var bBedava = buy.getAttribute('data-bedava') === '1';
  var bQty    = $('.qty', buy), bInp = $('input', bQty);
  var bEksi   = $('[data-act="eksi"]', bQty), bArti = $('[data-act="arti"]', bQty);

  var urunuCiz = function(){
    var ad = parseInt(bInp.value, 10);
    if(!ad || ad < 1) ad = 1;
    if(ad > 99) ad = 99;
    bInp.value = ad;
    bEksi.disabled = (ad === 1);

    var tutar = bFiyat * ad;
    var bv = $('.buy-v'); if(bv) bv.textContent = tl(tutar);

    var kEl = $('.buy-kargo');
    if(kEl){
      var bedava = bBedava || tutar >= ESIK;
      kEl.textContent = bedava ? 'Bu siparişte kargo ücretsiz.'
                               : 'Ücretsiz kargoya ' + tl(ESIK - tutar) + ' kaldı.';
      kEl.classList.toggle('done', bedava);
    }

    ozetiCiz({ metin: [bAd + ' × ' + ad + ' = ' + tl(tutar)], bedava: bBedava }, tutar);
  };

  bEksi.addEventListener('click', function(){ bInp.value = (parseInt(bInp.value,10)||1) - 1; urunuCiz(); });
  bArti.addEventListener('click', function(){ bInp.value = (parseInt(bInp.value,10)||1) + 1; urunuCiz(); });
  bInp.addEventListener('input', urunuCiz);
  bInp.addEventListener('blur',  urunuCiz);
  urunuCiz();
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
