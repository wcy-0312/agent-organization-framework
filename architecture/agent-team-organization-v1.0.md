# Agent Team Organization — Architecture Design
# Version 1.0

> 本文件記錄 Agent Team Skill 的完整架構設計，作為後續 skill 撰寫的規格輸入。
> 內容來自設計討論，尚未實作。
> 標記為 v1.0：核心架構已穩定，但仍有 Open Questions 待未來討論。

---

## 設計原則

1. **Mission 最穩定，Checkpoint Plan 最常變動**，Team、Protocol、Rules 介於兩者之間
2. **Governance 是規則引擎，不是獨立角色**——治理由文件定義，由 Orchestrator 執行
3. **規則保持精簡，案例承載複雜性**——經驗放進 Case Library，不自動提升為規則
4. **Checkpoint 綁定決策點，不綁定步驟完成**——有足夠新認識才觸發
5. **有意識的遺忘是必要設計**——資訊分三類，不是所有資訊都值得傳遞
6. **Artifact Layer 與 Governance Layer 分離**——產出本體在工作區，治理索引在 `.agent-org/`

---

## 目錄結構

```
project-root/
├── .agent-org/
│   ├── mission-contract.md
│   ├── team-roster.md
│   ├── governance-rules.md
│   ├── review-protocol.md
│   ├── replanning-rules.md
│   ├── team-evolution-rules.md
│   ├── artifact-backend.md
│   ├── artifact-manifest.md
│   ├── discard-log.md
│   │
│   ├── current/
│   │   ├── staging-buffer.md
│   │   └── handoff-package.md
│   │
│   ├── archive/
│   │   └── checkpoint-N/
│   │       ├── staging-buffer.md
│   │       └── handoff-package.md
│   │
│   └── memory/
│       ├── decision-log.md
│       └── case-library/
│
├── src/
├── docs/
├── benchmarks/
├── artifacts/
└── ...
```

職責邊界：`.agent-org/` 裡沒有任何任務產出本體；project-root 工作區裡沒有任何治理文件。

---

## 文件規格

### 穩定層（幾乎不變）

#### `mission-contract.md`
任務的根本目標與邊界。只有在核心假設被推翻時才修訂，需要人工介入確認。

內容包含：
- 任務目標與成功定義
- 明確的 in-scope / out-of-scope
- 不可逾越的限制條件

---

### 治理層（checkpoint 後可修訂，高門檻）

#### `team-roster.md`
定義此次任務的 Agent 角色組成。

每個角色包含：
- 角色名稱與職責描述
- 對應的 system prompt 範本
- 職責邊界（做什麼、不做什麼）
- 依賴關係（需要哪些角色的輸出）

修訂規則：只能在 checkpoint review 後正式修訂，且需要 Orchestrator 明確決策並記錄於 `decision-log.md`。

---

#### `governance-rules.md`
治理的基本規則，精簡且穩定。門檻：某個模式在至少三個不同案例中出現，才考慮提升為規則。

內容包含：
- 哪些層級的文件可以在什麼條件下修訂
- Orchestrator 行使裁量權的邊界
- 規則空白地帶的處理方式（記錄為 decision，而非即興發揮）

---

#### `review-protocol.md`
定義每個 checkpoint 的評估標準。

內容包含：
- Checkpoint 觸發條件（決策點，非步驟完成）
- 評估維度與 acceptance criteria
- 誰有資格宣告一個階段完成
- Verifier 審查 handoff-package 的檢查清單

---

#### `replanning-rules.md`
定義何時允許修改後續計畫。

發現嚴重性分級：

| 等級 | 描述 | 處置 |
|------|------|------|
| 小發現 | 不影響方向，只影響細節 | Executor 自行調整，記錄至 staging-buffer |
| 中發現 | 影響當前步驟的方法 | Orchestrator + 相關 Lead 開會 |
| 大發現 | 推翻核心假設 | 全員開會，mission-contract 可能需要修訂，人工介入 |

---

#### `team-evolution-rules.md`
定義何時允許修改 team-roster，門檻高於 replanning。

提案格式（由任何 Lead 提出）：
- 發現了什麼能力缺口
- 缺口造成什麼風險
- 是否符合 team-evolution-rules 的修訂條件

由 Orchestrator 根據規則批准或駁回，結果記錄至 `decision-log.md`。

---

### Artifact Layer

#### `artifact-backend.md`
定義本任務使用哪種 Artifact Backend 及其操作規範。

三種 Backend：

