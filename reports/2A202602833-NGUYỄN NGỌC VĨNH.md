# Individual contribution report

Mỗi thành viên copy template này thành:

```text
reports/<student-id>-<short-name>.md
```

Giới hạn khuyến nghị: 1 trang, không chép lại README hoặc mô tả lý thuyết chung. Báo cáo không phải một bài pipeline cá nhân; mục đích là ghi nhận ownership và bằng chứng đóng góp trong sản phẩm nhóm.

---

## Thông tin

- Họ và tên: NGUYỄN NGỌC VĨNH
- Mã học viên: 2A202602833
- Nhóm: ThreeMenSquad
- Repository/branch: local (thao tác không trên version control)

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 7 — reranking | Reciprocal Rank Fusion, deduplicate and deterministic tie-break | `src/task7_reranking.py` | Done |
| Task 9 — retrieval pipeline | Dense+sparse retrieval, RRF, threshold fallback and error-safe behavior | `src/task9_retrieval_pipeline.py` | Done |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

## Quyết định kỹ thuật quan trọng

Mô tả tối đa hai quyết định mà bạn trực tiếp tham gia:

1. **Quyết định:** Dùng RRF thay vì cộng trực tiếp hai loại score.  
   **Lý do/evidence:** Dense cosine và BM25 không cùng thang đo; rank fusion không cần calibration.  
   **Trade-off:** Mất thông tin độ lớn score tuyệt đối.

2. **Quyết định:** Dense score dưới threshold thì fallback sang hybrid/sparse.  
   **Lý do/evidence:** Giảm rủi ro dùng dense match yếu.  
   **Trade-off:** Có thể tăng latency vì chạy thêm retrieval branch.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `python -m pytest tests/test_contracts.py -q`.
- Kết quả trước/sau nếu có: contract tests pass; RRF ổn định và pipeline chịu lỗi fallback.
- Lỗi đã phát hiện và cách xử lý: loại duplicate theo lần xuất hiện đầu tiên để không phình context.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: threshold chưa được calibration bằng API evaluation.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: grid search threshold trên golden set.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-21
- Tên thành viên: NGUYỄN NGỌC VĨNH
