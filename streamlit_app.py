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
st.set_page_config(page_title="语言 Master - AI 学习终端", page_icon="🌐", layout="centered")

# --- 样式美化 (适配 iPhone 15 Pro Max & 华为 Pura) ---
st.markdown("""
    <style>
    /* 1. 移动端容器适配：减少顶部留白，增加可视区域 */
    div.block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* 2. 单词卡片容器：默认 Desktop 样式 */
    .word-card-container {
        background-color: #ffffff !important;
        padding: 40px 20px;
        border-radius: 24px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        text-align: center;
        border: 1px solid #f1f5f9;
        margin-bottom: 20px;
        min-height: 350px; /* 增加高度 */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: relative;
        transition: all 0.3s ease;
    }

    /* 3. 字体与元素基础样式 */
    .unit-tag {
        position: absolute;
        top: 15px;
        right: 15px;
        background-color: #f8fafc;
        color: #94a3b8;
        padding: 6px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 700;
        border: 1px solid #e2e8f0;
    }
    .label-text { 
        color: #6366f1 !important; 
        font-weight: 800; 
        font-size: 14px; 
        letter-spacing: 3px; 
        text-transform: uppercase; 
        margin-bottom: 20px;
        opacity: 0.8;
    }
    .word-display { 
        font-size: 64px !important; 
        font-weight: 900 !important; 
        color: #1e293b !important; 
        margin: 10px 0 20px 0; 
        line-height: 1.1; 
        word-break: keep-all; /* 防止韩语/日语被错误截断 */
    }
    .meaning-display { 
        font-size: 32px !important; 
        font-weight: 700 !important; 
        color: #4f46e5 !important; 
        margin: 0; 
        line-height: 1.4;
    }
    .example-box {
        background-color: #f8fafc !important;
        padding: 20px;
        border-radius: 16px;
        margin-top: 25px;
        border-left: 5px solid #6366f1;
        text-align: left;
        width: 100%;
        color: #334155 !important;
        font-size: 16px;
        line-height: 1.6;
    }
    
    /* 4. 按钮样式优化：更像原生 App 按钮 */
    .stButton>button {
        width: 100%;
        border-radius: 16px;
        height: 3.5em;
        font-weight: 700;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.1s;
    }
    .stButton>button:active {
        transform: scale(0.98);
    }

    /* 5. 练习模式分数与题目 */
    .quiz-score {
        font-size: 20px;
        font-weight: 800;
        color: #10b981;
        background: #ecfdf5;
        padding: 10px 20px;
        border-radius: 20px;
        display: inline-block;
        margin-bottom: 20px;
    }
    .quiz-question {
        font-size: 28px;
        font-weight: 800;
        text-align: center;
        margin: 10px 0 30px 0;
        color: #1e293b;
    }

    /* === 📱 移动端深度适配 (iPhone 15 Pro Max / Huawei Pura) === */
    @media only screen and (max-width: 600px) {
        /* 调整卡片容器 */
        .word-card-container {
            padding: 30px 15px;
            min-height: 280px; /* 稍微减小高度适应窄屏 */
            margin-bottom: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }
        
        /* 调整大字号，防止换行溢出 */
        .word-display { 
            font-size: 42px !important; /* 64px -> 42px */
        }
        .meaning-display { 
            font-size: 26px !important; /* 36px -> 26px */
        }
        
        /* 调整例句区域 */
        .example-box {
            padding: 15px;
            font-size: 14px;
            margin-top: 15px;
        }
        
        /* 调整按钮高度，更适合手指触摸 */
        .stButton>button {
            height: 4em; 
            font-size: 16px;
        }
        
        /* 调整 Quiz 模式 */
        .quiz-question {
            font-size: 22px;
            margin-bottom: 20px;
        }
        
        /* 隐藏或缩小次要元素 */
        .label-text {
            font-size: 12px;
            margin-bottom: 10px;
        }
        
        /* 优化顶部单元标签 */
        .unit-tag {
            top: 10px;
            right: 10px;
            padding: 4px 8px;
            font-size: 10px;
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
    """加载原始数据，可能是列表(旧版)或字典(新版-含单元)"""
    data = None
    
    # 1. 优先读取上传文件
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
        except:
            st.error("JSON 格式错误")
    
    # 2. 读取 GitHub 文件
    if data is None:
        target_file = LANG_CONFIG[selected_lang]["file"]
        if os.path.exists(target_file):
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
    
    # 3. 默认兜底数据
    if data is None:
        return [
            {"word": f"Demo {i}", "meaning": f"示例单词 {i}", "example": "Test", "example_cn": "测试"} 
            for i in range(1, 45)
        ]
    
    return data

def process_data_selection(raw_data):
    """处理数据并生成最终的学习列表"""
    final_list = []
    processed_data = {}

    # 情况 A: 数据是列表 -> 自动按 20 个切分
    if isinstance(raw_data, list):
        chunk_size = 20
        if len(raw_data) > 0:
            for i in range(0, len(raw_data), chunk_size):
                chunk = raw_data[i:i + chunk_size]
                unit_name = f"单元 {i//chunk_size + 1} ({i+1}-{min(i+chunk_size, len(raw_data))})"
                processed_data[unit_name] = chunk
        else:
            return []

    # 情况 B: 数据已经是字典 -> 直接使用
    elif isinstance(raw_data, dict):
        processed_data = raw_data
    
    else:
        st.error("数据结构无法识别")
        return []

    # 侧边栏选择逻辑
    if processed_data:
        st.sidebar.subheader("📚 单元选择")
        all_units = list(processed_data.keys())
        
        default_selections = [all_units[0]] if all_units else []
        
        selected_units = st.sidebar.multiselect(
            f"选择范围 (共 {len(all_units)} 单元):", 
            options=all_units, 
            default=default_selections,
            help="练习模式的题目和干扰项都将严格限制在你勾选的这些单元内"
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

# 执行加载和处理
raw_data_content = load_raw_data()
words = process_data_selection(raw_data_content)

# 如果没有单词，停止渲染
if not words:
    st.stop()

# 确保索引有效
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
    st.session_state.quiz_answered = True

def next_quiz():
    st.session_state.current_index = (st.session_state.current_index + 1) % len(words)
    st.session_state.quiz_answered = False
    st.session_state.quiz_options = [] 
    st.rerun()

# --- 主界面逻辑 ---
st.title("🌐 语言 Master")
st.caption(f"当前模式：{selected_lang} - {mode}")

if mode == "📖 卡片学习":
    progress = (idx + 1) / len(words)
    st.progress(progress)
    st.write(f"进度: {idx + 1} / {len(words)}")

    unit_tag_html = ""
    if 'source_unit' in current_word:
        unit_tag_html = f'<div class="unit-tag">{current_word["source_unit"]}</div>'

    card_html = ""
    if not st.session_state.flipped:
        card_html = f"""
        <div class="word-card-container">
            {unit_tag_html}
            <p class="label-text">{LANG_CONFIG[selected_lang]["label"]}单词</p>
            <p class="word-display">{current_word["word"]}</p>
            <p style="color:#94a3b8; font-size:12px; margin-top:30px;">👇 点击下方按钮查看解释</p>
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

    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("⬅️ 上一个"):
            st.session_state.current_index = (idx - 1) % len(words)
            st.session_state.flipped = False
            st.session_state.ai_analysis = None
            st.session_state.audio_bytes = None
            st.rerun()
    with c2:
        btn_txt = "👁️ 显示正面" if st.session_state.flipped else "🔄 翻转查看解释"
        if st.button(btn_txt, type="primary"):
            st.session_state.flipped = not st.session_state.flipped
            st.rerun()
    with c3:
        if st.button("下一个 ➡️"):
            st.session_state.current_index = (idx + 1) % len(words)
            st.session_state.flipped = False
            st.session_state.ai_analysis = None
            st.session_state.audio_bytes = None
            st.rerun()

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button(f"🔊 生成{selected_lang}发音"):
            with st.spinner("正在生成语音..."):
                audio_data = generate_audio(current_word['word'], LANG_CONFIG[selected_lang]['code'])
                if audio_data:
                    st.session_state.audio_bytes = audio_data
                    st.rerun()
        if st.session_state.audio_bytes:
            st.audio(st.session_state.audio_bytes, format="audio/mp3")
    with col_b:
        if st.button("✨ 获取 AI 深度助学"):
            with st.spinner("Gemini 正在思考..."):
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
    
    st.markdown(f'<div class="quiz-score" style="text-align:center;">🏆 当前积分: {st.session_state.quiz_score}</div>', unsafe_allow_html=True)
    
    if 'source_unit' in current_word:
        st.caption(f"当前题目来自：{current_word['source_unit']}")

    st.markdown(f'<div class="quiz-question">请选择 "{current_word["word"]}" 的正确含义：</div>', unsafe_allow_html=True)
    
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
            st.success(f"✅ 回答正确！\n\n**{current_word['word']}** = **{current_word['meaning']}**")
            if not st.session_state.audio_bytes:
                 audio_data = generate_audio(current_word['word'], LANG_CONFIG[selected_lang]['code'])
                 if audio_data: st.session_state.audio_bytes = audio_data
            if st.session_state.audio_bytes:
                st.audio(st.session_state.audio_bytes, format="audio/mp3", start_time=0)
        else:
            st.error(f"❌ 回答错误。\n\n正确答案是：**{current_word['meaning']}**")
        
        st.button("➡️ 继续下一题", type="primary", on_click=next_quiz, use_container_width=True)
