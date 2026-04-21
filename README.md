# 📊 주도 테마 분석 대시보드

장 마감 후 거래대금 TOP60 기준으로 주도 테마를 자동 분석합니다.

## 파일 구성
```
├── collect.py              ← 데이터 수집 스크립트
├── dashboard.html          ← 대시보드 웹페이지
├── data.json               ← 수집 데이터 (자동 생성)
└── .github/workflows/
    └── collect.yml         ← GitHub 자동 실행 설정
```

## 분석 로직
1. 당일 전체 종목 거래대금 상위 60위 추출
2. 60위 안에서 동일 테마 3종목 이상 상승 → 주도 테마 선정
3. 테마별 거래대금 합산 순위
4. 각 테마 내 대장주 선정 (상승률 × 거래대금 점수)

## 로컬 실행
```bash
pip install pykrx requests beautifulsoup4
python collect.py
# 이후 dashboard.html 더블클릭
```

## GitHub + Vercel 배포
1. 이 폴더를 GitHub에 업로드
2. Vercel에서 GitHub 연결
3. dashboard.html이 웹사이트로 배포됨
4. 평일 오후 4시 자동 데이터 갱신
