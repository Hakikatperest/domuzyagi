/* ============================================================
   Doğal Domuz Yağı — ortak script
   ============================================================ */
(function(){
'use strict';

/* Yapılandırma sayfadan gelir (_src/build.py yazar). Yedek değerler
   yalnızca DY_CFG hiç basılmamışsa devreye girer. */
var CFG     = window.DY_CFG || {};
var WA_NO   = CFG.whatsapp || '905516412065';
var ESIK    = CFG.esik     || 2500;        /* ücretsiz kargo eşiği */
var URUNLER = CFG.urunler  || {};

function tl(n){ return n.toLocaleString('tr-TR') + ' ₺'; }
function $(s,c){ return (c||document).querySelector(s); }
function $$(s,c){ return Array.prototype.slice.call((c||document).querySelectorAll(s)); }

/* ── yıl ── */
$$('.yil').forEach(function(e){ e.textContent = new Date().getFullYear(); });

/* ── header gölgesi ── */
var hdr = $('.hdr');
if(hdr){
  var onScroll = function(){ hdr.classList.toggle('stuck', window.scrollY > 8); };
  onScroll(); window.addEventListener('scroll', onScroll, {passive:true});
}

/* ── mobil menü ── */
var nav = $('.nav'), burger = $('.burger'), navX = $('.nav-x'), scrim = $('.scrim');
function menu(open){
  if(!nav) return;
  nav.classList.toggle('on', open);
  if(scrim) scrim.classList.toggle('on', open);
  document.body.style.overflow = open ? 'hidden' : '';
}
if(burger) burger.addEventListener('click', function(){ menu(!nav.classList.contains('on')); });
if(navX)   navX.addEventListener('click', function(){ menu(false); });
if(scrim)  scrim.addEventListener('click', function(){ menu(false); });
if(nav) $$('.nav a').forEach(function(a){ a.addEventListener('click', function(){ menu(false); }); });

/* ── yumuşak kaydırma ── */
$$('a[href^="#"]').forEach(function(a){
  a.addEventListener('click', function(e){
    var h = a.getAttribute('href');
    if(h === '#' || h.length < 2) return;
    var t = document.getElementById(h.slice(1));
    if(!t) return;
    e.preventDefault();
    window.scrollTo({ top: t.getBoundingClientRect().top + window.scrollY - 84, behavior:'smooth' });
  });
});

/* ── SSS akordiyon ── */
$$('.faq-q').forEach(function(q){
  q.addEventListener('click', function(){
    var item = q.closest('.faq'), a = $('.faq-a', item), acik = item.classList.contains('open');
    $$('.faq').forEach(function(f){
      f.classList.remove('open');
      $('.faq-a', f).style.maxHeight = null;
      $('.faq-q', f).setAttribute('aria-expanded','false');
    });
    if(!acik){
      item.classList.add('open');
      a.style.maxHeight = a.scrollHeight + 'px';
      q.setAttribute('aria-expanded','true');
    }
  });
});

/* ── giriş animasyonu ── */
var fx = $$('.fx');
if(fx.length){
  if(!('IntersectionObserver' in window)){
    fx.forEach(function(e){ e.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function(ents){
      ents.forEach(function(en){
        if(!en.isIntersecting) return;
        var kar = Array.prototype.slice.call(en.target.parentElement.children).filter(function(c){ return c.classList.contains('fx'); });
        setTimeout(function(){ en.target.classList.add('in'); }, kar.indexOf(en.target) * 70);
        io.unobserve(en.target);
      });
    }, { threshold:.08, rootMargin:'0px 0px -40px 0px' });
    fx.forEach(function(e){ io.observe(e); });
  }
}

/* ── lightbox ── */
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
  var kapat = function(){ lb.classList.remove('on'); document.body.style.overflow=''; };
  lb.addEventListener('click', kapat);
  document.addEventListener('keydown', function(e){ if(e.key === 'Escape') kapat(); });
}

/* ── sipariş paneli ── */
var cartList = $('.cart-list');
if(cartList){
  var sepet = {};

  function wa(mesaj){ return 'https://wa.me/' + WA_NO + '?text=' + encodeURIComponent(mesaj); }

  function ciz(){
    var ara = 0, satirlar = [], metin = [];

    Object.keys(URUNLER).forEach(function(k){
      var ad = sepet[k] || 0;
      if(!ad) return;
      var u = URUNLER[k], tutar = u.fiyat * ad;
      ara += tutar;
      satirlar.push(
        '<div class="cart-row"><span class="n">' + u.ad + ' <i>× ' + ad + '</i></span>' +
        '<span class="p">' + tl(tutar) + '</span>' +
        '<button class="rm" data-rm="' + k + '" aria-label="Kaldır"><svg class="ico"><use href="#i-x"></use></svg></button></div>'
      );
      metin.push('• ' + u.ad + ' × ' + ad + ' = ' + tl(tutar));
    });

    var bedava = ara >= ESIK;

    cartList.innerHTML = satirlar.length ? satirlar.join('') :
      '<div class="cart-empty">Henüz ürün seçmediniz — yukarıdaki ürünlerden adet ekleyin.</div>';

    $('.sum-ara').textContent = tl(ara);
    var kargoEl = $('.sum-kargo');
    kargoEl.textContent = bedava ? 'Ücretsiz' : 'Alıcıya ait';
    kargoEl.closest('.sum-row').classList.toggle('free', bedava);
    $('.sum-toplam').textContent = tl(ara);

    var kalan = Math.max(0, ESIK - ara);
    var oran  = Math.min(100, (ara / ESIK) * 100);
    var fill  = $('.ship-fill'), txt = $('.ship-txt');
    fill.style.width = oran + '%';
    fill.classList.toggle('done', bedava);
    txt.classList.toggle('done', bedava);
    $('.ship-msg').textContent = bedava
      ? 'Tebrikler, kargo bizden!'
      : (ara === 0
          ? 'Ücretsiz kargo için ' + tl(ESIK) + ' ve üzeri sipariş verin.'
          : 'Ücretsiz kargoya ' + tl(kalan) + ' kaldı.');

    var mesaj = satirlar.length
      ? 'Merhaba, sipariş vermek istiyorum:\n' + metin.join('\n') +
        '\n\nAra toplam: ' + tl(ara) +
        '\nKargo: ' + (bedava ? 'Ücretsiz (2.500 ₺ üzeri)' : 'Alıcıya ait')
      : 'Merhaba, domuz yağı hakkında bilgi almak istiyorum.';

    $$('.wa-order').forEach(function(b){ b.href = wa(mesaj); });

    /* mobil bar */
    var mt = $('.mbar-tot');
    if(mt){
      mt.style.display = ara ? 'flex' : 'none';
      $('.mbar-tot b').textContent = tl(ara);
      var mb = $('.mbar .wa-order');
      if(mb) $('.mbar-lbl', mb).textContent = ara ? 'Siparişi Gönder' : 'WhatsApp';
    }

    /* kart altı ara toplamlar */
    Object.keys(URUNLER).forEach(function(k){
      var el = $('.p-sub[data-sub="' + k + '"]');
      if(!el) return;
      var ad = sepet[k] || 0;
      el.innerHTML = ad ? 'Ara toplam: <b>' + tl(URUNLER[k].fiyat * ad) + '</b>' : '';
    });
  }

  $$('.qty').forEach(function(q){
    var k = q.getAttribute('data-p'), inp = $('input', q);
    var uygula = function(v){
      v = Math.max(0, Math.min(99, v|0));
      sepet[k] = v; inp.value = v;
      $('[data-act="eksi"]', q).disabled = (v === 0);
      ciz();
    };
    $('[data-act="eksi"]', q).addEventListener('click', function(){ uygula((sepet[k]||0) - 1); });
    $('[data-act="arti"]', q).addEventListener('click', function(){ uygula((sepet[k]||0) + 1); });
    inp.addEventListener('input',  function(){ uygula(parseInt(inp.value,10) || 0); });
    inp.addEventListener('blur',   function(){ inp.value = sepet[k] || 0; });
    uygula(0);
  });

  cartList.addEventListener('click', function(e){
    var b = e.target.closest('[data-rm]');
    if(!b) return;
    var k = b.getAttribute('data-rm');
    sepet[k] = 0;
    var inp = $('.qty[data-p="' + k + '"] input');
    if(inp) inp.value = 0;
    var eksi = $('.qty[data-p="' + k + '"] [data-act="eksi"]');
    if(eksi) eksi.disabled = true;
    ciz();
  });

  /* "Sipariş Ver" → panele kaydır + 1 adet ekle */
  $$('[data-ekle]').forEach(function(b){
    b.addEventListener('click', function(e){
      e.preventDefault();
      var k = b.getAttribute('data-ekle');
      if(!sepet[k]){
        var inp = $('.qty[data-p="' + k + '"] input');
        sepet[k] = 1;
        if(inp) inp.value = 1;
        var eksi = $('.qty[data-p="' + k + '"] [data-act="eksi"]');
        if(eksi) eksi.disabled = false;
        ciz();
      }
      var t = $('#siparis');
      if(t) window.scrollTo({ top: t.getBoundingClientRect().top + window.scrollY - 84, behavior:'smooth' });
    });
  });

  ciz();
}

/* ── tekil ürün sipariş kutusu (ürün detay sayfası) ── */
var buy = $('.buy');
if(buy){
  var bAd     = buy.getAttribute('data-ad');
  var bFiyat  = parseFloat(buy.getAttribute('data-fiyat')) || 0;
  var bBedava = buy.getAttribute('data-bedava') === '1';
  var bQty    = $('.qty', buy);
  var bInp    = $('input', bQty);
  var bEksi   = $('[data-act="eksi"]', bQty);
  var bArti   = $('[data-act="arti"]', bQty);

  var bCiz = function(){
    var ad = parseInt(bInp.value, 10);
    if(!ad || ad < 1) ad = 1;
    if(ad > 99) ad = 99;
    bInp.value = ad;

    var tutar  = bFiyat * ad;
    var bedava = bBedava || tutar >= ESIK;

    $('.buy-v').textContent = tl(tutar);
    bEksi.disabled = (ad === 1);

    var kEl = $('.buy-kargo');
    kEl.textContent = bedava ? 'Bu siparişte kargo ücretsiz.'
                             : 'Ücretsiz kargoya ' + tl(ESIK - tutar) + ' kaldı.';
    kEl.classList.toggle('done', bedava);

    var mesaj = 'Merhaba, sipariş vermek istiyorum:\n• ' + bAd + ' × ' + ad + ' = ' + tl(tutar) +
                '\n\nToplam: ' + tl(tutar) +
                '\nKargo: ' + (bedava ? 'Ücretsiz' : 'Alıcıya ait');
    $$('.wa-order').forEach(function(b){
      b.href = 'https://wa.me/' + WA_NO + '?text=' + encodeURIComponent(mesaj);
    });

    var mt = $('.mbar-tot');
    if(mt){
      mt.style.display = 'flex';
      $('.mbar-tot b').textContent = tl(tutar);
      var ml = $('.mbar-lbl');
      if(ml) ml.textContent = 'Siparişi Gönder';
    }
  };

  bEksi.addEventListener('click', function(){ bInp.value = (parseInt(bInp.value,10)||1) - 1; bCiz(); });
  bArti.addEventListener('click', function(){ bInp.value = (parseInt(bInp.value,10)||1) + 1; bCiz(); });
  bInp.addEventListener('input', bCiz);
  bInp.addEventListener('blur',  bCiz);
  bCiz();
}
})();
