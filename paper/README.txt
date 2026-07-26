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
   \newcommand{\debugenablereferencelink}{0}
     The link-embedding code (\pdfstartlink/\pdfendlink) has been REMOVED,
     so NO build of this source can emit a PDF link annotation. Both toggle
     settings are AAAI-27 compliant (0 link annotations):
     0 = SUBMISSION / CAMERA-READY. URLs hidden. <-- upload this build.
     1 = REVIEW-ONLY. Prints each reference URL as PLAIN, NON-CLICKABLE text
         so you can eyeball them; do not submit this build (URLs add length).
   Each .bib entry carries note={\refurl{<url>}}; the bst is unmodified.

Workflow:
  1) (Optional) Set toggle = 1, build, and read every reference URL to
     verify it; the URLs are plain text, never clickable annotations.
  2) Set toggle = 0, rebuild -> this is the PDF you upload.
     Build/verify: pdflatex main -> bibtex main -> pdflatex main -> pdflatex main
     Then confirm the PDF has ZERO link annotations before uploading.
  3) Fill & upload the Reproducibility Checklist; anonymize any Code & Data
     supplement (no names/paths/git history); external repo links forbidden.
