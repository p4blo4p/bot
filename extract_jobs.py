#!/usr/bin/env python3
"""
Script para extraer jobs de urls2watch.yaml
"""
import yaml
import sys

def extract_jobs():
    try:
        with open('urls2watch.yaml', 'r') as f:
            data = yaml.safe_load(f)
        
        # Extraer solo los jobs si existen
        jobs = data.get('jobs', [])
        
        if jobs:
            with open('.urlwatch/urls.yaml', 'w') as f:
                for i, job in enumerate(jobs):
                    # Escribir cada job como documento YAML separado
                    yaml.dump(job, f, default_flow_style=False, allow_unicode=True)
                    if i < len(jobs) - 1:
                        f.write('---\n')
            print(f"✅ Extraídos {len(jobs)} jobs al archivo .urlwatch/urls.yaml")
        else:
            print("⚠️ No se encontraron jobs en urls2watch.yaml")
            
    except Exception as e:
        print(f"❌ Error extrayendo jobs: {e}")
        sys.exit(1)

if __name__ == "__main__":
    extract_jobs()
