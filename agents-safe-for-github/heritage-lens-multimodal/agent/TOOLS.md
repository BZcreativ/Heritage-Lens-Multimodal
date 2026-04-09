# Heritage Lens Multimodal - Available Tools

## Tool Categories

### 1. Retrieval Tools

#### `search_text`
Search indexed text documents using semantic similarity.

**Parameters:**
- `query` (string): Search query
- `top_k` (int, optional): Number of results (default: 5)
- `threshold` (float, optional): Minimum similarity score

**Returns:**
- List of text chunks with metadata

**Example:**
```json
{
  "query": "Olmec colossal heads",
  "top_k": 5
}
```

---

#### `search_images`
Search indexed images using CLIP embeddings (if available).

**Parameters:**
- `query` (string): Search query
- `top_k` (int, optional): Number of results (default: 3)
- `threshold` (float, optional): Minimum similarity score

**Returns:**
- List of images with metadata and similarity scores

**Availability:** Requires vision dependencies

**Example:**
```json
{
  "query": "Maya hieroglyphics",
  "top_k": 3
}
```

---

#### `page_aware_match`
Match images to text chunks based on page proximity.

**Parameters:**
- `text_chunks` (list): Retrieved text chunks
- `images` (list): Retrieved images
- `tolerance` (int, optional): Page distance tolerance (default: 2)

**Returns:**
- Images scored by page proximity to text

---

### 2. Synthesis Tools

#### `synthesize_answer`
Generate Layer 1 (Answer) from retrieved context.

**Parameters:**
- `query` (string): Original query
- `text_chunks` (list): Retrieved text chunks
- `images` (list, optional): Retrieved images
- `conversation_history` (list, optional): Previous messages

**Returns:**
- Generated answer with inline citations

---

#### `generate_attribution`
Generate Layer 2 (Source Attribution).

**Parameters:**
- `text_chunks` (list): Retrieved text chunks
- `images` (list, optional): Retrieved images

**Returns:**
- Structured source list with metadata

---

### 3. Epistemic Analysis Tools

#### `analyze_biases`
Analyze sources for perspective biases.

**Parameters:**
- `text_chunks` (list): Text sources
- `images` (list, optional): Image sources

**Returns:**
- Bias analysis report

---

#### `calculate_confidence`
Calculate confidence metrics based on source diversity.

**Parameters:**
- `text_chunks` (list): Text sources
- `images` (list, optional): Image sources

**Returns:**
- Confidence scores and metrics

---

#### `identify_gaps`
Identify knowledge gaps in available sources.

**Parameters:**
- `query` (string): Original query
- `text_chunks` (list): Retrieved text
- `answer` (string): Generated answer

**Returns:**
- List of identified gaps

---

### 4. Vision Tools

#### `encode_image`
Generate CLIP embedding for an image (if available).

**Parameters:**
- `image_path` (string): Path to image file

**Returns:**
- Embedding vector

**Availability:** Requires vision dependencies

---

#### `add_image`
Index a new image to the knowledge base (if available).

**Parameters:**
- `image_path` (string): Path to image file
- `metadata` (dict, optional): Image metadata

**Returns:**
- Success status

**Availability:** Requires vision dependencies

---

### 5. Quality Control Tools

#### `evaluate_output`
Evaluate complete 3-layer output quality.

**Parameters:**
- `query` (string): Original query
- `l1_answer` (string): Layer 1 answer
- `l2_attribution` (dict): Layer 2 attribution
- `l3_epistemic` (dict): Layer 3 epistemic analysis
- `retrieval_stats` (dict): Retrieval statistics

**Returns:**
- Verdict and confidence score

---

#### `check_image_relevance`
Check if retrieved images are relevant to query.

**Parameters:**
- `query` (string): Original query
- `answer` (string): Generated answer
- `images` (list): Retrieved images

**Returns:**
- Relevance assessment

---

### 6. Session Management Tools

#### `get_session_history`
Retrieve conversation history for a session.

**Parameters:**
- `session_id` (string): Session identifier

**Returns:**
- List of previous messages

---

#### `update_session`
Update conversation history with new exchange.

**Parameters:**
- `session_id` (string): Session identifier
- `query` (string): User query
- `answer` (string): Assistant answer

**Returns:**
- Updated history

---

### 7. Configuration Tools

#### `get_config`
Get current system configuration.

**Parameters:**
- `section` (string, optional): Specific config section

**Returns:**
- Configuration dictionary

---

#### `get_stats`
Get system statistics.

**Returns:**
- Statistics including indexed documents, sessions, etc.

---

## Tool Usage Patterns

### Standard Query Flow
```
1. search_text(query) → text_chunks
2. search_images(query) → images (optional)
3. page_aware_match(text_chunks, images) → matched_images (optional)
4. synthesize_answer(query, text_chunks, matched_images) → l1_answer
5. generate_attribution(text_chunks, matched_images) → l2_attribution
6. analyze_biases(text_chunks, matched_images) → bias_analysis
7. calculate_confidence(text_chunks, matched_images) → confidence
8. identify_gaps(query, text_chunks, l1_answer) → gaps
9. evaluate_output(query, l1, l2, l3, stats) → verdict
```

### Revision Flow
```
If verdict != "accept":
  - If revision_strategy == "retrieval":
    → search_text(query, top_k=increased) → new_chunks
    → search_images(query, top_k=increased) → new_images
  - If revision_strategy == "synthesis":
    → synthesize_answer(query, chunks, images, feedback) → revised_answer
  - Re-evaluate → new_verdict
```

## Tool Availability Matrix

| Tool | Core Mode | Full Mode | Degraded |
|------|-----------|-----------|----------|
| search_text | ✓ | ✓ | ✓ |
| search_images | ✗ | ✓ | ✗ |
| page_aware_match | ✗ | ✓ | ✗ |
| synthesize_answer | ✓ | ✓ | ✓ |
| generate_attribution | ✓ | ✓ | ✓ |
| analyze_biases | ✓ | ✓ | ✓ |
| calculate_confidence | ✓ | ✓ | ✓ |
| identify_gaps | ✓ | ✓ | ✓ |
| encode_image | ✗ | ✓ | ✗ |
| add_image | ✗ | ✓ | ✗ |
| evaluate_output | ✓ | ✓ | ✗ |
| check_image_relevance | ✗ | ✓ | ✗ |
| get_session_history | ✓ | ✓ | ✓ |
| update_session | ✓ | ✓ | ✓ |
| get_config | ✓ | ✓ | ✓ |
| get_stats | ✓ | ✓ | ✓ |

## Error Handling

All tools follow graceful degradation:
- If a tool is unavailable, return empty result with explanation
- Never crash the entire system due to one tool failure
- Log errors for debugging
- Provide fallback options to user

## Tool Dependencies

### Core Dependencies (Always Required)
- llama_index
- qdrant_client
- openai
- pyyaml

### Optional Dependencies (For Full Mode)
- sentence_transformers
- Pillow (PIL)
- PyMuPDF (fitz)
- torch

## Tool Configuration

Tools read configuration from `config/settings.yaml`:
- `retrieval.text.top_k`: Default text results
- `retrieval.image.top_k`: Default image results
- `llm.synthesis.*`: Synthesis LLM settings
- `llm.epistemic.*`: Epistemic LLM settings
- `llm.critic.*`: Critic LLM settings
- `multimodal.enabled`: Master feature flag
- `multimodal.vision.enabled`: Vision feature flag
