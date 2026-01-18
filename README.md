# GenAI Legal Document Intelligence Platform

An async, agentic, and scalable system for ingesting legal documents, extracting structured legal intelligence, and indexing results for analytics.

## 1. Problem Statement
Legal teams handle thousands of contracts and legal documents. Manual review is slow, error-prone, and expensive. This platform automatically ingests legal documents, understands them using agent-based GenAI, extracts structured legal intelligence, and stores it for search and analytics — all asynchronously and reliably.

## 2. What This System Achieves
- Detects whether a document is legal
- Avoids reprocessing duplicate contracts
- Identifies contract type (CUAD-based)
- Extracts legal clauses
- Extracts entities (parties, people, dates, obligations)
- Indexes data for fast retrieval (ElasticSearch)
- Fully async, fault-tolerant, retry-enabled
- Pluggable LLM architecture
- Clean separation of concerns

## 3. High-Level Architecture (Conceptual)
```
Client
  |
  v
FastAPI (async)
  |
  | Submit job
  v
Redis (Broker)
  |
  v
Celery Orchestrator Task
  |
  +--> Agent 1: Legal Classifier (AWS Strands)
  |
  +--> Agent 2: Deduplication (AWS Strands)
  |
  +--> Agent 3: Contract Type Detection (AWS Strands, CUAD)
  |
  +--> Agent 4: Clause Extraction (AWS Strands, LLM)
  |
  +--> Agent 5: NER (AWS Strands, DL model)
  |
  v
ElasticSearch
  ├── legal_clauses_index
  └── legal_ner_index
  |
  v
Postgres (Logs + Metadata)
```

## 4. Agent-Based Processing Flow (Polished)
### 🧠 Agent 1: Legal Document Classifier (AWS Strands)
Determines legal vs non-legal. If non-legal, the pipeline stops.

### ♻️ Agent 2: Deduplication Agent (AWS Strands)
Uses document hash (SHA-256) and optional semantic embeddings to prevent reprocessing identical contracts.

### 📄 Agent 3: Contract Type Detection (AWS Strands)
Classifies contracts into CUAD taxonomy (NDA, Lease, Employment, Service Agreement, etc.).

### 🧩 Agent 4: Clause Extraction Agent (AWS Strands + LLM)
Extracts clause types such as termination, confidentiality, governing law, payment terms. Output example:
```json
{
  "clause_type": "termination",
  "text": "...",
  "confidence": 0.91
}
```

### 🧠 Agent 5: NER Agent (AWS Strands + DL Model)
Extracts parties, persons, dates, locations, monetary values.

## 5. ElasticSearch Index Design
### 📌 Index 1: `legal_clauses_index`
```json
{
  "document_id": "uuid",
  "contract_type": "NDA",
  "clause_type": "confidentiality",
  "clause_text": "...",
  "confidence": 0.92
}
```

### 📌 Index 2: `legal_ner_index`
```json
{
  "document_id": "uuid",
  "entity_type": "PARTY",
  "entity_value": "ABC Corp",
  "start_offset": 120,
  "end_offset": 128
}
```

## 6. FastAPI + Celery + Redis Organization
FastAPI handles uploads asynchronously and returns task IDs immediately:
```python
@app.post("/documents")
async def upload_document():
    task = process_legal_document.delay(doc_path)
    return {"task_id": task.id}
```

Celery orchestrates the multi-agent pipeline with retries, while Redis serves as the broker.

## 7. Prompt Management Strategy
### 📂 Prompts as Files
```
prompts/
 ├── classify_legal.txt
 ├── detect_contract_type.txt
 ├── extract_clauses.txt
```

### 📂 Variables as JSON
```
prompt_vars/
 ├── classify_legal.json
 ├── extract_clauses.json
```

Runtime flow:
```python
prompt = load_prompt("extract_clauses.txt")
vars = load_vars("extract_clauses.json")
final_prompt = prompt.format(**vars)
```

## 8. LLM Abstraction (Pluggable Design)
```python
class LLMClient:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError
```

Implementations: OpenAI, Bedrock, Claude, or local LLMs. Swap providers without touching business logic.

## 9. Error Handling, Retries & Reliability
### ✅ Standard Retry Strategy
- Exponential backoff
- Max retries: 3–5
- Retry only idempotent steps

```python
@celery.task(bind=True, autoretry_for=(Exception,),
             retry_kwargs={"max_retries": 5, "countdown": 60})
def process_legal_document(self, doc_path):
    ...
```

### 🔁 Resume Processing From Last Successful Step
```json
{
  "document_id": "uuid",
  "last_completed_step": "deduplication"
}
```

### 🧹 File Deletion Logic
- On success: final agent emits completion event; orchestrator deletes file.
- On failure: file retained for retry; delete only after success or max retries exceeded.

