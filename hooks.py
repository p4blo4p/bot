#!/usr/bin/env python3
"""
URLWatch Hooks - Captura información adicional sobre cambios
Archivo: ~/.config/urlwatch/hooks.py
"""

import json
import os
from datetime import datetime
from pathlib import Path

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
    Actualiza estadísticas finales
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
            current_status['monitored_sites'][url] = {
                'name': data['name'],
                'first_seen': data.get('first_seen'),
                'last_change': data.get('last_change_readable', 'Sin cambios registrados'),
                'total_changes': len(data.get('changes', [])),
                'recent_activity': data.get('changes', [])[-3:]  # Últimas 3 actividades
            }
        
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(current_status, f, indent=2, ensure_ascii=False)
            
        # Generar resumen legible
        readable_status = change_tracker.log_dir / "readable_status.txt"
        with open(readable_status, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("📊 ESTADO ACTUAL DE MONITOREO URLWatch\n") 
            f.write(f"🕐 Última ejecución: {current_status['last_execution_readable']}\n")
            f.write("=" * 60 + "\n\n")
            
            for url, site_data in current_status['monitored_sites'].items():
                f.write(f"🔍 {site_data['name']}\n")
                f.write(f"🌐 {url}\n")
                f.write(f"📅 Último cambio: {site_data['last_change']}\n")
                f.write(f"📊 Total cambios registrados: {site_data['total_changes']}\n")
                f.write("-" * 40 + "\n\n")
                
    except Exception as e:
        print(f"Error en report_finished hook: {e}")

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
