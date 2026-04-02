/**
 * theme.js — Void Codex theme switcher
 * Themes: stalker (default), jade, ash
 * Persists to localStorage under key 'void-theme'
 */

const THEME_NAMES = ['stalker', 'jade', 'ash'];
const THEME_DEFAULT = 'stalker';
const LS_KEY = 'void-theme';

function applyTheme(name) {
  THEME_NAMES.forEach(t => document.body.classList.remove('theme-' + t));
  if (name !== THEME_DEFAULT) {
    document.body.classList.add('theme-' + name);
  }
  localStorage.setItem(LS_KEY, name);
  document.querySelectorAll('.theme-dot').forEach(dot => {
    dot.classList.toggle('active', dot.dataset.theme === name);
  });
}

function initTheme() {
  const saved = localStorage.getItem(LS_KEY) || THEME_DEFAULT;
  applyTheme(saved);
  document.querySelectorAll('.theme-dot').forEach(dot => {
    dot.addEventListener('click', () => applyTheme(dot.dataset.theme));
  });
}

function initBackToTop() {
  const btn = document.getElementById('back-to-top');
  if (!btn) return;

  // Inner scroll containers (desktop uses these; mobile uses window)
  const SCROLL_SELECTORS = ['.content', '.live-wrap', '.factions-wrap'];

  function checkScroll(scrollTop) {
    btn.classList.toggle('visible', scrollTop > 200);
  }

  window.addEventListener('scroll', () => checkScroll(window.scrollY), { passive: true });

  SCROLL_SELECTORS.forEach(sel => {
    const el = document.querySelector(sel);
    if (el) el.addEventListener('scroll', () => checkScroll(el.scrollTop), { passive: true });
  });

  btn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    SCROLL_SELECTORS.forEach(sel => {
      const el = document.querySelector(sel);
      if (el) el.scrollTo({ top: 0, behavior: 'smooth' });
    });
  });
}

// Run immediately (no DOMContentLoaded needed — script loads after body)
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => { initTheme(); initBackToTop(); });
} else {
  initTheme();
  initBackToTop();
}
