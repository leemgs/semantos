# SemantOS AAAI-27 paper build.
#
# `make` (or `make all`) builds BOTH PDFs from the single source main.tex:
#
#   main.pdf           SUBMISSION version  -- no URL links, 0 link annotations,
#                                             fully AAAI-27 compliant. UPLOAD THIS.
#   main_bluelink.pdf  DEBUG version       -- blue CLICKABLE reference URLs, for
#                                             pre-submission link checking only.
#                                             MUST NOT be submitted to AAAI.
#
# The two builds are selected by overriding \debugenablereferencelink on the
# pdflatex command line (0 = submission, 1 = blue links) and writing distinct
# jobnames, so the submission file main.pdf is always the link-free build.

LATEX  = pdflatex -interaction=nonstopmode -halt-on-error
BIBTEX = bibtex
SRC    = $(wildcard *.tex) reference-data.bib aaai2027.sty aaai2027.bst \
         $(wildcard figures/*)

.PHONY: all clean
all: main.pdf main_bluelink.pdf

# --- Submission PDF: no links (compliant) -------------------------------------
main.pdf: $(SRC)
	$(LATEX)  -jobname=main "\def\debugenablereferencelink{0}\input{main.tex}"
	$(BIBTEX) main
	$(LATEX)  -jobname=main "\def\debugenablereferencelink{0}\input{main.tex}"
	$(LATEX)  -jobname=main "\def\debugenablereferencelink{0}\input{main.tex}"

# --- Debug PDF: blue clickable URLs (do NOT submit) ---------------------------
main_bluelink.pdf: $(SRC)
	$(LATEX)  -jobname=main_bluelink "\def\debugenablereferencelink{1}\input{main.tex}"
	$(BIBTEX) main_bluelink
	$(LATEX)  -jobname=main_bluelink "\def\debugenablereferencelink{1}\input{main.tex}"
	$(LATEX)  -jobname=main_bluelink "\def\debugenablereferencelink{1}\input{main.tex}"

clean:
	rm -f main.aux main.bbl main.blg main.log main.out \
	      main_bluelink.aux main_bluelink.bbl main_bluelink.blg \
	      main_bluelink.log main_bluelink.out
