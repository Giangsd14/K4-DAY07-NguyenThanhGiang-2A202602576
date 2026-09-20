# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thanh Giang
**Nhóm:** VGV
**Ngày:** 20/9/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao có nghĩa là hai vector embedding của văn bản hướng về cùng một phía trong không gian vector đa chiều, thể hiện rằng hai đoạn văn bản này có ngữ nghĩa (semantic meaning) rất giống nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Chú chó đang nằm ngủ say sưa trên tấm thảm ngoài hiên nhà.
- Câu B: Bên ngoài mái hiên, một con cún đang say giấc nồng trên miếng lót.
- Tại sao tương đồng: Mặc dù sử dụng các từ vựng hoàn toàn khác nhau ("Chú chó" vs "con cún", "ngủ say sưa" vs "say giấc nồng", "tấm thảm" vs "miếng lót"), nhưng mô hình embedding hiểu được ngữ nghĩa tổng thể mô tả cùng một sự việc nên sẽ cho điểm tương đồng cao.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Ngân hàng nhà nước vừa ra quyết định tăng lãi suất tiết kiệm.
- Câu B: Chiếc thuyền nhỏ đang neo đậu bình yên bên bờ sông.
- Tại sao khác: Hai câu mang ý nghĩa cốt lõi thuộc về hai lĩnh vực hoàn toàn khác nhau (tài chính kinh tế vs phong cảnh thiên nhiên), dù trong tiếng Anh có thể có sự trùng lặp từ vựng ("bank").

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Độ tương tự cosine chỉ quan tâm đến góc giữa hai vector (phương hướng) thay vì độ dài (magnitude) của chúng. Trong text embedding, tần suất xuất hiện của từ hoặc độ dài văn bản có thể làm thay đổi độ lớn của vector, nhưng ý nghĩa cốt lõi (thể hiện qua góc) mới là yếu tố quyết định sự tương đồng về ngữ nghĩa.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* số lượng chunk = làm_tròn_lên((10000 - 50) / (500 - 50)) = làm_tròn_lên(9950 / 450) = 23
> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Nếu overlap=100, số lượng chunk sẽ tăng lên: làm_tròn_lên((10000 - 100) / (500 - 100)) = làm_tròn_lên(9900 / 400) = 25 chunks. Việc tăng độ chồng chéo giúp duy trì ngữ cảnh (context) tốt hơn giữa các chunks liền kề, tránh việc một câu hay một ý quan trọng bị cắt đôi đột ngột làm mất đi ý nghĩa trọn vẹn khi truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng regex `re.split(r'(\. |\! |\? |\.\n)', text)` để tách văn bản nhưng vẫn giữ lại các dấu câu (bằng cách lấy cả nhóm separator). Sau đó lặp qua list kết quả, ghép lại mỗi phần tử với dấu câu tương ứng để tạo thành câu hoàn chỉnh, rồi gộp các câu lại thành chunk theo kích thước tối đa.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán tách dần theo từng separator trong danh sách ưu tiên. Tại mỗi bước `_split`, tách current_text bằng separator đầu tiên, sau đó lặp qua các phần tử. Nếu phần tử nào đã đủ nhỏ, ta nối dồn vào current_chunk (có tính kèm độ dài separator) cho đến khi đạt giới hạn. Nếu một phần tử vẫn lớn hơn chunk_size, hàm sẽ gọi đệ quy chính nó để tiếp tục tách với các separators còn lại (trường hợp cơ sở: văn bản ≤ chunk_size, hoặc hết separator thì chia theo ký tự).

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Với `add_documents`, duyệt qua list các Document, nhúng (embed) nội dung (dùng `self._embedding_fn(doc.content)`), và lưu thành record `{id, content, embedding, metadata}` vào in-memory `_store` (nếu dùng chroma thì đưa vào collection). Với `search`, nhúng câu truy vấn, rồi duyệt qua `_store` để tính tích vô hướng (dot product) giữa vector câu hỏi và vector mỗi chunk, cuối cùng sort theo score giảm dần và lấy top_k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Với `search_with_filter`, lọc (filter) record *trước* (bằng cách duyệt qua `_store` xem `metadata` có khớp với tất cả các key-value trong bộ lọc không), rồi mới đưa danh sách đã lọc vào hàm tính độ tương tự. Với `delete_document`, tạo lại list `_store` mới chỉ giữ lại các record có `metadata["doc_id"]` và `id` KHÁC với `doc_id` cần xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Hàm `answer` thực hiện quy trình RAG cơ bản: Đầu tiên, gọi `self.store.search(question, top_k)` để lấy về các chunks liên quan nhất. Sau đó, dùng vòng lặp để nối nội dung của các chunks này lại thành một chuỗi văn bản lớn (có đánh dấu `--- Chunk 1 ---` v.v. để tách biệt). Cuối cùng, ghép ngữ cảnh vừa tạo vào chuỗi prompt theo cấu trúc "Context: [context] \n\n Question: [question]" và truyền vào LLM (`self.llm_fn(prompt)`) để sinh câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

```
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\VinUni_AI2026\Lab\Lab7\K4-DAY07-NguyenThanhGiang-2A202602576
plugins: anyio-4.15.1
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
... (truncated output for brevity) ...
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.23s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | cao / thấp | | |
| 2 | | | cao / thấp | | |
| 3 | | | cao / thấp | | |
| 4 | | | cao / thấp | | |
| 5 | | | cao / thấp | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
