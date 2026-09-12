import streamlit as st
from google import genai
from google.genai import types
import json
import os
import uuid
import shutil


# ==========================================
# SETTINGS
# ==========================================

CHAT_FILE = "chats.json"
UPLOAD_FOLDER = "uploaded_files"


os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==========================================
# GEMINI CLIENT
# ==========================================

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)


# ==========================================
# AI STUDY ASSISTANT PERSONALITY
# ==========================================

STUDY_INSTRUCTION = """
You are a professional AI Study Assistant.

Rules:
1. Answer questions on any topic.
2. Use simple and clear language.
3. Keep answers focused and professional.
4. Use bullet points when useful.
5. Give examples when helpful.
6. For programming questions, give correct code when needed.
7. If the user asks ELI10, explain in very simple language.
8. For exam questions, provide exam-ready answers.
9. Do not give unnecessary long introductions.
10. Remember and use the conversation history provided to you.
11. If an image or PDF was discussed earlier in the conversation,
    use the information from the conversation history when answering.
"""


# ==========================================
# LOAD CHATS
# ==========================================

def load_chats():

    if not os.path.exists(CHAT_FILE):
        return []

    try:
        with open(
            CHAT_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except Exception:
        return []


# ==========================================
# SAVE CHATS
# ==========================================

def save_chats():

    with open(
        CHAT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            st.session_state.chats,
            file,
            indent=4,
            ensure_ascii=False
        )


# ==========================================
# SESSION STATE
# ==========================================

if "chats" not in st.session_state:
    st.session_state.chats = load_chats()

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

if "messages" not in st.session_state:
    st.session_state.messages = []


# ==========================================
# GET CHAT
# ==========================================

def get_chat(chat_id):

    for chat in st.session_state.chats:

        if chat.get("id") == chat_id:
            return chat

    return None


# ==========================================
# CREATE NEW CHAT
# ==========================================

def create_new_chat(name):

    new_chat = {
        "id": str(uuid.uuid4()),
        "name": name,
        "messages": []
    }

    st.session_state.chats.append(new_chat)

    st.session_state.current_chat = new_chat["id"]

    st.session_state.messages = []

    save_chats()


# ==========================================
# OPEN CHAT
# ==========================================

def open_chat(chat_id):

    chat = get_chat(chat_id)

    if chat is None:
        return

    st.session_state.current_chat = chat_id

    st.session_state.messages = chat.get(
        "messages",
        []
    )


# ==========================================
# DELETE CHAT
# ==========================================

def delete_chat(chat_id):

    st.session_state.chats = [
        chat
        for chat in st.session_state.chats
        if chat.get("id") != chat_id
    ]

    if st.session_state.current_chat == chat_id:

        st.session_state.current_chat = None

        st.session_state.messages = []

    save_chats()

    folder = os.path.join(
        UPLOAD_FOLDER,
        chat_id
    )

    if os.path.exists(folder):

        try:
            shutil.rmtree(folder)
        except Exception:
            pass


# ==========================================
# RENAME CHAT
# ==========================================

def rename_chat(chat_id, new_name):

    chat = get_chat(chat_id)

    if chat:

        chat["name"] = new_name

        save_chats()


# ==========================================
# SEND MESSAGE TO GEMINI
# ==========================================

def ask_gemini(
    messages,
    question,
    uploaded_file=None
):

    history = []

    for message in messages:

        user_text = message.get(
            "user",
            ""
        )

        ai_text = message.get(
            "ai",
            ""
        )

        if user_text:

            history.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text=user_text
                        )
                    ]
                )
            )

        if ai_text:

            history.append(
                types.Content(
                    role="model",
                    parts=[
                        types.Part.from_text(
                            text=ai_text
                        )
                    ]
                )
            )


    config = types.GenerateContentConfig(
        system_instruction=STUDY_INSTRUCTION
    )


    chat = client.chats.create(
        model="gemini-3.6-flash",
        history=history,
        config=config
    )


    # ======================================
    # TEXT QUESTION
    # ======================================

    if uploaded_file is None:

        response = chat.send_message(
            question
        )

        return response.text


    # ======================================
    # IMAGE / PDF QUESTION
    # ======================================

    file_part = types.Part.from_bytes(
        data=uploaded_file.getvalue(),
        mime_type=uploaded_file.type
    )


    response = chat.send_message(
        [
            types.Part.from_text(
                text=question
            ),
            file_part
        ]
    )

    return response.text


# ==========================================
# PAGE SETTINGS
# ==========================================

st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="🤖",
    layout="wide"
)


