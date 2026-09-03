import { type FormEvent, useState } from "react";
import { Link, Navigate } from "react-router";

import { ApiError } from "../../api/client";
import { useSignup, useVillages } from "../../api/hooks/useMe";
import { useAuth } from "../../app/AuthProvider";
import { Button } from "../../design/ui/Button";
import { Field } from "../../design/ui/Field";
import { Select } from "../../design/ui/Select";

function SignUpRoute() {
  const { me } = useAuth();
  const signup = useSignup();
  const { data: villages, isLoading: villagesLoading } = useVillages();
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [sex, setSex] = useState<"F" | "M">("F");
  const [villageId, setVillageId] = useState("");

  if (me) return <Navigate to="/" replace />;

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!villageId) return;
    signup.mutate({ phone, password, full_name: fullName, sex, village_id: Number(villageId), language: "lug" });
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <form onSubmit={onSubmit} className="flex w-full max-w-sm flex-col gap-4 rounded-lg bg-panel p-6 shadow-sm">
        <h1 className="text-lg font-semibold text-ink">Register as a farmer</h1>
        <Field label="Full name" required value={fullName} onChange={(e) => setFullName(e.target.value)} />
        <Field label="Phone number" type="tel" autoComplete="tel" required value={phone}
          onChange={(e) => setPhone(e.target.value)} />
        <Select label="Sex" value={sex} onChange={(e) => setSex(e.target.value as "F" | "M")}>
          <option value="F">Female</option>
          <option value="M">Male</option>
        </Select>
        <Select label="Village" required value={villageId} onChange={(e) => setVillageId(e.target.value)}
          disabled={villagesLoading}>
          <option value="">{villagesLoading ? "Loading villages…" : "Select village…"}</option>
          {villages?.map((v) => (
            <option key={v.id} value={v.id}>
              {v.name} — {v.parish} parish, {v.district}
            </option>
          ))}
        </Select>
        <Field label="Password" type="password" autoComplete="new-password" required minLength={6} value={password}
          onChange={(e) => setPassword(e.target.value)} />
        {signup.isError && (
          <p role="alert" className="text-sm text-murram">
            {signup.error instanceof ApiError ? signup.error.detail : "Something went wrong. Please try again."}
          </p>
        )}
        <Button type="submit" disabled={signup.isPending}>
          {signup.isPending ? "Registering…" : "Register"}
        </Button>
        <p className="text-center text-sm text-soft">
          Already registered?{" "}
          <Link to="/sign-in" className="text-sea underline">
            Sign in
          </Link>
        </p>
      </form>
    </div>
  );
}

export const Component = SignUpRoute;
