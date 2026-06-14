# Quiniela Mundial 2026 — marcador automático

Marcador en vivo que se actualiza solo con los resultados oficiales del Mundial,
usando API-Football + GitHub Actions. Cero captura manual durante los partidos.

**Página pública:** https://gk5mvgnnj4-spec.github.io/quiniela-mundial_2026/

---

## Cómo funciona

```
GitHub Actions (cron cada 30 min en horario de partidos)
   -> corre update.py
      -> pide resultados a API-Football (league=1, season=2026)
      -> casa cada partido con la hoja y deduce 1 / E / 2
      -> recalcula puntos de los 9 jugadores
      -> reescribe index.html
      -> commit + push automático
   -> GitHub Pages sirve la página actualizada
```

## Fuente de datos

Usa el endpoint público del **scoreboard de ESPN** (gratis, SIN API key):
`https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=YYYYMMDD`

ESPN actualiza marcadores casi en vivo. El script recorre las fechas de la fase
de grupos (11–27 jun 2026), junta todos los partidos, toma solo los 72 de grupos
y deduce el resultado de cada uno (`status.type.completed` + `score`).

Nota: es un endpoint no oficial de ESPN. Si algún día deja de responder, el script
sale con error y NO sobreescribe el `index.html` bueno; mientras tanto puedes
capturar a mano con el admin local.

## Archivos

| Archivo | Qué es |
|---|---|
| `update.py` | Script principal: descarga el JSON, calcula, regenera `index.html` |
| `teams.py` | Mapeo de los 48 equipos (nombre en inglés -> código de la hoja) |
| `picks.py` | Los 72 partidos y los picks de los 9 jugadores |
| `index.html` | El marcador público (lo genera `update.py`, NO se edita a mano) |
| `.github/workflows/quiniela.yml` | El cron de GitHub Actions |

---

## Setup (una sola vez)

### 1. Subir estos archivos al repo
Sube todo respetando la estructura (incluida la carpeta `.github/workflows/`).

### 2. Activar GitHub Pages
**Settings -> Pages -> Source: Deploy from a branch -> Branch: `main` / root -> Save**

### 3. Activar y probar el Action
1. Pestaña **Actions** -> si pide habilitarlos, acepta.
2. Entra a "Actualizar marcador quiniela" -> **Run workflow** (corrida manual de prueba).
3. Revisa el log: debe decir `Casé 72 de 72 partidos de grupos`.
4. Abre la página pública y verifica que se ve el marcador.

Listo. A partir de ahí corre solo según el cron. **No necesitas ninguna API key.**

---

## Vigilancia (lo único que tienes que checar de vez en cuando)

El script está hecho a prueba de fallos, pero revisa el log del Action si algo se ve raro:

- **`AVISO — nombres de equipo no reconocidos`**: ESPN nombró a un equipo distinto
  a lo previsto. Agrega ese nombre exacto al alias correcto en `teams.py`.
- Si **ESPN no responde** en ninguna fecha, el script sale con error y **NO**
  sobreescribe el `index.html` bueno: la página se queda en el último estado válido.
- ESPN es un endpoint no oficial: si en algún momento cambian la URL o el formato,
  el marcador dejaría de actualizarse. Mientras lo arreglas, captura a mano con el
  admin local (`quiniela_ADMIN_jorge.html`).

## Respaldo manual
Si un día la API no coopera, tu panel admin local (`quiniela_ADMIN_jorge.html`)
sigue sirviendo para capturar a mano y exportar. Cinturón y tirantes.

## Ajustar el horario del cron
En `.github/workflows/quiniela.yml`. Está en UTC (CDMX = UTC-6). Ahorita corre cada
30 min de 10:00 a 00:00 CDMX. ESPN es gratis y sin límite publicado; el script hace
~17 llamadas por corrida (una por fecha de grupos), sin problema.
