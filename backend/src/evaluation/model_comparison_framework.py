#!/usr/bin/env python3
"""
Model Comparison Framework for Emotion Analysis
Comprehensive evaluation of different transformer models for tweet emotion analysis
"""

from evaluation.evaluate_on_datasets import ComprehensiveModelEvaluator

def main():
    evaluator = ComprehensiveModelEvaluator()
    evaluator.run_comprehensive_evaluation()
    evaluator.generate_report_ready_analysis()

if __name__ == "__main__":
    main()


