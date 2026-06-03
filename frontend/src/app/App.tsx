import { useState, useRef, useEffect } from "react";
import { Brain, Send, Bot, User, Loader2, AlertTriangle, Zap, Sun, Moon, Menu } from "lucide-react";

type Message = {
  id: string;
  role: 'system' | 'user';
  content: string | React.ReactNode;
};

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'system',
      content: "Halo! Saya adalah AI Diagnosa Website. Ceritakan masalah website Anda secara detail (misal: 'website saya tiba-tiba blank' atau 'server saya tidak bisa di ping sejak pagi')."
    }
  ]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize Dark Mode based on system preference
  useEffect(() => {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setIsDarkMode(true);
    }
  }, []);

  // Toggle dark class on HTML element
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userText = inputText.trim();
    setInputText("");

    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'user',
      content: userText
    }]);

    setIsLoading(true);

    try {
      // Mengirim input teks user ke Backend Python untuk dianalisa menggunakan NLP
      const response = await fetch("http://localhost:8000/api/nlp-diagnose", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: userText }),
      });
      
      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }

      let systemResponse: React.ReactNode;

      if (data.showWarning) {
        systemResponse = (
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2 text-orange-600 dark:text-orange-400 font-medium">
              <AlertTriangle className="w-5 h-5" />
              Maaf, informasi kurang jelas.
            </div>
            <p>Saya tidak dapat mendiagnosa masalah secara pasti dari penjelasan Anda. Mohon berikan ciri-ciri atau pesan error yang lebih spesifik.</p>
          </div>
        );
      } else if (data.results && data.results.length > 0) {
        const result = data.results[0];
        systemResponse = (
          <div className="flex flex-col gap-4">
            <p>Berdasarkan analisa NLP pada penjelasan Anda, berikut adalah kemungkinan kerusakannya:</p>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-indigo-100 dark:border-indigo-900/30">
               <div className="flex items-center justify-between mb-3">
                 <h4 className="font-bold text-indigo-900 dark:text-indigo-300 text-lg">{result.kategori}</h4>
                 <span className="bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 px-2 py-1 rounded-md text-sm font-bold">{result.pct}% Cocok</span>
               </div>
               <div className="mb-3">
                 <h5 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase mb-1">Gejala (Keywords) Terdeteksi:</h5>
                 <div className="flex flex-wrap gap-1">
                   {result.matched.map((g: string) => (
                     <span key={g} className="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-1 rounded text-xs">{g}</span>
                   ))}
                 </div>
               </div>
               <div className="border-t border-indigo-50 dark:border-gray-700 pt-3">
                  <h5 className="text-sm font-bold text-gray-700 dark:text-gray-200 mb-1 flex items-center gap-1">
                    <Zap className="w-4 h-4 text-indigo-500 dark:text-indigo-400"/> Solusi Perbaikan:
                  </h5>
                  <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">{result.solusi}</p>
               </div>
            </div>
          </div>
        );
      }

      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'system',
        content: systemResponse
      }]);

    } catch (err: any) {
      console.error("Chat Error:", err);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'system',
        content: `Error: ${err.message || 'Koneksi ke server backend gagal. Pastikan server Flask sudah berjalan.'}`
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="h-screen w-full flex flex-col bg-white dark:bg-gray-900 transition-colors duration-200 overflow-hidden text-gray-800 dark:text-gray-100 font-sans">
      
      {/* Minimalist Header */}
      <header className="flex-shrink-0 h-14 border-b border-gray-100 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md flex items-center justify-between px-4 sm:px-6 z-10">
        <div className="flex items-center gap-3">
          <Menu className="w-5 h-5 text-gray-500 hover:text-gray-800 dark:hover:text-gray-200 cursor-pointer transition-colors sm:hidden" />
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            <h1 className="text-base sm:text-lg font-semibold tracking-tight text-gray-900 dark:text-gray-100">Diagnosa AI</h1>
          </div>
        </div>
        
        <button 
          onClick={() => setIsDarkMode(!isDarkMode)}
          className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 transition-colors"
          title="Toggle Theme"
        >
          {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 overflow-y-auto w-full scroll-smooth flex flex-col items-center">
        <div className="w-full max-w-3xl flex flex-col gap-6 p-4 sm:p-6 pb-6">
          {messages.map((msg) => (
            <div 
              key={msg.id} 
              className={`flex gap-4 sm:gap-5 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`flex justify-center ${msg.role === 'user' ? 'items-center w-10' : ''}`}>
                {/* Avatar Minimalist */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${msg.role === 'user' ? 'bg-indigo-100 dark:bg-indigo-900/50' : 'bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700'}`}>
                  {msg.role === 'user' ? <User className="w-4 h-4 text-indigo-600 dark:text-indigo-400" /> : <Brain className="w-4 h-4 text-gray-600 dark:text-gray-300" />}
                </div>
              </div>

              {/* Message Content */}
              <div className={`max-w-[85%] sm:max-w-prose pt-1 ${
                msg.role === 'user' 
                  ? 'text-gray-800 dark:text-gray-100' 
                  : 'text-gray-800 dark:text-gray-200'
              }`}>
                {msg.role === 'user' ? (
                   <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl px-5 py-3 inline-block ml-auto max-w-full text-[15px] leading-relaxed shadow-sm text-left">
                     {msg.content}
                   </div>
                ) : (
                   <div className="text-[15px] leading-relaxed pr-4">
                     {msg.content}
                   </div>
                )}
              </div>
            </div>
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex gap-4 sm:gap-6 w-full max-w-3xl">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 flex items-center justify-center">
                <Brain className="w-4 h-4 text-gray-600 dark:text-gray-300" />
              </div>
              <div className="flex-1 pt-2 flex items-center gap-2 text-gray-500 dark:text-gray-400">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm font-medium">Menganalisa...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} className="h-4" />
        </div>
      </main>

      {/* Input Area */}
      <div className="w-full bg-white dark:bg-gray-900 pt-2 pb-6 px-4 z-20 flex justify-center">
        <div className="w-full max-w-3xl relative">
          <div className="relative shadow-[0_0_15px_rgba(0,0,0,0.05)] dark:shadow-[0_0_15px_rgba(0,0,0,0.4)] rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex items-end">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Jelaskan masalah website Anda..."
              className="w-full bg-transparent text-gray-800 dark:text-gray-100 text-base p-4 pr-14 focus:outline-none resize-none max-h-32 min-h-[56px] rounded-2xl leading-relaxed"
              rows={1}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputText.trim() || isLoading}
              className="absolute right-2 bottom-2 p-2 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-500 transition-colors disabled:opacity-30 disabled:hover:bg-indigo-600 flex items-center justify-center"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <p className="text-center text-xs text-gray-400 mt-3">
            Sistem pakar ini menggunakan NLP untuk memahami konteks kalimat Anda secara otomatis.
          </p>
        </div>
      </div>

    </div>
  );
}
