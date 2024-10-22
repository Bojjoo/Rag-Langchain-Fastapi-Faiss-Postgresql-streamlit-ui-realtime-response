import os
import requests
import streamlit as st
import time
from api.database.database import SQLDatabase
from streamlit_float import *
from api.config import *

st.set_page_config(layout="wide")


float_init()

sql_conn = SQLDatabase()

USER_URL = os.getenv("CHATBOT_URL", "http://172.19.0.5:8000/get_answer_about_users_data/")
USER_RETRIEVER = os.getenv("RETRIEVER", "http://172.19.0.5:8000/get_retriever/")
CSV_QA_URL = os.getenv("CHATBOT_URL", "http://172.19.0.5:8000/get_answer_about_csv_file/")


def handler_input(question: str, conversation_id: str, user_id: str, url, model, prompt_template):
    data = {
        "question": question,
        "conversation_id": conversation_id,
        "prompt_template": prompt_template,
        "user_id": user_id,
        "model": model
    }
    response = requests.post(url=url, json=data, stream=True)

    if response.status_code == 200:
        for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
            # if chunk:
            yield chunk
    else:
        yield f"Error: {response.status_code} - {response.reason}"


def handler_input_csv(question: str, user_id: str, url, model):
    data = {
        "user_id": user_id,
        "question": question,
        "model": model
    }
    response = requests.post(url=url, json=data, stream=True)

    return response.json()

def get_apikey(user_id: str):
    data = {
        "user_id": user_id
    }
    url = "http://172.19.0.5:8000/get_apikey/"
    response = requests.post(url=url, json=data)
    return response.json()


def get_retriever(user_id: str):
    data = {
        "user_id": user_id
    }
    try:
        # Gửi yêu cầu POST đến endpoint FastAPI
        response = requests.post(url=USER_RETRIEVER, json=data)
        if response.status_code == 200:
            # Trả về nội dung phản hồi
            return response.json()
        else:
            # Nếu có lỗi, trả về thông báo lỗi
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"


# Màn hình đăng nhập
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("Login to access the chat")
    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_register:
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Register"):
            if new_password != confirm_password:
                st.warning("Passwords do not match!")
            elif len(new_username) == 0 or len(new_password) == 0:
                st.warning("Username and password cannot be empty!")
            else:
                register_data = {
                    "user_name": new_username,
                    "password": new_password
                }
                try:
                    response = requests.post("http://172.19.0.5:8000/register_account/", json=register_data)
                    if response.json() == 1:
                        st.success("Account registered successfully! You can now log in.")
                    else:
                        st.warning(f"The user name {new_username} is existed, please choose another user name!")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

    with tab_login:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            # Lấy mật khẩu từ cơ sở dữ liệu dựa trên username
            data = {
                "user_name": username,
                "password": password
            }
            response = requests.post("http://172.19.0.5:8000/sign_in_user/", json=data)
            # Kiểm tra nếu mật khẩu đúng
            if response.json() != 0:
                st.session_state["authenticated"] = True
                st.session_state["user_name"] = username
                st.success("Login successful! Welcome to the chat application.")

                # Lấy ID user từ tên user
                st.session_state['user_id'] = response.json()

                # Lấy apikey của user
                st.session_state["get_apikey"] = True
                if st.session_state["get_apikey"]:
                    apikey = get_apikey(st.session_state["user_id"])
                st.session_state["get_apikey"] = False

                # Lấy db Faiss của user
                st.session_state["update_retriever"] = True
                if st.session_state["update_retriever"]:
                    user_retriever = get_retriever(st.session_state["user_id"])
                    if user_retriever == "None":
                        st.warning("Look like you have not uploaded any documents yet! Please upload your documents first!")
                st.session_state["update_retriever"] = False

                # Lấy danh sách các phiên hội thoại
                st.session_state["update_conversation"] = True
                if st.session_state["update_conversation"]:
                    data_user_id = {
                        "user_id": st.session_state["user_id"]
                    }
                    st.session_state["conversations_user"] = requests.post("http://172.19.0.5:8000/get_conversation/", json=data_user_id)
                st.session_state["update_conversation"] = False

                st.rerun()

            # Nếu mk sai
            else:
                st.warning("Invalid username or password. Please try again.")



