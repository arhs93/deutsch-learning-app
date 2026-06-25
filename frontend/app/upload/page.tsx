"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const DEMO_USER_ID = "00000000-0000-0000-0000-000000000001";

const SOURCE_TYPES = [
  { value: "pdf", label: "PDF" },
  { value: "transcript_youtube", label: "YouTube Transcript" },
  { value: "transcript_movie", label: "Movie/TV Transcript (.srt)" },
  { value: "article", label: "Article" },
  { value: "book_excerpt", label: "Book Excerpt" },
];

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [sourceType, setSourceType] = useState("pdf");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) {
      setFile(accepted[0]);
      if (!title) setTitle(accepted[0].name.replace(/\.[^/.]+$/, ""));
    }
  }, [title]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "text/plain": [".txt"], "application/x-subrip": [".srt"] },
    maxFiles: 1,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !title.trim()) return;

    setUploading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", title.trim());
      formData.append("source_type", sourceType);
      formData.append("user_id", DEMO_USER_ID);

      const result = await api.uploadDocument(formData);
      router.push(`/documents/${result.document_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Upload Document</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Select File</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors ${
                isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/30 hover:border-primary/50"
              }`}
            >
              <input {...getInputProps()} />
              {file ? (
                <div>
                  <p className="font-medium">{file.name}</p>
                  <p className="text-sm text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              ) : (
                <div>
                  <p className="text-lg mb-1">Drop your file here</p>
                  <p className="text-sm text-muted-foreground">PDF, TXT, or SRT — up to 50 MB</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Document Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-1 block">Title</label>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Dark Season 1 Episode 1"
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Source Type</label>
              <div className="flex flex-wrap gap-2">
                {SOURCE_TYPES.map((st) => (
                  <button
                    key={st.value}
                    type="button"
                    onClick={() => setSourceType(st.value)}
                    className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                      sourceType === st.value
                        ? "bg-primary text-primary-foreground border-primary"
                        : "border-input hover:bg-muted"
                    }`}
                  >
                    {st.label}
                  </button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {error && <p className="text-destructive text-sm">{error}</p>}

        <Button type="submit" disabled={!file || !title.trim() || uploading} className="w-full" size="lg">
          {uploading ? "Uploading and analyzing…" : "Upload & Start Learning"}
        </Button>
      </form>
    </div>
  );
}
