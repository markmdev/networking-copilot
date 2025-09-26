"use client";

import { useCallback, useEffect, useState } from "react";
import { Sidebar } from "../../components/sidebar";
import { ChatPane } from "../../components/chat-pane";
import { CaptureButton } from "../../components/capture-button";
import { PersonListItem, PersonDetail, ChatMessage } from "../../types";
import { fetchPeople, sendChatMessage } from "../../lib/api";

export default function Home() {
  const [people, setPeople] = useState<PersonListItem[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const loadPeople = useCallback(async () => {
    try {
      const data = await fetchPeople();
      setPeople(data);
    } catch (error) {
      console.error("Failed to load people", error);
    }
  }, []);

  useEffect(() => {
    loadPeople();
  }, [loadPeople]);

  const mapDetailToListItem = useCallback(
    (record: PersonDetail): PersonListItem => ({
      id: record.id,
      name: record.person.name,
      subtitle: record.person.subtitle ?? record.person.experience ?? undefined,
      location: record.person.location ?? undefined,
      avatar: record.person.avatar ?? undefined,
      created_at: record.created_at,
    }),
    []
  );

  const handleCapture = useCallback(
    (record: PersonDetail) => {
      setPeople((prev) => {
        const next = prev.filter((p) => p.id !== record.id);
        return [mapDetailToListItem(record), ...next];
      });
      // Refresh list to keep order consistent with backend index
      loadPeople();
    },
    [loadPeople, mapDetailToListItem]
  );

  const handleSendMessage = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    const now = Date.now();
    const userMessage: ChatMessage = {
      id: `m_${now}`,
      sender: "user",
      text: trimmed,
      ts: Math.floor(now / 1000),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const { reply } = await sendChatMessage(trimmed);
      const assistantMessage: ChatMessage = {
        id: `m_${now + 1}`,
        sender: "assistant",
        text: reply,
        ts: Math.floor(now / 1000) + 1,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const assistantMessage: ChatMessage = {
        id: `m_${now + 1}`,
        sender: "assistant",
        text: `I couldn't get that info because of an error: ${error}`,
        ts: Math.floor(now / 1000) + 1,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    }
  }, []);

  return (
    <div className="flex h-screen">
      <Sidebar people={people} />
      <ChatPane messages={messages} onSendMessage={handleSendMessage} />
      <CaptureButton onCapture={handleCapture} />
    </div>
  );
}
