/**
 * theme.js — Void Codex theme switcher
 * Themes: stalker (default), forge, amber, infested, ash
 * Persists to localStorage under key 'void-theme'
 */

const THEME_NAMES = ['stalker', 'forge', 'amber', 'infested', 'ash'];
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

// Run immediately (no DOMContentLoaded needed — script loads after body)
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initTheme);
} else {
  initTheme();
}
