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
st.set_page_config(page_title="语言 Master", page_icon="🌐", layout="centered", initial_sidebar_state="collapsed")

# --- 核心样式美化 (App级质感) ---
st.markdown("""
    <style>
    /* 全局字体与背景优化 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&display=swap');
    
    .stApp {
        background-color: #f8fafc;
        font-family: 'Noto Sans SC', sans-serif;
    }

    /* 1. 移动端容器适配：去除多余留白 */
    div.block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        padding-left: 0.75rem;
        padding-right: 0.75rem;
        max-width: 700px; /* 限制最大宽度，类似 App 视图 */
    }

    /* 2. 单词卡片容器：悬浮感与柔和阴影 */
    .word-card-container {
        background: #ffffff;
        padding: 40px 20px;
        border-radius: 28px;
        box-shadow: 0 20px 40px -12px rgba(0,0,0,0.08), 0 2px 10px -5px rgba(0,0,0,0.03);
        text-align: center;
        border: 1px solid rgba(255,255,255,0.8);
        margin-bottom: 24px;
        min-height: 320px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: relative;
        transition: transform 0.2s ease;
    }
    
    /* 3. 字体美化 */
    .unit-tag {
        position: absolute;
        top: 16px;
        right: 16px;
        background-color: #f1f5f9;
        color: #64748b;
        padding: 6px 12px;
        border-radius: 99px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .label-text { 
        color: #94a3b8 !important; 
        font-weight: 800; 
        font-size: 12px; 
        letter-spacing: 2px; 
        text-transform: uppercase; 
        margin-bottom: 16px;
    }
    .word-display { 
        font-size: 3.5rem !important; 
        font-weight: 900 !important; 
        color: #1e293b !important; 
        margin: 8px 0 16px 0; 
        line-height: 1.1; 
        word-break: keep-all; 
    }
    .meaning-display { 
        font-size: 2rem !important; 
        font-weight: 700 !important; 
        color: #4f46e5 !important; 
        margin: 0; 
        line-height: 1.3;
    }
    .example-box {
        background-color: #f8fafc !important;
        padding: 18px;
        border-radius: 16px;
        margin-top: 24px;
        border-left: 4px solid #6366f1;
        text-align: left;
        width: 100%;
        color: #475569 !important;
        font-size: 15px;
        line-height: 1.6;
    }
    
    /* 4. 按钮样式重塑：更圆润、更有质感 */
    .stButton > button {
        width: 100%;
        border-radius: 16px;
        height: 3.2rem;
        font-weight: 700;
        border: 1px solid rgba(0,0,0,0.02);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: all 0.15s ease;
        background-color: white;
    }
    .stButton > button:active {
        transform: scale(0.96);
        box-shadow: none;
    }
    /* 主按钮样式 */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white;
        border: none;
        box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.3);
    }

    /* 5. 练习模式分数 */
    .quiz-score {
        font-size: 18px;
        font-weight: 800;
        color: #059669;
        background: #ecfdf5;
        padding: 8px 20px;
        border-radius: 99px;
        display: inline-block;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    /* === 📱 移动端深度适配 (iPhone/Pura 优化) === */
    @media only screen and (max-width: 600px) {
        /* 强制按钮行紧凑排列 */
        div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 0.4rem !important; /* 极小的间距 */
            align-items: center !important;
        }
        
        /* 列宽自动分配，不允许挤压 */
        div[data-testid="column"] {
            flex: 1 1 0 !important;
            min-width: 0 !important;
            padding: 0 !important; /* 去除列内边距 */
        }

        /* 按钮文字与大小微调 */
        .stButton > button {
            height: 3.5rem !important; /* 增加触摸高度 */
            padding: 0 4px !important;
            font-size: 14px !important;
            white-space: nowrap !important; /* 防止文字换行 */
            overflow: hidden;
        }
        
        /* 卡片文字适配 */
        .word-card-container {
            min-height: 280px;
            padding: 30px 15px;
        }
        .word-display { font-size: 2.8rem !important; }
        .meaning-display { font-size: 1.6rem !important; }
        
        /* 隐藏不重要的标签，节省空间 */
        .label-text { margin-bottom: 8px; font-size: 10px; }
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
    
    # 切换语言时重置状态
    if 'prev_lang' not in st.session_state or st.session_state.prev_lang != selected_lang:
        st.session_state.current_index = 0
        st.session_state.flipped = False
        st.session_state.ai_analysis = None
        st.session_state.audio_bytes = None
        st.session_state.quiz_score = 0
        st.session_state.quiz_answered = False
        st.session_state.quiz_options = [] # 清空选项
        st.session_state.prev_lang = selected_lang

    st.divider()
    
    # 模式选择
    mode = st.radio("选择模式", ["📖 卡片学习", "⚔️ 强化练习"])
    
    st.divider()
    uploaded_file = st.file_uploader("上传单词库 (JSON)", type="json")

# --- 数据加载逻辑 (自动分单元) ---
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
            {"word": f"Demo {i}", "meaning": f"示例单词 {i}", "example": "Test", "example_cn": "测试"} 
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
    
    # 顶部状态栏
    col_status_1, col_status_2 = st.columns([3, 1])
    with col_status_1:
        st.write(f"**进度**: {idx + 1} / {len(words)}")
    with col_status_2:
        if 'source_unit' in current_word:
            # 简化显示，不用 div
            st.caption(f"📍{current_word['source_unit'].split(' ')[0]}")

    # 卡片区域
    unit_tag_html = ""
    if 'source_unit' in current_word:
        unit_tag_html = f'<div class="unit-tag">{current_word["source_unit"]}</div>'

    card_html = ""
    if not st.session_state.flipped:
        card_html = f"""
        <div class="word-card-container">
            {unit_tag_html}
            <p class="label-text">{LANG_CONFIG[selected_lang]["label"]}</p>
            <p class="word-display">{current_word["word"]}</p>
            <p style="color:#cbd5e1; font-size:12px; margin-top:20px; font-weight:700;">● ● ●</p>
        </div>
        """
    else:
        example_html = ""
        example_text = current_word.get("example", "")
        if example_text and str(example_text).strip():
            example_html = f"""
            <div class="example-box">
                <b>例句：</b><br>{example_text}<br>
                <span style="color:#64748b; font-size:0.9em;">{current_word.get("example_cn","")}</span>
            </div>
            """
        card_html = f"""
        <div class="word-card-container">
            {unit_tag_html}
            <p class="label-text">中文释义</p>
            <p class="meaning-display">{current_word["meaning"]}</p>
            {example_html}
        </div>
        """
    st.markdown(card_html, unsafe_allow_html=True)

    # --- 核心导航按钮 (移动端强制紧凑单行) ---
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c1:
        if st.button("⬅️", help="上一个"):
            st.session_state.current_index = (idx - 1) % len(words)
            st.session_state.flipped = False
            st.session_state.ai_analysis = None
            st.session_state.audio_bytes = None
            st.rerun()
    with c2:
        btn_txt = "👁️ 查看" if st.session_state.flipped else "🔄 翻转"
        if st.button(btn_txt, type="primary"):
            st.session_state.flipped = not st.session_state.flipped
            st.rerun()
    with c3:
        if st.button("➡️", help="下一个"):
            st.session_state.current_index = (idx + 1) % len(words)
            st.session_state.flipped = False
            st.session_state.ai_analysis = None
            st.session_state.audio_bytes = None
            st.rerun()

    # --- 功能按钮 (移动端强制紧凑单行) ---
    st.write("") # 增加一点垂直间距
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
