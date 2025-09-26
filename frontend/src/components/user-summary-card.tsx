import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { PersonDetail } from '../types';

interface UserSummaryCardProps {
  detail: PersonDetail;
}

export function UserSummaryCard({ detail }: UserSummaryCardProps) {
  const { person, crew_outputs } = detail;
  const summary = crew_outputs.summary_generator_task.summary;
  const keyHighlights = crew_outputs.summary_generator_task.key_highlights;

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-4">
            <Avatar className="w-16 h-16">
              {person.avatar && (
                <AvatarImage src={person.avatar} alt={person.name} />
              )}
              <AvatarFallback className="text-lg">
                {person.name.split(' ').map(n => n[0]).join('')}
              </AvatarFallback>
            </Avatar>
            <div className="min-w-0">
              <CardTitle className="text-xl truncate">{person.name}</CardTitle>
              <p className="text-gray-600 truncate">
                {person.subtitle || person.experience || 'Role not available'}
              </p>
              {person.location && (
                <p className="text-sm text-gray-500">{person.location}</p>
              )}
            </div>
          </div>
          {keyHighlights.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {keyHighlights.map((tag, idx) => (
                <Badge key={idx} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="text-gray-700 whitespace-pre-line">{summary}</p>
        </div>
        {person.url && (
          <a
            href={person.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-600 hover:underline"
          >
            View LinkedIn Profile
          </a>
        )}
      </CardContent>
    </Card>
  );
}
