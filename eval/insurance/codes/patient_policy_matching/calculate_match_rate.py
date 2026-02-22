import pandas as pd
import os
import re

def calculate_match_rate(csv_path):
    '''Calculate the match rate from the CSV file.'''
    df = pd.read_csv(csv_path)
    df["matched"] = pd.to_numeric(df["matched"], errors="coerce").fillna(0).astype(int) # errors="coerce" ignore bugs
    total_cases = len(df)
    matched_cases = int(df["matched"].sum())
    match_rate = float(matched_cases / total_cases) if total_cases > 0 else 0.0
    return match_rate, matched_cases, int(total_cases)

def combine_match_rate(pairs, output_csv):
    """Combine match rates from multiple CSV files."""
    rows = []
    for retrieval_model, qna_model, retrieval_count, top_k, csv_path in pairs:
        match_rate, matched_cases, total_cases = calculate_match_rate(csv_path)
        rows.append({
            "retrieval_model": retrieval_model,
            "qna_model": qna_model, 
            "retrieval_count": int(retrieval_count),
            "top_k": int(top_k),
            "match_rate": match_rate,
            "matched_cases": matched_cases,
            "total_cases": total_cases
        })

    combined_df = pd.DataFrame(rows)
    combined_df.to_csv(output_csv, index=False)
    return combined_df

# entry function
if __name__ == "__main__": # only execute directly (not import)
    # test match rate calculation and combination
    import tempfile
    tmpdir = tempfile.mkdtemp(prefix="matchrate_")

    case_ids = [f"C{i}" for i in range(1, 6)]

    df1 = pd.DataFrame({"case_id": case_ids, "matched": [1,0,1,1,1]})
    p1 = os.path.join(tmpdir, "modelA_top3.csv")
    df1.to_csv(p1, index=False)

    df2 = pd.DataFrame({"case_id": case_ids, "matched": [0,1,0,1,0]})
    p2 = os.path.join(tmpdir, "modelB_top5.csv")
    df2.to_csv(p2, index=False)


    mr1 = calculate_match_rate(p1)  
    mr2 = calculate_match_rate(p2)  
    assert mr1 == (0.8, 4, 5)
    assert mr2 == (0.4, 2, 5)
   

    pairs = [
        ("modelA", 3, p1),
        ("modelB", 5, p2),
    ]
    out_csv = os.path.join(tmpdir, "combined.csv")
    result = combine_match_rate(pairs, out_csv)
    assert result.shape[0] == 2
    assert result.shape[1] == 5 

    print("combined:", out_csv)
    print(result)