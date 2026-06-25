"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, type Exercise } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const DEMO_USER_ID = "00000000-0000-0000-0000-000000000001";

const TYPE_COUNTS: Record<string, { label: string; desc: string; color: string }> = {
  multiple_choice: { label: "Multiple Choice", desc: "Pick the correct German translation", color: "bg-blue-50 border-blue-200" },
  fill_blank: { label: "Fill in the Blank", desc: "Complete the sentence with the right word", color: "bg-green-50 border-green-200" },
  translation_en_de: { label: "Translate EN → DE", desc: "Translate English sentences into German", color: "bg-purple-50 border-purple-200" },
  translation_de_en: { label: "Translate DE → EN", desc: "Translate German sentences into English", color: "bg-orange-50 border-orange-200" },
  sentence_builder: { label: "Sentence Builder", desc: "Arrange scrambled words into a correct sentence", color: "bg-yellow-50 border-yellow-200" },
};

const SESSION_LIMITS = [5, 10, 20, 50];

export default function ExercisesHubPage() {
  const { id } = useParams<{ id: string }>();
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [flashcardCount, setFlashcardCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [sessionLimit, setSessionLimit] = useState(10);

  useEffect(() => {
    Promise.all([
      api.getExercises({ document_id: id, limit: "100" }),
      api.getDueFlashcards(DEMO_USER_ID, id),
    ])
      .then(([exs, fcs]) => {
        setExercises(exs);
        setFlashcardCount(fcs.length);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  const byType = exercises.reduce<Record<string, number>>((acc, e) => {
    acc[e.exercise_type] = (acc[e.exercise_type] || 0) + 1;
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <p className="text-muted-foreground">Loading exercises…</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-8">
      <div>
        <Link href={`/documents/${id}`} className="text-sm text-muted-foreground hover:underline">
          ← Back to document
        </Link>
        <h1 className="text-2xl font-bold mt-2">Choose Your Exercise</h1>
        <p className="text-muted-foreground mt-1">{exercises.length} exercises available from this document</p>
      </div>

      {/* Session length picker */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-muted-foreground">Session length:</span>
        <div className="flex gap-2">
          {SESSION_LIMITS.map((n) => (
            <button
              key={n}
              onClick={() => setSessionLimit(n)}
              className={cn(
                "px-3 py-1 rounded-full text-sm border-2 transition-colors",
                sessionLimit === n
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border hover:border-primary/50",
              )}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      {/* Flashcards */}
      <Card className="border-2 border-primary/20 bg-primary/5">
        <CardContent className="py-5 flex items-center justify-between gap-4">
          <div>
            <p className="font-semibold text-lg">Flashcards</p>
            <p className="text-sm text-muted-foreground">Spaced repetition — review words at the right time</p>
            <p className="text-xs mt-1 font-medium text-primary">{flashcardCount} cards due today</p>
          </div>
          <Link
            href={`/documents/${id}/flashcards?limit=${sessionLimit}`}
            className={cn(buttonVariants({ size: "sm" }), flashcardCount === 0 && "opacity-50 pointer-events-none")}
          >
            {flashcardCount > 0 ? "Start Review" : "All caught up"}
          </Link>
        </CardContent>
      </Card>

      {/* Practice all */}
      {exercises.length > 0 && (
        <Card className="border-2 border-green-200 bg-green-50">
          <CardContent className="py-5 flex items-center justify-between gap-4">
            <div>
              <p className="font-semibold text-lg">Practice Session</p>
              <p className="text-sm text-muted-foreground">Mixed exercises from this document — all types</p>
              <p className="text-xs mt-1 font-medium text-green-700">{exercises.length} exercises total</p>
            </div>
            <Link href={`/documents/${id}/exercises/practice?limit=${sessionLimit}`} className={cn(buttonVariants({ size: "sm" }))}>
              Start
            </Link>
          </CardContent>
        </Card>
      )}

      {/* By type */}
      <div>
        <h2 className="text-sm font-semibold uppercase text-muted-foreground mb-3">By Exercise Type</h2>
        <div className="grid gap-3">
          {Object.entries(TYPE_COUNTS)
            .filter(([type]) => byType[type])
            .map(([type, meta]) => (
              <Card key={type} className={`border ${meta.color}`}>
                <CardContent className="py-4 flex items-center justify-between gap-4">
                  <div>
                    <p className="font-medium">{meta.label}</p>
                    <p className="text-sm text-muted-foreground">{meta.desc}</p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-sm text-muted-foreground">{byType[type]} exercises</span>
                    <Link
                      href={`/documents/${id}/exercises/practice?type=${type}&limit=${sessionLimit}`}
                      className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
                    >
                      Start
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
        </div>
      </div>

      {exercises.length === 0 && flashcardCount === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No exercises generated yet.</p>
            <Link href={`/documents/${id}`} className="text-primary hover:underline text-sm mt-2 inline-block">
              Back to document
            </Link>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
