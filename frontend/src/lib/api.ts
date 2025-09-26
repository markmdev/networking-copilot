import { PersonDetail, PersonListItem } from "../types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json() as Promise<T>;
}

export async function fetchPeople(limit = 50): Promise<PersonListItem[]> {
  const url = new URL("/people", API_BASE_URL);
  url.searchParams.set("limit", String(limit));
  const res = await fetch(url.toString(), { cache: "no-store" });
  const data = await handleResponse<{ people: PersonListItem[] }>(res);
  return data.people ?? [];
}

export async function fetchPerson(id: string): Promise<PersonDetail> {
  const url = new URL(`/people/${id}`, API_BASE_URL);
  const res = await fetch(url.toString(), { cache: "no-store" });
  return handleResponse<PersonDetail>(res);
}

export async function uploadExtractAndLookup(file: Blob): Promise<PersonDetail> {
  const formData = new FormData();
  formData.append("file", file, file instanceof File ? file.name : "capture.jpg");

  const res = await fetch(new URL("/extract-and-lookup", API_BASE_URL).toString(), {
    method: "POST",
    body: formData,
  });

  return handleResponse<PersonDetail>(res);
}