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

Usa **openfootball/worldcup.json** (dominio público, gratis, SIN API key ni límites):
`https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json`

El archivo se actualiza con los marcadores conforme avanza el torneo. El script
descarga ese JSON, toma solo los 72 partidos de fase de grupos (ignora la fase
final que aún tiene placeholders) y deduce el resultado de cada uno por el marcador
final (`score.ft`).

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

- **`AVISO — nombres de equipo no reconocidos`**: openfootball nombró a un equipo
  distinto a lo previsto. Agrega ese nombre exacto al alias correcto en `teams.py`.
- Si **openfootball no responde** (raro, pero pasa), el script sale con error y
  **NO** sobreescribe el `index.html` bueno: la página se queda en el último estado válido.
- openfootball a veces tarda unas horas en cargar el marcador final de un partido
  recién jugado. Si un resultado no aparece de inmediato, dale tiempo o captúralo
  a mano con el admin local mientras tanto.

## Respaldo manual
Si un día la API no coopera, tu panel admin local (`quiniela_ADMIN_jorge.html`)
sigue sirviendo para capturar a mano y exportar. Cinturón y tirantes.

## Ajustar el horario del cron
En `.github/workflows/quiniela.yml`. Está en UTC (CDMX = UTC-6). Ahorita corre cada
30 min de 10:00 a 00:00 CDMX. La fuente (openfootball) es gratis y sin límite de
llamadas, así que puedes correrlo tan seguido como quieras sin preocuparte por cuotas.
