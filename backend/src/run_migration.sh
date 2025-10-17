#!/bin/bash
# Database Migration Runner
# Fixes the schema to properly separate sentiment from emotions

echo "🗄️  Database Schema Migration"
echo "================================"
echo "⚠️  WARNING: This will DROP existing tables and DELETE all data!"
echo ""
read -p "Continue? (yes/no): " response

if [ "$response" != "yes" ]; then
    echo "Migration cancelled."
    exit 1
fi

echo ""
echo "1. Starting Docker services..."
cd "/Users/nh/Desktop/Naisarg/Final Project"
docker-compose up -d postgres

echo "2. Waiting for PostgreSQL to be ready..."
sleep 10

echo "3. Running database migration..."
cd backend/src
source ../realtime/bin/activate
python database_migration.py --yes

echo ""
echo "✅ Migration completed!"
echo ""
echo "Next steps:"
echo "1. Update your NLP pipeline to use new column names"
echo "2. Update API endpoints to use new schema" 
echo "3. Test with sample data"
echo ""
echo "Schema diagram saved to: database_schema_diagram.md"
echo "Copy the Mermaid code to https://mermaid.live/ to view the diagram"
