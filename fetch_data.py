"""UNTESTED against live NBA data. Builds data/nba.json via nba_api.
Run: pip install nba_api pandas ; python fetch_data.py
Pulls the two most recent seasons and keeps each player's last 40 games."""
import json, os, time, datetime
from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import playergamelog
SEASONS = ['2025-26', '2026-27']   # oldest first; update each year
K = {'PTS':'pts','REB':'reb','FGM':'fgm','AST':'ast','TOV':'tov','DREB':'dreb','OREB':'oreb','BLK':'blk','STL':'stl','FG3M':'fg3m','FTM':'ftm','PF':'pf'}
T = [{'id':str(t['id']),'name':t['full_name'],'abbr':t['abbreviation'],'oppFactor':1.0} for t in teams.get_teams()]
ab = {t['abbr']: t['id'] for t in T}
def games(pid):
    rows = []
    for s in SEASONS:
        for attempt in range(3):
            try:
                df = playergamelog.PlayerGameLog(player_id=pid, season=s, timeout=30).get_data_frames()[0]
                rows += list(df.iloc[::-1].to_dict('records')); break
            except Exception:
                time.sleep(2 * (attempt + 1))
        time.sleep(0.6)
    return rows
out = []
for p in players.get_active_players():
    rows = games(p['id'])[-40:]
    if len(rows) < 11: continue
    team = ab.get(rows[-1]['MATCHUP'].split()[0])
    if not team: continue
    logs = []
    for r in rows:
        g = {'d': r['GAME_DATE'], 'opp': ab.get(r['MATCHUP'].split()[-1], '')}
        for a, b in K.items(): g[b] = int(r[a])
        for a, b in (('FG3_PCT','fg3p'),('FG_PCT','fgp'),('FT_PCT','ftp')): g[b] = round(100 * float(r[a] or 0), 1)
        logs.append(g)
    out.append({'id': str(p['id']), 'name': p['full_name'], 'team': team, 'logs': logs})
if len(out) < 200: raise SystemExit('Too few players fetched; not overwriting data.')
os.makedirs('data', exist_ok=True)
json.dump({'source':'nba_api','updated':datetime.date.today().isoformat(),'teams':T,'players':out}, open('data/nba.json','w'))
print('wrote', len(out), 'players')
