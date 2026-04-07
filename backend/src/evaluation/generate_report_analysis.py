#!/usr/bin/env python3
"""
Generate Report-Ready Analysis for Model Comparison
"""

from evaluation.evaluate_on_datasets import ComprehensiveModelEvaluator

def main():
    evaluator = ComprehensiveModelEvaluator()
    evaluator.run_comprehensive_evaluation()
    evaluator.generate_report_ready_analysis()

if __name__ == "__main__":
    main()


