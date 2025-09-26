export type Person = {
  id: string;
  name: string;
  role: string;
  company: string;
  email: string;
  phone: string;
  linkedin: string;
  avatarUrl?: string;
  summary: string;
  tags: string[];
};

export type ChatMessage = {
  id: string;
  sender: "user" | "assistant" | "system";
  text: string;
  ts: number;
};

export type ChatThread = {
  threadId: string;
  messages: ChatMessage[];
};
