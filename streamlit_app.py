import streamlit as st
import google.generativeai as genai
import json
import os
import re
import random
import time
from gtts import gTTS
from io import BytesIO

# --- 页面配置 ---
st.set_page_config(page_title="语言 Master", page_icon="🦉", layout="centered", initial_sidebar_state="collapsed")

# --- 兼容性处理 ---
def rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

# --- 核心样式美化 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&display=swap');
    
    .stApp {
        background-color: #f8fafc;
        font-family: 'Noto Sans SC', sans-serif;
    }

    div.block-container {
        padding-top: 0.5rem;
        padding-bottom: 2rem;
        max-width: 600px;
    }

    /* === 单词卡片容器 === */
    .word-card-container {
        background: #ffffff;
        padding: 30px 15px;
        border-radius: 24px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.06);
        text-align: center;
        min-height: 300px; /* 固定高度，防止跳动 */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: relative;
        border: 1px solid #f1f5f9;
        margin-bottom: 5px; /* 紧贴下方按钮 */
    }
    
    /* 卡片内字体 */
    .unit-tag {
        position: absolute;
        top: 12px;
        right: 12px;
        background-color: #f1f5f9;
        color: #94a3b8;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 700;
    }
    .label-text { 
        color: #94a3b8; 
        font-weight: 800; 
        font-size: 11px; 
        letter-spacing: 2px; 
        text-transform: uppercase; 
        margin-bottom: 8px;
    }
    .word-display { 
        font-size: 3.2rem !important; 
        font-weight: 900 !important; 
        color: #1e293b; 
        margin: 5px 0; 
        line-height: 1.1; 
    }
    .meaning-display { 
        font-size: 1.8rem !important; 
        font-weight: 700 !important; 
        color: #4f46e5; 
        margin: 5px 0; 
    }
    
    /* 例句样式 */
    .example-box {
        background-color: #f8fafc;
        padding: 12px;
        border-radius: 12px;
        margin-top: 15px;
        border-left: 3px solid #6366f1;
        text-align: left;
        width: 100%;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .example-origin {
        color: #334155;
        font-size: 14px;
        font-weight: 700;
        line-height: 1.4;
    }
    .example-trans {
        color: #64748b;
        font-size: 12px;
        font-weight: 400;
    }

    /* === 导航按钮布局 (贴合卡片) === */
    
    div[data-testid="stHorizontalBlock"] {
        align-items: center;
        gap: 0px !important; /* 消除间距 */
    }
    
    .stButton > button {
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        transition: transform 0.1s;
        font-weight: 700;
    }
    .stButton > button:active {
        transform: scale(0.95);
        box-shadow: none;
    }

    /* 左箭头：靠右对齐，紧贴卡片 */
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-of-type(1) {
        display: flex; 
        justify-content: flex-end; /* 向右挤 */
        padding-right: 5px !important;
    }
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-of-type(1) button {
        background: transparent;
        border: 1px solid #f1f5f9;
        color: #94a3b8;
        border-radius: 50% !important;
        height: 48px !important;
        width: 48px !important;
        font-size: 20px !important;
        padding: 0 !important;
    }

    /* 中间翻转按钮 */
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-of-type(2) button {
        background: #ffffff;
        color: #4f46e5 !important;
        border: 1px solid #e0e7ff !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.1) !important;
        border-radius: 99px !important;
        height: 44px !important;
        font-size: 14px !important;
        width: auto !important;
        padding: 0 20px !important;
        min-width: 100px;
        margin-top: 10px;
    }

    /* 右箭头：靠左对齐，紧贴卡片 */
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-of-type(3) {
        display: flex; 
        justify-content: flex-start; /* 向左挤 */
        padding-left: 5px !important;
    }
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-of-type(3) button {
        background: transparent;
        border: 1px solid #f1f5f9;
        color: #94a3b8;
        border-radius: 50% !important;
        height: 48px !important;
        width: 48px !important;
        font-size: 20px !important;
        padding: 0 !important;
    }

    /* 底部功能按钮 */
    div[data-testid="stHorizontalBlock"]:nth-of-type(3) button {
        background-color: #f1f5f9;
        color: #334155;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        height: 48px !important;
        font-size: 14px !important;
        width: 100% !important;
        margin-top: 0px !important;
    }
    
    .quiz-score {
        font-size: 20px;
        font-weight: 800;
        color: #10b981;
        margin-bottom: 20px;
    }

    /* === 📱 移动端深度适配 === */
    @media only screen and (max-width: 600px) {
        div[data-testid="stHorizontalBlock"]:nth-of-type(1) {
            flex-wrap: nowrap !important;
            gap: 0px !important;
        }
        
        div[data-testid="stHorizontalBlock"]:nth-of-type(1) [data-testid="column"]:nth-of-type(1),
        div[data-testid="stHorizontalBlock"]:nth-of-type(1) [data-testid="column"]:nth-of-type(3) {
            flex: 0 0 50px !important; /* 箭头列宽 */
            min-width: 50px !important;
        }
        div[data-testid="stHorizontalBlock"]:nth-of-type(1) [data-testid="column"]:nth-of-type(2) {
            flex: 1 1 auto !important;
        }

        .word-display { font-size: 2.8rem !important; }
        .meaning-display { font-size: 1.8rem !important; }
        .word-card-container { 
            min-height: 260px; 
            padding: 20px 5px;
            margin-bottom: 5px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 语言配置 ---
LANG_CONFIG = {
    "韩语": {"code": "ko", "prompt": "资深的韩语老师", "label": "韩文", "file": "words_ko.json"},
    "泰语": {"code": "th", "prompt": "资深的泰语老师", "label": "泰文", "file": "words_th.json"},
    "日语": {"code": "ja", "prompt": "资深的日语老师", "label": "日语", "file": "words_ja.json"}
}

# --- 状态初始化 ---
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'flipped' not in st.session_state: st.session_state.flipped = False
if 'ai_analysis' not in st.session_state: st.session_state.ai_analysis = None
if 'audio_data' not in st.session_state: st.session_state.audio_data = None # 统一存放音频(bytes或URL)
if 'ai_audio_data' not in st.session_state: st.session_state.ai_audio_data = None
if 'quiz_score' not in st.session_state: st.session_state.quiz_score = 0
if 'quiz_answered' not in st.session_state: st.session_state.quiz_answered = False
if 'quiz_correct' not in st.session_state: st.session_state.quiz_correct = False
if 'quiz_options' not in st.session_state: st.session_state.quiz_options = []

# --- 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 设置")
    api_key = st.text_input("Gemini API Key", value="", type="password", help="在此输入 Key")
    selected_lang = st.selectbox("当前语言", options=list(LANG_CONFIG.keys()))
    
    if 'prev_lang' not in st.session_state or st.session_state.prev_lang != selected_lang:
        st.session_state.current_index = 0
        st.session_state.flipped = False
        st.session_state.ai_analysis = None
        st.session_state.audio_data = None
        st.session_state.ai_audio_data = None
        st.session_state.quiz_score = 0
        st.session_state.quiz_answered = False
        st.session_state.quiz_options = []
        st.session_state.prev_lang = selected_lang

    st.divider()
    mode = st.radio("选择模式", ["📖 卡片学习", "⚔️ 强化练习"])
    st.divider()
    uploaded_file = st.file_uploader("上传单词库 (JSON)", type="json")

# --- 数据加载逻辑 ---
def load_raw_data():
    data = None
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
        except:
            st.error("JSON 格式错误")
    if data is None:
        target_file = LANG_CONFIG[selected_lang]["file"]
        if os.path.exists(target_file):
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
    if data is None:
        return [{"word": f"Demo {i}", "meaning": f"示例 {i}", "example": "Test", "example_cn": "测试"} for i in range(1, 45)]
    return data

def process_data_selection(raw_data):
    final_list = []
    processed_data = {}

    if isinstance(raw_data, list):
        chunk_size = 20
        if len(raw_data) > 0:
            for i in range(0, len(raw_data), chunk_size):
                chunk = raw_data[i:i + chunk_size]
                unit_name = f"单元 {i//chunk_size + 1} ({i+1}-{min(i+chunk_size, len(raw_data))})"
                processed_data[unit_name] = chunk
        else:
            return []
    elif isinstance(raw_data, dict):
        processed_data = raw_data
    else:
        st.error("数据结构无法识别")
        return []

    if processed_data:
        st.sidebar.subheader("📚 单元选择")
        all_units = list(processed_data.keys())
        default_selections = [all_units[0]] if all_units else []
        selected_units = st.sidebar.multiselect(f"选择范围 (共 {len(all_units)} 单元):", options=all_units, default=default_selections)
        if not selected_units:
            st.warning("⚠️ 请至少勾选一个单元！")
            return []
        for unit in selected_units:
            for word_item in processed_data[unit]:
                new_item = word_item.copy()
                new_item['source_unit'] = unit
                final_list.append(new_item)
    return final_list

raw_data_content = load_raw_data()
words = process_data_selection(raw_data_content)

if not words: st.stop()
if st.session_state.current_index >= len(words): st.session_state.current_index = 0
    
idx = st.session_state.current_index
current_word = words[idx]

# --- 功能函数 (修复版：支持 URL 回退) ---
def generate_audio_data(text, lang_code):
    """
    生成音频数据。
    1. 尝试 gTTS (服务器生成)
    2. 如果失败，返回 Google TTS 的 URL (客户端直接播放，解决 iOS/IP 限制问题)
    """
    if not text or not str(text).strip(): return None
    
    # 尝试 1: gTTS
    try:
        tts = gTTS(text=str(text), lang=lang_code)
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp.getvalue() # 返回二进制
    except Exception:
        # 尝试 2: 返回 URL (Streamlit st.audio 支持直接播放 URL)
        # 注意：client=tw-ob 是 Google 的公开接口
        return f"https://translate.google.com/translate_tts?ie=UTF-8&q={text}&tl={lang_code}&client=tw-ob"

def get_ai_help():
    if not api_key:
        st.warning("请在侧边栏输入 API Key")
        return
    try:
        st.session_state.ai_audio_data = None
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

# --- 练习模式辅助 ---
def init_quiz_options():
    st.session_state.quiz_options = []
    options = [current_word]
    other_words = [w for w in words if w['word'] != current_word['word']]
    count_needed = 3
    if len(other_words) < count_needed:
        if len(other_words) == 0:
             distractors = [{"word": "N/A", "meaning": "无干扰项"}] * 3
        else:
             distractors = (other_words * (count_needed // len(other_words) + 1))[:count_needed]
    else:
        distractors = random.sample(other_words, count_needed)
    options.extend(distractors)
    random.shuffle(options)
    st.session_state.quiz_options = options

def check_answer(selected_option):
    is_correct = selected_option['word'] == current_word['word']
    st.session_state.quiz_correct = is_correct
    if is_correct: st.session_state.quiz_score += 10
    st.session_state.audio_data = None
    st.session_state.quiz_answered = True

def next_quiz():
    st.session_state.current_index = (st.session_state.current_index + 1) % len(words)
    st.session_state.quiz_answered = False
    st.session_state.quiz_options = [] 
    st.session_state.audio_data = None
    rerun()

# --- 主界面 ---
# 隐藏标题

if mode == "📖 卡片学习":
    progress = (idx + 1) / len(words)
    st.progress(progress)
    
    # 顶部容器：[左箭头] [  单词卡  ] [右箭头]
    c_left, c_card, c_right = st.columns([1, 8, 1], gap="small") 
    
    with c_left:
        # 左侧列靠右对齐，紧贴卡片
        st.markdown('<div class="nav-btn-container">', unsafe_allow_html=True)
        if st.button("❮", help="上一个"):
            st.session_state.current_index = (idx - 1) % len(words)
            st.session_state.flipped = False
            st.session_state.ai_analysis = None
            st.session_state.audio_data = None
            st.session_state.ai_audio_data = None
            rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c_card:
        unit_tag_html = ""
        if 'source_unit' in current_word:
            unit_tag_html = f'<div class="unit-tag">{current_word["source_unit"]}</div>'

        if not st.session_state.flipped:
            card_html = f"""<div class="word-card-container">
    {unit_tag_html}
    <p class="label-text">{LANG_CONFIG[selected_lang]["label"]}</p>
    <p class="word-display">{current_word["word"]}</p>
    <p style="color:#cbd5e1; font-size:12px; margin-top:20px;">●</p>
</div>"""
        else:
            example_html = ""
            example_text = current_word.get("example", "")
            if example_text and str(example_text).strip():
                example_html = f"""<div class="example-box">
    <div class="example-origin">{example_text}</div>
    <div class="example-trans">{current_word.get("example_cn","")}</div>
</div>"""
            card_html = f"""<div class="word-card-container">
    {unit_tag_html}
    <p class="label-text">中文释义</p>
    <p class="meaning-display">{current_word["meaning"]}</p>
    {example_html}
</div>"""
        st.markdown(card_html, unsafe_allow_html=True)
        
        st.markdown('<div class="flip-btn-container">', unsafe_allow_html=True)
        btn_txt = "🔄 翻转卡片" if not st.session_state.flipped else "↩️ 返回正面"
        if st.button(btn_txt, use_container_width=True):
            st.session_state.flipped = not st.session_state.flipped
            rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c_right:
        # 右侧列靠左对齐，紧贴卡片
        st.markdown('<div class="nav-btn-container">', unsafe_allow_html=True)
        if st.button("❯", help="下一个"):
            st.session_state.current_index = (idx + 1) % len(words)
            st.session_state.flipped = False
            st.session_state.ai_analysis = None
            st.session_state.audio_data = None
            st.session_state.ai_audio_data = None
            rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("") 
    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="func-btn-container">', unsafe_allow_html=True)
        if st.button(f"🔊 发音", use_container_width=True): 
            with st.spinner("."):
                # 获取音频（bytes 或 URL）
                data = generate_audio_data(current_word['word'], LANG_CONFIG[selected_lang]['code'])
                if data:
                    st.session_state.audio_data = data
                    rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.session_state.audio_data:
            # 兼容 bytes 和 URL
            # format="audio/mpeg" 对 iOS 最友好
            st.audio(st.session_state.audio_data, format="audio/mpeg")
    
    with col_b:
        st.markdown('<div class="func-btn-container">', unsafe_allow_html=True)
        if st.button("✨ AI 助学", use_container_width=True):
            with st.spinner("..."):
                get_ai_help()
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.ai_analysis:
        res = st.session_state.ai_analysis
        st.success(f"💡 **词源**: {res.get('root', '暂无')}")
        st.info(f"🧠 **助记**: {res.get('mnemonic', '暂无')}")
        st.warning(f"💬 **场景**: {res.get('scenario', '暂无')}\n\n*{res.get('scenario_cn', '')}*")
        
        st.markdown('<div class="ai-audio-btn">', unsafe_allow_html=True)
        if st.button("🔊 播放对话", key="ai_play"):
            with st.spinner("..."):
                scenario_text = res.get('scenario', '')
                if scenario_text:
                    st.session_state.ai_audio_data = generate_audio_data(scenario_text, LANG_CONFIG[selected_lang]['code'])
                    rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.session_state.ai_audio_data:
            st.audio(st.session_state.ai_audio_data, format="audio/mpeg")

else:
    # === 练习模式 ===
    is_options_valid = False
    if st.session_state.quiz_options:
        if any(opt['word'] == current_word['word'] for opt in st.session_state.quiz_options):
            is_options_valid = True
            
    if not st.session_state.quiz_answered and not is_options_valid:
        init_quiz_options()
    
    st.markdown(f'<div style="text-align:center; font-size:20px; font-weight:800; color:#10b981; margin-bottom:10px;">🏆 {st.session_state.quiz_score}</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center; font-size:24px; font-weight:800; color:#334155; margin:10px 0 30px 0;">"{current_word["word"]}" 是什么意思？</div>', unsafe_allow_html=True)
    
    options = st.session_state.quiz_options
    
    if not st.session_state.quiz_answered:
        col1, col2 = st.columns(2)
        for i, option in enumerate(options):
            with (col1 if i % 2 == 0 else col2):
                if st.button(option["meaning"], key=f"quiz_opt_{i}", use_container_width=True):
                    check_answer(option)
                    rerun()
    else:
        if st.session_state.quiz_correct:
            st.success(f"✅ 正确！\n\n**{current_word['word']}** = **{current_word['meaning']}**")
            if not st.session_state.audio_data:
                 data = generate_audio_data(current_word['word'], LANG_CONFIG[selected_lang]['code'])
                 if data: st.session_state.audio_data = data
            if st.session_state.audio_data:
                st.audio(st.session_state.audio_data, format="audio/mpeg", start_time=0)
        else:
            st.error(f"❌ 错误。\n\n正确答案：**{current_word['meaning']}**")
        
        st.button("➡️ 下一题", type="primary", on_click=next_quiz, use_container_width=True)
