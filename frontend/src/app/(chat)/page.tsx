'use client';

import { useState } from 'react';
import { Sidebar } from '../../components/sidebar';
import { ChatPane } from '../../components/chat-pane';
import { CaptureButton } from '../../components/capture-button';
import { Person, ChatMessage } from '../../types';
import usersData from '../../data/users.json';
import messagesData from '../../data/messages.json';

export default function Home() {
  const [people, setPeople] = useState<Person[]>(usersData as Person[]);
  const [messages, setMessages] = useState<ChatMessage[]>((messagesData as any)[0].messages as ChatMessage[]);

  const handleCapture = (newPerson: Person) => {
    setPeople(prev => [newPerson, ...prev]);
  };

  const handleSendMessage = (text: string) => {
    const userMessage: ChatMessage = {
      id: `m_${Date.now()}`,
      sender: 'user',
      text,
      ts: Math.floor(Date.now() / 1000)
    };

    const assistantMessage: ChatMessage = {
      id: `m_${Date.now() + 1}`,
      sender: 'assistant',
      text: '(mock) I would answer using scanned data.',
      ts: Math.floor(Date.now() / 1000) + 1
    };

    setMessages(prev => [...prev, userMessage, assistantMessage]);
  };

  return (
    <div className="flex h-screen">
      <Sidebar people={people} />
      <ChatPane messages={messages} onSendMessage={handleSendMessage} />
      <CaptureButton onCapture={handleCapture} />
    </div>
  );
}
