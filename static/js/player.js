/**
 * PodWave — Reproductor fijo (static file, Unidad 2)
 * ---------------------------------------------------
 * Vanilla JavaScript (sin frameworks): reemplaza al componente Player.jsx
 * de la SPA React. Cualquier botón con clase `.btn-play` publica su pista
 * en el reproductor fijo inferior mediante atributos data-*.
 *
 * PERSISTENCIA entre páginas (diferencia SPA vs MPA):
 * en la SPA React el player nunca se desmontaba al navegar, pero en Django
 * (MPA) cada enlace recarga la página completa. Para conservar la música
 * al navegar, el estado del reproductor (pista, minuto y reproducción) se
 * guarda en sessionStorage y se restaura al cargar cada nueva página.
 *
 * POLÍTICA DE AUTOPLAY: al restaurar en una página recién cargada, algunos
 * navegadores bloquean audio.play() sin interacción del usuario. En ese
 * caso se muestra un aviso y el PRIMER clic del usuario en cualquier parte
 * de la página reanuda la música automáticamente (y también el clic sobre
 * el aviso o el botón ▶).
 *
 * Seguridad: la URL de audio proviene del servidor (base de datos validada
 * por el TrackForm en el backend), nunca de entrada directa del usuario.
 */
(function () {
  'use strict';

  var STORAGE_KEY = 'podwave_player';
  var SAVE_EVERY = 1; // segundos mínimos entre escrituras de timeupdate

  var player = document.getElementById('podwave-player');
  var audio = document.getElementById('podwave-audio');
  var titleEl = document.getElementById('player-title');
  var artistEl = document.getElementById('player-artist');
  var toggleBtn = document.getElementById('player-toggle');
  var closeBtn = document.getElementById('player-close');
  var barFill = document.getElementById('player-bar-fill');
  var currentEl = document.getElementById('player-current');
  var durationEl = document.getElementById('player-duration');
  var hintEl = document.getElementById('player-hint');

  if (!player || !audio) return;

  var pendingSeek = 0;        // segundo a restaurar cuando cargue el metadata
  var lastSave = 0;           // control del throttle de timeupdate
  var pendingResume = false;  // el audio debería sonar pero el navegador lo bloqueó

  // ---------- Persistencia (sessionStorage) ----------

  function readState() {
    try {
      return JSON.parse(sessionStorage.getItem(STORAGE_KEY) || 'null');
    } catch (e) {
      return null;
    }
  }

  function saveState() {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
        url: audio.currentSrc || audio.src,
        title: titleEl.textContent,
        artist: artistEl.textContent,
        t: audio.currentTime || 0,
        playing: !audio.paused && !audio.ended
      }));
    } catch (e) { /* storage lleno o bloqueado: se ignora */ }
  }

  function clearState() {
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch (e) { /* noop */ }
    pendingResume = false;
    hideHint();
  }

  // Guarda al abandonar la página (navegación interna del MPA).
  window.addEventListener('pagehide', saveState);

  // ---------- UI ----------

  // Formatea segundos a mm:ss (equivalente a fmt() en Player.jsx).
  function fmt(s) {
    if (!isFinite(s) || s < 0) return '00:00';
    var m = Math.floor(s / 60);
    var sec = Math.floor(s % 60);
    return (
      String(m).padStart(2, '0') + ':' + String(sec).padStart(2, '0')
    );
  }

  // Alterna el icono de play/pausa.
  function setPlaying(playing) {
    toggleBtn.innerHTML = playing ? '&#10074;&#10074;' : '&#9654;';
    toggleBtn.setAttribute('aria-label', playing ? 'Pausar' : 'Reproducir');
  }

  function showHint() {
    if (hintEl) hintEl.hidden = false;
  }

  function hideHint() {
    if (hintEl) hintEl.hidden = true;
  }

  // Intenta reproducir. Si el navegador lo bloquea (política de autoplay),
  // marca la reanudación pendiente: el primer clic del usuario la retoma.
  function tryPlay() {
    var p = audio.play();
    if (p && typeof p.then === 'function') {
      p.then(function () {
        setPlaying(true);
        pendingResume = false;
        hideHint();
      }).catch(function () {
        pendingResume = true;
        setPlaying(false);
        showHint();
      });
    }
  }

  // Muestra el reproductor y carga una pista.
  function loadTrack(url, title, artist) {
    titleEl.textContent = title || '—';
    artistEl.textContent = artist || '—';
    audio.src = url;
    audio.load();
    player.hidden = false;
    tryPlay();
    saveState();
  }

  // ---------- Delegación de eventos: botones .btn-play de la página ----------

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.btn-play');
    if (!btn) return;
    e.preventDefault();
    loadTrack(btn.dataset.url, btn.dataset.title, btn.dataset.artist);
  });

  // ---------- Reanudación tras bloqueo de autoplay ----------
  // El PRIMER clic o tecla del usuario en la página reanuda la música si
  // el navegador la había pausado al cargar (sticky activation del origen).
  function resumeOnce() {
    if (pendingResume) tryPlay();
  }
  document.addEventListener('pointerdown', resumeOnce);
  document.addEventListener('keydown', resumeOnce);

  // El aviso también es clicable para reanudar.
  if (hintEl) {
    hintEl.addEventListener('click', tryPlay);
  }

  // ---------- Controles del reproductor ----------

  toggleBtn.addEventListener('click', function () {
    if (audio.paused) {
      tryPlay();
    } else {
      audio.pause();
    }
  });

  closeBtn.addEventListener('click', function () {
    audio.pause();
    audio.removeAttribute('src');
    audio.load();
    player.hidden = true;
    clearState(); // el cierre manual también limpia la persistencia
  });

  // ---------- Sincronización barra de progreso / tiempos ----------

  audio.addEventListener('timeupdate', function () {
    if (audio.duration > 0) {
      barFill.style.width = (audio.currentTime / audio.duration) * 100 + '%';
    }
    currentEl.textContent = fmt(audio.currentTime);
    // Throttle: persistir como mucho una vez por segundo.
    if (audio.currentTime - lastSave >= SAVE_EVERY) {
      lastSave = audio.currentTime;
      saveState();
    }
  });

  audio.addEventListener('loadedmetadata', function () {
    durationEl.textContent = fmt(audio.duration || 0);
    // Restaurar el minuto guardado tras una navegación entre páginas.
    if (pendingSeek > 0 && isFinite(audio.duration)) {
      audio.currentTime = Math.min(pendingSeek, audio.duration - 0.5);
      pendingSeek = 0;
    }
    // Reintento: algunos navegadores rechazan play() antes de cargar
    // el metadata y aquí ya hay datos suficientes para reintentar.
    if (pendingResume) tryPlay();
  });

  audio.addEventListener('play', function () {
    setPlaying(true);
    pendingResume = false;
    hideHint();
    saveState();
  });
  audio.addEventListener('pause', function () {
    setPlaying(false);
    saveState();
  });
  audio.addEventListener('ended', function () {
    setPlaying(false);
    clearState(); // la pista terminó: no hay nada que restaurar
  });

  // ---------- Restauración al cargar la página ----------

  var saved = readState();
  if (saved && saved.url) {
    titleEl.textContent = saved.title || '—';
    artistEl.textContent = saved.artist || '—';
    audio.src = saved.url;
    audio.load();
    player.hidden = false;
    currentEl.textContent = fmt(saved.t || 0);
    pendingSeek = saved.t || 0;
    if (saved.playing) {
      // Intenta continuar donde iba. Con audio local (media/ de Django)
      // el arranque es inmediato; si el navegador bloquea el autoplay,
      // el primer clic del usuario lo reanuda (ver resumeOnce).
      tryPlay();
    } else {
      setPlaying(false);
    }
  }
})();
