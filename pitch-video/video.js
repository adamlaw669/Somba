/* ============================================================
   SOMBA — THE FILM · timeline, scenes, transitions, controls
   Fixed 1920×1080 design space scaled to viewport.
   One anime.js master timeline; music cues fired on playback.
   ============================================================ */

(function () {
  "use strict";

  const stage = document.getElementById("stage");
  const scenesRoot = document.getElementById("scenes");
  const fx = document.getElementById("fx");

  /* ---------------- stage scaling ---------------- */
  function fit() {
    const s = Math.min(innerWidth / 1920, innerHeight / 1080);
    stage.style.transform = `scale(${s})`;
    stage.style.left = `${(innerWidth - 1920 * s) / 2}px`;
    stage.style.top = `${(innerHeight - 1080 * s) / 2}px`;
  }
  addEventListener("resize", fit);
  fit();

  /* ---------------- svg icon helpers ---------------- */
  const SW = 'stroke-width="5" stroke-linecap="round" stroke-linejoin="round" fill="none"';
  const icon = {
    dumbbell: (c, s = 56) => `<svg width="${s}" height="${s}" viewBox="0 0 64 64" stroke="${c}" ${SW}><rect x="6" y="24" width="10" height="16" rx="3"/><rect x="48" y="24" width="10" height="16" rx="3"/><rect x="14" y="18" width="8" height="28" rx="3"/><rect x="42" y="18" width="8" height="28" rx="3"/><line x1="22" y1="32" x2="42" y2="32"/></svg>`,
    school: (c, s = 56) => `<svg width="${s}" height="${s}" viewBox="0 0 64 64" stroke="${c}" ${SW}><path d="M8 24 32 12l24 12-24 12z"/><path d="M18 30v14c0 4 28 4 28 0V30"/><line x1="56" y1="24" x2="56" y2="40"/></svg>`,
    play: (c, s = 56) => `<svg width="${s}" height="${s}" viewBox="0 0 64 64" stroke="${c}" ${SW}><rect x="8" y="12" width="48" height="40" rx="8"/><path d="M27 24v16l14-8z" fill="${c}" stroke="none"/></svg>`,
    wifi: (c, s = 56) => `<svg width="${s}" height="${s}" viewBox="0 0 64 64" stroke="${c}" ${SW}><path d="M10 28c12-12 32-12 44 0"/><path d="M18 38c8-8 20-8 28 0"/><circle cx="32" cy="48" r="4" fill="${c}" stroke="none"/></svg>`,
    piggy: (c, s = 56) => `<svg width="${s}" height="${s}" viewBox="0 0 64 64" stroke="${c}" ${SW}><path d="M14 34c0-10 9-16 19-16 11 0 18 7 18 15 0 6-3 10-8 13v6h-8v-4h-8v4h-8v-7c-3-2-5-6-5-11z"/><line x1="26" y1="26" x2="38" y2="26"/><circle cx="44" cy="30" r="1.6" fill="${c}" stroke="none"/></svg>`,
    gear: (c, s = 34, cls = "") => `<svg class="gear ${cls}" width="${s}" height="${s}" viewBox="0 0 64 64" stroke="${c}" ${SW}><circle cx="32" cy="32" r="9"/><path d="M32 8v8M32 48v8M8 32h8M48 32h8M15 15l6 6M43 43l6 6M49 15l-6 6M21 43l-6 6"/></svg>`,
    person: (c, s = 40) => `<svg width="${s}" height="${s}" viewBox="0 0 64 64" stroke="${c}" ${SW}><circle cx="32" cy="22" r="10"/><path d="M12 54c2-12 10-18 20-18s18 6 20 18"/></svg>`,
    book: (c, s = 52) => `<svg width="${s}" height="${s}" viewBox="0 0 64 64" stroke="${c}" ${SW}><path d="M10 12h20v40H14a4 4 0 0 1-4-4z"/><path d="M54 12H34v40h16a4 4 0 0 0 4-4z"/><line class="bk-line" x1="16" y1="24" x2="26" y2="24"/><line class="bk-line" x1="16" y1="32" x2="26" y2="32"/><line class="bk-line" x1="38" y1="24" x2="48" y2="24"/></svg>`,
    radar: (c, s = 52) => `<svg width="${s}" height="${s}" viewBox="0 0 64 64" stroke="${c}" ${SW}><circle cx="32" cy="32" r="24"/><circle cx="32" cy="32" r="13" opacity="0.5"/><line class="rd-arm" x1="32" y1="32" x2="52" y2="16"/><circle cx="32" cy="32" r="3" fill="${c}" stroke="none"/></svg>`,
    key: (c, s = 52) => `<svg width="${s}" height="${s}" viewBox="0 0 64 64" stroke="${c}" ${SW}><circle cx="20" cy="32" r="10"/><line x1="30" y1="32" x2="54" y2="32"/><line x1="46" y1="32" x2="46" y2="42"/><line x1="54" y1="32" x2="54" y2="40"/></svg>`,
  };

  const psMark = (s = 34) =>
    `<svg class="ps-mark" width="${s}" height="${s}" viewBox="0 0 64 64"><rect x="6" y="8" width="52" height="9" rx="4.5"/><rect x="6" y="23" width="40" height="9" rx="4.5"/><rect x="6" y="38" width="52" height="9" rx="4.5"/><rect x="6" y="53" width="30" height="9" rx="4.5"/></svg>`;

  const nombaMark = () =>
    `<svg viewBox="0 0 64 64" fill="none" stroke="#0a0a0a" stroke-width="9" stroke-linecap="round"><path d="M14 46 32 18l18 28"/><path d="M22 34h20" opacity="0.85"/></svg>`;

  /* ---------------- scene table ---------------- */
  const S = {
    open:   [0, 14000],
    problem:[14000, 36000],
    market: [36000, 54000],
    insight:[54000, 78000],
    states: [78000, 100000],
    ledger: [100000, 122000],
    versus: [122000, 142000],
    model:  [142000, 158000],
    gymflow:[158000, 180000],
    finale: [180000, 206500],
  };
  const TOTAL = 206500;

  /* ============================================================
     scene DOM
     ============================================================ */
  function el(html) {
    const t = document.createElement("template");
    t.innerHTML = html.trim();
    return t.content.firstChild;
  }

  /* ---- S1 open ---- */
  const s1 = el(`
    <div class="scene th-black s1" id="sc-open">
      <svg class="s1-ecg" viewBox="0 0 1920 220" preserveAspectRatio="none">
        <path class="ecg-path" d="M0 110 H600 l30 0 18 -70 26 132 18 -62 h60 H1050 l30 0 18 -70 26 132 18 -62 h60 H1920"/>
      </svg>
      <div class="s1-badge">
        <div class="nomba-mark">${nombaMark()}</div>
        <div class="team">NOMBA &times; DEVCAREER 2026 &mdash; TEAM SETLD</div>
      </div>
      <div class="s1-core">
        <p class="s1-kicker kicker">RECURRING BILLING <span class="dot">&middot;</span> RECOVERY <span class="dot">&middot;</span> RECONCILIATION</p>
        <h1 class="s1-title display">
          <span class="s1-letter">S</span><span class="s1-letter o-letter">O</span><span class="s1-letter">M</span><span class="s1-letter">B</span><span class="s1-letter">A</span>
        </h1>
        <div class="s1-tagwrap"><span class="s1-tag mono"></span><span class="s1-tag caret"></span></div>
      </div>
      <svg class="s1-squig squig" viewBox="0 0 640 520">
        <path class="sq-path" d="M40 480 C 240 420, 120 300, 260 260 C 420 215, 470 360, 380 400 C 290 440, 280 240, 430 170 C 540 120, 600 80, 620 30"/>
      </svg>
    </div>`);

  /* ---- S2 problem ---- */
  const merchants = [
    ["gym", "GymFlow", "gym memberships", icon.dumbbell("#0a0a0a")],
    ["school", "Brightsteps", "school fees", icon.school("#0a0a0a")],
    ["stream", "NollyBox", "streaming", icon.play("#0a0a0a")],
    ["isp", "SwiftNet", "internet plans", icon.wifi("#0a0a0a")],
    ["save", "KoloSave", "savings plans", icon.piggy("#0a0a0a")],
  ];
  const s2 = el(`
    <div class="scene th-white s2" id="sc-problem">
      <p class="kicker s2-kicker">01 <span class="dot">/</span> THE PROBLEM</p>
      <h2 class="s2-head">Every subscription business on Nomba rebuilds the <span class="u">same billing engine</span>. Badly.</h2>
      <div class="merchant-row">
        ${merchants
          .map(
            (m) => `
          <div class="merchant">
            <div class="m-ic">${m[3]}</div>
            <div class="m-name">${m[1]}</div>
            <div class="m-sub">${m[2]}</div>
            <div class="gears">${icon.gear("#0a0a0a", 30, "spin")}${icon.gear("#0a0a0a", 22, "spin2")}${icon.gear("#0a0a0a", 30, "spin")}</div>
            <div class="m-tag">retry &middot; dunning &middot; ledger</div>
          </div>`
          )
          .join("")}
      </div>
      <div class="s2-fall">
        <div class="fail-line mono">charge.failed &mdash; insufficient_funds</div>
        <div class="s2-gone">A renewal fails silently. The customer is <span class="u">gone</span> &mdash; without deciding to leave.</div>
        <div class="avatar-row">
          ${[0, 1, 2, 3].map((i) => `<div class="avatar av-${i}">${icon.person("#0a0a0a")}</div>`).join("")}
        </div>
      </div>
      <div class="s2-stamp display">INVOLUNTARY CHURN</div>
    </div>`);

  /* ---- S3 market ---- */
  const s3 = el(`
    <div class="scene th-yellow s3" id="sc-market">
      <p class="kicker">02 <span class="dot">/</span> THE MARKET</p>
      <h2 class="s3-big" style="margin-top:34px"><span class="num display c-700">$0</span><br/>moved through Nigeria&rsquo;s rails in 2024.</h2>
      <div class="s3-sub mono">&#8358;1.07 quadrillion &middot; NIBSS-tracked &middot; and it keeps compounding</div>
      <div class="funnel">
        <div class="fun-band f1"><div class="fb-k">TAM &mdash; ALL DIGITAL PAYMENTS</div><div class="fb-v">$1.5&nbsp;TRILLION</div><div class="fb-s">annual GTV</div></div>
        <div class="fun-band f2"><div class="fb-k">SAM &mdash; RECURRING BILLING</div><div class="fb-v">$150&nbsp;BILLION</div><div class="fb-s">subscriptions &middot; utilities &middot; insurance &middot; content</div></div>
        <div class="fun-band f3"><div class="fb-k">SOM &mdash; SOMBA YEAR 1&ndash;2</div><div class="fb-v">$1.5&nbsp;BILLION</div><div class="fb-s">~1% of the recurring segment</div></div>
      </div>
      <div class="s3-ticks">
        <div class="s3-tick"><div class="tv display c-11b">0</div><div class="tl">NIP transactions in 2024</div></div>
        <div class="s3-tick"><div class="tv display c-60k">0</div><div class="tl">businesses selling subscriptions<br/>on Paystack alone</div></div>
      </div>
      <div class="pay-pill">${psMark(40)} <span>proven by <b>Paystack</b> &mdash; and still underserved</span></div>
    </div>`);

  /* ---- S4 insight ---- */
  const pairs = [
    ["empty_account", "reschedule for payday"],
    ["hard_decline", "straight to transfer"],
    ["soft_decline", "one retry, then fall back"],
    ["timeout", "freeze &amp; verify"],
    ["fraud_signal", "stop &amp; notify"],
  ];
  const s4 = el(`
    <div class="scene th-black s4" id="sc-insight">
      <p class="kicker" style="color:#6f6f68">03 <span class="dot">/</span> THE INSIGHT</p>
      <h2 class="s4-title display" style="margin-top:26px">
        <span class="t-timing">TIMING,</span><br/>
        <span class="t-retry">NOT RETRYING.<span class="slash"></span></span>
      </h2>
      <div class="s4-stage">
        <div class="wallet-box">
          <svg class="wallet-svg" width="220" height="190" viewBox="0 0 220 190">
            <rect x="10" y="30" width="200" height="150" rx="22" fill="none" stroke="#3a3a34" stroke-width="6"/>
            <rect class="w-fill" x="22" y="42" width="176" height="126" rx="14" fill="#ffc907" transform="scale(1,0)" transform-origin="110 168"/>
            <rect x="150" y="86" width="60" height="40" rx="12" fill="#0a0a0a" stroke="#3a3a34" stroke-width="6"/>
            <circle cx="180" cy="106" r="7" fill="#5c5c56"/>
          </svg>
          <div class="wallet-label mono w-lab">balance: &#8358;0</div>
        </div>
        <div class="retry-x rx-0" style="left:70px; top:30px">&times;</div>
        <div class="retry-x rx-1" style="left:180px; top:110px">&times;</div>
        <div class="retry-x rx-2" style="left:110px; top:210px">&times;</div>
        <div class="cal">
          ${Array.from({ length: 14 }, (_, i) => {
            const d = i + 17;
            const pay = d === 28;
            return `<div class="cal-day ${pay ? "payday" : ""}" data-d="${d}">${pay ? '<span class="pd-tag mono">PAYDAY &darr;</span>' : ""}${d}</div>`;
          }).join("")}
        </div>
        <div class="charge-dart"></div>
        <img class="s4-clock a-float" src="./assets/clock.png" alt=""/>
        <div class="pairs">
          ${pairs
            .map(
              (p) => `
            <div class="pair">
              <div class="p-from">${p[0]}</div>
              <div class="p-arrow">&darr;</div>
              <div class="p-to">${p[1]}</div>
            </div>`
            )
            .join("")}
        </div>
      </div>
    </div>`);

  /* ---- S5 lifecycle ---- */
  const railStates = ["trialing", "active", "past_due", "payment_uncertain"];
  const sideStates = ["paused", "cancelled", "expired"];
  const s5 = el(`
    <div class="scene th-black s5" id="sc-states">
      <p class="kicker s5-kicker">04 <span class="dot">/</span> THE PRODUCT</p>
      <h2 class="s5-head"><span class="n7">7</span> lifecycle states. One spine.</h2>
      <div class="rail-wrap">
        <div class="rail-line"><div class="rl-fill"></div></div>
        <div class="orb"></div>
        <div class="rail">
          ${railStates
            .map(
              (st) => `
            <div class="state-pill sp-${st}">${st === "payment_uncertain" ? '<span class="sp-tag mono">FREEZE &amp; VERIFY &mdash; THE DIFFERENTIATOR</span>' : ""}${st}</div>`
            )
            .join("")}
        </div>
      </div>
      <div class="side-states">
        ${sideStates.map((st) => `<div class="state-pill sp-${st}">${st}</div>`).join("")}
      </div>
      <div class="s5-verdict">Somba never assumes success or failure. <b>It confirms.</b> Then it heals the subscription backward.</div>
    </div>`);

  /* ---- S6 ledger ---- */
  const s6 = el(`
    <div class="scene th-black s6" id="sc-ledger">
      <p class="kicker s6-kicker">05 <span class="dot">/</span> WHY IT&rsquo;S TECHNICALLY STRONG</p>
      <h2 class="s6-head display">Zero double charges,<br/>by design.</h2>
      <div class="ncards">
        <div class="ncard">
          <div class="nc-num">01</div>
          <div class="nc-t">Ledger before Nomba</div>
          <div class="nc-d">Intent is written to the ledger before any call goes out. A crash mid-charge loses nothing.</div>
          <div class="nc-ic">${icon.book("#ffc907")}</div>
        </div>
        <div class="ncard">
          <div class="nc-num">02</div>
          <div class="nc-t">Verify pass, every 5 min</div>
          <div class="nc-d">Anything stuck in an uncertain state gets resolved automatically. No human in the loop.</div>
          <div class="nc-ic">${icon.radar("#ffc907")}</div>
        </div>
        <div class="ncard">
          <div class="nc-num">03</div>
          <div class="nc-t">Idempotency key, always</div>
          <div class="nc-d">Every charge attempt carries one &mdash; a retried request can never charge twice.</div>
          <div class="nc-ic">${icon.key("#ffc907")}</div>
        </div>
      </div>
      <img class="s6-shield a-tile" src="./assets/shield.png" alt=""/>
      <div class="statband">
        <div class="stat"><div class="sv c-999">0%</div><div class="sl">API uptime target</div></div>
        <div class="stat"><div class="sv">&lt;60s</div><div class="sl">p95 billing cycle</div></div>
        <div class="stat"><div class="sv c-10k">0/min</div><div class="sl">charge attempts at spike</div></div>
        <div class="stat"><div class="sv">3 layers</div><div class="sl">double-charge protection</div></div>
      </div>
    </div>`);

  /* ---- S7 competition ---- */
  const rows = [
    ["Reason-aware recovery, not blind retry", [1, 0, 0, 0]],
    ["Card-first with transfer fallback", [1, 0, 0, 1]],
    ["Correctness ledger &mdash; source of truth", [1, 0, 0, 0]],
    ["Built for how Nigerians pay", [1, 1, 0, 1]],
  ];
  const s7 = el(`
    <div class="scene th-yellow s7" id="sc-versus">
      <p class="kicker">06 <span class="dot">/</span> COMPETITION</p>
      <h2 class="s7-head" style="margin-top:26px">The only recovery engine built for how Nigerians <span style="box-shadow:inset 0 -0.26em 0 #0a0a0a; color:inherit">actually pay</span>.</h2>
      <table class="cmp">
        <thead>
          <tr>
            <th></th>
            <th class="col-somba">SOMBA</th>
            <th><span class="logo-cell">${psMark(26)} <span class="wordmark" style="color:#09a5db">Paystack</span> <span class="wordmark wm-flw">Flutterwave</span></span></th>
            <th><span class="logo-cell"><span class="wordmark wm-stripe">stripe</span></span></th>
            <th><span class="logo-cell"><span class="wordmark wm-remita">remita</span></span></th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (r, ri) => `
            <tr class="cmp-row r-${ri}">
              <td>${r[0]}</td>
              ${r[1]
                .map(
                  (v, ci) => `
                <td class="${ci === 0 ? "col-somba" : ""}">
                  <span class="cmp-cell cc-${ri}-${ci}">${v ? '<span class="cmp-check">&#10003;</span>' : '<span class="cmp-x">&times;</span>'}</span>
                </td>`
                )
                .join("")}
            </tr>`
            )
            .join("")}
        </tbody>
      </table>
      <div class="s7-crown mono">$ somba &mdash; the only yes in every row_</div>
    </div>`);

  /* ---- S8 model ---- */
  const s8 = el(`
    <div class="scene th-white s8" id="sc-model">
      <p class="kicker s8-kicker">07 <span class="dot">/</span> BUSINESS MODEL</p>
      <h2 class="s8-head">We only get paid when we <span class="hl">save you money</span>.</h2>
      <img class="s8-bag" src="./assets/moneybag.png" alt=""/>
      ${[0, 1, 2].map((i) => `<img class="s8-coin sc-${i}" src="./assets/coin.png" alt=""/>`).join("")}
      <div class="model-pills">
        <div class="mpill"><div class="mp-n">01</div><div><div class="mp-t">Recovery success fee</div><div class="mp-d">charged only on revenue Somba actually rescues from involuntary churn</div></div></div>
        <div class="mpill"><div class="mp-n">02</div><div><div class="mp-t">Platform fee</div><div class="mp-d">tiered monthly, by active subscriber count &mdash; plans, portal, dashboards</div></div></div>
        <div class="mpill"><div class="mp-n">03</div><div><div class="mp-t">Revenue share with Nomba</div><div class="mp-d">a value-added billing layer on Nomba&rsquo;s rails &mdash; not a competing product</div></div></div>
      </div>
    </div>`);

  /* ---- S9 gymflow ---- */
  const screens = [
    ["CHOOSE PLAN", "yel", "&#8358;", "Monthly &mdash; NGN 15,000", "basic &middot; standard &middot; premium<br/>7-day free trial", "Continue"],
    ["PAYMENT", "ok", "&#10003;", "Payment successful<br/>NGN 15,000", "charged via card<br/>next billing in 30 days", "Done"],
    ["PAYMENT", "bad", "&times;", "Payment failed<br/>NGN 15,000", "card declined<br/>membership at risk", "See options"],
    ["COMPLETE PAYMENT", "due", "&#8644;", "Pay by transfer", "Somba Collections<br/>0123456789 &middot; NGN 15,000", "I&rsquo;ve sent it"],
    ["MEMBERSHIP", "ok", "&#10003;", "Membership active", "restored automatically<br/>no re-subscribe needed", "Back to gym"],
  ];
  const captions = [
    ["01", "Signs up,<br/>picks a plan"],
    ["02", "Gets charged"],
    ["03", "Payment fails"],
    ["04", "Transfer<br/>fallback"],
    ["05", "Membership<br/>restores"],
  ];
  const events9 = [
    ["subscription.created", ""],
    ["invoice.paid", "ok"],
    ["charge.failed", "bad"],
    ["recovery.scheduled", ""],
    ["virtual_account.assigned", ""],
    ["transfer.received", "ok"],
    ["subscription.healed", "ok"],
  ];
  const s9 = el(`
    <div class="scene th-black s9" id="sc-gymflow">
      <p class="kicker s9-kicker">08 <span class="dot">/</span> SOMBA IN A REAL BUSINESS</p>
      <h2 class="s9-head display"><span class="gf">GYMFLOW</span> <span style="font-family:'Space Grotesk';font-weight:700">&mdash; live on the Somba API.</span></h2>
      <div class="phone">
        <div class="notch"></div>
        ${screens
          .map(
            (sc, i) => `
          <div class="pscreen psc-${i}">
            <div class="ps-k">${sc[0]}</div>
            <div class="ps-orb ${sc[1]}">${sc[2]}</div>
            <div class="ps-t">${sc[3]}</div>
            <div class="ps-d">${sc[4]}</div>
            <div class="ps-btn">${sc[5]}</div>
          </div>`
          )
          .join("")}
      </div>
      <div class="step-caption">
        <div class="sc-n display">01</div>
        <div class="sc-t">Signs up,<br/>picks a plan</div>
      </div>
      <div class="evfeed">
        <div class="ev-h">WEBHOOKS &mdash; LIVE FROM SOMBA</div>
        ${events9
          .map(
            (e) => `
          <div class="ev ${e[1]}"><span class="ev-dot">&#9679;</span><span class="ev-name">${e[0]}</span></div>`
          )
          .join("")}
      </div>
      <div class="s9-close">No admin console. No manual reconciliation. <b>Every step inside GymFlow&rsquo;s own screens.</b></div>
    </div>`);

  /* ---- S10 finale (team → ask → close) ---- */
  const team = [
    ["SS", "Sanni Shazily", "Frontend Developer"],
    ["AL", "Adam Lawal", "Data Science &amp; AI"],
    ["LQ", "Lasisi Quadri", "Software Engineer"],
    ["RA", "Raufu Abdurrahman", "Backend Engineer"],
  ];
  const asks = [
    ["01", "Production API access + 3&ndash;5 pilot merchants", "from Nomba&rsquo;s network &mdash; run Somba live for 30 days"],
    ["02", "Placement in Nomba&rsquo;s developer ecosystem", "as a recommended billing layer"],
    ["03", "Continued build support", "prize funding or a sponsored sprint &mdash; production grade in 60 days"],
  ];
  const s10 = el(`
    <div class="scene th-black s10" id="sc-finale">
      <div class="s10-team">
        <p class="kicker s10-tk">09 <span class="dot">/</span> THE TEAM</p>
        <h2 class="s10-th display">4 BUILDERS. <span class="it">Team SetId.</span></h2>
        <div class="tcards">
          ${team
            .map(
              (t) => `
            <div class="tcard">
              <div class="tc-face"><div class="tc-init">${t[0]}</div></div>
              <div class="tc-bar"><div class="tc-name">${t[1]}</div><div class="tc-role">${t[2]}</div></div>
            </div>`
            )
            .join("")}
        </div>
      </div>
      <div class="s10-ask">
        <p class="kicker ask-k">10 <span class="dot">/</span> THE ASK</p>
        <h2 class="ask-h display">ONE QUERY ANSWERS <span class="hl">EVERY NAIRA</span>.</h2>
        <div class="asks">
          ${asks
            .map(
              (a) => `
            <div class="ask">
              <div class="a-n">${a[0]}</div>
              <div><div class="a-t">${a[1]}</div><div class="a-d">${a[2]}</div></div>
            </div>`
            )
            .join("")}
        </div>
      </div>
      <div class="s10-close">
        <div class="close-core">
          <div class="close-logo display">S<span class="o">O</span>MBA</div>
          <svg class="close-squig squig" viewBox="0 0 420 60"><path class="cs-path" d="M8 40 C 70 10, 120 55, 180 30 C 240 8, 290 52, 350 28 C 380 17, 400 22, 412 30"/></svg>
          <div class="close-line mono">Stripe Billing for Nomba &mdash; with a recovery engine <b>no global processor has</b>.</div>
          <div class="close-sub">BUILT ON NOMBA RAILS &middot; NOMBA &times; DEVCAREER 2026 &middot; TEAM SETLD</div>
        </div>
      </div>
    </div>`);

  [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10].forEach((s) => scenesRoot.appendChild(s));

  /* ---------------- fx elements ---------------- */
  const iris = el(`<div class="fx-iris"></div>`);
  fx.appendChild(iris);
  const strips = Array.from({ length: 8 }, (_, i) => {
    const st = el(`<div class="fx-strip ${i % 2 ? "yel" : ""}" style="left:${i * 12.5}%;width:12.6%"></div>`);
    fx.appendChild(st);
    return st;
  });
  const slats = Array.from({ length: 6 }, (_, i) => {
    const sl = el(`<div class="fx-slat" style="top:${(i * 100) / 6}%;height:${100 / 6 + 0.2}%"></div>`);
    fx.appendChild(sl);
    return sl;
  });
  const stamp = el(`<div class="fx-stamp"></div>`);
  const ring = el(`<div class="fx-ring" style="width:300px;height:300px;left:810px;top:390px"></div>`);
  const fxCoin = el(`<img class="fx-coin" src="./assets/coin.png" alt=""/>`);
  const doorL = el(`<div class="fx-door" style="left:-0.5%"><div class="hz" style="margin-left:auto"></div></div>`);
  const doorR = el(`<div class="fx-door" style="right:-0.5%"><div class="hz" style="margin-right:auto"></div></div>`);
  const diag = el(`<div class="fx-diag"></div>`);
  const fxPhone = el(`<div class="fx-phone"></div>`);
  const flash = el(`<div class="fx-flash"></div>`);
  [stamp, ring, fxCoin, doorL, doorR, diag, fxPhone, flash].forEach((e) => fx.appendChild(e));
  // parked offscreen state
  doorL.style.transform = "translateX(-101%)";
  doorR.style.transform = "translateX(101%)";

  /* ============================================================
     master timeline
     ============================================================ */
  const tl = anime.timeline({ autoplay: false, easing: "easeOutCubic", duration: 800 });
  const q = (sel) => {
    const n = document.querySelector(sel);
    if (!n) console.warn("missing", sel);
    return n;
  };
  const qa = (sel) => Array.from(document.querySelectorAll(sel));

  /* seek-safe text dynamics, driven every frame from tick() —
     anime child update callbacks don't fire reliably for finished
     children on seek, so counters/typewriters live outside the timeline */
  const outExpo = (p) => (p >= 1 ? 1 : 1 - Math.pow(2, -10 * p));
  const clamp01 = (v) => Math.min(1, Math.max(0, v));
  const COUNTERS = []; // {sel, from, to, fmt, at, dur}
  const TYPES = [];    // {sel, text, at, dur}
  function addType(sel, text, at, dur) { TYPES.push({ sel, text, at, dur }); }
  function addCount(sel, from, to, fmt, at, dur) { COUNTERS.push({ sel, from, to, fmt, at, dur }); }
  function runDynamics(t) {
    for (const c of COUNTERS) {
      const v = c.from + (c.to - c.from) * outExpo(clamp01((t - c.at) / c.dur));
      const n = q(c.sel);
      if (n) n.innerHTML = c.fmt(v);
    }
    for (const ty of TYPES) {
      const i = Math.round(ty.text.length * clamp01((t - ty.at) / ty.dur));
      const n = q(ty.sel);
      if (n) {
        const cut = ty.text.slice(0, i);
        if (n.__last !== cut) { n.innerHTML = cut; n.__last = cut; }
      }
    }
  }
  function shake(at, power = 14, dur = 420) {
    tl.add(
      {
        targets: "#scenes",
        translateX: [
          { value: -power, duration: 50 }, { value: power * 0.8, duration: 50 },
          { value: -power * 0.5, duration: 60 }, { value: power * 0.3, duration: 60 },
          { value: 0, duration: dur - 220 },
        ],
        translateY: [
          { value: power * 0.6, duration: 55 }, { value: -power * 0.5, duration: 55 },
          { value: 0, duration: dur - 110 },
        ],
        easing: "easeOutQuad",
      },
      at
    );
  }

  /* ================= S1 — COLD OPEN (0–14s) ================= */
  // park fx that would otherwise leak their from-state at seek(0)
  tl.add({ targets: ring, opacity: [0, 0], duration: 1, easing: "linear" }, 0);
  tl.add({ targets: ".ecg-path", strokeDashoffset: [anime.setDashoffset, 0], duration: 2800, easing: "easeInOutSine" }, 100);
  tl.add({ targets: ".s1-ecg", opacity: [1, 0], scale: [1, 1.06], duration: 700 }, 2900);
  tl.add({ targets: ".s1-badge", opacity: [0, 1], translateY: [-24, 0], duration: 700 }, 3000);
  tl.add({
    targets: ".s1-letter",
    translateY: ["120%", "0%"],
    duration: 1000,
    delay: anime.stagger(110),
    easing: "easeOutExpo",
  }, 3200);
  tl.add({ targets: ".s1-kicker", opacity: [0, 1], letterSpacing: ["0.6em", "0.32em"], duration: 900 }, 4200);
  addType(".s1-tag", "Stripe Billing for Nomba &mdash; with a recovery engine no global processor has.", 5000, 2600);
  tl.add({ targets: ".sq-path", strokeDashoffset: [anime.setDashoffset, 0], duration: 2200, easing: "easeInOutQuad" }, 5400);
  // breathe on the wordmark
  tl.add({ targets: ".s1-title", scale: [1, 1.03], duration: 4000, easing: "easeInOutSine" }, 8600);
  // T1: iris flood from the O
  tl.add({ targets: iris, left: "710px", top: "420px", duration: 1, easing: "linear" }, 12700);
  tl.add({ targets: iris, scale: [0, 34], duration: 1050, easing: "easeInExpo" }, 12800);
  tl.add({ targets: iris, scale: 0, duration: 900, easing: "easeOutExpo" }, 14150);

  /* ================= S2 — PROBLEM (14–36s) ================= */
  tl.add({ targets: ".s2-kicker", opacity: [0, 1], translateX: [-30, 0], duration: 600 }, 14300);
  tl.add({ targets: ".s2-head", opacity: [0, 1], translateY: [50, 0], duration: 900, easing: "easeOutExpo" }, 14500);
  tl.add({
    targets: ".merchant",
    opacity: [0, 1],
    translateY: [70, 0],
    rotate: () => anime.random(-3, 3),
    duration: 700,
    delay: anime.stagger(160),
    easing: "easeOutBack",
  }, 16200);
  // "same engine" pulse — all cards throb in unison
  tl.add({ targets: ".merchant", scale: [1, 1.045, 1], duration: 700, delay: anime.stagger(0), easing: "easeInOutQuad" }, 20200);
  tl.add({ targets: ".merchant .m-tag", backgroundColor: ["#0a0a0a", "#e05252", "#0a0a0a"], duration: 900 }, 20200);
  // panel takes focus: merchants recede
  tl.add({ targets: ".merchant", opacity: 0.35, scale: 0.96, duration: 700, delay: anime.stagger(60) }, 22200);
  tl.add({ targets: ".s2-fall", opacity: [0, 1], translateY: [40, 0], duration: 800 }, 22200);
  // avatar #2 dies
  tl.add({ targets: ".av-2", backgroundColor: "#e6e4dc", duration: 500 }, 24400);
  tl.add({
    targets: ".av-2",
    opacity: [1, 0],
    translateY: [0, -90],
    filter: ["blur(0px)", "blur(10px)"],
    duration: 1400,
    easing: "easeInQuad",
  }, 25000);
  tl.add({ targets: ".s2-stamp", opacity: [0, 1], scale: [3, 1], rotate: ["-7deg", "-7deg"], duration: 420, easing: "easeInExpo" }, 29600);
  shake(30020, 16);
  // T2: hazard strips sweep
  tl.add({
    targets: strips,
    translateY: ["-101%", "0%"],
    duration: 620,
    delay: anime.stagger(55),
    easing: "easeInQuart",
  }, 34900);
  tl.add({
    targets: strips,
    translateY: ["0%", "101%"],
    duration: 620,
    delay: anime.stagger(55, { direction: "reverse" }),
    easing: "easeOutQuart",
  }, 36050);

  /* ================= S3 — MARKET (36–54s) ================= */
  tl.add({ targets: ".s3 .kicker", opacity: [0, 1], translateX: [-30, 0], duration: 600 }, 36300);
  tl.add({ targets: ".s3-big", opacity: [0, 1], translateY: [60, 0], duration: 900, easing: "easeOutExpo" }, 36400);
  addCount(".c-700", 0, 700, (v) => `$${Math.round(v)}B+`, 36600, 2000);
  tl.add({ targets: ".s3-sub", opacity: [0, 1], duration: 700 }, 38800);
  tl.add({ targets: ".fun-band.f1", opacity: [0, 1], translateY: [-60, 0], duration: 700, easing: "easeOutBounce" }, 40200);
  tl.add({ targets: ".fun-band.f2", opacity: [0, 1], translateY: [-60, 0], duration: 700, easing: "easeOutBounce" }, 41400);
  tl.add({ targets: ".fun-band.f3", opacity: [0, 1], translateY: [-60, 0], scale: [1, 1.04, 1], duration: 800, easing: "easeOutBounce" }, 42600);
  tl.add({ targets: ".s3-tick", opacity: [0, 1], translateY: [40, 0], delay: anime.stagger(220), duration: 700 }, 45200);
  addCount(".c-11b", 0, 11, (v) => `${v.toFixed(1)}B`, 45400, 1800);
  addCount(".c-60k", 0, 60, (v) => `${Math.round(v)}k+`, 45800, 1800);
  tl.add({ targets: ".pay-pill", opacity: [0, 1], scale: [0.8, 1], duration: 700, easing: "easeOutBack" }, 47800);
  // T3: 3D flip of the whole stage
  tl.add({ targets: "#scenes", rotateY: [0, -92], duration: 900, easing: "easeInCubic" }, 52900);
  tl.add({ targets: "#scenes", rotateY: [92, 0], duration: 950, easing: "easeOutCubic" }, 53810);

  /* ================= S4 — INSIGHT (54–78s) ================= */
  tl.add({ targets: ".s4 .kicker", opacity: [0, 1], translateX: [-30, 0], duration: 600 }, 54400);
  tl.add({ targets: ".t-timing", opacity: [0, 1], translateY: [80, 0], duration: 800, easing: "easeOutExpo" }, 54600);
  tl.add({ targets: ".t-retry", opacity: [0, 1], translateY: [80, 0], duration: 800, easing: "easeOutExpo" }, 55000);
  tl.add({ targets: ".t-retry .slash", scaleX: [0, 1], duration: 380, easing: "easeInExpo" }, 56100);
  shake(56480, 10, 300);
  tl.add({ targets: ".wallet-box", opacity: [0, 1], translateY: [40, 0], duration: 700 }, 56900);
  [0, 1, 2].forEach((i) => {
    tl.add({ targets: `.rx-${i}`, opacity: [0, 1], scale: [2.2, 1], duration: 260, easing: "easeInExpo" }, 57400 + i * 620);
    tl.add({ targets: `.rx-${i}`, opacity: 0, duration: 400 }, 59800);
  });
  tl.add({
    targets: ".cal-day",
    opacity: [0, 1],
    scale: [0.6, 1],
    delay: anime.stagger(70, { grid: [7, 2], from: "first" }),
    duration: 500,
    easing: "easeOutBack",
  }, 59400);
  // time passes: days dim in order
  tl.add({
    targets: ".cal-day:not(.payday)",
    opacity: [1, 0.28],
    delay: anime.stagger(90),
    duration: 300,
    easing: "linear",
  }, 61800);
  tl.add({ targets: ".cal-day.payday .pd-tag", opacity: [0, 1], translateY: [-8, 0], duration: 500 }, 62400);
  tl.add({
    targets: ".cal-day.payday",
    backgroundColor: "#ffc907",
    color: "#0a0a0a",
    borderColor: "#ffc907",
    scale: [1, 1.22, 1.08],
    duration: 700,
    easing: "easeOutBack",
  }, 62900);
  // wallet fills
  tl.add({ targets: ".w-fill", scaleY: [0, 1], duration: 900, easing: "easeOutQuart" }, 63700);
  // charge dart: payday → wallet
  tl.add({ targets: ".charge-dart", opacity: [0, 1], left: ["1000px", "240px"], top: ["150px", "150px"], duration: 620, easing: "easeInQuad" }, 65000);
  tl.add({ targets: ".charge-dart", opacity: 0, duration: 200 }, 65640);
  tl.add({ targets: ".wallet-svg", scale: [1, 1.12, 1], duration: 500, easing: "easeOutBack" }, 65650);
  // wallet label is time-driven in tick(): ₦0 → counts to ₦68,500 → charge.succeeded ✓
  tl.add({ targets: ".s4-clock", opacity: [0, 1], translateY: [80, 0], rotate: ["8deg", "-4deg"], duration: 900, easing: "easeOutBack" }, 66700);
  tl.add({
    targets: ".pair",
    opacity: [0, 1],
    translateY: [60, 0],
    delay: anime.stagger(300),
    duration: 650,
    easing: "easeOutExpo",
  }, 68200);
  // T4: coin rolls across, scenes shove left
  tl.add({ targets: fxCoin, opacity: { value: [0, 1], duration: 120 }, translateX: [-500, 2420], translateY: [660, 660], rotate: [0, 900], duration: 1750, easing: "easeInOutQuad" }, 76500);
  tl.add({ targets: fxCoin, opacity: 0, duration: 120 }, 78230);
  tl.add({ targets: s4, translateX: [0, -640], duration: 1400, easing: "easeInOutQuad" }, 76650);
  tl.add({ targets: s5, translateX: [640, 0], duration: 1400, easing: "easeInOutQuad" }, 76750);

  /* ================= S5 — LIFECYCLE (78–100s) ================= */
  tl.add({ targets: ".s5-kicker", opacity: [0, 1], translateX: [-30, 0], duration: 600 }, 78500);
  tl.add({ targets: ".s5-head", opacity: [0, 1], translateY: [60, 0], duration: 900, easing: "easeOutExpo" }, 78700);
  tl.add({ targets: ".rail-line", opacity: [0, 1], duration: 600 }, 80000);
  tl.add({
    targets: ".rail .state-pill",
    opacity: [0, 1],
    translateY: [40, 0],
    delay: anime.stagger(180),
    duration: 600,
    easing: "easeOutBack",
  }, 80200);
  tl.add({
    targets: ".side-states .state-pill",
    opacity: [0, 0.55],
    translateY: [40, 0],
    delay: anime.stagger(150),
    duration: 600,
  }, 81600);
  tl.add({ targets: ".orb", opacity: [0, 1], duration: 300 }, 83000);
  // orb walks the rail; pills light up as it arrives (color tweens = seek-safe)
  tl.add({ targets: ".sp-trialing", backgroundColor: "#232323", color: "#ffffff", borderColor: "#4a4a44", duration: 400 }, 83000);
  tl.add({ targets: ".orb", left: ["60px", "560px"], duration: 1200, easing: "easeInOutQuad" }, 83400);
  tl.add({ targets: ".sp-active", backgroundColor: "#12341f", color: "#45c06f", borderColor: "#45c06f", duration: 400 }, 84500);
  tl.add({ targets: ".sp-past_due", backgroundColor: "#33270b", color: "#d99a1b", borderColor: "#d99a1b", duration: 400 }, 87300);
  tl.add({ targets: ".sp-payment_uncertain", backgroundColor: "#361313", color: "#e05252", borderColor: "#e05252", duration: 400 }, 89500);
  // heal backward: uncertain dims out, active re-lights hard
  tl.add({ targets: ".sp-payment_uncertain", backgroundColor: "#141414", color: "#7c7c75", borderColor: "#232323", duration: 600 }, 94200);
  tl.add({ targets: ".sp-active", backgroundColor: "#16482a", color: "#5fe08c", borderColor: "#5fe08c", duration: 500 }, 95200);
  tl.add({ targets: ".rl-fill", width: ["0%", "36%"], duration: 1200, easing: "easeInOutQuad" }, 83400);
  tl.add({ targets: ".sp-active", scale: [1, 1.12, 1], duration: 500 }, 84500);
  tl.add({ targets: ".orb", left: ["560px", "1010px"], duration: 1200, easing: "easeInOutQuad" }, 86200);
  tl.add({ targets: ".rl-fill", width: ["36%", "63%"], duration: 1200, easing: "easeInOutQuad" }, 86200);
  tl.add({ targets: ".sp-past_due", scale: [1, 1.12, 1], duration: 500 }, 87300);
  shake(87350, 8, 260);
  tl.add({ targets: ".orb", left: ["1010px", "1500px"], duration: 1200, easing: "easeInOutQuad" }, 88400);
  tl.add({ targets: ".rl-fill", width: ["63%", "92%"], duration: 1200, easing: "easeInOutQuad" }, 88400);
  tl.add({ targets: ".sp-payment_uncertain", scale: [1, 1.14, 1], duration: 550 }, 89500);
  tl.add({ targets: ".sp-payment_uncertain .sp-tag", opacity: [0, 1], translateX: ["-50%", "-50%"], translateY: [-10, 0], duration: 600 }, 90100);
  tl.add({ targets: ".s5-verdict", opacity: [0, 1], translateY: [30, 0], duration: 800 }, 91300);
  // heal backward: orb returns to active
  tl.add({ targets: ".orb", left: ["1500px", "560px"], duration: 1500, easing: "easeInOutQuart" }, 93600);
  tl.add({ targets: ".rl-fill", width: ["92%", "36%"], duration: 1500, easing: "easeInOutQuart" }, 93600);
  tl.add({ targets: ".sp-active", scale: [1, 1.18, 1], duration: 650, easing: "easeOutBack" }, 95200);
  tl.add({ targets: ".orb", opacity: 0, duration: 400 }, 96600);
  // T5: slats
  tl.add({ targets: slats, scaleY: [0, 1], delay: anime.stagger(70), duration: 480, easing: "easeInQuart" }, 98900);
  tl.add({ targets: slats, scaleY: [1, 0], delay: anime.stagger(70, { direction: "reverse" }), duration: 480, easing: "easeOutQuart" }, 100050);

  /* ================= S6 — LEDGER (100–122s) ================= */
  tl.add({ targets: ".s6-kicker", opacity: [0, 1], translateX: [-30, 0], duration: 600 }, 100500);
  tl.add({ targets: ".s6-head", opacity: [0, 1], translateY: [60, 0], duration: 900, easing: "easeOutExpo" }, 100700);
  tl.add({
    targets: ".ncard",
    opacity: [0, 1],
    translateY: [90, 0],
    rotateX: [24, 0],
    delay: anime.stagger(260),
    duration: 800,
    easing: "easeOutExpo",
  }, 102600);
  tl.add({ targets: ".s6-shield", opacity: [0, 1], translateY: [-60, 0], rotate: ["6deg", "-3deg"], duration: 900, easing: "easeOutBack" }, 106200);
  // radar arm sweeps forever-ish
  tl.add({ targets: ".rd-arm", rotate: [0, 1080], duration: 12000, easing: "linear", transformOrigin: ["6px 20px 0", "6px 20px 0"] }, 104000);
  tl.add({ targets: ".stat", opacity: [0, 1], translateY: [30, 0], delay: anime.stagger(200), duration: 650 }, 110300);
  addCount(".c-999", 0, 99.9, (v) => `${v.toFixed(1)}%`, 110400, 1600);
  addCount(".c-10k", 0, 10000, (v) => `${Math.round(v).toLocaleString()}/min`, 110800, 1800);
  // T6: stamp slam
  tl.add({ targets: stamp, opacity: [0, 1], scale: [1.7, 1], duration: 360, easing: "easeInExpo" }, 120900);
  tl.add({ targets: ring, opacity: [0.9, 0], scale: [0.4, 4], duration: 900, easing: "easeOutExpo" }, 121260);
  shake(121270, 18);
  tl.add({ targets: stamp, opacity: 0, duration: 500 }, 122200);

  /* ================= S7 — COMPETITION (122–142s) ================= */
  tl.add({ targets: ".s7 .kicker", opacity: [0, 1], translateX: [-30, 0], duration: 600 }, 122300);
  tl.add({ targets: ".s7-head", opacity: [0, 1], translateY: [50, 0], duration: 900, easing: "easeOutExpo" }, 122400);
  tl.add({ targets: ".cmp thead th", opacity: [0, 1], translateY: [-20, 0], delay: anime.stagger(110), duration: 500 }, 124300);
  rows.forEach((r, ri) => {
    const rowAt = 125300 + ri * 1900;
    tl.add({ targets: `.cmp-row.r-${ri} td:first-child`, opacity: [0, 1], translateX: [-30, 0], duration: 500 }, rowAt);
    // somba check first, slams
    tl.add({ targets: `.cc-${ri}-0`, opacity: [0, 1], scale: [2.4, 1], duration: 330, easing: "easeInExpo" }, rowAt + 350);
    // others pop after
    [1, 2, 3].forEach((ci) => {
      tl.add({ targets: `.cc-${ri}-${ci}`, opacity: [0, 1], scale: [0, 1], duration: 380, easing: "easeOutBack" }, rowAt + 700 + ci * 160);
    });
  });
  tl.add({ targets: ".s7-crown", opacity: [0, 1], duration: 300 }, 134100);
  addType(".s7-crown", "$ somba &mdash; the only yes in every row_", 134200, 1400);
  // T7: diagonal squeegee
  tl.add({ targets: diag, translateX: ["-130%", "0%"], rotate: [-10, -10], duration: 700, easing: "easeInQuart" }, 140700);
  tl.add({ targets: diag, translateX: ["0%", "130%"], rotate: [-10, -10], duration: 700, easing: "easeOutQuart" }, 141900);

  /* ================= S8 — MODEL (142–158s) ================= */
  tl.add({ targets: ".s8-kicker", opacity: [0, 1], translateX: [-30, 0], duration: 600 }, 142400);
  tl.add({ targets: ".s8-head", opacity: [0, 1], translateY: [50, 0], duration: 900, easing: "easeOutExpo" }, 142600);
  tl.add({ targets: ".s8-bag", opacity: [0, 1], translateY: [-700, 0], duration: 750, easing: "easeInQuad" }, 144500);
  tl.add({ targets: ".s8-bag", scaleY: [0.82, 1], scaleX: [1.14, 1], duration: 550, easing: "easeOutElastic(1, .5)" }, 145260);
  shake(145270, 12, 300);
  // coins arc into the bag
  [0, 1, 2].forEach((i) => {
    tl.add({
      targets: `.sc-${i}`,
      opacity: { value: [0, 1], duration: 150 },
      left: [`${240 + i * 140}px`, "1560px"],
      top: ["940px", "420px"],
      scale: [1, 0.4],
      rotate: [0, 540],
      duration: 950,
      easing: "easeInBack",
    }, 145900 + i * 260);
    tl.add({ targets: `.sc-${i}`, opacity: 0, duration: 120 }, 146830 + i * 260);
  });
  tl.add({ targets: ".s8-bag", scale: [1, 1.05, 1], duration: 400 }, 147000);
  tl.add({
    targets: ".mpill",
    opacity: [0, 1],
    translateX: [-80, 0],
    delay: anime.stagger(340),
    duration: 700,
    easing: "easeOutExpo",
  }, 147600);
  // T8: flash + phone zoom
  tl.add({ targets: flash, opacity: [0, 0.9], duration: 300, easing: "easeInQuad" }, 156800);
  tl.add({ targets: flash, opacity: 0, duration: 600 }, 157150);
  tl.add({ targets: fxPhone, opacity: [0, 1], scale: [9, 1], duration: 1100, easing: "easeOutExpo" }, 157100);
  tl.add({ targets: fxPhone, opacity: 0, duration: 350 }, 158900);

  /* ================= S9 — GYMFLOW (158–180s) ================= */
  tl.add({ targets: ".s9-kicker", opacity: [0, 1], translateX: [-30, 0], duration: 600 }, 158400);
  tl.add({ targets: ".s9-head", opacity: [0, 1], translateY: [40, 0], duration: 800, easing: "easeOutExpo" }, 158500);
  tl.add({ targets: ".step-caption", opacity: [0, 1], translateX: [-40, 0], duration: 600 }, 159600);
  tl.add({ targets: ".evfeed .ev-h", opacity: [0, 1], duration: 600 }, 159600);
  const stepAt = [159800, 163000, 166200, 169400, 172600];
  screens.forEach((_, i) => {
    tl.add({ targets: `.psc-${i}`, opacity: [0, 1], translateX: ["100%", "0%"], duration: 620, easing: "easeOutExpo" }, stepAt[i]);
    if (i > 0) tl.add({ targets: `.psc-${i - 1}`, translateX: ["0%", "-38%"], opacity: [1, 0], duration: 620, easing: "easeInQuad" }, stepAt[i]);
    // caption dip (content swap is time-driven in tick, seek-safe)
    if (i > 0) {
      tl.add({ targets: ".step-caption", opacity: [1, 0], translateY: [0, -14], duration: 240, easing: "easeInQuad" }, stepAt[i] - 60);
      tl.add({ targets: ".step-caption", opacity: [0, 1], translateY: [14, 0], duration: 320, easing: "easeOutQuad" }, stepAt[i] + 220);
    }
  });
  // fail moment shake
  shake(166500, 12, 320);
  // webhook feed
  const evAt = [160400, 163600, 166800, 167900, 170000, 171400, 173300];
  qa(".ev").forEach((_, i) => {
    tl.add({ targets: `.ev:nth-of-type(${i + 2})`, opacity: [0, 1], translateX: [40, 0], duration: 480, easing: "easeOutQuad" }, evAt[i] || 174000);
  });
  tl.add({ targets: ".s9-close", opacity: [0, 1], translateY: [24, 0], duration: 700 }, 175600);
  // T9: hazard doors close
  tl.add({ targets: doorL, translateX: ["-101%", "0%"], duration: 650, easing: "easeInQuart" }, 178900);
  tl.add({ targets: doorR, translateX: ["101%", "0%"], duration: 650, easing: "easeInQuart" }, 178900);
  tl.add({ targets: doorL, translateX: ["0%", "-101%"], duration: 750, easing: "easeOutQuart" }, 180400);
  tl.add({ targets: doorR, translateX: ["0%", "101%"], duration: 750, easing: "easeOutQuart" }, 180400);

  /* ================= S10 — TEAM / ASK / CLOSE (180–206.5s) ================= */
  tl.add({ targets: ".s10-tk", opacity: [0, 1], translateX: [-30, 0], duration: 600 }, 180700);
  tl.add({ targets: ".s10-th", opacity: [0, 1], translateY: [50, 0], duration: 900, easing: "easeOutExpo" }, 180900);
  tl.add({
    targets: ".tcard",
    opacity: [0, 1],
    translateY: [90, 0],
    delay: anime.stagger(220),
    duration: 750,
    easing: "easeOutExpo",
  }, 182400);
  // ask overlay ("on" class is time-driven in tick, seek-safe)
  tl.add({ targets: ".s10-ask", opacity: [0, 1], duration: 700, easing: "easeInOutQuad" }, 188600);
  tl.add({ targets: ".ask-k", opacity: [0, 1], translateX: [-30, 0], duration: 600 }, 189200);
  tl.add({ targets: ".ask-h", opacity: [0, 1], translateY: [50, 0], duration: 900, easing: "easeOutExpo" }, 189400);
  tl.add({
    targets: ".ask",
    opacity: [0, 1],
    translateX: [-70, 0],
    delay: anime.stagger(600),
    duration: 700,
    easing: "easeOutExpo",
  }, 191000);
  // close overlay
  tl.add({ targets: ".s10-close", opacity: [0, 1], duration: 900, easing: "easeInOutQuad" }, 198600);
  tl.add({ targets: ".close-logo", opacity: [0, 1], scale: [1.4, 1], duration: 900, easing: "easeOutExpo" }, 199200);
  tl.add({ targets: ".cs-path", strokeDashoffset: [anime.setDashoffset, 0], duration: 1200, easing: "easeInOutQuad" }, 200200);
  tl.add({ targets: ".close-line", opacity: [0, 1], translateY: [16, 0], duration: 700 }, 201200);
  tl.add({ targets: ".close-sub", opacity: [0, 1], duration: 700 }, 202400);
  tl.add({ targets: ".close-logo .o", color: ["#ffc907", "#ffffff", "#ffc907"], duration: 1200 }, 203400);
  // final settle frame
  tl.add({ targets: ".close-core", scale: [1, 1.015], duration: 2000, easing: "easeInOutSine" }, 204400);

  /* ============================================================
     scene visibility + music intensity + cue firing
     ============================================================ */
  // [node, start, end, preRoll] — preRoll is how early a scene may become
  // visible. Later scenes paint above earlier ones, so each may only appear
  // once its transition has the screen covered.
  const sceneWindows = [
    [s1, ...S.open, 0],
    [s2, ...S.problem, 250],   // iris fully expanded at ~13850
    [s3, ...S.market, 100],    // strips covered at ~35900
    [s4, ...S.insight, 220],   // stage edge-on at ~53800
    [s5, ...S.states, 1300],   // slides in alongside the rolling coin
    [s6, ...S.ledger, 150],    // slats covered at ~99750
    [s7, ...S.versus, 550],    // stamp lands at ~121260
    [s8, ...S.model, 450],     // diagonal covered at ~141400
    [s9, ...S.gymflow, 850],   // flash peak at ~157150
    [s10, ...S.finale, 350],   // doors shut at ~179550
  ];
  const INTENSITY = [
    [S.open[0], 0], [S.problem[0], 1], [S.market[0], 2], [S.insight[0], 2],
    [S.states[0], 2], [S.ledger[0], 3], [S.versus[0], 3], [S.model[0], 2],
    [S.gymflow[0], 3], [S.finale[0], 4], [188600, 2], [198600, 0],
  ];
  // sound cues (fired only during natural playback)
  const CUES = [
    { t: 12650, fn: () => Music.riser(1.3) },
    { t: 13850, fn: () => Music.impact() },
    { t: 30020, fn: () => Music.impact() },
    { t: 34750, fn: () => Music.riser(1.2) },
    { t: 36100, fn: () => Music.impact() },
    { t: 42600, fn: () => Music.ding() },
    { t: 52750, fn: () => Music.riser(1.1) },
    { t: 54100, fn: () => Music.impact() },
    { t: 56480, fn: () => Music.impact() },
    { t: 62900, fn: () => Music.ding() },
    { t: 65650, fn: () => Music.ding() },
    { t: 76400, fn: () => Music.riser(1.6) },
    { t: 78100, fn: () => Music.impact() },
    { t: 84500, fn: () => Music.ding() },
    { t: 87350, fn: () => Music.impact() },
    { t: 95300, fn: () => Music.ding() },
    { t: 98750, fn: () => Music.riser(1.2) },
    { t: 100150, fn: () => Music.impact() },
    { t: 120750, fn: () => Music.riser(1.1) },
    { t: 121270, fn: () => Music.impact() },
    { t: 125650, fn: () => Music.ding() },
    { t: 127550, fn: () => Music.ding() },
    { t: 129450, fn: () => Music.ding() },
    { t: 131350, fn: () => Music.ding() },
    { t: 140550, fn: () => Music.riser(1.2) },
    { t: 142100, fn: () => Music.impact() },
    { t: 145270, fn: () => Music.impact() },
    { t: 146800, fn: () => Music.ding() },
    { t: 156700, fn: () => Music.riser(1.2) },
    { t: 158200, fn: () => Music.impact() },
    { t: 163100, fn: () => Music.ding() },
    { t: 166500, fn: () => Music.impact() },
    { t: 172700, fn: () => Music.ding() },
    { t: 178750, fn: () => Music.riser(1.2) },
    { t: 180500, fn: () => Music.impact() },
    { t: 198800, fn: () => Music.impact() },
    { t: 202500, fn: () => Music.fadeOut(3.5) },
  ];
  let lastT = 0;

  function tick() {
    const t = tl.currentTime;
    for (const [node, a, b, pre] of sceneWindows) {
      node.classList.toggle("on", t >= a - pre && t < b + 1600);
    }
    // seek-safe text + overlay dynamics
    runDynamics(t);
    const wlab = q(".wallet-label");
    if (wlab) {
      let txt;
      if (t >= 66000) txt = "charge.succeeded &#10003;";
      else if (t >= 63700) txt = `balance: &#8358;${Math.round(68500 * outExpo(clamp01((t - 63700) / 1000))).toLocaleString()}`;
      else txt = "balance: &#8358;0";
      if (wlab.__last !== txt) { wlab.innerHTML = txt; wlab.__last = txt; }
    }
    const cap = q(".step-caption");
    if (cap) {
      let idx = 0;
      for (let i = 0; i < stepAt.length; i++) if (t >= stepAt[i]) idx = i;
      if (cap.__idx !== idx) {
        cap.__idx = idx;
        cap.querySelector(".sc-n").innerHTML = captions[idx][0];
        cap.querySelector(".sc-t").innerHTML = captions[idx][1];
      }
    }
    q(".s10-ask").classList.toggle("on", t >= 188000);
    q(".s10-close").classList.toggle("on", t >= 198000);
    let lvl = 0;
    for (const [at, v] of INTENSITY) if (t >= at) lvl = v;
    Music.setIntensity(lvl);
    // fire cues during forward playback only
    if (!tl.paused && t > lastT && t - lastT < 700) {
      for (const c of CUES) if (c.t > lastT && c.t <= t) c.fn();
    }
    lastT = t;
    // controls
    scrubFill.style.width = `${(t / TOTAL) * 100}%`;
    timecode.textContent = fmt(t);
  }
  tl.update = tick; // anime v3 honors config.update; assign post-hoc too
  tl.config && (tl.config.update = tick);

  /* ============================================================
     controls / gate
     ============================================================ */
  const gate = document.getElementById("gate");
  const controls = document.getElementById("controls");
  const btnStart = document.getElementById("btn-start");
  const btnPlay = document.getElementById("btn-play");
  const btnMute = document.getElementById("btn-mute");
  const btnFull = document.getElementById("btn-full");
  const scrub = document.getElementById("scrub");
  const scrubFill = document.getElementById("scrub-fill");
  const markers = document.getElementById("scrub-markers");
  const timecode = document.getElementById("timecode");

  Object.values(S).forEach(([a]) => {
    if (a === 0) return;
    const m = document.createElement("div");
    m.className = "scrub-mark";
    m.style.left = `${(a / TOTAL) * 100}%`;
    markers.appendChild(m);
  });

  const fmt = (ms) => {
    const s = Math.floor(ms / 1000);
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  };

  let audioCtx = null;
  let raf = null;
  function frame() {
    tick();
    raf = requestAnimationFrame(frame);
  }

  function begin() {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      Music.start(audioCtx);
    }
    gate.classList.add("off");
    controls.classList.remove("hidden");
    document.fonts.ready.then(() => {
      tl.seek(0);
      lastT = 0;
      tl.play();
      Music.fadeIn();
      if (!raf) frame();
    });
  }
  btnStart.addEventListener("click", begin);

  function setPlayIcon(playing) {
    btnPlay.innerHTML = playing ? '<span class="ico-pause"></span>' : '<span class="ico-play"></span>';
  }
  function toggle() {
    if (tl.completed) { replay(); return; }
    if (tl.paused) {
      tl.play();
      Music.resume();
      if (audioCtx && audioCtx.state === "suspended") audioCtx.resume();
      setPlayIcon(true);
    } else {
      tl.pause();
      Music.pause();
      setPlayIcon(false);
    }
  }
  btnPlay.addEventListener("click", toggle);

  function replay() {
    tl.seek(0);
    lastT = 0;
    Music.fadeIn();
    tl.play();
    setPlayIcon(true);
  }

  tl.finished.then(() => {
    setPlayIcon(false);
    const inner = gate.querySelector(".gate-inner");
    inner.querySelector(".gate-sub").textContent = "THAT WAS SOMBA. EVERY NAIRA, ANSWERED.";
    btnStart.innerHTML = '<span class="tri"></span> REPLAY';
    btnStart.addEventListener("click", () => { gate.classList.add("off"); replay(); }, { once: true });
    gate.classList.remove("off");
  });

  scrub.addEventListener("click", (e) => {
    const r = scrub.getBoundingClientRect();
    const p = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
    tl.seek(p * TOTAL);
    lastT = p * TOTAL;
    tick();
  });

  btnMute.addEventListener("click", () => {
    Music.setMuted(!Music.muted);
    btnMute.classList.toggle("muted", Music.muted);
  });
  btnFull.addEventListener("click", () => {
    if (document.fullscreenElement) document.exitFullscreen();
    else document.documentElement.requestFullscreen();
  });
  addEventListener("keydown", (e) => {
    if (e.code === "Space") { e.preventDefault(); if (!gate.classList.contains("off")) begin(); else toggle(); }
    if (e.key === "m") btnMute.click();
    if (e.key === "f") btnFull.click();
    if (e.key === "ArrowRight") { tl.seek(Math.min(TOTAL, tl.currentTime + 5000)); lastT = tl.currentTime; }
    if (e.key === "ArrowLeft") { tl.seek(Math.max(0, tl.currentTime - 5000)); lastT = tl.currentTime; }
  });

  // idle-hide controls
  let hideTimer = null;
  addEventListener("mousemove", () => {
    controls.classList.remove("hidden");
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => {
      if (!tl.paused && gate.classList.contains("off")) controls.classList.add("hidden");
    }, 2600);
  });

  // expose for debugging / screenshot harness
  window.__film = { tl, TOTAL, seek: (t) => { tl.seek(t); lastT = t; tick(); }, begin };
})();
