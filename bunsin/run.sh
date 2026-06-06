#!/usr/bin/env bash
# 분신 봇 실행 (집 서버/PC용). 처음 한 번만 셋업 후, 매번 ./run.sh 로 켬.
set -euo pipefail
cd "$(dirname "$0")"

# 가상환경 없으면 만들고 의존성 설치
if [ ! -d ".venv" ]; then
  echo "▶ 첫 셋업: 가상환경 + 의존성 설치"
  python3 -m venv .venv
  ./.venv/bin/pip install --quiet --upgrade pip
  ./.venv/bin/pip install --quiet -r requirements.txt
fi

# .env 로드
if [ -f ".env" ]; then
  set -a; source .env; set +a
else
  echo "⚠️  .env 가 없어. .env.example 복사해서 채워: cp .env.example .env"
  exit 1
fi

echo "👑 분신 봇 켠다…"
exec ./.venv/bin/python bot.py
