import streamlit as st
import google.generativeai as genai
import json
import os
import re
from gtts import gTTS
from io import BytesIO

# --- 页面配置 ---
st.set_page_config(page_title="语言 Master - AI 学习终端", page_icon="🌐", layout="centered")

# --- 样式美化 ---
st.markdown("""
    <style>
    /* 强制背景色，避免深色模式下看不清 */
    .word-card-container {
        background-color: #ffffff !important;
        padding: 40px 20px;
        border-radius: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        text-align: center;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
        min-height: 300px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .label-text { 
        color: #6366f1 !important; 
        font-weight: 800; 
        font-size: 14px; 
        letter-spacing: 2px; 
        text-transform: uppercase; 
        margin-bottom: 15px;
    }
    .word-display { 
        font-size: 60px !important; 
        font-weight: 800 !important; 
        color: #1e293b !important; 
        margin: 0; 
        line-height: 1.2; 
    }
    .meaning-display { 
        font-size: 36px !important; 
        font-weight: 700 !important; 
        color: #4f46e5 !important; 
        margin: 0; 
    }
    .example-box {
        background-color: #f8fafc !important;
        padding: 15px;
        border-radius: 12px;
        margin-top: 20px;
        border-left: 4px solid #6366f1;
        text-align: left;
        width: 100%;
        color: #334155 !important;
        font-size: 16px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 语言配置 (gTTS 使用简写代码) ---
LANG_CONFIG = {
    "韩语": {"code": "ko", "prompt": "资深的韩语老师", "label": "韩文", "file": "words_ko.json"},
    "泰语": {"code": "th", "prompt": "资深的泰语老师", "label": "泰文", "file": "words_th.json"},
    "日语": {"code": "ja", "prompt": "资深的日语老师", "label": "日语", "file": "words_ja.json"}
}

# --- 状态初始化 ---
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'flipped' not in st.session_state: st.session_state.flipped = False
if 'ai_analysis' not in st.session_state: st.session_state.ai_analysis = None
if 'audio_bytes' not in st.session_state: st.session_state.audio_bytes = None

# --- 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 设置")
    api_key = st.text_input("Gemini API Key", value="", type="password", help="在此输入 Key")
    selected_lang = st.selectbox("当前语言", options=list(LANG_CONFIG.keys()))
    
    # 切换语言时重置状态
    if 'prev_lang' not in st.session_state or st.session_state.prev_lang != selected_lang:
        st.session_state.current_index = 0
        st.session_state.flipped = False
        st.session_state.ai_analysis = None
        st.session_state.audio_bytes = None
        st.session_state.prev_lang = selected_lang

    st.divider()
    uploaded_file = st.file_uploader("上传单词库 (JSON)", type="json")

# --- 数据加载逻辑 ---
def load_words():
    # 1. 优先读取上传文件
    if uploaded_file:
        try:
            return json.load(uploaded_file)
        except:
            st.error("JSON 格式错误")
            
    # 2. 读取 GitHub 文件
    target_file = LANG_CONFIG[selected_lang]["file"]
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # 3. 默认兜底数据（防止空白）
    return [
        {"word": "Hello", "meaning": "你好 (默认数据)", "example": "请上传 JSON 文件", "example_cn": "Waiting for data..."},
        {"word": "World", "meaning": "世界 (默认数据)", "example": "Data not found", "example_cn": "未找到数据文件"}
    ]

words = load_words()
# 确保索引有效
current_word = words[st.session_state.current_index % len(words)]

# --- 功能函数 ---
def generate_audio(text, lang_code):
    """使用 gTTS 生成音频流"""
    try:
        tts = gTTS(text=text, lang=lang_code)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception as e:
        st.error(f"发音生成失败: {e}")
        return None

def get_ai_help():
    if not api_key:
        st.warning("请在侧边栏输入 API Key")
        return
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
        prompt = f"""
        作为{LANG_CONFIG[selected_lang]['prompt']}，请分析单词 "{current_word['word']}" (含义: {current_word['meaning']})。
        请以纯 JSON 格式返回，包含字段：root (词源), mnemonic (助记), scenario (短对话), scenario_cn (翻译)。
        """
        response = model.generate_content(prompt)
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            st.session_state.ai_analysis = json.loads(match.group())
    except Exception as e:
        st.error(f"AI 响应错误: {e}")

# --- 主界面 ---
st.title("🌐 语言 Master")
st.caption(f"模式：{selected_lang}智能辅导")

# 进度条
progress = (st.session_state.current_index + 1) / len(words)
st.progress(progress)
st.write(f"进度: {st.session_state.current_index + 1} / {len(words)}")

# --- 卡片区域 ---
card_html = ""
if not st.session_state.flipped:
    # 正面
    card_html = f"""
    <div class="word-card-container">
        <p class="label-text">{LANG_CONFIG[selected_lang]["label"]}单词</p>
        <p class="word-display">{current_word["word"]}</p>
        <p style="color:#94a3b8; font-size:12px; margin-top:30px;">👇 点击下方按钮查看解释</p>
    </div>
    """
else:
    # 反面
    example_html = ""
    if "example" in current_word:
        example_html = f"""
        <div class="example-box">
            <b>例句：</b><br>{current_word["example"]}<br>
            <span style="color:#64748b; font-size:0.9em;">{current_word.get("example_cn","")}</span>
        </div>
        """
    card_html = f"""
    <div class="word-card-container">
        <p class="label-text">中文释义</p>
        <p class="meaning-display">{current_word["meaning"]}</p>
        {example_html}
    </div>
    """

st.markdown(card_html, unsafe_allow_html=True)

# --- 按钮控制 ---
c1, c2, c3 = st.columns([1, 2, 1])
with c1:
    if st.button("⬅️ 上一个"):
        st.session_state.current_index = (st.session_state.current_index - 1) % len(words)
        st.session_state.flipped = False
        st.session_state.ai_analysis = None
        st.session_state.audio_bytes = None # 切换单词清空音频
        st.rerun()
with c2:
    btn_txt = "👁️ 显示正面" if st.session_state.flipped else "🔄 翻转查看解释"
    if st.button(btn_txt, type="primary"):
        st.session_state.flipped = not st.session_state.flipped
        st.rerun()
with c3:
    if st.button("下一个 ➡️"):
        st.session_state.current_index = (st.session_state.current_index + 1) % len(words)
        st.session_state.flipped = False
        st.session_state.ai_analysis = None
        st.session_state.audio_bytes = None
        st.rerun()

st.divider()

# --- 发音与 AI ---
col_a, col_b = st.columns(2)

with col_a:
    # 生成音频按钮
    if st.button(f"🔊 生成{selected_lang}发音"):
        with st.spinner("正在生成语音..."):
            audio_data = generate_audio(current_word['word'], LANG_CONFIG[selected_lang]['code'])
            if audio_data:
                st.session_state.audio_bytes = audio_data
                st.rerun()
    
    # 音频播放器
    if st.session_state.audio_bytes:
        st.audio(st.session_state.audio_bytes, format="audio/mp3")

with col_b:
    if st.button("✨ 获取 AI 深度助学"):
        with st.spinner("Gemini 正在思考..."):
            get_ai_help()

# AI 结果
if st.session_state.ai_analysis:
    res = st.session_state.ai_analysis
    st.success(f"💡 **词源**: {res.get('root', '暂无')}")
    st.info(f"🧠 **助记**: {res.get('mnemonic', '暂无')}")
    st.warning(f"💬 **场景**: {res.get('scenario', '暂无')}\n\n*{res.get('scenario_cn', '')}*")
