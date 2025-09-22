#!/usr/bin/env python3
"""
URLWatch Hooks - Captura información adicional sobre cambios
Archivo: ~/.config/urlwatch/hooks.py
"""

import json
import os
from datetime import datetime
from pathlib import Path

def generate_guid(url):
    """Genera GUID consistente para una URL"""
    import hashlib
    return hashlib.sha1(url.encode()).hexdigest()

# Modificar la función record_change para usar GUIDs
def record_change(self, job_name, url, change_type, content_length=0):
    """Registra un cambio usando GUIDs consistentes"""
    timestamp = datetime.now().isoformat()
    guid = generate_guid(url)
    
    if guid not in self.history:
        self.history[guid] = {
            'name': job_name,
            'url': url,
            'first_seen': timestamp,
            'changes': []
        }
    
    change_record = {
        'timestamp': timestamp,
        'type': change_type,
        'content_length': content_length,
        'readable_date': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }
    
    self.history[guid]['changes'].append(change_record)
    self.history[guid]['last_change'] = timestamp
    self.history[guid]['last_change_readable'] = change_record['readable_date']
    
    # Mantener solo los últimos 50 cambios
    if len(self.history[guid]['changes']) > 50:
        self.history[guid]['changes'] = self.history[guid]['changes'][-50:]
    
    self.save_history()

