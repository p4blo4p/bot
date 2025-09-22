#!/usr/bin/env python3
"""
Script para generar reportes detallados de URLWatch
Muestra información de fechas de último cambio y estado de URLs
"""

import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path

def get_urlwatch_db_path():
    """Obtiene la ruta de la base de datos de URLWatch"""
    home = Path.home()
    cache_dir = home / ".cache" / "urlwatch"
    db_path = cache_dir / "cache.db"
    
    if not db_path.exists():
        # Intentar otras ubicaciones posibles
        alt_paths = [
            home / ".config" / "urlwatch" / "cache.db",
            Path("./cache.db"),
            Path("./logs/cache.db")
        ]
        
        for alt_path in alt_paths:
            if alt_path.exists():
                return alt_path
        
        print(f"❌ No se encontró la base de datos de URLWatch")
        print(f"Rutas buscadas:")
        print(f"  - {db_path}")
        for alt_path in alt_paths:
            print(f"  - {alt_path}")
        return None
    
    return db_path

def format_timestamp(timestamp):
    """Convierte timestamp a fecha legible"""
    if timestamp:
        try:
            return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S")
        except:
            return "Fecha inválida"
    return "Sin datos"

def get_job_info():
    """Obtiene información básica de los trabajos desde el config"""
    jobs_info = {
        "cced95a59b1f3044d3f200a36c0312b3cf6a2ddf": {
            "name": "Oposiciones UCA - Informática",
            "url": "https://personal.uca.es/oposiciones-turno-libre/"
        },
        "ad2247145f4f85341613aacc6b70e02dcde0e89b": {
            "name": "Cursos INAP - Informática", 
            "url": "https://buscadorcursos.inap.es/#/?abierto=true&funcion=6"
        },
        "7e9a3d72638d85a09b09260a765d924d61007ffb": {
            "name": "Ayto Puerto Real - Tablón",
            "url": "https://puertoreal.sedelectronica.es/board"
        },
        "e7c4f5a11af0244bbee598b93b2c74c2e3356845": {
            "name": "Ayto Puerto Real - OPE",
            "url": "https://puertoreal.es/oferta-publica-de-empleo/"
        },
        "fa1ffa577b126907b0607c07979d579d95d74fcd": {
            "name": "BOE - Oposiciones Estado",
            "url": "https://www.boe.es/buscar/ult_dias.php?id=BOE-A&t=4"
        },
        "dab7d089c6aaa937b7ea6555e4171cfa30a208ec": {
            "name": "Junta de Andalucía - OPE", 
            "url": "https://www.juntadeandalucia.es/organismos/funcionpublica/areas/oposiciones.html"
        }
    }
    return jobs_info

def generate_detailed_report():
    """Genera un reporte detallado con fechas de cambio"""
    
    db_path = get_urlwatch_db_path()
    if not db_path:
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Obtener información de la base de datos
        cursor.execute("""
            SELECT guid, timestamp, tries, etag, 
                   CASE WHEN data IS NULL THEN 'ERROR' ELSE 'OK' END as status
            FROM CacheEntry 
            ORDER BY guid, timestamp DESC
        """)
        
        results = cursor.fetchall()
        jobs_info = get_job_info()
        
        print("=" * 80)
        print("📊 REPORTE DETALLADO DE URLWATCH")
        print(f"🕐 Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 80)
        print()
        
        # Agrupar resultados por GUID
        guid_data = {}
        for row in results:
            guid, timestamp, tries, etag, status = row
            if guid not in guid_data:
                guid_data[guid] = []
            guid_data[guid].append({
                'timestamp': timestamp,
                'tries': tries,
                'etag': etag,
                'status': status
            })
        
        # Generar reporte para cada job
        for guid, entries in guid_data.items():
            job_info = jobs_info.get(guid, {
                "name": f"Job desconocido ({guid[:8]}...)",
                "url": "URL desconocida"
            })
            
            print(f"🔍 {job_info['name']}")
            print(f"🌐 {job_info['url']}")
            
            if entries:
                latest = entries[0]
                print(f"📅 Última verificación: {format_timestamp(latest['timestamp'])}")
                print(f"✅ Estado: {latest['status']}")
                print(f"🔄 Intentos: {latest['tries']}")
                
                # Buscar el último cambio exitoso (cuando data no es NULL)
                last_successful = None
                for entry in entries:
                    if entry['status'] == 'OK':
                        last_successful = entry
                        break
                
                if last_successful:
                    print(f"📝 Último cambio exitoso: {format_timestamp(last_successful['timestamp'])}")
                else:
                    print("📝 Último cambio exitoso: Sin datos disponibles")
                    
                # Mostrar historial reciente
                if len(entries) > 1:
                    print("📊 Historial reciente:")
                    for i, entry in enumerate(entries[:5]):  # Mostrar últimas 5 entradas
                        status_icon = "✅" if entry['status'] == 'OK' else "❌"
                        print(f"   {i+1}. {format_timestamp(entry['timestamp'])} {status_icon} ({entry['tries']} intentos)")
            else:
                print("❌ Sin datos disponibles")
            
            print("-" * 60)
            print()
        
        conn.close()
        
        # Guardar reporte en archivo
        report_file = f"logs/detailed_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        os.makedirs("logs", exist_ok=True)
        
        print(f"💾 Reporte guardado en: {report_file}")
        
    except sqlite3.Error as e:
        print(f"❌ Error accediendo a la base de datos: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def show_cache_stats():
    """Muestra estadísticas de la cache"""
    db_path = get_urlwatch_db_path()
    if not db_path:
        return
        
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM CacheEntry")
        total_entries = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT guid) FROM CacheEntry")
        unique_jobs = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM CacheEntry")
        min_ts, max_ts = cursor.fetchone()
        
        print("📈 ESTADÍSTICAS DE CACHE")
        print(f"📝 Total de entradas: {total_entries}")
        print(f"🔗 Jobs únicos: {unique_jobs}")
        print(f"📅 Período: {format_timestamp(min_ts)} - {format_timestamp(max_ts)}")
        print()
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 URLWatch - Generador de Reportes Detallados")
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--stats":
        show_cache_stats()
    else:
        generate_detailed_report()
        show_cache_stats()
