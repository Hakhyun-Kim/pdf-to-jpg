# PDF → JPG 변환기 (PDF to JPG Converter)

PDF 파일을 페이지별 JPG 이미지로 변환하는 **Windows용 GUI 프로그램**입니다.

A simple Windows GUI tool that converts PDF pages into JPG images. Built with Python, tkinter, and PyMuPDF.

## 주요 기능

- 📄 **여러 PDF 동시 변환** — 파일 여러 개를 넣고 한 번에 일괄 처리
- 🖱️ **드래그 앤 드롭** — 탐색기에서 PDF를 끌어다 놓기만 하면 추가
- 🔍 **해상도(DPI) 선택** — 72 ~ 600 DPI (기본 200, 인쇄용은 300 이상 권장)
- 🎚️ **JPG 품질 조절** — 10 ~ 100 (기본 90)
- 📑 **페이지 범위 지정** — `1-3,5` 형식으로 원하는 페이지만 변환
- 📁 **자동 정리 저장** — PDF마다 하위 폴더를 만들어 `파일명_001.jpg`, `파일명_002.jpg` … 형식으로 저장
- ⏳ **진행률 표시** — 변환 중에도 창이 멈추지 않고, 완료되면 저장 폴더를 바로 열어줌

## 설치 방법

### 1. Python 설치

[python.org](https://www.python.org/downloads/)에서 Python 3.10 이상을 설치합니다.
(설치 시 **"Add Python to PATH"** 체크 필수)

### 2. 라이브러리 설치

명령 프롬프트(cmd)에서:

```bash
pip install -r requirements.txt
```

또는 직접:

```bash
pip install pymupdf tkinterdnd2
```

> `tkinterdnd2`는 드래그 앤 드롭 기능용입니다. 설치하지 않아도 프로그램은 작동합니다.

## 실행 방법

- **`PDF변환기 실행.bat`** 파일을 더블클릭 (콘솔 창 없이 실행됨)
- 또는 터미널에서: `python pdf_to_jpg.py`

## 사용 방법

1. **PDF 추가...** 버튼을 누르거나, 파일 목록에 PDF를 드래그 앤 드롭
2. 저장 위치 선택 — 비워두면 각 PDF가 있는 폴더에 저장
3. 옵션 설정 (해상도 / 품질 / 페이지 범위)
4. **변환 시작** 클릭

### 옵션 안내

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| 해상도(DPI) | 클수록 선명하지만 파일 용량이 커짐. 화면용 150~200, 인쇄용 300+ | 200 |
| JPG 품질 | 10~100. 높을수록 화질이 좋고 용량이 커짐 | 90 |
| 페이지 | `1-3,5,8-10` 형식. 비우면 전체 페이지 변환 | 전체 |
| 하위 폴더 | PDF마다 폴더를 만들어 저장 (여러 PDF 변환 시 깔끔) | 켜짐 |

## 동작 원리

[PyMuPDF](https://pymupdf.readthedocs.io/) (MuPDF 엔진)로 PDF 페이지를 지정한 DPI로 렌더링한 뒤 JPG로 저장합니다. 외부 프로그램(포플러, 고스트스크립트 등) 설치가 필요 없습니다.

## 라이선스

[MIT License](LICENSE)
