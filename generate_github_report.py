#!/usr/bin/env python3
"""
Generador de reportes detallados para GitHub Actions
Analiza logs de URLWatch y genera reportes con fechas de último cambio
"""

import json
import re
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import glob

class GitHubReportGenerator:
    def __init__(self):
        self.logs_dir = Path("logs")
        self.cache_file = Path(".urlwatch/cache.db")
        
        # Mapeo de URLs a nombres legibles
        self.url_mapping = {
            "personal.uca.es/oposiciones-turno-libre/": "Oposiciones UCA - Informática",
            "buscadorcursos.inap.es": "Cursos INAP - Informática", 
            "puertoreal.sedelectronica.es/board": "Ayto Puerto Real - Tablón",
            "puertoreal.es/oferta-publica-de-empleo/": "Ayto Puerto Real - OPE",
            "www.boe.es/buscar/": "BOE - Búsqueda Oposiciones",
            "www.juntadeandalucia.es/organismos/funcionpublica/": "Junta de Andalucía - Función Pública"
        }
        
    def analyze_recent_logs(self):
        """Analiza los logs más recientes para extraer información"""
        log_files = sorted(glob.glob("logs/urlwatch_*.txt"), reverse=True)
        
        sites_status = {}
        
        for log_file in log_files[:5]:  # Analizar últimos 5 logs
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extraer timestamp del archivo
                timestamp_match = re.search(r'urlwatch_(\d{8}_\d{6})\.txt', log_file)
                if timestamp_match:
                    file_timestamp = datetime.strptime(timestamp_match.group(1), "%Y%m%d_%H%M%S")
                else:
                    file_timestamp = datetime.fromtimestamp(os.path.getmtime(log_file))
                
                # Buscar información de procesamiento de cada URL
                processing_lines = re.findall(r'handler INFO: Processing: <url url=\'([^\']+)\'[^>]*name=\'([^\']+)\'', content)
                
                for url, name in processing_lines:
                    # Verificar si hubo éxito (no hay ERROR posterior)
                    error_pattern = f"ERROR:.*{re.escape(name)}"
                    has_error = bool(re.search(error_pattern, content))
                    
                    if url not in sites_status:
                        sites_status[url] = {
                            'name': name,
                            'last_successful_check': None,
                            'last_error': None,
                            'total_checks': 0,
                            'error_count': 0,
                            'recent_status': []
                        }
                    
                    sites_status[url]['total_checks'] += 1
                    
                    if has_error:
                        sites_status[url]['error_count'] += 1
                        sites_status[url]['last_error'] = file_timestamp
                        sites_status[url]['recent_status'].append({
                            'timestamp': file_timestamp,
                            'status': 'ERROR'
                        })
                    else:
                        sites_status[url]['last_successful_check'] = file_timestamp
                        sites_status[url]['recent_status'].append({
                            'timestamp': file_timestamp,
                            'status': 'OK'
                        })
                
            except Exception as e:
                print(f"Error analizando {log_file}: {e}")
        
        return sites_status
    
    def analyze_cache_database(self):
        """Analiza la base de datos de cache para obtener información detallada"""
        if not self.cache_file.exists():
            return {}
            
        cache_info = {}
        
        try:
            conn = sqlite3.connect(str(self.cache_file))
            cursor = conn.cursor()
            
            # Obtener información de todas las entradas
            cursor.execute("""
                SELECT guid, timestamp, tries, etag,
                       CASE WHEN data IS NULL THEN 0 ELSE 1 END as has_data,
                       length(data) as data_length
                FROM CacheEntry
                ORDER BY guid, timestamp DESC
            """)
            
            results = cursor.fetchall()
            
            # Agrupar por GUID
            guid_data = {}
            for row in results:
                guid, timestamp, tries, etag, has_data, data_length = row
                
                if guid not in guid_data:
                    guid_data[guid] = []
                
                guid_data[guid].append({
                    'timestamp': timestamp,
                    'tries': tries,
                    'has_data': bool(has_data),
                    'data_length': data_length or 0,
                    'datetime': datetime.fromtimestamp(timestamp) if timestamp else None
                })
            
            # Procesar cada GUID
            for guid, entries in guid_data.items():
                # Ordenar por timestamp descendente
                entries.sort(key=lambda x: x['timestamp'] or 0, reverse=True)
                
                latest = entries[0] if entries else {}
                
                # Buscar última entrada exitosa
                last_successful = None
                for entry in entries:
                    if entry['has_data']:
                        last_successful = entry
                        break
                
                cache_info[guid] = {
                    'latest_check': latest.get('datetime'),
                    'latest_status': 'OK' if latest.get('has_data') else 'ERROR',
                    'latest_tries': latest.get('tries', 0),
                    'last_successful_check': last_successful.get('datetime') if last_successful else None,
                    'total_entries': len(entries),
                    'data_size': latest.get('data_length', 0)
                }
            
            conn.close()
            
        except Exception as e:
            print(f"Error analizando cache: {e}")
            
        return cache_info
    
    def generate_detailed_report(self):
        """Genera el reporte detallado combinando logs y cache"""
        print("🔍 Generando reporte detallado...")
        
        # Analizar logs y cache
        sites_from_logs = self.analyze_recent_logs()
        cache_info = self.analyze_cache_database()
        
        # Combinar información
        final_report = {}
        
        for url, log_data in sites_from_logs.items():
            # Buscar GUID correspondiente en cache (aproximación)
            matching_cache = None
            for guid, cache_data in cache_info.items():
                # Esta es una aproximación - en un sistema real tendríamos mejor mapeo
                if len(cache_info) <= len(sites_from_logs):
                    matching_cache = cache_data
                    break
            
            final_report[url] = {
                'name': log_data['name'],
                'url': url,
                'last_successful_check': log_data['last_successful_check'],
                'last_error': log_data.get('last_error'),
                'total_checks': log_data['total_checks'],
                'error_count': log_data['error_count'],
                'current_status': 'OK' if log_data['last_successful_check'] else 'ERROR',
                'cache_info': matching_cache
            }
        
        return final_report
    
    def format_datetime(self, dt):
        """Formatea datetime para mostrar"""
        if dt:
            return dt.strftime("%d/%m/%Y %H:%M:%S")
        return "Sin datos"
    
    def generate_summary_report(self, detailed_data):
        """Genera resumen en formato texto"""
        os.makedirs("logs", exist_ok=True)
        
        # Reporte detallado
        with open("logs/detailed_status_report.txt", 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("🔍 REPORTE DETALLADO DE MONITOREO URLWatch\n")
            f.write(f"📅 Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            for url, data in detailed_data.items():
                f.write(f"📊 {data['name']}\n")
                f.write(f"🌐 {data['url']}\n")
                f.write(f"📅 Último cambio exitoso: {self.format_datetime(data['last_successful_check'])}\n")
                f.write(f"✅ Estado actual: {data['current_status']}\n")
                f.write(f"🔢 Total verificaciones: {data['total_checks']}\n")
                f.write(f"❌ Errores: {data['error_count']}\n")
                
                if data.get('last_error'):
                    f.write(f"⚠️ Último error: {self.format_datetime(data['last_error'])}\n")
                
                if data.get('cache_info'):
                    cache = data['cache_info']
                    f.write(f"💾 Última verificación: {self.format_datetime(cache.get('latest_check'))}\n")
                    f.write(f"📏 Tamaño datos: {cache.get('data_size', 0)} bytes\n")
                
                f.write("-" * 60 + "\n\n")
        
        # Reporte JSON para procesamiento automático
        report_json = {
            'generated_at': datetime.now().isoformat(),
            'generated_readable': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'summary': {
                'total_sites': len(detailed_data),
                'sites_ok': sum(1 for d in detailed_data.values() if d['current_status'] == 'OK'),
                'sites_error': sum(1 for d in detailed_data.values() if d['current_status'] == 'ERROR')
            },
            'sites': {}
        }
        
        for url, data in detailed_data.items():
            report_json['sites'][url] = {
                'name': data['name'],
                'last_change': data['last_successful_check'].isoformat() if data['last_successful_check'] else None,
                'last_change_readable': self.format_datetime(data['last_successful_check']),
                'status': data['current_status'],
                'total_checks': data['total_checks'],
                'error_count': data['error_count']
            }
        
        with open("logs/status_report.json", 'w', encoding='utf-8') as f:
            json.dump(report_json, f, indent=2, ensure_ascii=False)
        
        return report_json
    
    def generate_markdown_summary(self, report_data):
        """Genera resumen en formato Markdown para GitHub"""
        
        summary_content = f"""# URLWatch Monitoring Summary

**Generated:** {report_data['generated_readable']}
**Status:** ✅ Monitoring completed successfully

## 📊 Overview
- **Total sites monitored:** {report_data['summary']['total_sites']}
- **Sites OK:** {report_data['summary']['sites_ok']} ✅
- **Sites with errors:** {report_data['summary']['sites_error']} ❌

## 🔍 Sites Status

"""
        
        for url, site_data in report_data['sites'].items():
            status_icon = "✅" if site_data['status'] == 'OK' else "❌"
            
            summary_content += f"""### {status_icon} {site_data['name']}
- **URL:** `{url}`
- **Último cambio:** {site_data['last_change_readable']}
- **Estado:** {site_data['status']}
- **Total verificaciones:** {site_data['total_checks']}

"""
        
        summary_content += f"""
## 📝 Latest Activity

Latest execution log: `{self.get_latest_log_filename()}`

---
*Generated by URLWatch automation*
"""
        
        with open("logs/summary.md", 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        return summary_content
    
    def get_latest_log_filename(self):
        """Obtiene el nombre del último archivo de log"""
        log_files = glob.glob("logs/urlwatch_*.txt")
        if log_files:
            return os.path.basename(sorted(log_files)[-1])
        return "No log files found"
    
    def run(self):
        """Ejecuta la generación completa de reportes"""
        try:
            # Generar datos detallados
            detailed_data = self.generate_detailed_report()
            
            if not detailed_data:
                print("⚠️ No se encontraron datos para procesar")
                return
            
            # Generar reportes
            report_json = self.generate_summary_report(detailed_data)
            markdown_summary = self.generate_markdown_summary(report_json)
            
            print("✅ Reportes generados exitosamente:")
            print("   - logs/detailed_status_report.txt")
            print("   - logs/status_report.json")
            print("   - logs/summary.md")
            
            # Mostrar resumen en consola
            print("\n" + "="*50)
            print("📋 RESUMEN EJECUTIVO")
            print("="*50)
            
            for url, data in detailed_data.items():
                status_icon = "✅" if data['current_status'] == 'OK' else "❌"
                print(f"{status_icon} {data['name']}")
                print(f"   📅 Último cambio: {self.format_datetime(data['last_successful_check'])}")
                print()
            
        except Exception as e:
            print(f"❌ Error generando reportes: {e}")
            raise

if __name__ == "__main__":
    generator = GitHubReportGenerator()
    generator.run()
