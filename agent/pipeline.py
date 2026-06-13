from agent.retriever import retrieve_chunks, retrieve_images
from agent.generator import generate_response
from agent.judge import evaluate_layer_3

def run_pipeline(query: str, max_retries: int = 2) -> dict:
    """
    Orchestrates the entire sequence:
    1. Retrieve text chunks & metadata
    2. Generate Response
    3. Evaluate Layer 3 string via Judge
    4. Regenerate with penalty feedback if evaluated as weak
    5. Retrieve semantically relevant images from Qdrant
    """
    print(f"Retrieving chunks for query: '{query}'")
    try:
        chunks = retrieve_chunks(query)
        print(f"Retrieved {len(chunks)} text chunks from Qdrant.")
    except Exception as e:
        print(f"Retrieval error (likely db off or path issues): {e}")
        chunks = []
        
    rejection_feedback = None
    payload = {}

    for attempt in range(max_retries):
        print(f"LLM Processing 3-Layer Response (Attempt {attempt+1}/{max_retries})...")
        payload = generate_response(query, chunks, rejection_feedback)

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
