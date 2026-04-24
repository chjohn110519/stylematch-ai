# PRD: StyleMatch AI
### 연예인 착장 → SSF SHOP 유사 상품 매칭 엔진 (MVP)

| 항목 | 내용 |
|---|---|
| 문서 버전 | v1.1 |
| 작성일 | 2026-04-24 |
| 최종 수정 | 2026-04-24 (SSF 실제 데이터 반영) |
| 작성자 | 지안 |
| 제품 코드명 | StyleMatch AI |
| MVP 기간 | 4주 (혼자 개발) |
| MVP 목표 | SSF SHOP MD팀 대상 라이브 데모에서 "해볼만하다" 판단 끌어내기 |

---

## 1. 제품 개요

### 1.1 한 줄 정의
연예인 착장 사진을 업로드하면, SSF SHOP 상품 DB에서 시각적·속성적으로 유사한 상품 3~5개를 자동 매칭해 제시하는 AI 큐레이션 엔진.

### 1.2 해결하는 문제

**팬덤 사용자 관점**
- 최애 연예인이 입은 옷을 찾고 싶은데, 동일 상품은 하이엔드/품절/해외 브랜드라 접근 불가
- "비슷한 옷"을 찾으려면 직접 검색어를 조합하며 여러 쇼핑몰을 돌아야 함
- 결국 포기하거나 무신사/구글 이미지 검색으로 흩어짐

**SSF SHOP 관점**
- 수천 개 재고 중 "연예인 스타일과 연결될 수 있는 상품"이 숨어있지만 발굴이 어려움
- 팬덤 트래픽이라는 고관여·고구매의향 사용자 풀을 놓치고 있음
- 경쟁사(무신사·29CM)는 스트릿 중심이라 SSF의 컨템포러리 포지션을 활용한 팬덤 유입 채널이 공백

### 1.3 해결 방식

이미지 → AI 속성 분해(카테고리·실루엣·컬러·패턴·디테일·무드) → SSF 상품 DB에서 속성 기반 매칭 → Top-K 유사 상품 반환.

### 1.4 제품 경계 (Scope)

**MVP에 포함**
- 연예인 착장 이미지 업로드 (단일 이미지)
- 이미지에서 최대 3개 아이템 자동 분해 (상의·하의·아우터)
- 각 아이템별 SSF 유사 상품 Top 3~5 매칭
- 매칭 근거 텍스트 자동 생성 ("왜 유사한가")
- 웹 기반 데모 UI (Streamlit)

**MVP에 포함하지 않음 (명시적 제외)**
- 신발·가방·액세서리 매칭 (세그멘테이션 난이도와 SSF 재고 집중도 고려)
- 다중 이미지 업로드
- 사용자 계정·히스토리
- 실제 SSF 상품 DB 연동 (크롤링 기반 대체 DB 사용)
- 팬덤 코너 UI 내 삽입형 위젯 (파트너십 체결 후 2차 개발)
- 모바일 최적화
- 결제·장바구니 연동

---

## 2. 사용자 및 이해관계자

### 2.1 1차 사용자 (MVP 단계)
**SSF MD팀 실무자·의사결정권자** — 데모를 보고 파트너십 가치를 판단함.

### 2.2 2차 사용자 (파트너십 체결 후)
**SSF SHOP 방문 팬덤 사용자** — 실제 최종 소비자.

### 2.3 데모 사용자 시나리오
1. MD팀 미팅 자리에서 지안님이 노트북으로 데모 실행
2. MD팀이 그 자리에서 직접 검색한 연예인 사진을 업로드
3. 10초 이내에 SSF 내 유사 상품 3~5개가 시각적 근거와 함께 제시됨
4. MD팀이 "이게 진짜 유사하네" "왜 유사한지 설명이 있네" 두 가지 반응을 보이면 성공

---

## 3. 핵심 사용자 플로우

