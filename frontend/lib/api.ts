const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(error || `API error ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Documents
  uploadDocument: (formData: FormData) =>
    fetch(`${API_URL}/api/v1/documents/upload`, { method: "POST", body: formData }).then((r) => r.json()),

  listDocuments: (userId: string) =>
    apiFetch<Document[]>(`/api/v1/documents?user_id=${userId}`),

  getDocument: (id: string) =>
    apiFetch<Document>(`/api/v1/documents/${id}`),

  getDocumentStatus: (id: string) =>
    apiFetch<{ status: string }>(`/api/v1/documents/${id}/status`),

  deleteDocument: (id: string) =>
    apiFetch(`/api/v1/documents/${id}`, { method: "DELETE" }),

  // Analysis
  getVocabulary: (documentId: string, params?: Record<string, string>) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch<VocabularyItem[]>(`/api/v1/documents/${documentId}/vocabulary${qs ? `?${qs}` : ""}`);
  },

  getGrammar: (documentId: string, patternType?: string) => {
    const qs = patternType ? `?pattern_type=${patternType}` : "";
    return apiFetch<GrammarPattern[]>(`/api/v1/documents/${documentId}/grammar${qs}`);
  },

  // Exercises
  getExercises: (params: Record<string, string>) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch<Exercise[]>(`/api/v1/exercises?${qs}`);
  },

  submitAttempt: (data: { exercise_id: string; user_id: string; user_answer: string; time_spent_ms?: number }) =>
    apiFetch<AttemptResult>("/api/v1/exercises/attempt", { method: "POST", body: JSON.stringify(data) }),

  // Flashcards
  getDueFlashcards: (userId: string, documentId?: string) => {
    const qs = new URLSearchParams({ user_id: userId, ...(documentId ? { document_id: documentId } : {}) }).toString();
    return apiFetch<Flashcard[]>(`/api/v1/flashcards/due?${qs}`);
  },

  reviewFlashcard: (flashcardId: string, quality: number) =>
    apiFetch(`/api/v1/flashcards/${flashcardId}/review`, { method: "POST", body: JSON.stringify({ quality }) }),

  getFlashcardStats: (userId: string) =>
    apiFetch<{ due_today: number; reviewed_today: number; total: number }>(`/api/v1/flashcards/stats?user_id=${userId}`),

  // Progress
  getProgress: (userId: string) =>
    apiFetch<ProgressData>(`/api/v1/progress?user_id=${userId}`),

  startSession: (data: { user_id: string; document_id?: string; session_type?: string }) =>
    apiFetch<{ session_id: string }>("/api/v1/sessions/start", { method: "POST", body: JSON.stringify(data) }),

  endSession: (sessionId: string, data: { exercises_done: number; accuracy_pct?: number }) =>
    apiFetch<SessionResult>(`/api/v1/sessions/${sessionId}/end`, { method: "POST", body: JSON.stringify(data) }),

  // Achievements
  getAchievements: (userId: string) =>
    apiFetch<AchievementItem[]>(`/api/v1/achievements?user_id=${userId}`),
};

// Types
export interface Document {
  id: string; title: string; source_type: string;
  processing_status: string; word_count?: number; created_at: string;
  raw_text?: string;
}
export interface VocabularyItem {
  id: string; german_word: string; lemma?: string; translation_en: string;
  part_of_speech?: string; gender?: string; plural_form?: string;
  difficulty?: number; cefr_level?: string; frequency_in_doc: number;
  example_sentence?: string;
}
export interface GrammarPattern {
  id: string; pattern_type: string; pattern_name: string;
  explanation: string; rule_summary: string; example_from_doc: string;
  example_translation: string; difficulty?: number; occurrences: number;
}
export interface Exercise {
  id: string; exercise_type: string; prompt: string;
  correct_answer: string; distractors?: string[]; hint?: string; difficulty?: number;
}
export interface Flashcard {
  flashcard_id: string; vocabulary_item_id: string; german_word: string;
  translation_en: string; gender?: string; part_of_speech?: string;
  cefr_level?: string; example_sentence?: string;
  ease_factor: number; interval_days: number; repetitions: number;
  times_correct: number; times_incorrect: number;
}
export interface AttemptResult {
  is_correct: boolean; correct_answer: string; explanation?: string;
  xp_earned: number; level_up: boolean; achievements_unlocked: AchievementItem[];
}
export interface ProgressData {
  level: number; total_xp: number; xp_to_next_level: number;
  streak_days: number; longest_streak: number;
  documents: { document_id: string; document_title: string; vocabulary_mastered: number;
    vocabulary_total: number; exercises_completed: number; completion_percentage: number; }[];
}
export interface AchievementItem {
  key: string; name: string; description: string; icon?: string;
  xp_reward: number; earned: boolean; earned_at?: string;
}
export interface SessionResult {
  xp_earned: number; level_up: boolean; achievements_unlocked: AchievementItem[];
  duration_seconds?: number;
}
