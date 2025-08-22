# Recurse Paper

Hobby program intended to improve understanding while reading research papers.

Academic and technical jargon is automatically detected and displayed with dropdown summaries for each page of the pdf along with corresponding wikipedia links for each term. 
If you find yourself bogged down with the same jargon in those summaries you can descend another layer and provide yourself even more context.

Detection is performed through [Dandelion](https://dandelion.eu/) [entity extraction](https://en.wikipedia.org/wiki/Named-entity_recognition) 

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
