#!/usr/bin/env python3
import base64, re, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
def p(name): return os.path.join(HERE, name)

with open(p('register.html'), 'r', encoding='utf-8') as f: base = f.read()
with open(p('landing.html'),  'r', encoding='utf-8') as f: land = f.read()
with open(p('trailing.js'),   'r', encoding='utf-8') as f: trailing = f.read().strip()
with open(p('icon.png'),      'rb') as f: icon_b64 = base64.b64encode(f.read()).decode('ascii')

report = []

# ── 0. Expose the local `views` object on window so the installApp view can be
#       registered onto the SAME object that go() renders from. ──
views_anchor = 'const views = {};'
assert base.count(views_anchor) == 1, "views declaration anchor not found"
base = base.replace(views_anchor, 'const views = {}; window.views = views;', 1)
report.append("Exposed the app's internal `views` registry on window.views so the installApp screen registers on the same object go() renders from")

# ── 1. Landing: rewrite the register handoff to postMessage the parent ──
old_handoff = "if (t){ e.preventDefault(); window.location.href = 'bank36-register.html'; }"
new_handoff = "if (t){ e.preventDefault(); try{ window.parent.postMessage('b36:openRegister','*'); }catch(_){ } }"
assert land.count(old_handoff) == 1, "landing handoff anchor not found"
land = land.replace(old_handoff, new_handoff, 1)
report.append("Landing CTAs (data-open-register) now postMessage('b36:openRegister') to parent instead of redirecting to bank36-register.html")

land_b64 = base64.b64encode(land.encode('utf-8')).decode('ascii')

# ── 2. Build the landing overlay markup + listener ──
overlay = (
'<!-- ════════ MERGED LANDING OVERLAY (isolated iframe) ════════ -->\n'
'<div id="b36Landing" style="position:fixed;inset:0;z-index:9000;background:#070b18">\n'
'  <iframe id="b36LandingFrame" title="Bank36 — Private Banking &amp; Wealth" '
'style="border:0;width:100%;height:100%;display:block" '
'src="data:text/html;base64,' + land_b64 + '"></iframe>\n'
'</div>\n'
'<script>\n'
'(function(){\n'
'  function hideLanding(){\n'
'    var el=document.getElementById("b36Landing");\n'
'    if(!el) return;\n'
'    el.style.transition="opacity .45s ease";\n'
'    el.style.opacity="0";\n'
'    el.style.pointerEvents="none";\n'
'    setTimeout(function(){ if(el&&el.parentNode){ el.style.display="none"; } }, 480);\n'
'  }\n'
'  window.b36HideLanding=hideLanding;\n'
'  window.addEventListener("message", function(e){\n'
'    if(e && e.data==="b36:openRegister"){\n'
'      hideLanding();\n'
'      (function tryGo(n){\n'
'        try{ if(typeof window.go==="function"){ window.go("accountType"); return; } }catch(_){ }\n'
'        if(n<40) setTimeout(function(){ tryGo(n+1); }, 150);\n'
'      })(0);\n'
'    }\n'
'  }, false);\n'
'})();\n'
'</script>\n'
)

anchor = '<div class="app" id="app">'
assert base.count(anchor) == 1, "app container anchor not found"
base = base.replace(anchor, overlay + anchor, 1)
report.append("Injected landing overlay (full marketing page in an isolated data-URI iframe, z-index 9000, below the 99999 splash) just above the main app container")

# ── 3. go(): hide landing overlay when an authenticated user is routed to dashboard ──
go_anchor = "function go(name){\n  if(name==='login'){slideIdx=0}"
go_new = ("function go(name){\n"
          "  if(name==='dashboard' && typeof window.b36HideLanding==='function'){ try{ window.b36HideLanding(); }catch(_){ } }\n"
          "  if(name==='login'){slideIdx=0}")
assert base.count(go_anchor) == 1, "go() anchor not found"
base = base.replace(go_anchor, go_new, 1)
report.append("go() now hides the landing overlay whenever the app routes to 'dashboard' (covers returning/auth auto-redirect)")

# ── 4. Replace the old register sub-app overlay (nav restriction + external redirect) ──
start_marker = '<script>\n/* ══════════ REGISTER SUB-APP OVERLAY ══════════'
si = base.find(start_marker)
assert si != -1, "register sub-app overlay start not found"
# find the closing </script> that precedes </body> after si
ei = base.find('</script>', si)
assert ei != -1
ei = ei + len('</script>')
base = base[:si] + trailing + base[ei:]
report.append("Replaced the old register sub-app overlay (which restricted navigation to registration screens and redirected to a separate bank36-app.html) with an in-app version: the Install App step now continues to dashboard (KYC selfie gate) within the same file")

# ── 5. Inline the PWA manifest (self-contained) with generated icon ──
import json
manifest = {
  "name": "bank36 — Private Banking & Wealth",
  "short_name": "bank36",
  "start_url": ".",
  "scope": ".",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#0a0f0d",
  "theme_color": "#0a0f0d",
  "icons": [
    {"src": "data:image/png;base64," + icon_b64, "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
  ]
}
manifest_data_uri = "data:application/manifest+json;base64," + base64.b64encode(
    json.dumps(manifest, separators=(',',':')).encode('utf-8')).decode('ascii')
old_manifest = '<link rel="manifest" href="manifest.json">'
assert base.count(old_manifest) == 1, "manifest link not found"
base = base.replace(old_manifest, '<link rel="manifest" href="' + manifest_data_uri + '">', 1)
# also inline an apple-touch-icon for iOS Add-to-Home-Screen
base = base.replace(
  old_manifest, '', 0)  # no-op safeguard
report.append("Inlined the PWA manifest as a data URI (with a generated 512x512 icon) so the file is self-contained — external manifest.json no longer required")

# ── Write output ──
out_dir = os.path.join(HERE, '..', 'public')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, 'bank36.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(base)

print("WROTE", os.path.abspath(out_path))
print("SIZE", len(base), "bytes /", base.count('\n')+1, "lines")
print("CHECKS:")
print("  views.installApp present:", 'window.views.installApp' in base)
print("  REG restriction removed:", 'REG_ALLOWED' not in base)
print("  external bank36-app.html redirect removed:", "location.href = window.PWA_APP_URL" not in base)
print("  landing iframe present:", 'b36LandingFrame' in base)
print("  inline manifest present:", 'data:application/manifest+json' in base)
print("\nREPORT:")
for i,r in enumerate(report,1): print(f"  {i}. {r}")
