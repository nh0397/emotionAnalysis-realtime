#!/usr/bin/env python3
"""
Master's Thesis Defense: Emotion Analysis Model Evaluation
"""

from evaluation.evaluate_on_datasets import ComprehensiveModelEvaluator

def main():
    evaluator = ComprehensiveModelEvaluator()
    evaluator.run_comprehensive_evaluation()
    evaluator.generate_report_ready_analysis()

if __name__ == "__main__":
    main()


