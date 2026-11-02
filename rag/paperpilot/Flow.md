# Flow.md — PaperPilot Execution Flow

## Call Chains

### Command: `paperpilot search "query"`
```
__main__.main()
  └─ cmd_search(args)
       ├─ search_arxiv(query, max_results, sort_by)
       │    └─ _get_client().get(ARXIV_QUERY_URL, params)
       │         └─ httpx.Client.get() → HTTP GET to export.arxiv.org
       │    └─ _parse_feed(xml_text)
       │         └─ ET.fromstring(xml)
       │         └─ [for each entry] extract id, title, summary, authors, categories, links
       │         └─ returns list[ArxivPaper]
       ├─ PaperIndex.load() → reads ~/.paperpilot/index.json + embeddings.npy
       ├─ PaperIndex.add_papers(papers)
       │    └─ _chunk_paper(paper) → split abstract into sentence-groups
       │    └─ _get_encoder() → SentenceTransformer('all-MiniLM-L6-v2')
       │    └─ encoder.encode(chunk_texts) → numpy embedding matrix
       │    └─ self.embeddings = np.vstack(...) → append to existing matrix
       └─ PaperIndex.save() → writes index.json + embeddings.npy
```

### Command: `paperpilot query "question"`
```
__main__.main()
  └─ cmd_query(args)
       ├─ PaperIndex.load()
       ├─ _answer_question(index, question, k)
       │    ├─ PaperIndex.search(question, k)
       │    │    ├─ _get_encoder().encode([question]) → query vector
       │    │    └─ np.dot(embeddings, query_vector.T) → cosine similarities
       │    │    └─ np.argsort(scores)[-top_k:] → top indices
       │    │    └─ returns list[SearchHit]
       │    ├─ query_papers(question, hits)
       │    │    ├─ build context block from hit chunks
       │    │    ├─ _get_client() → OpenAI(api_key, base_url=nexos.ai)
       │    │    └─ client.chat.completions.create() → LLM answer
       │    └─ print(answer)
```

### Command: `paperpilot list`
```
__main__.main()
  └─ cmd_list()
       ├─ PaperIndex.load()
       └─ PaperIndex.list_papers() → list[dict{id, title}]
```

## Module Dependency Graph

```
paperpilot/__main__.py
  ├── paperpilot/arxiv_client.py
  │    ├── paperpilot/models.py  (ArxivPaper)
  │    └── httpx
  ├── paperpilot/indexer.py
  │    ├── paperpilot/models.py  (ArxivPaper, Chunk, SearchHit)
  │    ├── numpy
  │    └── sentence_transformers
  ├── paperpilot/llm.py
  │    ├── paperpilot/models.py  (SearchHit)
  │    └── openai (OpenAI client)
  └── paperpilot/__init__.py     (version)
```

## Data Flow

```
User CLI Input
    │
    ▼
__main__.py (argparse routing)
    │
    ├──▶ search ──▶ arxiv_client.search_arxiv()
    │                      │
    │                      ▼
    │               arXiv API (http://export.arxiv.org)
    │                      │
    │                      ▼  Atom XML
    │               arxiv_client._parse_feed()
    │                      │
    │                      ▼  list[ArxivPaper]
    │               indexer.PaperIndex.add_papers()
    │                      │
    │                      ▼  sentence-transformers encode
    │               numpy embedding matrix
    │                      │
    │                      ▼
    │               ~/.paperpilot/ (index.json + embeddings.npy)
    │
    ├──▶ query ──▶ indexer.PaperIndex.search()
    │                      │
    │                      ▼  cosine similarity
    │               list[SearchHit] (top-k chunks)
    │                      │
    │                      ▼
    │               llm.query_papers(question, hits)
    │                      │
    │                      ▼  LLM (OpenRouter via OpenAI SDK)
    │               final answer with citations
    │
    └──▶ list ──▶ indexer.PaperIndex.list_papers()
                           │
                           ▼  list[dict{id, title}]
```

## File Layout

```
rag/paperpilot/
├── paperpilot/
│   ├── __init__.py          Version string
│   ├── __main__.py          CLI entry, argparse, command routing
│   ├── models.py            ArxivPaper, Chunk, SearchHit dataclasses
│   ├── arxiv_client.py      arXiv API HTTP client + XML parser
│   ├── indexer.py           Embedding index: add, search, save, load
│   └── llm.py               LLM query: answer generation, summarization
├── tests/
│   ├── __init__.py
│   └── test_paperpilot.py   Unit tests (mock HTTP, mock LLM)
├── requirements.txt
├── README.md
├── Decisions.md
└── Flow.md
```