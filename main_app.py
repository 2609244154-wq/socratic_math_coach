"""
苏格拉底式数学解题教练 - 主应用
基于Streamlit的Web界面，通过AI引导帮助学生自主解决数学问题
"""

import streamlit as st
import uuid
from datetime import datetime
import os
import json
from io import BytesIO
import traceback
from PIL import Image
import io
import sys
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 尝试导入核心模块
try:
    from core_agent import SocraticMathCoach
    CORE_IMPORTED = True
except ImportError as e:
    st.error(f"❌ 导入核心模块失败: {e}")
    CORE_IMPORTED = False
    # 创建一个虚拟的教练类用于调试
    class SocraticMathCoach:
        def __init__(self):
            self.api_available = False
        def analyze_problem(self, text, image_bytes):
            return {"status": "no_api"}
        def chat_with_student(self, text):
            return "请先在侧边栏设置智谱AI API密钥"

# 页面配置
st.set_page_config(
    page_title="🦉 苏格拉底数学教练",
    page_icon="🦉",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/socratic-math-coach',
        'Report a bug': 'https://github.com/yourusername/socratic-math-coach/issues',
        'About': """
        # 🦉 苏格拉底式数学解题教练
        
        一个基于AI的数学学习助手，通过引导式提问帮助学生自主解决数学问题。
        
        **功能特点:**
        - 📸 支持拍照/上传数学题目图片
        - 💬 智能OCR文字识别
        - 🧠 苏格拉底式引导提问
        - 📚 知识点自动分析
        - 💾 多会话历史管理
        
        **教育理念:**
        我们不直接给出答案，而是通过提问引导学生自己思考，培养独立解决问题的能力。
        
        **版本:** 1.0.0
        **开发者:** 人工智能课程项目组
        """
    }
)

# 检查是否在云端环境
IS_CLOUD = os.getenv("STREAMLIT_CLOUD") is not None

