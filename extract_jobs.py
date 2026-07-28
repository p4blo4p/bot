import yaml
import os

def extract_jobs():
    """
    Lee urls2watch.yaml y genera los archivos .urlwatch/urls.yaml y .urlwatch/config.yaml
    compatibles con la ejecucion de urlwatch.
    """
    os.makedirs('.urlwatch', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    if not os.path.exists('urls2watch.yaml'):
        print("⚠️ No se encontró urls2watch.yaml")
        return

    with open('urls2watch.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        print("⚠️ Formato invalido en urls2watch.yaml")
        return

    jobs = data.get('jobs', [])

    # Guardar urls.yaml para urlwatch
    with open('.urlwatch/urls.yaml', 'w', encoding='utf-8') as f:
        yaml.dump_all(jobs, f, default_flow_style=False, allow_unicode=True)

    # Guardar config.yaml para urlwatch
    config = {
        'display': data.get('display', {'new': True, 'error': True}),
        'report': data.get('report', {'text': {'line_length': 120, 'details': True}}),
        'storage': data.get('storage', {'minidb': {'filename': '.urlwatch/cache.db'}}),
        'reporters': [{'text': {'filename': 'logs/detailed_report.txt', 'details': True}}]
    }

    with open('.urlwatch/config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False)

    print(f"✅ Extraidos {len(jobs)} trabajos a .urlwatch/urls.yaml")

if __name__ == '__main__':
    extract_jobs()
