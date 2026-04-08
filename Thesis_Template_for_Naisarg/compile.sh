#!/bin/bash
# LaTeX compilation script with BibTeX

echo "Step 1: Running pdflatex (first pass)..."
pdflatex -interaction=nonstopmode main.tex

echo "Step 2: Running BibTeX..."
bibtex main

echo "Step 3: Running pdflatex (second pass)..."
pdflatex -interaction=nonstopmode main.tex

echo "Step 4: Running pdflatex (third pass for cross-references)..."
pdflatex -interaction=nonstopmode main.tex

echo "Compilation complete! Check main.pdf"
