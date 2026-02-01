import streamlit as st
import google.generativeai as genai
import json
import os
import re
import time

# --- 页面配置 ---
st.set_page_config(page_title="语言 Master - AI 学习终端", page_icon="🌐", layout="centered")

# --- 样式美化 ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; font-weight: bold; }
    .word-card {
        background-color: white;
        padding: 50px 20px;
        border-radius: 24px;
        box-shadow: 0 10px 30px rgba(79, 70, 229, 0.1);
        text-align: center;
        border: 2px solid #f1f5f9;
        margin-bottom: 20px;
        min-height: 300px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .label-text { color: #6366f1; font-weight: 900; font-size: 14px; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 16px; }
    .word-display { font-size: 64px; font-weight: 800; color: #1e293b; margin: 0; line-height: 1.2; }
    .meaning-display { font-size: 40px; font-weight: 700; color: #4f46e5; margin: 0; }
    .example-box {
        background-color: #f8fafc;
        padding: 20px;
        border-radius: 16px;
        margin-top: 24px;
        border-left: 4px solid #6366f1;
        text-align: left;
        width: 100%;
        color: #334155;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 语言配置 ---
LANG_CONFIG = {
    "韩语": {"code": "ko-KR", "prompt": "资深的韩语老师", "label": "韩文", "file": "words_ko.json"},
    "泰语": {"code": "th-TH", "prompt": "资深的泰语老师", "label": "泰文", "file": "words_th.json"},
    "日语": {"code": "ja-JP", "prompt": "资深的日语老师", "label": "日语", "file": "words_ja.json"}
}

# --- 状态初始化 ---
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'flipped' not in st.session_state: st.session_state.flipped = False
if 'ai_analysis' not in st.session_state: st.session_state.ai_analysis = None
if 'words' not in st.session_state: st.session_state.words = []

# --- 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 设置")
    # 安全性：API Key 仅存在内存中
    api_key = st.text_input("Gemini API Key", value="", type="password", help="在此输入 Key，不会被保存到代码中")
    selected_lang = st.selectbox("当前语言", options=list(LANG_CONFIG.keys()))
    
    st.divider()
    uploaded_file = st.file_uploader("上传自定义 JSON", type="json")

# --- 数据加载逻辑 ---
def load_words():
    # 1. 优先读取上传文件
    if uploaded_file:
        try:
            return json.load(uploaded_file)
        except:
            st.error("JSON 文件格式错误")
            
    # 2. 其次读取 GitHub 仓库文件
    target_file = LANG_CONFIG[selected_lang]["file"]
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # 3. 默认演示数据
    return [{"word": "等待数据", "meaning": "请上传 JSON", "example": "请确保 words.json 在目录下", "example_cn": ""}]

# 加载数据
words = load_words()
# 防止索引越界
current_word = words[st.session_state.current_index % len(words)]

# --- 功能函数 ---
def speak(text, lang_code):
    """通过注入 JS 调用浏览器原生 TTS"""
    js = f"""
    <script>
        var utterance = new SpeechSynthesisUtterance("{text}");
        utterance.lang = "{lang_code}";
        window.speechSynthesis.speak(utterance);
    </script>
    """
    st.components.v1.html(js, height=0)

def get_ai_help():
    if not api_key:
        st.warning("请在左侧侧边栏输入 API Key")
        return
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
        prompt = f"""
        作为{LANG_CONFIG[selected_lang]['prompt']}，请分析单词 "{current_word['word']}" (含义: {current_word['meaning']})。
        请以纯 JSON 格式返回，包含字段：root (词源), mnemonic (助记), scenario (短对话), scenario_cn (翻译)。
        """
        
        response = model.generate_content(prompt)
        # 提取 JSON 块
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            st.session_state.ai_analysis = json.loads(match.group())
        else:
            st.error("AI 返回格式异常，请重试")
    except Exception as e:
        st.error(f"AI 响应错误: {e}")

# --- 主界面 UI ---
st.title("🌐 语言 Master")
st.caption(f"模式：{selected_lang}智能辅导")

# 进度
progress = (st.session_state.current_index + 1) / len(words)
st.progress(progress)
st.write(f"进度: {st.session_state.current_index + 1} / {len(words)}")

# 单词卡片区
with st.container():
    st.markdown('<div class="word-card">', unsafe_allow_html=True)
    if not st.session_state.flipped:
        # 正面
        st.markdown(f'<p class="label-text">{LANG_CONFIG[selected_lang]["label"]}单词</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="word-display">{current_word["word"]}</p>', unsafe_allow_html=True)
        st.markdown('<p style="color:#94a3b8; font-size:12px; margin-top:30px;">👇 点击下方按钮查看解释</p>', unsafe_allow_html=True)
    else:
        # 反面 (逻辑切换，绝无镜像问题)
        st.markdown(f'<p class="label-text">中文释义</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="meaning-display">{current_word["meaning"]}</p>', unsafe_allow_html=True)
        if "example" in current_word:
            st.markdown(f'<div class="example-box"><b>例句：</b><br>{current_word["example"]}<br><span style="color:#64748b; font-size:0.9em;">{current_word.get("example_cn","")}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 控制按钮
c1, c2, c3 = st.columns([1, 2, 1])
with c1:
    if st.button("⬅️ 上一个"):
        st.session_state.current_index = (st.session_state.current_index - 1) % len(words)
        st.session_state.flipped = False
        st.session_state.ai_analysis = None
        st.rerun()
with c2:
    btn_label = "👁️ 显示正面" if st.session_state.flipped else "🔄 翻转查看解释"
    if st.button(btn_label):
        st.session_state.flipped = not st.session_state.flipped
        st.rerun()
with c3:
    if st.button("下一个 ➡️"):
        st.session_state.current_index = (st.session_state.current_index + 1) % len(words)
        st.session_state.flipped = False
        st.session_state.ai_analysis = None
        st.rerun()

st.divider()

# 发音与 AI
col_a, col_b = st.columns(2)
with col_a:
    if st.button(f"🔊 播放{selected_lang}发音"):
        speak(current_word['word'], LANG_CONFIG[selected_lang]['code'])
with col_b:
    if st.button("✨ 获取 AI 深度助学"):
        with st.spinner("Gemini 正在分析..."):
            get_ai_help()

# AI 结果展示
if st.session_state.ai_analysis:
    res = st.session_state.ai_analysis
    st.success(f"💡 **词源分析**: {res.get('root', '暂无')}")
    st.info(f"🧠 **助记口诀**: {res.get('mnemonic', '暂无')}")
    st.warning(f"💬 **场景模拟**: {res.get('scenario', '暂无')}\n\n*{res.get('scenario_cn', '')}*")
