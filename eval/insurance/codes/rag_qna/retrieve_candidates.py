import os
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from embedding_policies import embed_policies_from_headers

path = '/home/cptaswadu/new-rescue/RESCUE-n8n'
load_dotenv(dotenv_path=os.path.join(path, ".env"))
openai_api_key = os.getenv("OPEN_AI_API_KEY")
chatgpt_agent = OpenAI(api_key=openai_api_key)

def cosine_topk(vecs, qv, k, vecs_normalized=True, eps=1e-12): # simulate 
    a = np.asarray(vecs, dtype=np.float32)      
    q = np.asarray(qv,  dtype=np.float32).ravel()  
    if not vecs_normalized:
        a = a / (np.linalg.norm(a, axis=1, keepdims=True) + eps)

    q = q / (np.linalg.norm(q) + eps)
    scores = a @ q
    
    if k >= len(scores):
        idx = np.argsort(-scores)
    else:
        part = np.argpartition(-scores, k-1)[:k]
        idx = part[np.argsort(-scores[part])]
    return idx, scores[idx]

def retrieve_candidates(vecs, names, query_text, doc_texts=None, embedder_id="all-MiniLM-L6-v2", vecs_normalized=True, k=10):
    '''Retrieve candidate policy documents based on cosine similarity.'''
    if embedder_id.startswith("text-embedding"):
        client = OpenAI(api_key=os.getenv("OPEN_AI_API_KEY"))
        response = client.embeddings.create(input=query_text, model=embedder_id)
        qv = np.array(response.data[0].embedding).astype(np.float32)
    else:
        model = SentenceTransformer(embedder_id, local_files_only=True)
        qv = model.encode([query_text], normalize_embeddings=False)[0].astype(np.float32)

    idx, sc = cosine_topk(vecs, qv, k, vecs_normalized=vecs_normalized)
    texts = doc_texts or {}
    return [(names[i], float(s), texts.get(names[i], "")) for i, s in zip(idx, sc)]

if __name__ == "__main__":
    import tempfile
    model = SentenceTransformer("all-MiniLM-L6-v2")

    A = np.array([
        [1,0,0,0,0],
        [1,1,0,0,0],
        [1,1,1,0,0],
        [0,0,0,1,1],
        [0,0,0,1,0],
    ], dtype=np.int32)

    q = np.array([1,1,1,0,0], dtype=np.int32)

    idx, sc = cosine_topk(A, q, k=3, vecs_normalized=False)  
    assert idx.tolist() == [2,1,0]

    headers_ex = {
        "BCBS_FEP_20402 Germline Genetic Testing for.pdf": "Guidelines section: Comprehensive Variant Analysis). Individuals with any close blood relative with a known BRCA1 , BRCA2 , or PALB2  pathogenic/likely pathogenic variant (see Policy Guidelines Individuals meeting the criteria below but with previous limited testing ( eg, single gene and/or absent deletion duplication analysis) ≥1 close relative (see Policy Guidelines) with breast, ovarian, pancreatic, or prostate cancer at any age; or Triple-negative breast cancer (see Policy Guidelines) Metastatic or intraductal/cribriform prostate cancer , or high-risk group or very-high-risk group (see Policy Guidelines) (See Policy Guidelines section: Testing Unaffected Individuals.) Genetic testing for BRCA1,  BRCA2,  and PALB2  variants of cancer-unaffected individuals and individuals with cancer but not meeting the above criteria An individual with or without cancer and not meeting the above criteria but who has a 1st- or 2nd-degree blood relative meeting any criterion listed above for Patients With Cancer (except individuals who meet criteria only for systemic therapy decision-making). If the individual with An individual with any type of cancer (cancer related to hereditary breast and ovarian cancer syndrome but not meeting above criteria, or cancer unrelated to hereditary breast and ovarian cancer syndrome) or unaffected individual who otherwise does not meet the criteria above criteria above are not met is considered investigational . Testing for PALB2  variants in individuals who do not meet the criteria outlined above is considered investigational . (see Policy Guidelines). POLICY  GUIDELINES Plans may need to alter local coverage medical policy to conform to state law regarding coverage of biomarker testing. Risk Assessment: Breast, Ovarian, and Pancreatic ( v .3.2024). Not all of the NCCN criteria are clearly separated for determining hereditary breast and ovarian cancer syndrome versus for guiding therapy . Testing for BRCA1, BRCA2,  and/or PALB2  outside of the above criteria, such as testing all respectively . Genetic testing for PALB2  variants in pancreatic cancer-affected individuals is also addressed in 2.04.148. Additionally , conflicting criteria reflect that some of the NCCN criteria are based on limited or no evidence; the lower level of evidence might be needed when determining coverage of Current U.S. Preventive Services Task Force guidelines recommend screening women with a personal or family history of breast, ovarian, tubal, or Individuals who meet criteria for genetic testing as outlined in the policy statements above should be tested for variants in BRCA1,  BRCA2,  and Ashkenazi ethnicity (or if other BRCA1/2  testing criteria are met), comprehensive genetic testing should be considered. Testing strategy may also include testing individuals not meeting the above criteria who are adopted and have limited medical information on biological repeat testing for the rearrangements (see Policy section for criteria).",
        "Cigna_MOL.TS_.150A_CMA_for_Developmental_Disorders_and_Prenatal_Diagnosis_eff01.01.2025_pub09.10.2024_1.pdf": "Lab Management Guidelines V1.0.2025 Criteria the prenatal and postnatal setting are reviewed using the following criteria. Criteria Lab Management Guidelines V1.0.2025 Lab Management Guidelines V1.0.2025 test based on clinical history will be considered for coverage. If CMA has been necessary. Each test may require medical necessity review. criteria for CMA are met. This approval may be subject to claims review to ensure Testing by Multigene Panels  clinical use guideline; do not apply the criteria in this Lab Management Guidelines V1.0.2025 Lab Management Guidelines V1.0.2025"
    }
    md5s_ex = {"BCBS_FEP_20402 Germline Genetic Testing for.pdf": "0"*32, "Cigna_MOL.TS_.150A_CMA_for_Developmental_Disorders_and_Prenatal_Diagnosis_eff01.01.2025_pub09.10.2024_1.pdf": "1"*32}

    cache_dir = tempfile.mkdtemp(prefix="emb_cache_")

    emb, names, vecs = embed_policies_from_headers(headers_ex, md5s_ex, cache_dir, embedder_id="all-MiniLM-L6-v2")

    k = 1
    res = retrieve_candidates(vecs, names, "CMA coverage criteria",
                          doc_texts=headers_ex, embedder_id="all-MiniLM-L6-v2",
                          vecs_normalized=True, k=k)

    assert res[0][0] == "Cigna_MOL.TS_.150A_CMA_for_Developmental_Disorders_and_Prenatal_Diagnosis_eff01.01.2025_pub09.10.2024_1.pdf"
    assert res[0][2] == headers_ex["Cigna_MOL.TS_.150A_CMA_for_Developmental_Disorders_and_Prenatal_Diagnosis_eff01.01.2025_pub09.10.2024_1.pdf"]   