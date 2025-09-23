#!/usr/bin/env python3
"""
Script para analizar cambios y generar reportes detallados
"""
import sqlite3
import json
import os
import yaml
from datetime import datetime
from pathlib import Path

def analyze_cache_changes():
    """Analiza la cache y genera reporte de cambios"""
    
    cache_file = Path(".urlwatch/cache.db")
    if not cache_file.exists():
        print("❌ No se encontró archivo de cache")
        return
    
    # Cargar URLs desde el archivo de configuración
    urls_config = {}
    try:
        with open(".urlwatch/urls.yaml", 'r') as f:
            # Cargar múltiples documentos YAML
            urls_data = list(yaml.safe_load_all(f))
            for job in urls_data:
                if isinstance(job, dict) and 'name' in job and 'url' in job:
                    urls_config[job['url']] = job['name']
    except Exception as e:
        print(f"⚠️ Error cargando configuración de URLs: {e}")
    
    try:
        conn = sqlite3.connect(str(cache_file))
        cursor = conn.cursor()
        
        # Obtener todas las entradas ordenadas por timestamp
        cursor.execute("""
            SELECT guid, timestamp, tries, etag, 
                   CASE WHEN data IS NULL THEN 0 ELSE 1 END as has_data,
                   length(data) as data_length
            FROM CacheEntry 
            ORDER BY timestamp DESC
        """)
        
        results = cursor.fetchall()
        current_time = datetime.now()
        
        # Procesar resultados
        sites_info = {}
        for row in results:
            guid, timestamp, tries, etag, has_data, data_length = row
            
            if guid not in sites_info:
                sites_info[guid] = {
                    'latest_timestamp': timestamp,
                    'latest_tries': tries,
                    'has_data': has_data,
                    'data_length': data_length or 0,
                    'entries_count': 0
                }
            
            sites_info[guid]['entries_count'] += 1
        
        # Generar reporte detallado
        report_data = {
            'generated_at': current_time.isoformat(),
            'generated_readable': current_time.strftime("%d/%m/%Y %H:%M:%S"),
            'sites': {}
        }
        
        # Por cada GUID, intentar encontrar la URL correspondiente
        cursor.execute("SELECT DISTINCT guid FROM CacheEntry")
        guids = cursor.fetchall()
        
        for (guid,) in guids:
            site_info = sites_info.get(guid, {})
            
            # Buscar en el historial para obtener URL
            cursor.execute("SELECT url FROM CacheEntry WHERE guid = ? LIMIT 1", (guid,))
            url_result = cursor.fetchone()
            
            if url_result and url_result[0]:
                url = url_result[0]
                site_name = urls_config.get(url, url)
            else:
                site_name = "Sitio desconocido"
                url = f"guid:{guid}"
            
            formatted_date = "Sin datos"
            if site_info.get('latest_timestamp'):
                try:
                    formatted_date = datetime.fromtimestamp(
                        site_info['latest_timestamp']
                    ).strftime("%d/%m/%Y %H:%M:%S")
                except:
                    pass
            
            status = "✅ OK" if site_info.get('has_data') else "❌ ERROR" 
            if site_info.get('latest_tries', 0) > 1:
                status += f" ({site_info['latest_tries']} intentos)"
            
            report_data['sites'][guid] = {
                'name': site_name,
                'url': url,
                'last_check': formatted_date,
                'status': status,
                'data_size': site_info.get('data_size', 0),
                'total_checks': site_info.get('entries_count', 0)
            }
        
        # Guardar reporte
        os.makedirs("logs", exist_ok=True)
        with open("logs/change_history.json", 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Generar reporte legible
        with open("logs/sites_status.txt", 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("🔍 ESTADO DETALLADO DE MONITOREO URLWatch\n")
            f.write(f"📅 Generado: {report_data['generated_readable']}\n") 
            f.write("=" * 80 + "\n\n")
            
            for guid, site in report_data['sites'].items():
                f.write(f"📊 {site['name']}\n")
                f.write(f"🌐 {site['url']}\n")
                f.write(f"📅 Última verificación: {site['last_check']}\n")
                f.write(f"✅ Estado: {site['status']}\n")
                f.write(f"📏 Tamaño datos: {site['data_size']} bytes\n")
                f.write(f"🔢 Total verificaciones: {site['total_checks']}\n")
                f.write("-" * 60 + "\n\n")
        
        print("✅ Análisis de cambios completado")
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analizando cache: {e}")

if __name__ == "__main__":
    analyze_cache_changes()
