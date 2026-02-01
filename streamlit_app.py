import streamlit as st
import google.generativeai as genai
import json
import os
import re

# --- 页面配置 ---
st.set_page_config(page_title="语言 Master - AI 学习终端", page_icon="🌐", layout="centered")

# --- 样式美化 ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        font-weight: bold;
    }
    .word-card {
        background-color: white;
        padding: 40px;
        border-radius: 25px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        text-align: center;
        border: 1px solid #eee;
        margin-bottom: 20px;
    }
    .word-text { font-size: 64px; font-weight: bold; color: #1e293b; margin-bottom: 10px; }
    .meaning-text { font-size: 40px; font-weight: bold; color: #4f46e5; }
    .example-box {
        background-color: #f1f5f9;
        padding: 15px;
        border-radius: 15px;
        margin-top: 20px;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 语言配置 ---
LANG_CONFIG = {
    "韩语": {"code": "ko-KR", "prompt": "资深的韩语老师", "label": "韩文", "file": "words_ko.json"},
    "泰语": {"code": "th-TH", "prompt": "资深的泰语老师", "label": "泰文", "file": "words_th.json"},
    "日语": {"code": "ja-JP", "prompt": "资深的日语老师", "label": "日语", "file": "words_ja.json"}
}

# --- 侧边栏：设置与导入 ---
with st.sidebar:
    st.title("⚙️ 设置中心")
    api_key = st.text_input("Gemini API Key", value="AIzaSyDjWGjbHOvCKJ9IZQ-P6F0MHyiYVtH4w9I", type="password")
    selected_lang = st.selectbox("学习目标语言", options=list(LANG_CONFIG.keys()))
    
    st.divider()
    st.subheader("数据管理")
    uploaded_file = st.file_uploader("手动覆盖单词库 (JSON)", type="json")

# --- 核心数据加载逻辑 ---
def load_data():
    # 1. 如果用户手动上传了文件，优先使用上传的
    if uploaded_file is not None:
        try:
            return json.load(uploaded_file)
        except:
            st.error("上传的 JSON 格式有误")
    
    # 2. 否则，根据选定的语言自动读取 GitHub 仓库里的文件
    target_file = LANG_CONFIG[selected_lang]["file"]
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # 3. 如果都没有，返回默认演示数据
    return [
        {"word": "Hello", "meaning": "你好 (示例)", "example": "Hello world", "example_cn": "你好，世界"}
    ]

# 每次切换语言或上传文件时，重新加载数据
words_data = load_data()

# 初始化/重置索引逻辑
if 'prev_lang' not in st.session_state or st.session_state.prev_lang != selected_lang:
    st.session_state.current_index = 0
    st.session_state.flipped = False
    st.session_state.ai_analysis = None
    st.session_state.prev_lang = selected_lang

if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'flipped' not in st.session_state:
    st.session_state.flipped = False
if 'ai_analysis' not in st.session_state:
    st.session_state.ai_analysis = None

# --- 核心逻辑函数 ---
def speak(text, lang_code):
    js_code = f"""
        var msg = new SpeechSynthesisUtterance('{text}');
        msg.lang = '{lang_code}';
        window.speechSynthesis.speak(msg);
    """
    st.components.v1.html(f"<script>{js_code}</script>", height=0)

def get_ai_analysis(word_data, lang_info):
    if not api_key:
        st.error("请输入 API Key")
        return None
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
    
    prompt = f"""
    作为一个{lang_info['prompt']}，请为单词 "{word_data['word']}" (含义: {word_data['meaning']}) 提供深度学习分析。
    请以纯 JSON 格式返回，包含字段：root (词源分析), mnemonic (助记口诀), scenario (对话场景), scenario_cn (翻译)。
    """
    
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        st.error(f"AI 解析失败: {e}")
    return None

# --- 主界面 ---
st.title("🌐 语言 Master")
st.caption(f"当前模式：{selected_lang}智能辅导")

lang_info = LANG_CONFIG[selected_lang]
# 确保索引不越界
idx = st.session_state.current_index % len(words_data)
current_word = words_data[idx]

# 进度条
progress = (idx + 1) / len(words_data)
st.progress(progress)
st.write(f"进度：{idx + 1} / {len(words_data)}")

# 单词卡片展示
with st.container():
    st.markdown('<div class="word-card">', unsafe_allow_html=True)
    
    if not st.session_state.flipped:
        st.markdown(f'<p style="color:#6366f1; font-weight:bold; letter-spacing:2px;">{lang_info["label"]}</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="word-text">{current_word["word"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<p style="color:#6366f1; font-weight:bold; letter-spacing:2px;">中文释义</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="meaning-text">{current_word["meaning"]}</div>', unsafe_allow_html=True)
        if "example" in current_word:
            st.markdown(f'<div class="example-box">"{current_word["example"]}"<br><small>{current_word.get("example_cn", "")}</small></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# 交互按钮
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("上一个"):
        st.session_state.current_index = (idx - 1) % len(words_data)
        st.session_state.flipped = False
        st.session_state.ai_analysis = None
        st.rerun()

with col2:
    if st.button("🔄 翻转卡片"):
        st.session_state.flipped = not st.session_state.flipped
        st.rerun()

with col3:
    if st.button("下一个"):
        st.session_state.current_index = (idx + 1) % len(words_data)
        st.session_state.flipped = False
        st.session_state.ai_analysis = None
        st.rerun()

# 发音与 AI 解析
st.divider()
c1, c2 = st.columns(2)
with c1:
    if st.button(f"🔊 播放{selected_lang}发音"):
        speak(current_word['word'], lang_info['code'])

with c2:
    if st.button("✨ 获取 AI 助学解析"):
        with st.spinner("Gemini 正在深度分析中..."):
            st.session_state.ai_analysis = get_ai_analysis(current_word, lang_info)

# 展示 AI 解析结果
if st.session_state.ai_analysis:
    res = st.session_state.ai_analysis
    st.info("💡 **词源/构成分析**")
    st.write(res.get('root', '暂无分析'))
    
    st.success("🧠 **趣味助记**")
    st.write(f"*{res.get('mnemonic', '暂无助记')}*")
    
    st.warning("💬 **场景模拟**")
    st.write(f"**{res.get('scenario', '')}**")
    st.caption(res.get('scenario_cn', ''))

# 底部词库列表
with st.expander("查看当前词库列表"):
    st.table(words_data)