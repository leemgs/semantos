# SemantOS ACL 2027 paper build.
#
# `make` builds main.pdf (the anonymous review version) from main.tex using the
# official ACL style files (acl.sty / acl_natbib.bst). Reference URLs are
# clickable links; ACL permits hyperref, so no separate link-check build is needed.

LATEX  = pdflatex -interaction=nonstopmode -halt-on-error
BIBTEX = bibtex
SRC    = $(wildcard *.tex) reference-data.bib acl.sty acl_natbib.bst \
         $(wildcard figures/*)

.PHONY: all clean
all: main.pdf

main.pdf: $(SRC)
	$(LATEX)  main.tex
	$(BIBTEX) main
	$(LATEX)  main.tex
	$(LATEX)  main.tex

clean:
	rm -f main.aux main.bbl main.blg main.log main.out
