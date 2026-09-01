from agent.retriever import retrieve_chunks, retrieve_images
from agent.generator import generate_response
from agent.judge import evaluate_layer_3

# Answer Mode -> retrieval breadth. Strict tightens to traceable evidence;
# Exploratory widens to surface more material for broader connections.
MODE_TOP_K = {
    "Strict Corpus-Only": 8,
    "Corpus + Background": 15,
    "Exploratory": 25,
}

def run_pipeline(query: str, max_retries: int = 2, mode: str = "Strict Corpus-Only") -> dict:
    """
    Orchestrates the entire sequence:
    1. Retrieve text chunks & metadata
    2. Generate Response
    3. Evaluate Layer 3 string via Judge
    4. Regenerate with penalty feedback if evaluated as weak
    5. Retrieve semantically relevant images from Qdrant

    `mode` is the UI Answer Mode; it controls retrieval breadth here and is passed
    to the generator to control corpus-grounding strictness and temperature.
    """
    top_k = MODE_TOP_K.get(mode, 15)
    print(f"Retrieving chunks for query: '{query}' (mode={mode}, top_k={top_k})")
    try:
        chunks = retrieve_chunks(query, top_k=top_k)
        print(f"Retrieved {len(chunks)} text chunks from Qdrant.")
    except Exception as e:
        print(f"Retrieval error (likely db off or path issues): {e}")
        chunks = []
        
    rejection_feedback = None
    payload = {}

    for attempt in range(max_retries):
        print(f"LLM Processing 3-Layer Response (Attempt {attempt+1}/{max_retries})...")
        payload = generate_response(query, chunks, rejection_feedback, mode=mode)

        layer_3 = payload.get("layer_3_transparency", "")

        print("Judge is evaluating Layer 3 Specificity...")
        is_valid, feedback = evaluate_layer_3(layer_3)

        if is_valid:
            print("-> Judge Evaluation: VALID. Output meets Mission 4 standards.")
            break
        else:
            print(f"-> Judge Evaluation: WEAK. Boilerplate detected.\nFeedback: {feedback}")
            rejection_feedback = feedback

    else:
        print("Maximum retries over. Yielding final generated state.")

    payload["retrieved_chunks"] = chunks

    print("Retrieving semantically relevant images from Qdrant...")
    try:
        image_hits = retrieve_images(query, top_k=3)
        if not image_hits:
            raise ValueError("No Qdrant image results — falling back to keyword extraction.")
        payload["retrieved_images"] = image_hits
        print(f"Retrieved {len(image_hits)} images via semantic search.")
    except Exception as e:
        print(f"Image semantic retrieval failed ({e}), using keyword fallback.")
        payload["retrieved_images"] = []

    return payload