| Backend | Executor 提交方式 | Verifier 審查介面 | Orchestrator 決策 |
|---------|-----------------|-----------------|-----------------|
| GitHub | branch + PR | PR review / inline comment | merge 或 request changes |
| local-git | commit + patch file | diff review | cherry-pick 或 revert |
| folder | 寫入 `artifacts/` + 更新 manifest | 讀 manifest + 檢查檔案 | manifest 標記 approved / rejected |

必要欄位：
- `backend_type`: github | local-git | folder
- `submit_protocol`: Executor 如何提交工作單位
- `review_protocol`: Verifier 如何審查（對應 review-protocol.md 的 checklist）
- `approve_protocol`: Orchestrator 如何批准或駁回
- `large_asset_policy`: path、checksum、storage location 的管理規則

注意：folder backend 缺少內建 diff 機制，需在 manifest 設計「版本號 + 前一版 reference」欄位，讓 Verifier 知道本次提交相對於上次的變化。

---

#### `artifact-manifest.md`
所有 backend 共用的 artifact 統一索引。放在 `.agent-org/` 內——它是治理索引，不是產出本身。

每筆記錄欄位：
- `artifact_id`: 唯一識別碼
- `checkpoint`: 對應的 checkpoint 編號
- `type`: code | config | schema | report | benchmark | prompt | test | other
- `path`: 產出的實際路徑（相對於 project-root）
- `version`: 版本號
- `previous_version`: 前一版的 artifact_id
- `produced_by`: 產生此 artifact 的 Agent role
- `review_status`: 見狀態機定義
- `checksum`: 檔案雜湊，用於驗證完整性
- `large_asset`: 是否為大型資產（不進版本控制，只存 reference）
- `notes`: 補充說明

`review_status` 狀態機：
```
pending    → Executor 已提交，等待審查
in-review  → Verifier 正在審查
approved   → Orchestrator 批准
rejected   → Orchestrator 駁回，需要 Executor 修改
superseded → 被新版本取代（previous_version 欄位指向它）
```

handoff-package 中引用 artifact 時，一律使用 `artifact_id`，不使用路徑，避免因檔案搬移造成斷鏈。

---

### 執行層（高頻運作）

#### `current/staging-buffer.md`
**階段級文件。** 執行中的待分類資訊佇列。

規則：
- 執行 Agent 可以隨時寫入
- 每一條必須包含：摘要、來源、為什麼可能重要、關聯 artifact_id
- 不允許直接塞入完整討論或大段內容
- 每個 checkpoint review 必須清空
- 清空方式只有四種：進 handoff、進 archive、提升 memory、discard

---

#### `current/handoff-package.md`
**階段級文件。** 下一個 Agent 接手所需的最小必要 context。

更新職責：
- **由 Orchestrator 產生**（在 checkpoint review 後）
- **由 Verifier 審查**（依據 `review-protocol.md` 的 acceptance criteria）
- 執行 Agent 不可直接修改

內容包含：
- 當前任務狀態摘要
- 已確認的決策與理由（引用 artifact_id，不塞入 artifact 內容）
- 下一個階段的起點
- 需要特別注意的風險或未解決問題

---

### 記憶層（跨任務）

#### `memory/decision-log.md`
**跨任務的組織記憶。** 記錄每一次 Orchestrator 行使裁量權（規則未覆蓋的情況）的過程與結果。

用途：供未來任務參考，作為 case library 的人工篩選來源，不自動提升為規則。

每筆記錄包含：
- 任務 ID 與 checkpoint
- 遭遇的情況
- 可用規則是否覆蓋
- 決策內容與理由
- 事後評估（結果如何）

---

#### `memory/case-library/`
跨任務的經驗庫。每個案例是一份獨立文件。

案例來源：從 `decision-log.md` 中**人工篩選**出值得長期保留的非平凡決策。
提升門檻：某個模式在至少三個不同案例中出現，才考慮提升為 governance rule。

---

#### `discard-log.md`
記錄有意識丟棄的資訊，包含丟棄理由。確保「遺忘」是可審計的，而非意外遺失。

---

## 資訊分流機制

### 三類資訊

| 類別 | 定義 | 去向 |
|------|------|------|
| Must Carry Forward | 下一個 Agent 必須知道 | `current/handoff-package.md` |
| Archive Only | 保留但不主動載入，需要時可查 | `archive/checkpoint-N/` |
| Discard | 確定沒有價值 | `discard-log.md`（記錄理由） |

### 時間設計

**執行中：**
- Agent 把 Must Carry Forward 的資訊放進 staging-buffer（標記類別）
- 不確定的資訊放進 staging-buffer（待分類）
- 確定無價值的細節不記錄

