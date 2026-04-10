import streamlit as st
from pdf2image import convert_from_bytes
from pypdf import PdfReader
import zipfile
import io
import os

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="PDF → Image 변환기",
    page_icon="🖼️",
    layout="wide",
)

# ── 비밀번호 인증 (2명) ───────────────────────────────────────
def check_password():
    pw1 = st.secrets.get("PASSWORD_1", "")
    pw2 = st.secrets.get("PASSWORD_2", "")

    if not pw1 and not pw2:
        st.error("⚠️ 환경변수 `PASSWORD_1` / `PASSWORD_2`가 설정되지 않았습니다.")
        st.stop()

    if st.session_state.get("authenticated"):
        return

    st.title("🔐 로그인")
    pw = st.text_input("비밀번호를 입력하세요", type="password", placeholder="Password")

    if st.button("확인", use_container_width=True, type="primary"):
        if pw and pw in (pw1, pw2):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("❌ 비밀번호가 틀렸습니다.")

    st.stop()

check_password()

# ── 이미지 → bytes 변환 헬퍼 ─────────────────────────────────
def img_to_bytes(img, fmt, quality):
    buf = io.BytesIO()
    if fmt == "JPG":
        img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
    else:
        img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()

# ── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 변환 옵션")

    output_format = st.selectbox(
        "📄 출력 형식",
        ["JPG", "PNG"],
        help="JPG는 파일 크기가 작고, PNG는 선명한 텍스트에 유리합니다.",
    )

    dpi = st.select_slider(
        "🔍 해상도 (DPI)",
        options=[72, 100, 150, 200, 300, 400, 600],
        value=150,
        help="높을수록 고화질이지만 파일 크기가 커집니다.",
    )

    jpg_quality = 95
    if output_format == "JPG":
        jpg_quality = st.slider(
            "🎨 JPG 품질",
            min_value=50,
            max_value=100,
            value=85,
            step=5,
            help="높을수록 고화질 (파일 크기 증가)",
        )

    st.divider()

    page_mode = st.radio(
        "📑 페이지 선택",
        ["전체 페이지", "특정 페이지 지정"],
    )

    st.divider()
    st.info(
        "💡 **팁**\n"
        "- 고화질 인쇄용 → DPI 300+\n"
        "- 웹/미리보기용 → DPI 150\n"
        "- 투명 배경 필요 → PNG"
    )

    st.divider()
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ── 메인 타이틀 ──────────────────────────────────────────────
st.title("🖼️ PDF → Image 변환기")
st.caption("PDF 파일을 JPG 또는 PNG 이미지로 변환합니다.")

# ── 파일 업로드 ──────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "PDF 파일을 업로드하세요",
    type=["pdf"],
    help="최대 200MB까지 지원합니다.",
)

# 파일이 바뀌면 이전 변환 결과 초기화
current_file = uploaded_file.name if uploaded_file else None
if current_file != st.session_state.get("last_file"):
    st.session_state["converted_images"] = None
    st.session_state["converted_zip"] = None
    st.session_state["last_file"] = current_file
    st.session_state["conv_meta"] = None

if uploaded_file is None:
    st.markdown(
        """
        ### 사용 방법
        1. 왼쪽 사이드바에서 **출력 형식**, **해상도**, **페이지 범위**를 설정하세요.
        2. 위 영역에 PDF 파일을 드래그하거나 클릭해서 업로드하세요.
        3. **변환 시작** 버튼을 누르면 전체 ZIP 다운로드 또는 페이지별 개별 다운로드가 가능합니다.

        | 형식 | 특징 |
        |------|------|
        | **JPG** | 파일 크기 작음, 사진/스캔 문서에 적합 |
        | **PNG** | 무손실, 선명한 텍스트, 투명 배경 지원 |
        """
    )
    st.stop()

# ── PDF 읽기 ─────────────────────────────────────────────────
pdf_bytes = uploaded_file.read()

try:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(reader.pages)
except Exception:
    st.error("PDF 파일을 읽을 수 없습니다. 손상되었거나 암호화된 파일일 수 있습니다.")
    st.stop()

