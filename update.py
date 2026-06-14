#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update.py — corazón de la automatización.

Hace:
  1. Pide a API-Football los fixtures del Mundial 2026 (league=1, season=2026).
  2. Casa cada fixture con uno de los 72 partidos de la quiniela (por los dos equipos).
  3. Si el partido terminó, deduce el resultado 1/E/2 con el marcador final.
  4. Recalcula los puntos de los 9 jugadores.
  5. Reescribe index.html (marcador público de solo lectura).

Diseño defensivo (estilo ASM):
  - Si un equipo no se reconoce, lo reporta y NO inventa resultado.
  - Solo cuenta partidos con status final (FT/AET/PEN). Los demás quedan pendientes.
  - Loguea "casé X de Y fixtures" para detectar nombres raros al instante.
  - Si la API falla, sale con error y NO sobreescribe el index.html bueno.
"""

import os
import sys
import json
import datetime
import urllib.request
import urllib.error

from teams import code_for, NOMBRE
from picks import MATCHES, PICKS, PEN, PLAYERS

API_BASE = "https://v3.football.api-sports.io"
LEAGUE_ID = 1        # FIFA World Cup en API-Football
SEASON = 2026
# estados que consideramos "partido terminado" según la doc de API-Football
FINISHED = {"FT", "AET", "PEN"}

OUT = os.path.join(os.path.dirname(__file__), "index.html")


def log(msg):
    print(msg, flush=True)


def api_get(path):
    key = os.environ.get("API_FOOTBALL_KEY")
    if not key:
        log("ERROR: falta la variable de entorno API_FOOTBALL_KEY (el secret del repo).")
        sys.exit(1)
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(url, headers={"x-apisports-key": key})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        log(f"ERROR HTTP {e.code} al pedir {path}: {e.read()[:300]}")
        sys.exit(1)
    except Exception as e:
        log(f"ERROR de red al pedir {path}: {e}")
        sys.exit(1)
    # API-Football mete los errores dentro del cuerpo, no en el status
    if data.get("errors"):
        log(f"ERROR de la API: {data['errors']}")
        sys.exit(1)
    return data.get("response", [])


def build_index():
    """índice {frozenset(codigoLocal, codigoVisita): posicion 0..71}"""
    idx = {}
    for i, m in enumerate(MATCHES):
        idx[frozenset((m[3], m[4]))] = i
    return idx


def fetch_results():
    """devuelve lista de 72: ''|'1'|'E'|'2'."""
    results = [""] * 72
    pos_by_pair = build_index()

    fixtures = api_get(f"/fixtures?league={LEAGUE_ID}&season={SEASON}")
    log(f"API devolvió {len(fixtures)} fixtures del Mundial.")

    matched = 0
    finished = 0
    unknown_names = set()

    for fx in fixtures:
        try:
            home_name = fx["teams"]["home"]["name"]
            away_name = fx["teams"]["away"]["name"]
            status = fx["fixture"]["status"]["short"]
            gh = fx["goals"]["home"]
            ga = fx["goals"]["away"]
        except (KeyError, TypeError):
            continue

        ch = code_for(home_name)
        ca = code_for(away_name)
        if ch is None:
            unknown_names.add(home_name)
        if ca is None:
            unknown_names.add(away_name)
        if ch is None or ca is None:
            continue

        pos = pos_by_pair.get(frozenset((ch, ca)))
        if pos is None:
            # un partido de ese par que no está en nuestra hoja (no debería pasar en grupos)
            continue
        matched += 1

        if status not in FINISHED or gh is None or ga is None:
            continue  # aún no termina: lo dejamos pendiente

        # ¿el equipo local de la API es el equipo local de NUESTRA hoja?
        m = MATCHES[pos]
        home_is_our_local = (ch == m[3])
        if gh == ga:
            results[pos] = "E"
        else:
            api_home_wins = gh > ga
            our_local_wins = api_home_wins if home_is_our_local else (not api_home_wins)
            results[pos] = "1" if our_local_wins else "2"
        finished += 1

    log(f"Casé {matched} de 72 partidos de la quiniela. Terminados con resultado: {finished}.")
    if unknown_names:
        log("AVISO — nombres de equipo no reconocidos (revisa teams.py): "
            + ", ".join(sorted(unknown_names)))
    return results


def score(results):
    played = sum(1 for r in results if r)
    rows = []
    for p in PLAYERS:
        picks = PICKS[p]
        pts = sum(1 for i, r in enumerate(results) if r and picks[i] == r)
        rows.append({"p": p, "pts": pts, "errs": played - pts})
    rows.sort(key=lambda x: (-x["pts"], x["errs"], x["p"]))
    return rows, played


def render_html(results, rows, played):
    """genera el index.html completo, estático, con los datos ya incrustados."""
    stamp = datetime.datetime.utcnow() - datetime.timedelta(hours=6)  # CDMX (UTC-6)
    stamp_str = stamp.strftime("%d/%m/%Y %H:%M") + " (hora CDMX)"

    data = {
        "matches": MATCHES,
        "picks": PICKS,
        "pen": PEN,
        "players": PLAYERS,
        "nombre": NOMBRE,
        "results": results,
    }
    data_json = json.dumps(data, ensure_ascii=False)

    # plantilla: el HTML/JS del marcador de solo lectura
    return TEMPLATE.replace("/*DATA*/", data_json).replace("__STAMP__", stamp_str)


def main():
    results = fetch_results()
    rows, played = score(results)
    log("Marcador actual:")
    for i, r in enumerate(rows):
        log(f"  {i+1}. {r['p']}: {r['pts']} pts ({r['errs']} err)")
    html = render_html(results, rows, played)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    log(f"index.html regenerado ({played}/72 partidos capturados).")


# ===================== PLANTILLA HTML (solo lectura) =====================
TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>Quiniela Mundial 2026 · Marcador</title>
<style>
  :root{--bg:#0d2014;--panel:#143122;--panel2:#1b3f2c;--line:rgba(240,236,222,.13);--ink:#f0ecde;--muted:#94ab9a;--gold:#efc15c;--ok:#6fd08c;--bad:#e96a5b;--chalk:rgba(240,236,222,.55)}
  *{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
  html{font-size:16px}
  body{background:var(--bg);color:var(--ink);min-height:100vh;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background-image:radial-gradient(ellipse 120% 60% at 50% -10%, rgba(239,193,92,.08), transparent 60%),repeating-linear-gradient(90deg, transparent 0 64px, rgba(255,255,255,.018) 64px 128px);padding-bottom:90px}
  header{padding:18px 16px 12px;text-align:center;position:relative;border-bottom:2px solid var(--line)}
  header::after{content:"";position:absolute;left:50%;bottom:-6px;transform:translateX(-50%);width:84px;height:10px;border:2px solid var(--chalk);border-top:none;border-radius:0 0 8px 8px;opacity:.5}
  h1{font-size:1.35rem;letter-spacing:.06em;text-transform:uppercase;font-weight:900;line-height:1.15}
  h1 .gold{color:var(--gold)}
  .sub{color:var(--muted);font-size:.78rem;margin-top:4px;letter-spacing:.04em}
  .badge-ro{display:inline-block;margin-top:8px;font-size:.64rem;font-weight:900;letter-spacing:.14em;color:#0d2014;background:var(--muted);border-radius:5px;padding:3px 8px}
  .pot{display:inline-flex;gap:14px;margin-top:10px;padding:6px 14px;border:1px solid var(--line);border-radius:999px;font-size:.74rem;color:var(--muted);background:rgba(0,0,0,.18)}
  .pot b{color:var(--gold);font-weight:800}
  .stamp{display:block;margin-top:8px;font-size:.68rem;color:var(--muted)}
  .live{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--ok);margin-right:5px;animation:pulse 2s infinite}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
  nav{position:fixed;bottom:0;left:0;right:0;z-index:50;display:flex;background:#0a1a10ee;backdrop-filter:blur(10px);border-top:1px solid var(--line);padding:6px 8px calc(8px + env(safe-area-inset-bottom))}
  nav button{flex:1;background:none;border:none;color:var(--muted);font:inherit;font-size:.78rem;font-weight:700;padding:9px 4px;border-radius:12px;cursor:pointer;letter-spacing:.02em}
  nav button .ico{display:block;font-size:1.15rem;margin-bottom:2px}
  nav button.on{color:var(--gold);background:rgba(239,193,92,.10)}
  main{max-width:680px;margin:0 auto;padding:14px 12px}
  .hidden{display:none}
  .progress-note{font-size:.78rem;color:var(--muted);text-align:center;margin-bottom:12px}
  .progress-note b{color:var(--ink)}
  .rowP{display:flex;align-items:center;gap:10px;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:12px;margin-bottom:8px;position:relative;overflow:hidden}
  .rowP.lead{border-color:rgba(239,193,92,.55);background:linear-gradient(180deg, rgba(239,193,92,.10), var(--panel))}
  .rank{width:26px;text-align:center;font-weight:900;font-size:1rem;color:var(--muted);flex:none}
  .rowP.lead .rank{color:var(--gold)}
  .pdot{width:10px;height:10px;border-radius:50%;flex:none}
  .pname{font-weight:800;font-size:.95rem;flex:1;min-width:0}
  .pname small{display:block;font-weight:600;color:var(--muted);font-size:.7rem;margin-top:2px}
  .pname small .hit{color:var(--ok)} .pname small .miss{color:var(--bad)}
  .ppts{font-size:1.5rem;font-weight:900;color:var(--gold);flex:none;line-height:1}
  .ppts small{display:block;font-size:.6rem;color:var(--muted);font-weight:700;text-align:right;letter-spacing:.06em}
  .pbar{position:absolute;left:0;bottom:0;height:3px;background:linear-gradient(90deg,var(--gold),#f7e3ae);transition:width .5s ease}
  .prize{font-size:.66rem;font-weight:800;color:#0d2014;background:var(--gold);border-radius:6px;padding:2px 6px;flex:none}
  .prize.p2{background:#cfd6cd} .prize.p3{background:#d9a05b}
  .tiebreak{font-size:.7rem;color:var(--muted);text-align:center;margin-top:10px;line-height:1.5}
  .selwrap{position:relative;margin-bottom:10px}
  select{width:100%;appearance:none;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:12px;padding:12px 38px 12px 12px;font:inherit;font-size:.85rem;font-weight:700}
  .selwrap::after{content:"▾";position:absolute;right:14px;top:50%;transform:translateY(-50%);color:var(--muted);pointer-events:none}
  .navmatch{display:flex;gap:8px;margin-bottom:12px}
  .navmatch button{flex:1;background:var(--panel);border:1px solid var(--line);color:var(--ink);border-radius:10px;padding:9px;font:inherit;font-weight:800;font-size:.8rem;cursor:pointer}
  .bigmatch{text-align:center;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px 10px;margin-bottom:12px}
  .bigmatch .vs{font-size:1.05rem;font-weight:900;letter-spacing:.02em}
  .bigmatch .meta{font-size:.7rem;color:var(--muted);margin-top:4px}
  .bigmatch .resline{margin-top:8px;font-size:.78rem;font-weight:800;color:var(--gold)}
  .bigmatch .resline.none{color:var(--muted);font-weight:600}
  .pickrow{display:flex;align-items:center;gap:10px;padding:9px 10px;border-bottom:1px solid var(--line)}
  .pickrow:last-child{border-bottom:none}
  .pickrows{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden}
  .pickrow .nm{flex:1;font-weight:700;font-size:.88rem;display:flex;align-items:center;gap:8px}
  .pickchip{min-width:96px;text-align:center;border-radius:9px;padding:6px 8px;font-size:.76rem;font-weight:900;background:var(--panel2);border:1.5px solid var(--line);letter-spacing:.02em}
  .pickchip.hit{border-color:var(--ok);color:var(--ok);background:rgba(111,208,140,.1)}
  .pickchip.miss{border-color:var(--bad);color:var(--bad);background:rgba(233,106,91,.08);opacity:.85}
  .note{font-size:.7rem;color:var(--muted);line-height:1.5;margin-top:10px;padding:0 4px}
</style>
</head>
<body>
<header>
  <h1>Quiniela <span class="gold">Mundial 2026</span></h1>
  <div class="sub">Fase de grupos · 9 analistas certificados · 72 partidos</div>
  <div><span class="badge-ro">📊 MARCADOR OFICIAL · SOLO LECTURA</span></div>
  <div class="pot">🏆 Bolsa <b>$2,700</b><span>1º $1,890 · 2º $540 · 3º $270</span></div>
  <span class="stamp"><span class="live"></span>Actualizado automático: __STAMP__</span>
</header>
<main>
  <section id="view-tabla"></section>
  <section id="view-picks" class="hidden"></section>
</main>
<nav>
  <button id="tab-tabla" class="on" onclick="show('tabla')"><span class="ico">🏆</span>Tabla</button>
  <button id="tab-picks" onclick="show('picks')"><span class="ico">📋</span>Picks</button>
</nav>
<script>
const DATA = /*DATA*/;
const M = DATA.matches, PICKS = DATA.picks, PEN = DATA.pen, PLAYERS = DATA.players, NOM = DATA.nombre, RES = DATA.results;
let cur = 0;
function scores(){
  let played = RES.filter(function(r){return r;}).length;
  let rows = PLAYERS.map(function(p){
    let pts=0; RES.forEach(function(r,i){ if(r && PICKS[p][i]===r) pts++; });
    return {p:p, pts:pts, errs:played-pts};
  });
  rows.sort(function(a,b){ return b.pts-a.pts || a.errs-b.errs || a.p.localeCompare(b.p); });
  return {rows:rows, played:played};
}
function renderTabla(){
  let s = scores();
  let html = '<div class="progress-note">Partidos capturados: <b>'+s.played+' / 72</b></div>';
  s.rows.forEach(function(r,i){
    let lead = (i===0 && s.played>0);
    let prize = s.played>0 ? (i===0?'<span class="prize">$1,890</span>': i===1?'<span class="prize p2">$540</span>': i===2?'<span class="prize p3">$270</span>':'') : '';
    let pct = s.played ? (r.pts/s.played*100) : 0;
    html += '<div class="rowP'+(lead?' lead':'')+'"><div class="rank">'+((i===0&&s.played>0)?'👑':(i+1))+'</div><span class="pdot" style="background:'+PEN[r.p]+'"></span><div class="pname">'+r.p+'<small><span class="hit">✓ '+r.pts+' aciertos</span> · <span class="miss">✗ '+r.errs+' errores</span></small></div>'+prize+'<div class="ppts">'+r.pts+'<small>PTS</small></div><div class="pbar" style="width:'+pct+'%"></div></div>';
  });
  html += '<div class="tiebreak">Desempate oficial: 1) menor número de errores · 2) mayor cantidad de aciertos · 3) sorteo<br>Bolsa total $2,700 (9 × $300) · 70% / 20% / 10%</div>';
  document.getElementById('view-tabla').innerHTML = html;
}
function renderPicks(){
  let m = M[cur], r = RES[cur];
  let opts = M.map(function(x,i){ return '<option value="'+i+'"'+(i===cur?' selected':'')+'>J'+x[0]+' · '+x[1]+' — '+NOM[x[3]]+' vs '+NOM[x[4]]+'</option>'; }).join('');
  let rows = '';
  PLAYERS.forEach(function(p){
    let pk = PICKS[p][cur];
    let label = pk==='E' ? 'EMPATE' : NOM[pk==='1'?m[3]:m[4]];
    let cls = r ? (pk===r?'hit':'miss') : '';
    rows += '<div class="pickrow"><div class="nm"><span class="pdot" style="background:'+PEN[p]+'"></span>'+p+'</div><div class="pickchip '+cls+'">'+label+'</div></div>';
  });
  let resline = r ? ('Resultado: ' + (r==='E'?'Empate':'Ganó '+NOM[r==='1'?m[3]:m[4]])) : 'Resultado pendiente';
  document.getElementById('view-picks').innerHTML =
    '<div class="selwrap"><select onchange="goMatch(this.value)">'+opts+'</select></div>'+
    '<div class="navmatch"><button onclick="goMatch('+((cur+71)%72)+')">‹ Anterior</button><button onclick="goMatch('+((cur+1)%72)+')">Siguiente ›</button></div>'+
    '<div class="bigmatch"><div class="vs">'+NOM[m[3]]+' vs '+NOM[m[4]]+'</div><div class="meta">Jornada '+m[0]+' · '+m[1]+'/2026 · '+m[2]+' h</div><div class="resline '+(r?'':'none')+'">'+resline+'</div></div>'+
    '<div class="pickrows">'+rows+'</div>'+
    '<div class="note">Marcador de solo lectura, actualizado automáticamente con los resultados oficiales. Si crees que un pick tuyo está mal transcrito de tu hoja, dile a Jorge.</div>';
}
function goMatch(i){ cur=+i; renderPicks(); }
function show(v){ ['tabla','picks'].forEach(function(x){ document.getElementById('view-'+x).classList.toggle('hidden',x!==v); document.getElementById('tab-'+x).classList.toggle('on',x===v); }); window.scrollTo({top:0}); }
renderTabla(); renderPicks();
</script>
</body>
</html>"""


if __name__ == "__main__":
    main()
