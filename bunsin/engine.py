"""
분신 두뇌 — 판단엔진 v1 (조경준 튜닝)

파편(짧은 텍스트)을 받아서:
  1) 하드 게이트 2개 통과 판정
  2) 5축 점수 (1~5)
  3) 가중합 점수 계산 (파이썬에서 결정론적으로)
  4) 태그 + 이유 한 줄

Claude는 '판정값'만 뱉고, 산수(가중합)는 코드가 한다.
모델이 점수 흔들리는 걸 막기 위함.
"""

import json
import os
import re

from anthropic import Anthropic

# 분신 두뇌 모델 — 환경변수로 교체 가능
MODEL = os.environ.get("BUNSIN_MODEL", "claude-sonnet-4-6")

# 5축 가중치 (v1 확정값) — 합 = 1.0
WEIGHTS = {
    "leverage": 0.30,  # AI·자동화·나 없이 굴러감 (핵심 렌즈)
    "asset":    0.25,  # 복리로 쌓임
    "money":    0.20,  # 즉시 현금흐름
    "brand":    0.15,  # IB 레퍼런스·공모전·노출
    "urgency":  0.10,  # 데드라인
}

SYSTEM_PROMPT = """\
너는 조경준의 '분신'이다. 조경준은 부동산금융에서 IB(기업금융·M&A 인수금융·CB/BW 메자닌)로
진화 중인 사람이고, 그 위에서 AI 군단을 굴리는 '그림자 군주'를 지향한다.
12개월 목표: 자산화 · IB 커버리지 커리어 · 공모전 수상 · 프로젝트 런칭 · 다이어리 사업 런칭.
핵심 판단 렌즈: "AI로 레버리지 되나? 그럼 나도 한다."

너의 임무: 그가 던지는 '짧은 파편'(할 일/딜/아이디어)을 받아서, 아래 판단엔진 v1으로 평가한다.

[STEP 1 — 하드 게이트]
- gate_a (복리 게이트): 이 일이 자산/커리어/브랜드 중 하나라도 복리로 쌓이나?
    쌓이면 pass, 아무데도 안 남는 순수 단발성이면 cut.
- gate_b (레버리지 게이트): 조경준이 없어도 굴러가게 설계 가능한가?
    "yes"  = 이미 위임/자동화 가능
    "auto" = 지금은 손이 가지만 자동화 설계하면 가능 (유연 통과, 자동화 과제로 태깅)
    "cut"  = 설계해도 무조건 그의 시간을 계속 갈아넣어야 함

[STEP 2 — 5축 점수, 각 1~5 정수]
- leverage: AI/자동화/위임으로 레버리지 되는 정도 (높을수록 5)
- asset:    복리로 쌓이는 정도 (자산/커리어/브랜드 축적)
- money:    즉시 현금흐름 기여
- brand:    IB 레퍼런스·공모전·외부 노출 가치
- urgency:  데드라인 임박도

[태그] 다음 중 하나: 딜 / 사업 / 공모전 / 본업 / 기타

반드시 아래 JSON 형식 '하나만' 출력한다. 설명 문장 금지.
{
  "title": "<파편을 한 줄 액션으로 정제>",
  "gate_a": "pass" | "cut",
  "gate_b": "yes" | "auto" | "cut",
  "leverage": 1-5,
  "asset": 1-5,
  "money": 1-5,
  "brand": 1-5,
  "urgency": 1-5,
  "tag": "딜|사업|공모전|본업|기타",
  "reason": "<왜 이 점수/판정인지 한 줄. 조경준 목표 기준으로.>"
}
"""

_client = None


def client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()  # ANTHROPIC_API_KEY 환경변수 사용
    return _client


def _extract_json(text: str) -> dict:
    """모델 응답에서 JSON 블록만 뽑는다 (혹시 군더더기가 붙어도 견디게)."""
    text = text.strip()
    # ```json ... ``` 코드펜스 제거
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"JSON 못 찾음: {text[:200]}")
    return json.loads(text[start : end + 1])


def evaluate(fragment: str) -> dict:
    """
    파편 한 줄을 판단엔진에 통과시켜 평가 dict를 돌려준다.
    돌려주는 키: title, tag, reason, gate_a, gate_b, axes(dict), score(float), cut(bool)
    """
    msg = client().messages.create(
        model=MODEL,
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": fragment}],
    )
    raw = "".join(b.text for b in msg.content if b.type == "text")
    data = _extract_json(raw)

    axes = {k: int(data[k]) for k in WEIGHTS}
    score = round(sum(axes[k] * WEIGHTS[k] for k in WEIGHTS), 2)

    gate_a = data.get("gate_a", "pass")
    gate_b = data.get("gate_b", "yes")
    # 게이트 A 실패 = 즉시 컷.  게이트 B 'cut' = 컷.  'auto' = 통과(자동화 태깅).
    cut = (gate_a == "cut") or (gate_b == "cut")

    return {
        "title": data.get("title", fragment).strip(),
        "tag": data.get("tag", "기타"),
        "reason": data.get("reason", "").strip(),
        "gate_a": gate_a,
        "gate_b": gate_b,
        "axes": axes,
        "score": score,
        "cut": cut,
        "auto": gate_b == "auto",
    }
