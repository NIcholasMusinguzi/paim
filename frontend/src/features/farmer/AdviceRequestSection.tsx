import { type FormEvent, useState } from "react";

import { ApiError } from "../../api/client";
import { useMyAdvisoryRequests, useSubmitAdvisoryRequest } from "../../api/hooks/useAdvisoryRequests";
import { Button } from "../../design/ui/Button";
import { EmptyState } from "../../design/ui/EmptyState";
import { Field } from "../../design/ui/Field";
import { Pill } from "../../design/ui/Pill";

export function AdviceRequestSection() {
  const { data: requests, isLoading } = useMyAdvisoryRequests();
  const submit = useSubmitAdvisoryRequest();
  const [message, setMessage] = useState("");

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!message.trim()) return;
    submit.mutate(message, { onSuccess: () => setMessage("") });
  }

  return (
    <section className="flex flex-col gap-3 rounded-lg bg-panel p-4">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-soft">Ask for advice</h2>

      <form onSubmit={onSubmit} className="flex flex-col gap-2">
        <Field label="Your question" hideLabel value={message} onChange={(e) => setMessage(e.target.value)}
          placeholder="Describe what you're seeing — e.g. yellowing leaves, pests, low yield…" />
        {submit.isError && (
          <p role="alert" className="text-sm text-murram">
            {submit.error instanceof ApiError ? submit.error.detail : "Something went wrong. Please try again."}
          </p>
        )}
        <Button type="submit" disabled={submit.isPending} className="self-start">
          {submit.isPending ? "Sending…" : "Send question"}
        </Button>
      </form>

      {isLoading ? (
        <p className="text-soft">Loading…</p>
      ) : !requests || requests.length === 0 ? (
        <EmptyState title="You haven't asked anything yet." />
      ) : (
        <ul className="flex flex-col gap-3">
          {requests.map((r) => (
            <li key={r.id} className="border-t border-rule pt-3 first:border-0 first:pt-0">
              <div className="flex items-center gap-2">
                <p className="text-sm text-ink">{r.message}</p>
                <Pill tone={r.status === "answered" ? "leaf" : "grain"}>{r.status}</Pill>
              </div>
              {r.responses.map((resp) => (
                <p key={resp.id} className="mt-1 text-sm text-soft">
                  <span className="font-medium text-ink">{resp.responder_name}:</span> {resp.body}
                </p>
              ))}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
