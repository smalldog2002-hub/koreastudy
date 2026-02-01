import streamlit as st
import google.generativeai as genai
import json
import os
import re
import random
import time
import textwrap
from gtts import gTTS
from io import BytesIO

# --- 页面配置 ---
st.set_page_config(page_title="语言 Master", page_icon="🌐", layout="centered", initial_sidebar_state="collapsed")

# --- 核心样式美化 (App级质感 + 布局修复) ---
st.markdown("""
    <style>
    /* 全局字体与背景 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&display=swap');
    
    .stApp {
        background-color: #f8fafc;
        font-family: 'Noto Sans SC', sans-serif;
    }

    /* 1. 容器适配：限制最大宽度，让手机端和电脑端保持一致的 App 比例 */
    div.block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        max-width: 600px; 
    }

    /* 2. 单词卡片容器 */
    .word-card-container {
        background: #ffffff;
        padding: 40px 20px;
        border-radius: 24px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.08);
        text-align: center;
        margin-bottom: 15px; /* 减少卡片与按钮的间距 */
        min-height: 320px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: relative;
        border: 1px solid #f1f5f9;
    }
    
    /* 3. 卡片内元素样式 */
    .unit-tag {
        position: absolute;
        top: 15px;
        right: 15px;
        background-color: #f1f5f9;
        color: #64748b;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 700;
    }
    .label-text { 
        color: #94a3b8; 
        font-weight: 800; 
        font-size: 12px; 
        letter-spacing: 2px; 
        text-transform: uppercase; 
        margin-bottom: 12px;
    }
    .word-display { 
        font-size: 3.5rem !important; 
        font-weight: 900 !important; 
        color: #1e293b; 
        margin: 10px 0; 
        line-height: 1.1; 
    }
    .meaning-display { 
        font-size: 2rem !important; 
        font-weight: 700 !important; 
        color: #4f46e5; 
        margin: 5px 0; 
    }
    
    /* 例句样式 - 修复显示问题 */
    .example-box {
        background-color: #f8fafc;
        padding: 16px;
        border-radius: 12px;
        margin-top: 20px;
        border-left: 4px solid #6366f1;
        text-align: left;
        width: 100%;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .example-origin {
        color: #334155;
        font-size: 15px;
        font-weight: 700;
        line-height: 1.4;
    }
    .example-trans {
        color: #64748b;
        font-size: 13px;
        font-weight: 400;
    }

    /* 4. 导航按钮布局 (关键修复：Flexbox 两端对齐) */
    
    /* 定位包含三个导航按钮的容器 (通常是页面上的第一个 horizontal block) */
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) {
        align-items: center;
        gap: 10px !important; /* 减小列间距 */
    }
    
    /* 左侧列：按钮左对齐 */
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-of-type(1) {
        display: flex;
        justify-content: flex-start; 
    }
    
    /* 中间列：按钮居中 */
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-of-type(2) {
        display: flex;
        justify-content: center;
    }
    
    /* 右侧列：按钮右对齐 */
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-of-type(3) {
        display: flex;
        justify-content: flex-end; 
    }

    /* 5. 按钮样式重塑 */
    .stButton > button {
        border-radius: 12px;
        font-weight: 700;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        transition: transform 0.1s;
        background-color: white;
        color: #475569;
        height: auto !important;
        padding: 10px 20px !important;
    }
    .stButton > button:active {
        transform: scale(0.95);
        box-shadow: none;
    }

    /* === 导航按钮专用样式 === */
    
    /* 左右箭头：方形、大图标 */
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-of-type(1) button, 
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-of-type(3) button {
        background-color: white;
        border: 1px solid #e2e8f0;
        color: #64748b;
        width: 52px !important;
        height: 52px !important;
        padding: 0 !important;
        border-radius: 16px !important;
        font-size: 20px !important;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* 中间翻转按钮：胶囊形、自适应宽度、去除多余装饰 */
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-of-type(2) button {
        background: #ffffff;
        color: #4f46e5 !important;
        border: 1px solid #e0e7ff !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.1) !important;
        padding: 12px 30px !important; /* 左右增加内边距 */
        font-size: 15px !important;
        border-radius: 99px !important;
        width: auto !important; /* 宽度自适应 */
        min-width: 120px;
    }
    
    /* 翻转按钮文字图标 */
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-of-type(2) button:before {
        content: "🔄 "; 
        font-size: 14px;
        margin-right: 4px;
    }

    /* === 底部功能按钮样式 (发音 & AI) === */
    /* 强制等高、灰色背景 */
    div[data-testid="stHorizontalBlock"]:nth-of-type(3) button {
        background-color: #f8fafc;
        color: #334155;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        height: 54px !important;
        font-size: 15px !important;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }

    /* 练习模式分数 */
    .quiz-score {
        font-size: 24px;
        font-weight: 800;
        color: #10b981;
        margin-bottom: 20px;
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
if 'audio_bytes' not in st.session_state: st.session_state.audio_bytes = None
# 练习模式状态
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
        st.session_state.audio_bytes = None
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
        return [
            {"word": f"Demo {i}", "meaning": f"示例单词 {i}", "example": "Test Sentence", "example_cn": "测试例句"} 
            for i in range(1, 45)
        ]
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
        selected_units = st.sidebar.multiselect(
            f"选择范围 (共 {len(all_units)} 单元):", 
            options=all_units, 
            default=default_selections
        )
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

if not words:
    st.stop()

if st.session_state.current_index >= len(words):
    st.session_state.current_index = 0
    
idx = st.session_state.current_index
current_word = words[idx]

# --- 功能函数 ---
def generate_audio(text, lang_code):
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

# --- 练习模式辅助函数 ---
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
    if is_correct:
        st.session_state.quiz_score += 10
    st.session_state.audio_bytes = None
    st.session_state.quiz_answered = True

def next_quiz():
    st.session_state.current_index = (st.session_state.current_index + 1) % len(words)
    st.session_state.quiz_answered = False
    st.session_state.quiz_options = [] 
    st.session_state.audio_bytes = None
    st.rerun()

# --- 主界面逻辑 ---
st.title("🌐 语言 Master")
st.caption(f"当前模式：{selected_lang} - {mode}")

if mode == "📖 卡片学习":
    progress = (idx + 1) / len(words)
    st.progress(progress)
    
    # 卡片显示逻辑
    unit_tag_html = ""
    if 'source_unit' in current_word:
        unit_tag_html = f'<div class="unit-tag">{current_word["source_unit"]}</div>'

    # 修复 HTML 渲染 bug：使用 textwrap.dedent 去除缩进
    if not st.session_state.flipped:
        card_html = textwrap.dedent(f"""
            <div class="word-card-container">
                {unit_tag_html}
                <p class="label-text">{LANG_CONFIG[selected_lang]["label"]}</p>
                <p class="word-display">{current_word["word"]}</p>
                <p style="color:#cbd5e1; font-size:12px; margin-top:20px; font-weight:700;">● ● ●</p>
            </div>
        """)
    else:
        example_html = ""
        example_text = current_word.get("example", "")
        if example_text and str(example_text).strip():
            example_html = textwrap.dedent(f"""
            <div class="example-box">
                <div class="example-origin">{example_text}</div>
                <div class="example-trans">{current_word.get("example_cn","")}</div>
            </div>
            """)
        
        card_html = textwrap.dedent(f"""
            <div class="word-card-container">
                {unit_tag_html}
                <p class="label-text">中文释义</p>
                <p class="meaning-display">{current_word["meaning"]}</p>
                {example_html}
            </div>
        """)
    
    st.markdown(card_html, unsafe_allow_html=True)

    # --- 导航按钮 (完美对齐) ---
    # 使用 columns 布局，CSS 会处理具体的对齐方式
    c1, c2, c3 = st.columns([1, 2, 1]) 
    with c1:
        if st.button("⬅️", help="上一个"):
            st.session_state.current_index = (idx - 1) % len(words)
            st.session_state.flipped = False
            st.session_state.ai_analysis = None
            st.session_state.audio_bytes = None
            st.rerun()
    with c2:
        # 去掉眼睛，使用胶囊样式
        btn_txt = "翻转卡片" if not st.session_state.flipped else "返回正面"
        if st.button(btn_txt, use_container_width=True):
            st.session_state.flipped = not st.session_state.flipped
            st.rerun()
    with c3:
        if st.button("➡️", help="下一个"):
            st.session_state.current_index = (idx + 1) % len(words)
            st.session_state.flipped = False
            st.session_state.ai_analysis = None
            st.session_state.audio_bytes = None
            st.rerun()

    st.divider()

    # --- 功能按钮 (发音 & AI) ---
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button(f"🔊 发音"): 
            with st.spinner("."):
                audio_data = generate_audio(current_word['word'], LANG_CONFIG[selected_lang]['code'])
                if audio_data:
                    st.session_state.audio_bytes = audio_data
                    st.rerun()
        if st.session_state.audio_bytes:
            st.audio(st.session_state.audio_bytes, format="audio/mp3")
    with col_b:
        if st.button("✨ AI 助学"):
            with st.spinner("..."):
                get_ai_help()

    if st.session_state.ai_analysis:
        res = st.session_state.ai_analysis
        st.success(f"💡 **词源**: {res.get('root', '暂无')}")
        st.info(f"🧠 **助记**: {res.get('mnemonic', '暂无')}")
        st.warning(f"💬 **场景**: {res.get('scenario', '暂无')}\n\n*{res.get('scenario_cn', '')}*")

else:
    # === 练习模式 ===
    is_options_valid = False
    if st.session_state.quiz_options:
        if any(opt['word'] == current_word['word'] for opt in st.session_state.quiz_options):
            is_options_valid = True
            
    if not st.session_state.quiz_answered and not is_options_valid:
        init_quiz_options()
    
    st.markdown(f'<div style="text-align:center;"><span class="quiz-score">🏆 {st.session_state.quiz_score}</span></div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="quiz-question">"{current_word["word"]}" 是什么意思？</div>', unsafe_allow_html=True)
    
    options = st.session_state.quiz_options
    
    if not st.session_state.quiz_answered:
        col1, col2 = st.columns(2)
        for i, option in enumerate(options):
            with (col1 if i % 2 == 0 else col2):
                if st.button(option["meaning"], key=f"quiz_opt_{i}", use_container_width=True):
                    check_answer(option)
                    st.rerun()
    else:
        if st.session_state.quiz_correct:
            st.success(f"✅ 正确！\n\n**{current_word['word']}** = **{current_word['meaning']}**")
            if not st.session_state.audio_bytes:
                 audio_data = generate_audio(current_word['word'], LANG_CONFIG[selected_lang]['code'])
                 if audio_data: st.session_state.audio_bytes = audio_data
            if st.session_state.audio_bytes:
                st.audio(st.session_state.audio_bytes, format="audio/mp3", start_time=0)
        else:
            st.error(f"❌ 错误。\n\n正确答案：**{current_word['meaning']}**")
        
        st.button("➡️ 下一题", type="primary", on_click=next_quiz, use_container_width=True)