st.success(f"✅ **{uploaded_file.name}** 업로드 완료 ({total_pages}페이지)")

# ── 페이지 범위 선택 ─────────────────────────────────────────
first_page, last_page = 1, total_pages

if page_mode == "특정 페이지 지정" and total_pages > 1:
    col1, col2 = st.columns(2)
    with col1:
        first_page = st.number_input("시작 페이지", min_value=1, max_value=total_pages, value=1)
    with col2:
        last_page = st.number_input("끝 페이지", min_value=first_page, max_value=total_pages, value=total_pages)

num_pages = last_page - first_page + 1

# ── 변환 요약 ────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("변환 페이지", f"{num_pages}장")
c2.metric("출력 형식", output_format)
c3.metric("해상도", f"{dpi} DPI")
c4.metric("품질", f"{jpg_quality}%" if output_format == "JPG" else "무손실")

st.divider()

# ── 변환 버튼 ────────────────────────────────────────────────
if st.button("🚀 변환 시작", type="primary", use_container_width=True):
    progress = st.progress(0, text="변환 준비 중...")
    status = st.empty()

    try:
        status.info(f"🔄 {num_pages}페이지 변환 중... (DPI: {dpi})")

        images = convert_from_bytes(
            pdf_bytes,
            dpi=dpi,
            first_page=first_page,
            last_page=last_page,
            fmt="jpeg" if output_format == "JPG" else "png",
        )

        progress.progress(60, text="이미지 생성 완료, ZIP 압축 중...")

        basename = os.path.splitext(uploaded_file.name)[0]
        ext = "jpg" if output_format == "JPG" else "png"

        # 개별 bytes 미리 변환해서 session_state에 저장
        image_bytes_list = []
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, img in enumerate(images):
                page_num = first_page + i
                b = img_to_bytes(img, output_format, jpg_quality)
                image_bytes_list.append((page_num, img, b))
                zf.writestr(f"{basename}_p{page_num:04d}.{ext}", b)
                progress.progress(60 + int(35 * (i + 1) / len(images)), text=f"압축 중... ({i+1}/{len(images)})")

        zip_buf.seek(0)
        progress.progress(100, text="완료!")
        status.success(f"🎉 변환 완료! {len(images)}장의 이미지가 준비되었습니다.")

        # ── session_state에 저장 (다운로드 클릭해도 유지) ────
        st.session_state["converted_images"] = image_bytes_list
        st.session_state["converted_zip"] = zip_buf.getvalue()
        st.session_state["conv_meta"] = {
            "basename": basename,
            "ext": ext,
            "fmt": output_format,
            "count": len(images),
        }

    except Exception as e:
        progress.empty()
        status.error(f"❌ 변환 중 오류 발생: {str(e)}")
        st.exception(e)

# ── 변환 결과 표시 (session_state 기반) ──────────────────────
if st.session_state.get("converted_images"):
    image_bytes_list = st.session_state["converted_images"]
    meta = st.session_state["conv_meta"]

    # ZIP 다운로드
    st.download_button(
        label=f"⬇️ 전체 ZIP 다운로드 ({meta['count']}장)",
        data=st.session_state["converted_zip"],
        file_name=f"{meta['basename']}_images.zip",
        mime="application/zip",
        use_container_width=True,
        type="primary",
    )

    st.divider()

    # 페이지별 미리보기 + 개별 다운로드
    st.subheader("📄 페이지별 미리보기 & 개별 다운로드")

    cols = st.columns(3)
    for i, (page_num, img, b) in enumerate(image_bytes_list):
        with cols[i % 3]:
            st.image(img, caption=f"페이지 {page_num}", use_container_width=True)
            st.download_button(
                label=f"⬇️ p{page_num} 다운로드",
                data=b,
                file_name=f"{meta['basename']}_p{page_num:04d}.{meta['ext']}",
                mime="image/jpeg" if meta['fmt'] == "JPG" else "image/png",
                use_container_width=True,
                key=f"dl_{page_num}",
            )
