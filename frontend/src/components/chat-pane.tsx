'use client';

import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Textarea } from './ui/textarea';
import { ChatMessage } from '../types';
import { MessageBubble } from './message-bubble';
import { Send } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';

interface ChatPaneProps {
  messages: ChatMessage[];
  onSendMessage: (text: string) => Promise<void>;
}

export function ChatPane({ messages, onSendMessage }: ChatPaneProps) {
  const [input, setInput] = useState('');
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (trimmed) {
      setInput('');
      await onSendMessage(trimmed);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
        <div className="space-y-1 min-w-0">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>
      <div className="border-t p-4">
        <div className="flex gap-2">
          <Textarea
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            className="resize-none min-h-[40px] max-h-[120px]"
            rows={1}
          />
          <Button onClick={() => void handleSend()} size="sm" className="self-end">
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
