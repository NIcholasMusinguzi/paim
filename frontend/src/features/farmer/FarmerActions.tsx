import { type FormEvent, useState } from "react";

import { api, ApiError } from "../../api/client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "../../design/ui/Button";
import { Card } from "../../design/ui/Card";
import { Field } from "../../design/ui/Field";
import { Select } from "../../design/ui/Select";

type Crop = { id: number; name: string };
type ReferenceData = { crops: Crop[] };
type Profile = {
  full_name: string;
  phone: string;
  sex: "F" | "M";
  language: string;
  area_acres: string | null;
  crop_id: number | null;
  planting_date: string | null;
};

function useProfile() {
  return useQuery({
    queryKey: ["farmer", "profile"],
    queryFn: () => api<Profile>("/farmer/profile/"),
  });
}

export function FarmerProfileSection() {
  const { data, isLoading } = useProfile();
  const { data: reference } = useQuery({
    queryKey: ["reference"],
    queryFn: () => api<ReferenceData>("/reference/"),
  });
  const qc = useQueryClient();
  const update = useMutation({
    mutationFn: (body: Partial<Profile>) =>
      api<Profile>("/farmer/profile/", {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: (profile) => qc.setQueryData(["farmer", "profile"], profile),
  });
  const [form, setForm] = useState<Profile | null>(null);

  if (isLoading || !data)
    return (
      <Card title="My profile">
        <p className="text-soft">Loading…</p>
      </Card>
    );
  const values = form ?? data;
  function onSubmit(event: FormEvent) {
    event.preventDefault();
    update.mutate(values);
    setForm(values);
  }

  return (
    <Card title="My profile and farm">
      <form onSubmit={onSubmit} className="flex flex-col gap-3">
        <Field
          label="Full name"
          value={values.full_name}
          onChange={(e) => setForm({ ...values, full_name: e.target.value })}
        />
        <Field
          label="Phone"
          value={values.phone}
          onChange={(e) => setForm({ ...values, phone: e.target.value })}
        />
        <div className="grid gap-3 sm:grid-cols-3">
          <Select
            label="Sex"
            value={values.sex}
            onChange={(e) =>
              setForm({ ...values, sex: e.target.value as "F" | "M" })
            }
          >
            <option value="F">Female</option>
            <option value="M">Male</option>
          </Select>
          <Field
            label="Farm size (acres)"
            type="number"
            step="0.01"
            value={values.area_acres ?? ""}
            onChange={(e) => setForm({ ...values, area_acres: e.target.value })}
          />
          <Select
            label="Main crop"
            value={values.crop_id ?? ""}
            onChange={(e) =>
              setForm({ ...values, crop_id: Number(e.target.value) })
            }
          >
            <option value="">Select crop</option>
            {reference?.crops.map((crop) => (
              <option key={crop.id} value={crop.id}>
                {crop.name}
              </option>
            ))}
          </Select>
        </div>
        <Field
          label="Planting date"
          type="date"
          value={values.planting_date ?? ""}
          onChange={(e) =>
            setForm({ ...values, planting_date: e.target.value })
          }
        />
        {update.isError && (
          <p className="text-sm text-murram">
            {update.error instanceof ApiError
              ? update.error.detail
              : "Could not update your profile."}
          </p>
        )}
        <Button
          type="submit"
          disabled={update.isPending}
          className="self-start"
        >
          {update.isPending ? "Saving…" : "Save profile"}
        </Button>
      </form>
    </Card>
  );
}

export function DeclarationSection() {
  const { data: reference } = useQuery({
    queryKey: ["reference"],
    queryFn: () => api<ReferenceData>("/reference/"),
  });
  const qc = useQueryClient();
  const declare = useMutation({
    mutationFn: (body: {
      crop_id: number;
      bags: number;
      moisture_pct?: number;
    }) =>
      api("/farmer/declarations/", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["farmer", "home"] }),
  });
  const [cropId, setCropId] = useState("");
  const [bags, setBags] = useState("");
  const [moisture, setMoisture] = useState("");
  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!cropId || !bags) return;
    declare.mutate({
      crop_id: Number(cropId),
      bags: Number(bags),
      ...(moisture ? { moisture_pct: Number(moisture) } : {}),
    });
    setBags("");
    setMoisture("");
  }
  return (
    <Card title="Declare harvest">
      <form
        onSubmit={onSubmit}
        className="grid gap-3 sm:grid-cols-4 sm:items-end"
      >
        <Select
          label="Crop"
          required
          value={cropId}
          onChange={(e) => setCropId(e.target.value)}
        >
          <option value="">Select crop</option>
          {reference?.crops.map((crop) => (
            <option key={crop.id} value={crop.id}>
              {crop.name}
            </option>
          ))}
        </Select>
        <Field
          label="Bags"
          type="number"
          min={1}
          max={200}
          required
          value={bags}
          onChange={(e) => setBags(e.target.value)}
        />
        <Field
          label="Moisture % (optional)"
          type="number"
          step="0.1"
          value={moisture}
          onChange={(e) => setMoisture(e.target.value)}
        />
        <Button type="submit" disabled={declare.isPending}>
          {declare.isPending ? "Saving…" : "Declare harvest"}
        </Button>
      </form>
      {declare.isError && (
        <p className="mt-2 text-sm text-murram">
          {declare.error instanceof ApiError
            ? declare.error.detail
            : "Could not save declaration."}
        </p>
      )}
    </Card>
  );
}