# ==========================================
# 自定义CSS样式
# ==========================================
st.markdown("""
<style>
    /* 主标题样式 */
    .main-title {
        text-align: center;
        color: #1E3A8A;
        margin-bottom: 1rem;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* 副标题 */
    .sub-title {
        text-align: center;
        color: #6B7280;
        margin-bottom: 2rem;
        font-size: 1.1rem;
    }
    
    /* 卡片样式 */
    .info-card {
        background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        color: white;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    
    .warning-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        color: white;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    
    .success-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        color: white;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    
    /* 按钮样式 */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    
    /* 主按钮 */
    [data-testid="stButton"]:has(button[kind="primary"]) button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* 二级按钮 */
    [data-testid="stButton"]:has(button[kind="secondary"]) button {
        background: linear-gradient(135deg, #6EE7B7 0%, #3B82F6 100%);
        color: white;
    }
    
    /* 聊天消息样式 */
    .user-message {
        background: linear-gradient(135deg, #3B82F6 0%, #1E40AF 100%);
        color: white;
        border-radius: 20px 20px 0 20px;
        padding: 12px 18px;
        margin: 8px 0;
        max-width: 85%;
        margin-left: auto;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%);
        color: #1F2937;
        border-radius: 20px 20px 20px 0;
        padding: 12px 18px;
        margin: 8px 0;
        max-width: 85%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* 进度条容器 */
    .progress-container {
        width: 100%;
        height: 8px;
        background-color: #E5E7EB;
        border-radius: 10px;
        margin: 15px 0;
        overflow: hidden;
    }
    
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        transition: width 1s ease-in-out;
    }
    
    /* 会话卡片 */
    .session-card {
        border: 2px solid transparent;
        background: linear-gradient(white, white) padding-box,
                    linear-gradient(135deg, #667eea 0%, #764ba2 100%) border-box;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .session-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    
    .session-card.active {
        border: 2px solid #3B82F6;
        background-color: rgba(59, 130, 246, 0.05);
    }
    
    /* 图片预览 */
    .image-preview {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    
    /* 响应式调整 */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem;
        }
        
        .user-message, .assistant-message {
            max-width: 90%;
        }
    }
    
    /* 代码块样式 */
    .stCodeBlock {
        border-radius: 10px;
        border: 1px solid #E5E7EB;
    }
    
    /* 分隔线 */
    .divider {
        height: 3px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 3px;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 状态管理
# ==========================================
if "history" not in st.session_state:
    st.session_state.history = {}

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "app_started" not in st.session_state:
    st.session_state.app_started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 辅助函数：创建一个全新的问题会话
def create_new_session():
    """创建一个新的解题会话"""
    new_session_id = str(uuid.uuid4())
    
    # 初始化教练
    coach = None
    if CORE_IMPORTED:
        try:
            coach = SocraticMathCoach()
        except Exception as e:
            st.error(f"创建AI教练失败: {e}")
    
    st.session_state.history[new_session_id] = {
        "title": "新问题",
        "problem_text": "",
        "problem_image": None,
        "problem_image_display": None,  # 用于显示的图片
        "coach": coach,
        "messages": [],
        "problem_analyzed": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "step_count": 0,
        "hint_count": 0
    }
    st.session_state.current_session_id = new_session_id
    
    # 记录日志
    log_event("create_session", new_session_id)
    
    return new_session_id

# 辅助函数：日志记录
def log_event(event_type, session_id, data=None):
    """记录用户事件"""
    if IS_CLOUD:
        return  # 云端不记录日志
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        "session_id": session_id,
        "data": data or {}
    }
    
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/usage_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"日志记录失败: {e}")

# 压缩图片函数
def compress_image(image_bytes, max_size=(1024, 1024), quality=85):
    """压缩图片以减少内存使用"""
    try:
        image = Image.open(BytesIO(image_bytes))
        
        # 如果是PNG且有透明通道，转换为RGB
        if image.mode in ('RGBA', 'LA', 'P'):
            # 创建一个白色背景
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # 调整尺寸
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 转换为JPEG格式
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
        return img_byte_arr.getvalue()
    except Exception as e:
        st.warning(f"图片压缩失败: {e}")
        return image_bytes

# 保存会话到本地
def save_session_to_file(session_id, session_data):
    """将会话保存到本地文件（仅用于备份）"""
    if IS_CLOUD:
        return
    
    try:
        os.makedirs("sessions", exist_ok=True)
        filepath = f"sessions/session_{session_id}.json"
        
        # 准备保存的数据（移除教练对象）
        save_data = {k: v for k, v in session_data.items() if k != 'coach'}
        save_data['coach'] = {
            'api_available': session_data['coach'].api_available if hasattr(session_data['coach'], 'api_available') else False
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存会话失败: {e}")

# 清理旧会话
def cleanup_old_sessions(max_sessions=20):
    """清理旧的会话，防止内存占用过大"""
    if len(st.session_state.history) > max_sessions:
        # 按最后更新时间排序
        sorted_sessions = sorted(
            st.session_state.history.items(),
            key=lambda x: x[1]["last_updated"]
        )
        
        # 删除最旧的会话
        while len(st.session_state.history) > max_sessions:
            oldest_id, _ = sorted_sessions.pop(0)
            del st.session_state.history[oldest_id]

# ==========================================
# 侧边栏
# ==========================================
with st.sidebar:
    # 应用标题卡片
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("### 🦉 苏格拉底数学教练")
    st.markdown("通过提问引导你自主解决数学问题")
    st.markdown("**版本:** 1.0.0")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # API密钥设置
    with st.expander("🔑 API设置", expanded=False):
        if IS_CLOUD:
            st.success("✅ API密钥已通过云端配置")
        else:
            # 尝试从环境变量获取
            env_api_key = os.getenv("ZHIPUAI_API_KEY", "")
            default_key = env_api_key if env_api_key else ""
            
            api_key = st.text_input(
                "智谱AI API密钥",
                type="password",
                help="从 https://open.bigmodel.cn/ 获取",
                value=default_key,
                placeholder="请输入你的智谱AI API密钥"
            )
            
            if api_key:
                os.environ["ZHIPUAI_API_KEY"] = api_key
                st.success("✅ API密钥已保存到当前会话")
                
                # 如果已存在问题会话，更新教练的API密钥
                for session_id, session_data in st.session_state.history.items():
                    if session_data["coach"]:
                        session_data["coach"].update_api_key(api_key)
    
    # 新建问题按钮
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("➕ 新建问题", use_container_width=True, type="primary"):
            new_id = create_new_session()
            st.toast(f"✅ 已创建新问题会话: {new_id[:8]}...")
            st.rerun()
    with col2:
        if st.button("🔄", help="刷新页面", use_container_width=True):
            st.rerun()
    
    st.markdown("### 📚 历史会话")
    
    # 显示历史会话
    if not st.session_state.history:
        st.info("暂无历史问题，点击'新建问题'开始")
    else:
        # 按最后更新时间排序
        sorted_sessions = sorted(
            st.session_state.history.items(),
            key=lambda x: x[1]["last_updated"],
            reverse=True
        )
        
        for session_id, session_data in sorted_sessions:
            if session_data["problem_analyzed"]:
                # 判断当前会话
                is_current = session_id == st.session_state.current_session_id
                
                # 创建会话卡片
                card_class = "session-card active" if is_current else "session-card"
                st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([6, 1, 1])
                with col1:
                    display_title = session_data["title"]
                    if len(display_title) > 20:
                        display_title = display_title[:20] + "..."
                    
                    if st.button(
                        f"📝 {display_title}",
                        key=f"btn_{session_id}",
                        use_container_width=True,
                        help=f"创建于: {session_data['created_at']}"
                    ):
                        st.session_state.current_session_id = session_id
                        st.rerun()
                
                with col2:
                    steps = session_data.get("step_count", 0)
                    st.caption(f"🔢 {steps}")
                
                with col3:
                    if st.button("🗑️", key=f"del_{session_id}", help="删除此会话"):
                        if len(st.session_state.history) > 1:
                            del st.session_state.history[session_id]
                            if st.session_state.current_session_id == session_id:
                                # 切换到另一个会话
                                remaining_ids = list(st.session_state.history.keys())
                                st.session_state.current_session_id = remaining_ids[0] if remaining_ids else None
                            st.toast(f"🗑️ 已删除会话: {session_id[:8]}...")
                            st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    # 显示当前题目
    if st.session_state.current_session_id and st.session_state.history:
        current_session = st.session_state.history[st.session_state.current_session_id]
        if current_session["problem_analyzed"]:
            st.markdown("---")
            st.markdown("### 📌 当前题目")
            
            if current_session["problem_image_display"]:
                st.image(current_session["problem_image_display"], 
                        caption="📷 题目图片", 
                        use_container_width=True)
            
            if current_session["problem_text"]:
                with st.expander("📄 题目文字", expanded=False):
                    st.info(current_session["problem_text"])
    
    # 系统状态
    st.markdown("---")
    st.markdown("### 🔧 系统状态")
    
    col1, col2 = st.columns(2)
    with col1:
        # 检查API密钥
        api_key = os.getenv("ZHIPUAI_API_KEY", "")
        if not api_key and hasattr(st, "secrets"):
            if "ZHIPUAI_API_KEY" in st.secrets:
                api_key = st.secrets["ZHIPUAI_API_KEY"]
        
        if api_key:
            st.success("🔑 API: 已设置")
        else:
            st.error("🔑 API: 未设置")
    
    with col2:
        if CORE_IMPORTED:
            st.success("🧠 核心: 正常")
        else:
            st.error("🧠 核心: 异常")
    
    # 统计信息
    active_sessions = len([s for s in st.session_state.history.values() if s["problem_analyzed"]])
    st.metric("📊 活跃会话", active_sessions)
    
    # 清理会话按钮
    if len(st.session_state.history) > 10:
        if st.button("🧹 清理旧会话", use_container_width=True, type="secondary"):
            cleanup_old_sessions(max_sessions=10)
            st.toast(f"🧹 已清理，保留10个最新会话")
            st.rerun()
    
    # 分享功能
    st.markdown("---")
    st.markdown("### 📤 分享应用")
    
    if IS_CLOUD:
        share_url = st.secrets.get("SHARE_URL", "https://socratic-math-coach.streamlit.app")
    else:
        share_url = "http://localhost:8501"
    
    st.code(share_url, language="text")
    
    if st.button("📋 复制链接", use_container_width=True, type="secondary"):
        st.code(share_url, language="text")
        st.toast("🔗 链接已复制到剪贴板！")

# ==========================================
# 主界面
# ==========================================
# 页面标题
st.markdown('<h1 class="main-title">🦉 苏格拉底式数学解题教练</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">💡 我不会直接给你答案，但我会通过提问引导你自己找到答案。</p>', unsafe_allow_html=True)

# 检查核心模块
if not CORE_IMPORTED:
    st.markdown('<div class="warning-card">', unsafe_allow_html=True)
    st.error("⚠️ 无法导入核心模块，请检查依赖安装：")
    st.code("pip install -r requirements.txt", language="bash")
    st.markdown("""
    如果已安装依赖仍报错，请尝试：
    1. 重新安装虚拟环境
    2. 检查Python版本（需要3.8+）
    3. 查看详细错误信息
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 显示详细的错误信息
    with st.expander("🔍 查看详细错误"):
        st.code(traceback.format_exc())

# 如果没有当前会话，创建新会话
if st.session_state.current_session_id is None or st.session_state.current_session_id not in st.session_state.history:
    create_new_session()

# 获取当前会话
current_session = st.session_state.history[st.session_state.current_session_id]

# 分支1：还未分析的"新问题"
if not current_session["problem_analyzed"]:
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("## 📝 上传数学题目")
    st.markdown("请选择一种方式提供题目，我们将通过AI进行分析和引导")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 上传方式选择
    upload_method = st.radio(
        "选择上传方式：",
        ["📷 上传图片", "✍️ 输入文字", "📸 拍照（手机推荐）"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    problem_text = ""
    uploaded_file = None
    image_bytes = None
    
    if upload_method == "📷 上传图片":
        uploaded_file = st.file_uploader(
            "选择数学题目图片",
            type=["png", "jpg", "jpeg", "bmp"],
            help="支持 PNG, JPG, JPEG, BMP 格式，建议图片清晰、光线充足",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            # 压缩并显示图片
            image_bytes = uploaded_file.getvalue()
            try:
                compressed_bytes = compress_image(image_bytes)
                current_session["problem_image_display"] = compressed_bytes
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.image(compressed_bytes, 
                            caption="📷 已上传的题目", 
                            use_container_width=True)
                with col2:
                    file_size = len(compressed_bytes) / 1024
                    st.metric("📁 文件大小", f"{file_size:.1f} KB")
                    
            except Exception as e:
                st.error(f"图片处理失败: {e}")
                current_session["problem_image_display"] = image_bytes
                st.image(image_bytes, caption="📷 原始图片", use_container_width=True)
    
    elif upload_method == "✍️ 输入文字":
        problem_text = st.text_area(
            "输入题目内容：",
            placeholder="""例如：
在直角三角形ABC中，∠C=90°，AC=3，BC=4，求AB的长度。

或者更复杂的问题：
已知二次函数f(x)=ax²+bx+c的图像经过点(1,0)、(2,0)和(0,2)，
求该二次函数的表达式，并判断其图像的开口方向。""",
            height=200,
            label_visibility="collapsed"
        )
        
        if problem_text:
            st.info(f"📄 已输入 {len(problem_text)} 个字符")
    
    else:  # 拍照模式
        st.info("📱 请在手机浏览器中打开此页面，使用相机拍照上传")
        
        camera_input = st.camera_input(
            "对准数学题目拍照",
            help="确保题目清晰可见，避免反光",
            label_visibility="collapsed"
        )
        
        if camera_input is not None:
            image_bytes = camera_input.getvalue()
            compressed_bytes = compress_image(image_bytes)
            current_session["problem_image_display"] = compressed_bytes
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.image(compressed_bytes, 
                        caption="📸 拍摄的题目", 
                        use_container_width=True)
            with col2:
                file_size = len(compressed_bytes) / 1024
                st.metric("📁 文件大小", f"{file_size:.1f} KB")
    
    # 如果上传了图片，可以补充文字说明
    if uploaded_file is not None or camera_input is not None:
        st.markdown("### 📝 补充说明")
        problem_text = st.text_area(
            "补充文字说明（可选）：",
            placeholder="如果图片中的文字识别不准确，可以在这里补充或修正...\n也可以描述图片中难以识别的部分。",
            height=120,
            label_visibility="collapsed"
        )
    
    # 开始分析按钮
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        analyze_disabled = (not problem_text.strip() and uploaded_file is None and camera_input is None)
        
        if st.button("🚀 开始AI分析", 
                    type="primary", 
                    use_container_width=True,
                    disabled=analyze_disabled):
            
            if analyze_disabled:
                st.warning("请上传图片或输入题目文字！")
            else:
                with st.spinner("🤔 AI正在分析题目..."):
                    try:
                        # 更新会话的最后修改时间
                        current_session["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # 处理图片
                        image_bytes_to_analyze = None
                        if uploaded_file is not None:
                            image_bytes_to_analyze = uploaded_file.getvalue()
                        elif camera_input is not None:
                            image_bytes_to_analyze = camera_input.getvalue()
                        
                        # 1. 分析题目
                        current_session["problem_text"] = problem_text
                        if current_session["problem_image_display"]:
                            current_session["problem_image"] = current_session["problem_image_display"]
                        
                        analysis_result = {}
                        if current_session["coach"]:
                            analysis_result = current_session["coach"].analyze_problem(
                                problem_text, 
                                image_bytes_to_analyze
                            )
                        
                        # 2. 更新会话状态
                        current_session["problem_analyzed"] = True
                        current_session["step_count"] = 1
                        
                        # 3. 生成标题
                        if problem_text:
                            # 提取前20个字符作为标题
                            clean_text = ' '.join(problem_text.split())
                            if len(clean_text) > 20:
                                title = clean_text[:20] + "..."
                            else:
                                title = clean_text
                        else:
                            title = f"图片题 {datetime.now().strftime('%H:%M')}"
                        current_session["title"] = title
                        
                        # 4. 添加欢迎消息
                        welcome_msg = """🤔 我已经仔细看过这道题了！让我通过提问来引导你找到答案。

首先，请告诉我：
1. 题目中给出了哪些已知条件？
2. 题目要求我们求什么？

试着用自己的话描述一下题目的意思。"""
                        
                        current_session["messages"].append({
                            "role": "assistant",
                            "content": welcome_msg,
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                        
                        # 5. 记录日志
                        log_event("analyze_problem", st.session_state.current_session_id, {
                            "has_image": image_bytes_to_analyze is not None,
                            "text_length": len(problem_text)
                        })
                        
                        # 6. 保存会话
                        save_session_to_file(st.session_state.current_session_id, current_session)
                        
                        st.toast("✅ 题目分析完成！开始对话吧")
                        
                    except Exception as e:
                        st.error(f"❌ 分析失败: {str(e)}")
                        with st.expander("查看错误详情"):
                            st.code(traceback.format_exc())
                    
                    finally:
                        # 添加一个小延迟确保状态更新
                        time.sleep(0.5)
                        st.rerun()

# 分支2：已经分析过的历史问题，显示对话流
else:
    # 显示当前会话信息
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"### 💬 对话: {current_session['title']}")
    with col2:
        st.caption(f"步骤: {current_session.get('step_count', 0)}")
    with col3:
        st.caption(f"📅 {current_session['created_at'][:10]}")
    
    # 进度条
    progress_value = min(current_session.get("step_count", 0) * 0.2, 1.0)
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar" style="width: {progress_value * 100}%"></div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("理解题目")
    with col2:
        st.caption("分析思路")
    with col3:
        st.caption("解决问题" if progress_value > 0.5 else "")
    
    # 渲染当前会话的历史聊天记录
    chat_container = st.container()
    
    with chat_container:
        for idx, msg in enumerate(current_session["messages"]):
            avatar = "🦉" if msg["role"] == "assistant" else "👨‍🎓"
            
            with st.chat_message(msg["role"], avatar=avatar):
                # 显示消息内容
                st.markdown(msg["content"])
                
                # 显示时间戳
                if "timestamp" in msg:
                    st.caption(f"⏰ {msg['timestamp']}")
                
                # 为AI消息添加反馈按钮
                if msg["role"] == "assistant" and idx == len(current_session["messages"]) - 1:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if st.button("👍 有帮助", key=f"helpful_{idx}", use_container_width=True):
                            st.toast("谢谢反馈！")
                    with col2:
                        if st.button("👎 没帮助", key=f"unhelpful_{idx}", use_container_width=True):
                            st.toast("收到反馈，我会改进！")
                    with col3:
                        if st.button("💡 需要提示", key=f"hint_{idx}", use_container_width=True):
                            with st.spinner("思考中..."):
                                hint = current_session["coach"].generate_hint()
                                current_session["messages"].append({
                                    "role": "assistant",
                                    "content": f"💡 提示: {hint}",
                                    "timestamp": datetime.now().strftime("%H:%M:%S")
                                })
                                current_session["hint_count"] += 1
                                st.rerun()
                    with col4:
                        if st.button("🔄 重新解释", key=f"rephrase_{idx}", use_container_width=True):
                            with st.spinner("重新组织语言..."):
                                # 这里可以调用API重新生成解释
                                st.toast("功能开发中...")
    
    # 接收学生新的输入
    st.markdown("---")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        student_input = st.chat_input(
            "输入你的想法、疑问或计算结果...",
            key=f"chat_input_{st.session_state.current_session_id}"
        )
    with col2:
        if st.button("💡 获取提示", use_container_width=True, type="secondary"):
            with st.spinner("生成提示中..."):
                if current_session["coach"]:
                    hint = current_session["coach"].generate_hint()
                    current_session["messages"].append({
                        "role": "assistant",
                        "content": f"💡 提示: {hint}",
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    current_session["hint_count"] += 1
                    st.rerun()
    
    if student_input:
        # 记录用户的输入
        current_session["messages"].append({
            "role": "user",
            "content": student_input,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        
        # 更新会话信息
        current_session["step_count"] += 1
        current_session["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 显示用户消息
        with chat_container:
            with st.chat_message("user", avatar="👨‍🎓"):
                st.markdown(student_input)
                st.caption(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        
        # 调用AI生成回复
        with st.spinner("🦉 教练正在思考如何引导你..."):
            try:
                if current_session["coach"]:
                    tutor_reply = current_session["coach"].chat_with_student(student_input)
                else:
                    tutor_reply = "请先在侧边栏设置智谱AI API密钥才能继续对话。"
                
                # 显示教练回复
                with chat_container:
                    with st.chat_message("assistant", avatar="🦉"):
                        st.markdown(tutor_reply)
                        st.caption(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
                
                # 记录教练的回复
                current_session["messages"].append({
                    "role": "assistant",
                    "content": tutor_reply,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
                # 记录日志
                log_event("chat_message", st.session_state.current_session_id, {
                    "input_length": len(student_input),
                    "reply_length": len(tutor_reply)
                })
                
                # 保存会话
                save_session_to_file(st.session_state.current_session_id, current_session)
                
            except Exception as e:
                error_msg = f"❌ 对话出错: {str(e)}"
                st.error(error_msg)
                
                with st.expander("查看错误详情"):
                    st.code(traceback.format_exc())
                
                # 添加错误消息
                current_session["messages"].append({
                    "role": "assistant",
                    "content": "抱歉，处理您的消息时出现了技术问题。请检查API密钥设置或稍后重试。",
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
        
        # 自动滚动
        st.rerun()

# ==========================================
# 页脚
# ==========================================
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.caption(f"🦉 苏格拉底数学教练 v1.0.0")
with footer_col2:
    st.caption("🎯 培养独立思考能力")
with footer_col3:
    st.caption(f"🚀 启动于: {st.session_state.app_started}")

# 显示会话统计
if st.session_state.history:
    total_messages = sum(len(session["messages"]) for session in st.session_state.history.values())
    active_sessions = len([s for s in st.session_state.history.values() if s["problem_analyzed"]])
    
    st.caption(f"📊 统计: {active_sessions}个活跃会话, {total_messages}条消息")

# 清理旧会话
cleanup_old_sessions(max_sessions=20)