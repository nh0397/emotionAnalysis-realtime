# How to Compile LaTeX to PDF

## Method 1: Command Line (Local)

### Prerequisites
- Install TeX Live (macOS: `brew install --cask mactex` or `brew install basictex`)
- Or use MacTeX distribution

### Compilation Steps

The LaTeX document requires multiple passes to resolve all references and citations:

```bash
cd "/Users/nh/Desktop/Naisarg/Final Project/Thesis_Template_for_Naisarg"

# Step 1: First pdflatex pass (creates .aux files)
pdflatex -interaction=nonstopmode main.tex

# Step 2: Run bibtex (processes bibliography)
bibtex main

# Step 3: Second pdflatex pass (includes bibliography)
pdflatex -interaction=nonstopmode main.tex

# Step 4: Third pdflatex pass (resolves all cross-references)
pdflatex -interaction=nonstopmode main.tex
```

### Quick Compile Script

You can also use this one-liner:

```bash
cd "/Users/nh/Desktop/Naisarg/Final Project/Thesis_Template_for_Naisarg" && \
pdflatex -interaction=nonstopmode main.tex && \
bibtex main && \
pdflatex -interaction=nonstopmode main.tex && \
pdflatex -interaction=nonstopmode main.tex
```

### Using latexmk (Recommended - Automatic)

If you have `latexmk` installed:

```bash
cd "/Users/nh/Desktop/Naisarg/Final Project/Thesis_Template_for_Naisarg"
latexmk -pdf main.tex
```

This automatically runs all necessary passes.

## Method 2: Using a LaTeX Editor

### TeXShop (macOS)
1. Open `main.tex` in TeXShop
2. Click "Typeset" button (or press Cmd+T)
3. TeXShop will automatically run all necessary passes

### TeXstudio
1. Open `main.tex` in TeXstudio
2. Click "Build & View" (F5)
3. TeXstudio handles multiple passes automatically

### VS Code with LaTeX Workshop Extension
1. Install "LaTeX Workshop" extension
2. Open `main.tex`
3. Press Cmd+Alt+B (or click "Build LaTeX project")
4. Extension handles compilation automatically

## Method 3: Overleaf (Online)

1. Go to [overleaf.com](https://www.overleaf.com)
2. Create a new project or upload your files
3. Click "Recompile" button
4. Overleaf handles all compilation passes automatically

**Note:** If you get timeout errors on Overleaf free plan:
- Add `draft,` to `\documentclass` options (line 6 in main.tex)
- This skips image processing for faster compilation
- Remove `draft,` for final PDF with images

## Troubleshooting

### Missing Images
If you see "File not found" errors for images:
- Check that images are in `Docs/Figures/` directory
- Or update paths in the `.tex` files

### Bibliography Errors
If citations show as `[?]`:
- Make sure `bibtex main` was run
- Check that `Chapters/Bibi.bib` exists and is valid
- Run pdflatex again after bibtex

### Undefined References
If you see "??" for figure/table references:
- Run pdflatex multiple times (usually 2-3 times after bibtex)
- LaTeX needs multiple passes to resolve all cross-references

## Output

The compiled PDF will be:
```
/Users/nh/Desktop/Naisarg/Final Project/Thesis_Template_for_Naisarg/main.pdf
```

## Clean Build (Remove Auxiliary Files)

To start fresh and remove all auxiliary files:

```bash
cd "/Users/nh/Desktop/Naisarg/Final Project/Thesis_Template_for_Naisarg"
rm -f *.aux *.log *.bbl *.blg *.out *.toc *.lof *.fls *.fdb_latexmk *.synctex.gz
rm -f Chapters/*.aux Chapters/Appendices/*.aux
```

Then compile again from scratch.

