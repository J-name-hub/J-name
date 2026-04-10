import streamlit as st
from webdav4.client import Client
import io
import os
import base64
from urllib.parse import unquote

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
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
PDF_EXTS   = {".pdf"}
VIDEO_EXTS = {".mp4", ".webm", ".ogg"}
AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".m4a"}

def get_icon(item):
    if item["type"] == "directory": return "📁"
    ext = os.path.splitext(item["name"])[1].lower()
    if ext in IMAGE_EXTS: return "🖼️"
    if ext in PDF_EXTS:   return "📄"
    if ext in VIDEO_EXTS: return "🎬"
    if ext in AUDIO_EXTS: return "🎵"
    return "📎"

def fmt_size(size):
    if size is None: return "—"
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def fmt_date(item):
    modified = item.get("modified") or item.get("last_modified")
    if not modified: return "—"
    try:
        if hasattr(modified, "strftime"):
            return modified.strftime("%Y-%m-%d %H:%M")
        return str(modified)[:16]
    except Exception:
        return str(modified)[:16]

def safe_path(path):
    """URL 인코딩된 경로를 디코딩하여 WebDAV 클라이언트에 전달"""
    return unquote(path)

# ── 세션 초기화 ──────────────────────────────────────────────
ROOT_PATH = st.secrets.get("WEBDAV_ROOT", "/")

for key, default in [
    ("path_stack", [ROOT_PATH]),
    ("preview", None),
    ("sort_by", "이름"),
    ("sort_asc", True),
    ("delete_confirm", None),
    ("refresh_counter", 0),
]:
    if key not in st.session_state:
        st.session_state[key] = default

def current_path():
    return st.session_state["path_stack"][-1]

def navigate_to(path):
    if path in st.session_state["path_stack"]:
        idx = st.session_state["path_stack"].index(path)
        st.session_state["path_stack"] = st.session_state["path_stack"][:idx+1]
    else:
        st.session_state["path_stack"].append(path)
    st.session_state["preview"] = None
    st.session_state["delete_confirm"] = None

def do_refresh():
    st.session_state["refresh_counter"] += 1
    st.session_state["delete_confirm"] = None

def download_file(item_path):
    """파일 다운로드 - URL 디코딩된 경로 사용"""
    buf = io.BytesIO()
    client.download_fileobj(safe_path(item_path), buf)
    buf.seek(0)
    return buf.getvalue()

# ── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:
    st.header("🗂️ NAS 브라우저")
    st.caption(st.secrets.get("WEBDAV_URL", ""))
    st.divider()

    if st.session_state["preview"]:
        pv = st.session_state["preview"]
        ext = pv["ext"]
        st.subheader(f"🔎 {pv['name']}")

        if ext in IMAGE_EXTS:
            st.image(pv["data"], use_container_width=True)
        elif ext in PDF_EXTS:
            b64 = base64.b64encode(pv["data"]).decode()
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{b64}" '
                f'width="100%" height="600px"></iframe>',
                unsafe_allow_html=True,
            )

        st.download_button(
            "⬇️ 다운로드",
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

# ── 메인 ─────────────────────────────────────────────────────
st.title("🗂️ NAS 파일 브라우저")

# 브레드크럼 + 새로고침
crumbs = st.session_state["path_stack"]
nav_cols = st.columns([9, 1])
with nav_cols[0]:
    bc_cols = st.columns(max(len(crumbs), 1))
    for i, crumb in enumerate(crumbs):
        label = "🏠 홈" if crumb == ROOT_PATH else f"📁 {os.path.basename(unquote(crumb).rstrip('/'))}"
        with bc_cols[i]:
            if i < len(crumbs) - 1:
                if st.button(label, key=f"crumb_{i}"):
                    navigate_to(crumb)
                    st.rerun()
            else:
                st.markdown(f"**{label}**")
with nav_cols[1]:
    if st.button("🔄", help="새로고침", use_container_width=True):
        do_refresh()
        st.rerun()

st.divider()

# 정렬 옵션
s1, s2, _ = st.columns([2, 2, 6])
with s1:
    st.session_state["sort_by"] = st.selectbox(
        "정렬",
        ["이름", "수정 날짜", "크기"],
        index=["이름", "수정 날짜", "크기"].index(st.session_state["sort_by"]),
        label_visibility="collapsed",
    )
with s2:
    asc_label = "⬆️ 오름차순" if st.session_state["sort_asc"] else "⬇️ 내림차순"
    if st.button(asc_label, use_container_width=True):
        st.session_state["sort_asc"] = not st.session_state["sort_asc"]
        st.rerun()

# ── 목록 불러오기 ─────────────────────────────────────────────
_ = st.session_state["refresh_counter"]

try:
    with st.spinner("목록 불러오는 중..."):
        items = client.ls(safe_path(current_path()), detail=True)
except Exception as e:
    st.error(f"❌ 목록 불러오기 실패: {e}")
    st.stop()

def sort_key(item):
    sb = st.session_state["sort_by"]
    if sb == "이름":
        return (item["name"] or "").lower()
    elif sb == "수정 날짜":
        mod = item.get("modified") or item.get("last_modified")
        return mod.timestamp() if hasattr(mod, "timestamp") else 0
    elif sb == "크기":
        return item.get("content_length") or 0
    return ""

dirs  = sorted([i for i in items if i["type"] == "directory"],  key=sort_key, reverse=not st.session_state["sort_asc"])
files = sorted([i for i in items if i["type"] != "directory"],  key=sort_key, reverse=not st.session_state["sort_asc"])
all_items = dirs + files

if not all_items:
    st.info("📭 폴더가 비어 있습니다.")
    st.stop()

# ── 헤더 ─────────────────────────────────────────────────────
h = st.columns([0.5, 4, 1.5, 2, 3])
h[0].markdown("**　**")
h[1].markdown("**이름**")
h[2].markdown("**크기**")
h[3].markdown("**수정 날짜**")
h[4].markdown("**동작**")
st.divider()

# ── 파일 목록 ────────────────────────────────────────────────
for item in all_items:
    raw_name = item["name"]                          # 원본 (인코딩될 수 있음)
    name     = unquote(raw_name)                     # 화면 표시용 디코딩 이름
    is_dir   = item["type"] == "directory"
    ext      = os.path.splitext(name)[1].lower()
    href     = item.get("href", "")
    item_path = href if href.startswith("/") else os.path.join(current_path(), raw_name)
    if is_dir and not item_path.endswith("/"):
        item_path += "/"

    # 파일명만 표시 (경로 제거)
    display_name = os.path.basename(name.rstrip("/"))

    col_icon, col_name, col_size, col_date, col_action = st.columns([0.5, 4, 1.5, 2, 3])
    col_icon.write(get_icon(item))
    col_name.write(display_name)
    col_size.write("—" if is_dir else fmt_size(item.get("content_length")))
    col_date.write(fmt_date(item))

    with col_action:
        if is_dir:
            a1, a2 = st.columns([3, 1])
            with a1:
                if st.button("열기 →", key=f"open_{item_path}", use_container_width=True):
                    navigate_to(item_path)
                    st.rerun()
            with a2:
                if st.button("🗑️", key=f"del_{item_path}", help="삭제", use_container_width=True):
                    st.session_state["delete_confirm"] = item_path
                    st.rerun()

        else:
            can_preview = ext in IMAGE_EXTS | PDF_EXTS

            if can_preview:
                a1, a2, a3 = st.columns([2, 2, 1])
            else:
                a1, a2 = st.columns([3, 1])
                a3 = None

            # 미리보기
            if can_preview:
                with a1:
                    if st.button("🔎 미리보기", key=f"pv_{item_path}", use_container_width=True):
                        try:
                            data = download_file(item_path)
                            st.session_state["preview"] = {
                                "name": display_name,
                                "data": data,
                                "ext": ext,
                            }
                            st.rerun()
                        except Exception as e:
                            st.error(f"미리보기 실패: {e}")

            # 다운로드
            dl_col = a2 if can_preview else a1
            with dl_col:
                try:
                    data = download_file(item_path)
                    st.download_button(
                        "⬇️ 다운로드",
                        data=data,
                        file_name=display_name,
                        key=f"dl_{item_path}",
                        use_container_width=True,
                    )
                except Exception:
                    st.caption("다운로드 불가")

            # 삭제
            del_col = a3 if can_preview else a2
            with del_col:
                if st.button("🗑️", key=f"del_{item_path}", help="삭제", use_container_width=True):
                    st.session_state["delete_confirm"] = item_path
                    st.rerun()

# ── 삭제 확인 ────────────────────────────────────────────────
if st.session_state["delete_confirm"]:
    target      = st.session_state["delete_confirm"]
    target_name = os.path.basename(unquote(target).rstrip("/"))

    st.divider()
    st.warning(f"⚠️ **'{target_name}'** 을(를) 정말 삭제하시겠습니까? 되돌릴 수 없습니다.")
    c1, c2, _ = st.columns([1, 1, 4])

    with c1:
        if st.button("✅ 삭제 확인", type="primary", use_container_width=True):
            try:
                client.remove(safe_path(target))
                st.success(f"🗑️ '{target_name}' 삭제 완료")
                st.session_state["delete_confirm"] = None
                do_refresh()
                st.rerun()
            except Exception as e:
                st.error(f"삭제 실패: {e}")
    with c2:
        if st.button("❌ 취소", use_container_width=True):
            st.session_state["delete_confirm"] = None
            st.rerun()
