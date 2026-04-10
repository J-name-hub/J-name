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

# ── 비밀번호 인증 ─────────────────────────────────────────────
def check_password():
    correct_pw = st.secrets.get("APP_PASSWORD", "")

    if not correct_pw:
        st.error("⚠️ 환경변수 `APP_PASSWORD`가 설정되지 않았습니다.")
        st.stop()

    if st.session_state.get("authenticated"):
        return True

    st.title("🔐 로그인")
    pw = st.text_input("비밀번호를 입력하세요", type="password", placeholder="Password")

    if st.button("확인", use_container_width=True, type="primary"):
        if pw == correct_pw:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("❌ 비밀번호가 틀렸습니다.")

    st.stop()

check_password()

st.title("🖼️ PDF → Image 변환기")
st.caption("PDF 파일을 JPG 또는 PNG 이미지로 변환합니다.")

# ── 사이드바: 변환 옵션 ──────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 변환 옵션")

    output_format = st.selectbox(
        "📄 출력 형식",
        ["JPG", "PNG"],
        help="JPG는 파일 크기가 작고, PNG는 투명 배경을 지원합니다.",
    )

    dpi = st.select_slider(
        "🔍 해상도 (DPI)",
        options=[72, 100, 150, 200, 300, 400, 600],
        value=150,
        help="높을수록 고화질이지만 파일 크기가 커집니다.",
    )

    if output_format == "JPG":
        jpg_quality = st.slider(
            "🎨 JPG 품질",
            min_value=50,
            max_value=100,
            value=85,
            step=5,
            help="높을수록 고화질 (파일 크기 증가)",
        )
    else:
        jpg_quality = 95

    st.divider()

    page_mode = st.radio(
        "📑 페이지 선택",
        ["전체 페이지", "특정 페이지 지정"],
        help="변환할 페이지 범위를 선택하세요.",
    )

    st.divider()
    st.info(
        "💡 **팁**\n"
        "- 고화질이 필요하면 DPI 300+\n"
        "- 빠른 변환은 DPI 150\n"
        "- 투명 배경 필요 시 PNG 선택"
    )

# ── 메인: 파일 업로드 ────────────────────────────────────────
uploaded_file = st.file_uploader(
    "PDF 파일을 업로드하세요",
    type=["pdf"],
    help="최대 200MB까지 지원합니다.",
)

if uploaded_file is not None:
    pdf_bytes = uploaded_file.read()

    # 페이지 수 파악
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
    except Exception:
        st.error("PDF 파일을 읽을 수 없습니다. 파일이 손상되었거나 암호화되어 있을 수 있습니다.")
        st.stop()

    st.success(f"✅ 파일 업로드 완료 — **{uploaded_file.name}** ({total_pages}페이지)")

    # ── 페이지 범위 선택 ────────────────────────────────────
    first_page, last_page = 1, total_pages

    if page_mode == "특정 페이지 지정" and total_pages > 1:
        col1, col2 = st.columns(2)
        with col1:
            first_page = st.number_input(
                "시작 페이지",
                min_value=1,
                max_value=total_pages,
                value=1,
            )
        with col2:
            last_page = st.number_input(
                "끝 페이지",
                min_value=first_page,
                max_value=total_pages,
                value=total_pages,
            )

        page_range_str = f"{first_page} ~ {last_page}페이지"
    else:
        page_range_str = f"전체 {total_pages}페이지"

    # ── 변환 요약 표시 ───────────────────────────────────────
    num_pages = last_page - first_page + 1
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("변환 페이지", f"{num_pages}장")
    col_b.metric("출력 형식", output_format)
    col_c.metric("해상도", f"{dpi} DPI")
    col_d.metric("품질", f"{jpg_quality}%" if output_format == "JPG" else "무손실")

    st.divider()

    # ── 변환 버튼 ────────────────────────────────────────────
    if st.button("🚀 변환 시작", type="primary", use_container_width=True):
        progress = st.progress(0, text="변환 준비 중...")
        status = st.empty()

        try:
            status.info(f"🔄 {page_range_str} 변환 중... (DPI: {dpi})")

            images = convert_from_bytes(
                pdf_bytes,
                dpi=dpi,
                first_page=first_page,
                last_page=last_page,
                fmt="jpeg" if output_format == "JPG" else "png",
            )

            progress.progress(50, text="이미지 생성 완료, 파일 압축 중...")

            # ZIP 파일 생성
            zip_buffer = io.BytesIO()
            basename = os.path.splitext(uploaded_file.name)[0]
            ext = "jpg" if output_format == "JPG" else "png"

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, img in enumerate(images):
                    page_num = first_page + i
                    img_buffer = io.BytesIO()

                    if output_format == "JPG":
                        img = img.convert("RGB")
                        img.save(img_buffer, format="JPEG", quality=jpg_quality, optimize=True)
                    else:
                        img.save(img_buffer, format="PNG", optimize=True)

                    img_buffer.seek(0)
                    zf.writestr(f"{basename}_p{page_num:04d}.{ext}", img_buffer.getvalue())

                    progress.progress(
                        50 + int(50 * (i + 1) / len(images)),
                        text=f"압축 중... ({i+1}/{len(images)})",
                    )

            zip_buffer.seek(0)
            progress.progress(100, text="완료!")
            status.success(f"🎉 변환 완료! {len(images)}장의 이미지가 준비되었습니다.")

            st.download_button(
                label=f"⬇️ ZIP 다운로드 ({len(images)}장)",
                data=zip_buffer,
                file_name=f"{basename}_images.zip",
                mime="application/zip",
                use_container_width=True,
                type="primary",
            )

            # ── 미리보기 ─────────────────────────────────────
            st.subheader("🔎 미리보기")
            preview_count = min(6, len(images))
            cols = st.columns(min(3, preview_count))

            for i in range(preview_count):
                with cols[i % 3]:
                    st.image(
                        images[i],
                        caption=f"페이지 {first_page + i}",
                        use_container_width=True,
                    )

            if len(images) > preview_count:
                st.caption(f"※ 처음 {preview_count}장만 미리보기로 표시됩니다.")

        except Exception as e:
            progress.empty()
            status.error(f"❌ 변환 중 오류 발생: {str(e)}")
            st.exception(e)

else:
    # 업로드 전 안내
    st.markdown(
        """
        ### 사용 방법
        1. 왼쪽 사이드바에서 **출력 형식**, **해상도**, **페이지 범위**를 설정하세요.
        2. 위 영역에 PDF 파일을 드래그하거나 클릭해서 업로드하세요.
        3. **변환 시작** 버튼을 누르면 ZIP 파일로 다운로드할 수 있습니다.

        ---
        | 형식 | 특징 |
        |------|------|
        | **JPG** | 파일 크기 작음, 사진/스캔 문서에 적합 |
        | **PNG** | 무손실, 투명 배경 지원, 선명한 텍스트 |
        """,
        unsafe_allow_html=False,
    )
