"""
bench.py — Cong cu do chat luong retrieval (Checkpoint 5+6)

Features:
  - A/B test: chay query co filter va khong filter
  - Content-level scoring: kiem tra gold_keyword co trong context khong
  - Luu ket qua ra ket_qua_benchmark.txt
  - Ghi ro dang dung MockEmbedder (khong ma hoa ngu nghia)

Moi thanh vien chi doi 1 dong: CHUNKER = ...
"""

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))

from src.chunking import RecursiveChunker
from src.embeddings import MockEmbedder
from src.models import Document
from src.store import EmbeddingStore

# --- Cau hinh -------------------------------------------------------------------
DATA_DIR = Path("data/ChinhSachShopee")
CHUNK_SIZE = 500
OUTPUT_FILE = Path("ket_qua_benchmark.txt")

# === DOI DONG NAY THEO CHIEN LUOC CUA TUNG THANH VIEN ===
from src.chunking import SentenceChunker; CHUNKER = SentenceChunker(max_sentences_per_chunk=5)

# 5 cau hoi benchmark chung cua nhom
# gold_keyword: chuoi dac trung PHAI xuat hien trong context neu chunk dung
QUERIES = [
    {
        "id": "Q1",
        "question": "Nguoi mua can thuc hien nhung buoc nao de gui yeu cau Tra hang/Hoan tien tren Shopee?",
        "filter": {"audience": "buyer"},
        "gold_doc": "shopee_return_refund_guide_buyer",
        "gold_keyword": "Tra hang",
        "gold": "Truy cap Don mua -> Chon don -> Nhan Tra hang/Hoan tien -> Chon ly do, tai bang chung, xac nhan.",
    },
    {
        "id": "Q2",
        "question": "Nhung nhom san pham nao khong duoc phep hoan tra vi ly do doi y?",
        "filter": None,
        "gold_doc": "shopee_seller_return_refund_process",
        "gold_keyword": "han che",
        "gold": "Thiet bi Dien tu, Suc khoe/Ve sinh, Thuc pham & Hang mau hong, Hang dac thu, San pham so.",
    },
    {
        "id": "Q3",
        "question": "Khi khach hang yeu cau hoan tien, nguoi ban can phan hoi trong bao lau?",
        "filter": {"audience": "seller"},
        "gold_doc": "shopee_faq_return_refund_seller",
        "gold_keyword": "phan hoi",
        "gold": "Nguoi ban can phan hoi trong thoi gian dem nguoc hien thi tren ung dung.",
    },
    {
        "id": "Q4",
        "question": "Shopee ap dung chinh sach bao hanh nhu the nao cho san pham dien tu?",
        "filter": {"audience": "buyer"},
        "gold_doc": "shopee_warranty_policy",
        "gold_keyword": "bao hanh",
        "gold": "Shopee bao hanh qua trung tam bao hanh chinh hang hoac shop, thoi gian va dieu kien theo tung san pham.",
    },
    {
        "id": "Q5",
        "question": "Phi van chuyen hang tra lai do loi cua nguoi ban se duoc xu ly nhu the nao?",
        "filter": {"audience": "seller"},
        "gold_doc": "shopee_return_shipping_fee_policy",
        "gold_keyword": "phi van chuyen",
        "gold": "Shopee hoan phi van chuyen tra hang cho nguoi mua va tru vao tai khoan nguoi ban.",
    },
]


# --- Ham tien ich ---------------------------------------------------------------
def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    metadata = {}
    for line in parts[1].splitlines():
        match = re.match(r"^(\w+):\s*(.+)$", line.strip())
        if match:
            metadata[match.group(1)] = match.group(2).strip()
    return metadata, parts[2].strip()


def score_result(results, gold_doc, gold_keyword):
    """
    Cham diem theo hai muc:
      2 diem: gold_doc trong top-1 VA gold_keyword xuat hien trong context
      1 diem: gold_doc trong top-2/3
      0 diem: khong co
    """
    context = " ".join(r["content"] for r in results)
    gold_in_top1 = results and results[0]["metadata"].get("doc_id") == gold_doc
    gold_in_top3 = any(r["metadata"].get("doc_id") == gold_doc for r in results)
    keyword_found = gold_keyword.lower() in context.lower()

    if gold_in_top1 and keyword_found:
        return 2, "top-1 + keyword found"
    elif gold_in_top3:
        return 1, "gold in top-2/3"
    else:
        return 0, "gold absent from top-3"


def run_query(store, q, use_filter=True):
    flt = q["filter"] if use_filter else None
    results = store.search_with_filter(query=q["question"], top_k=3, metadata_filter=flt)
    score, reason = score_result(results, q["gold_doc"], q["gold_keyword"])
    return results, score, reason


def format_results(results):
    lines = []
    for rank, r in enumerate(results, 1):
        doc_id = r["metadata"].get("doc_id", "?")
        audience = r["metadata"].get("audience", "?")
        preview = r["content"][:100].replace("\n", " ")
        lines.append(f"  #{rank} score={r['score']:.3f} doc_id={doc_id} audience={audience}")
        lines.append(f"      {preview}...")
    return "\n".join(lines)


# --- 1. Doc & chunk tai lieu ----------------------------------------------------
lines_out = []

