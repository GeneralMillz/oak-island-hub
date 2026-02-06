#!/bin/bash
# ============================================================================
# run_semantic_pipeline.sh
# ============================================================================
# Semantic ETL Pipeline Orchestrator
#
# Runs all phases of semantic database construction:
#   Phase 1: Ingest raw data from JSON/JSONL sources
#   Phase 2: Deduplicate people and theories
#   Phase 3: Normalize relationships and resolve FKs
#   Phase 4: Verify data quality and integrity
#   Phase 5: Export optimized views for frontend
#
# Usage:
#   bash run_semantic_pipeline.sh [options]
#
# Options:
#   --db DATABASE_PATH          Database file path (default: oak_island_hub.db)
#   --source-dir DIR            Frontend data directory
#   --extracted-dir DIR         Extracted facts directory
#   --output-dir DIR            Output directory for exports
#   --drop-existing             Drop and rebuild database
#   --skip-phase N              Skip a specific phase
#   --only-phase N              Only run a specific phase
#   --verbose                   Verbose output
#   --dry-run                   Show what would be done (no changes)
#
# Environment:
#   PYTHON                      Python 3 binary (default: python3)
#
# Example:
#   cd /path/to/oak-island-hub/semantic_sqlite_pipeline
#   bash run_semantic_pipeline.sh --drop-existing --verbose
#
# Author: Copilot (Semantic Pipeline)
# Version: 1.0.0
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
DB_PATH="${PROJECT_ROOT}/oak_island_hub.db"
SOURCE_DIR="${PROJECT_ROOT}/docs/data"
EXTRACTED_DIR="${PROJECT_ROOT}/data_extracted/facts"
OUTPUT_DIR="${PROJECT_ROOT}/docs/data"
PYTHON="${PYTHON:-python3}"
VERBOSE=0
DRY_RUN=0
DROP_EXISTING=0
SKIP_PHASES=()
ONLY_PHASE=0

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $@"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $@"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $@"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $@" >&2
}

print_usage() {
    grep '^#' "$0" | head -30 | tail -28
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python
    if ! command -v "$PYTHON" &> /dev/null; then
        log_error "Python not found: $PYTHON"
        return 1
    fi
    log_success "Python: $($PYTHON --version)"
    
    # Check directories
    if [ ! -d "$SOURCE_DIR" ]; then
        log_warning "Source directory not found: $SOURCE_DIR"
    fi
    
    if [ ! -d "$EXTRACTED_DIR" ]; then
        log_warning "Extracted directory not found: $EXTRACTED_DIR"
    fi
    
    # Check schema file
    if [ ! -f "$SCRIPT_DIR/schema.sql" ]; then
        log_error "Schema file not found: $SCRIPT_DIR/schema.sql"
        return 1
    fi
    log_success "Schema file found"
    
    return 0
}

