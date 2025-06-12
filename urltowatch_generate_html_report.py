import json
from datetime import datetime

with open('cambios.json') as f:
    data = json.load(f)

html = ['<html><body>']

for job in data.get('jobs', []):
    name = job.get('name', 'Sin nombre')
    url = job.get('url', '#')
    changes = job.get('changes', [])
    if not changes:
        continue

    # Último cambio
    last_change = changes[-1]
    last_date = datetime.fromisoformat(last_change['timestamp']).strftime('%Y-%m-%d %H:%M')

    # Fechas anteriores (excluye el último)
    previous_dates = [
        datetime.fromisoformat(c['timestamp']).strftime('%Y-%m-%d %H:%M')
        for c in changes[:-1]
    ]

    # HTML principal
    html.append(f'<div>')
    html.append(f'<a href="{url}">{name}</a><br>')
    html.append(f'Último cambio: {last_date}<br>')

    # Elemento desplegable
    if previous_dates:
        html.append(f'''
            <details>
              <summary>Ver cambios anteriores</summary>
              <ul>
                {''.join(f'<li>{d}</li>' for d in previous_dates)}
              </ul>
            </details>
        ''')
    html.append(f'</div><hr>')

html.append('</body></html>')

with open('resultado.html', 'w') as f:
    f.write('\n'.join(html))
