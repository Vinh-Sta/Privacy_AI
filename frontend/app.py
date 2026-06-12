import streamlit as st
import requests
import time
import os

# Cấu hình địa chỉ của Backend FastAPI
API_URL = "http://localhost:8000"

# 1. Khởi tạo Session State để lưu trữ dữ liệu tạm thời trên trình duyệt
if "token" not in st.session_state:
    st.session_state.token = None
if "current_conv_id" not in st.session_state:
    st.session_state.current_conv_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- CÁC HÀM GỌI API ---
def register(email, password):
    # Gọi API POST /users mà chúng ta đã viết trong routers/user.py
    response = requests.post(
        f"{API_URL}/users", # Đường dẫn này tùy thuộc vào prefix trong file user.py của bạn
        json={"email": email, "password": password}
    )
    if response.status_code == 201:
        st.success("🎉 Tạo tài khoản thành công! Bạn hãy chuyển sang tab Đăng nhập để vào nhé.")
    elif response.status_code == 400:
        st.error("⚠️ Email này đã tồn tại!")
    else:
        st.error(f"❌ Có lỗi xảy ra: {response.text}")

def login(email, password):
    # FastAPI OAuth2 dùng form-data nên ta truyền qua tham số 'data'
    response = requests.post(f"{API_URL}/login", data={"username": email, "password": password})
    if response.status_code == 200:
        st.session_state.token = response.json().get("access_token")
        st.success("Đăng nhập thành công!")
        st.rerun() # Tải lại trang để cập nhật giao diện
    else:
        st.error("Sai email hoặc mật khẩu!")

