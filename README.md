# Recurse Paper

Hobby program intended to improve understanding while reading research papers.

## Usage
- Get a free [Dandelion API key](https://dandelion.eu/) which provides 1000 tks/day of entity extraction
- run:
  ```
  export DAND_TOKEN=<your API key>
  pip install dearpygui requests pymupdf arxiv
  git clone https://github.com/GabrielNakamoto/recursepaper
  cd recursepaper
  mkdir entities papers
  python3 src/main.py
  ```

## How it works

Academic and technical jargon is automatically detected and displayed with dropdown summaries for each page of the pdf along with corresponding wikipedia links for each term. 
If you find yourself bogged down with the same jargon in those summaries you can descend another layer and provide yourself even more context.

Detection is performed through [Dandelion](https://dandelion.eu/) [entity extraction](https://en.wikipedia.org/wiki/Named-entity_recognition) 

A rudimentary arxiv client is provided to download papers directly to the `papers/` directory but you can just copy your own pdfs there directly. 
Any entity extraction that is performed on a paper will be cached recursively and stored in the `entities/` directory for faster access and reduced API usage.

## PDF Operations
- vim style movement with`j` and `k` keys
- pdf scaling with `-` and `=`

## Example video
https://github.com/user-attachments/assets/e20d4d07-a2aa-4666-a07d-0f7fee587e90

## Todo

- Retrieve entity thumbnails from wikipedia
- Support pdf fetching from url (wget?)
- make runnable from path name
- better error handling + more descriptive messages
- proper logging instead of printing logs to stdout
