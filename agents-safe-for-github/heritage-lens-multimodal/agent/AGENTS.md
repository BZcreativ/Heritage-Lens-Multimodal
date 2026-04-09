# Heritage Lens Multimodal - Agent Definitions

This file defines all sub-agents and their capabilities for the Heritage Lens Multimodal system.

## Agent Hierarchy

```
EnhancedOrchestrator (Coordinator)
├── MultimodalRetrievalAgent
│   └── OptionalVisionService (graceful degradation)
├── MultimodalSynthesisAgent
├── EnhancedEpistemicAgent
├── MultimodalCriticAgent
└── VisionAgent
```

## Agent Definitions

### 1. EnhancedOrchestrator
**Role:** Central coordinator for all heritage queries
**Type:** kimberley-orchestrator
**Responsibilities:**
- Route queries to appropriate sub-agents
- Coordinate 3-layer output generation
- Manage conversation history and sessions
- Handle revision loops based on critic feedback

**Capabilities:**
- text_retrieval
- image_retrieval
- multimodal_synthesis
- epistemic_analysis
- quality_control
- session_management

**Decision Authority:** High - can override sub-agent outputs

---

### 2. MultimodalRetrievalAgent
**Role:** Retrieve relevant text and images from knowledge base
**Type:** kimberley-retriever
**Responsibilities:**
- Search text chunks using LlamaIndex + Qdrant
- Search images using CLIP embeddings
- Perform page-aware matching between text and images
- Return unified retrieval results

**Capabilities:**
- semantic_search
- hybrid_search
- image_similarity_search
- page_aware_matching

**Decision Authority:** Low - provides raw data

---

### 3. MultimodalSynthesisAgent
**Role:** Generate Layer 1 (Answer) and Layer 2 (Attribution)
**Type:** kimberley-synthesizer
**Responsibilities:**
- Synthesize coherent answers from text and image context
- Generate source attributions with citations
- Format output for human readability
- Handle conversation context

**Capabilities:**
- text_synthesis
- multimodal_reasoning
- source_citation
- conversation_memory

**Decision Authority:** Medium - generates primary output

---

### 4. EnhancedEpistemicAgent
**Role:** Generate Layer 3 (Epistemic Transparency)
**Type:** kimberley-auditor
**Responsibilities:**
- Analyze textual sources for bias and perspective
- Analyze visual sources for representation gaps
- Calculate confidence metrics
- Identify knowledge gaps and uncertainties

**Capabilities:**
- bias_detection
- perspective_analysis
- visual_bias_analysis
- confidence_scoring
- gap_identification

**Decision Authority:** Medium - provides critical analysis

---

### 5. MultimodalCriticAgent
**Role:** Evaluate output quality and trigger revisions
**Type:** kimberley-critic
**Responsibilities:**
- Evaluate answer quality, attribution completeness, and epistemic rigor
- Check image relevance to query
- Determine if revision is needed
- Select revision strategy (retrieval, synthesis, epistemic, vision)

**Capabilities:**
- quality_evaluation
- revision_triggering
- image_relevance_check
- strategy_selection

**Decision Authority:** High - can trigger revision loops

---

### 6. VisionAgent
**Role:** Handle image-specific operations
**Type:** kimberley-vision
**Responsibilities:**
- Index images with CLIP embeddings
- Search images by text query
- Cache embeddings for performance
- Provide image metadata

**Capabilities:**
- image_embedding
- image_search
- image_caching
- metadata_extraction

**Decision Authority:** Low - specialized tool

---

## Communication Patterns

### Standard Flow
```
Query → RetrievalAgent → SynthesisAgent → EpistemicAgent → CriticAgent
                                            ↓ (if revision needed)
                                    ← Revision Loop ←
```

### Revision Flow
```
CriticAgent detects issue
  ↓
Determine revision strategy
  ↓
Re-run targeted agent(s)
  ↓
Re-evaluate with CriticAgent
```

## Specialization Areas

### Cultural Heritage Focus
All agents specialize in Mesoamerican civilizations:
- Olmec (1500-400 BCE)
- Maya (2000 BCE - 900 CE)
- Aztec (1300-1521 CE)
- Mixtec (1500 BCE - 1523 CE)
- Zapotec (700 BCE - 1521 CE)

### Bias Awareness Priorities
1. Colonial vs. indigenous perspectives
2. Western academic vs. local knowledge
3. Temporal bias (modern interpretation of ancient cultures)
4. Geographic bias (museum collections vs. origin contexts)
5. Visual representation gaps

## Graceful Degradation

When vision dependencies are unavailable:
- VisionAgent returns empty results
- RetrievalAgent falls back to text-only
- SynthesisAgent formats text-only responses
- EpistemicAgent skips visual bias analysis
- CriticAgent skips image relevance checking
- Full system continues operating in text-only mode
