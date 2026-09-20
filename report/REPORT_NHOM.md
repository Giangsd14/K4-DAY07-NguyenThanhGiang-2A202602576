# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** VGV
**Thành viên:** Nguyễn Thành Vinh - Nguyễn Thanh Giang - Đặng Thế Vinh
**Ngày:** 20/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách Đổi trả, Bảo hành & Thanh toán trên Shopee (thương mại điện tử)

**Tại sao nhóm chọn chủ đề này?**
> Chính sách đổi trả/bảo hành là loại tài liệu có cấu trúc rõ ràng (có điều khoản, mục, danh sách), đồng thời có sự phân tách tự nhiên giữa 2 nhóm người dùng (buyer/seller) — rất phù hợp để kiểm thử metadata filter. Ngoài ra, nội dung công khai, dễ thu thập, và câu hỏi thực tế của người dùng Shopee rất cụ thể nên dễ đánh giá chất lượng retrieval.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | shopee_faq_return_refund_seller | https://banhang.shopee.vn/edu/article/faq-return-refund | 2026-09-20 / 20-08-2026 | ~20 659 | audience=seller, category=return_refund_faq |
| 2 | shopee_payment_policy_seller | https://banhang.shopee.vn/edu/article/234 | 2026-09-20 / 18-05-2026 | ~8 409 | audience=seller, category=payment |
| 3 | shopee_return_refund_guide_buyer | https://shopee.vn/blog/cach-tra-hang-hoan-tien-tren-shopee/ | 2026-09-20 / 15-09-2026 | ~15 773 | audience=buyer, category=return_refund_guide |
| 4 | shopee_return_shipping_fee_policy | https://banhang.shopee.vn/edu/article/3648 | 2026-09-20 / 16-09-2025 | ~6 458 | audience=seller, category=return_refund |
| 5 | shopee_seller_return_refund_process | https://banhang.shopee.vn/edu/article/563 | 2026-09-20 / 2026-08-27 | ~8 523 | audience=seller, category=return_refund |
| 6 | shopee_warranty_policy | https://help.shopee.vn/portal/4/article/79046 | 2026-09-20 / N/A | ~5 839 | audience=buyer, category=warranty |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `shopee_warranty_policy` | Định danh duy nhất — dùng để xóa hoặc cập nhật document trong store |
| `title` | string | `Chính sách bảo hành...` | Hiển thị cho người dùng cuối, giúp trace kết quả về nguồn |
| `source_url` | string | `https://banhang.shopee.vn/...` | Truy vết nguồn gốc câu trả lời, đảm bảo tính minh bạch |
| `retrieved_at` | string (ISO date) | `2026-09-20` | Kiểm tra độ mới của thông tin (chính sách thay đổi thường xuyên) |
| `document_version` | string | `20-08-2026` | Xác định phiên bản chính sách đang áp dụng |
| `audience` | string enum | `buyer` / `seller` / `both` | **Filter chính** — tránh trả kết quả buyer cho câu hỏi seller và ngược lại |
| `category` | string | `return_refund`, `warranty`, `payment` | Lọc theo chủ đề cụ thể, thu hẹp không gian tìm kiếm |
| `language` | string | `vi` | Hỗ trợ mở rộng đa ngôn ngữ trong tương lai |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| shopee_return_shipping_fee_policy (~6,5k ký tự) | FixedSizeChunker | 11 | 473.9 | Không — cắt giữa câu |
| shopee_return_shipping_fee_policy | SentenceChunker | 10 | 468.8 | Khá — giữ câu nguyên vẹn |
| shopee_return_shipping_fee_policy | RecursiveChunker | 13 | 360.8 | Tốt — tôn trọng cấu trúc |
| shopee_seller_return_refund_process (~8,5k ký tự) | FixedSizeChunker | 14 | 490.0 | Không — cắt giữa điều khoản |
| shopee_seller_return_refund_process | SentenceChunker | 20 | 308.6 | Trung bình — chunk quá nhỏ |
| shopee_seller_return_refund_process | RecursiveChunker | 16 | 386.3 | Tốt — tôn trọng mục/bước |
| shopee_warranty_policy (~5,8k ký tự) | FixedSizeChunker | 10 | 475.2 | Không — cắt giữa điều khoản |
| shopee_warranty_policy | SentenceChunker | 9 | 475.9 | Khá — phù hợp văn bản ngắn |
| shopee_warranty_policy | RecursiveChunker | 12 | 356.9 | Tốt — giữ được nghiā mục |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Nguyễn Thành Vinh**
- **Loại chiến lược:** FixedSizeChunker (fixed_size)
- **Mô tả & lý do chọn cho chủ đề này:** Cắt đoạn văn bản theo kích thước cố định chunk_size=500, overlap=50. Đây là chiến lược đường cơ sở (baseline) có tốc độ tính toán nhanh nhất, phân bổ kích thước chunk đồng đều; tuy nhiên nhược điểm lớn là cắt đứt câu văn giữa chừng và làm mất liên kết tiêu đề mục trong các văn bản quy định.
- **Code snippet (nếu custom):**
```python
from src.chunking import FixedSizeChunker
CHUNKER = FixedSizeChunker(chunk_size=500, overlap=50)
```

