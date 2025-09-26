export type PersonListItem = {
  id: string;
  name: string;
  subtitle?: string | null;
  location?: string | null;
  avatar?: string | null;
  created_at?: string;
};

export type ExtractedLinks = {
  linkedin?: string | null;
  github?: string | null;
  website?: string | null;
  email?: string | null;
  phone?: string | null;
};

export type ExtractedBasicInfo = {
  names?: string | null;
  company?: string | null;
};

export type ExtractedData = {
  basic_info?: ExtractedBasicInfo;
  links?: ExtractedLinks;
  image?: string | null;
};

export type AnalyzerOutput = {
  profile_name?: string;
  headline?: string | null;
  current_title?: string | null;
  current_company?: string | null;
  location?: string | null;
  highlights: string[];
};

export type SummaryOutput = {
  summary: string;
  key_highlights: string[];
};

export type IcebreakerItem = {
  category: string;
  prompt: string;
};

export type CrewOutputs = {
  linkedin_profile_analyzer_task: AnalyzerOutput;
  summary_generator_task: SummaryOutput;
  icebreaker_generator_task: {
    icebreakers: IcebreakerItem[];
  };
};

export type PersonDetail = {
  id: string;
  created_at?: string;
  filename?: string;
  extracted?: ExtractedData;
  person: {
    url?: string | null;
    name: string;
    subtitle?: string | null;
    location?: string | null;
    experience?: string | null;
    education?: string | null;
    avatar?: string | null;
  };
  selector_rationale?: string | null;
  crew_outputs: CrewOutputs;
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
