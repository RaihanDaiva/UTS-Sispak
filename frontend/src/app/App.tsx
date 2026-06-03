import { useState, useRef, useEffect } from "react";
import { Brain, Send, Bot, User, Loader2, AlertTriangle, Zap } from "lucide-react";

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
  const messagesEndRef = useRef<HTMLDivElement>(null);

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

    // Menambahkan pesan pengguna ke UI
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
            <div className="flex items-center gap-2 text-orange-600 font-medium">
              <AlertTriangle className="w-5 h-5" />
              Maaf, informasi kurang jelas.
            </div>
            <p>Saya tidak dapat mendiagnosa masalah secara pasti dari penjelasan Anda. Mohon berikan ciri-ciri atau pesan error yang lebih spesifik.</p>
          </div>
        );
      } else if (data.results && data.results.length > 0) {
        const result = data.results[0]; // Mengambil ranking diagnosa tertinggi
        systemResponse = (
          <div className="flex flex-col gap-4">
            <p>Berdasarkan analisa NLP pada penjelasan Anda, berikut adalah kemungkinan kerusakannya:</p>
            <div className="bg-white rounded-xl p-4 shadow-sm border border-indigo-100">
               <div className="flex items-center justify-between mb-3">
                 <h4 className="font-bold text-indigo-900 text-lg">{result.kategori}</h4>
                 <span className="bg-indigo-100 text-indigo-700 px-2 py-1 rounded-md text-sm font-bold">{result.pct}% Cocok</span>
               </div>
               <div className="mb-3">
                 <h5 className="text-xs font-bold text-gray-500 uppercase mb-1">Gejala (Keywords) Terdeteksi:</h5>
                 <div className="flex flex-wrap gap-1">
                   {result.matched.map((g: string) => (
                     <span key={g} className="bg-gray-100 text-gray-600 px-2 py-1 rounded text-xs">{g}</span>
                   ))}
                 </div>
               </div>
               <div className="border-t border-indigo-50 pt-3">
                  <h5 className="text-sm font-bold text-gray-700 mb-1 flex items-center gap-1">
                    <Zap className="w-4 h-4 text-indigo-500"/> Solusi Perbaikan:
                  </h5>
                  <p className="text-sm text-gray-600 leading-relaxed">{result.solusi}</p>
               </div>
            </div>
          </div>
        );
      }

      // Menambahkan balasan sistem ke UI
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
    // Submit pesan dengan tombol Enter (Shift+Enter untuk baris baru)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex justify-center p-0 sm:p-6 lg:p-8">
      <div className="w-full max-w-4xl bg-white sm:rounded-3xl shadow-2xl flex flex-col overflow-hidden border border-gray-100 h-[100dvh] sm:h-[90vh]">
        
        {/* Chat Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-4 sm:p-6 flex items-center gap-4 text-white shadow-md z-10">
          <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold">Website Diagnostic AI</h1>
            <p className="text-indigo-100 text-sm">Powered by NLP & Expert System</p>
          </div>
        </div>

        {/* Chat Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 bg-gradient-to-b from-gray-50 to-white scroll-smooth">
          <div className="flex flex-col gap-6">
            {messages.map((msg) => (
              <div 
                key={msg.id} 
                className={`flex gap-3 sm:gap-4 max-w-[85%] sm:max-w-[75%] ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
              >
                {/* Avatar */}
                <div className={`flex-shrink-0 w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center ${msg.role === 'user' ? 'bg-indigo-100' : 'bg-gradient-to-br from-indigo-500 to-purple-600 shadow-md'}`}>
                  {msg.role === 'user' ? <User className="w-5 h-5 text-indigo-600" /> : <Bot className="w-5 h-5 text-white" />}
                </div>

                {/* Message Bubble */}
                <div className={`p-4 rounded-2xl text-sm sm:text-base ${
                  msg.role === 'user' 
                    ? 'bg-indigo-600 text-white rounded-tr-sm shadow-md' 
                    : 'bg-white border border-gray-100 text-gray-800 rounded-tl-sm shadow-sm'
                }`}>
                  {msg.content}
                </div>
              </div>
            ))}

            {/* Loading Indicator */}
            {isLoading && (
               <div className="flex gap-3 sm:gap-4 max-w-[85%] sm:max-w-[75%]">
                 <div className="flex-shrink-0 w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 shadow-md flex items-center justify-center">
                   <Bot className="w-5 h-5 text-white" />
                 </div>
                 <div className="p-4 rounded-2xl bg-white border border-gray-100 text-gray-800 rounded-tl-sm shadow-sm flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
                    <span className="text-sm text-gray-500">Menganalisa teks menggunakan NLP...</span>
                 </div>
               </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Chat Input Area */}
        <div className="bg-white border-t border-gray-100 p-4 sm:p-6 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-10">
          <div className="relative flex items-end gap-2 max-w-4xl mx-auto">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ketik masalah website Anda di sini..."
              className="w-full bg-gray-50 border border-gray-200 text-gray-800 text-sm sm:text-base rounded-2xl p-4 pr-14 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all resize-none max-h-32 min-h-[60px]"
              rows={1}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputText.trim() || isLoading}
              className="absolute right-2 bottom-2 p-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center shadow-sm"
            >
              <Send className="w-5 h-5 ml-1" />
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
