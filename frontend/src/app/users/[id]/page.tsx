'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '../../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Input } from '../../../components/ui/input';
import { UserSummaryCard } from '../../../components/user-summary-card';
import { Person } from '../../../types';
import usersData from '../../../data/users.json';
import { ArrowLeft, Copy, Mail, Phone, Linkedin, Plus } from 'lucide-react';

interface Note {
  id: string;
  text: string;
  createdAt: number;
}

export default function UserDetail() {
  const params = useParams();
  const router = useRouter();
  const [person, setPerson] = useState<Person | null>(null);
  const [notes, setNotes] = useState<Note[]>([
    { id: '1', text: 'Met at Tech Conference 2024', createdAt: 1710000000 },
    { id: '2', text: 'Interested in AI/ML partnerships', createdAt: 1710001000 }
  ]);
  const [newNote, setNewNote] = useState('');

  useEffect(() => {
    const foundPerson = (usersData as Person[]).find(p => p.id === params.id);
    setPerson(foundPerson || null);
  }, [params.id]);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const handleAddNote = () => {
    if (newNote.trim()) {
      const note: Note = {
        id: Date.now().toString(),
        text: newNote.trim(),
        createdAt: Math.floor(Date.now() / 1000)
      };
      setNotes(prev => [note, ...prev]);
      setNewNote('');
    }
  };

  if (!person) {
    return (
      <div className="p-4">
        <Button onClick={() => router.back()} variant="ghost" className="mb-4">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <p>Person not found</p>
      </div>
    );
  }

  return (
    <div className="p-4 max-w-6xl mx-auto">
      <Button onClick={() => router.back()} variant="ghost" className="mb-4">
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back
      </Button>

      <div className="mb-6">
        <UserSummaryCard person={person} />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Essential Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Mail className="w-4 h-4 text-gray-500" />
                <span className="text-sm">{person.email}</span>
              </div>
              <Button size="sm" variant="ghost" onClick={() => handleCopy(person.email)}>
                <Copy className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Phone className="w-4 h-4 text-gray-500" />
                <span className="text-sm">{person.phone}</span>
              </div>
              <Button size="sm" variant="ghost" onClick={() => handleCopy(person.phone)}>
                <Copy className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Linkedin className="w-4 h-4 text-gray-500" />
                <span className="text-sm">{person.linkedin}</span>
              </div>
              <Button size="sm" variant="ghost" onClick={() => handleCopy(person.linkedin)}>
                <Copy className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700">{person.summary}</p>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Notes</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 mb-4">
            <Input
              placeholder="Add a note..."
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAddNote()}
            />
            <Button onClick={handleAddNote} size="sm">
              <Plus className="w-4 h-4" />
            </Button>
          </div>

          <div className="space-y-3">
            {notes.map((note) => (
              <div key={note.id} className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm">{note.text}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {new Date(note.createdAt * 1000).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