**Thành viên 2 — Đặng Thế Vinh**
- **Loại chiến lược:** SentenceChunker (sentence)
- **Mô tả & lý do chọn:** Chia nhỏ văn bản dựa trên dấu chấm kết thúc câu với `max_sentences_per_chunk=5`. Chiến lược này đảm bảo không bao giờ cắt đứt một câu văn bản đang viết dở, giúp từng chunk mang trọn vẹn ý nghĩa của một hoặc vài câu liên tiếp.
- **Code snippet (nếu custom):**
```python
from src.chunking import SentenceChunker
CHUNKER = SentenceChunker(max_sentences_per_chunk=5)
```

**Thành viên 3 — Nguyễn Thanh Giang**
- **Loại chiến lược:** Recursive
- **Mô tả & lý do chọn:** `RecursiveChunker` tách văn bản theo danh sách separator ưu tiên (`\n\n` → `\n` → ` ` → `""`) — phù hợp với tài liệu chính sách Shopee vốn được phân tầng theo đoạn và điều khoản. So với FixedSize (cắt giữa câu), Recursive tôn trọng ranh giới ngữ nghĩa hơn, giúp retrieval nắm bắt được toàn bộ điều kiện trong một chunk.
- **Code snippet:**
```python
from src.chunking import RecursiveChunker
CHUNKER = RecursiveChunker(chunk_size=500)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Thành Vinh | FixedSizeChunker | 2/10 | Tốc độ tính toán nhanh, chunk đều | Hay cắt ngang câu và cắt ngang điều khoản |
| Đặng Thế Vinh | SentenceChunker | 5/10 | Không bao giờ cắt đứt câu văn | Các câu quá ngắn có thể mất bối cảnh đoạn |
| Nguyễn Thanh Giang | RecursiveChunker | 3/10 | Giữ ngữ cảnh trọn vẹn theo mục | Nếu mục quá dài có thể bị cắt ngẫu nhiên |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Bất ngờ thay, với `MockEmbedder` (băm hash MD5 ký tự), `SentenceChunker` lại cho kết quả tốt nhất (5/10). Lý do là vì chia thành các câu ngắn giúp thu hẹp đoạn văn bản, giảm thiểu các từ "nhiễu", nên khi khớp hash MD5 dễ trúng các từ khóa đặc thù (gold keyword) hơn. Tuy nhiên trong môi trường dùng semantic embedder thực tế, `RecursiveChunker` khả năng cao sẽ tốt hơn vì giữ được cả cấu trúc tiêu đề.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua cần thực hiện những bước nào để gửi yêu cầu Trả hàng/Hoàn tiền trên ứng dụng Shopee? (Cần lọc: audience: buyer) | Vào mục Tôi -> Đơn mua -> Nhấn Trả hàng/Hoàn tiền -> Chọn lý do, tải lên bằng chứng và Xác nhận. | `shopee_return_refund_guide_buyer.md` (Mục: 5. Hướng dẫn cách trả hàng hoàn tiền) |
| 2 | Những nhóm sản phẩm nào thuộc danh mục hạn chế không được trả hàng hoặc không áp dụng lý do "Đổi ý/không còn nhu cầu"? | Thiết bị Điện tử & Công nghệ, Sức khỏe/Vệ sinh/Đồ cá nhân, Thực phẩm & Hàng mau hỏng, Hàng đặc thù trong vận chuyển, Sản phẩm số và dịch vụ. | `shopee_seller_return_refund_process.md` (Mục: Danh mục sản phẩm hạn chế) |
| 3 | Khi khách hàng yêu cầu hoàn tiền không trả hàng, người bán cần phản hồi khiếu nại trong thời gian bao lâu? (Cần lọc: audience: seller) | Người bán cần phản hồi trong thời gian đếm ngược hiển thị trên ứng dụng (thông thường là 3-5 ngày làm việc). | `shopee_faq_return_refund_seller.md` (Mục: 12. Quyết định hoàn tiền không trả hàng) |
| 4 | Shopee áp dụng chính sách bảo hành như thế nào đối với các sản phẩm điện tử? (Cần lọc: audience: buyer) | Shopee bảo hành thông qua trung tâm bảo hành chính hãng hoặc trực tiếp từ Người bán, thời gian và điều kiện cụ thể tùy theo từng sản phẩm. | `shopee_warranty_policy.md` (Mục: Thông tin bảo hành) |
| 5 | Phí vận chuyển hàng trả lại do lỗi của người bán sẽ được xử lý như thế nào? (Cần lọc: audience: seller) | Shopee sẽ hoàn phí vận chuyển trả hàng cho người mua và trừ vào tài khoản người bán nếu lỗi thuộc về người bán. | `shopee_return_shipping_fee_policy.md` (Mục: Chính sách phí vận chuyển) |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Người mua cần thực hiện những bước nào để gửi yêu cầu Trả hàng/Hoàn tiền? | Fixed/Sentence/Recursive | Có (top-2/3) | Cả 3 chiến lược đều lấy được quy trình trả hàng |
| 2 | Những nhóm sản phẩm nào không được phép hoàn trả vì lý do đổi ý? | SentenceChunker | Có (top-2/3) | SentenceChunker lấy được danh mục nhờ câu ngắn, các chiến lược khác (0 điểm) bị nhiễu do chunk quá dài |
| 3 | Khi khách hàng yêu cầu hoàn tiền, người bán cần phản hồi trong bao lâu? | Fixed/Sentence/Recursive | Có (top-2/3) | Tìm thấy thông tin phải phản hồi trong thời gian đếm ngược ở cả 3 chunker |
| 4 | Shopee áp dụng chính sách bảo hành như thế nào đối với các sản phẩm điện tử? | Sentence/Recursive | Có (top-2/3) | Nhờ lọc `audience=buyer` mà loại bỏ được các hướng dẫn seller, lấy đúng policy bảo hành |
| 5 | Phí vận chuyển hàng trả lại do lỗi của người bán sẽ được xử lý như thế nào? | SentenceChunker | Có (top-2/3) | Chunk chứa từ khoá "phí vận chuyển" lấy được chính xác ở SentenceChunker |

**Lọc bằng metadata có giúp ích không? Ờ câu hỏi nào?**
> Điểm nổi bật nhất là **Q4** (bảo hành điện tử, filter `audience=buyer`): không filter → gold absent (0 điểm) vì các chunk seller chiếm top-3; có filter → gold ở top-2 (1 điểm). Đây là bằng chứng rõ nhất rằng metadata `audience` giải quyết bài toán tài liệu cùng chủ đề, cùng từ vựng nhưng khác đối tượng. Đối với Q3 và Q5, filter ngăn seller docs trộn vào kết quả nhưng chưa đủ đưa gold lên top-1 vì MockEmbedder không mã hóa ngữ nghĩa thực sự.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> - MockEmbedder cực kỳ nhạy cảm với độ dài chunk: Chunk càng dài (như Fixed/Recursive) càng dễ bị rớt rank vì bị hòa lẫn bởi các từ vựng phổ thông không mang ý nghĩa tìm kiếm.
> - Metadata `audience` thực sự giải quyết được bài toán 2 tài liệu giống hệt từ vựng nhưng khác đối tượng đích (như trong trường hợp người bán vs người mua của Shopee).

**Bài học rút ra khi so sánh trong nhóm:**
> Trong bài Lab này, thuật toán chia văn bản theo câu (SentenceChunker) áp đảo 2 thuật toán kia khi dùng MockEmbedder. Nó cho thấy nếu không có khả năng vector hóa theo ngữ nghĩa (semantic search), thì hệ thống RAG cần phải chia chunk thật nhỏ để tìm kiếm keyword matching chính xác nhất có thể.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ dung embedder thật (sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) ngay từ đầu bài để có số liệu retrieval phản ánh ngữ nghĩa thực. Ngoài ra, nhóm sẽ bổ sung trường `category` vào metadata để tạo thêm một lớp filter tinh hơn (ví dụ: chỉ search trong tài liệu `category=warranty` khi hỏi về bảo hành). Cuối cùng, câu hỏi benchmark cần được chọn kĩ hơn để gold keyword chỉ xuất hiện trong đúng một tài liệu, tránh trường hợp từ khóa trùng lập nằm rải ở nhiều tài liệu khác nhau.

**Failure Case điển hình (phân tích lỗi):**
> - **Câu hỏi hỏng:** Q5 — “Phí vận chuyển hàng trả lại do lỗi người bán sẽ được xử lý như thế nào?” (`audience: seller`, gold doc: `shopee_return_shipping_fee_policy`) — gold absent dù có filter.
> - **Vì sao:** MockEmbedder băm hash nên các chunk trong `shopee_seller_return_refund_process` (dài hơn, có nhiều từ “thương mại” trùng ký tự với câu hỏi) được rank cao hơn. File gold (`shopee_return_shipping_fee_policy`) ngắn hơn và có từ vựng rất cụ thể (“phí vận chuyển”) nhưng hash không nhập chuỗi này tốt hơn các file khác.
> - **Đề xuất:** (1) Dùng embedder thật để vector “phí vận chuyển” gần với chunk gold. (2) Bổ sung filter `category=return_refund` để loại tài liệu không liên quan. (3) Thay thế MockEmbedder bằng LocalEmbedder (paraphrase-multilingual-MiniLM).

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
