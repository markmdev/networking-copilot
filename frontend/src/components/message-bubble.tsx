'use client';

import { ChatMessage } from '../types';
import { cn } from '../lib/utils';

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.sender === 'user';
  const isSystem = message.sender === 'system';

  return (
    <div
      className={cn(
        'flex mb-3',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={cn(
          'max-w-xs lg:max-w-md px-4 py-2 rounded-lg',
          isUser
            ? 'bg-blue-500 text-white'
            : isSystem
            ? 'bg-gray-100 text-gray-600 text-sm'
            : 'bg-gray-200 text-gray-900'
        )}
      >
        <p className="text-sm">{message.text}</p>
        <p className="text-xs opacity-70 mt-1">
          {new Date(message.ts * 1000).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}
