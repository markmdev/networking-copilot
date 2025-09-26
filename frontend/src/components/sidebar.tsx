'use client';

import { Avatar, AvatarFallback } from './ui/avatar';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import { Person } from '../types';
import { Search } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';

interface SidebarProps {
  people: Person[];
}

export function Sidebar({ people }: SidebarProps) {
  const [search, setSearch] = useState('');

  const filteredPeople = people.filter(person =>
    person.name.toLowerCase().includes(search.toLowerCase()) ||
    person.role.toLowerCase().includes(search.toLowerCase()) ||
    person.company.toLowerCase().includes(search.toLowerCase())
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
          {filteredPeople.map((person) => (
            <Link
              key={person.id}
              href={`/users/${person.id}`}
              className="flex items-center gap-3 p-3 rounded-lg hover:bg-white transition-colors block"
            >
              <Avatar>
                <AvatarFallback>
                  {person.name.split(' ').map((n: string) => n[0]).join('')}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{person.name}</p>
                <p className="text-xs text-gray-500 truncate">{person.role}</p>
              </div>
            </Link>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
