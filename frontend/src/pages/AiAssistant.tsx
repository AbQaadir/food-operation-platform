import React, { useState, useRef, useEffect } from 'react';
import {
  Bot,
  Send,
  User,
  Terminal,
  RefreshCw,
  Database
} from 'lucide-react';
import { aiApi, ChatMessage, ToolCallPayload, ToolResultPayload } from '../api/client';

interface MessageItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCallPayload[];
  toolResults?: ToolResultPayload[];
  isStreaming?: boolean;
}

export const AiAssistant: React.FC = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<MessageItem[]>([
    {
      id: 'initial',
      role: 'assistant',
      content:
        'Hello! I am your AI Operations Assistant. I have real-time read-only access to multi-warehouse inventory, order statuses, low-stock alerts, and daily sales KPIs. How can I assist your operations today?',
    },
  ]);
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const quickPrompts = [
    'What is the stock level of product a68d0d41-c837-4da4-8c66-e64f5ea6e761?',
    "Show today's sales and revenue KPI",
    'List all products below low stock threshold',
    'What is the status of order 12389a41-8375-42ef-9344-dae519c8c2ac?',
  ];

  const handleSend = async (textToSend?: string) => {
    const userText = (textToSend || input).trim();
    if (!userText || isStreaming) return;

    setInput('');

    const userMessage: MessageItem = {
      id: crypto.randomUUID(),
      role: 'user',
      content: userText,
    };

    const assistantMessageId = crypto.randomUUID();
    const assistantMessage: MessageItem = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      toolCalls: [],
      toolResults: [],
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setIsStreaming(true);

    const chatHistory: ChatMessage[] = [...messages, userMessage].map((m) => ({
      role: m.role,
      content: m.content,
    }));

    await aiApi.streamChat(chatHistory, {
      onToolCall: (call) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, toolCalls: [...(msg.toolCalls || []), call] }
              : msg
          )
        );
      },
      onToolResult: (res) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, toolResults: [...(msg.toolResults || []), res] }
              : msg
          )
        );
      },
      onToken: (chunk) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: msg.content + chunk }
              : msg
          )
        );
      },
      onDone: () => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId ? { ...msg, isStreaming: false } : msg
          )
        );
        setIsStreaming(false);
      },
      onError: (_err) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  content:
                    msg.content +
                    '\n\n*[Error: Could not complete streaming response. Check if ai-service (:8087) is running.]*',
                  isStreaming: false,
                }
              : msg
          )
        );
        setIsStreaming(false);
      },
    });
  };

  return (
    <div className="h-[calc(100vh-10rem)] flex flex-col bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-slate-950 font-bold shadow-md">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-tight flex items-center space-x-2">
              <span>FoodOps AI Assistant</span>
              <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full font-mono font-medium">
                Tool-Calling Agent
              </span>
            </h1>
            <p className="text-xs text-slate-400">Read-only operational telemetry &amp; live diagnostics</p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs text-emerald-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-medium">Online (:8087)</span>
        </div>
      </div>

      {/* Message Feed */}
      <div className="flex-1 overflow-y-auto p-6 space-y-5 bg-slate-50/50">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start space-x-3 ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center flex-shrink-0 shadow-sm">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div
              className={`max-w-2xl rounded-2xl p-4 text-sm shadow-sm space-y-3 ${
                msg.role === 'user'
                  ? 'bg-slate-900 text-white rounded-tr-none'
                  : 'bg-white text-slate-800 border border-slate-200 rounded-tl-none'
              }`}
            >
              {/* Tool Execution Visual Cards */}
              {msg.toolCalls && msg.toolCalls.length > 0 && (
                <div className="space-y-2">
                  {msg.toolCalls.map((call, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-900 text-emerald-400 font-mono text-xs rounded-xl p-3 border border-slate-800 space-y-1 shadow-inner"
                    >
                      <div className="flex items-center justify-between text-slate-400 border-b border-slate-800 pb-1 text-[11px]">
                        <span className="flex items-center space-x-1.5 text-emerald-400 font-semibold">
                          <Terminal className="w-3.5 h-3.5" />
                          <span>Tool Dispatched:</span>
                        </span>
                        <span className="bg-slate-800 px-2 py-0.5 rounded text-[10px] text-slate-300">
                          {call.tool}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-300 pt-1">
                        Arguments: <code className="text-emerald-300">{JSON.stringify(call.args)}</code>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Tool Results Preview */}
              {msg.toolResults && msg.toolResults.length > 0 && (
                <div className="space-y-2">
                  {msg.toolResults.map((res, idx) => (
                    <div
                      key={idx}
                      className="bg-emerald-50/60 rounded-xl p-3 border border-emerald-200 text-xs text-slate-700 space-y-1"
                    >
                      <div className="flex items-center space-x-1 font-semibold text-emerald-800 text-[11px]">
                        <Database className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Data Returned from Service:</span>
                      </div>
                      <pre className="font-mono text-[11px] bg-white/80 p-2 rounded border border-emerald-100 overflow-x-auto text-slate-800">
                        {JSON.stringify(res.result, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>
              )}

              {/* Natural Language Message Body */}
              <div className="whitespace-pre-wrap leading-relaxed">
                {msg.content || (msg.isStreaming && (
                  <span className="flex items-center space-x-1 text-slate-400 text-xs italic">
                    <RefreshCw className="w-3 h-3 animate-spin mr-1" />
                    Synthesizing response...
                  </span>
                ))}
              </div>
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-lg bg-slate-800 text-white flex items-center justify-center flex-shrink-0 shadow-sm">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompts */}
      <div className="px-6 py-2 bg-slate-100/80 border-t border-slate-200 overflow-x-auto flex space-x-2">
        {quickPrompts.map((prompt, i) => (
          <button
            key={i}
            disabled={isStreaming}
            onClick={() => handleSend(prompt)}
            className="flex-shrink-0 text-xs bg-white hover:bg-emerald-50 text-slate-700 hover:text-emerald-700 px-3 py-1.5 rounded-full border border-slate-200 shadow-sm transition disabled:opacity-50"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <div className="p-4 bg-white border-t border-slate-200">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center space-x-3"
        >
          <input
            type="text"
            placeholder="Ask about inventory levels, order statuses, or sales metrics..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isStreaming}
            className="flex-1 border border-slate-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-sm font-semibold shadow-sm transition flex items-center space-x-2 disabled:opacity-50"
          >
            {isStreaming ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <span>Send</span>
                <Send className="w-4 h-4" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
