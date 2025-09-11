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

# ======= Tạo list khung giờ (1 tiếng, loại giờ trưa) =======
def generate_time_slots():
    slots = []
    for hour in range(5, 17):
        start = datetime.time(hour, 0)
        end = datetime.time(hour+1, 0)
        # Bỏ các khung giờ nằm trong khoảng 11:00–13:00
        if start >= datetime.time(11, 0) and start < datetime.time(13, 0):
            continue
        slots.append(f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}")
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
            min_day = today + datetime.timedelta(days=1)
            max_day = today + datetime.timedelta(days=15)

            date = st.date_input("Ngày mong muốn", min_value=min_day, max_value=max_day)
            time = st.selectbox("Khung giờ khám", time_slots)

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
