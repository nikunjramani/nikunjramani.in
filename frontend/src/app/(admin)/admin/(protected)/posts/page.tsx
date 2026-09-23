import { FileText } from "lucide-react";

// Stub — writing (posts/blog) is wired up in Phase 8, per the plan. The backend domain and
// schema already exist; this just isn't a screen worth building until there's a writing
// workflow to design around.
export default function AdminPostsPage() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-24 text-center text-muted-foreground">
      <FileText className="h-8 w-8" aria-hidden="true" />
      <p className="font-medium text-foreground">Posts aren&apos;t built yet</p>
      <p className="max-w-sm text-sm">
        Writing is planned for Phase 8, once there&apos;s a publishing workflow worth designing around.
      </p>
    </div>
  );
}