```
[1] 사용자가 연예인 사진 업로드 (jpg/png, 10MB 이하)
       ↓
[2] Claude Vision API가 이미지 내 의류 아이템 분해
    → JSON: [{item_id: 1, category: "아우터", bbox: [...]}, ...]
       ↓
[3] 각 아이템별 속성 추출
    → {category, silhouette, color, pattern, material_guess, details, mood}
       ↓
[4] SSF 상품 DB에서 속성 매칭
    (카테고리 하드필터 → 속성 유사도 계산 → Top-K 선별)
       ↓
[5] LLM이 매칭 근거 텍스트 생성
    "오버사이즈 실루엣과 베이지 톤, 후드 디테일이 유사"
       ↓
[6] UI에 결과 렌더링
    (원본 이미지 + 감지된 바운딩박스 + 아이템별 매칭 Top 5)
```

---

## 4. 기능 요구사항

### 4.1 데이터 수집 모듈 (Week 1)

**F-01: SSF 상품 DB 로더** *(변경: 크롤러 → JSON 임포터)*
- ~~대상: www.ssfshop.com 카테고리별 상품 리스트~~
- **입력: `scnt.a_items.json` — SSF 실제 상품 데이터 11,345개 제공됨**
- 수집 필드: `godNo, brandCode, brandName, class, category, subcategory, gender, tagPrice, imageUrl, attribute[], color[], priceRange`
- **규모: 10,938개 (의류 class 한정: TOP/BOTTOM/OUTER/TOP_L, BAG/SHOES 제외)**
  - TOP: 5,498개 · BOTTOM: 3,065개 · OUTER: 1,267개 · TOP_L: 1,108개
- **실행: 1회성 JSON → SQLite 임포트 (`src/data_loader.py`)**
- 저장: SQLite (`ssf_products.db`) — 이미지는 CDN URL 직접 사용 (로컬 저장 불필요)
- **속성 체계: SSF 기존 att01/attVal 코드 체계 활용** (COLOR 34값, FIT 31값, PATTERN 37값 등 18개 속성 타입)

**F-02: 데모용 연예인 이미지 샘플 세트**
- 자체 준비: 네이버 엔터 포토에서 수동으로 30~50장 수집 (데모 리허설·QA용)
- 원본 URL과 촬영 매체 기록 (출처 표기용)

### 4.2 비전 분석 모듈 (Week 2)

**F-03: 의류 아이템 분해**
- 입력: 연예인 사진 1장
- 처리: Claude Vision API 호출
- 출력 JSON 스키마:
```json
{
  "items": [
    {
      "item_id": 1,
      "category": "outer",
      "subcategory": "blazer",
      "bbox_description": "상반신 좌우 가장자리까지 덮는 검은색 아우터"
    }
  ]
}
```
- 요구사항: 최대 3개 아이템까지 (상의·하의·아우터 우선)
- 실패 케이스 처리: 아이템이 0개 감지되면 "이미지에서 의류를 찾지 못함" 메시지

**F-04: 속성 추출**
- 입력: 의류 이미지(크롭 또는 원본) + 아이템 정보
- 처리: Claude Vision API 호출 (구조화 프롬프트)
- 출력 JSON 스키마:
```json
{
  "category": "outer",
  "subcategory": "blazer",
  "silhouette": "oversized",
  "length": "hip",
  "primary_color": "black",
  "secondary_colors": [],
  "pattern": "solid",
  "material_guess": "wool_blend",
  "details": ["notch_lapel", "double_breasted", "shoulder_pad"],
  "mood": ["formal", "minimal"],
  "gender_impression": "unisex"
}
```
- 속성 값 사전(enum) 정의 필요 → 매칭 일관성 확보

**F-05: SSF 상품 DB 속성 인덱싱** *(변경: Claude 배치 → 기존 데이터 직접 활용)*
- ~~크롤링한 3,000개 상품 각각에 대해 F-04와 동일 스키마로 속성 추출~~
- ~~배치 실행 (비용 관리: $0.01 × 3,000 = ~$30 예상)~~
- **`scnt.a_items.json`에 속성(attribute[])이 이미 포함되어 있어 Claude 배치 인덱싱 불필요 → $30 절감**
- JSON → SQLite 임포트 시 `product_attrs` 테이블에 att01/attVal 평탄화 저장
- **Claude↔SSF 속성 매핑 레이어(`schema.py`)**: 쿼리 이미지 분석 결과를 SSF 속성 코드로 변환

### 4.3 매칭 엔진 (Week 3)

**F-06: Hybrid Retrieval** *(가중치 조정: SSF 데이터 특성 반영)*

