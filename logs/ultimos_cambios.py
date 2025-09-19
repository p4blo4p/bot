import os
import sys

# La ruta por defecto de la base de datos de urlwatch
db_path = os.path.expanduser('~/.cache/urlwatch/urls.db')

if not os.path.exists(db_path):
    print("La base de datos de urlwatch no existe aún. Omitiendo el script.")
    print("Esto es normal en la primera ejecución del workflow.")
    sys.exit(0) # Sale del script sin error

# ... el resto de tu código para procesar la base de datos ...
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
