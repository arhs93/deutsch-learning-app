"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type Document, type ProgressData } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const DEMO_USER_ID = "00000000-0000-0000-0000-000000000001";

export default function DashboardPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.listDocuments(DEMO_USER_ID),
      api.getProgress(DEMO_USER_ID),
    ])
      .then(([docs, prog]) => {
        setDocuments(docs);
        setProgress(prog);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(docId: string, title: string) {
    if (!confirm(`Delete "${title}"? This cannot be undone.`)) return;
    setDeleting(docId);
    try {
      await api.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (e) {
      alert("Failed to delete document.");
    } finally {
      setDeleting(null);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-muted-foreground">Loading…</p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <Link href="/upload" className={cn(buttonVariants())}>
          + Upload Document
        </Link>
      </div>

      {/* Gamification bar */}
      {progress && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">Level</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{progress.level}</p>
              <Progress
                value={Math.max(0, 100 - (progress.xp_to_next_level / (progress.level * 150)) * 100)}
                className="mt-2"
              />
              <p className="text-xs text-muted-foreground mt-1">{progress.xp_to_next_level} XP to next level</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">Streak</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{progress.streak_days} days</p>
              <p className="text-xs text-muted-foreground mt-1">Best: {progress.longest_streak} days</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">Total XP</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{progress.total_xp.toLocaleString()}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Documents */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Your Documents</h2>
        {documents.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground mb-4">No documents yet. Upload your first German text to get started.</p>
              <Link href="/upload" className={cn(buttonVariants())}>Upload Document</Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {documents.map((doc) => (
              <Card key={doc.id} className="hover:shadow-md transition-shadow">
                <CardContent className="flex items-center justify-between py-4">
                  <div>
                    <p className="font-semibold">{doc.title}</p>
                    <div className="flex gap-2 mt-1 flex-wrap">
                      <Badge variant="outline">{doc.source_type}</Badge>
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
                      {doc.word_count && (
                        <Badge variant="outline">{doc.word_count.toLocaleString()} words</Badge>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    {doc.processing_status === "ready" && (
                      <Link
                        href={`/documents/${doc.id}`}
                        className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
                      >
                        Study
                      </Link>
                    )}
                    <button
                      onClick={() => handleDelete(doc.id, doc.title)}
                      disabled={deleting === doc.id}
                      className="text-sm px-3 py-1 rounded-md border border-destructive/40 text-destructive hover:bg-destructive/10 transition-colors disabled:opacity-50"
                    >
                      {deleting === doc.id ? "Deleting…" : "Delete"}
                    </button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
