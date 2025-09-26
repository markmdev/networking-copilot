import { Avatar, AvatarFallback } from './ui/avatar';
import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Person } from '../types';

interface UserSummaryCardProps {
  person: Person;
}

export function UserSummaryCard({ person }: UserSummaryCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-4">
          <Avatar className="w-16 h-16">
            <AvatarFallback className="text-lg">
              {person.name.split(' ').map(n => n[0]).join('')}
            </AvatarFallback>
          </Avatar>
          <div>
            <CardTitle className="text-xl">{person.name}</CardTitle>
            <p className="text-gray-600">{person.role} at {person.company}</p>
            <div className="flex gap-1 mt-2">
              {person.tags.map((tag) => (
                <Badge key={tag} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-gray-700">{person.summary}</p>
      </CardContent>
    </Card>
  );
}
