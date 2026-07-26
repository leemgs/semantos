SemantOS — AAAI-27 Main Technical Track submission source (double-blind)
=======================================================================
Build:   pdflatex main -> bibtex main -> pdflatex main -> pdflatex main
Style:   Official AAAI-27 Author Kit (aaai2027.sty / .bst / .bib), unmodified.
Fonts:   aaai2027.sty auto-loads newtx/helvet/courier (present on Overleaf
         and full TeX Live installs).
Layout:  7 pages main + references (9 pages total). No forbidden packages,
         no \clearpage/\pagestyle, no spacing hacks. Author block is
         auto-anonymized by the [submission] option.

Reference web-link toggle (main.tex, one line):
   \newcommand{\debugenablereferencelink}{1}
     1 = DEBUG/REVIEW-ONLY. Prints each reference URL as a BLUE, CLICKABLE
         link so you can click-check every reference. This is done with the
         pdfTeX primitives \pdfstartlink/\pdfendlink (NOT hyperref, which
         aaai2027.sty blocks), and it embeds link annotations in the PDF.
         >>> A PDF built with 1 MUST NOT be submitted to AAAI. <<<
     0 = SUBMISSION / CAMERA-READY. No color, no links, URLs hidden.
         Fully AAAI-27 compliant (0 link annotations).
   Each .bib entry carries note={\refurl{<url>}}; the bst is unmodified.

Workflow:
  1) Keep toggle = 1, build, and click every reference URL to verify it.
  2) Set toggle = 0, rebuild -> this is the PDF you upload to OpenReview.
  3) Fill & upload the Reproducibility Checklist; anonymize any Code & Data
     supplement (no names/paths/git history); external repo links forbidden.