1단계: 하드 필터 (SQL)
- `class` 일치 (TOP / BOTTOM / OUTER)
- `gender` 호환 (WOMEN/MEN/ALL — ALL은 모두 매칭)

2단계: 소프트 스코어링
- SSF `product_attrs` 테이블의 att01/attVal을 직접 활용
- 쿼리 속성(Claude 추출) → SSF 코드 변환 후 집합 매칭
```
score = 0.30 * color_match      ← LAB 근접 색상 포함 (SSF 34색 코드 기반)
      + 0.25 * fit_match         ← silhouette → SSF FIT 코드 매핑
      + 0.20 * pattern_match     ← SSF PATTERN 코드 직접 비교
      + 0.15 * texture_match     ← SSF TEXTURE 코드 (DENIM/WOOL/KNITTING 등)
      + 0.10 * style_tpo_match   ← SSF STYLE_TPO / STYLE_IMAGE 코드
```
- 색상 유사도: SSF 34개 색상 코드 → CIE LAB 매핑 테이블 (`color_map.py`)

3단계: Top-5 선별 + 최소 스코어 임계값 (0.4 미만은 "유사 상품 부족" 표시)

**F-07: 매칭 근거 텍스트 생성**
- 입력: 쿼리 속성 + 매칭된 상품 속성
- 처리: Claude API로 "왜 유사한가" 한 문장 생성
- 예시: "오버사이즈 실루엣과 블랙 컬러, 더블브레스트 디테일이 유사합니다"
- 길이: 40자 이내

### 4.4 데모 UI (Week 4)

**F-08: 업로드 페이지**
- 기술: Streamlit
- 컴포넌트:
  - 이미지 업로드 영역 (드래그앤드롭)
  - 로딩 인디케이터 (예상 10~15초)
  - 결과 영역

**F-09: 결과 디스플레이**
- 상단: 원본 이미지 + 감지된 아이템 시각화 (PIL로 bbox 그리기 또는 색상 주석)
- 하단: 아이템별 섹션
  - 왼쪽: 감지된 속성 요약 카드
  - 오른쪽: SSF 매칭 상품 Top 3~5 카드 (이미지·브랜드·상품명·가격·매칭 근거)

**F-10: 데모 시나리오 사전 테스트**
- 준비된 샘플 30~50장으로 매칭 품질 수동 검증
- Top 10 "확실한 wow" 케이스를 별도 북마크 (MD팀 미팅 플랜 B)

---

## 5. 비기능 요구사항

### 5.1 성능
- 이미지 업로드 → 결과 표시: **15초 이내** (Claude Vision API 응답 시간이 대부분)
- 매칭 엔진 자체: **1초 이내** (10,938개 상품 순회는 단순 연산)

### 5.2 비용
- API 비용 예산: 4주간 **$100 이내** (실제 예상 ~$70)
  - ~~상품 DB 속성 인덱싱: ~$30 (1회성)~~ → **$0 절감** (SSF 데이터에 속성 내장)
  - 개발·테스트 중 호출: ~$40
  - MD팀 데모 당일 여유분: ~$30
- 초과 시 대응: 이미지 리사이즈(장변 512px 제한)로 토큰 절감

### 5.3 정확도 (자체 검증 기준)
- 30장 샘플셋 기준 **Top-5 안에 "주관적으로 유사하다고 판단되는 상품" 3개 이상 포함** = 67% 이상
- 이 수치가 데모 슬라이드의 핵심 정량 지표

### 5.4 저작권·법적 리스크 관리
- 업로드 이미지: 세션 메모리에만 저장, 영구 저장 X (서버리스 원칙)
- SSF 크롤링 데이터: MVP 데모 내부 용도 한정, 외부 배포·재판매 금지 명시
- MD팀 미팅 자료에 "저작권 대응 로드맵" 한 슬라이드 포함:
  - 단계 1 (현재): 내부 데모, 이미지 영구 저장 X
  - 단계 2 (출시): 연예인 사진 비노출, SSF 상품만 노출 + 원본 아웃링크
  - 단계 3 (스케일): 소속사 공식 제휴

---

## 6. 4주 실행 계획

