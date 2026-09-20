# Individual contribution report

Mỗi thành viên copy template này thành:

```text
reports/<student-id>-<short-name>.md
```

Giới hạn khuyến nghị: 1 trang, không chép lại README hoặc mô tả lý thuyết chung. Báo cáo không phải một bài pipeline cá nhân; mục đích là ghi nhận ownership và bằng chứng đóng góp trong sản phẩm nhóm.

---

## Thông tin

- Họ và tên: NGUYỄN VŨ QUANG ANH
- Mã học viên: 2A202602805
- Nhóm: ThreeMenSquad
- Repository/branch: local (thao tác không trên version control)

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 8 — PageIndex | PDF upload/cache, query polling and tree-result parsing | `src/task8_pageindex_vectorless.py` | Done |
| Task 10 — generation | Provider dispatch, grounded context, refusal and citation validation | `src/task10_generation.py`, `app.py` | Done |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

## Quyết định kỹ thuật quan trọng

Mô tả tối đa hai quyết định mà bạn trực tiếp tham gia:

1. **Quyết định:** PageIndex cache ID/query và trả list rỗng an toàn khi thiếu key.  
   **Lý do/evidence:** Không upload lại PDF ở mỗi lần chạy và không phá pipeline local.  
   **Trade-off:** Query vectorless phụ thuộc dịch vụ ngoài.

2. **Quyết định:** Prompt bắt buộc citation `[ID]`, sau đó validate citation thuộc context.  
   **Lý do/evidence:** Giảm citation bịa và bảo đảm câu trả lời có nguồn.  
   **Trade-off:** Có thể từ chối nếu model không theo format.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `python -m pytest tests/test_contracts.py -q`.
- Kết quả trước/sau nếu có: contract tests pass; generation/refusal/citation paths được kiểm tra.
- Lỗi đã phát hiện và cách xử lý: provider/API errors được chuyển thành lỗi rõ ràng hoặc empty PageIndex result.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: citation validation chưa đo được faithfulness khi chưa gọi evaluator ngoài.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: thêm retry/backoff và đo latency theo provider.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-21
- Tên thành viên: NGUYỄN VŨ QUANG ANH
