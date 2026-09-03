import { type FormEvent, useState } from "react";
import { Link, Navigate } from "react-router";

import { ApiError } from "../../api/client";
import { useLogin } from "../../api/hooks/useMe";
import { useAuth } from "../../app/AuthProvider";
import { Button } from "../../design/ui/Button";
import { Field } from "../../design/ui/Field";

function SignInRoute() {
  const { me } = useAuth();
  const login = useLogin();
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");

  if (me) return <Navigate to="/" replace />;

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    login.mutate({ phone, password });
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <form onSubmit={onSubmit} className="flex w-full max-w-sm flex-col gap-4 rounded-lg bg-panel p-6 shadow-sm">
        <h1 className="text-lg font-semibold text-ink">Sign in to PAIM</h1>
        <Field label="Phone number" type="tel" autoComplete="tel" required value={phone}
          onChange={(e) => setPhone(e.target.value)} />
        <Field label="Password" type="password" autoComplete="current-password" required value={password}
          onChange={(e) => setPassword(e.target.value)} />
        {login.isError && (
          <p role="alert" className="text-sm text-murram">
            {login.error instanceof ApiError ? login.error.detail : "Something went wrong. Please try again."}
          </p>
        )}
        <Button type="submit" disabled={login.isPending}>
          {login.isPending ? "Signing in…" : "Sign in"}
        </Button>
        <p className="text-center text-sm text-soft">
          Farmer, new here?{" "}
          <Link to="/sign-up" className="text-sea underline">
            Register
          </Link>
        </p>
      </form>
    </div>
  );
}

export const Component = SignInRoute;
