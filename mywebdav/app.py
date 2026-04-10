import streamlit as st
from webdav4.client import Client
import io
import os

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="NAS 파일 브라우저",
    page_icon="🗂️",
    layout="wide",
)

# ── 비밀번호 인증 ─────────────────────────────────────────────
def check_password():
    pw1 = st.secrets.get("PASSWORD_1", "")
    pw2 = st.secrets.get("PASSWORD_2", "")
    if not pw1 and not pw2:
        st.error("⚠️ PASSWORD_1 / PASSWORD_2 환경변수가 설정되지 않았습니다.")
        st.stop()
    if st.session_state.get("authenticated"):
        return
    st.title("🔐 로그인")
    pw = st.text_input("비밀번호", type="password", placeholder="Password")
    if st.button("확인", type="primary", use_container_width=True):
        if pw and pw in (pw1, pw2):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("❌ 비밀번호가 틀렸습니다.")
    st.stop()

check_password()

# ── WebDAV 클라이언트 ─────────────────────────────────────────
@st.cache_resource
def get_client():
    return Client(
        base_url=st.secrets["WEBDAV_URL"],
        auth=(st.secrets["WEBDAV_USER"], st.secrets["WEBDAV_PASSWORD"]),
    )

try:
    client = get_client()
except Exception as e:
    st.error(f"WebDAV 연결 실패: {e}")
    st.stop()

# ── 파일 타입 분류 ────────────────────────────────────────────
IMAGE_EXTS  = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
PDF_EXTS    = {".pdf"}
VIDEO_EXTS  = {".mp4", ".webm", ".ogg"}
AUDIO_EXTS  = {".mp3", ".wav", ".ogg", ".m4a"}

def get_icon(item):
    if item["type"] == "directory":
        return "📁"
    ext = os.path.splitext(item["name"])[1].lower()
    if ext in IMAGE_EXTS:  return "🖼️"
    if ext in PDF_EXTS:    return "📄"
    if ext in VIDEO_EXTS:  return "🎬"
    if ext in AUDIO_EXTS:  return "🎵"
    return "📎"

def fmt_size(size):
    if size is None:
        return ""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

# ── 세션 초기화 ──────────────────────────────────────────────
ROOT_PATH = st.secrets.get("WEBDAV_ROOT", "/")

if "path_stack" not in st.session_state:
    st.session_state["path_stack"] = [ROOT_PATH]
if "preview" not in st.session_state:
    st.session_state["preview"] = None  # {"name": ..., "data": ..., "ext": ...}

def current_path():
    return st.session_state["path_stack"][-1]

def navigate_to(path):
    if path in st.session_state["path_stack"]:
        idx = st.session_state["path_stack"].index(path)
        st.session_state["path_stack"] = st.session_state["path_stack"][:idx+1]
    else:
        st.session_state["path_stack"].append(path)
    st.session_state["preview"] = None

# ── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:
    st.header("🗂️ NAS 브라우저")
    st.caption(st.secrets.get("WEBDAV_URL", ""))
    st.divider()

    # 미리보기 패널
    if st.session_state["preview"]:
        pv = st.session_state["preview"]
        ext = pv["ext"]
        st.subheader(f"🔎 {pv['name']}")

        if ext in IMAGE_EXTS:
            st.image(pv["data"], use_container_width=True)

        elif ext in PDF_EXTS:
            st.download_button(
                "⬇️ PDF 다운로드",
                data=pv["data"],
                file_name=pv["name"],
                mime="application/pdf",
                use_container_width=True,
            )
            # base64 embed for PDF preview
            import base64
            b64 = base64.b64encode(pv["data"]).decode()
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{b64}" '
                f'width="100%" height="600px"></iframe>',
                unsafe_allow_html=True,
            )

        st.download_button(
            f"⬇️ 다운로드",
            data=pv["data"],
            file_name=pv["name"],
            use_container_width=True,
            key="sidebar_dl",
        )
        if st.button("✖️ 닫기", use_container_width=True):
            st.session_state["preview"] = None
            st.rerun()

    st.divider()
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ── 메인 영역 ────────────────────────────────────────────────
st.title("🗂️ NAS 파일 브라우저")

# 브레드크럼 네비게이션
crumbs = st.session_state["path_stack"]
breadcrumb_cols = st.columns(len(crumbs) + 1)

for i, crumb in enumerate(crumbs):
    label = "🏠 홈" if crumb == ROOT_PATH else f"📁 {os.path.basename(crumb.rstrip('/'))}"
    with breadcrumb_cols[i]:
        if i < len(crumbs) - 1:
            if st.button(label, key=f"crumb_{i}"):
                navigate_to(crumb)
                st.rerun()
        else:
            st.markdown(f"**{label}**")

st.divider()

# ── 디렉토리 목록 불러오기 ────────────────────────────────────
try:
    with st.spinner("목록 불러오는 중..."):
        items = client.ls(current_path(), detail=True)
except Exception as e:
    st.error(f"❌ 목록 불러오기 실패: {e}")
    st.stop()

# 정렬: 폴더 먼저, 이름순
dirs  = sorted([i for i in items if i["type"] == "directory"], key=lambda x: x["name"])
files = sorted([i for i in items if i["type"] != "directory"],  key=lambda x: x["name"])
all_items = dirs + files

if not all_items:
    st.info("📭 폴더가 비어 있습니다.")
    st.stop()

# ── 파일 목록 테이블 ─────────────────────────────────────────
header = st.columns([0.4, 4, 1.5, 2])
header[0].markdown("**타입**")
header[1].markdown("**이름**")
header[2].markdown("**크기**")
header[3].markdown("**동작**")

st.divider()

for item in all_items:
    name    = item["name"]
    is_dir  = item["type"] == "directory"
    size    = item.get("content_length")
    ext     = os.path.splitext(name)[1].lower()
    # WebDAV href를 절대 경로로
    href    = item.get("href", "")
    # 일부 서버는 href에 full path 포함
    item_path = href if href.startswith("/") else os.path.join(current_path(), name)
    if is_dir and not item_path.endswith("/"):
        item_path += "/"

    col_icon, col_name, col_size, col_action = st.columns([0.4, 4, 1.5, 2])

    col_icon.write(get_icon(item))
    col_name.write(name)
    col_size.write(fmt_size(size) if not is_dir else "—")

    with col_action:
        if is_dir:
            if st.button("열기 →", key=f"open_{item_path}", use_container_width=True):
                navigate_to(item_path)
                st.rerun()
        else:
            can_preview = ext in IMAGE_EXTS | PDF_EXTS
            action_cols = st.columns(2) if can_preview else [st.container()]

            # 다운로드
            try:
                dl_buf = io.BytesIO()
                client.download_fileobj(item_path, dl_buf)
                dl_buf.seek(0)
                raw = dl_buf.getvalue()
            except Exception:
                raw = None

            if can_preview:
                with action_cols[0]:
                    if st.button("🔎 미리보기", key=f"pv_{item_path}", use_container_width=True):
                        if raw is not None:
                            st.session_state["preview"] = {
                                "name": name,
                                "data": raw,
                                "ext": ext,
                            }
                            st.rerun()
                with action_cols[1]:
                    if raw:
                        st.download_button(
                            "⬇️",
                            data=raw,
                            file_name=name,
                            key=f"dl_{item_path}",
                            use_container_width=True,
                        )
            else:
                if raw:
                    st.download_button(
                        "⬇️ 다운로드",
                        data=raw,
                        file_name=name,
                        key=f"dl_{item_path}",
                        use_container_width=True,
                    )