def get_conversations():
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = requests.get(f"{API_URL}/conversations/", headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def create_conversation(title="Cuộc trò chuyện mới"):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = requests.post(f"{API_URL}/conversations/", json={"title": title}, headers=headers)
    if response.status_code == 201:
        st.session_state.current_conv_id = response.json().get("id")
        st.rerun()

def get_messages(conv_id):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = requests.get(f"{API_URL}/conversations/{conv_id}/messages/", headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def send_message(conv_id, content):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = requests.post(
        f"{API_URL}/conversations/{conv_id}/messages/", 
        json={"role": "user", "content": content}, 
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Có lỗi xảy ra khi gửi tin nhắn!")
        return None
    
def upload_pdf(conv_id, file):
    """Hàm gửi file PDF lên Backend FastAPI"""
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    # Thư viện requests sẽ tự động định dạng multipart/form-data khi dùng tham số 'files'
    files = {"file": (file.name, file, "application/pdf")}
    response = requests.post(
        f"{API_URL}/conversations/{conv_id}/attachments/", 
        headers=headers, 
        files=files
    )
    return response

def get_attachments(conv_id):
    """Hàm lấy danh sách các file PDF đã tải lên trong cuộc trò chuyện"""
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = requests.get(f"{API_URL}/conversations/{conv_id}/attachments/", headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def check_attachment_status(attachment_id):
    """Hỏi thăm Backend xem file đã xử lý xong chưa"""
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = requests.get(f"{API_URL}/attachments/{attachment_id}/status", headers=headers)
    if response.status_code == 200:
        return response.json().get("status")
    return "Failed"

def delete_conversation_api(conv_id):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = requests.delete(f"{API_URL}/conversations/{conv_id}", headers=headers)
    return response.status_code == 204
# --- GIAO DIỆN CHÍNH (UI) ---

st.set_page_config(page_title="AI Chat App", page_icon="🤖", layout="wide")

# NẾU CHƯA ĐĂNG NHẬP -> HIỂN THỊ FORM ĐĂNG NHẬP
# NẾU CHƯA ĐĂNG NHẬP -> HIỂN THỊ FORM ĐĂNG NHẬP/ĐĂNG KÝ
if not st.session_state.token:
    st.title("🤖 Chào mừng đến với AI Chat")
    
    # Tạo 2 tab để user dễ dàng chuyển đổi
    tab1, tab2 = st.tabs(["🔐 Đăng nhập", "📝 Tạo tài khoản mới"])

    # --- TAB ĐĂNG NHẬP ---
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Mật khẩu", type="password")
            submitted = st.form_submit_button("Đăng nhập", use_container_width=True)
            if submitted:
                if email and password:
                    login(email, password)
                else:
                    st.warning("Vui lòng nhập đủ email và mật khẩu!")

    # --- TAB ĐĂNG KÝ ---
    with tab2:
        with st.form("register_form"):
            st.info("Tạo tài khoản để lưu trữ lịch sử trò chuyện của riêng bạn.")
            new_email = st.text_input("Nhập Email mới")
            new_password = st.text_input("Nhập Mật khẩu mới", type="password")
            confirm_password = st.text_input("Xác nhận lại Mật khẩu", type="password")
            
            reg_submitted = st.form_submit_button("Đăng ký ngay", use_container_width=True)
            if reg_submitted:
                if not new_email or not new_password:
                    st.warning("Vui lòng điền đầy đủ thông tin!")
                elif new_password != confirm_password:
                    st.error("Mật khẩu xác nhận không khớp!")
                else:
                    register(new_email, new_password)

# NẾU ĐÃ ĐĂNG NHẬP -> HIỂN THỊ GIAO DIỆN CHAT
else:
    # --- SIDEBAR: Quản lý cuộc hội thoại ---
    with st.sidebar:
        st.title("💬 Cuộc trò chuyện")
        
        if st.button("➕ Tạo Chat Mới", use_container_width=True):
            create_conversation()

        st.divider()
        
        # Lấy và hiển thị danh sách cuộc hội thoại
        conversations = get_conversations()
        # for conv in conversations:
        #     # Nếu click vào một cuộc hội thoại, gán ID của nó vào session
        #     if st.button(f"🗨️ {conv['title']} (ID: {conv['id']})", key=f"conv_{conv['id']}", use_container_width=True):
        #         st.session_state.current_conv_id = conv['id']
        #         st.rerun()
        for conv in conversations:
        # Tạo 2 cột: 1 cột cho nút chọn chat, 1 cột nhỏ cho nút xóa
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                if st.button(f"🗨️ {conv['title']}", key=f"select_{conv['id']}", use_container_width=True):
                    st.session_state.current_conv_id = conv['id']
                    st.rerun()
        
            with col2:
                # Nút xóa với icon thùng rác
                if st.button("🗑️", key=f"del_{conv['id']}", help="Xóa cuộc hội thoại này"):
                    if delete_conversation_api(conv['id']):
                        # Nếu đang ở đúng phòng vừa xóa thì reset ID
                        if st.session_state.current_conv_id == conv['id']:
                            st.session_state.current_conv_id = None
                        st.toast(f"Đã xóa: {conv['title']}")
                        st.rerun() # Tải lại để mất tên phòng đó trên sidebar
                
        st.divider()
        if st.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.token = None
            st.session_state.current_conv_id = None
            st.rerun()

    # --- KHUNG CHAT CHÍNH ---
    if st.session_state.current_conv_id:
        st.header(f"Phòng Chat ID: {st.session_state.current_conv_id}")
        
        # 1. Lấy lịch sử tin nhắn từ Backend và hiển thị
        messages = get_messages(st.session_state.current_conv_id)
        for msg in messages:
            # st.chat_message nhận role là "user" hoặc "assistant" (khớp với Database của ta)
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # --- GIAO DIỆN UPLOAD DẠNG NÚT BẤM (POP-OVER) CHUYÊN NGHIỆP ---
        # Đặt một container ở dưới cùng để chứa nút Upload ngay trên ô chat
        upload_container = st.container()
        with upload_container:
            # Tạo nút popover, khi bấm vào sẽ hiển thị khung upload
            with st.popover("➕ Đính kèm PDF", help="Tải lên tài liệu cho cuộc trò chuyện này"):
                uploaded_file = st.file_uploader("Kéo thả file vào đây", type=["pdf"], label_visibility="collapsed")
                
                if uploaded_file is not None:
                    if st.button("🚀 Tải lên", use_container_width=True):
                        # Gửi file lên lấy ID về (Chạy cực nhanh do Background Task)
                        res = upload_pdf(st.session_state.current_conv_id, uploaded_file)
                        
                        if res.status_code == 201:
                            attachment_data = res.json()
                            attachment_id = attachment_data.get("id")
                            
                            # Khởi tạo một 'vùng trống' trên UI để cập nhật chữ liên tục
                            status_ui = st.empty() 
                            
                            # --- BẮT ĐẦU VÒNG LẶP POLLING (HỎI THĂM) ---
                            max_retries = 30 # Hỏi tối đa 30 lần (khoảng 60 giây)
                            retries = 0
                            is_done = False
                            
                            while retries < max_retries:
                                # Cập nhật UI (hiệu ứng đếm giây)
                                status_ui.info(f"⏳ File đang được AI đọc và nạp vào não... ({retries * 2}s)")
                                
                                # Gọi API kiểm tra
                                current_status = check_attachment_status(attachment_id)
                                
                                if current_status == "Done":
                                    status_ui.success("✅ Tải lên và AI học xong! Bạn có thể hỏi ngay.")
                                    is_done = True
                                    time.sleep(1.5) # Dừng 1.5s để user kịp đọc chữ Success
                                    break
                                elif current_status == "Failed":
                                    status_ui.error("❌ Có lỗi xảy ra khi phân tích file này.")
                                    break
                                
                                # Nếu vẫn là "Processing", ngủ 2 giây rồi hỏi tiếp
                                time.sleep(2)
                                retries += 1
                                
                            if not is_done and retries == max_retries:
                                status_ui.warning("⚠️ Thời gian xử lý quá lâu, hệ thống đang chạy ngầm, bạn có thể kiểm tra lại sau.")
                                time.sleep(2)
                            
                            st.rerun() # Refresh lại trang để reset form và update danh sách file
                        else:
                            st.error(f"Lỗi: {res.text}")
                
                # Hiển thị nhanh các file đã tải lên trong bong bóng này luôn
                st.divider()
                st.caption("📚 Tài liệu trong phòng:")
                attachments = get_attachments(st.session_state.current_conv_id)
                if attachments:
                    for att in attachments:
                        # Gắn icon dựa vào status từ Backend
                        status = att.get("status", "Processing")
                        if status == "Done":
                            icon = "✅"
                        elif status == "Failed":
                            icon = "❌"
                        else:
                            icon = "⏳"
                            
                        st.text(f"{icon} {att['file_name']}")
                else:
                    st.text("Chưa có file nào.")

        # 2. Ô nhập tin nhắn mới
        if prompt := st.chat_input("Hãy hỏi tôi bất cứ điều gì..."):
            # Hiển thị ngay tin nhắn của người dùng lên màn hình cho nhanh
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Gửi tin nhắn xuống Backend và chờ AI trả lời
            with st.spinner("AI đang suy nghĩ..."):
                ai_response = send_message(st.session_state.current_conv_id, prompt)
                
            # Hiển thị câu trả lời của AI
            if ai_response:
                with st.chat_message("assistant"):
                    st.markdown(ai_response["content"])
                st.rerun() # Tải lại để luồng chat mượt mà hơn
    else:
        st.info("👈 Hãy chọn một cuộc trò chuyện ở cột bên trái hoặc tạo mới để bắt đầu!")