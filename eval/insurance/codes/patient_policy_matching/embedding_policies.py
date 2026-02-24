import os
import hashlib
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def embed_policies_from_headers(headers: dict, md5s: dict, cache_dir: str, embedder_id: str = "all-MiniLM-L6-v2",
                                cache_suffix: str = ""):
    """Embed policy documents from their headers."""
    # corpus hash
    items = [f"{name}:{md5s[name]}" for name in sorted(headers.keys())]
    corpus_key = f"{embedder_id}\n" + "\n".join(items)
    corpus_hash = hashlib.md5(corpus_key.encode("utf-8")).hexdigest()
    embedder_dir = embedder_id + (f"_{cache_suffix}" if cache_suffix else "")
    cache_root = os.path.join(cache_dir, embedder_dir, corpus_hash)
    os.makedirs(cache_root, exist_ok=True)
    names_path = os.path.join(cache_root, "doc_names.json")
    vecs_path  = os.path.join(cache_root, "embeddings.npy")

    # load cache
    if os.path.exists(names_path) and os.path.exists(vecs_path):
        try:
            with open(names_path, "r", encoding="utf-8") as f:
                names = json.load(f)
            vecs = np.load(vecs_path)
            if len(names) == len(headers) and set(names) == set(headers.keys()):
                emb = {name: vecs[i] for i, name in enumerate(names)}
                print(f"Loaded embeddings from cache ({len(names)} docs).")
                return emb, names, vecs
        except Exception as e:
            print(f"Failed to load cache. Recomputing… ({e})")

    # calculate new embeddings
    names = sorted(headers.keys())

    if embedder_id.startswith("text-embedding"):
        client = OpenAI(api_key=os.getenv("OPEN_AI_API_KEY"))
        encoding = tiktoken.encoding_for_model(embedder_id)
        
        corpus = []
        chunk_info = {}
        max_token = 8100

        for n in names:
            text = (headers[n] or "").strip()

            tokens = encoding.encode(text)
            chunks = []

            for i in range(0, len(tokens), max_token):
                chunk_tokens = tokens[i:i+max_token]
                chunk_text = encoding.decode(chunk_tokens)
                if chunk_text.strip():
                    chunks.append(chunk_text)

            if not chunks:
                chunks = [""]
            
            corpus.extend(chunks)
            chunk_info[n] = len(chunks)
    
        print(f"[SUMMARY] total_chunks={sum(chunk_info.values())}, corpus_len={len(corpus)}")

        batch_size = 35
        all_vecs = []

        for i in range(0, len(corpus), batch_size):
            batch = corpus[i:i+batch_size]
            try:
                response = client.embeddings.create(input=batch, model=embedder_id)
                batch_vecs = [item.embedding for item in response.data]
                all_vecs.extend(batch_vecs)

            except Exception as e:
                print(f"Error in batch {i//batch_size + 1}: {e}")
                raise
    
        vecs = np.array(all_vecs, dtype=np.float32)

        final_vecs = []
        idx = 0
        for n in names:
            k = chunk_info[n]
            if k == 1:
                v = vecs[idx]
                final_vecs.append(v / (np.linalg.norm(v) + 1e-12))
            else:
                v = vecs[idx:idx+k].mean(axis=0)
                final_vecs.append(v / (np.linalg.norm(v) + 1e-12))
            idx += k
    
        final_vecs = np.array(final_vecs, dtype=np.float32)

    else:
        model = SentenceTransformer(embedder_id)

        corpus = []
        chunk_info = {}
        max_seen = 0

        for n in names:
            text = (headers[n] or "").strip()
            enc = model.tokenizer(
                text,
                add_special_tokens=True,
                truncation=True,
                max_length=256,
                return_overflowing_tokens=True
            )
            ids_batches = enc["input_ids"] if isinstance(enc["input_ids"][0], list) else [enc["input_ids"]]
            ids_batches = [ids[:256] for ids in ids_batches]
            chunks = model.tokenizer.batch_decode(ids_batches, skip_special_tokens=True, clean_up_tokenization_spaces=True)
            corpus.extend(chunks)
            chunk_info[n] = len(chunks)

            max_seen = max(max_seen, *(len(ids) for ids in ids_batches))
            #print(f"total_chunks={sum(chunk_info.values())}, corpus_len={len(corpus)}")
            #print(f"[DEBUG] longest_chunk_tokens={max_seen}  (should be <= 256)")

        print(f"[SUMMARY] total_chunks={sum(chunk_info.values())}, corpus_len={len(corpus)}")
        vecs = model.encode(corpus, show_progress_bar=False, normalize_embeddings=True).astype(np.float32)

        final_vecs = []
        idx = 0
        for n in names:
            k = chunk_info[n]
            if k == 1:
                v = vecs[idx]
                final_vecs.append(v / (np.linalg.norm(v) + 1e-12))
            else:
                v = vecs[idx:idx+k].mean(axis=0)
                final_vecs.append(v / (np.linalg.norm(v) + 1e-12))
            idx += k

        final_vecs = np.array(final_vecs, dtype=np.float32)

    try:
        #print(f"[DEBUG] final_vecs.shape={final_vecs.shape}")
        #if len(final_vecs) > 0:
            #print(f"[DEBUG] norms(sample)={np.linalg.norm(final_vecs[:3], axis=1)}")
        with open(names_path, "w", encoding="utf-8") as f:
            json.dump(names, f, ensure_ascii=False)
        np.save(vecs_path, final_vecs)
        print(f"Embeddings created & cached ({len(names)} docs).")
    except Exception as e:
        print(f"Failed to write cache: {e}")

    emb = {name: final_vecs[i] for i, name in enumerate(names)}
    return emb, names, final_vecs