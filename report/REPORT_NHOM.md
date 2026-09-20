# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

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

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

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
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua cần thực hiện những bước nào trên ứng dụng Shopee để gửi yêu cầu Trả hàng/Hoàn tiền? | Truy cập Đơn mua -> Chọn đơn hàng -> Nhấn Trả hàng/Hoàn tiền -> Chọn lý do, tải lên bằng chứng và Xác nhận. *(Cần bổ sung tài liệu chứa thông tin này)* | *(Chưa có trong dữ liệu hiện tại)* |
| 2 | Khi Shopee yêu cầu bổ sung bằng chứng cho yêu cầu Trả hàng/Hoàn tiền, Người mua có bao nhiêu thời gian để phản hồi? | Thông thường là 24h hoặc theo thời gian đếm ngược hiển thị trên ứng dụng. *(Cần bổ sung tài liệu chứa thông tin này)* | *(Chưa có trong dữ liệu hiện tại)* |
| 3 | Những nhóm sản phẩm nào thuộc danh mục hạn chế không được trả hàng hoặc không áp dụng lý do "Đổi ý/không còn nhu cầu"? | Thiết bị Điện tử & Công nghệ, Sức khỏe/Vệ sinh/Đồ cá nhân, Thực phẩm & Hàng mau hỏng, Hàng đặc thù trong vận chuyển, Sản phẩm số và dịch vụ. | `shopee_seller_return_refund_process.md` (Mục: Danh mục sản phẩm hạn chế) |
| 4 | Shopee Xu và Mã giảm giá (Voucher) đã sử dụng sẽ được hoàn lại như thế nào khi yêu cầu Trả hàng/Hoàn tiền thành công? | Tự động hoàn lại vào tài khoản Người mua sau khi yêu cầu THHT được chấp nhận, với điều kiện mã còn hạn sử dụng. *(Cần bổ sung tài liệu chứa thông tin này)* | *(Chưa có trong dữ liệu hiện tại)* |
| 5 | Người bán vi phạm quy định đăng bán sản phẩm trên Shopee (như bán hàng cấm, hàng giả, gian lận) sẽ bị xử lý bằng những hình thức nào? (Cần lọc: audience: seller) | Khóa sản phẩm, trừ Sao Quả Tạ, giới hạn quyền bán hàng, hoặc khóa tài khoản vĩnh viễn tùy mức độ. *(Cần bổ sung tài liệu chứa thông tin này)* | *(Chưa có trong dữ liệu hiện tại)* |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
