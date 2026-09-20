# Individual contribution report

Mỗi thành viên copy template này thành:

```text
reports/<student-id>-<short-name>.md
```

Giới hạn khuyến nghị: 1 trang, không chép lại README hoặc mô tả lý thuyết chung. Báo cáo không phải một bài pipeline cá nhân; mục đích là ghi nhận ownership và bằng chứng đóng góp trong sản phẩm nhóm.

---

## Thông tin

- Họ và tên: MAI PHAN ANH TÙNG
- Mã học viên: 2A202602980
- Nhóm: ThreeMenSquad
- Repository/branch: local (thao tác không trên version control)

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 4 — chunking/indexing | Recursive chunks 500/50, BGE-M3 embeddings, stable IDs and Chroma cosine upsert | `src/task4_chunking_indexing.py` | Done |
| Task 3 — contract integration | Validated document/chunk metadata and idempotent conversion path | `src/task3_convert_markdown.py`, `src/contracts.py` | Done |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

## Quyết định kỹ thuật quan trọng

Mô tả tối đa hai quyết định mà bạn trực tiếp tham gia:

1. **Quyết định:** RecursiveCharacterTextSplitter với `chunk_size=500`, `overlap=50`.  
   **Lý do/evidence:** Giữ ngữ cảnh theo đoạn và tạo ID `document::chunk-index` ổn định.  
   **Trade-off:** Nhiều chunk hơn và tăng chi phí embedding.

2. **Quyết định:** Dùng cosine distance trong Chroma và normalize embedding.  
   **Lý do/evidence:** Phù hợp semantic search, upsert theo ID không tạo duplicate.  
   **Trade-off:** BGE-M3 chạy CPU chậm hơn model nhỏ.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `python -m pytest tests/test_contracts.py -q`; kiểm tra collection main có 1.456 chunk.
- Kết quả trước/sau nếu có: contract tests pass; index được tạo trong `chroma_db/`.
- Lỗi đã phát hiện và cách xử lý: lazy-cache model và dùng `HF_HUB_OFFLINE=1` khi model đã cache.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: BGE-M3 embedding trên CPU có latency cao.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: benchmark batch size và lưu corpus manifest/hash.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-21
- Tên thành viên: MAI PHAN ANH TÙNG
