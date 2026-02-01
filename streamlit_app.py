import React, { useState, useEffect, useMemo } from 'react';
import { 
  BookOpen, 
  RotateCw, 
  Volume2, 
  ChevronLeft, 
  ChevronRight, 
  LayoutGrid, 
  CheckCircle2, 
  Upload,
  Trophy,
  BrainCircuit,
  Sparkles,
  Loader2,
  MessageSquareQuote,
  Lightbulb,
  Globe,
  Settings,
  X,
  Key
} from 'lucide-react';

// 语言配置常量
const LANGUAGE_CONFIG = {
  ko: { name: '韩语', code: 'ko-KR', label: '韩文', prompt: '资深的韩语老师' },
  th: { name: '泰语', code: 'th-TH', label: '泰文', prompt: '资深的泰语老师' },
  ja: { name: '日语', code: 'ja-JP', label: '日语', prompt: '资深的日语老师' }
};

const App = () => {
  const [currentLang, setCurrentLang] = useState('ko'); 
  const [words, setWords] = useState([
    { word: "안녕하세요", meaning: "你好", example: "안녕하세요, 만나서 반갑습니다.", example_cn: "你好，很高兴见到你。" },
    { word: "감사합니다", meaning: "谢谢", example: "도와주셔서 감사합니다.", example_cn: "谢谢你的帮助。" }
  ]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [viewMode, setViewMode] = useState('flashcard');
  const [score, setScore] = useState({ correct: 0, total: 0 });

  // --- 安全性：API Key 仅存在内存中，默认为空 ---
  const [apiKey, setApiKey] = useState(""); 
  const [showSettings, setShowSettings] = useState(false);

  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const langMeta = useMemo(() => LANGUAGE_CONFIG[currentLang], [currentLang]);

  // --- 新增：自动加载对应语言的 JSON 文件 ---
  useEffect(() => {
    const fileName = `words_${currentLang}.json`;
    console.log(`尝试加载: ${fileName}`);
    
    fetch(fileName)
      .then(res => {
        if (!res.ok) throw new Error("File not found");
        return res.json();
      })
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setWords(data);
          setCurrentIndex(0);
          setIsFlipped(false);
          setAiAnalysis(null); // 切换词库时清空 AI 分析
        }
      })
      .catch(err => {
        console.log(`未找到 ${fileName}，使用默认示例`);
        // 如果未找到文件，重置为简单的提示数据
        setWords([
          { 
            word: "等待数据", 
            meaning: `未找到 words_${currentLang}.json`, 
            example: "请上传文件或确保JSON在同一目录", 
            example_cn: "点击右上角上传按钮手动导入" 
          }
        ]);
        setCurrentIndex(0);
      });
  }, [currentLang]);

  const speak = (text) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = langMeta.code;
    window.speechSynthesis.speak(utterance);
  };

  const callGemini = async (prompt) => {
    if (!apiKey) {
      alert("请先点击右上角设置，输入你的 Gemini API Key");
      return null;
    }

    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`;
    
    const fetchWithRetry = async (retries = 0) => {
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [{ parts: [{ text: prompt }] }],
            generationConfig: { responseMimeType: "application/json" }
          })
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const result = await response.json();
        const text = result.candidates?.[0]?.content?.parts?.[0]?.text;
        return JSON.parse(text || "{}");
      } catch (error) {
        if (retries < 5) {
          const delay = Math.pow(2, retries) * 1000;
          await new Promise(resolve => setTimeout(resolve, delay));
          return fetchWithRetry(retries + 1);
        }
        throw error;
      }
    };

    return fetchWithRetry();
  };

  const fetchAiAnalysis = async () => {
    if (isAnalyzing) return;
    setIsAnalyzing(true);
    setAiAnalysis(null);
    
    const current = words[currentIndex];
    const prompt = `
      作为一个${langMeta.prompt}，请为${langMeta.name}单词 "${current.word}" (含义: ${current.meaning}) 提供深度学习分析。
      请以 JSON 格式返回以下字段：
      - root: 词根、词源或字形简析
      - mnemonic: 趣味助记口诀
      - scenario: 一个简短对话场景
      - scenario_cn: 对话场景的翻译
      仅返回 JSON。
    `;

    try {
      const data = await callGemini(prompt);
      if (data) setAiAnalysis(data);
    } catch (error) {
      console.error("AI Analysis failed", error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  useEffect(() => {
    setAiAnalysis(null);
  }, [currentIndex]);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const json = JSON.parse(event.target.result);
          if (Array.isArray(json)) {
            setWords(json);
            setCurrentIndex(0);
            setIsFlipped(false);
          }
        } catch (err) {
          console.error("Upload failed", err);
        }
      };
      reader.readAsText(file);
    }
  };

  const handleNext = () => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev + 1) % words.length);
  };

  const handlePrev = () => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev - 1 + words.length) % words.length);
  };

  const currentWord = words[currentIndex] || { word: "无数据", meaning: "请导入" };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 font-sans p-4 md:p-8">
      {/* 设置浮层 */}
      {showSettings && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl relative animate-in zoom-in-95 duration-200">
            <button onClick={() => setShowSettings(false)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600">
              <X size={24} />
            </button>
            <div className="flex items-center gap-3 mb-6">
              <div className="bg-amber-100 p-2 rounded-xl text-amber-600"><Key size={20} /></div>
              <h3 className="text-xl font-bold">API 安全配置</h3>
            </div>
            <p className="text-sm text-slate-500 mb-6 leading-relaxed">
              API Key 不会保存在代码中。请输入你的 Google AI Key，它仅保存在当前网页内存中，刷新后需重新输入。
            </p>
            <input 
              type="password" 
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="粘贴你的 AI API Key..."
              className="w-full p-4 bg-slate-50 border-2 border-slate-100 rounded-2xl outline-none focus:border-indigo-500 transition-all mb-6"
            />
            <button onClick={() => setShowSettings(false)} className="w-full py-4 bg-indigo-600 text-white rounded-2xl font-bold hover:bg-indigo-700 transition-all">
              保存并返回
            </button>
          </div>
        </div>
      )}

      {/* 顶部导航 */}
      <header className="max-w-4xl mx-auto flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
        <div className="flex items-center gap-3">
          <div className="bg-indigo-600 p-2 rounded-xl text-white"><Globe size={24} /></div>
          <div><h1 className="text-xl font-bold tracking-tight">语言 Master</h1><p className="text-xs text-slate-400 font-medium">{langMeta.name}模式</p></div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex bg-white p-1 rounded-xl border border-slate-200 shadow-sm mr-2">
            {Object.entries(LANGUAGE_CONFIG).map(([key, config]) => (
              <button key={key} onClick={() => { setCurrentLang(key); }} className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${currentLang === key ? 'bg-indigo-100 text-indigo-700' : 'text-slate-400'}`}>{config.name}</button>
            ))}
          </div>
          <button onClick={() => setShowSettings(true)} className="p-2 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 shadow-sm"><Settings size={18} className={apiKey ? "text-green-500" : "text-slate-500"} /></button>
          <label className="p-2 bg-white border border-slate-200 rounded-xl cursor-pointer hover:bg-slate-50 shadow-sm"><Upload size={18} className="text-slate-500" /><input type="file" accept=".json" onChange={handleFileUpload} className="hidden" /></label>
        </div>
      </header>

      <main className="max-w-4xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          {/* 进度条 */}
          <div className="mb-6 flex items-center gap-4 px-2">
            <div className="flex-1 h-2 bg-slate-300 rounded-full overflow-hidden"><div className="h-full bg-indigo-500 transition-all duration-500" style={{ width: `${((currentIndex + 1) / words.length) * 100}%` }} /></div>
            <span className="text-sm font-semibold text-slate-500">{currentIndex + 1} / {words.length}</span>
          </div>

          {/* 卡片区域 */}
          <div className="perspective-1000 h-[400px] relative group">
            <div 
              onClick={() => setIsFlipped(!isFlipped)}
              className="w-full h-full cursor-pointer relative transition-all duration-700 transform-style-3d"
              style={{ transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)' }}
            >
              {/* 正面：默认显示 */}
              <div 
                className="absolute inset-0 bg-white rounded-[2.5rem] flex flex-col items-center justify-center p-8 border border-slate-200 shadow-xl backface-hidden"
              >
                <span className="text-indigo-500 text-xs font-black mb-6 tracking-[0.3em] uppercase opacity-50">{langMeta.label}单词</span>
                <h2 className="text-6xl font-bold mb-8 text-center leading-tight text-slate-800">{currentWord.word}</h2>
                <button onClick={(e) => { e.stopPropagation(); speak(currentWord.word); }} className="p-5 bg-indigo-50 text-indigo-600 rounded-full hover:bg-indigo-100 transition-all active:scale-90 shadow-sm border border-indigo-100"><Volume2 size={36} /></button>
                <p className="mt-10 text-slate-300 text-[10px] font-black uppercase tracking-widest animate-pulse">点击翻转</p>
              </div>

              {/* 反面：预先旋转180度 */}
              <div 
                className="absolute inset-0 bg-indigo-600 rounded-[2.5rem] flex flex-col items-center justify-center p-8 text-white shadow-2xl backface-hidden"
                style={{ transform: 'rotateY(180deg)' }}
              >
                <span className="text-indigo-200 text-xs font-black mb-6 tracking-[0.3em] uppercase opacity-50">中文释义</span>
                <h2 className="text-5xl font-bold mb-10 text-center text-white">{currentWord.meaning}</h2>
                {currentWord.example && (
                  <div className="bg-white/10 p-6 rounded-3xl max-w-sm text-center border border-white/20 backdrop-blur-sm shadow-inner">
                    <p className="text-lg font-medium mb-2 leading-relaxed italic">"{currentWord.example}"</p>
                    <p className="text-xs text-indigo-100/70 font-medium">{currentWord.example_cn}</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="flex justify-between mt-10 items-center px-4">
            <button onClick={handlePrev} className="p-5 bg-white rounded-2xl shadow-md border border-slate-200 text-slate-600 hover:bg-indigo-50 transition-all active:scale-95"><ChevronLeft size={32} /></button>
            <div className="text-slate-400 text-[10px] font-black uppercase tracking-[0.2em] text-center opacity-40">SWIPE OR USE KEYS</div>
            <button onClick={handleNext} className="p-5 bg-white rounded-2xl shadow-md border border-slate-200 text-slate-600 hover:bg-indigo-50 transition-all active:scale-95"><ChevronRight size={32} /></button>
          </div>
        </div>

        {/* AI 面板 */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-[2rem] shadow-xl border border-slate-200 p-8 flex flex-col h-full sticky top-8 min-h-[550px]">
            <div className="flex items-center justify-between mb-8 border-b border-slate-50 pb-4">
              <div className="flex items-center gap-2"><Sparkles className="text-amber-500" /><h3 className="text-lg font-black tracking-tight">AI AGENT</h3></div>
              <span className="text-[9px] bg-slate-100 px-2 py-1 rounded text-slate-400 font-bold uppercase tracking-tighter">Gemini 2.5</span>
            </div>

            {!aiAnalysis && !isAnalyzing && (
              <div className="flex flex-col items-center justify-center flex-1 py-12 text-center">
                <div className="bg-slate-50 p-6 rounded-full mb-6 border border-slate-100 shadow-inner"><BrainCircuit className="text-slate-300 w-16 h-16" /></div>
                <p className="text-slate-500 text-sm mb-8 leading-relaxed font-medium px-4">解锁单词背后的含义。提供词源分析、记忆技巧及场景对话。</p>
                <button onClick={fetchAiAnalysis} className="w-full py-4 bg-slate-900 text-white rounded-[1.25rem] font-black flex items-center justify-center gap-3 shadow-xl hover:bg-indigo-600 transition-all active:scale-95 tracking-widest text-xs"><Sparkles size={16} /> 开启 AI 深度学习</button>
              </div>
            )}

            {isAnalyzing && (
              <div className="flex flex-col items-center justify-center flex-1 py-12">
                <div className="relative mb-6"><Loader2 className="animate-spin text-indigo-600 w-16 h-16 opacity-20" /><Sparkles className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-indigo-600 animate-pulse" size={24} /></div>
                <p className="text-slate-400 font-black animate-pulse text-[10px] tracking-[0.2em] uppercase">Processing Analysis...</p>
              </div>
            )}

            {aiAnalysis && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 overflow-y-auto max-h-[65vh] pr-2 scrollbar-hide">
                <section><div className="flex items-center gap-2 text-indigo-600 font-black text-[10px] mb-3 tracking-[0.2em] uppercase"><BookOpen size={14} /> Etymology</div><p className="text-slate-700 text-sm bg-indigo-50/50 p-4 rounded-2xl border border-indigo-100/50 leading-relaxed shadow-sm font-medium">{aiAnalysis.root}</p></section>
                <section><div className="flex items-center gap-2 text-amber-600 font-black text-[10px] mb-3 tracking-[0.2em] uppercase"><Lightbulb size={14} /> Mnemonic</div><div className="bg-amber-50/50 p-4 rounded-2xl border border-amber-100/50 italic text-slate-800 text-sm shadow-sm font-medium">“{aiAnalysis.mnemonic}”</div></section>
                <section><div className="flex items-center gap-2 text-teal-600 font-black text-[10px] mb-3 tracking-[0.2em] uppercase"><MessageSquareQuote size={14} /> Dialogue</div><div className="bg-teal-50/50 p-5 rounded-3xl border border-teal-100/50 shadow-sm"><p className="text-slate-800 font-bold mb-2 text-sm leading-relaxed">{aiAnalysis.scenario}</p><p className="text-[11px] text-slate-500 italic leading-relaxed font-medium opacity-80">{aiAnalysis.scenario_cn}</p></div></section>
                <button onClick={fetchAiAnalysis} className="w-full py-2 text-slate-400 text-[9px] font-black hover:text-indigo-600 hover:bg-indigo-50 transition-all rounded-lg border border-slate-100 uppercase tracking-[0.3em] opacity-50 hover:opacity-100">Refresh Data</button>
              </div>
            )}
          </div>
        </div>
      </main>

      <style dangerouslySetInnerHTML={{ __html: `
        .perspective-1000 { perspective: 1000px; }
        .backface-hidden { backface-visibility: hidden; -webkit-backface-visibility: hidden; }
        .transform-style-3d { transform-style: preserve-3d; }
        .scrollbar-hide::-webkit-scrollbar { display: none; }
        .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
      `}} />
    </div>
  );
};

export default App;
