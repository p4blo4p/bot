import sqlite3
import os
import sys
from datetime import datetime

# --- Configuración ---
# Ruta estándar de la base de datos de urlwatch.
DB_PATH = os.path.expanduser('~/.cache/urlwatch/urls.db')
# Archivo de salida donde se guardará el reporte.
OUTPUT_FILE = 'logs/ultimos_cambios.txt'

def get_last_changes():
    """
    Se conecta a la base de datos de urlwatch, extrae la fecha del último
    cambio para cada URL y devuelve los resultados ordenados.
    """
    # 1. Comprobar si la base de datos existe. Si no, salir sin error.
    #    Esto es crucial para que la primera ejecución del workflow no falle.
    if not os.path.exists(DB_PATH):
        print("INFO: La base de datos de urlwatch no se ha encontrado.")
        print("      (Esto es normal en la primera ejecución). Se omitirá el script.")
        # Salimos del script con código 0 para que la Action continúe y guarde la caché.
        sys.exit(0)

    conn = None
    try:
        # 2. Conectar a la base de datos SQLite.
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 3. Ejecutar una consulta para obtener el timestamp más reciente para cada URL.
        #    Agrupamos por 'url' y usamos MAX(timestamp) para encontrar el último registro.
        #    Ordenamos de forma descendente para tener los cambios más nuevos primero.
        query = """
            SELECT url, MAX(timestamp)
            FROM snapshots
            GROUP BY url
            ORDER BY MAX(timestamp) DESC;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return results

    except sqlite3.Error as e:
        print(f"ERROR: Ha ocurrido un error con la base de datos: {e}")
        sys.exit(1) # Salir con código de error para que la Action falle.

    finally:
        # 4. Asegurarse de cerrar la conexión.
        if conn:
            conn.close()

def write_report(results):
    """
    Formatea los resultados y los escribe en el archivo de salida.
    """
    # Asegurarse de que el directorio 'logs' exista.
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        if not results:
            f.write("No se ha encontrado historial de cambios en la base de datos.\n")
            return

        f.write("URLs ordenadas por su última fecha de cambio (más recientes primero):\n")
        f.write("====================================================================\n")
        for url, unix_timestamp in results:
            # Convertir el timestamp de Unix a un formato legible.
            change_date = datetime.fromtimestamp(unix_timestamp)
            formatted_date = change_date.strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{formatted_date} - {url}\n")

    print(f"Reporte guardado correctamente en '{OUTPUT_FILE}'.")

# --- Bloque principal de ejecución ---
if __name__ == "__main__":
    change_data = get_last_changes()
    if change_data is not None:
        write_report(change_data)
