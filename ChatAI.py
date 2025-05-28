import os
import streamlit as st
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader, CSVLoader,UnstructuredExcelLoader
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.chains.conversation.base import ConversationChain
from langchain_openai import ChatOpenAI

api_key = "sk-8dca673d82b74bf59bac651337b7fba8"
base_url = "https://api.deepseek.com"  # 这是您需要使用的 API 基础 URL

# 初始化模型
model = ChatOpenAI(
    api_key=api_key,
    model='deepseek-chat',
    base_url=base_url
)

# 初始化对话记忆
memory = ConversationBufferMemory(return_messages=True)
# 初始化对话链
chain = ConversationChain(llm=model, memory=memory)
# 初始化对话上下文
if 'messages' not in st.session_state:
    st.session_state['messages'] = [{'role': 'ai', 'content': '你好主人，我是你的AI助手，我叫小凌'}]
    st.session_state['memory'] = memory

def get_ai_response(model, memory, user_input):
    # 初始化对话记忆
    memory = ConversationBufferMemory(return_messages=True)
    # 初始化对话链
    chain = ConversationChain(llm=model, memory=memory)
    response = chain.invoke({'input': user_input})
    ai_response = response["response"]  # 获取AI的回复内容
    return ai_response

# 主标题
st.title('我的ChatGPT')

# 文件上传功能
st.subheader("上传文档")
uploaded_file = st.file_uploader("选择一个文件", type=["txt", "pdf", "docx", "csv", "xlsx"])

# 欢迎信息
st.write("你好主人，我是你的AI助手，我叫小凌")

def extract_content(file_path, file_type):
    """根据文件类型提取内容"""
    if file_type == "text/plain":
        loader = TextLoader(file_path, encoding="utf-8")
    elif file_type == "application/pdf":
        loader = PyPDFLoader(file_path)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        loader = Docx2txtLoader(file_path)
    elif file_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.csv", "application/vnd.ms-excel", "text/csv"]:
        loader = CSVLoader(file_path, encoding="utf-8")
    elif file_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        loader = UnstructuredExcelLoader(file_path)
    else:
        st.error(f"不支持的文件类型: {file_type}。请上传以下类型的文件：TXT, PDF, DOCX, CSV, XLSX")
        st.stop()

    docs = loader.load()
    file_content = ""
    for doc in docs:
        if hasattr(doc, 'page_content'):
            file_content += doc.page_content + "\n"
        elif hasattr(doc, 'text'):
            file_content += doc.text + "\n"
        else:
            file_content += str(doc) + "\n"
    return file_content

if uploaded_file is not None:
    # 打印文件类型，用于调试
    st.write(f"调试文件类型：{uploaded_file.type}")

    # 将上传的文件保存到本地
    file_path = os.path.join("uploads", uploaded_file.name)
    os.makedirs("uploads", exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getvalue())

    # 提取文件内容
    try:
        file_content = extract_content(file_path, uploaded_file.type)
        st.write("文件内容预览：")
        st.code(file_content, language="plaintext")
    except Exception as e:
        st.error(f"处理文件时出错: {e}")
        st.stop()

    # 保存文件内容到对话记忆
    st.session_state['memory'].save_context({"input": file_content}, {"output": ""})
    st.write("文件已成功加载，我可以帮您总结主要内容、提取关键信息或回答与文件内容相关的问题，请告诉我您的需求。")

for message in st.session_state['messages']:
    role, content = message['role'], message['content']
    st.chat_message(role).write(content)

user_input = st.chat_input()
if user_input:
    st.chat_message('human').write(user_input)
    st.session_state['messages'].append({'role': 'human', 'content': user_input})
    with st.spinner('AI正在思考，请等待……'):
        resp_from_ai = get_ai_response(model, st.session_state['memory'], user_input)
        st.session_state['messages'].append({'role': 'ai', 'content': resp_from_ai})
        st.chat_message('ai').write(resp_from_ai)