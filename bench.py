"""
bench.py — Cong cu do chat luong retrieval cua nhom (Checkpoint 5)

Cach dung:
    python bench.py

Moi thanh vien chi doi dong `CHUNKER = ...` sang chien luoc rieng cua minh.
Moi thu khac giu nguyen de so sanh cong bang.
"""

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))

from src.chunking import RecursiveChunker  # R3 -- doi dong nay theo chien luoc rieng
from src.embeddings import MockEmbedder
from src.models import Document
from src.store import EmbeddingStore

# --- Cau hinh -------------------------------------------------------------------
DATA_DIR = Path("data/ChinhSachShopee")
CHUNK_SIZE = 500

# === DOI DONG NAY THEO CHIEN LUOC CUA TUNG THANH VIEN ===
CHUNKER = RecursiveChunker(chunk_size=CHUNK_SIZE)
# R1 (FixedSize):  CHUNKER = FixedSizeChunker(chunk_size=CHUNK_SIZE)
# R2 (Sentence):   CHUNKER = SentenceChunker(max_sentences_per_chunk=5)
# R3 (Recursive):  CHUNKER = RecursiveChunker(chunk_size=CHUNK_SIZE)  <- ban

# 5 cau hoi benchmark chung cua nhom
QUERIES = [
    {
        "id": "Q1",
        "question": "Nguoi mua can thuc hien nhung buoc nao de gui yeu cau Tra hang/Hoan tien tren Shopee?",
        "filter": {"audience": "buyer"},
        "gold": "Truy cap Don mua -> Chon don -> Nhan Tra hang/Hoan tien -> Chon ly do, tai bang chung, xac nhan.",
    },
    {
        "id": "Q2",
        "question": "Nhung nhom san pham nao khong duoc phep hoan tra vi ly do doi y?",
        "filter": None,
        "gold": "Thiet bi Dien tu & Cong nghe, Suc khoe/Ve sinh/Do ca nhan, Thuc pham & Hang mau hong, Hang dac thu, San pham so.",
    },
    {
        "id": "Q3",
        "question": "Khi khach hang yeu cau hoan tien, nguoi ban can phan hoi trong bao lau?",
        "filter": {"audience": "seller"},
        "gold": "Nguoi ban can phan hoi trong thoi gian dem nguoc hien thi tren ung dung (thuong 3-5 ngay lam viec).",
    },
    {
        "id": "Q4",
        "question": "Shopee ap dung chinh sach bao hanh nhu the nao cho san pham dien tu?",
        "filter": {"audience": "buyer"},
        "gold": "Shopee bao hanh qua trung tam bao hanh chinh hang hoac shop, thoi gian va dieu kien theo tung san pham.",
    },
    {
        "id": "Q5",
        "question": "Phi van chuyen hang tra lai do loi cua nguoi ban se duoc xu ly nhu the nao?",
        "filter": {"audience": "seller"},
        "gold": "Shopee se hoan phi van chuyen tra hang cho nguoi mua va tru vao tai khoan nguoi ban neu loi thuoc ve nguoi ban.",
    },
]


# --- Ham tien ich ---------------------------------------------------------------
def parse_frontmatter(text: str) -> tuple:
    """Tach YAML frontmatter thanh dict metadata va phan noi dung."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm_text = parts[1]
    content = parts[2].strip()
    metadata = {}
    for line in fm_text.splitlines():
        match = re.match(r"^(\w+):\s*(.+)$", line.strip())
        if match:
            metadata[match.group(1)] = match.group(2).strip()
    return metadata, content


# --- 1. Doc & chunk tai lieu ----------------------------------------------------
print("=" * 60)
print(f"Chien luoc: {CHUNKER.__class__.__name__}  (chunk_size={CHUNK_SIZE})")
print("=" * 60)

all_docs = []
md_files = sorted(DATA_DIR.glob("*.md"))

for path in md_files:
    raw = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(raw)

    chunks = CHUNKER.chunk(body)
    for i, chunk_text in enumerate(chunks):
        doc = Document(
            id=f"{path.stem}#{i}",
            content=chunk_text,
            metadata={
                **frontmatter,
                "doc_id": path.stem,
                "chunk_index": str(i),
                "source": str(path),
            },
        )
        all_docs.append(doc)

print(f"\nDa nap {len(md_files)} tai lieu -> {len(all_docs)} chunks vao store\n")

# --- 2. Nap vao EmbeddingStore --------------------------------------------------
store = EmbeddingStore(
    collection_name="bench_recursive",
    embedding_fn=MockEmbedder(),
)
store.add_documents(all_docs)

# --- 3. Chay 5 query & in top-3 -------------------------------------------------
for q in QUERIES:
    print("-" * 60)
    print(f"[{q['id']}] {q['question']}")
    print(f"  Filter: {q['filter']}")
    print(f"  Gold  : {q['gold']}")
    print()

    results = store.search_with_filter(
        query=q["question"],
        top_k=3,
        metadata_filter=q["filter"],
    )

    if not results:
        print("  [!] Khong co ket qua (kiem tra metadata_filter hoac du lieu)")
    else:
        for rank, r in enumerate(results, 1):
            preview = r["content"][:120].replace("\n", " ")
            doc_id = r["metadata"].get("doc_id", "?")
            audience = r["metadata"].get("audience", "?")
            score = r["score"]
            print(f"  #{rank}  score={score:.3f}  doc_id={doc_id}  audience={audience}")
            print(f"       {preview}...")
    print()

print("=" * 60)
print("bench.py hoan thanh OK")
