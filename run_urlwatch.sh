#!/bin/bash

# URLWatch Automation Script
# Script para ejecutar URLWatch y generar reportes detallados

set -e

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
CONFIG_DIR="$HOME/.config/urlwatch"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Funciones de logging
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Crear directorios necesarios
setup_directories() {
    log_info "Configurando directorios..."
    mkdir -p "$LOG_DIR"
    mkdir -p "$CONFIG_DIR"
    log_success "Directorios configurados"
}

# Verificar instalación de URLWatch
check_urlwatch() {
    log_info "Verificando instalación de URLWatch..."
    
    if ! command -v urlwatch &> /dev/null; then
        log_error "URLWatch no está instalado"
        log_info "Instalando URLWatch..."
        
        if command -v pip3 &> /dev/null; then
            pip3 install urlwatch
        elif command -v pip &> /dev/null; then
            pip install urlwatch
        else
            log_error "No se encontró pip. Por favor, instala URLWatch manualmente"
            exit 1
        fi
    fi
    
    log_success "URLWatch está disponible"
    urlwatch --version
}

# Configurar URLWatch si es necesario
setup_urlwatch() {
    log_info "Configurando URLWatch..."
    
    # Si no existe la configuración, crear una básica
    if [ ! -f "$CONFIG_DIR/urlwatch.yaml" ]; then
        log_warning "No se encontró configuración de URLWatch"
        log_info "Creando configuración básica..."
        
        # Aquí copiarías la configuración desde el artifact anterior
        # Por ahora solo informamos al usuario
        log_warning "Por favor, copia el archivo urlwatch.yaml al directorio $CONFIG_DIR"
    else
        log_success "Configuración encontrada"
    fi
    
    # Verificar archivo de URLs
    if [ ! -f "$CONFIG_DIR/urls.yaml" ] && [ ! -f "urls2watch.yaml" ]; then
        log_warning "No se encontró archivo de URLs"
        log_info "Asegúrate de tener urls2watch.yaml o $CONFIG_DIR/urls.yaml"
    fi
}

# Ejecutar URLWatch
run_urlwatch() {
    log_info "Ejecutando URLWatch..."
    
    local output_file="$LOG_DIR/urlwatch_${TIMESTAMP}.txt"
    local error_file="$LOG_DIR/urlwatch_errors_${TIMESTAMP}.txt"
    
    # Ejecutar URLWatch con logging detallado
    if urlwatch --verbose 2>&1 | tee "$output_file"; then
        log_success "URLWatch ejecutado exitosamente"
        
        # Verificar si hay errores en la salida
        if grep -q "ERROR:" "$output_file"; then
            log_warning "Se detectaron algunos errores durante la ejecución"
            grep "ERROR:" "$output_file" > "$error_file"
        fi
    else
        log_error "URLWatch falló durante la ejecución"
        return 1
    fi
    
    echo "$output_file"
}

# Generar reporte detallado
generate_detailed_report() {
    log_info "Generando reporte detallado..."
    
    if [ -f "generate_detailed_report.py" ]; then
        python3 generate_detailed_report.py
        log_success "Reporte detallado generado"
    else
        log_warning "Script de reporte detallado no encontrado"
    fi
}

# Generar resumen
generate_summary() {
    local output_file="$1"
    local summary_file="$LOG_DIR/summary.md"
    
    log_info "Generando resumen..."
    
    cat > "$summary_file" << EOF
# URLWatch Monitoring Summary

**Generated:** $(date)
**Status:** Monitoring completed

## Recent Activity

### Latest Execution Log
\`\`\`
$(basename "$output_file")
\`\`\`

### Summary
$(if grep -q "ERROR:" "$output_file"; then echo "⚠️ **Warnings/Errors detected**"; else echo "✅ **All monitored sites processed successfully**"; fi)

### Monitored Sites Status
EOF

    # Agregar información de cada sitio si está disponible
    if [ -f "$LOG_DIR/current_status.json" ]; then
        echo "Información detallada disponible en current_status.json" >> "$summary_file"
    fi
    
    log_success "Resumen generado: $summary_file"
}

# Limpiar archivos antiguos
cleanup_old_files() {
    log_info "Limpiando archivos antiguos (>30 días)..."
    
    find "$LOG_DIR" -name "urlwatch_*.txt" -mtime +30 -delete 2>/dev/null || true
    find "$LOG_DIR" -name "detailed_report_*.txt" -mtime +30 -delete 2>/dev/null || true
    find "$LOG_DIR" -name "execution_summary_*.json" -mtime +30 -delete 2>/dev/null || true
    
    log_success "Limpieza completada"
}

# Mostrar estadísticas
show_stats() {
    log_info "Estadísticas de monitoreo:"
    
    if [ -f "$LOG_DIR/current_status.json" ]; then
        local total_sites=$(cat "$LOG_DIR/current_status.json" | jq -r '.monitored_sites | keys | length' 2>/dev/null || echo "N/A")
        local last_execution=$(cat "$LOG_DIR/current_status.json" | jq -r '.last_execution_readable' 2>/dev/null || echo "N/A")
        
        echo -e "${CYAN}📊 Sitios monitoreados: $total_sites${NC}"
        echo -e "${CYAN}🕐 Última ejecución: $last_execution${NC}"
    fi
    
    # Contar archivos de log
    local log_count=$(find "$LOG_DIR" -name "urlwatch_*.txt" | wc -l)
    echo -e "${CYAN}📝 Total de ejecuciones registradas: $log_count${NC}"
}

# Función principal
main() {
    echo -e "${PURPLE}🔍 URLWatch Automation Script${NC}"
    echo -e "${PURPLE}================================${NC}"
    echo
    
    # Verificar argumentos
    case "${1:-}" in
        "--stats")
            show_stats
            exit 0
            ;;
        "--setup-only")
            setup_directories
            check_urlwatch
            setup_urlwatch
            log_success "Configuración completada"
            exit 0
            ;;
        "--cleanup")
            cleanup_old_files
            exit 0
            ;;
        "--help")
            echo "Uso: $0 [--stats|--setup-only|--cleanup|--help]"
            echo "  --stats      Mostrar estadísticas ún
