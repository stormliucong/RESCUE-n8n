import os
import json
import hashlib
import numpy as np
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

path = '/home/cptaswadu/new-rescue/RESCUE-n8n'
load_dotenv(dotenv_path=os.path.join(path, ".env"))
openai_api_key = os.getenv("OPEN_AI_API_KEY")
chatgpt_agent = OpenAI(api_key=openai_api_key)

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

if __name__ == "__main__":
    import tempfile
    from load_policy import load_policies, calculate_pdf_md5
    BASE_DIR = '/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset'
    POLICY_FOLDER = os.path.join(BASE_DIR, 'policy_answer_real')
    CACHE_DIR = os.path.join(BASE_DIR, 'embeddings_cache')
    
    # headers_ex = {
    #     "BCBS_FEP_20402 Germline Genetic Testing for.pdf": "Guidelines section: Comprehensive V ariant Analysis). Individuals with any close blood relative with a known BRCA1 , BRCA2 , or PALB2  pathogenic/likely pathogenic variant (see Policy Guidelines Individuals meeting the criteria below but with previous limited testing ( eg, single gene and/or absent deletion duplication analysis) ≥1 close relative (see Policy Guidelines) with breast, ovarian, pancreatic, or prostate cancer at any age; or Triple-negative breast cancer (see Policy Guidelines) Metastatic or intraductal/cribriform prostate cancer , or high-risk group or very-high-risk group (see Policy Guidelines) (See Policy Guidelines section: Testing Unaf fected Individuals.) Genetic testing for BRCA1,  BRCA2,  and PALB2  variants of cancer-unaf fected individuals and individuals with cancer but not meeting the above criteria An individual with or without cancer and not meeting the above criteria but who has a 1st- or 2nd-degree blood relative meeting any criterion listed above for Patients With Cancer (except individuals who meet criteria only for systemic therapy decision-making). If the individual with An individual with any type of cancer (cancer related to hereditary breast and ovarian cancer syndrome but not meeting above criteria, or cancer unrelated to hereditary breast and ovarian cancer syndrome) or unaf fected individual who otherwise does not meet the criteria above criteria above are not met is considered investigational . Testing for PALB2  variants in individuals who do not meet the criteria outlined above is considered investigational . (see Policy Guidelines). POLICY  GUIDELINES Plans may need to alter local coverage medical policy to conform to state law regarding coverage of biomarker testing. Risk Assessment: Breast, Ovarian, and Pancreatic ( v .3.2024). Not all of the NCCN criteria are clearly separated for determining hereditary breast and ovarian cancer syndrome versus for guiding therapy . Testing for BRCA1, BRCA2,  and/or PALB2  outside of the above criteria, such as testing all respectively . Genetic testing for PALB2  variants in pancreatic cancer-af fected individuals is also addressed in 2.04.148. Additionally , conflicting criteria reflect that some of the NCCN criteria are based on limited or no evidence; the lower level of evidence might be needed when determining coverage of Current U.S. Preventive Services Task Force guidelines recommend screening women with a personal or family history of breast, ovarian, tubal, or Individuals who meet criteria for genetic testing as outlined in the policy statements above should be tested for variants in BRCA1,  BRCA2,  and Ashkenazi ethnicity (or if other BRCA1/2  testing criteria are met), comprehensive genetic testing should be considered. Testing strategy may also include testing individuals not meeting the above criteria who are adopted and have limited medical information on biological repeat testing for the rearrangements (see Policy section for criteria).",
    #     "Cigna_MOL.TS_.150A_CMA_for_Developmental_Disorders_and_Prenatal_Diagnosis_eff01.01.2025_pub09.10.2024_1.pdf": "Lab Management Guidelines V1.0.2025 Criteria the prenatal and postnatal setting are reviewed using the following criteria. Criteria Lab Management Guidelines V1.0.2025 Lab Management Guidelines V1.0.2025 test based on clinical history will be considered for coverage. If CMA has been necessary. Each test may require medical necessity review. criteria for CMA are met. This approval may be subject to claims review to ensure Testing by Multigene Panels  clinical use guideline; do not apply the criteria in this Lab Management Guidelines V1.0.2025 Lab Management Guidelines V1.0.2025"
    # }
    # md5s_ex = {"BCBS_FEP_20402 Germline Genetic Testing for.pdf": "0"*32, "Cigna_MOL.TS_.150A_CMA_for_Developmental_Disorders_and_Prenatal_Diagnosis_eff01.01.2025_pub09.10.2024_1.pdf": "1"*32}

    # cache_dir = tempfile.mkdtemp(prefix="emb_cache_")

    # emb, names, vecs = embed_policies_from_headers(headers_ex, md5s_ex, cache_dir, embedder_id="all-MiniLM-L6-v2")

    # assert set(names) == set(headers_ex) and vecs.shape[0] == len(names)
    # assert np.allclose(np.linalg.norm(vecs, axis=1), 1.0, atol=1e-3)  

    # _ = embed_policies_from_headers(headers_ex, md5s_ex, cache_dir, embedder_id="all-MiniLM-L6-v2")

    path = '/home/cptaswadu/new-rescue/RESCUE-n8n'
    load_dotenv(dotenv_path=os.path.join(path, ".env"))
    openai_api_key = os.getenv("OPEN_AI_API_KEY")
    chatgpt_agent = OpenAI(api_key=openai_api_key)

    policies, md5s, headers = load_policies(POLICY_FOLDER)
    emb, names, vecs = embed_policies_from_headers(
        headers=policies,
        md5s=md5s,
        cache_dir=CACHE_DIR,
        embedder_id="text-embedding-3-small",
        cache_suffix="openai_example2"
    )
    assert vecs.shape[0] == len(headers)
    print(vecs.shape)