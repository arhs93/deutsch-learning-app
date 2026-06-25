"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api, type Flashcard } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const DEMO_USER_ID = "00000000-0000-0000-0000-000000000001";

// SM-2 quality values
const RATINGS = [
  { label: "Again", quality: 0, color: "border-red-300 hover:bg-red-50 text-red-700" },
  { label: "Hard", quality: 2, color: "border-orange-300 hover:bg-orange-50 text-orange-700" },
  { label: "Good", quality: 4, color: "border-blue-300 hover:bg-blue-50 text-blue-700" },
  { label: "Easy", quality: 5, color: "border-green-300 hover:bg-green-50 text-green-700" },
];

export default function FlashcardsPage() {
  const { id } = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const limitParam = parseInt(searchParams.get("limit") || "10", 10);
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [current, setCurrent] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [done, setDone] = useState(false);
  const [reviewed, setReviewed] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDueFlashcards(DEMO_USER_ID, id)
      .then((fcs) => setCards(fcs.slice(0, limitParam)))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  async function rate(quality: number) {
    const card = cards[current];
    await api.reviewFlashcard(card.flashcard_id, quality);
    setReviewed((r) => r + 1);
    if (current + 1 >= cards.length) {
      setDone(true);
    } else {
      setCurrent((c) => c + 1);
      setFlipped(false);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <p className="text-muted-foreground">Loading flashcards…</p>
      </div>
    );
  }

  if (cards.length === 0 || done) {
    return (
      <div className="max-w-xl mx-auto p-6 text-center space-y-6">
        <div className="text-6xl">✅</div>
        <h1 className="text-2xl font-bold">{done ? "All done!" : "No cards due"}</h1>
        <p className="text-muted-foreground">
          {done
            ? `You reviewed ${reviewed} card${reviewed !== 1 ? "s" : ""}. Come back tomorrow for your next session.`
            : "You have no flashcards due for review right now. Check back tomorrow!"}
        </p>
        <Link href={`/documents/${id}/exercises`} className={cn(buttonVariants())}>
          Back to Exercises
        </Link>
      </div>
    );
  }

  const card = cards[current];
  const progress = Math.round((current / cards.length) * 100);

  return (
    <div className="max-w-xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link href={`/documents/${id}/exercises`} className="text-sm text-muted-foreground hover:underline">
          ✕ Exit
        </Link>
        <span className="text-sm text-muted-foreground">{current + 1} / {cards.length}</span>
      </div>

      {/* Progress */}
      <div className="w-full bg-muted rounded-full h-2">
        <div className="bg-primary h-2 rounded-full transition-all" style={{ width: `${progress}%` }} />
      </div>

      {/* Card */}
      <div
        className="cursor-pointer select-none"
        onClick={() => setFlipped((f) => !f)}
      >
        <Card className={cn(
          "border-2 min-h-[240px] flex items-center justify-center transition-all",
          flipped ? "border-primary/30 bg-primary/5" : "border-border hover:border-primary/30",
        )}>
          <CardContent className="py-8 text-center space-y-3">
            {!flipped ? (
              <>
                <p className="text-3xl font-bold">{card.german_word}</p>
                {card.gender && (
                  <p className="text-muted-foreground text-sm">{card.gender} · {card.part_of_speech}</p>
                )}
                {card.cefr_level && (
                  <span className="inline-block text-xs bg-muted px-2 py-0.5 rounded-full">{card.cefr_level}</span>
                )}
                <p className="text-sm text-muted-foreground mt-4">Tap to reveal translation</p>
              </>
            ) : (
              <>
                <p className="text-2xl font-semibold text-primary">{card.translation_en}</p>
                {card.example_sentence && (
                  <p className="text-sm italic text-muted-foreground mt-2">"{card.example_sentence}"</p>
                )}
                <div className="text-xs text-muted-foreground mt-3">
                  Reviewed {card.times_correct + card.times_incorrect} times · {card.times_correct} correct
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Rating buttons — only show after flip */}
      {flipped ? (
        <div>
          <p className="text-xs text-center text-muted-foreground mb-3">How well did you know it?</p>
          <div className="grid grid-cols-4 gap-2">
            {RATINGS.map((r) => (
              <button
                key={r.quality}
                onClick={() => rate(r.quality)}
                className={cn(
                  "py-2 px-3 rounded-lg border-2 font-medium text-sm transition-colors",
                  r.color,
                )}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <p className="text-center text-sm text-muted-foreground">Tap the card to see the answer</p>
      )}
    </div>
  );
}
