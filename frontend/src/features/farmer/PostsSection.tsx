import { type FormEvent, useState } from "react";

import { useAddComment, useComments, usePosts } from "../../api/hooks/usePosts";
import { Button } from "../../design/ui/Button";
import { Card } from "../../design/ui/Card";
import { EmptyState } from "../../design/ui/EmptyState";
import { Field } from "../../design/ui/Field";

function CommentThread({ postId }: { postId: number }) {
  const { data: comments } = useComments(postId);
  const addComment = useAddComment(postId);
  const [body, setBody] = useState("");

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!body.trim()) return;
    addComment.mutate(body, { onSuccess: () => setBody("") });
  }

  return (
    <div className="mt-2 flex flex-col gap-2 border-t border-rule pt-2">
      {comments?.map((c) => (
        <p key={c.id} className="text-sm text-ink">
          <span className="font-medium">{c.author_name}:</span> {c.body}
        </p>
      ))}
      <form onSubmit={onSubmit} className="flex gap-2">
        <Field label="Comment" hideLabel value={body} onChange={(e) => setBody(e.target.value)}
          placeholder="Add a comment…" className="flex-1" />
        <Button type="submit" variant="secondary" disabled={addComment.isPending} className="self-end px-3 py-2 text-sm">
          Send
        </Button>
      </form>
    </div>
  );
}

export function PostsSection() {
  const { data: posts, isLoading } = usePosts();
  const [openId, setOpenId] = useState<number | null>(null);

  return (
    <Card title="From your officers">
      {isLoading ? (
        <p className="text-soft">Loading…</p>
      ) : !posts || posts.length === 0 ? (
        <EmptyState title="No announcements yet." />
      ) : (
        posts.map((p) => (
          <div key={p.id} className="border-t border-rule pt-3 first:border-0 first:pt-0">
            <p className="text-sm font-medium text-ink">{p.title}</p>
            <p className="text-sm text-ink">{p.body}</p>
            <button onClick={() => setOpenId(openId === p.id ? null : p.id)} className="mt-1 text-xs font-medium text-leaf">
              {p.comment_count} comment{p.comment_count === 1 ? "" : "s"}
            </button>
            {openId === p.id && <CommentThread postId={p.id} />}
          </div>
        ))
      )}
    </Card>
  );
}
