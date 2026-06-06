# 👑 분신 봇 (Bunsin) — 조경준 운영체제 v1

텔레그램에 **파편을 던지면**, 분신이 **판단엔진 v1**으로 점수 매겨 **실시간 우선순위 큐**로 돌려준다.
손은 파편만 던지고, 구조화·정렬은 분신이 한다.

```
[텔레그램]  ⇄  [분신 봇]  ⇄  [Claude = 두뇌]
                  ↓
            [SQLite 큐]
```

---

## 🧠 판단엔진 v1 (봇에 박혀 있음)

**하드 게이트 2개 (먼저 거름)**
- **게이트 A — 복리:** 자산/커리어/브랜드 중 하나라도 쌓이나? → 아니면 컷
- **게이트 B — 레버리지:** 나 없이 굴러가게 설계 가능한가?
  - `yes` 통과 · `auto` 통과(🔧자동화 먼저 깔기 태깅) · `cut` 컷

**5축 가중 점수 (각 1~5)**
| 축 | 가중치 |
|---|---|
| 레버리지 (AI·자동화·나없이굴러감) | 0.30 |
| 자산 (복리로 쌓임) | 0.25 |
| 돈 (즉시 현금흐름) | 0.20 |
| 브랜드/커리어 (IB·공모전) | 0.15 |
| 긴급 (데드라인) | 0.10 |

> 산수(가중합)는 코드가 결정론적으로 계산 → 점수가 흔들리지 않음.

---

## 💬 명령어

| 입력 | 동작 |
|---|---|
| (아무 텍스트) | 파편으로 보고 점수화 → 큐 삽입 + TOP 회신 |
| `/now` | 지금 할 거 1개 + 이유 |
| `/queue` | 점수순 전체 큐 |
| `/brief` | 아침 브리핑 (오늘 순서 + 이유) |
| `/done <번호>` | 완료 처리 |
| `/cut <번호>` | 손으로 컷 |

---

## ⚙️ 셋업 (집 서버 / PC, 5분)

**1. 봇 토큰 발급** — 텔레그램에서 `@BotFather` → `/newbot` → 토큰 복사

**2. API 키 발급** — console.anthropic.com → API 키 발급

**3. 키 넣기**
```bash
cd bunsin
cp .env.example .env
# .env 열어서 TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY 채우기
```

**4. 실행**
```bash
./run.sh        # 첫 실행은 자동으로 가상환경+설치까지
```

**5. 잠그기** — 봇한테 `/start` 치면 네 `chat_id` 가 나옴 →
`.env` 의 `OWNER_CHAT_ID` 에 그 숫자 넣고 다시 `./run.sh`.
(이래야 너만 봇을 쓸 수 있음)

---

## 🔁 24시간 띄우기 (집 서버에서 꺼지지 않게)

**리눅스 (systemd):**
```ini
# /etc/systemd/system/bunsin.service
[Unit]
Description=Bunsin Bot
After=network.target
[Service]
WorkingDirectory=/path/to/bunsin
ExecStart=/path/to/bunsin/run.sh
Restart=always
[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable --now bunsin
```

**맥/윈도우 PC:** 그냥 터미널에서 `./run.sh` 켜두면 됨.
PC 꺼지면 봇도 꺼지니, 항상 켜두는 기기에서 돌리는 걸 권장.

---

## 🔐 보안 메모
- `.env`, `bunsin.db` 는 `.gitignore` 로 깃 제외됨 — **API 키는 절대 커밋되지 않음**.
- 키는 채팅창에 붙여넣지 말고 `.env` 파일에만.
- `OWNER_CHAT_ID` 꼭 채워서 너만 쓰게 잠그기.

---

## 🛣️ 다음 확장 (원하면)
- `/brief` 를 매일 아침 정해진 시간에 자동 발송 (job queue)
- 큐를 구글시트/노션으로 미러링 (눈으로 보고 싶을 때)
- 딜 파이프라인 전용 명령 (`/deals`)
- 주간 리뷰 자동 생성 (`/week`)
