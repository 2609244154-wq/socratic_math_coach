# main_app.py
import streamlit as st
import uuid
from datetime import datetime
from core_agent import SocraticMathCoach

st.set_page_config(page_title="苏格拉底数学教练", page_icon="🦉", layout="centered")

# ==========================================
# 状态管理核心 (Session Management)
# ==========================================
# 初始化一个字典，用来存储所有的历史记录
if "history" not in st.session_state:
    st.session_state.history = {}

# 辅助函数：创建一个全新的问题会话
def create_new_session():
    new_session_id = str(uuid.uuid4()) # 生成唯一的ID
    st.session_state.history[new_session_id] = {
        "title": "新问题",
        "problem_text": "",
        "problem_image": None,
        "coach": SocraticMathCoach(), # 为这个会话创建一个独立的AI大脑
        "messages":[],               # 独立的聊天记录
        "problem_analyzed": False     # 状态：是否已解析
    }
    st.session_state.current_session_id = new_session_id

# 如果当前没有激活的会话，或者一开始刚进页面，则创建一个新会话
if "current_session_id" not in st.session_state or st.session_state.current_session_id is None:
    create_new_session()

# 获取当前正在操作的会话数据（后续代码都操作 current_session）
current_session = st.session_state.history[st.session_state.current_session_id]

# ==========================================
# 侧边栏：历史记录与当前题目
# ==========================================
with st.sidebar:
    # 新建问题按钮
    if st.button("➕ 问一道新题", use_container_width=True):
        create_new_session()
        st.rerun() # 刷新页面
        
    st.markdown("### 📚 历史问题")
    
    # 倒序遍历字典，让最新的问题显示在最上面
    for session_id, session_data in reversed(st.session_state.history.items()):
        # 只有已经被分析过（开始做）的题才显示在历史列表中
        if session_data["problem_analyzed"]:
            # 判断是不是当前正在看的题，加上一个小箭头标识
            prefix = "👉 " if session_id == st.session_state.current_session_id else "📝 "
            # 点击按钮切换当前的 session_id
            if st.button(prefix + session_data["title"], key=f"btn_{session_id}", use_container_width=True):
                st.session_state.current_session_id = session_id
                st.rerun()

    # 如果当前题已经开始做了，就在左下角展示题目的图片和文字，方便参考
    if current_session["problem_analyzed"]:
        st.markdown("---")
        st.markdown("### 📌 当前题目参考")
        if current_session["problem_image"]:
            st.image(current_session["problem_image"], use_container_width=True)
        if current_session["problem_text"]:
            st.info(current_session["problem_text"])


# ==========================================
# 主界面内容区
# ==========================================
st.title("🦉 苏格拉底式 AI 数学助教")
st.caption("“我不会直接给你答案，但我会引导你自己找到答案。”")

# 分支1：如果是还没开始分析的“新问题”
if not current_session["problem_analyzed"]:
    st.markdown("### 📝 请上传题目图片或输入文字")
    
    uploaded_file = st.file_uploader("📸 拍照或上传数学题图片 (支持 png, jpg)", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="已上传的题目预览", width=400)
    
    problem_text = st.text_area("补充文字说明 (可选)：", placeholder="请输入题目...", height=100)
    
    if st.button("🚀 开始分析题目"):
        if not problem_text.strip() and uploaded_file is None:
            st.warning("请上传图片或输入题目文字哦！")
        else:
            with st.spinner("AI正在后台读图、分析题目并提取知识点..."):
                image_bytes = uploaded_file.getvalue() if uploaded_file else None
                
                # 1. 调用当前会话的教练来解题
                current_session["coach"].analyze_problem(problem_text, image_bytes)
                
                # 2. 存储题目数据到当前会话
                current_session["problem_analyzed"] = True
                current_session["problem_text"] = problem_text
                current_session["problem_image"] = image_bytes
                
                # 3. 智能生成侧边栏显示的标题
                if problem_text:
                    # 取文字前12个字当标题
                    current_session["title"] = problem_text[:12] + "..."
                else:
                    # 如果只有图，按时间生成标题
                    current_session["title"] = f"图片题 {datetime.now().strftime('%H:%M:%S')}"
                
                # 4. Agent 2 主动开启对话
                greeting = "我已经仔细看过这道题啦！我们一步一步来解决它。你觉得第一步应该求什么？"
                current_session["messages"].append({"role": "assistant", "content": greeting})
                current_session["coach"].chat_history.append({"role": "assistant", "content": greeting})
                
            st.rerun()

# 分支2：如果是已经分析过的历史问题，显示对话流
else:
    st.markdown("### 💬 跟着教练一步步思考")
    
    # 渲染当前会话的历史聊天记录
    for msg in current_session["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # 接收学生新的输入
    if student_input := st.chat_input("输入你的想法、疑问或计算结果..."):
        # 记录用户的输入
        current_session["messages"].append({"role": "user", "content": student_input})
        with st.chat_message("user"):
            st.markdown(student_input)
        
        # 调用当前会话的教练生成回复
        with st.chat_message("assistant"):
            with st.spinner("教练正在思考如何引导你..."):
                tutor_reply = current_session["coach"].chat_with_student(student_input)
                st.markdown(tutor_reply)
        
        # 记录教练的回复
        current_session["messages"].append({"role": "assistant", "content": tutor_reply})