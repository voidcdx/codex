/* ── Orokin Rain — sparse ambient background animation ── */
(function () {
  const canvas = document.getElementById('matrix-bg');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  // Orokin-aesthetic characters: runic, alchemical, geometric, mathematical
  const CHARS = 'ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ◈◉◊◆◇▣▤▦▨▩∆∇∑∞≋⊕⊗⊞⊟⎔⌘∯∰⋈⋉⋊⋄⋆⟁⟂⟃⟐⟡';
  const COL_W    = 18;   // px per column
  const FONT_SZ  = 13;   // px
  const TRAIL    = 12;   // chars per drop
  const MAX_FRAC = 0.40; // drops die at this fraction of screen height
  const SPAWN_P  = 0.0015; // probability a dead col spawns per frame
  const SPEED    = 0.4;  // rows per frame

  let cols = 0;
  let drops = [];    // [{y, active, cooldown}]

  function rand(min, max) { return min + Math.random() * (max - min); }
  function randChar() { return CHARS[Math.floor(Math.random() * CHARS.length)]; }

  function resize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    cols = Math.floor(canvas.width / COL_W);
    drops = Array.from({ length: cols }, () => ({
      y:        -rand(0, 40),     // staggered start offscreen
      active:   false,
      cooldown: rand(0, 6000),    // ms before first possible spawn
    }));
    // Clear canvas on resize
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }

  let lastTime = 0;

  function draw(ts) {
    const dt = ts - lastTime;
    lastTime = ts;

    // Fade existing trails
    ctx.fillStyle = 'rgba(5,5,5,0.07)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.font = `${FONT_SZ}px 'Rajdhani', sans-serif`;

    const maxY = canvas.height * MAX_FRAC;

    for (let i = 0; i < cols; i++) {
      const d = drops[i];

      // Tick cooldown for inactive drops
      if (!d.active) {
        d.cooldown -= dt;
        if (d.cooldown <= 0 && Math.random() < SPAWN_P) {
          d.active = true;
          d.y = 0;
        }
        continue;
      }

      const x = i * COL_W;
      const yPx = d.y * COL_W;

      // Draw trail (fading)
      for (let t = 0; t < TRAIL; t++) {
        const rowY = yPx - t * COL_W;
        if (rowY < 0) continue;
        const alpha = (1 - t / TRAIL) * 0.6;
        if (t === 0) {
          // Head — bright
          ctx.fillStyle = `rgba(220,20,60,${0.9})`;
        } else {
          ctx.fillStyle = `rgba(139,0,0,${alpha})`;
        }
        ctx.fillText(randChar(), x, rowY);
      }

      d.y += SPEED;

      // Kill drop when it passes the max fraction line
      if (yPx > maxY) {
        d.active   = false;
        d.cooldown = rand(3000, 9000);
        d.y        = 0;
      }
    }

    requestAnimationFrame(draw);
  }

  window.addEventListener('resize', resize);
  resize();
  requestAnimationFrame(draw);
})();
