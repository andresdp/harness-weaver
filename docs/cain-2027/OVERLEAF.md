# Overleaf package

`HarnessWeaver-CAIN-2027-Overleaf.zip` is the import-ready archive for the current paper draft. It contains:

- `main.tex` — the main LaTeX document. Its figure is written in TikZ.
- `references.bib` — the bibliography used by `main.tex`.
- `README.md` — import and rebuild instructions.

In Overleaf, choose **New Project → Upload Project** and upload the ZIP. If Overleaf does not select it automatically, set `main.tex` as the main document. The document uses `IEEEtran` and is intended to compile with pdfLaTeX and BibTeX.

After editing `main.tex` or `references.bib`, rebuild the archive from the repository root:

```bash
python docs/cain-2027/package_overleaf.py
```

The script uses only the Python standard library and writes this ZIP beside the source files. Rebuild it before uploading an updated draft to Overleaf.
