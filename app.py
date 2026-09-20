import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("RAG Chatbot")
    st.caption("Thay mô tả theo đề tài của nhóm")
    top_k = st.slider("Số chunks", 3, 10, 5)

st.title("RAG Chatbot")
st.caption("Hỏi đáp dựa trên corpus pháp luật Việt Nam và tin công nghệ")


def render_sources(message: dict) -> None:
    sources = message.get("sources", [])
    if not sources:
        return
    with st.expander(f"Nguồn đã dùng ({len(sources)})"):
        st.caption(f"Retrieval source: {message.get('retrieval_source', 'unknown')}")
        for index, source in enumerate(sources, 1):
            metadata = source.get("metadata", {})
            title = metadata.get("title", metadata.get("source", "Unknown"))
            url = metadata.get("url")
            label = f"{index}. {title} — score={source.get('score', 0):.4f}"
            if url:
                st.markdown(f"- [{label}]({url})")
            else:
                st.markdown(f"- {label}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_sources(message)

query = st.chat_input("Nhập câu hỏi...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        result = generate_with_citation(query, top_k=top_k)
        answer = result["answer"]
        st.markdown(answer)
        render_sources(result)
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "sources": result["sources"],
                "retrieval_source": result["retrieval_source"],
            }
        )
