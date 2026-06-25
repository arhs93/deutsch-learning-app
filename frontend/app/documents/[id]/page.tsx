"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, type Document, type VocabularyItem, type GrammarPattern } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const POLL_INTERVAL_MS = 3000;

const PATTERN_TYPE_LABELS: Record<string, string> = {
  um_zu: "um…zu (Purpose clause)",
  modal_verb: "Modal Verb",
  separable_verb: "Separable Verb",
  subordinate_clause: "Subordinate Clause",
  dative_case: "Dative Case",
  accusative_case: "Accusative Case",
  genitive_case: "Genitive Case",
  passive_voice: "Passive Voice",
  konjunktiv_ii: "Konjunktiv II",
  relative_clause: "Relative Clause",
  weil_clause: "weil Clause",
  dass_clause: "dass Clause",
  idiom: "Idiom",
  common_phrase: "Common Phrase",
};

const DIFFICULTY_COLORS = [
  "",
  "bg-green-100 text-green-800",
  "bg-blue-100 text-blue-800",
  "bg-yellow-100 text-yellow-800",
  "bg-orange-100 text-orange-800",
  "bg-red-100 text-red-800",
];

export default function DocumentPage() {
  const { id } = useParams<{ id: string }>();
  const [doc, setDoc] = useState<Document | null>(null);
  const [vocabulary, setVocabulary] = useState<VocabularyItem[]>([]);
  const [grammar, setGrammar] = useState<GrammarPattern[]>([]);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    api
      .getDocument(id)
      .then((d) => {
        setDoc(d);
        setLoading(false);
        if (d.processing_status === "ready") {
          loadAnalysis();
        } else if (d.processing_status !== "failed") {
          startPolling();
        }
      })
      .catch(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  function startPolling() {
    setPolling(true);
    const interval = setInterval(async () => {
      try {
        const status = await api.getDocumentStatus(id);
        if (status.status === "ready" || status.status === "failed") {
          clearInterval(interval);
          setPolling(false);
          const updated = await api.getDocument(id);
          setDoc(updated);
          if (status.status === "ready") loadAnalysis();
        }
      } catch {
        clearInterval(interval);
        setPolling(false);
      }
    }, POLL_INTERVAL_MS);
  }

  async function loadAnalysis() {
    const [vocab, gram] = await Promise.all([api.getVocabulary(id), api.getGrammar(id)]);
    setVocabulary(vocab);
    setGrammar(gram);
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <p className="text-muted-foreground">Loading…</p>
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="p-6">
        <p>Document not found.</p>
        <Link href="/dashboard" className="text-primary underline">
          Back to dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link href="/dashboard" className="text-sm text-muted-foreground hover:underline">
            ← Dashboard
          </Link>
          <h1 className="text-2xl font-bold mt-1">{doc.title}</h1>
          <div className="flex gap-2 mt-2">
            <Badge variant="outline">{doc.source_type}</Badge>
            {doc.word_count && (
              <Badge variant="outline">{doc.word_count.toLocaleString()} words</Badge>
            )}
            <Badge
              variant={
                doc.processing_status === "ready"
                  ? "default"
                  : doc.processing_status === "failed"
                  ? "destructive"
                  : "secondary"
              }
            >
              {doc.processing_status}
            </Badge>
          </div>
        </div>
        {doc.processing_status === "ready" && (
          <Link href={`/documents/${id}/exercises`} className={cn(buttonVariants())}>
            Start Exercises
          </Link>
        )}
      </div>

      {/* Processing indicator */}
      {polling && (
        <Card>
          <CardContent className="py-6 text-center">
            <div className="flex items-center justify-center gap-3">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary" />
              <p className="text-muted-foreground">Analyzing your document with AI… This takes 1–3 minutes.</p>
            </div>
          </CardContent>
        </Card>
      )}

      {doc.processing_status === "failed" && (
        <Card>
          <CardContent className="py-6 text-center">
            <p className="text-destructive">Analysis failed. Please try uploading the document again.</p>
          </CardContent>
        </Card>
      )}

      {doc.processing_status === "ready" && (
        <Tabs defaultValue="vocabulary">
          <TabsList>
            <TabsTrigger value="vocabulary">Vocabulary ({vocabulary.length})</TabsTrigger>
            <TabsTrigger value="grammar">Grammar Patterns ({grammar.length})</TabsTrigger>
            <TabsTrigger value="text">Extracted Text</TabsTrigger>
          </TabsList>

          {/* Vocabulary Tab */}
          <TabsContent value="vocabulary" className="mt-4">
            {vocabulary.length === 0 ? (
              <p className="text-muted-foreground">No vocabulary extracted yet.</p>
            ) : (
              <div className="grid gap-3">
                {vocabulary.map((v) => (
                  <Card key={v.id} className="hover:shadow-sm transition-shadow">
                    <CardContent className="py-3 flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-lg">{v.german_word}</span>
                          {v.gender && (
                            <Badge variant="outline" className="text-xs">
                              {v.gender}
                            </Badge>
                          )}
                          {v.cefr_level && (
                            <span
                              className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                                v.difficulty ? DIFFICULTY_COLORS[v.difficulty] : ""
                              }`}
                            >
                              {v.cefr_level}
                            </span>
                          )}
                        </div>
                        <p className="text-muted-foreground">{v.translation_en}</p>
                        {v.example_sentence && (
                          <p className="text-sm italic mt-1 text-muted-foreground">
                            &quot;{v.example_sentence}&quot;
                          </p>
                        )}
                      </div>
                      <div className="text-right shrink-0">
                        {v.part_of_speech && (
                          <Badge variant="secondary" className="text-xs">
                            {v.part_of_speech}
                          </Badge>
                        )}
                        {v.frequency_in_doc > 1 && (
                          <p className="text-xs text-muted-foreground mt-1">×{v.frequency_in_doc}</p>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Grammar Tab */}
          <TabsContent value="grammar" className="mt-4">
            {grammar.length === 0 ? (
              <p className="text-muted-foreground">No grammar patterns detected yet.</p>
            ) : (
              <div className="grid gap-4">
                {grammar.map((p) => (
                  <Card key={p.id}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <CardTitle className="text-base">{p.pattern_name}</CardTitle>
                        <Badge variant="outline" className="text-xs">
                          {PATTERN_TYPE_LABELS[p.pattern_type] || p.pattern_type}
                        </Badge>
                        {p.difficulty && (
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                              DIFFICULTY_COLORS[p.difficulty]
                            }`}
                          >
                            Level {p.difficulty}
                          </span>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div>
                        <p className="text-xs font-semibold uppercase text-muted-foreground mb-1">Rule</p>
                        <p className="text-sm">{p.rule_summary}</p>
                      </div>
                      <div>
                        <p className="text-xs font-semibold uppercase text-muted-foreground mb-1">
                          Why it&apos;s used here
                        </p>
                        <p className="text-sm">{p.explanation}</p>
                      </div>
                      <div className="bg-muted rounded-md p-3">
                        <p className="text-sm font-medium">{p.example_from_doc}</p>
                        <p className="text-sm text-muted-foreground italic mt-1">{p.example_translation}</p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Raw Text Tab */}
          <TabsContent value="text" className="mt-4">
            <Card>
              <CardContent className="pt-4">
                <pre className="whitespace-pre-wrap text-sm font-mono max-h-96 overflow-y-auto text-muted-foreground">
                  {doc.raw_text || "No text extracted."}
                </pre>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {doc.processing_status === "pending" && !polling && (
        <Card>
          <CardContent className="py-6 text-center">
            <p className="text-muted-foreground">Document queued for analysis…</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
