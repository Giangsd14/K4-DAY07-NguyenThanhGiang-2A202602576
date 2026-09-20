import csv
import re
from pathlib import Path


# ============================================================
# CẤU HÌNH
# ============================================================

D = Path(
    "D:/VinUni_AI2026/Lab/Lab7/"
    "K4-DAY07-NguyenThanhGiang-2A202602576/"
    "data/ChinhSachShopee"
)

REQ = [
    "doc_id",
    "title",
    "source_url",
    "retrieved_at",
    "document_version",
    "audience",
]


# ============================================================
# KIỂM TRA THƯ MỤC
# ============================================================

if not D.exists():
    print("LOI: Khong tim thay thu muc:")
    print(D)
    raise SystemExit(1)


# ============================================================
# LẤY FILE MARKDOWN
# ============================================================

mds = sorted(D.glob("*.md"))

if not mds:
    print("LOI: Khong tim thay file .md trong:")
    print(D)
    raise SystemExit(1)


# ============================================================
# ĐỌC SOURCES.CSV
# ============================================================

csv_path = D / "sources.csv"

if not csv_path.exists():
    print("LOI: Khong tim thay:")
    print(csv_path)
    raise SystemExit(1)

with open(
    csv_path,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:
    rows = list(csv.DictReader(f))


# ============================================================
# KIỂM TRA METADATA
# ============================================================

ids = []
auds = {}

print()
print("=" * 70)
print("KIEM TRA FILE MARKDOWN")
print("=" * 70)

for p in mds:

    text = p.read_text(encoding="utf-8")

    # --------------------------------------------------------
    # Kiểm tra YAML front matter
    # --------------------------------------------------------

    parts = text.split("---")

    if len(parts) < 3:
        print(f"{p.name:40} THIEU FRONT MATTER")
        continue

    front_matter = parts[1]

    # --------------------------------------------------------
    # Đọc metadata
    # --------------------------------------------------------

    fm = {}

    for line in front_matter.splitlines():

        line = line.strip()

        if not line or ":" not in line:
            continue

        key, value = line.split(":", 1)

        key = key.strip()
        value = value.strip()

        fm[key] = value

    # --------------------------------------------------------
    # Kiểm tra trường bắt buộc
    # --------------------------------------------------------

    missing = [
        key
        for key in REQ
        if not fm.get(key)
    ]

    doc_id = fm.get("doc_id")
    audience = fm.get("audience")

    # Chỉ thêm ID nếu thực sự tồn tại
    if doc_id:
        ids.append(doc_id)

    if audience:
        auds[audience] = auds.get(audience, 0) + 1

    # --------------------------------------------------------
    # Kiểm tra doc_id có khớp tên file không
    # --------------------------------------------------------

    doc_id_ok = doc_id == p.stem

    if not missing and doc_id_ok:
        print(f"{p.name:40} OK")

    else:
        print(f"{p.name:40} THIEU METADATA")

        if missing:
            print(
                "    Thieu:",
                ", ".join(missing)
            )

        if doc_id and not doc_id_ok:
            print(
                f"    doc_id sai: {doc_id}"
            )
            print(
                f"    Can co : {p.stem}"
            )


# ============================================================
# KIỂM TRA CSV
# ============================================================

print()
print("=" * 70)
print("TONG KET")
print("=" * 70)

print(
    f"so file : {len(mds)} (can 5-10)"
)


csv_ids = sorted(
    r.get("doc_id", "").strip()
    for r in rows
    if r.get("doc_id")
)

md_ids = sorted(ids)


if csv_ids == md_ids:
    print("csv     : khop")
else:
    print("csv     : LECH")

    print()
    print("Doc_id trong Markdown:")

    if md_ids:
        for x in md_ids:
            print("  ", x)
    else:
        print("   KHONG CO DOC_ID")

    print()
    print("Doc_id trong sources.csv:")

    if csv_ids:
        for x in csv_ids:
            print("  ", x)
    else:
        print("   KHONG CO DOC_ID")


print()
print("audience:", auds)

print()
print("=" * 70)
print("HOAN TAT")
print("=" * 70)