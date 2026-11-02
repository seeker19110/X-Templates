---
title: Đề xuất từ stored PR105 — mở rộng 28 chuyên mục, XT-H-094…105
kind: research
updated: 2026-11-02
---

# Đề xuất từ stored: dữ liệu, model, tài liệu, kỹ thuật và hiệu quả sản phẩm

Bổ sung cho [đợt nâng trần trước](2026-11-02-stored-delta-ceiling.md). File này chỉ là **research note đề xuất**: chưa sửa yêu cầu trong `framework/`, chưa cấp ID mới, chưa đổi mức hiện có và chưa triển khai công cụ/cổng. Mọi mức đề xuất dưới đây là **SHOULD**, chỉ áp khi dự án có tính năng tương ứng.

## 1. Phạm vi và cách đối chiếu

- Nguồn: [stored PR105](https://github.com/seeker19110/stored/pull/105), merge `d8d2708377933491107c0cd3f2f88f64da95ba34` ngày 2026-11-02; phạm vi từ base `a1413e6` đến merge này. Catalog 908→976, thêm 68 hồ sơ, đọc sâu lại 18 hồ sơ; cả 23 mục cũ được mở sâu và thêm 5 mục mới. Ngày snapshot không có nghĩa mọi hồ sơ đều được kiểm lại.
- Bàn giao máy đọc: [XT-H-094…105](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/data/xt-handoff.json), [bảng phía stored](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/X-TEMPLATES.md#4d-bàn-giao-mở-rộng-28-chuyên-mục-xt-h-094105).
- Khung đối chiếu: `24f221bd992560525a917a9fee1154a53fb67347`, ngày 2026-11-02. Đọc lại 32 ID đã có và các research note trước; 32 ID/nội dung/line không đổi từ `628e36c`. Phân loại 10 **nông hơn**, 2 **chưa có hợp đồng cụ thể** (OCR/CAD); không nói cả chủ đề hoàn toàn vắng mặt.
- Giữ nguồn permalink của từng hồ sơ. Bằng chứng upstream là đọc mã/đặc tả, không chạy model/benchmark; tiêu chí kiểm trong đề xuất là việc cần triển khai nếu được chấp nhận. CI của note này chỉ kiểm chính repo X-Templates.

## 2. Bản đồ 12 đề xuất

| Bàn giao | Phạm vi | ID gần nhất | Cột |
|---|---|---|---|
| XT-H-094 | Catalog đích phải đo completeness trước khi runtime/compiler áp fallback; compile --strict sau fallback vẫn có thể xanh với câu nguồn. | `XC-I18N-009`, `XC-I18N-013`, `XC-I18N-016` | nông hơn |
| XT-H-095 | Retrieval docs cần giữ requested_version và served_version; HTTP200 có thể là fallback sang docs của phiên bản khác, không chứng minh khớp lockfile. | `WF-DOC-011`, `XC-DOCAI-012`, `XC-DOCAI-013` | nông hơn |
| XT-H-096 | Split train/validation/test theo source/cluster trước augment hoặc synthetic; propagate group ID và kiểm overlap trên artifact export cuối. | `AI-DATA-007`, `AI-DATA-010`, `QA-DATA-013` | nông hơn |
| XT-H-097 | Dataset có nội dung synthetic/AI feedback cần manifest generator/judge/prompt/config/source split; cache resume không thay provenance phát hành. | `AI-DATA-001`, `AI-DATA-002`, `AI-DATA-011` | nông hơn |
| XT-H-098 | Training gate cần xem sample đã render/tokenize và loss mask; tên assistant_only_loss không bảo đảm template có mask hoặc đáp án không bị truncation. | `AI-DATA-006`, `AI-DATA-009`, `AI-DATA-010` | nông hơn |
| XT-H-099 | Adapter/merge/quantization/export là các artifact có thể đổi hành vi; load được file không đủ để kế thừa điểm eval của checkpoint huấn luyện. | `AI-DATA-006`, `AI-DATA-009`, `AI-EVAL-001` | nông hơn |
| XT-H-100 | Document pipeline cần giữ page outcome và citation theo hash tài liệu/parser/model; fallback, discarded và unmeasured không được gộp vào số trang OCR đạt. | `BE-FILE-010`, `AI-DATA-002`, `AI-EVAL-006` | chưa có hợp đồng cụ thể |
| XT-H-101 | CAD/BIM agent cần kiểm riêng schema, requirements, geometry và host execution; preview/confirm phải gắn đúng hash model/spec trước khi ghi. | `QA-INT-020`, `AI-AGENT-003`, `PRF-AGENTIC-012` | chưa có hợp đồng cụ thể |
| XT-H-102 | A/B phải kiểm assignment khác exposure, mẫu số và SRM trước effect size; evaluator incomplete/unknown không được coi là thí nghiệm đạt. | `PM-METRIC-002`, `PM-METRIC-011`, `AI-EVAL-017` | nông hơn |
| XT-H-103 | Durable journal không giao dịch nguyên tử với dịch vụ ngoài; kiểm cửa sổ crash sau external commit trước checkpoint, cùng retry/time/cancel/retention contract. | `AI-AGENTIC-002`, `AI-AGENT-005`, `ARC-INT-016` | nông hơn |
| XT-H-104 | Replay cache và repeated fresh generation có mục đích khác; thống kê phải ghi đơn vị attempt/sample/episode và cluster, không đếm output cache như mẫu độc lập. | `AI-EVAL-002`, `AI-EVAL-013`, `AI-EVAL-018` | nông hơn |
| XT-H-105 | Voice agent phải đo turn/episode completion và interruption/reconnect; phát lại audio không cho phép thực thi lại tool đã ghi. | `BE-RT-013`, `BE-RT-006`, `AI-EVAL-007` | nông hơn |

## 3. Delta và phép kiểm đề xuất

### XT-H-094

**Hồ sơ nguồn:** [06-ui-ux-design/README.md#i18n-lifecycle-2026-11-02](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/06-ui-ux-design/README.md#i18n-lifecycle-2026-11-02).

**Khung đã có:** XC-I18N-009 đã bắt đủ khoá hoặc fallback khai báo và gợi ý lingui compile --strict; 013 có review và 016 có pseudo-locale.

**Phần cần bổ sung:** Bổ sung vị trí kiểm trước fallback và tách completeness của locale đích khỏi availability sau fallback; 93 bàn giao cũ chưa có trường hợp compileStrict phủ thiếu bằng ngôn ngữ nguồn.

**Đề xuất SHOULD:** Với sản phẩm phát hành nhiều locale, SHOULD kiểm catalog của từng locale đích trước khi áp fallback: thiếu/fuzzy/chưa review, placeholder và plural; báo riêng fallback được phép theo danh sách ngoại lệ. Giữ cổng compile/runtime fallback và E2E pseudo-locale/locale thật, nhưng không dùng build xanh sau fallback làm bằng chứng đã dịch đủ. Kiểm bằng fixture có một khoá vi rỗng nhưng en đầy đủ: completeness phải phát hiện khoá đó dù compile dùng fallback thành công.

**Đối chiếu khung:** [XC-I18N-009](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/18-cross-cutting/i18n-and-l10n.md#L49), [XC-I18N-013](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/18-cross-cutting/i18n-and-l10n.md#L53), [XC-I18N-016](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/18-cross-cutting/i18n-and-l10n.md#L56).

**Nguồn triển khai upstream:** [nguồn 1](https://github.com/i18next/i18next/blob/b84e4180d71d271b9ae1f19ebb668224069b435e/src/PluralResolver.js) · [nguồn 2](https://github.com/i18next/i18next/blob/b84e4180d71d271b9ae1f19ebb668224069b435e/src/defaults.js) · [nguồn 3](https://github.com/lingui/js-lingui/blob/cbf16e9825cea76408ce06da02980ba57c8ea6c0/packages/cli/src/api/compile/compileLocale.ts) · [nguồn 4](https://github.com/lingui/js-lingui/blob/cbf16e9825cea76408ce06da02980ba57c8ea6c0/packages/conf/src/types.ts) · [nguồn 5](https://github.com/WeblateOrg/weblate/blob/9106f6a31fdeae6fc9e57a3bc1ffc3979824213d/README.rst) · [nguồn 6](https://github.com/WeblateOrg/weblate/blob/9106f6a31fdeae6fc9e57a3bc1ffc3979824213d/docs/workflows.rst).

### XT-H-095

**Hồ sơ nguồn:** [16-docs-tools/README.md#docs-version-trust-2026-11-02](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/16-docs-tools/README.md#docs-version-trust-2026-11-02).

**Khung đã có:** WF-DOC-011 đã yêu cầu docs theo release;XC-DOCAI-012 có version/ngày tài liệu và013 bao gói nguồn đưa agent.

**Phần cần bổ sung:** Thiếu hợp đồng response của retrieval khi server tự fallback; khác việc chỉ ghim link/installversion hoặc lint freshness đã có trong XT-H-071.

**Đề xuất SHOULD:** Với công cụ truy xuất tài liệu theo dependency version, SHOULD lấy requested version từ lockfile/config đang dùng, giữ served version hoặc source tag/commit thực của response, URL nguồn và thời điểm lấy. Nếu không khớp hoặc không xác định được thì báo mismatch và tra docs/source đã ghim trước khi dựa vào snippet để đổi API; ví dụ quan trọng phải typecheck/test với dependency thật. Kiểm fixture provider trả200 nhưng served version khác request không được ghi là đã xác minh tương thích.

**Đối chiếu khung:** [WF-DOC-011](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/10-workflow/documentation-workflow.md#L55), [XC-DOCAI-012](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/18-cross-cutting/docs-for-ai-agents.md#L54), [XC-DOCAI-013](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/18-cross-cutting/docs-for-ai-agents.md#L55).

**Liên quan đợt trước:** XT-H-071; chỉ giữ phần delta nêu trên, không cấp yêu cầu song song cho cơ chế đã có.

**Nguồn triển khai upstream:** [nguồn 1](https://github.com/upstash/context7/blob/18d6f5d632d4cf53c464f36c79d2e4caa19a8e56/docs/api-guide.mdx) · [nguồn 2](https://github.com/upstash/context7/blob/18d6f5d632d4cf53c464f36c79d2e4caa19a8e56/packages/mcp/src/lib/api.ts) · [nguồn 3](https://github.com/backstage/backstage/blob/24deeed9605d2afa54c2e7456912317fa8a1dcee/plugins/techdocs-backend/src/DocsBuilder/builder.ts) · [nguồn 4](https://github.com/backstage/backstage/blob/24deeed9605d2afa54c2e7456912317fa8a1dcee/plugins/techdocs-backend/src/service/DocsSynchronizer.ts).

### XT-H-096

**Hồ sơ nguồn:** [24-ai-data-engineering/README.md#datatrove](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/24-ai-data-engineering/README.md#datatrove), [24-ai-data-engineering/README.md#data-juicer](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/24-ai-data-engineering/README.md#data-juicer), [24-ai-data-engineering/README.md#5-cổng-kiểm-có-thể-đo-và-quy-trình-human-review](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/24-ai-data-engineering/README.md#5-cổng-kiểm-có-thể-đo-và-quy-trình-human-review).

**Khung đã có:** AI-DATA-007 đã cấm trùng hash/near-duplicate giữa train/validation/holdout/eval;QA-DATA-013 giữ holdout khi tinh chỉnh prompt.

**Phần cần bổ sung:** Bổ sung chia theo nhóm nguồn trước generation và kiểm lại export cuối, tránh rò ngữ nghĩa dù hash khác. Không lặp đề xuất validation của XT-H-069 hay license dataset của089.

**Đề xuất SHOULD:** Với dữ liệu có nhiều biến thể cùng tài liệu, người dùng, hội thoại hoặc near-duplicate cluster, SHOULD xác định group/source ID và khoá split trước augmentation/generation; mọi bản dẫn xuất kế thừa group và split. Kiểm hash/near-duplicate lẫn group overlap lại trên artifact thực xuất cho trainer/eval, không chỉ tập thô. Báo số nhóm/mẫu từng split và ca bị loại; fixture hai biến thể cùng nguồn không được nằm ở train và final test.

**Đối chiếu khung:** [AI-DATA-007](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/data-and-fine-tuning.md#L57), [AI-DATA-010](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/data-and-fine-tuning.md#L60), [QA-DATA-013](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/14-testing-quality/test-data-and-fixtures.md#L48).

**Liên quan đợt trước:** XT-H-069, XT-H-089; chỉ giữ phần delta nêu trên, không cấp yêu cầu song song cho cơ chế đã có.

**Nguồn triển khai upstream:** [nguồn 1](https://github.com/huggingface/datatrove/blob/4c488a135cc582b482df81895e631aadff2fa4c1/README.md) · [nguồn 2](https://github.com/huggingface/datatrove/blob/4c488a135cc582b482df81895e631aadff2fa4c1/LICENSE) · [nguồn 3](https://github.com/datajuicer/data-juicer/blob/09178e1e0ac76cfbfe11232d66244e1ccc5add6f/README.md) · [nguồn 4](https://github.com/datajuicer/data-juicer/blob/09178e1e0ac76cfbfe11232d66244e1ccc5add6f/LICENSE).

### XT-H-097

**Hồ sơ nguồn:** [24-ai-data-engineering/README.md#distilabel](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/24-ai-data-engineering/README.md#distilabel), [24-ai-data-engineering/README.md#dvc](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/24-ai-data-engineering/README.md#dvc), [24-ai-data-engineering/README.md#4-chuẩn-gốc-data-card-và-hợp-đồng-dữ-liệu](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/24-ai-data-engineering/README.md#4-chuẩn-gốc-data-card-và-hợp-đồng-dữ-liệu).

**Khung đã có:** AI-DATA-001/002 đã bắt hash/version và datasheet nguồn/biến đổi/giấy phép;011 yêu cầu nhãn synthetic và tỷ lệ.

**Phần cần bổ sung:** Bổ sung lineage theo từng producer/judge/model/prompt và phiên bản human review, vượt metadata datasheet tổng quan; không lặp89 về quyền dataset.

**Đề xuất SHOULD:** Với pipeline sinh hoặc chấm dữ liệu bằng AI, SHOULD phát hành dataset manifest gồm source IDs/license, input/output hash, recipe revision, generator/judge endpoint và model revision, prompt hash, sampling config, validator và human-review revision nếu có; giữ lý do rejected/retained. Manifest chỉ ra dataset snapshot thực của release; cache và experiment log chỉ là nguồn hỗ trợ. Kiểm thiếu generator/judge revision hoặc không truy được nguồn của một mẫu synthetic thì báo incomplete provenance trước khi chấp nhận snapshot.

**Đối chiếu khung:** [AI-DATA-001](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/data-and-fine-tuning.md#L51), [AI-DATA-002](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/data-and-fine-tuning.md#L52), [AI-DATA-011](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/data-and-fine-tuning.md#L61).

**Liên quan đợt trước:** XT-H-089; chỉ giữ phần delta nêu trên, không cấp yêu cầu song song cho cơ chế đã có.

**Nguồn triển khai upstream:** [nguồn 1](https://github.com/argilla-io/distilabel/blob/313fac85b1a2472dd88db1a31c2b754599f46476/README.md) · [nguồn 2](https://github.com/argilla-io/distilabel/blob/313fac85b1a2472dd88db1a31c2b754599f46476/LICENSE) · [nguồn 3](https://github.com/treeverse/dvc/blob/56e59829512ff134aa269099a2099587b810b4dd/README.rst) · [nguồn 4](https://github.com/treeverse/dvc/blob/56e59829512ff134aa269099a2099587b810b4dd/LICENSE).

### XT-H-098

**Hồ sơ nguồn:** [25-model-adaptation-post-training/README.md#trl](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/25-model-adaptation-post-training/README.md#trl), [25-model-adaptation-post-training/README.md#llamafactory](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/25-model-adaptation-post-training/README.md#llamafactory), [25-model-adaptation-post-training/README.md#5-cổng-chất-lượng-từ-dữ-liệu-đến-runtime](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/25-model-adaptation-post-training/README.md#5-cổng-chất-lượng-từ-dữ-liệu-đến-runtime).

**Khung đã có:** AI-DATA-006 yêu cầu eval trước/sau;009 gắn model với config/eval;010 test pipeline dữ liệu.

**Phần cần bổ sung:** Chưa có cổng kiểm hợp đồng ở ranh giới text→token→labels trước training; không trùng93bàn giao cũ.

**Đề xuất SHOULD:** Với tác vụ SFT/chat/tool-call, SHOULD trước job dài lưu một bộ sample sau chat template/tokenization gồm token IDs, labels/loss mask và phần truncation; kiểm user/system/assistant/tool span đúng mục tiêu đã khai, có token được học và đáp án không bị cắt ngoài chủ ý. Ghim tokenizer/chat-template cùng config. Fixture thiếu generation mask hoặc nhãn toàn -100 phải bị phát hiện, không chỉ nhìn cờ cấu hình của trainer hay loss giảm.

**Đối chiếu khung:** [AI-DATA-006](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/data-and-fine-tuning.md#L56), [AI-DATA-009](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/data-and-fine-tuning.md#L59), [AI-DATA-010](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/data-and-fine-tuning.md#L60).

**Nguồn triển khai upstream:** [nguồn 1](https://github.com/huggingface/trl/blob/c734c60d85766aff4542a00643a2ca7e4a3c72ac/README.md) · [nguồn 2](https://github.com/huggingface/trl/blob/c734c60d85766aff4542a00643a2ca7e4a3c72ac/LICENSE) · [nguồn 3](https://github.com/hiyouga/LlamaFactory/blob/9997aa078b4da35e04bb492a8a27d45141f4b80b/README.md) · [nguồn 4](https://github.com/hiyouga/LlamaFactory/blob/9997aa078b4da35e04bb492a8a27d45141f4b80b/LICENSE).

### XT-H-099

**Hồ sơ nguồn:** [25-model-adaptation-post-training/README.md#peft](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/25-model-adaptation-post-training/README.md#peft), [25-model-adaptation-post-training/README.md#axolotl](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/25-model-adaptation-post-training/README.md#axolotl), [25-model-adaptation-post-training/README.md#5-cổng-chất-lượng-từ-dữ-liệu-đến-runtime](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/25-model-adaptation-post-training/README.md#5-cổng-chất-lượng-từ-dữ-liệu-đến-runtime).

**Khung đã có:** AI-DATA-009 đã version model và yêu cầu deploy eval gate; 006 có baseline/holdout/regression; AI-EVAL-001 kiểm khi đổi model/pipeline.

**Phần cần bổ sung:** Làm rõ cổng sau từng chuyển đổi artifact và binding base/tokenizer/runtime, chưa có trong93bài học cũ.

**Đề xuất SHOULD:** Với model/adapter được merge, quantize hoặc export sang runtime khác, SHOULD có manifest base revision, tokenizer/chat-template, adapter/config, precision, export tool và artifact hash; nạp trong tiến trình sạch rồi chạy lại bộ held-out/regression trên artifact và runtime đích thực. Giữ baseline trước/sau chuyển đổi, latency/RAM khi là mục tiêu; chỉ triển khai artifact đã qua cổng, không dùng việc load thành công thay số đo chất lượng.

**Đối chiếu khung:** [AI-DATA-006](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/data-and-fine-tuning.md#L56), [AI-DATA-009](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/data-and-fine-tuning.md#L59), [AI-EVAL-001](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/evaluation.md#L57).

**Nguồn triển khai upstream:** [nguồn 1](https://github.com/huggingface/peft/blob/d672982142a705f47696db2dd2218805517509cd/README.md) · [nguồn 2](https://github.com/huggingface/peft/blob/d672982142a705f47696db2dd2218805517509cd/LICENSE) · [nguồn 3](https://github.com/axolotl-ai-cloud/axolotl/blob/da7d6b8138d6c0bcf7815ffb2475845dd40718d5/README.md) · [nguồn 4](https://github.com/axolotl-ai-cloud/axolotl/blob/da7d6b8138d6c0bcf7815ffb2475845dd40718d5/LICENSE).

### XT-H-100

**Hồ sơ nguồn:** [26-document-intelligence-ocr/README.md#3-cổng-kiểm-cho-pipeline-tài-liệu](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/26-document-intelligence-ocr/README.md#3-cổng-kiểm-cho-pipeline-tài-liệu), [26-document-intelligence-ocr/README.md#4-bài-học-kiến-trúc](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/26-document-intelligence-ocr/README.md#4-bài-học-kiến-trúc).

**Khung đã có:** BE-FILE-010 có timeout/sandbox cho OCR;AI-DATA-002 có datasheet; AI-EVAL-006 phân hạng claim. Chưa có hợp đồng provenance/outcome cấp trang.

**Phần cần bổ sung:** Bổ sung cơ chế chuyên biệt cho document intelligence; áp dụng khi dự án thực sự xử lý tài liệu, không mở thành MUST toàn mọi sản phẩm.

**Đề xuất SHOULD:** Với OCR/document extraction, SHOULD có ledger từng trang/block: document hash, page, parser/model/config revision, outcome success/fallback/discarded/unmeasured và locator/bbox nếu có. Báo đủ mẫu số trang vào/ra/bỏ; trường schema có citation về bằng chứng gốc hoặc null+reason khi không đọc được, không bịa bbox. Kiểm fixture có một trang fallback hoặc bị loại vẫn xuất hiện trong báo cáo outcome và không được tính như OCR thành công; thay tài liệu/parser/model làm mất hiệu lực cache/evidence cũ.

**Đối chiếu khung:** [BE-FILE-010](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/08-backend/files-and-media.md#L53), [AI-DATA-002](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/data-and-fine-tuning.md#L52), [AI-EVAL-006](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/evaluation.md#L62).

### XT-H-101

**Hồ sơ nguồn:** [27-3d-cad-bim-engineering/README.md#3-cổng-kiểm-theo-biểu-diễn](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/27-3d-cad-bim-engineering/README.md#3-cổng-kiểm-theo-biểu-diễn), [27-3d-cad-bim-engineering/README.md#4-kiến-trúc-agent-sửa-model](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/27-3d-cad-bim-engineering/README.md#4-kiến-trúc-agent-sửa-model).

**Khung đã có:** QA-INT-020 đã có corpus IDS/BCF chuẩn;AI-AGENT-003 kiểm policy trước hành động;PRF-AGENTIC-012 audit hash input/approval.

**Phần cần bổ sung:** Thiếu thang kiểm theo biểu diễn kỹ thuật và stale-preview binding cụ thể. Không thay luật kỹ thuật chuyên ngành bằng một cổng chung hay yêu cầu CAD cho dự án ngoài scope.

**Đề xuất SHOULD:** Với agent sửa CAD/BIM/3D kỹ thuật, SHOULD khai các cổng riêng theo biểu diễn: schema/đơn vị, yêu cầu bàn giao, geometry validity và kết quả host/export; không suy ảnh render, watertight hoặc IDS pass thành mọi lớp đã đạt. Preview/approval giữ model+spec hash, target IDs và diff; model thay sau preview thì phải tạo lại preview/approval phù hợp trước khi áp. Kiểm fixture stale preview, geometry lỗi dù schema đúng và schema đúng nhưng thiếu requirement phải có outcome riêng; không retry mù khi host trả outcome_unknown.

**Đối chiếu khung:** [QA-INT-020](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/14-testing-quality/integration-and-contract.md#L55), [AI-AGENT-003](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/agents-and-tools.md#L60), [PRF-AGENTIC-012](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/02-profiles/agentic-system.md#L81).

### XT-H-102

**Hồ sơ nguồn:** [28-product-discovery-experimentation/README.md#3-chuẩn-phương-pháp-và-cổng-quyết-định](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/28-product-discovery-experimentation/README.md#3-chuẩn-phương-pháp-và-cổng-quyết-định).

**Khung đã có:** PM-METRIC-002 đã có event schema;011 có hypothesis/metric/guardrail/cỡ mẫu/phương pháp trước A/B; AI-EVAL-017 có online guardrail.

**Phần cần bổ sung:** Bổ sung validity của assignment/exposure/data-quality trước phép kiểm effect; 93bàn giao cũ chưa đề cập SRM hay exposure instrumentation.

**Đề xuất SHOULD:** Với thử nghiệm sản phẩm, SHOULD xác định đơn vị randomization và event exposure thực tế tách assignment; giữ event ID/version, join rule, attribution window và consent. Trước diễn giải effect, kiểm missing/duplicate event, join rate, A/A khi phù hợp và Sample Ratio Mismatch theo phương pháp đã chọn. Nếu exposure mất, mẫu số không khớp hoặc evaluator incomplete/unknown thì báo chưa đủ bằng chứng và điều tra instrumentation; không coi lack of significance là hai phương án tương đương. Kiểm fixture variant assignment có nhưng không gửi exposure phải bị phát hiện.

**Đối chiếu khung:** [PM-METRIC-002](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/17-product-project/metrics-and-analytics.md#L42), [PM-METRIC-011](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/17-product-project/metrics-and-analytics.md#L51), [AI-EVAL-017](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/evaluation.md#L73).

### XT-H-103

**Hồ sơ nguồn:** [21-autonomous-workflows/README.md#10f-nâng-trần-toàn-diện-2112026-phục-hồi-idempotency-và-timeout-có-hợp-đồng-kiểm](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/21-autonomous-workflows/README.md#10f-nâng-trần-toàn-diện-2112026-phục-hồi-idempotency-và-timeout-có-hợp-đồng-kiểm), [02-agent-frameworks/README.md#core-framework-semantics](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/02-agent-frameworks/README.md#core-framework-semantics).

**Khung đã có:** AI-AGENTIC-002 đã đòi kill worker đúng1effect;AI-AGENT-005 có key/outcome_unknown/reconcile;ARC-INT-016 có durable flow.

**Phần cần bổ sung:** Không lặp XT-H-066 về bọc I/O thành activity. Delta là failure window external commit→journal, cancellation/total retry budget và retention phải được thử rõ; nguồn SDK chỉ ra cửa sổ chạy lại.

**Đề xuất SHOULD:** Với workflow có external side effect, SHOULD test có chủ đích lỗi sau dịch vụ ngoài đã commit nhưng trước khi activity/step result được persist; dùng business idempotency key/receipt và đọc lại để reconcile trước retry. Khai tổng deadline, retry cap/backoff, heartbeat/cancellation và retention/version của journal. Báo rõ bảo đảm phụ thuộc API đích; checkpoint hay một lần ghi journal không tự bảo đảm external effect đúng một lần. Kiểm lost response ở cửa sổ này và replay/restart không tạo giao dịch thứ hai.

**Đối chiếu khung:** [AI-AGENTIC-002](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/agentic-systems.md#L82), [AI-AGENT-005](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/agents-and-tools.md#L62), [ARC-INT-016](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/05-architecture/integration-patterns.md#L66).

**Liên quan đợt trước:** XT-H-066; chỉ giữ phần delta nêu trên, không cấp yêu cầu song song cho cơ chế đã có.

**Nguồn triển khai upstream:** [nguồn 1](https://github.com/langchain-ai/langgraph/blob/ee3c043bddcc514012885167dd5916b15d6e4731/LICENSE) · [nguồn 2](https://github.com/langchain-ai/langgraph/blob/ee3c043bddcc514012885167dd5916b15d6e4731/libs/langgraph/langgraph/pregel/main.py) · [nguồn 3](https://github.com/pydantic/pydantic-ai/blob/129c94ef2940565af3bc9f638196fcc994d1ed4d/LICENSE) · [nguồn 4](https://github.com/pydantic/pydantic-ai/blob/129c94ef2940565af3bc9f638196fcc994d1ed4d/pydantic_ai_slim/pydantic_ai/usage.py).

### XT-H-104

**Hồ sơ nguồn:** [07-eval-observability/README.md#core-eval-validity](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/07-eval-observability/README.md#core-eval-validity).

**Khung đã có:** AI-EVAL-002/013 đã có record/replay và refresh;018 có n/runs/CI/paired test. Chưa chỉ rõ cache repeat và correlated rows ảnh hưởng tính độc lập.

**Phần cần bổ sung:** Bổ sung ngữ nghĩa repeat cache + đơn vị thống kê/cluster, khác XT-H-073 về judge calibration/task version và092 về environment error.

**Đề xuất SHOULD:** Với eval có repeat/epoch hoặc nhiều câu chung tài liệu/hội thoại, SHOULD báo cache policy, fresh/replay mode, unit of analysis và group/cluster ID. Replay dùng để kiểm hồi quy tất định; khi đo biến thiên sinh mới phải bảo đảm response cache không tái dùng cùng output. Tính uncertainty/test cặp theo đơn vị độc lập hoặc cluster phù hợp, giữ errors/unscored và mẫu số. Fixture hai epoch lấy cùng cached response không được báo thành hai lần sinh độc lập; không dùng giao/không giao hai CI như phép kiểm cặp đầy đủ.

**Đối chiếu khung:** [AI-EVAL-002](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/evaluation.md#L58), [AI-EVAL-013](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/evaluation.md#L69), [AI-EVAL-018](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/evaluation.md#L74).

**Liên quan đợt trước:** XT-H-073, XT-H-092; chỉ giữ phần delta nêu trên, không cấp yêu cầu song song cho cơ chế đã có.

**Nguồn triển khai upstream:** [nguồn 1](https://github.com/promptfoo/promptfoo/blob/bfb96e2ee2304ec87a7a32054a4907ea39f5c920/LICENSE) · [nguồn 2](https://github.com/promptfoo/promptfoo/blob/bfb96e2ee2304ec87a7a32054a4907ea39f5c920/src/evaluator.ts) · [nguồn 3](https://github.com/UKGovernmentBEIS/inspect_ai/blob/1f1a0039d49c628a41898a7a7ba4843c5bbbc91b/LICENSE) · [nguồn 4](https://github.com/UKGovernmentBEIS/inspect_ai/blob/1f1a0039d49c628a41898a7a7ba4843c5bbbc91b/src/inspect_ai/model/_cache.py).

### XT-H-105

**Hồ sơ nguồn:** [14-voice-multimodal/README.md#5e-voice-reliability](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/14-voice-multimodal/README.md#5e-voice-reliability).

**Khung đã có:** BE-RT-013 đã truyền huỷ stream tới model/job; 006 có reconnect replay event; AI-EVAL-007 kiểm final state/pass^k.

**Phần cần bổ sung:** Không lặp XT-H-080 về WER/MOS/video benchmark; thêm vòng đời hội thoại và tách replay transport/audio khỏi execution receipt.

**Đề xuất SHOULD:** Với voice agent streaming, SHOULD gắn session/turn ID qua STT→model/tool→TTS/playback và đo completion, interruption/barge-in, reconnect theo cùng turn/episode. Tách playback retry khỏi tool execution; ghi receipt/idempotency cho tác vụ ghi để reconnect hoặc replay audio không kích tool lần nữa. Kiểm fixture ngắt lời giữa TTS và mất mạng sau tool commit: audio dừng/khôi phục theo hợp đồng và chỉ một side effect. Báo latency từng tầng, lỗi và task outcome bên cạnh WER/MOS.

**Đối chiếu khung:** [BE-RT-013](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/08-backend/realtime-and-streaming.md#L56), [BE-RT-006](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/08-backend/realtime-and-streaming.md#L49), [AI-EVAL-007](https://github.com/seeker19110/X-Templates/blob/24f221bd992560525a917a9fee1154a53fb67347/framework/13-ai-engineering/evaluation.md#L63).

**Liên quan đợt trước:** XT-H-080; chỉ giữ phần delta nêu trên, không cấp yêu cầu song song cho cơ chế đã có.

**Nguồn triển khai upstream:** [nguồn 1](https://github.com/snakers4/silero-vad/tree/066409f3d9db45a30d21dfcbf9147826ffdd7052) · [nguồn 2](https://github.com/aiortc/aiortc/tree/d6a003fcb6511675318b4494e5b225b78abd2af2).

## 4. Thứ tự gợi ý và giới hạn áp dụng

1. **Cổng đang có nhưng có thể xanh giả:**094 (locale trước fallback), 095 (requested/served docs), 104 (cache và đơn vị mẫu). Bổ sung phép kiểm âm tại đúng nhà hiện có trước khi tạo công cụ mới.
2. **Vòng đời dữ liệu/model:**096–099. Chỉ áp cho dự án tạo dataset hoặc huấn luyện/xuất model; giữ nguồn/cluster, loss-mask và eval artifact cuối.
3. **Tính năng có tác dụng phụ:**103 và 105. Kiểm cửa sổ external commit→journal, receipt/idempotency và turn/episode; không suy replay thành exactly-once.
4. **Hợp đồng theo miền:**100 (OCR), 101 (CAD/BIM), 102 (thí nghiệm sản phẩm). Dùng requirement có điều kiện hoặc profile/ngành phù hợp; không biến thành MUST cho mọi blueprint.

Phiên triển khai tiếp theo cần tự quyết cách gộp vào ID hiện có hay cấp ID mới; cập nhật module/README/CHANGELOG và ADR khi quy tắc khung yêu cầu. Research note này không cài thêm stack, không sửa blueprint dự án đích và không tự bật auto-merge.

## 5. Nguồn và trạng thái xác minh

- [stored: phương pháp và mức bằng chứng](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/METHOD.md), [catalog](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/data/projects.json), [nguồn](https://github.com/seeker19110/stored/blob/d8d2708377933491107c0cd3f2f88f64da95ba34/SOURCES.md).
- Nguồn trực tiếp và ngày/SHA ở từng hồ sơ phía stored; những chỗ **(chưa xác minh)** hoặc chưa chạy giữ nguyên mức đó. Đọc lại khung ngày 2026-11-02 không nâng bằng chứng đọc mã upstream thành benchmark được tái lập.
- Đã so với các note stored-delta trước và 93 bàn giao cũ. Những dòng có related_handoffs chỉ đề xuất phần sâu hơn: propagation theo cluster, post-export eval, exposure, external commit window và đơn vị mẫu.
