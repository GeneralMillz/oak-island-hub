#!/bin/bash
# Oak Island Hub: SQLite Migration Quick-Start Guide
# Run this script to initialize the database and test the new API

set -e

echo "=========================================="
echo "Oak Island Hub - SQLite Setup Quick-Start"
echo "=========================================="
echo

PROJECT_ROOT="/home/pi/oak-island-hub"
DB_DIR="$PROJECT_ROOT/data"
DATA_DIR="$PROJECT_ROOT/docs/data"

# Ensure directories exist
mkdir -p "$DB_DIR"

echo "📁 Project directories:"
echo "  Project: $PROJECT_ROOT"
echo "  Database: $DB_DIR"
echo "  Data: $DATA_DIR"
echo

# Step 1: Verify files exist
echo "✓ Step 1: Verifying required files..."

if [ ! -f "$PROJECT_ROOT/pipeline/schema.sql" ]; then
    echo "❌ ERROR: schema.sql not found!"
    exit 1
fi
echo "  ✓ pipeline/schema.sql found"

if [ ! -f "$PROJECT_ROOT/pipeline/etl_pipeline.py" ]; then
    echo "❌ ERROR: etl_pipeline.py not found!"
    exit 1
fi
echo "  ✓ pipeline/etl_pipeline.py found"

if [ ! -f "$PROJECT_ROOT/api_server_v2.py" ]; then
    echo "❌ ERROR: api_server_v2.py not found!"
    exit 1
fi
echo "  ✓ api_server_v2.py found"

if [ ! -d "$DATA_DIR" ]; then
    echo "❌ ERROR: $DATA_DIR not found!"
    exit 1
fi
echo "  ✓ docs/data directory found"

echo

# Step 2: Check Python version
echo "✓ Step 2: Checking Python..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python version: $PYTHON_VERSION"
if command -v python3 &> /dev/null; then
    echo "  ✓ Python 3 available"
else
    echo "  ❌ Python 3 not found!"
    exit 1
fi
echo

# Step 3: Verify JSON data files
echo "✓ Step 3: Checking source data files..."
for file in locations.json episodes.json events.json people.json theories.json; do
    if [ -f "$DATA_DIR/$file" ]; then
        SIZE=$(du -h "$DATA_DIR/$file" | cut -f1)
        echo "  ✓ $file ($SIZE)"
    else
        echo "  ⚠ WARNING: $file not found"
    fi
done
echo

# Step 4: Run ETL pipeline
echo "✓ Step 4: Running ETL pipeline..."
echo "  Command: python3 $PROJECT_ROOT/pipeline/etl_pipeline.py --db-path $DB_DIR --data-dir $DATA_DIR --reset"
echo

cd "$PROJECT_ROOT"

python3 pipeline/etl_pipeline.py \
    --db-path "$DB_DIR" \
    --data-dir "$DATA_DIR" \
    --reset

echo
echo "✓ ETL pipeline completed!"
echo

# Step 5: Verify database
echo "✓ Step 5: Verifying database..."
DB_FILE="$DB_DIR/oak_island_hub.db"

if [ -f "$DB_FILE" ]; then
    DB_SIZE=$(du -h "$DB_FILE" | cut -f1)
    echo "  ✓ Database created: $DB_FILE ($DB_SIZE)"
else
    echo "  ❌ ERROR: Database file not created!"
    exit 1
fi

# Count records
echo "  Database contents:"

LOCATIONS=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM locations;")
EPISODES=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM episodes;")
EVENTS=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM events;")
PEOPLE=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM people;")
THEORIES=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM theories;")

echo "    - Locations: $LOCATIONS"
echo "    - Episodes: $EPISODES"
echo "    - Events: $EVENTS"
echo "    - People: $PEOPLE"
echo "    - Theories: $THEORIES"
echo

# Step 6: Test API server
echo "✓ Step 6: Starting API server (test mode)..."
echo "  To test, run in another terminal:"
echo
echo "  # Test endpoints:"
echo "  curl http://localhost:5000/api/v2/locations | head -20"
echo "  curl http://localhost:5000/api/v2/locations/money_pit"
echo "  curl http://localhost:5000/api/v2/theories"
echo "  curl http://localhost:5000/api/status"
echo
echo "  # Or start the server:"
echo "  cd $PROJECT_ROOT && python3 api_server_v2.py --dev"
echo

echo "=========================================="
echo "✅ SQLite setup complete!"
echo "=========================================="
echo
echo "Next steps:"
echo "  1. Start the API server:"
echo "     cd $PROJECT_ROOT && python3 api_server_v2.py"
echo
echo "  2. Test the endpoints:"
echo "     curl http://localhost:5000/api/v2/locations"
echo "     curl http://localhost:5000/api/status"
echo
echo "  3. Review the migration guide:"
echo "     cat $PROJECT_ROOT/SQLITE_MIGRATION_GUIDE.md"
echo
echo "  4. When ready, update frontend to use API (optional):"
echo "     Modify docs/js/data.js, details.js, search.js"
echo
echo "  5. To rollback:"
echo "     rm $DB_FILE"
echo "     (API will fall back to JSON files automatically)"
echo
