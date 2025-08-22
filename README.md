# Recurse Paper

Hobby program intended to improve understanding while reading research papers.
Recursive entity extraction per page allows users to familiarize themselves with technical terms, giving themselves more context with summaries and wikipedia links available at each depth.

[recursepaper-example.webm](https://github.com/user-attachments/assets/a2494cc7-9e36-4cdd-a682-bfa27cddd411)

### Usage
- Get a free [Dandelion API key](https://dandelion.eu/) which provides 1000 tks/day of entity extraction
- run:
  ```
  export DAND_TOKEN=<your API key>`
  pip install dearpygui requests pymupdf arxiv
  git clone https://github.com/GabrielNakamoto/recursepaper
  cd recursepaper
  python3 src/main.py
  ```

The file system consists of an entities and papers directory, the papers directory stores downloaded pdfs from the arxiv client however you can use your own paper pdfs too.
Any entity extraction that is performed on a paper will be cached recursively and stored in the entities directory for faster access and reduced API usage.

### Dependencies:
- [Dandelion API](https://dandelion.eu/) for entity extraction
- [Dear Py Gui](https://github.com/hoffstadt/DearPyGui) for gui
- [pymupdf](https://github.com/pymupdf/PyMuPDF) for pdf manipulation
- [arxiv](https://pypi.org/project/arxiv/) for a python arxiv API wrapper
