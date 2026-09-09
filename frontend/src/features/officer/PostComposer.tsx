import { type FormEvent, useState } from "react";

import { useCreatePost, usePosts } from "../../api/hooks/usePosts";
import { useAuth } from "../../app/AuthProvider";
import { Button } from "../../design/ui/Button";
import { Card } from "../../design/ui/Card";
import { EmptyState } from "../../design/ui/EmptyState";
import { Field } from "../../design/ui/Field";
import { Select } from "../../design/ui/Select";
import { useParishes } from "./useParishDashboard";

const OWN_SCOPE_LABEL: Record<string, string> = {
  national: "Everyone (national)",
  district: "My district",
  subcounty: "My subcounty",
  parish: "My parish",
};

function PostComposer() {
  const { me } = useAuth();
  const { data: parishes } = useParishes();
  const create = useCreatePost();
  const [target, setTarget] = useState<"own" | "parish">("own");
  const [parishId, setParishId] = useState("");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");

  if (!me) return null;
  const canChooseNarrower = me.scope.level !== "parish" && (parishes?.length ?? 0) > 0;

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const payload =
      target === "parish"
        ? { scope_level: "parish" as const, scope_id: Number(parishId), title, body }
        : { scope_level: me!.scope.level as "national" | "district" | "subcounty" | "parish", scope_id: me!.scope.id, title, body };
    create.mutate(payload, { onSuccess: () => { setTitle(""); setBody(""); } });
  }

  return (
    <Card title="Post an announcement">
      <form onSubmit={onSubmit} className="flex flex-col gap-3">
        {canChooseNarrower && (
          <div className="flex flex-wrap items-end gap-3">
            <Select label="Audience" value={target} onChange={(e) => setTarget(e.target.value as "own" | "parish")}>
              <option value="own">{OWN_SCOPE_LABEL[me.scope.level] ?? "My scope"}</option>
              <option value="parish">A specific parish…</option>
            </Select>
            {target === "parish" && (
              <Select label="Parish" required value={parishId} onChange={(e) => setParishId(e.target.value)}>
                <option value="">Select…</option>
                {parishes?.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.district})
                  </option>
                ))}
              </Select>
            )}
          </div>
        )}
        <Field label="Title" required value={title} onChange={(e) => setTitle(e.target.value)} />
        <Field label="Message" required value={body} onChange={(e) => setBody(e.target.value)} />
        <Button type="submit" disabled={create.isPending || (target === "parish" && !parishId)} className="self-start">
          {create.isPending ? "Posting…" : "Post"}
        </Button>
      </form>
    </Card>
  );
}

export function PostsSection() {
  const { data: posts, isLoading } = usePosts();

  return (
    <div className="flex flex-col gap-4">
      <PostComposer />
      <Card title="Recent posts">
        {isLoading ? (
          <p className="text-soft">Loading…</p>
        ) : !posts || posts.length === 0 ? (
          <EmptyState title="No posts yet." />
        ) : (
          posts.map((p) => (
            <div key={p.id} className="border-t border-rule pt-3 first:border-0 first:pt-0">
              <div className="flex items-center gap-2 text-xs text-soft">
                <span>{p.author_name}</span>
                <span>·</span>
                <span>{p.scope_level}</span>
              </div>
              <p className="text-sm font-medium text-ink">{p.title}</p>
              <p className="text-sm text-ink">{p.body}</p>
              <p className="mt-1 text-xs text-soft">
                {p.comment_count} comment{p.comment_count === 1 ? "" : "s"}
              </p>
            </div>
          ))
        )}
      </Card>
    </div>
  );
}
