"""UNTESTED against live NBA data. Builds data/nba.json via nba_api.
Uses one league-wide request per season (fast) instead of one per player."""
import json, os, sys, time, datetime
from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamelog
SEASONS = ['2025-26', '2026-27']   # oldest first; update each year
K = {'PTS':'pts','REB':'reb','FGM':'fgm','AST':'ast','TOV':'tov','DREB':'dreb','OREB':'oreb','BLK':'blk','STL':'stl','FG3M':'fg3m','FTM':'ftm','PF':'pf'}
T = [{'id':str(t['id']),'name':t['full_name'],'abbr':t['abbreviation'],'oppFactor':1.0} for t in teams.get_teams()]
ab = {t['abbr']: t['id'] for t in T}
def log(*a): print(*a, flush=True)
def season_rows(s):
    for attempt in range(3):
        try:
            log('fetching', s, 'attempt', attempt + 1)
            df = leaguegamelog.LeagueGameLog(season=s, player_or_team_abbreviation='P', timeout=60).get_data_frames()[0]
            log(s, 'rows:', len(df)); return df.to_dict('records')
        except Exception as e:
            log('failed:', type(e).__name__, str(e)[:200]); time.sleep(5 * (attempt + 1))
    return None
rows = []
for s in SEASONS:
    r = season_rows(s)
    if r is None and s == SEASONS[0]: sys.exit('Could not reach NBA stats (possibly blocked from this server).')
    rows += r or []
rows.sort(key=lambda r: r['GAME_DATE'])
by = {}
for r in rows: by.setdefault(r['PLAYER_ID'], []).append(r)
out = []
for pid, rs in by.items():
    rs = rs[-40:]
    team = ab.get(rs[-1]['MATCHUP'].split()[0])
    if len(rs) < 11 or not team: continue
    logs = []
    for r in rs:
        g = {'d': r['GAME_DATE'], 'opp': ab.get(r['MATCHUP'].split()[-1], '')}
        for a, b in K.items(): g[b] = int(r[a] or 0)
        for a, b in (('FG3_PCT','fg3p'),('FG_PCT','fgp'),('FT_PCT','ftp')): g[b] = round(100 * float(r[a] or 0), 1)
        logs.append(g)
    out.append({'id': str(pid), 'name': rs[-1]['PLAYER_NAME'], 'team': team, 'logs': logs})
log('players built:', len(out))
if len(out) < 200: sys.exit('Too few players; not overwriting data.')
os.makedirs('data', exist_ok=True)
json.dump({'source':'nba_api','updated':datetime.date.today().isoformat(),'teams':T,'players':out}, open('data/nba.json','w'))
log('wrote data/nba.json')
