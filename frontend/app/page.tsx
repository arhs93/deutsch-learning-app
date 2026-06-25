import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 p-8 text-center">
      <div>
        <h1 className="text-5xl font-bold tracking-tight mb-3">Deutsch Learning App</h1>
        <p className="text-xl text-muted-foreground max-w-xl">
          Learn German from content you love — PDFs, movie transcripts, YouTube videos, and more.
        </p>
      </div>
      <div className="flex gap-4">
        <Link href="/dashboard" className={cn(buttonVariants({ size: "lg" }))}>
          Go to Dashboard
        </Link>
        <Link href="/upload" className={cn(buttonVariants({ variant: "outline", size: "lg" }))}>
          Upload Document
        </Link>
      </div>
    </main>
  );
}
