import streamlit as st
from webdav4.client import Client
import io
import os
import base64

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
    if not modified:
        return "—"
    try:
        # modified는 datetime 또는 문자열
        if hasattr(modified, "strftime"):
            return modified.strftime("%Y-%m-%d %H:%M")
        return str(modified)[:16]
    except Exception:
        return str(modified)[:16]

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

# ── 메인 타이틀 ──────────────────────────────────────────────
st.title("🗂️ NAS 파일 브라우저")

# ── 브레드크럼 + 새로고침 ────────────────────────────────────
crumbs = st.session_state["path_stack"]
nav_cols = st.columns([8, 1])

with nav_cols[0]:
    bc_cols = st.columns(len(crumbs))
    for i, crumb in enumerate(crumbs):
        label = "🏠 홈" if crumb == ROOT_PATH else f"📁 {os.path.basename(crumb.rstrip('/'))}"
        with bc_cols[i]:
            if i < len(crumbs) - 1:
                if st.button(label, key=f"crumb_{i}"):
                    navigate_to(crumb)
                    st.rerun()
            else:
                st.markdown(f"**{label}**")

with nav_cols[1]:
    if st.button("🔄", help="현재 폴더 새로고침", use_container_width=True):
        do_refresh()
        st.rerun()

st.divider()

# ── 정렬 옵션 ────────────────────────────────────────────────
sort_cols = st.columns([3, 3, 6])
with sort_cols[0]:
    st.session_state["sort_by"] = st.selectbox(
        "정렬 기준",
        ["이름", "수정 날짜", "크기"],
        index=["이름", "수정 날짜", "크기"].index(st.session_state["sort_by"]),
        label_visibility="collapsed",
    )
with sort_cols[1]:
    order_label = "⬆️ 오름차순" if st.session_state["sort_asc"] else "⬇️ 내림차순"
    if st.button(order_label, use_container_width=True):
        st.session_state["sort_asc"] = not st.session_state["sort_asc"]
        st.rerun()

# ── 디렉토리 목록 불러오기 ────────────────────────────────────
_ = st.session_state["refresh_counter"]  # refresh 트리거 의존

try:
    with st.spinner("목록 불러오는 중..."):
        items = client.ls(current_path(), detail=True)
except Exception as e:
    st.error(f"❌ 목록 불러오기 실패: {e}")
    st.stop()

# ── 정렬 함수 ────────────────────────────────────────────────
def sort_key(item):
    sb = st.session_state["sort_by"]
    if sb == "이름":
        return (item["name"] or "").lower()
    elif sb == "수정 날짜":
        mod = item.get("modified") or item.get("last_modified")
        if hasattr(mod, "timestamp"):
            return mod.timestamp()
        return 0
    elif sb == "크기":
        return item.get("content_length") or 0
    return ""

dirs  = [i for i in items if i["type"] == "directory"]
files = [i for i in items if i["type"] != "directory"]

dirs  = sorted(dirs,  key=sort_key, reverse=not st.session_state["sort_asc"])
files = sorted(files, key=sort_key, reverse=not st.session_state["sort_asc"])
all_items = dirs + files

if not all_items:
    st.info("📭 폴더가 비어 있습니다.")
    st.stop()

# ── 헤더 ─────────────────────────────────────────────────────
h = st.columns([0.4, 3.5, 1.2, 1.8, 2.5])
h[0].markdown("**　**")
h[1].markdown("**이름**")
h[2].markdown("**크기**")
h[3].markdown("**수정 날짜**")
h[4].markdown("**동작**")
st.divider()

# ── 파일 목록 ────────────────────────────────────────────────
for item in all_items:
    name   = item["name"]
    is_dir = item["type"] == "directory"
    ext    = os.path.splitext(name)[1].lower()
    href   = item.get("href", "")
    item_path = href if href.startswith("/") else os.path.join(current_path(), name)
    if is_dir and not item_path.endswith("/"):
        item_path += "/"

    col_icon, col_name, col_size, col_date, col_action = st.columns([0.4, 3.5, 1.2, 1.8, 2.5])

    col_icon.write(get_icon(item))
    col_name.write(name)
    col_size.write("—" if is_dir else fmt_size(item.get("content_length")))
    col_date.write(fmt_date(item))

    with col_action:
        can_preview = ext in IMAGE_EXTS | PDF_EXTS

        if is_dir:
            a1, a2 = st.columns(2)
            with a1:
                if st.button("열기 →", key=f"open_{item_path}", use_container_width=True):
                    navigate_to(item_path)
                    st.rerun()
            with a2:
                if st.button("🗑️", key=f"del_{item_path}", help="삭제", use_container_width=True):
                    st.session_state["delete_confirm"] = item_path
                    st.rerun()

        elif can_preview:
            a1, a2, a3 = st.columns(3)
            with a1:
                if st.button("🔎", key=f"pv_{item_path}", help="미리보기", use_container_width=True):
                    try:
                        buf = io.BytesIO()
                        client.download_fileobj(item_path, buf)
                        st.session_state["preview"] = {
                            "name": name, "data": buf.getvalue(), "ext": ext
                        }
                        st.rerun()
                    except Exception as e:
                        st.error(f"미리보기 실패: {e}")
            with a2:
                try:
                    buf = io.BytesIO()
                    client.download_fileobj(item_path, buf)
                    st.download_button("⬇️", data=buf.getvalue(), file_name=name,
                                       key=f"dl_{item_path}", use_container_width=True)
                except Exception:
                    pass
            with a3:
                if st.button("🗑️", key=f"del_{item_path}", help="삭제", use_container_width=True):
                    st.session_state["delete_confirm"] = item_path
                    st.rerun()

        else:
            a1, a2 = st.columns(2)
            with a1:
                try:
                    buf = io.BytesIO()
                    client.download_fileobj(item_path, buf)
                    st.download_button("⬇️ 다운로드", data=buf.getvalue(), file_name=name,
                                       key=f"dl_{item_path}", use_container_width=True)
                except Exception:
                    pass
            with a2:
                if st.button("🗑️", key=f"del_{item_path}", help="삭제", use_container_width=True):
                    st.session_state["delete_confirm"] = item_path
                    st.rerun()

# ── 삭제 확인 다이얼로그 ─────────────────────────────────────
if st.session_state["delete_confirm"]:
    target = st.session_state["delete_confirm"]
    target_name = os.path.basename(target.rstrip("/"))

    st.divider()
    st.warning(f"⚠️ **'{target_name}'** 을(를) 정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.")
    c1, c2, _ = st.columns([1, 1, 4])

    with c1:
        if st.button("✅ 삭제 확인", type="primary", use_container_width=True):
            try:
                if target.endswith("/"):
                    client.remove(target)
                else:
                    client.remove(target)
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
