import { type FormEvent, useState } from "react";

import { useAdvisoryQueue, useRespondToRequest } from "../../api/hooks/useAdvisoryRequests";
import { Button } from "../../design/ui/Button";
import { EmptyState } from "../../design/ui/EmptyState";
import { Field } from "../../design/ui/Field";
import { Pill } from "../../design/ui/Pill";

function RespondForm({ requestId }: { requestId: number }) {
  const respond = useRespondToRequest();
  const [body, setBody] = useState("");

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!body.trim()) return;
    respond.mutate({ id: requestId, body }, { onSuccess: () => setBody("") });
  }

  return (
    <form onSubmit={onSubmit} className="mt-2 flex gap-2">
      <Field label="Response" hideLabel value={body} onChange={(e) => setBody(e.target.value)}
        placeholder="Write a response…" className="flex-1" />
      <Button type="submit" variant="secondary" disabled={respond.isPending} className="self-end px-3 py-2 text-sm">
        Respond
      </Button>
    </form>
  );
}

export function AdvisoryQueueSection() {
  const { data: requests, isLoading } = useAdvisoryQueue();

  return (
    <section className="flex flex-col gap-3 rounded-lg bg-panel p-4">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-soft">Advisory requests</h2>
      {isLoading ? (
        <p className="text-soft">Loading…</p>
      ) : !requests || requests.length === 0 ? (
        <EmptyState title="No advisory requests right now." />
      ) : (
        requests.map((r) => (
          <div key={r.id} className="border-t border-rule pt-3 first:border-0 first:pt-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-ink">{r.farmer_name}</span>
              <span className="text-xs text-soft">{r.parish_name}</span>
              <Pill tone={r.status === "answered" ? "leaf" : "grain"}>{r.status}</Pill>
            </div>
            <p className="text-sm text-ink">{r.message}</p>
            {r.responses.map((resp) => (
              <p key={resp.id} className="mt-1 text-sm text-soft">
                <span className="font-medium text-ink">{resp.responder_name}:</span> {resp.body}
              </p>
            ))}
            {r.status === "open" && <RespondForm requestId={r.id} />}
          </div>
        ))
      )}
    </section>
  );
}