class ChangeTracker:
    """Clase para rastrear cambios detallados"""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.changes_file = self.log_dir / "changes_history.json"
        self.load_history()
    
    def load_history(self):
        """Carga el historial de cambios"""
        try:
            if self.changes_file.exists():
                with open(self.changes_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            else:
                self.history = {}
        except:
            self.history = {}
    
    def save_history(self):
        """Guarda el historial de cambios"""
        try:
            with open(self.changes_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando historial: {e}")
    
    def record_change(self, job_name, url, change_type, content_length=0):
        """Registra un cambio"""
        timestamp = datetime.now().isoformat()
        
        if url not in self.history:
            self.history[url] = {
                'name': job_name,
                'first_seen': timestamp,
                'changes': []
            }
        
        change_record = {
            'timestamp': timestamp,
            'type': change_type,  # 'new', 'changed', 'error', 'unchanged'
            'content_length': content_length,
            'readable_date': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        
        self.history[url]['changes'].append(change_record)
        self.history[url]['last_change'] = timestamp
        self.history[url]['last_change_readable'] = change_record['readable_date']
        
        # Mantener solo los últimos 50 cambios por URL
        if len(self.history[url]['changes']) > 50:
            self.history[url]['changes'] = self.history[url]['changes'][-50:]
        
        self.save_history()

# Instancia global del tracker
change_tracker = ChangeTracker()

# Hooks de URLWatch
def filter_result(url, job, result):
    """
    Hook llamado después de aplicar filtros
    Registra información sobre el contenido procesado
    """
    try:
        job_name = getattr(job, 'name', 'Unnamed Job')
        content_length = len(result) if result else 0
        
        # Este hook se llama siempre, registramos como 'processed'
        change_tracker.record_change(
            job_name, 
            url, 
            'processed', 
            content_length
        )
        
        return result
        
    except Exception as e:
        print(f"Error en filter_result hook: {e}")
        return result

def job_list_finished(jobs):
    """
    Hook llamado cuando terminan todos los jobs
    Genera un resumen de la ejecución
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = change_tracker.log_dir / f"execution_summary_{timestamp}.json"
        
        execution_summary = {
            'timestamp': datetime.now().isoformat(),
            'readable_date': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'total_jobs': len(jobs),
            'jobs_summary': []
        }
        
        for job in jobs:
            job_summary = {
                'name': getattr(job, 'name', 'Unnamed'),
                'url': getattr(job, 'url', 'Unknown URL'),
                'timeout': getattr(job, 'timeout', 30),
                'filters': str(getattr(job, 'filter', [])),
            }
            execution_summary['jobs_summary'].append(job_summary)
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(execution_summary, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"Error en job_list_finished hook: {e}")

def report_finished(reports):
    """
    Hook llamado después de generar reportes
    Actualiza estadísticas finales y genera reporte mejorado
    """
    try:
        # Generar reporte de estado actual
        status_file = change_tracker.log_dir / "current_status.json"
        current_status = {
            'last_execution': datetime.now().isoformat(),
            'last_execution_readable': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'monitored_sites': {}
        }
        
        for url, data in change_tracker.history.items():
            # Obtener información detallada de cambios
            changes = data.get('changes', [])
            last_change = data.get('last_change_readable', 'Sin cambios registrados')
            
            # Encontrar la última vez que no hubo cambios (estado 'unchanged')
            last_unchanged = 'No disponible'
            for change in reversed(changes):
                if change.get('type') == 'unchanged':
                    last_unchanged = change.get('readable_date', 'Fecha no disponible')
                    break
            
            # Si no hay 'unchanged', buscar el último 'processed' exitoso
            if last_unchanged == 'No disponible':
                for change in reversed(changes):
                    if change.get('type') in ['processed', 'new'] and change.get('content_length', 0) > 0:
                        last_unchanged = change.get('readable_date', 'Fecha no disponible')
                        break
            
            current_status['monitored_sites'][url] = {
                'name': data['name'],
                'first_seen': data.get('first_seen'),
                'last_change': last_change,
                'last_unchanged': last_unchanged,
                'total_changes': len(changes),
                'recent_activity': changes[-3:] if changes else []
            }
        
        # Guardar estado actual en JSON
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(current_status, f, indent=2, ensure_ascii=False)
        
        # Generar resumen legible en formato Markdown
        readable_status = change_tracker.log_dir / "status_summary.md"
        with open(readable_status, 'w', encoding='utf-8') as f:
            # Encabezado del reporte
            f.write("# 📊 URLWatch Monitoring Summary\n\n")
            f.write(f"**Generated:** {current_status['last_execution_readable']}\n")
            f.write("**Status:** ✅ Monitoring completed successfully\n\n")
            
            # Sección de actividad reciente
            f.write("## Recent Activity\n\n")
            f.write("### Latest Execution Log\n")
            f.write(f"`urlwatch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt`\n\n")
            
            # Sección de sitios monitoreados
            f.write("## Monitored Sites\n\n")
            f.write("### Detailed Status\n")
            f.write("```\n")
            
            # Generar entrada para cada sitio
            for url, site_data in current_status['monitored_sites'].items():
                f.write(f"================================================================================\n")
                f.write(f"🔍 {site_data['name']}\n")
                f.write(f"🌐 [{url}]({url})\n")
                f.write(f"📅 Última verificación: {current_status['last_execution_readable']}\n")
                f.write(f"✅ Estado: ✅ OK\n")
                f.write(f"📏 Último cambio: {site_data['last_change']}\n")
                f.write(f"🔄 Última verificación sin cambios: {site_data['last_unchanged']}\n")
                f.write(f"📊 Total cambios registrados: {site_data['total_changes']}\n")
                f.write("------------------------------------------------------------\n\n")
            
            f.write("```\n")
            
            # Generar versión más legible sin formato de código
            f.write("\n## 📋 Detailed Status (Readable Format)\n\n")
            
            for url, site_data in current_status['monitored_sites'].items():
                f.write(f"### 🔍 {site_data['name']}\n\n")
                f.write(f"- **URL:** [{url}]({url})\n")
                f.write(f"- **Última verificación:** {current_status['last_execution_readable']}\n")
                f.write(f"- **Estado:** ✅ OK\n")
                f.write(f"- **Último cambio:** {site_data['last_change']}\n")
                f.write(f"- **Última verificación sin cambios:** {site_data['last_unchanged']}\n")
                f.write(f"- **Total cambios registrados:** {site_data['total_changes']}\n\n")
                
                # Mostrar actividad reciente si existe
                if site_data['recent_activity']:
                    f.write("**Actividad reciente:**\n")
                    for activity in site_data['recent_activity']:
                        activity_type = activity.get('type', 'unknown')
                        icon = {'new': '🆕', 'changed': '🔄', 'error': '❌', 'processed': '⚙️', 'unchanged': '✅'}.get(activity_type, '❓')
                        f.write(f"  - {icon} {activity.get('readable_date', 'Fecha no disponible')} ({activity_type})\n")
                    f.write("\n")
                
                f.write("---\n\n")
        
        print(f"✅ Reporte generado: {readable_status}")
        
    except Exception as e:
        print(f"❌ Error en report_finished hook: {e}")

# Funciones de utilidad para debugging
def debug_job_info(job):
    """Función auxiliar para debugging de jobs"""
    print(f"DEBUG Job: {getattr(job, 'name', 'No name')}")
    print(f"DEBUG URL: {getattr(job, 'url', 'No URL')}")
    print(f"DEBUG Filters: {getattr(job, 'filter', 'No filters')}")

# Hook opcional para errores
def job_failed(job, exception):
    """
    Hook llamado cuando un job falla
    Registra el error para análisis
    """
    try:
        job_name = getattr(job, 'name', 'Unnamed Job')
        job_url = getattr(job, 'url', 'Unknown URL')
        
        change_tracker.record_change(
            job_name,
            job_url, 
            f'error: {str(exception)[:100]}',
            0
        )
        
        # Log del error
        error_log = change_tracker.log_dir / "errors.log"
        with open(error_log, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()} - {job_name} ({job_url}): {exception}\n")
            
    except Exception as e:
        print(f"Error en job_failed hook: {e}")
