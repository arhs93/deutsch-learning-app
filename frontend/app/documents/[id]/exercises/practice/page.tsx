"use client";

import { useEffect, useState, useRef, useMemo } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api, type Exercise, type AttemptResult } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const DEMO_USER_ID = "00000000-0000-0000-0000-000000000001";

type Status = "answering" | "correct" | "wrong";

export default function PracticeSessionPage() {
  const { id } = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const filterType = searchParams.get("type") || undefined;
  const limitParam = parseInt(searchParams.get("limit") || "10", 10);

  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [current, setCurrent] = useState(0);
  const [status, setStatus] = useState<Status>("answering");
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [userAnswer, setUserAnswer] = useState("");
  const [selectedChoice, setSelectedChoice] = useState<string | null>(null);
  const [sessionXp, setSessionXp] = useState(0);
  const [correct, setCorrect] = useState(0);
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(true);
  const [hintVisible, setHintVisible] = useState(false);
  const startTime = useRef<number>(Date.now());
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const params: Record<string, string> = { document_id: id, limit: "100" };
    if (filterType) params.exercise_type = filterType;
    api.getExercises(params)
      .then((exs) => {
        const shuffled = exs.sort(() => Math.random() - 0.5);
        setExercises(shuffled.slice(0, limitParam));
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id, filterType]);

  useEffect(() => {
    if (status === "answering" && inputRef.current) {
      inputRef.current.focus();
    }
  }, [current, status]);

  const exercise = exercises[current];

  async function submit(answer: string) {
    if (!answer.trim() || !exercise) return;
    const elapsed = Date.now() - startTime.current;
    const res = await api.submitAttempt({
      exercise_id: exercise.id,
      user_id: DEMO_USER_ID,
      user_answer: answer,
      time_spent_ms: elapsed,
    });
    setResult(res);
    setStatus(res.is_correct ? "correct" : "wrong");
    if (res.is_correct) setCorrect((c) => c + 1);
    setSessionXp((xp) => xp + res.xp_earned);
    startTime.current = Date.now();
  }

  function next() {
    if (current + 1 >= exercises.length) {
      setDone(true);
    } else {
      setCurrent((c) => c + 1);
      setStatus("answering");
      setResult(null);
      setUserAnswer("");
      setSelectedChoice(null);
      setHintVisible(false);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <p className="text-muted-foreground">Loading exercises…</p>
      </div>
    );
  }

  if (exercises.length === 0) {
    return (
      <div className="max-w-xl mx-auto p-6 text-center space-y-4">
        <p className="text-muted-foreground">No exercises found.</p>
        <Link href={`/documents/${id}/exercises`} className={cn(buttonVariants({ variant: "outline" }))}>
          Back
        </Link>
      </div>
    );
  }

  if (done) {
    const accuracy = Math.round((correct / exercises.length) * 100);
    return (
      <div className="max-w-xl mx-auto p-6 space-y-6 text-center">
        <div className="text-6xl">{accuracy >= 80 ? "🎉" : accuracy >= 50 ? "👍" : "💪"}</div>
        <h1 className="text-2xl font-bold">Session Complete!</h1>
        <div className="grid grid-cols-3 gap-4">
          <Card><CardContent className="py-4"><p className="text-2xl font-bold">{correct}/{exercises.length}</p><p className="text-xs text-muted-foreground">Correct</p></CardContent></Card>
          <Card><CardContent className="py-4"><p className="text-2xl font-bold">{accuracy}%</p><p className="text-xs text-muted-foreground">Accuracy</p></CardContent></Card>
          <Card><CardContent className="py-4"><p className="text-2xl font-bold text-primary">+{sessionXp}</p><p className="text-xs text-muted-foreground">XP earned</p></CardContent></Card>
        </div>
        <div className="flex gap-3 justify-center">
          <Link href={`/documents/${id}/exercises`} className={cn(buttonVariants({ variant: "outline" }))}>
            Back to Exercises
          </Link>
          <button onClick={() => { setCurrent(0); setStatus("answering"); setResult(null); setUserAnswer(""); setSelectedChoice(null); setSessionXp(0); setCorrect(0); setDone(false); setExercises((e) => e.sort(() => Math.random() - 0.5)); }} className={cn(buttonVariants())}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const progress = Math.round((current / exercises.length) * 100);

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link href={`/documents/${id}/exercises`} className="text-sm text-muted-foreground hover:underline">
          ✕ Exit
        </Link>
        <span className="text-sm font-medium text-primary">+{sessionXp} XP</span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-muted rounded-full h-2">
        <div className="bg-primary h-2 rounded-full transition-all" style={{ width: `${progress}%` }} />
      </div>
      <p className="text-xs text-muted-foreground text-right">{current + 1} / {exercises.length}</p>

      {/* Exercise card */}
      <ExerciseCard
        exercise={exercise}
        status={status}
        result={result}
        userAnswer={userAnswer}
        setUserAnswer={setUserAnswer}
        selectedChoice={selectedChoice}
        setSelectedChoice={setSelectedChoice}
        hintVisible={hintVisible}
        setHintVisible={setHintVisible}
        inputRef={inputRef}
        onSubmit={submit}
        onNext={next}
      />
    </div>
  );
}

function ExerciseCard({
  exercise, status, result, userAnswer, setUserAnswer,
  selectedChoice, setSelectedChoice, hintVisible, setHintVisible, inputRef, onSubmit, onNext,
}: {
  exercise: Exercise;
  status: Status;
  result: AttemptResult | null;
  userAnswer: string;
  setUserAnswer: (v: string) => void;
  selectedChoice: string | null;
  setSelectedChoice: (v: string | null) => void;
  hintVisible: boolean;
  setHintVisible: (v: boolean) => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
  onSubmit: (answer: string) => void;
  onNext: () => void;
}) {
  const typeLabel: Record<string, string> = {
    multiple_choice: "Multiple Choice",
    fill_blank: "Fill in the Blank",
    translation_en_de: "Translate → German",
    translation_de_en: "Translate → English",
    sentence_builder: "Sentence Builder",
  };

  // Shuffle choices once per exercise (stable across re-renders)
  const choices = useMemo(
    () =>
      exercise.exercise_type === "multiple_choice" && exercise.distractors
        ? [...exercise.distractors, exercise.correct_answer].sort(() => Math.random() - 0.5)
        : [],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [exercise.id],
  );

  return (
    <Card className={cn(
      "border-2 transition-colors",
      status === "correct" && "border-green-400 bg-green-50",
      status === "wrong" && "border-red-300 bg-red-50",
      status === "answering" && "border-border",
    )}>
      <CardContent className="py-6 space-y-5">
        {/* Type badge */}
        <p className="text-xs font-semibold uppercase text-muted-foreground">
          {typeLabel[exercise.exercise_type] || exercise.exercise_type}
        </p>

        {/* Prompt */}
        <p className="text-lg font-medium leading-relaxed">{exercise.prompt}</p>


        {/* Input area */}
        {exercise.exercise_type === "multiple_choice" ? (
          <div className="grid grid-cols-1 gap-2">
            {choices.map((choice) => (
              <button
                key={choice}
                disabled={status !== "answering"}
                onClick={() => {
                  if (status !== "answering") return;
                  setSelectedChoice(choice);
                  onSubmit(choice);
                }}
                className={cn(
                  "text-left px-4 py-3 rounded-lg border-2 transition-colors text-sm",
                  status === "answering" && selectedChoice !== choice && "border-border hover:border-primary hover:bg-primary/5",
                  status === "answering" && selectedChoice === choice && "border-primary bg-primary/10",
                  status !== "answering" && choice === result?.correct_answer && "border-green-400 bg-green-100",
                  status !== "answering" && choice === selectedChoice && choice !== result?.correct_answer && "border-red-400 bg-red-100",
                  status !== "answering" && choice !== result?.correct_answer && choice !== selectedChoice && "border-border opacity-50",
                )}
              >
                {choice}
              </button>
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            <input
              ref={inputRef}
              type="text"
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && status === "answering") onSubmit(userAnswer); }}
              disabled={status !== "answering"}
              placeholder="Type your answer…"
              className={cn(
                "w-full px-4 py-3 rounded-lg border-2 text-sm outline-none transition-colors",
                status === "answering" && "border-border focus:border-primary",
                status === "correct" && "border-green-400 bg-green-50",
                status === "wrong" && "border-red-400 bg-red-50",
              )}
            />
            {status === "answering" && (
              <button
                onClick={() => onSubmit(userAnswer)}
                disabled={!userAnswer.trim()}
                className={cn(buttonVariants(), "w-full")}
              >
                Check
              </button>
            )}
          </div>
        )}

        {/* Result feedback */}
        {status !== "answering" && result && (
          <div className={cn(
            "rounded-lg p-4 space-y-1",
            status === "correct" ? "bg-green-100" : "bg-red-100",
          )}>
            <p className={cn("font-semibold", status === "correct" ? "text-green-800" : "text-red-800")}>
              {status === "correct" ? `Correct! +${result.xp_earned} XP` : `Incorrect — correct answer: ${result.correct_answer}`}
            </p>
            {result.explanation && (
              <p className="text-sm text-muted-foreground">{result.explanation}</p>
            )}
          </div>
        )}

        {/* Next button */}
        {status !== "answering" && (
          <button onClick={onNext} className={cn(buttonVariants(), "w-full")}>
            Continue →
          </button>
        )}
      </CardContent>
    </Card>
  );
}
