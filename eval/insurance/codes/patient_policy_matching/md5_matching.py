import os
from retrieve_candidates import retrieve_candidates

def md5_match_by_rerank_order(
    candidates, order, md5s, expected_md5,
    save_dir=None, case_id=None, retrieval_model=None, top_k=None,
    embedding_matrix=None, doc_names=None, query_text=None, embedder_id="text-embedding-3-small"
): 
    '''Check if the expected MD5 is in the reranked candidates, and optionally save stats.'''
    matched_name = None

    limit = top_k if top_k else len(order)
    for rpos, i in enumerate(order[:limit], start=1):
        name, _, _ = candidates[i]
        if md5s.get(name) == expected_md5:
            matched_name = name
            break

    matched = matched_name is not None

    llm_rank = None
    for rpos, i in enumerate(order, start=1):
        name, _, _ = candidates[i]
        if md5s.get(name) == expected_md5:
            llm_rank = rpos
            break

    # Check original ranking
    full_candidates = retrieve_candidates(embedding_matrix, doc_names, query_text, embedder_id=embedder_id, k=len(doc_names))
    orig_name, orig_rank_full = None, None
    for rank, (name, _, _) in enumerate(full_candidates, start=1):
        if md5s.get(name) == expected_md5:
            orig_name, orig_rank_full = name, rank
            break

    orig_rank_cand = None
    for cpos, (n, _, _) in enumerate(candidates, start=1):
        if md5s.get(n) == expected_md5:
            orig_rank_cand = cpos
            break        

    # Append a compact CSV row for match-rate stats
    if save_dir and case_id:
        parts = [save_dir, "retrieval"]
        if retrieval_model:
            parts.append(retrieval_model.replace("-", "_"))
        if top_k is not None:
            parts.append(f"top{int(top_k)}")
        final_dir = os.path.join(*parts)
        os.makedirs(final_dir, exist_ok=True)
        
        csv_path = os.path.join(final_dir, "matching_summary.csv")
        file_exists = os.path.exists(csv_path)

        with open(csv_path, "a", encoding="utf-8") as f:
            if not file_exists:
                f.write("case_id,matched,llm_rank,orig_rank_cand,orig_rank_full,doc_name\n")
            
            doc_name = matched_name or orig_name or ""
            matched_int = 1 if matched else 0
            llm_rank_str = llm_rank if llm_rank else ""
            orig_rank_cand_str = orig_rank_cand if orig_rank_cand else ""
            orig_rank_full_str = orig_rank_full if orig_rank_full else ""

            f.write(f"{case_id},{matched_int},{llm_rank_str},{orig_rank_cand_str},{orig_rank_full_str},{doc_name}\n")

        if matched and top_k and top_k > 1:
            top_k_docs = [candidates[order[i]][0] for i in range(min(top_k, len(order)))]

            top_k_path = os.path.join(final_dir, f"top{top_k}_docs.csv")    
            topk_exists = os.path.exists(top_k_path)
            with open(top_k_path, "a", encoding="utf-8") as tkf:
                if not topk_exists:
                    tkf.write("case_id,doc_names\n")

                doc_names_str = "|".join(top_k_docs)
                tkf.write(f"{case_id},{doc_names_str}\n")
        else:
            top_k_docs = None
    else:
        top_k_docs = None

    return matched_name, matched, llm_rank, top_k_docs

if __name__ == "__main__":
    import tempfile
    tmpdir = tempfile.mkdtemp(prefix="md5match_")

    candidates_ex2 = [
        ("Aetna_WES_2024.pdf", 0.9, "Coverage criteria: WES is medically necessary when"),
        ("UHC_WGS_2023.pdf",   0.8, "Medical necessity guidelines for WGS in UHC"),
        ("Cigna_WES_2023.pdf", 0.7, "WES coverage policy from Cigna"),
    ]
    order_ex2 = [2, 1, 0]  

    md5s_ex2 = {
        "Aetna_WES_2024.pdf": "a"*32,
        "UHC_WGS_2023.pdf":   "b"*32,
        "Cigna_WES_2023.pdf": "c"*32,
    }

    outA = md5_match_by_rerank_order(
        candidates_ex2, order_ex2, md5s_ex2, expected_md5="c"*32,
        save_dir=tmpdir, case_id="CaseA", retrieval_model="gpt-4o", top_k=1
    )

    outB = md5_match_by_rerank_order(
    candidates_ex2, order_ex2, md5s_ex2, expected_md5="b"*32,
    save_dir=tmpdir, case_id="CaseB", retrieval_model="gpt-4o", top_k=3
    )

    outC = md5_match_by_rerank_order(
    candidates_ex2, order_ex2, md5s_ex2, expected_md5="a"*32,
    save_dir=tmpdir, case_id="CaseC", retrieval_model="gpt-4o", top_k=1
    )

    base = os.path.join(tmpdir, "retrieval", "gpt_4o")

    for sub in ["top1", "top3"]:
        d = os.path.join(base, sub)
        if not os.path.isdir(d):
            continue
    
        for fn in os.listdir(d):
            path = os.path.join(d, fn)
            print(f"[{fn}]")
            with open(path, "r", encoding="utf-8") as f:
                print(f.read())

    assert outA == ("Cigna_WES_2023.pdf", True, 1, None)
    assert outB == ("UHC_WGS_2023.pdf", True, 2, ["Cigna_WES_2023.pdf", "UHC_WGS_2023.pdf", "Aetna_WES_2024.pdf"])
    assert outC == (None, False, 3, None)
