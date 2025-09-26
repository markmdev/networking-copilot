/**
 * Backend API client for Networking Copilot
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export interface ExtractedData {
  basic_info: {
    names: string;
    company: string;
  };
  links: {
    linkedin?: string;
    github?: string;
    website?: string;
    email?: string;
    phone?: string;
  };
  image: string;
}

export interface ProfileData {
  url: string;
  name: string;
  subtitle: string;
  location: string;
  experience: string;
  education: string;
  avatar: string;
}

export interface CrewOutputs {
  linkedin_profile_analyzer_task: {
    profile_name: string;
    headline: string;
    current_title: string;
    current_company: string;
    location: string;
    highlights: string[];
  };
  summary_generator_task: {
    summary: string;
    key_highlights: string[];
  };
  icebreaker_generator_task: {
    icebreakers: Array<{
      category: "professional" | "educational" | "industry" | "interest" | "personal";
      prompt: string;
    }>;
  };
}

export interface ExtractAndLookupResponse {
  filename: string;
  markdown: string;
  person: ProfileData;
  selector_rationale: string;
  crew_outputs: CrewOutputs;
}

export interface ExtractImageResponse {
  filename: string;
  extracted: ExtractedData;
  markdown: string;
}

class NetworkingAPI {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  /**
   * Health check endpoint
   */
  async health(): Promise<{ status: string }> {
    try {
      console.log(`Checking health at: ${this.baseURL}/health`);

      // Add timeout and better error handling
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

      const response = await fetch(`${this.baseURL}/health`, {
        signal: controller.signal,
        headers: {
          Accept: "application/json",
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status} ${response.statusText}`);
      }
      const result = await response.json();
      console.log("Health check successful:", result);
      return result;
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === "AbortError") {
          console.error("Health check timed out - backend server may not be running");
        } else if (error.message.includes("Failed to fetch")) {
          console.error("Cannot connect to backend - is the server running at", this.baseURL, "?");
        }
      }
      console.error("Health check failed:", error);
      throw error;
    }
  }

  /**
   * Extract structured data from an uploaded image
   */
  async extractImage(file: File): Promise<ExtractImageResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${this.baseURL}/extract-image`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(`Extract image failed: ${errorData.detail || response.statusText}`);
    }

    return response.json();
  }

  /**
   * One-shot pipeline: extract image, find LinkedIn profile, and run crew analysis
   */
  async extractAndLookup(file: File): Promise<ExtractAndLookupResponse> {
    try {
      console.log(`Uploading image to: ${this.baseURL}/extract-and-lookup`);
      console.log("File details:", { name: file.name, type: file.type, size: file.size });

      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${this.baseURL}/extract-and-lookup`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("=== BACKEND ERROR DETAILS ===");
        console.error("Status:", response.status, response.statusText);
        console.error("Headers:", Object.fromEntries(response.headers.entries()));
        console.error("Raw Response:", errorText);
        console.error("==============================");

        let errorData;
        try {
          errorData = JSON.parse(errorText);
          console.error("Parsed Error:", errorData);
        } catch {
          errorData = { detail: errorText || "Unknown error" };
          console.error("Failed to parse error as JSON");
        }

        throw new Error(
          `Extract and lookup failed (${response.status}): ${
            errorData.detail || response.statusText
          }`
        );
      }

      const result = await response.json();
      console.log("Extract and lookup successful:", result);
      return result;
    } catch (error) {
      console.error("Extract and lookup failed:", error);
      throw error;
    }
  }

  /**
   * Search for LinkedIn profiles by name
   */
  async searchProfiles(firstName: string, lastName: string, additionalContext?: string) {
    const payload = {
      first_name: firstName,
      last_name: lastName,
      additional_context: additionalContext,
    };

    const response = await fetch(`${this.baseURL}/search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(`Search failed: ${errorData.detail || response.statusText}`);
    }

    return response.json();
  }
}

export const networkingAPI = new NetworkingAPI();
