#!/usr/bin/env python3
"""
Run Master's Thesis Defense Evaluation
Installs dependencies and generates comprehensive HTML report
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required dependencies"""
    print("Installing required dependencies...")
    
    try:
        # Install VADER sentiment analysis
        subprocess.check_call([sys.executable, "-m", "pip", "install", "vaderSentiment"])
        print("✅ VADER sentiment analysis installed")
        
        # Install other required packages
        subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib", "seaborn", "pandas", "numpy"])
        print("✅ Additional packages installed")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def run_thesis_defense():
    """Run the thesis defense evaluation"""
    print("🚀 Running Master's Thesis Defense Evaluation")
    print("=" * 60)
    
    try:
        # Import and run the evaluation
        from thesis_defense_evaluation import ThesisDefenseEvaluator
        
        evaluator = ThesisDefenseEvaluator()
        results = evaluator.run_comprehensive_evaluation()
        
        print("\n✅ Thesis defense evaluation completed!")
        print("📊 Check the generated HTML report for complete analysis")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required packages are installed")
        return False
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return False

def main():
    """Main execution function"""
    print("Master's Thesis Defense: Emotion Analysis Model Evaluation")
    print("=" * 70)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies. Exiting.")
        return
    
    # Run evaluation
    if run_thesis_defense():
        print("\n🎓 Thesis defense evaluation completed successfully!")
        print("📄 Open the generated HTML file in your browser to view the complete report")
        print("💡 This report is ready for your thesis defense presentation")
    else:
        print("\n❌ Thesis defense evaluation failed")
        print("🔧 Check the error messages above for troubleshooting")

if __name__ == "__main__":
    main()
