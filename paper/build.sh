#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Verify that all required figure PDFs are present in paper/figures/
python3 "${REPO_ROOT}/tools/collect_paper_figures.py" --check

# Four-pass build sequence to resolve all labels, citations, and cross-references
cd "${SCRIPT_DIR}"
pdflatex -interaction=nonstopmode paper.tex
bibtex paper
pdflatex -interaction=nonstopmode paper.tex
pdflatex -interaction=nonstopmode paper.tex
