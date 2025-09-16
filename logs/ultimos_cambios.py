import sqlite3
from datetime import datetime
import os

DB_PATH = os.path.expanduser('~/.local/share/urlwatch/urls.db')

if not os.path.exists(DB_PATH):
    with open("logs/ultimos_cambios.txt", "w") as f:
        f.write("No existe la base de datos de urlwatch. ¿Se ejecutó urlwatch al menos una vez?\n")
    exit(0)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute('SELECT job, last_changed FROM job_state ORDER BY last_changed DESC')

with open("logs/ultimos_cambios.txt", "w") as f:
    f.write(f"{'Fecha último cambio':<20} | URL\n")
    f.write('-' * 70 + "\n")
    for job, last_changed in cur.fetchall():
        url = eval(job)['url']
        fecha = datetime.fromtimestamp(last_changed).strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"{fecha:<20} | {url}\n")

conn.close()