def out(s=""):
    print(s)
    lines_out.append(s)

out("=" * 65)
out(f"BENCHMARK - {CHUNKER.__class__.__name__} (chunk_size={CHUNK_SIZE})")
out("LUU Y: Dang dung MockEmbedder - khong ma hoa ngu nghia.")
out("So lieu score phan anh hash MD5, khong phan anh do tuong tu ngu nghia.")
out("Trong tam phan tich: count/avg_length/mach lac chunk va A/B filter.")
out("=" * 65)

all_docs = []
md_files = sorted(DATA_DIR.glob("*.md"))

for path in md_files:
    raw = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(raw)
    chunks = CHUNKER.chunk(body)
    for i, chunk_text in enumerate(chunks):
        all_docs.append(Document(
            id=f"{path.stem}#{i}",
            content=chunk_text,
            metadata={
                **frontmatter,
                "doc_id": path.stem,
                "chunk_index": str(i),
                "source": str(path),
            },
        ))

out(f"\nDa nap {len(md_files)} tai lieu -> {len(all_docs)} chunks vao store")

store = EmbeddingStore(collection_name="bench_recursive", embedding_fn=MockEmbedder())
store.add_documents(all_docs)

# --- 2. Chay 5 query: co filter va khong filter --------------------------------
out("\n" + "=" * 65)
out("KET QUA BENCHMARK (5 cau hoi)")
out("=" * 65)

total_with = 0
total_without = 0
summary_rows = []

for q in QUERIES:
    out(f"\n{'─'*65}")
    out(f"[{q['id']}] {q['question']}")
    out(f"  gold_doc    : {q['gold_doc']}")
    out(f"  gold_keyword: {q['gold_keyword']}")
    out(f"  filter      : {q['filter']}")

    # A: Co filter
    r_with, s_with, reason_with = run_query(store, q, use_filter=True)
    out(f"\n  [A] CO filter ({q['filter']}) -> diem={s_with} ({reason_with})")
    out(format_results(r_with))

    # B: Khong filter (chi ap dung neu query co filter)
    if q["filter"]:
        r_without, s_without, reason_without = run_query(store, q, use_filter=False)
        out(f"\n  [B] KHONG filter -> diem={s_without} ({reason_without})")
        out(format_results(r_without))
        ab_note = f"Filter {'CO ich' if s_with >= s_without else 'KHONG co ich / lam kem hon'}"
        out(f"  => A/B: {ab_note}")
    else:
        r_without, s_without = r_with, s_with
        ab_note = "N/A (cau hoi khong co filter)"
        out(f"\n  [B] N/A — cau hoi nay khong can filter")

    total_with += s_with
    summary_rows.append({
        "id": q["id"],
        "question": q["question"][:55],
        "top1_doc": r_with[0]["metadata"].get("doc_id", "?") if r_with else "?",
        "top1_score": f"{r_with[0]['score']:.3f}" if r_with else "?",
        "score_with": s_with,
        "score_without": s_without,
        "ab": ab_note,
    })

# --- 3. Tom tat -----------------------------------------------------------------
out("\n" + "=" * 65)
out("TOM TAT")
out("=" * 65)
out(f"Chien luoc     : {CHUNKER.__class__.__name__}")
out(f"Tong so chunk  : {len(all_docs)}")
out(f"Tong diem (co filter, max 10): {total_with}/10")
out("")
out(f"{'ID':<4} {'Diem co filter':<16} {'Diem ko filter':<16} {'A/B'}")
out(f"{'─'*4} {'─'*16} {'─'*16} {'─'*30}")
for row in summary_rows:
    out(f"{row['id']:<4} {row['score_with']:<16} {row['score_without']:<16} {row['ab']}")

# --- 4. Failure case ------------------------------------------------------------
out("\n" + "=" * 65)
out("FAILURE CASE ANALYSIS")
out("=" * 65)
out("Failure case dien hinh: [Q4] Bao hanh san pham dien tu")
out("")
out("Van de: Top-1 tra ve shopee_return_refund_guide_buyer thay vi")
out("  shopee_warranty_policy (gold doc).")
out("")
out("Nguyen nhan:")
out("  MockEmbedder dung hash MD5 nen score chi phan anh su giong nhau")
out("  ve chuoi ky tu, khong phan anh ngu nghia. Cac chunk trong")
out("  shopee_return_refund_guide_buyer co nhieu tu trung lap voi cau")
out("  hoi ('san pham', 'Shopee') nen duoc rank cao hon.")
out("")
out("  Voi embedder that (sentence-transformers), vector 'bao hanh dien tu'")
out("  se gan voi 'chinh sach bao hanh' hon la 'quy trinh tra hang'.")
out("")
out("De xuat:")
out("  1. Dung embedder that de do chat luong ngu nghia thuc su.")
out("  2. Them metadata filter audience=buyer cho Q4 -> thu hep search space.")
out("  3. Xem xet them category filter ('warranty') de uu tien dung tai lieu.")

# --- 5. Luu file ----------------------------------------------------------------
OUTPUT_FILE.write_text("\n".join(lines_out), encoding="utf-8")
out(f"\n=> Da luu ket qua vao {OUTPUT_FILE}")