### Week 1: 데이터 기반 구축
| 일차 | 작업 | 산출물 |
|---|---|---|
| D1 | ~~SSF 크롤러 개발~~ → **JSON 로더 + DB 스키마 설계** | `data_loader.py`, `db_init.py` |
| D2 | **`scnt.a_items.json` → SQLite 임포트 (10,938개)** | `ssf_products.db` |
| D3 | **속성 스키마 + Claude↔SSF 매핑 함수 구현** | `schema.py`, `color_map.py` |
| D4~D5 | 데이터 품질 검수 (결측·중복 제거) | 정제된 DB |
| D6~D7 | 데모용 연예인 샘플 30~50장 수동 수집 | `demo_samples/` |

### Week 2: AI 분석 파이프라인
| 일차 | 작업 | 산출물 |
|---|---|---|
| D8~D9 | Claude Vision API 래퍼 + 프롬프트 설계 (SSF 어휘 기반) | `vision_analyzer.py` |
| D10 | 프롬프트 3종 완성 + enum 제약 검증 | `prompts/*.txt` |
| ~~D11~D12~~ | ~~SSF 상품 3,000개 속성 추출 배치~~ → **불필요 ($30 절감)** | *(생략)* |
| D11~D14 | 연예인 이미지 30장 속성 추출 테스트 + 품질 검증 | 정확도 리포트 |

### Week 3: 매칭 엔진
| 일차 | 작업 | 산출물 |
|---|---|---|
| D15~D16 | 유사도 함수 구현 + 가중치 튜닝 | `matcher.py` |
| D17 | 색상 유사도 테이블 구축 (색상명 → LAB) | `color_map.py` |
| D18~D19 | 매칭 근거 텍스트 생성기 | `explainer.py` |
| D20~D21 | End-to-end 파이프라인 통합 테스트 | 동작하는 CLI 버전 |

### Week 4: 데모 UI + 리허설
| 일차 | 작업 | 산출물 |
|---|---|---|
| D22~D23 | Streamlit UI 개발 | `app.py` |
| D24 | 시각화 레이어 (bbox, 속성 카드) | UI 완성본 |
| D25 | 30장 전체 리허설 + 실패 케이스 분석 | 품질 리포트 |
| D26~D27 | 데모 슬라이드 덱 작성 (5분 피치용) | `pitch_deck.pdf` |
| D28 | 최종 리허설 + 예비 시나리오 준비 | 데모 준비 완료 |

---

## 7. 기술 아키텍처

### 7.1 스택
- **언어**: Python 3.11
- **AI API**: Anthropic Claude Vision (claude-sonnet-4-6 기본, 품질 부족 시 claude-opus-4-7 전환)
- ~~**크롤링**: Playwright (JS 렌더링 필요) 또는 httpx + selectolax~~ → **불필요** (데이터 제공됨)
- **DB**: SQLite (MVP에 충분, 파일 1개로 이식성 확보)
- **UI**: Streamlit (1인 4주 제약 고려)
- **이미지 처리**: Pillow (색상 분석은 color_map.py의 LAB 테이블로 대체)
- **환경관리**: uv 또는 poetry

### 7.2 디렉토리 구조
```
stylematch/
├── data/
│   ├── scnt.a_items.json    # 입력: SSF 실제 상품 데이터 (11,345개)
│   ├── ssf_products.db      # 생성: JSON → SQLite 변환본
│   └── demo_samples/        # 연예인 샘플 이미지 30~50장
├── src/
│   ├── schema.py            # SSF 속성 코드 + Claude↔SSF 매핑 함수
│   ├── db_init.py           # SQLite 테이블/인덱스 생성
│   ├── data_loader.py       # F-01: JSON → SQLite 임포터
│   ├── vision_analyzer.py   # F-03, F-04: 쿼리 이미지 분석
│   ├── matcher.py           # F-06: 하이브리드 매칭 엔진
│   ├── explainer.py         # F-07: 매칭 근거 텍스트 생성
│   └── color_map.py         # SSF 34색 코드 → CIE LAB 매핑
├── app.py                   # Streamlit UI
├── tests/
│   └── eval_matcher.py      # 30장 샘플 자동 평가
├── prompts/
│   ├── item_detection.txt
│   ├── attribute_extraction.txt  # SSF 어휘 기반 제약 포함
│   └── match_explanation.txt
├── .env
└── pyproject.toml
```