run_phase() {
    local phase_num=$1
    local phase_name=$2
    local script=$3
    shift 3
    local args=("$@")
    
    # Check if phase should be skipped
    for skip_phase in "${SKIP_PHASES[@]}"; do
        if [ "$skip_phase" == "$phase_num" ]; then
            log_warning "Skipping Phase $phase_num: $phase_name"
            return 0
        fi
    done
    
    # Check if only running specific phase
    if [ "$ONLY_PHASE" != 0 ] && [ "$ONLY_PHASE" != "$phase_num" ]; then
        return 0
    fi
    
    echo ""
    log_info "=========================================="
    log_info "PHASE $phase_num: $phase_name"
    log_info "=========================================="
    echo ""
    
    if [ "$DRY_RUN" == 1 ]; then
        log_info "[DRY RUN] Would execute: $PYTHON $script ${args[@]}"
        return 0
    fi
    
    if ! "$PYTHON" "$SCRIPT_DIR/$script" "${args[@]}"; then
        log_error "Phase $phase_num failed: $phase_name"
        return 1
    fi
    
    log_success "Phase $phase_num completed: $phase_name"
}

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --db)
                DB_PATH="$2"
                shift 2
                ;;
            --source-dir)
                SOURCE_DIR="$2"
                shift 2
                ;;
            --extracted-dir)
                EXTRACTED_DIR="$2"
                shift 2
                ;;
            --output-dir)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            --drop-existing)
                DROP_EXISTING=1
                shift
                ;;
            --verbose)
                VERBOSE=1
                shift
                ;;
            --dry-run)
                DRY_RUN=1
                shift
                ;;
            --skip-phase)
                SKIP_PHASES+=("$2")
                shift 2
                ;;
            --only-phase)
                ONLY_PHASE="$2"
                shift 2
                ;;
            --help|-h)
                print_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                print_usage
                exit 1
                ;;
        esac
    done
    
    # Header
    echo ""
    log_info "=========================================="
    log_info "SEMANTIC INGESTION ENGINE"
    log_info "Oak Island Hub — Unified Knowledge System"
    log_info "=========================================="
    echo ""
    
    # Configuration summary
    log_info "Configuration:"
    echo "  Database:        $DB_PATH"
    echo "  Source:          $SOURCE_DIR"
    echo "  Extracted:       $EXTRACTED_DIR"
    echo "  Output:          $OUTPUT_DIR"
    echo "  Drop Existing:   $DROP_EXISTING"
    if [ "$VERBOSE" == 1 ]; then echo "  Verbose:         enabled"; fi
    if [ "$DRY_RUN" == 1 ]; then echo "  Dry Run:         enabled"; fi
    [ ${#SKIP_PHASES[@]} -gt 0 ] && echo "  Skip Phases:     ${SKIP_PHASES[@]}"
    [ "$ONLY_PHASE" != 0 ] && echo "  Only Phase:      $ONLY_PHASE"
    echo ""
    
    # Verify prerequisites
    if ! check_prerequisites; then
        return 1
    fi
    
    echo ""
    
    # Build arguments array
    ingest_args=(--db "$DB_PATH" --source-dir "$SOURCE_DIR" --extracted-dir "$EXTRACTED_DIR")
    if [ "$DROP_EXISTING" == 1 ]; then
        ingest_args+=(--drop-existing)
    fi
    
    # Phase 1: Ingest
    if ! run_phase 1 "Raw Data Ingestion" "etl_ingest_semantic.py" "${ingest_args[@]}"; then
        return 1
    fi
    
    # Phase 2: Deduplicate
    dedupe_args=(--db "$DB_PATH" --extracted-dir "$EXTRACTED_DIR")
    if ! run_phase 2 "Intelligent Deduplication" "etl_dedupe_semantic.py" "${dedupe_args[@]}"; then
        return 1
    fi
    
    # Phase 3: Normalize
    normalize_args=(--db "$DB_PATH")
    if ! run_phase 3 "Semantic Normalization" "etl_normalize_semantic.py" "${normalize_args[@]}"; then
        return 1
    fi
    
    # Phase 4: Verify
    verify_args=(--db "$DB_PATH")
    if ! run_phase 4 "Data Quality Verification" "etl_verify_semantic.py" "${verify_args[@]}"; then
        return 1
    fi
    
    # Phase 5: Export
    export_args=(--db "$DB_PATH" --output-dir "$OUTPUT_DIR")
    if ! run_phase 5 "Export Optimized Views" "export_semantic_views.py" "${export_args[@]}"; then
        return 1
    fi
    
    # Summary
    echo ""
    log_info "=========================================="
    log_info "PIPELINE COMPLETE"
    log_info "=========================================="
    echo ""
    
    if [ -f "$DB_PATH" ]; then
        db_size=$(du -h "$DB_PATH" | cut -f1)
        log_success "Database: $DB_PATH ($db_size)"
    fi
    
    if [ -d "$OUTPUT_DIR" ]; then
        file_count=$(find "$OUTPUT_DIR" -maxdepth 1 -name "*.json" | wc -l)
        log_success "Exported views: $file_count JSON files to $OUTPUT_DIR"
    fi
    
    echo ""
    log_info "Next steps:"
    log_info "  1. Review exported JSON views in $OUTPUT_DIR"
    log_info "  2. Test database with: sqlite3 $DB_PATH"
    log_info "  3. Update frontend to use API instead of JSON"
    log_info "  4. Deploy api_server_v2.py"
    echo ""
    
    return 0
}

# Run main
if ! main "$@"; then
    log_error "Pipeline failed"
    exit 1
fi

exit 0
