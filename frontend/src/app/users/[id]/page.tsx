import { notFound } from "next/navigation";
import { fetchPerson } from "../../../lib/api";
import { UserSummaryCard } from "../../../components/user-summary-card";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { Badge } from "../../../components/ui/badge";
import Link from "next/link";

interface PersonPageProps {
  params: { id: string };
}

export default async function PersonPage({ params }: PersonPageProps) {
  let detail;
  try {
    detail = await fetchPerson(params.id);
  } catch (error) {
    console.error("Failed to load person", error);
    notFound();
  }

  if (!detail) {
    notFound();
  }

  const analyzer = detail.crew_outputs.linkedin_profile_analyzer_task;
  const icebreakers = detail.crew_outputs.icebreaker_generator_task.icebreakers;
  const links = detail.extracted?.links;
  const basicInfo = detail.extracted?.basic_info;

  return (
    <div className="container mx-auto py-8 space-y-6">
      <UserSummaryCard detail={detail} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Key Highlights</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {analyzer.highlights.map((item, index) => (
              <div key={index} className="text-sm text-gray-700">
                • {item}
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Icebreakers</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {icebreakers.map((icebreaker, index) => (
              <div key={index}>
                <Badge variant="outline" className="text-xs mb-1">
                  {icebreaker.category}
                </Badge>
                <p className="text-sm text-gray-700">{icebreaker.prompt}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Contact Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-gray-700">
          {basicInfo?.company && (
            <div>
              <span className="font-medium mr-2">Company:</span>
              <span>{basicInfo.company}</span>
            </div>
          )}
          {links?.linkedin && (
            <div>
              <span className="font-medium mr-2">LinkedIn:</span>
              <Link href={links.linkedin} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                {links.linkedin}
              </Link>
            </div>
          )}
          {links?.email && (
            <div>
              <span className="font-medium mr-2">Email:</span>
              <a href={`mailto:${links.email}`} className="text-blue-600 hover:underline">{links.email}</a>
            </div>
          )}
          {links?.phone && (
            <div>
              <span className="font-medium mr-2">Phone:</span>
              <span>{links.phone}</span>
            </div>
          )}
          {links?.website && (
            <div>
              <span className="font-medium mr-2">Website:</span>
              <Link href={links.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                {links.website}
              </Link>
            </div>
          )}
          {links?.github && (
            <div>
              <span className="font-medium mr-2">GitHub:</span>
              <Link href={links.github} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                {links.github}
              </Link>
            </div>
          )}
          {!links && <p>No additional contact details found.</p>}
        </CardContent>
      </Card>

    </div>
  );
}