**Checkpoint Review 時：**
- Orchestrator + Verifier 掃描 `current/staging-buffer.md`
- 對每一條做分類決定（四選一）
- Orchestrator 產生新的 `current/handoff-package.md`
- Verifier 審查 handoff-package
- 舊的 staging-buffer 和 handoff-package 歸檔至 `archive/checkpoint-N/`
- 判斷 archive 裡有無值得提升至 `memory/` 的內容
- 下一個 checkpoint 重新建立空白的 `current/staging-buffer.md`

---

## Agent 角色職責

### Orchestrator（Team Lead / main window）
- 不直接執行任務
- 分派步驟給 Executor Lead
- 接收 Verifier 的審查結果
- 決定是否召集開會
- 批准或駁回 replanning / team-evolution 提案
- 產生 `current/handoff-package.md`
- 在規則空白地帶行使裁量權，並記錄至 `decision-log.md`

### Executor Lead（Teammate）
- 接收 Orchestrator 的執行指令
- 派發 subagent 執行
- 彙整執行結果與 artifact
- 寫入 `current/staging-buffer.md`
- 依 `artifact-backend.md` 提交工作單位

### Verifier Lead（Teammate）
- 接收 Executor Lead 的執行結果
- 派發 subagent 審查
- 依據 `review-protocol.md` 的 acceptance criteria 判斷
- 更新 `artifact-manifest.md` 的 review_status
- 回報審查結果給 Orchestrator
- 在 checkpoint review 時審查 handoff-package

### Subagents
- 由各 Lead 派發，執行具體工作
- Context 僅包含當前任務所需的最小必要資訊

---

## Checkpoint 完整流程

```
1. 觸發條件達成（決策點，非步驟完成）
2. Executor Lead 彙整執行結果，依 artifact-backend 提交
3. Verifier Lead 審查，更新 artifact-manifest review_status
4. Orchestrator 召集 checkpoint review
   ├── 清空 current/staging-buffer.md（四選一分類）
   ├── 產生新的 current/handoff-package.md（引用 artifact_id）
   ├── Verifier 審查 handoff-package
   ├── 歸檔至 archive/checkpoint-N/
   ├── 判斷是否有 memory 值得提升
   ├── 判斷發現的嚴重性（replanning-rules）
   └── 判斷是否需要 team-evolution
5. Orchestrator 宣告 checkpoint 完成，進入下一階段
```

---

## 任何 Agent 的「應該讀什麼」

| 情況 | 讀取目標 |
|------|---------|
| 剛接手任務 | `current/handoff-package.md` + 所有 `.agent-org/` 治理文件 |
| 執行中遇到不確定資訊 | 寫入 `current/staging-buffer.md` |
| 引用任務產出 | 查 `artifact-manifest.md`，使用 artifact_id |
| 需要追溯歷史決策 | 查 `archive/` |
| 需要跨任務經驗 | 查 `memory/` |
| 任何時候 | 不需要讀所有東西 |

---

## Open Questions

以下問題在 v1.0 討論中刻意延後，留待下一輪討論。

### OQ-001：Agent Team Skill 是 Generator 還是 Manager？

目前架構的定位是：計畫書確認後 → 執行 Agent Team Skill → 產生 `.agent-org/`

但 Team Evolution、Checkpoint Review、Memory 整理都需要在執行中持續維護。這讓 Agent Team Skill 可能更像一個長期存在的 Organization Manager，而不只是初始化工具。

待釐清：Skill 的職責邊界在初始化之後是否延續？還是後續維護由 Orchestrator 自主處理？

---

### OQ-002：Case Library 如何擴展？

當案例從 10 個成長到 1000 個時：
- 如何索引？
- 如何檢索？
- 如何選出與當前任務最相關的案例？

這可能會演化成一個獨立的 Memory Retrieval 問題，需要 tag、index、甚至 embedding 機制。

---

### OQ-003：Role 是否擁有自己的記憶？

目前 Memory Layer 是 Organization 級別（跨任務共用）。

但若 Executor 是 Python Expert、Verifier 是 Research Reviewer，他們是否應該在不同任務間累積自己的經驗？

待釐清：
- Organization Memory（現有）
- Role Memory（尚未設計）

兩者是否需要分開管理？

---

### OQ-004：Memory Layer 是否需要向量化？

目前 Memory 是純文件集合，依賴人工篩選與 Orchestrator 主動查詢。

案例量成長後，可能需要：
- tag 與 index
- embedding
- semantic retrieval

屆時 Memory Layer 可能需要演化成獨立的 Memory Backend，而非單純的 markdown 資料夾。

---

## 版本紀錄

| 版本 | 內容 |
|------|------|
| v1.0 | 完成 Governance、Memory、Handoff、Artifact 四個 Layer 的核心設計 |

---

*下一輪討論主題：Agent Organization 的長期演化——OQ-001 到 OQ-004*
