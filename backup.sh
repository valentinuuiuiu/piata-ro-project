#!/bin/bash
# Production backup script for Piața.ro

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Load environment variables
if [ -f .env.prod ]; then
    export $(grep -v '^#' .env.prod | xargs)
fi

create_backup_dir() {
    log_info "Creating backup directory..."
    mkdir -p "$BACKUP_DIR"
}

backup_database() {
    local backup_file="$BACKUP_DIR/database_$TIMESTAMP.sql"
    
    log_info "Backing up database..."
    
    if docker compose -f docker-compose.yml exec -T db \
        pg_dump -U piata_user piata_ro > "$backup_file"; then
        
        # Compress the backup
        gzip "$backup_file"
        log_success "Database backup created: ${backup_file}.gz"
        
        # Verify backup
        if gzip -t "${backup_file}.gz"; then
            log_success "Backup verification passed"
        else
            log_error "Backup verification failed"
            return 1
        fi
        
    else
        log_error "Database backup failed"
        return 1
    fi
}

backup_media() {
    local backup_file="$BACKUP_DIR/media_$TIMESTAMP.tar.gz"
    
    log_info "Backing up media files..."
    
    if [ -d "media" ] && [ "$(ls -A media 2>/dev/null)" ]; then
        tar -czf "$backup_file" media/
        log_success "Media backup created: $backup_file"
    else
        log_warning "No media files to backup"
    fi
}

backup_logs() {
    local backup_file="$BACKUP_DIR/logs_$TIMESTAMP.tar.gz"
    
    log_info "Backing up logs..."
    
    if [ -d "logs" ] && [ "$(ls -A logs 2>/dev/null)" ]; then
        tar -czf "$backup_file" logs/
        log_success "Logs backup created: $backup_file"
    else
        log_warning "No logs to backup"
    fi
}

cleanup_old_backups() {
    log_info "Cleaning up backups older than $RETENTION_DAYS days..."
    
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
    
    log_success "Old backups cleanup completed"
}

create_backup_report() {
    local report_file="$BACKUP_DIR/backup_report_$TIMESTAMP.txt"
    
    cat > "$report_file" << EOF
Piața.ro Backup Report
=====================
Timestamp: $(date)
Backup Type: Full

Backup Files:
$(find "$BACKUP_DIR" -name "*_$TIMESTAMP.*" -printf "%f\n")

Storage Usage:
$(du -h "$BACKUP_DIR"/*_$TIMESTAMP.*)

Total Backup Size:
$(du -sh "$BACKUP_DIR" | cut -f1)

Retention Policy: $RETENTION_DAYS days
EOF
    
    log_success "Backup report created: $report_file"
}

notify_backup_status() {
    local status=$1
    local message=$2
    
    # This function can be extended to send notifications
    # via email, Slack, Discord, etc.
    
    if [ "$status" = "success" ]; then
        log_success "Backup completed successfully"
        echo "$message"
    else
        log_error "Backup failed"
        echo "$message"
        # Exit with error code
        exit 1
    fi
}

main() {
    log_info "🚀 Starting Piața.ro production backup..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Check if services are running
    if ! docker compose -f docker-compose.yml ps | grep -q "Up"; then
        log_warning "Some services are not running. Backup may be incomplete."
    fi
    
    create_backup_dir
    
    # Perform backups
    if ! backup_database; then
        notify_backup_status "error" "Database backup failed"
        return 1
    fi
    
    backup_media
    backup_logs
    cleanup_old_backups
    create_backup_report
    
    # Summary
    local total_size=$(du -sh "$BACKUP_DIR" | cut -f1)
    local backup_count=$(find "$BACKUP_DIR" -name "*_$TIMESTAMP.*" | wc -l)
    
    notify_backup_status "success" "Backup completed: $backup_count files, total size $total_size"
}

# Handle signals
trap 'log_error "Backup interrupted by user"; exit 1' INT TERM

# Run main function
if main; then
    log_success "🎉 Backup completed successfully!"
    echo ""
    echo "📊 Backup location: $BACKUP_DIR"
    echo "📦 Total size: $(du -sh "$BACKUP_DIR" | cut -f1)"
    echo "🕒 Retention: $RETENTION_DAYS days"
    echo ""
else
    log_error "Backup failed"
    exit 1
fi
