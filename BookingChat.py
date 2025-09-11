import streamlit as st
import datetime

# Khởi tạo trạng thái
if "messages" not in st.session_state:
    st.session_state.messages = []
if "step" not in st.session_state:
    st.session_state.step = "ask_form"
if "form_data" not in st.session_state:
    st.session_state.form_data = {}

st.title("🩺 Trợ lý đặt lịch khám")

# Hiển thị các tin nhắn trước đó
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ======= Tạo list giờ (5h-11h, 13h-17h, cách 30p) =======
def generate_time_slots():
    slots = []
    # Buổi sáng
    t = datetime.time(5, 0)
    while t < datetime.time(11, 30):
        slots.append(t.strftime("%H:%M"))
        h, m = t.hour, t.minute
        m += 30
        if m == 60:
            h += 1
            m = 0
        t = datetime.time(h, m)
    # Buổi chiều
    t = datetime.time(13, 0)
    while t <= datetime.time(17, 0):
        slots.append(t.strftime("%H:%M"))
        h, m = t.hour, t.minute
        m += 30
        if m == 60:
            h += 1
            m = 0
        if h > 17: break
        t = datetime.time(h, m)
    return slots

time_slots = generate_time_slots()

# ======= Luồng hội thoại =======
if st.session_state.step == "ask_form":
    if not any(m["content"].startswith("Mời bạn chọn") for m in st.session_state.messages):
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Mời bạn chọn ngày và giờ khám bên dưới 👇"
        })
        st.rerun()

    with st.chat_message("assistant"):
        with st.form("booking_form"):
            today = datetime.date.today()
            date = st.date_input("Ngày mong muốn", min_value=today)
            time = st.selectbox("Giờ khám", time_slots)
            submitted = st.form_submit_button("Submit")
            if submitted:
                st.session_state.form_data = {
                    "date": str(date),
                    "time": time
                }
                st.session_state.messages.append({
                    "role": "user",
                    "content": f"📅 {date} lúc {time}"
                })
                st.session_state.step = "confirm"
                st.rerun()

elif st.session_state.step == "confirm":
    with st.chat_message("assistant"):
        st.markdown("Bạn có muốn xác nhận lịch hẹn này không?")
        col1, col2 = st.columns(2)
        if col1.button("✅ Yes"):
            st.session_state.step = "final"
            st.rerun()
        if col2.button("❌ No"):
            st.session_state.step = "ask_form"
            st.rerun()

elif st.session_state.step == "final":
    data = st.session_state.form_data
    with st.chat_message("assistant"):
        st.markdown(
            f"📌 Bạn đã đặt lịch vào ngày **{data['date']}** lúc **{data['time']}**."
        )
        col1, col2 = st.columns(2)
        if col1.button("Cancel"):
            st.session_state.step = "cancelled"
            st.rerun()
        if col2.button("Reschedule"):
            st.session_state.step = "reschedule"
            st.rerun()

elif st.session_state.step == "cancelled":
    with st.chat_message("assistant"):
        st.markdown("❌ Lịch hẹn của bạn đã được hủy.")
        if st.button("Đặt lại"):
            st.session_state.step = "ask_form"
            st.rerun()

elif st.session_state.step == "reschedule":
    with st.chat_message("assistant"):
        st.markdown("🔁 Vui lòng nhập lại thông tin để đổi lịch.")
        if st.button("Điền lại form"):
            st.session_state.step = "ask_form"
            st.rerun()
