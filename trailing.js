<script>
/* ══════════════════════════════════════════════════════════════
   MERGED FLOW — INSTALL APP STEP + CONTINUE INTO PWA
   Replaces the old "register sub-app" overlay. This version does NOT
   restrict navigation (the whole app lives in this one file now) and
   continues the user in-app after install instead of redirecting to a
   separate file.
   Flow: ... → otp → installApp → (install / continue) → KYC selfie → dashboard
   ══════════════════════════════════════════════════════════════ */
(function(){
  function defineInstallView(){
    if (typeof window.views !== 'object') { return setTimeout(defineInstallView, 60); }
    window.views.installApp = function(){
      return `
<div style="min-height:100vh;background:linear-gradient(180deg,#2d4a46 0%,#162626 50%,#0a0f0d 100%);color:#fff;padding:48px 24px 32px;display:flex;flex-direction:column;align-items:center;text-align:center">
  <div style="margin-top:24px;width:96px;height:96px;border-radius:24px;background:rgba(168,212,204,0.12);display:flex;align-items:center;justify-content:center;border:1px solid rgba(168,212,204,0.35)">
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#a8d4cc" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
  </div>
  <h1 style="font-family:'Plus Jakarta Sans',Inter,sans-serif;font-size:28px;font-weight:700;margin:24px 0 12px;letter-spacing:-0.5px">Install bank36 to continue</h1>
  <p style="color:#a8b3b0;font-size:15px;line-height:1.55;max-width:340px;margin:0 0 32px">Your account is verified. Install the bank36 app on your device, then continue to finish setup (selfie &amp; video verification) and access your dashboard.</p>
  <button id="installBtn" style="background:#a8d4cc;color:#0a0f0d;border:0;border-radius:32px;padding:18px 32px;font-size:16px;font-weight:700;font-family:inherit;cursor:pointer;width:100%;max-width:340px;box-shadow:0 8px 24px rgba(168,212,204,0.2)">Install App</button>
  <div id="installHint" style="margin-top:20px;color:#7a8a86;font-size:13px;max-width:340px;line-height:1.5"></div>
  <div id="continueRow" style="display:none;margin-top:24px;width:100%;max-width:340px">
    <button id="continueAppBtn" style="background:transparent;color:#a8d4cc;border:1px solid rgba(168,212,204,0.35);border-radius:32px;padding:16px;width:100%;font-weight:600;font-family:inherit;cursor:pointer">Continue to bank36 →</button>
  </div>
  <div style="margin-top:auto;padding-top:40px;color:#5a6864;font-size:12px">After installing, you'll continue to identity verification.</div>
</div>`;
    };
  }
  defineInstallView();

  // Continue into the app — go('dashboard') triggers the KYC gate which routes
  // a freshly-registered (not-yet-verified) user to the selfie step first.
  function continueToApp(){
    try { if (typeof window.go === 'function') window.go('dashboard'); } catch(e){}
  }
  window._b36ContinueToApp = continueToApp;

  // Once the OS confirms the PWA was installed, continue automatically.
  window.addEventListener('appinstalled', function(){
    setTimeout(continueToApp, 600);
  });

  // Handle the Install / Continue buttons on the installApp screen.
  document.addEventListener('click', function(e){
    var cont = e.target && e.target.closest && e.target.closest('#continueAppBtn');
    if (cont) { e.preventDefault(); continueToApp(); return; }

    var btn = e.target && e.target.closest && e.target.closest('#installBtn');
    if (!btn) return;

    var hint = document.getElementById('installHint');
    var row  = document.getElementById('continueRow');
    var p = window._pwaPrompt;

    if (p && typeof p.prompt === 'function') {
      p.prompt();
      if (p.userChoice && p.userChoice.then) {
        p.userChoice.then(function(choice){
          if (choice && choice.outcome === 'accepted') {
            if (hint) hint.textContent = 'Installing… continuing to verification.';
            setTimeout(continueToApp, 900);
          } else {
            if (hint) hint.textContent = 'Install dismissed — you can still continue below.';
            if (row) row.style.display = 'block';
          }
          window._pwaPrompt = null;
        });
      }
    } else {
      // iOS / browsers without beforeinstallprompt: show manual A2HS instructions.
      var ua = navigator.userAgent || '';
      var isIOS = /iPad|iPhone|iPod/.test(ua);
      if (hint) hint.innerHTML = isIOS
        ? 'Tap the <strong>Share</strong> icon in Safari, then choose <strong>Add to Home Screen</strong>. Then tap Continue.'
        : 'Open the browser menu (⋮) and choose <strong>Install app</strong> / <strong>Add to Home screen</strong>. Then tap Continue.';
      if (row) row.style.display = 'block';
    }
  });
})();
</script>
