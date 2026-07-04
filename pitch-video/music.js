/* ============================================================
   SOMBA — THE FILM · generative soundtrack
   No audio files: everything is synthesized live with Web Audio.
   A-minor, 112 BPM. Intensity is driven scene-by-scene from video.js:
     0 pad + heartbeat pulse          (cold open)
     1 + kick + sub bass              (story begins)
     2 + hats + arp                   (moving)
     3 + clap, brighter filter        (full energy)
     4 breakdown: pad + arp only      (team / quiet moment)
   ============================================================ */

(function () {
  const BPM = 112;
  const SPB = 60 / BPM;          // seconds per beat
  const STEP = SPB / 4;          // 16th note
  const LOOKAHEAD = 0.14;        // schedule horizon (s)
  const TICK = 25;               // scheduler interval (ms)

  let ctx = null;
  let master, comp, duck, wet;
  let running = false;
  let muted = false;
  let intensity = 0;
  let step = 0;
  let nextTime = 0;
  let timer = null;

  // A minor land. Frequencies.
  const N = {
    A1: 55.0, C2: 65.41, D2: 73.42, E2: 82.41, F2: 87.31, G2: 98.0,
    A2: 110.0, C3: 130.81, D3: 146.83, E3: 164.81, G3: 196.0,
    A3: 220.0, C4: 261.63, D4: 293.66, E4: 329.63, G4: 392.0, A4: 440.0,
    B3: 246.94, F3: 174.61,
  };

  // 4-bar bass loop (one note per bar, walked on 16ths)
  const BASS_BARS = [N.A1, N.A1, N.F2 / 2, N.G2 / 2];
  // arp pool per bar (pentatonic-ish)
  const ARPS = [
    [N.A3, N.C4, N.E4, N.G4, N.E4, N.C4],
    [N.A3, N.C4, N.E4, N.A4, N.E4, N.C4],
    [N.F3, N.A3, N.C4, N.E4, N.C4, N.A3],
    [N.G3, N.B3, N.D4, N.G4, N.D4, N.B3],
  ];
  // pad chords per bar
  const PADS = [
    [N.A2, N.C3, N.E3],
    [N.A2, N.C3, N.E3],
    [N.F2, N.A2, N.C3],
    [N.G2, N.B3 / 2, N.D3],
  ];

  function init(audioCtx) {
    ctx = audioCtx;
    master = ctx.createGain();
    master.gain.value = 0.9;
    comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -18;
    comp.ratio.value = 6;
    comp.attack.value = 0.004;
    comp.release.value = 0.18;
    duck = ctx.createGain(); // sidechain bus (everything except kick)
    duck.gain.value = 1;
    wet = ctx.createGain();  // mute bus
    wet.gain.value = 1;
    duck.connect(comp);
    comp.connect(wet);
    wet.connect(master);
    master.connect(ctx.destination);
  }

  /* ---------- voices ---------- */
  function kick(t) {
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = "sine";
    o.frequency.setValueAtTime(150, t);
    o.frequency.exponentialRampToValueAtTime(46, t + 0.11);
    g.gain.setValueAtTime(1.0, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.3);
    o.connect(g); g.connect(comp); // kick skips the duck bus
    o.start(t); o.stop(t + 0.32);
    // sidechain pump
    duck.gain.cancelScheduledValues(t);
    duck.gain.setValueAtTime(0.35, t);
    duck.gain.linearRampToValueAtTime(1, t + 0.22);
  }

  function heartbeat(t) {
    // softer, rounder kick for the cold open
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = "sine";
    o.frequency.setValueAtTime(90, t);
    o.frequency.exponentialRampToValueAtTime(40, t + 0.14);
    g.gain.setValueAtTime(0.5, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.34);
    o.connect(g); g.connect(duck);
    o.start(t); o.stop(t + 0.36);
  }

  function hat(t, open) {
    const len = open ? 0.24 : 0.05;
    const buf = ctx.createBuffer(1, ctx.sampleRate * len, ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    const src = ctx.createBufferSource();
    src.buffer = buf;
    const hp = ctx.createBiquadFilter();
    hp.type = "highpass"; hp.frequency.value = 8200;
    const g = ctx.createGain();
    g.gain.setValueAtTime(open ? 0.16 : 0.11, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + len);
    src.connect(hp); hp.connect(g); g.connect(duck);
    src.start(t);
  }

  function clap(t) {
    const buf = ctx.createBuffer(1, ctx.sampleRate * 0.2, ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    const src = ctx.createBufferSource();
    src.buffer = buf;
    const bp = ctx.createBiquadFilter();
    bp.type = "bandpass"; bp.frequency.value = 1400; bp.Q.value = 1.4;
    const g = ctx.createGain();
    // triple-hit envelope
    g.gain.setValueAtTime(0.0, t);
    [0, 0.02, 0.04].forEach((off) => {
      g.gain.setValueAtTime(0.5, t + off);
      g.gain.exponentialRampToValueAtTime(0.08, t + off + 0.018);
    });
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.2);
    src.connect(bp); bp.connect(g); g.connect(duck);
    src.start(t);
  }

  function bass(t, f) {
    const o = ctx.createOscillator();
    const o2 = ctx.createOscillator();
    const lp = ctx.createBiquadFilter();
    const g = ctx.createGain();
    o.type = "sawtooth"; o.frequency.value = f;
    o2.type = "square"; o2.frequency.value = f / 2;
    lp.type = "lowpass";
    lp.frequency.setValueAtTime(intensity >= 3 ? 520 : 300, t);
    lp.frequency.exponentialRampToValueAtTime(120, t + STEP * 0.9);
    g.gain.setValueAtTime(0.34, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + STEP * 0.95);
    o.connect(lp); o2.connect(lp); lp.connect(g); g.connect(duck);
    o.start(t); o2.start(t);
    o.stop(t + STEP); o2.stop(t + STEP);
  }

  function pluck(t, f) {
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    const lp = ctx.createBiquadFilter();
    o.type = "triangle"; o.frequency.value = f;
    lp.type = "lowpass"; lp.frequency.value = 3400;
    g.gain.setValueAtTime(0.16, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.26);
    o.connect(lp); lp.connect(g);
    g.connect(duck);
    // dub echo
    const dl = ctx.createDelay(1);
    dl.delayTime.value = STEP * 3;
    const fb = ctx.createGain(); fb.gain.value = 0.32;
    const wetG = ctx.createGain(); wetG.gain.value = 0.4;
    g.connect(dl); dl.connect(fb); fb.connect(dl); dl.connect(wetG); wetG.connect(duck);
    o.start(t); o.stop(t + 0.3);
  }

  function padChord(t, freqs, dur) {
    freqs.forEach((f, i) => {
      [0.996, 1.004].forEach((det) => {
        const o = ctx.createOscillator();
        const g = ctx.createGain();
        const lp = ctx.createBiquadFilter();
        o.type = "sawtooth";
        o.frequency.value = f * det;
        lp.type = "lowpass";
        lp.frequency.setValueAtTime(700 + intensity * 260, t);
        g.gain.setValueAtTime(0, t);
        g.gain.linearRampToValueAtTime(0.045, t + dur * 0.3);
        g.gain.linearRampToValueAtTime(0.03, t + dur * 0.8);
        g.gain.linearRampToValueAtTime(0, t + dur);
        o.connect(lp); lp.connect(g); g.connect(duck);
        o.start(t); o.stop(t + dur + 0.05);
      });
    });
  }

  /* ---------- sequencer ---------- */
  function scheduleStep(s, t) {
    const bar = Math.floor(s / 16) % 4;
    const inBar = s % 16;
    const lvl = intensity;

    // pad: once per bar, always on (it IS the atmosphere)
    if (inBar === 0) padChord(t, PADS[bar], SPB * 4);

    if (lvl === 0) {
      // heartbeat: lub-dub on beat 1
      if (inBar === 0) heartbeat(t);
      if (inBar === 3) heartbeat(t);
      return;
    }

    if (lvl === 4) {
      // breakdown: pad + sparse arp, no drums
      if (inBar % 4 === 2) pluck(t, ARPS[bar][(s / 4) % 6 | 0]);
      return;
    }

    // kick four-on-the-floor
    if (inBar % 4 === 0) kick(t);
    // bass drives 8ths, skips the kick step for pocket
    if (lvl >= 1 && inBar % 2 === 0 && inBar % 4 !== 0) bass(t, BASS_BARS[bar]);
    if (lvl >= 2) {
      if (inBar % 2 === 1) hat(t, false);
      if (inBar === 14) hat(t, true);
      // arp on offbeat 8ths
      if (inBar % 2 === 0) pluck(t, ARPS[bar][(inBar / 2) % 6]);
    }
    if (lvl >= 3 && (inBar === 4 || inBar === 12)) clap(t);
  }

  function loop() {
    while (nextTime < ctx.currentTime + LOOKAHEAD) {
      scheduleStep(step, nextTime);
      step++;
      nextTime += STEP;
    }
  }

  /* ---------- one-shots for sync moments ---------- */
  function impact(when) {
    // boom + noise burst for scene-transition hits
    if (!ctx || !running) return;
    const t = ctx.currentTime + (when || 0);
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = "sine";
    o.frequency.setValueAtTime(120, t);
    o.frequency.exponentialRampToValueAtTime(30, t + 0.5);
    g.gain.setValueAtTime(0.9, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.8);
    o.connect(g); g.connect(comp);
    o.start(t); o.stop(t + 0.85);
    const buf = ctx.createBuffer(1, ctx.sampleRate * 0.4, ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
    const src = ctx.createBufferSource(); src.buffer = buf;
    const lp = ctx.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 2000;
    const ng = ctx.createGain(); ng.gain.setValueAtTime(0.4, t);
    ng.gain.exponentialRampToValueAtTime(0.001, t + 0.4);
    src.connect(lp); lp.connect(ng); ng.connect(comp);
    src.start(t);
  }

  function riser(dur) {
    // white-noise sweep up into a transition
    if (!ctx || !running) return;
    const t = ctx.currentTime;
    const len = dur || 1.2;
    const buf = ctx.createBuffer(1, ctx.sampleRate * len, ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    const src = ctx.createBufferSource(); src.buffer = buf;
    const bp = ctx.createBiquadFilter();
    bp.type = "bandpass"; bp.Q.value = 1.2;
    bp.frequency.setValueAtTime(300, t);
    bp.frequency.exponentialRampToValueAtTime(6000, t + len);
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.001, t);
    g.gain.exponentialRampToValueAtTime(0.22, t + len);
    g.gain.linearRampToValueAtTime(0.0, t + len + 0.05);
    src.connect(bp); bp.connect(g); g.connect(duck);
    src.start(t);
  }

  function ding(when) {
    // bright success chime (recovery healed, checks landing)
    if (!ctx || !running) return;
    const t = ctx.currentTime + (when || 0);
    [N.A4 * 2, N.E4 * 2].forEach((f, i) => {
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = "sine"; o.frequency.value = f;
      g.gain.setValueAtTime(0.0, t + i * 0.07);
      g.gain.linearRampToValueAtTime(0.18, t + i * 0.07 + 0.01);
      g.gain.exponentialRampToValueAtTime(0.001, t + i * 0.07 + 0.9);
      o.connect(g); g.connect(duck);
      o.start(t + i * 0.07); o.stop(t + i * 0.07 + 1);
    });
  }

  /* ---------- public api ---------- */
  window.Music = {
    start(audioCtx) {
      if (running) return;
      if (!ctx) init(audioCtx);
      running = true;
      step = 0;
      nextTime = ctx.currentTime + 0.06;
      timer = setInterval(loop, TICK);
    },
    stop() {
      running = false;
      if (timer) clearInterval(timer);
      timer = null;
    },
    pause() {
      if (timer) clearInterval(timer);
      timer = null;
    },
    resume() {
      if (!ctx || !running) return;
      nextTime = Math.max(nextTime, ctx.currentTime + 0.06);
      if (!timer) timer = setInterval(loop, TICK);
    },
    setIntensity(n) { intensity = n; },
    setMuted(m) {
      muted = m;
      if (wet) wet.gain.linearRampToValueAtTime(m ? 0 : 1, ctx.currentTime + 0.15);
    },
    get muted() { return muted; },
    impact, riser, ding,
    fadeOut(sec) {
      if (!wet) return;
      wet.gain.linearRampToValueAtTime(0, ctx.currentTime + (sec || 2));
    },
    fadeIn() {
      if (!wet || muted) return;
      wet.gain.linearRampToValueAtTime(1, ctx.currentTime + 0.4);
    },
  };
})();
