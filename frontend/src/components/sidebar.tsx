'use client';

import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import { PersonListItem } from '../types';
import { Search } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';

interface SidebarProps {
  people: PersonListItem[];
}

export function Sidebar({ people }: SidebarProps) {
  const [search, setSearch] = useState('');

  const filteredPeople = people.filter(person =>
    person.name.toLowerCase().includes(search.toLowerCase()) ||
    (person.subtitle ?? '').toLowerCase().includes(search.toLowerCase()) ||
    (person.location ?? '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="w-72 border-r bg-gray-50 h-full flex flex-col">
      <div className="p-4">
        <h1 className="text-lg font-semibold mb-3">People</h1>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder="Search people..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>
      <Separator />
      <ScrollArea className="flex-1">
        <div className="p-2">
          {filteredPeople.length === 0 && (
            <p className="text-sm text-gray-500 p-3">No people captured yet.</p>
          )}
          {filteredPeople.map((person) => {
            const initials = person.name
              ? person.name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()
              : '?';
            return (
              <Link
                key={person.id}
                href={`/users/${person.id}`}
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-white transition-colors block"
              >
                <Avatar>
                  {person.avatar && <AvatarImage src={person.avatar} alt={person.name} />}
                  <AvatarFallback>{initials}</AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{person.name}</p>
                  <p className="text-xs text-gray-500 truncate">
                    {person.subtitle || person.location || '—'}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}
