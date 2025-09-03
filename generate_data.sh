#!/bin/bash

echo "🚀 Fast Data Generator for Tweet Analysis System"
echo "================================================"

cd backend/src

# Install required packages if not present
echo "📦 Installing required packages..."
pip install psycopg2-binary numpy tqdm ollama

echo ""
echo "🎯 Choose generation mode:"
echo "A. FAST MODE (Synthetic emotions - fastest)"
echo "B. NLP MODE (Real AI analysis - slower but realistic)"
echo ""

read -p "Enter mode (A/B): " mode

case $mode in
    [Aa]*)
        mode_flag="--fast-mode"
        echo "⚡ Fast Mode selected - Using synthetic emotions"
        ;;
    [Bb]*)
        mode_flag="--use-nlp"
        echo "🧠 NLP Mode selected - Using real AI analysis"
        echo "⚠️  Note: Requires Ollama to be running locally"
        ;;
    *)
        echo "❌ Invalid choice - defaulting to Fast Mode"
        mode_flag="--fast-mode"
        ;;
esac

echo ""
echo "🎯 Choose generation size:"
echo "1. Quick test (100K records) - Fast: ~30s, NLP: ~5min"
echo "2. Medium dataset (1M records) - Fast: ~5min, NLP: ~45min" 
echo "3. Large dataset (5M records) - Fast: ~20min, NLP: ~4hrs"
echo "4. Massive dataset (10M records) - Fast: ~45min, NLP: ~8hrs"
echo "5. Custom amount"

read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo "🔥 Generating 100K records for testing..."
        python fast_data_generator.py --records 100000 --workers 4 $mode_flag
        ;;
    2)
        echo "🔥 Generating 1M records..."
        python fast_data_generator.py --records 1000000 --workers 6 $mode_flag
        ;;
    3)
        echo "🔥 Generating 5M records..."
        python fast_data_generator.py --records 5000000 --workers 8 $mode_flag
        ;;
    4)
        echo "🔥 Generating 10M records..."
        python fast_data_generator.py --records 10000000 --workers 8 $mode_flag
        ;;
    5)
        read -p "Enter number of records: " custom_records
        read -p "Enter number of workers (4-12): " custom_workers
        echo "🔥 Generating $custom_records records with $custom_workers workers..."
        python fast_data_generator.py --records $custom_records --workers $custom_workers $mode_flag
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Data generation complete!"
echo "🎯 Your SimpleDotPlot is now ready to handle massive datasets!"
echo ""
echo "📊 Next steps:"
echo "1. Start the backend: cd backend/src && python api_server.py"
echo "2. Start the frontend: cd frontend && npm start"
echo "3. Test the visualization with millions of data points!"