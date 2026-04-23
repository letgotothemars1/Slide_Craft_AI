const STORAGE_KEY = "ai-pres-history";

export interface HistoryEntry {
  job_id: string;
  prompt_snippet: string;
  created_at: string;
  status: string;
}

export function getHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function addToHistory(entry: HistoryEntry) {
  const list = getHistory().filter((e) => e.job_id !== entry.job_id);
  list.unshift(entry);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(0, 50)));
}

export function updateHistoryStatus(jobId: string, status: string) {
  const list = getHistory();
  const idx = list.findIndex((e) => e.job_id === jobId);
  if (idx !== -1) {
    list[idx].status = status;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  }
}