### 7.3 Claude Vision 프롬프트 설계 원칙
- 속성 추출: 구조화 JSON 출력 강제 (response format 명시)
- 속성값은 미리 정의한 enum 중에서만 선택하도록 제약 (매칭 일관성 핵심)
- Few-shot 예시 3~5개 프롬프트에 포함 (한국 패션 맥락 반영)

---

## 8. 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|---|---|---|
| ~~SSF 크롤링 차단 (robots.txt·rate limit)~~ | ~~높음~~ | **해소됨** — 실제 데이터 제공으로 크롤링 불필요 |
| Claude Vision 속성 일관성 부족 | 높음 | enum 강제 + few-shot, 재시도 로직, 낮은 신뢰도 응답은 수동 검수 큐로 |
| 매칭 품질이 "wow" 못 만듦 | 중간 | 30장 QA에서 Top 10 "골든 샘플" 확보 → 데모 때 이 중심으로 시연 |
| API 비용 초과 | 낮음 | 이미지 리사이즈 + 캐싱 (동일 이미지 재분석 방지) |
| 혼자 4주에 못 끝냄 | 중간 | Week 4에 UI는 최소한만, 백엔드 품질 우선. UI는 "그냥 돌아가는" 수준으로 타협 |
| MD팀이 "실제 SSF DB 아니잖아" 반박 | 중간 | 제안서에 "현재 단계는 공개 정보 기반 PoC, 파트너십 후 실제 DB 연동 시 정확도 X% 향상 예상" 프레임 |

---

## 9. 성공 기준 (Definition of Done)

### 9.1 기술적 완성도
- [ ] SSF 상품 10,938개 SQLite 임포트 완료 (`scnt.a_items.json` → `ssf_products.db`)
- [ ] 연예인 이미지 업로드 → 결과 표시 E2E 파이프라인 15초 이내 동작
- [ ] 30장 QA 샘플 기준 "Top-5 내 주관적 유사 상품 3개 이상" 달성률 ≥ 67%
- [ ] Streamlit UI가 네트워크 끊김 없이 5분 이상 안정 동작

### 9.2 파트너십 준비도
- [ ] 5분 피치 덱 완성 (문제-솔루션-데모-로드맵-제안)
- [ ] 라이브 데모 실패 대비 "골든 샘플 10장" 사전 녹화 또는 스크린샷 세트 확보
- [ ] 저작권 대응 로드맵 한 슬라이드
- [ ] SSF 측 ROI 수치 시뮬레이션 (추정치라도 OK — "월 10만 팬덤 세션 × 3% CVR 가정 시…")

### 9.3 최종 판정
**MD팀 첫 미팅 후 "팀 내부 논의해볼 테니 자료 더 보내달라" 이상의 반응을 얻으면 MVP 성공.**

---

## 10. 오픈 이슈 (다음 결정 필요)

1. **SSF 접촉 루트** — Cold outreach? 삼성물산 출신 멘토·교수 네트워크? POSTECH 창업지원단 경유?
2. **크롤링 법적 검토** — MVP 내부 용도는 괜찮지만 제안서 제시 전 한번 더 확인 필요
3. **데모 영상 사전 녹화 여부** — 라이브 실패 대비 백업 영상 준비할지
4. **Capstone/창업대회 일정과의 우선순위 충돌** — 4주 중 경쟁 마감이 있는 주차에 대한 버퍼 계획

---

## 부록 A: 속성 스키마 enum (v1.1 — SSF 실제 데이터 기반으로 갱신)

> SSF 원본 코드를 직접 사용. Claude 쿼리 어휘는 별도 정의 후 매핑.

