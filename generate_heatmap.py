"""Gera contrib-heatmap.svg animado (células "pulam" coluna a coluna) com os últimos 12 meses."""
import json, os, sys, urllib.request
from datetime import date

USER = os.environ.get("GH_USER", "GabrielBechtlufft")
LABEL = "gabriel@github"
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date weekday } }
      }
    }
  }
}"""

def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"},
    )
    return json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def level(n):
    return 0 if n == 0 else 1 if n < 3 else 2 if n < 6 else 3 if n < 10 else 4

def build(cal):
    weeks = cal["weeks"]
    PITCH, X0, Y0 = 15, 58, 56            # centro da 1ª célula
    W = X0 + len(weeks) * PITCH + 10
    H = Y0 + 7 * PITCH + 52
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
         '<defs><linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d1420"/><stop offset="1" stop-color="#0a0e14"/></linearGradient></defs>',
         f'<rect width="{W}" height="{H}" rx="12" fill="url(#hbg)"/><rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="#1f6feb" stroke-opacity="0.55"/>',
         f'<line x1="0" y1="30" x2="{W}" y2="30" stroke="#1f6feb" stroke-opacity="0.35"/>',
         '<circle cx="22" cy="15" r="5" fill="#ff5f56"/><circle cx="38" cy="15" r="5" fill="#ffbd2e"/><circle cx="54" cy="15" r="5" fill="#27c93f"/>',
         f'<text x="{W/2}" y="19" fill="#7d8590" font-size="12" text-anchor="middle">{LABEL}: ~/contributions --graph</text>']
    # rótulos de mês (quando o mês muda na 1ª linha da semana)
    prev = None
    for w, week in enumerate(weeks):
        m = int(week["contributionDays"][0]["date"][5:7]) - 1
        if m != prev and w < len(weeks) - 2:
            o.append(f'<text x="{X0 - 6 + w*PITCH}" y="44" fill="#7d8590" font-size="10">{MESES[m]}</text>')
        prev = m
    for r, name in ((1, "Seg"), (3, "Qua"), (5, "Sex")):
        o.append(f'<text x="22" y="{Y0 + r*PITCH + 4.4}" fill="#7d8590" font-size="9">{name}</text>')
    # células com pop-in por coluna
    for w, week in enumerate(weeks):
        for day in week["contributionDays"]:
            r = day.get("weekday", date.fromisoformat(day["date"]).isoweekday() % 7)
            n = day["contributionCount"]; t = w * 0.045
            o.append(f'<g transform="translate({X0 + w*PITCH},{Y0 + r*PITCH})" opacity="0">'
                     f'<rect x="-6" y="-6" width="12" height="12" rx="2.5" fill="{COLORS[level(n)]}"><title>{day["date"]}: {n}</title></rect>'
                     f'<animate attributeName="opacity" from="0" to="1" begin="{t:.3f}s" dur="0.09s" fill="freeze"/>'
                     f'<animateTransform attributeName="transform" type="scale" additive="sum" values="0.1;1.15;1" keyTimes="0;0.72;1" calcMode="spline" keySplines="0.22 1 0.36 1;0.33 0 0.66 1" begin="{t:.3f}s" dur="0.42s" fill="freeze"/></g>')
    # legenda + prompt
    yl = Y0 + 7 * PITCH + 8
    o.append(f'<line x1="0" y1="{yl}" x2="{W}" y2="{yl}" stroke="#1f6feb" stroke-opacity="0.35"/>')
    o.append(f'<text x="20" y="{yl+24}" fill="#7d8590" font-size="12">{LABEL}:~$ <tspan fill="#c9d1d9">{cal["totalContributions"]} contribuições nos últimos 12 meses</tspan></text>')
    for i, col in enumerate(COLORS):
        o.append(f'<rect x="{W-20-(5-i)*15}" y="{yl+14}" width="11" height="11" rx="2.5" fill="{col}"/>')
    o.append('</svg>')
    return "\n".join(o)

if __name__ == "__main__":
    if "--demo" in sys.argv:   # dados fictícios p/ testar sem token
        import random, datetime as dt
        d0 = dt.date.today() - dt.timedelta(days=365); d0 -= dt.timedelta(days=(d0.isoweekday() % 7))
        weeks = [{"contributionDays": [{"date": (d0 + dt.timedelta(days=7*w+i)).isoformat(), "weekday": i,
                  "contributionCount": random.choice([0,0,0,1,2,4,7,12])} for i in range(7)]} for w in range(53)]
        cal = {"totalContributions": 999, "weeks": weeks}
    else:
        cal = fetch()
    open("contrib-heatmap.svg", "w", encoding="utf-8").write(build(cal))
