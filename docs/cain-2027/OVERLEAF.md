# Overleaf package

`HarnessWeaver-CAIN-2027-Overleaf.zip` is the import-ready archive for the current paper draft. It contains:

- `PAPER-DRAFT.tex` — the main LaTeX document. Its figure is written in TikZ and its bibliography is inline, so no separate figure or `.bib` files are required.
- `PAPER-DRAFT.md` — the parallel Markdown draft for co-author review; Overleaf does not compile this file.
- `README.md` — import and rebuild instructions.

In Overleaf, choose **New Project → Upload Project** and upload the ZIP. If Overleaf does not select it automatically, set `PAPER-DRAFT.tex` as the main document. The document uses `IEEEtran` and is intended to compile with pdfLaTeX.

After editing either paper source, rebuild the archive from the repository root:

```bash
python docs/cain-2027/package_overleaf.py
```

The script uses only the Python standard library and writes this ZIP beside the source files. Rebuild it before uploading an updated draft to Overleaf.
