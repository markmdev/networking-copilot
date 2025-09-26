'use client';

import { useCallback, useEffect, useState } from 'react';
import { Sidebar } from '../../components/sidebar';
import { ChatPane } from '../../components/chat-pane';
import { CaptureButton } from '../../components/capture-button';
import { PersonListItem, PersonDetail, ChatMessage } from '../../types';
import messagesData from '../../data/messages.json';
import { fetchPeople } from '../../lib/api';

type MessageThread = {
  threadId: string;
  messages: ChatMessage[];
};

const initialThreads = messagesData as MessageThread[];
const initialMessages = initialThreads[0]?.messages ?? [];

export default function Home() {
  const [people, setPeople] = useState<PersonListItem[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const loadPeople = useCallback(async () => {
    try {
      const data = await fetchPeople();
      setPeople(data);
    } catch (error) {
      console.error('Failed to load people', error);
    }
  }, []);

  useEffect(() => {
    loadPeople();
  }, [loadPeople]);

  const mapDetailToListItem = (record: PersonDetail): PersonListItem => ({
    id: record.id,
    name: record.person.name,
    subtitle: record.person.subtitle ?? record.person.experience ?? undefined,
    location: record.person.location ?? undefined,
    avatar: record.person.avatar ?? undefined,
    created_at: record.created_at,
  });

  const handleCapture = (record: PersonDetail) => {
    setPeople(prev => {
      const next = prev.filter(p => p.id !== record.id);
      return [mapDetailToListItem(record), ...next];
    });
    loadPeople();
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