### 🧾 Logging Strategy
Postgres stores task lifecycle, agent execution logs, errors, and retry attempts for auditability.

## 10. MCP (Model Context Protocol) Use
Introduce MCP servers for:
- **Prompt registry**: centralized prompt loading and versioning.
- **Schema/ontology registry**: CUAD taxonomy and clause definitions.
- **Model routing**: select LLM providers based on tenant or data sensitivity.

MCP allows agents to fetch prompts, schemas, or routing rules dynamically without redeploying code.

## 11. Full Folder Structure (Proposed)
```
lexiai-legal-intelligence/
├── app/
│   ├── api/
│   │   └── routes.py
│   ├── agents/
│   │   ├── legal_classifier.py
│   │   ├── deduplicator.py
│   │   ├── contract_type.py
│   │   ├── clause_extractor.py
│   │   └── ner_agent.py
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   ├── mcp/
│   │   ├── prompt_registry.py
│   │   ├── schema_registry.py
│   │   └── routing.py
│   ├── models/
│   │   ├── document.py
│   │   └── pipeline_state.py
│   ├── prompts/
│   │   ├── classify_legal.txt
│   │   ├── detect_contract_type.txt
│   │   └── extract_clauses.txt
│   ├── prompt_vars/
│   │   ├── classify_legal.json
│   │   └── extract_clauses.json
│   ├── services/
│   │   ├── llm_client.py
│   │   ├── elastic.py
│   │   ├── postgres.py
│   │   └── redis.py
│   ├── tasks/
│   │   └── orchestrator.py
│   └── utils/
│       └── hashing.py
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 12. Key Code Files (Sketches)
### `app/tasks/orchestrator.py`
```python
@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 5, "countdown": 60})
def process_legal_document(self, doc_path):
    state = load_pipeline_state(doc_path)
    if state.last_completed_step < "classification":
        legal = legal_classifier.run(doc_path)
        if not legal:
            return
        save_step("classification")

    if state.last_completed_step < "deduplication":
        deduplicator.run(doc_path)
        save_step("deduplication")

    if state.last_completed_step < "contract_type":
        contract_type = contract_type_agent.run(doc_path)
        save_step("contract_type")

    if state.last_completed_step < "clauses":
        clauses = clause_extractor.run(doc_path)
        index_clauses(clauses)
        save_step("clauses")

    if state.last_completed_step < "ner":
        entities = ner_agent.run(doc_path)
        index_entities(entities)
        save_step("ner")

    delete_file(doc_path)
```

### `app/agents/legal_classifier.py`
```python
class LegalClassifierAgent:
    def run(self, doc_path: str) -> bool:
        # AWS Strands invocation (classification prompt)
        return True
```

## 13. Retry & Failure Handling Logic
- Celery retries on transient failures with exponential backoff.
- Pipeline state stored in Postgres allows resuming from the last successful agent.
- Idempotent steps ensure safe retries.

## 14. Docker Compose (Sketch)
```yaml
version: "3.9"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - postgres
      - elasticsearch
  worker:
    build: .
    command: celery -A app.tasks.orchestrator worker --loglevel=info
    depends_on:
      - redis
      - postgres
      - elasticsearch
  redis:
    image: redis:7
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: lexiai
      POSTGRES_PASSWORD: lexiai
      POSTGRES_DB: lexiai
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
    environment:
      - discovery.type=single-node
```

---

### Master Prompt (for LLM use)
You are a senior AI platform architect.

Design and generate a production-grade GenAI Legal Document Intelligence system with the following requirements:

Architecture:
- FastAPI (async) for API layer
- Celery for background orchestration
- Redis as task broker
- PostgreSQL for logs and metadata
- ElasticSearch for search and indexing

Processing Pipeline:
1. User uploads a document
2. AWS Strands agent determines if document is legal
3. Deduplication agent avoids reprocessing duplicates
4. Contract type detection using CUAD taxonomy
5. Clause extraction using LLM
6. Named Entity Recognition using a deep learning NER model
7. Store clause text and NER entities in two separate ElasticSearch indexes

Design Requirements:
- Agent-based architecture
- Modular LLM abstraction (pluggable providers)
- Prompts stored as text files
- Prompt variables stored as JSON files
- Dynamic prompt loading
- Robust error handling with retries
- Exponential backoff retry strategy
- Resume processing from last successful step
- Automatic file deletion after successful processing
- Detailed logging stored in PostgreSQL
- Docker-compose setup
- All agents implemented in AWS Strands
- MCP servers introduced where needed for prompt/schema/routing management

Code Quality:
- Clean folder structure
- Well-commented
- Interview-ready
- Production-grade patterns

Return:
- Full folder structure
- Key code files
- Architecture explanation
- Retry and failure handling logic