# ==========================================
# HEADER
# ==========================================

st.title("🤖 AI Study Assistant")

st.caption(
    "Your personal AI assistant for learning, coding and everyday questions."
)


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.header("💬 Chats")


    # ======================================
    # NEW CHAT
    # ======================================

    new_chat_name = st.text_input(
        "New chat name"
    )


    if st.button(
        "➕ Start New Chat",
        use_container_width=True
    ):

        if new_chat_name.strip():

            create_new_chat(
                new_chat_name.strip()
            )

            st.rerun()

        else:

            st.warning(
                "Enter a chat name first."
            )


    st.divider()


    # ======================================
    # PREVIOUS CHATS
    # ======================================

    st.subheader("Previous Chats")


    if st.session_state.chats:

        for chat in st.session_state.chats:

            col1, col2 = st.columns(
                [5, 1]
            )


            with col1:

                if st.button(
                    chat.get(
                        "name",
                        "Unnamed Chat"
                    ),
                    key="open_" + chat["id"],
                    use_container_width=True
                ):

                    open_chat(
                        chat["id"]
                    )

                    st.rerun()


            with col2:

                if st.button(
                    "🗑️",
                    key="delete_" + chat["id"]
                ):

                    delete_chat(
                        chat["id"]
                    )

                    st.rerun()

    else:

        st.info(
            "No previous chats."
        )


# ==========================================
# CURRENT CHAT
# ==========================================

current_chat = None


if st.session_state.current_chat:

    current_chat = get_chat(
        st.session_state.current_chat
    )


# ==========================================
# CHAT SCREEN
# ==========================================

if current_chat:

    st.subheader(
        "💬 " + current_chat.get(
            "name",
            "Chat"
        )
    )


    # ======================================
    # RENAME CHAT
    # ======================================

    with st.expander("✏️ Rename Chat"):

        rename_input = st.text_input(
            "New chat name",
            value=current_chat.get(
                "name",
                ""
            )
        )


        if st.button(
            "Save New Name"
        ):

            if rename_input.strip():

                rename_chat(
                    current_chat["id"],
                    rename_input.strip()
                )

                st.rerun()


    # ======================================
    # SHOW OLD MESSAGES
    # ======================================

    for message in st.session_state.messages:

        user_message = message.get(
            "user",
            ""
        )

        ai_message = message.get(
            "ai",
            ""
        )


        if user_message:

            with st.chat_message("user"):

                st.write(
                    user_message
                )


        if ai_message:

            with st.chat_message("assistant"):

                st.markdown(
                    ai_message
                )


        # Show previously uploaded file name
        if message.get("file"):

            st.caption(
                "📎 " + message["file"]
            )


    # ======================================
    # FILE UPLOAD
    # ======================================

    uploaded_file = st.file_uploader(
        "📎 Upload an image or PDF",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
            "pdf"
        ]
    )


    # ======================================
    # CHAT INPUT
    # ======================================

    question = st.chat_input(
        "Ask your question..."
    )


    if question:

        with st.chat_message("user"):

            st.write(
                question
            )


        with st.chat_message("assistant"):

            with st.spinner(
                "Thinking..."
            ):

                try:

                    answer = ask_gemini(
                        st.session_state.messages,
                        question,
                        uploaded_file
                    )


                    st.markdown(
                        answer
                    )


                    # ==================================
                    # SAVE MESSAGE
                    # ==================================

                    message_data = {
                        "type": (
                            "file"
                            if uploaded_file
                            else "text"
                        ),
                        "user": question,
                        "ai": answer
                    }


                    # ==================================
                    # SAVE FILE
                    # ==================================

                    if uploaded_file:

                        message_data["file"] = (
                            uploaded_file.name
                        )


                        chat_folder = os.path.join(
                            UPLOAD_FOLDER,
                            current_chat["id"]
                        )


                        os.makedirs(
                            chat_folder,
                            exist_ok=True
                        )


                        file_path = os.path.join(
                            chat_folder,
                            uploaded_file.name
                        )


                        with open(
                            file_path,
                            "wb"
                        ) as file:

                            file.write(
                                uploaded_file.getvalue()
                            )


                    # ==================================
                    # UPDATE CHAT
                    # ==================================

                    st.session_state.messages.append(
                        message_data
                    )


                    current_chat["messages"] = (
                        st.session_state.messages
                    )


                    save_chats()


                except Exception as e:

                    st.error(
                        f"Error: {e}"
                    )


else:

    st.info(
        "👈 Start a new chat or open a previous chat."
    )