#st.rerun()
# Nếu người dùng đã đăng nhập thành công, hiển thị giao diện chat
if st.session_state["authenticated"]:
    def Chat_Session():
        # Định nghĩa prompt template
        if "prompt_template" not in st.session_state:
            st.session_state["prompt_template"] = PROMPT_TEMPLATE
        if "title_prompt_template" not in st.session_state:
            st.session_state["title_prompt_template"] = "System Prompt Template"

        with st.sidebar:
            st.info(f"Nice to meet you: {st.session_state['user_name']}", icon=":material/sentiment_satisfied:")

            st.markdown(":green-background[UpLoad Your Documents:]")
            uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf", "docx"])

            # Kiểm tra nếu người dùng chọn file
            if uploaded_file is not None:
                # Xác định URL của endpoint FastAPI và user_id
                upload_file_endpoint = "http://172.19.0.5:8000/upload_data/"

                if st.button(label="Upload File", icon=":material/upload_file:"):
                    # Gửi POST request với file trực tiếp từ Streamlit lên FastAPI
                    with st.spinner("Uploading..."):
                        try:
                            # Định nghĩa multipart-form cho file và các thông tin khác
                            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                            data = {"user_id": st.session_state["user_id"]}

                            # Gửi request lên FastAPI
                            response = requests.post(upload_file_endpoint, files=files, data=data)

                            # Hiển thị phản hồi
                            if response.status_code == 200:
                                st.success(response.json())
                            else:
                                st.error(f"Failed to upload file. Error {response.status_code}: {response.text}")
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")
                    # Update lai retriever
                    st.session_state["update_retriever"] = True
                    if st.session_state["update_retriever"]:
                        retriever_status = get_retriever(st.session_state["user_id"])
                    st.markdown(retriever_status)
                    st.session_state["update_retriever"] = False

            # Hiển thị danh sách các file đã upload
            st.markdown("Uploaded Documents:")
            files = sql_conn.get_files(st.session_state["user_id"])

            if files:
                i = 0
                for file_name, size in files:
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"📄 {file_name} ({size:.2f} MB)", unsafe_allow_html=True)
                    with col2:
                        delete_file_endpoint = "http://172.19.0.5:8000/delete_file/"
                        if st.button(label="", icon=":material/delete:", key=i+1, use_container_width=True):
                            data = {"file_name": file_name, "user_id": st.session_state["user_id"]}
                            response = requests.delete(delete_file_endpoint, json=data)
                            st.success(f"{file_name} deleted successfully!")

                            # Update lai retriever
                            st.session_state["update_retriever"] = True
                            if st.session_state["update_retriever"]:
                                retriever_status = get_retriever(st.session_state["user_id"])
                            st.markdown(retriever_status)
                            st.session_state["update_retriever"] = False

                            st.rerun()
                    i = i + 1
            else:
                st.write("No files uploaded yet.")

            # Thêm tùy chọn để tạo cuộc hội thoại mới
            st.header(":green-background[**Create New Conversation:**]")
            if st.button("Create New Conversation"):
                st.session_state["create_new_conversation"] = True

            # Nếu nhấn nút "Create New Conversation", hiển thị hộp nhập để người dùng nhập tên hội thoại
            if "create_new_conversation" in st.session_state and st.session_state["create_new_conversation"]:
                conversation_name = st.text_input("Enter the name of the new conversation:")

                if st.button("Submit"):
                    if conversation_name:
                        # Tạo một phiên hội thoại mới với loại conversation đã chọn
                        sql_conn.create_conversation(conversation_name, st.session_state["user_id"])
                        st.success(f"New conversation '{conversation_name}' created successfully!")

                        # Lấy danh sách các phiên hội thoại
                        st.session_state["update_conversation"] = True
                        if st.session_state["update_conversation"]:
                            data_user_id = {
                                "user_id": st.session_state["user_id"]
                            }
                            st.session_state["conversations_user"] = requests.post("http://172.19.0.5:8000/get_conversation/",
                                                               json=data_user_id)
                            st.session_state["update_conversation"] = False
                        st.session_state["create_new_conversation"] = False

                    else:
                        st.warning("Conversation name cannot be empty.")
                    st.rerun()

            st.header(":green-background[**All Conversations:**]", divider='orange')

            # Thêm menu chọn Conversation vào sidebar dưới dạng danh sách các nút
            if "conversations_user" in st.session_state:
                # Duyệt qua toàn bộ danh sách hội thoại với User Data và hiển thị dưới dạng nút
                for conv in st.session_state["conversations_user"].json():
                    if st.button(f"{conv[1]}", icon=":material/chat:", key=f"user_{conv[0]}", use_container_width=True):
                        st.session_state["selected_conversation_id"] = conv[0]
                        # st.experimental_rerun()  # Làm mới giao diện khi chọn một conversation
            else:
                st.warning("No conversation sessions available.")

        st.session_state.model = 'gpt-4o-mini'
        col1, col2, col3 = st.columns([1.15, 5, 2], vertical_alignment="top")

        with col1:
            # st.logo("D:/Rearrange_project_29_9_2024/nasa.gif")
            option = st.selectbox(
                label="Model:",
                options=("gpt-4", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "Leme-3hehe"
                         , "gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro", "gemini-1.5-flash-002"
                         , "gemini-1.5-pro-002", "gemini-1.5-flash-8b"),
                index=None,
                placeholder="gpt-4o-mini",
            )
            if option:
                st.session_state.model = option
        col1.float()

        question = st.chat_input("What do you want to know?")
        with col2:
            # Hiển thị lịch sử hội thoại của phiên đã chọn
            if "messages" not in st.session_state:
                st.session_state.messages = []

            if "selected_conversation_id" in st.session_state:
                chat_history = sql_conn.get_chat_history(st.session_state["selected_conversation_id"])
                st.session_state.messages = []
                # Cập nhật tin nhắn vào session_state.messages nếu có lịch sử
                if chat_history:
                    st.session_state.messages = [
                        {"role": "user" if sender == "human" else "assistant", "output": message}
                        for sender, message in chat_history
                    ]

            # Hiển thị các tin nhắn trong phiên hội thoại đã chọn
            if "messages" in st.session_state:
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["output"])
            try:
            # Gửi tin nhắn mới trong giao diện chat
                if question:
                    st.chat_message("user").markdown(question)
                    st.session_state.messages.append({"role": "user", "output": question})

                    with st.chat_message("assistant"):
                        assistant_message = st.empty()

                        prompt_template = st.session_state["prompt_template"]
                        response_stream = handler_input(
                            question, st.session_state["selected_conversation_id"], st.session_state["user_id"], USER_URL,
                            st.session_state.model, prompt_template)

                        # Stream and display the assistant's response
                        output = ""
                        for token in response_stream:
                            output += token
                            assistant_message.markdown(output)
                            time.sleep(0.01)
                        st.session_state.messages.append({"role": "assistant", "output": output})

                    if output.startswith('["Error"]'):
                        st.warning("Please provide your api key first!")
                    else:
                        sender = ['human', 'ai']
                        sql_conn.insert_chat(st.session_state["selected_conversation_id"], sender[0], question)
                        sql_conn.insert_chat(st.session_state["selected_conversation_id"], sender[1], output)
            except:
                st.warning("Please select a conversation first!")

        with col3:
            st.markdown(f'Prompt Template is using: {st.session_state["title_prompt_template"]}')
            st.markdown("System Prompt Template:")
            col_1, col_2 = st.columns([3, 1.5])
            with col_1:
                with st.popover("System Prompt Template", use_container_width=True):
                    st.markdown(f"{PROMPT_TEMPLATE}")
            with col_2:
                if st.button("Use this prompt", key='use_system_prompt_template'):
                    st.session_state["prompt_template"] = PROMPT_TEMPLATE
                    st.session_state["title_prompt_template"] = "System Prompt Template"
                    st.rerun()
            st.markdown("Your Prompt Template:")
            prompts = sql_conn.get_prompt_template(st.session_state["user_id"])
            for prompt_id, title, prompt_text in prompts:
                col_a, col_b, col_c = st.columns([5, 3, 0.5])
                with col_a:
                    with st.popover(f"{title}", use_container_width=True):
                        st.markdown(f"{prompt_text}")
                with col_b:
                    if st.button("Use this prompt", key='use'+prompt_id):
                        st.session_state["prompt_template"] = prompt_text
                        st.session_state["title_prompt_template"] = title
                        st.rerun()
                with col_c:
                    if st.button(label="", icon=":material/delete:", key=prompt_id, use_container_width=True):
                        sql_conn.delete_prompt_template(prompt_id)
                        st.rerun()
        col3.float()

    def Prompt_Session():
        st.markdown("Hello this is where you create your prompt template")
        if st.button(label="Add Prompt", icon=":material/add:"):
            st.session_state["add_prompt"] = True

        # Nếu nhấn nút "Create New Conversation", hiển thị hộp nhập để người dùng nhập tên hội thoại
        if "add_prompt" in st.session_state and st.session_state["add_prompt"]:
            title = st.text_input("Prompt Title:")
            prompt = st.text_area("Prompt:")
            if st.button(label="Add", icon=":material/add:"):
                if len(title) == 0:
                    st.warning("Title must not be empty!")
                elif len(prompt) == 0:
                    st.warning("Prompt message must not be empty!")
                else:
                    add_prompt_endpoint = "http://172.19.0.5:8000/add_prompt_template/"
                    data = {"title": title, "prompt_text": prompt, "user_id": st.session_state["user_id"]}
                    response = requests.post(add_prompt_endpoint, json=data)
                    if response.status_code == 200:
                        st.success("Add prompt successfully!")
                        st.session_state["add_prompt"] = False
                    else:
                        st.error(f"Failed to add prompt. Error {response.status_code}: {response.text}")

    def Chat_With_CSVFile():
        with st.sidebar:
            st.info(f"Nice to meet you: {st.session_state['user_name']}", icon=":material/sentiment_satisfied:")
            uploaded_file = st.file_uploader("Choose a file", type=["csv", "xls", "xlsx", "xlsm", "xlsb"])

            # Kiểm tra nếu người dùng chọn file
            if uploaded_file is not None:
                # Xác định URL của endpoint FastAPI và user_id
                upload_file_endpoint = "http://172.19.0.5:8000/upload_CSV_file/"

                if st.button(label="Upload File", icon=":material/upload_file:"):
                    # Gửi POST request với file trực tiếp từ Streamlit lên FastAPI
                    with st.spinner("Uploading..."):
                        try:
                            # Định nghĩa multipart-form cho file và các thông tin khác
                            files = {"file": (uploaded_file.name, uploaded_file)}
                            data = {"user_id": st.session_state["user_id"]}

                            # Gửi request lên FastAPI
                            response = requests.post(upload_file_endpoint, files=files, data=data)

                            # Hiển thị phản hồi
                            if response.status_code == 200:
                                st.success(response.json())
                                if "csv_file" in st.session_state:
                                    st.session_state["csv_file"].append(uploaded_file.name)
                                else:
                                    st.session_state["csv_file"] = [uploaded_file.name]
                                # for i in st.session_state["csv_file"]:
                                #     st.markdown(i)

                            else:
                                st.error(f"Failed to upload file. Error {response.status_code}: {response.text}")
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")
            if "csv_file" in st.session_state:
                for i in st.session_state["csv_file"]:
                    st.markdown(i)

        st.session_state.model = 'gpt-4o-mini'

        question = st.chat_input("What do you want to know?")

        if "messages_" not in st.session_state:
            st.session_state.messages_ = []

        for message in st.session_state.messages_:
            with st.chat_message(message["role"]):
                st.markdown(message["output"])

        # Gửi tin nhắn mới trong giao diện chat
        # try:
        if question:
            st.chat_message("user").markdown(question)
            st.session_state.messages_.append({"role": "user", "output": question})

            with st.chat_message("assistant"):
                response = handler_input_csv(question, st.session_state["user_id"], CSV_QA_URL, st.session_state.model)
                st.session_state.messages_.append({"role": "assistant", "output": response})
                st.rerun()
        # except:
        #     st.warning("Please upload csv file first!")

    def API_Key():
        st.subheader("API Keys")
        st.markdown("Your API Keys are stored locally on you computer and never sent anywhere else.")
        lst = [["./logo/gpt-4.webp", "openaikey"], ["./logo/gemini.png", "geminikey"]]
        col1, col2 = st.columns([6, 3])
        with col1:
            for logo, name in lst:
                col1, col2, col3 = st.columns([0.7, 10, 2.5])
                with col1:
                    st.image(logo)
                with col2:
                    if name == "openaikey":
                        st.session_state["openaikey"] = st.text_input(label="OpenAI API Key:", placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
                    else:
                        st.session_state["geminikey"] = st.text_input(label="Google Gemini API Key:", placeholder="AIxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
                with col3:
                    if st.button(label="", icon=":material/send:", key="key"+name):
                        if len(st.session_state[f"{name}"]) > 0:
                            try:
                                sql_conn.add_api_key(st.session_state["user_id"], name, st.session_state[f"{name}"])
                                st.session_state["get_apikey"] = True
                                if st.session_state["get_apikey"]:
                                    apikey = get_apikey(st.session_state["user_id"])
                                st.session_state["get_apikey"] = False
                                st.success("Saved API key!")
                            except:
                                sql_conn.change_api_key(st.session_state["user_id"], name, st.session_state[f"{name}"])
                                st.session_state["get_apikey"] = True
                                if st.session_state["get_apikey"]:
                                    apikey = get_apikey(st.session_state["user_id"])
                                st.session_state["get_apikey"] = False
                                st.success("Changed API key!")
                        else:
                            st.warning("API must not be empty!")


    pg = st.navigation([st.Page(Chat_Session), st.Page(Prompt_Session), st.Page(Chat_With_CSVFile), st.Page(API_Key)])
    pg.run()