```python
# === SSF 원본 속성 코드 (product_attrs 테이블 저장값) ===

SSF_CLASS = ["TOP", "BOTTOM", "OUTER", "TOP_L"]

SSF_COLORS = [
    "0_IVORY", "1_WHITE", "2_LIGHT_GREY", "3_GREY", "4_ASH", "5_BLACK",
    "6_RED", "7_CORAL", "8_ORANGE", "9_SALMON_PINK", "A_BEIGE",
    "B_YELLOWISH_BROWN", "C_BRICK", "D_BROWN", "E_YELLOW", "F_LEMON",
    "G_MUSTAR", "H_KHAKI", "J_OLIVE", "K_APPLE_GREEN", "L_GREEN",
    "M_MINT", "N_EMERALD", "O_SKY_BLUE", "P_BLUE", "Q_SKY_BLUE",
    "R_NAVY", "S_PURPLE", "T_PINK", "U_LAVENDER", "V_WINE",
    "W_GOLD", "X_SILVER", "Y_MULTI"
]  # 34개

SSF_FIT = [
    "BAGGY", "BOOTSCUT", "BOXY", "CASUAL_SLIM", "CASUAL_TOP_FIT_ETC",
    "CASUAL_TOP_FIT_REGULAR", "CASUAL_TOP_OVER_FIT", "DRESS_A-LINE",
    "DRESS_FIT_ETC", "DRESS_H-LINE", "EMPIRE-HIGHT_WAIST", "JOGGER",
    "LOOSE-WIDE", "MERMAID", "OUTER_FIT_REGULAR", "OUTER_OVER_FIT",
    "OUTER_SLIM", "PANTS_FIT_ETC", "PANTS_SLIM", "REGULAR-STRAIGHT",
    "SKIRT_A-LINE", "SKIRT_FIT_ETC", "SKIRT_H-LINE", "SKIRT_MERMAID",
    ...  # 31개 전체 (schema.py에 정의)
]

SSF_PATTERN = [
    "ANIMAL", "CAMOUFLAGE", "COLORED", "COLOR_BLOCK", "COLOR_CONTRAST",
    "DOT", "FAIR_ISLE", "FLORAL", "GARMENT_WASHING", "GLEN", "GRADATION",
    "GRAPHIC", "HERRINGBONE", "JACQUARD", "MELANGE", "METALIC",
    "MONOGRAM", "MULTI_CHECK", "PAISLEY", "PLAID", "SEERSUCKER",
    "SOLID", "STRIPE", "STRIPE_ROPE", "TIE_DYE", "WASHING",
    ...  # 37개 전체
]

SSF_TEXTURE = [
    "BOA-BOUCLE-FLEECE", "CHIFFON", "CORDUROY", "DENIM", "FUR",
    "KNITTING", "LACE", "LEATHER", "LINEN", "NYLON", "SEERSUCKER",
    "SEE_THROUGH-MESH", "SEQUINS", "SILK", "SUEDE", "TERRY", "VELVET", "WOOL"
]  # 18개

SSF_STYLE_TPO = [
    "CASUAL-ACTIVE", "CASUAL-BASIC-CASUAL", "CASUAL-CASUAL", "CASUAL-FUNK",
    "CASUAL-KITSCH", "CASUAL-MILITARY", "CASUAL-ROMANTIC-CASUAL", "CASUAL-STREET",
    "CLASSIC-FORMAL", "CLASSIC-SEMI-FORMAL", "ELEGANCE", "ETHNIC",
    "MANNISH", "MODERN", "NATURAL", "ORIENTAL", "PARTY-EVENT-FANCY",
    "PARTY-EVENT-ROMANTIC", "SEXY", "SPORTS", "SPORTS-OUTDOOR"
]  # 21개

# === Claude 쿼리 추출 어휘 (프롬프트 제약용, SSF 코드로 매핑됨) ===

QUERY_CLASS = ["TOP", "BOTTOM", "OUTER"]
QUERY_COLOR = [
    "black", "white", "grey", "ivory", "beige", "brown", "navy", "blue",
    "sky_blue", "green", "khaki", "olive", "red", "pink", "coral",
    "yellow", "purple", "orange", "gold", "silver", "multi"
]
QUERY_SILHOUETTE = ["slim", "regular", "oversized", "boxy", "wide"]
QUERY_PATTERN = [
    "solid", "stripe", "check", "floral", "logo", "graphic",
    "color_block", "animal", "denim_wash"
]
QUERY_TEXTURE = [
    "denim", "knit", "wool", "leather", "linen", "chiffon",
    "cotton", "nylon", "velvet", "fur"
]
QUERY_STYLE = [
    "casual", "formal", "street", "romantic", "sporty",
    "mannish", "elegant", "minimal"
]
```

---

*끝.*
