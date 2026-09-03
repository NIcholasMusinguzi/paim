import { useLiveQuery } from "dexie-react-hooks";
import { type FormEvent, useEffect, useState } from "react";

import { useLogout } from "../../api/hooks/useMe";
import { Button } from "../../design/ui/Button";
import { EmptyState } from "../../design/ui/EmptyState";
import { Field } from "../../design/ui/Field";
import { Meter } from "../../design/ui/Meter";
import { Pill } from "../../design/ui/Pill";
import { Select } from "../../design/ui/Select";
import { bootstrap } from "./bootstrap";
import { db } from "./db";
import { syncNow } from "./sync";
import { useDeclareHarvest } from "./useDeclareHarvest";
import { useOnlineStatus } from "./useOnlineStatus";
import { useRegisterFarmer } from "./useRegisterFarmer";

function SyncStatus() {
  const online = useOnlineStatus();
  const pending = useLiveQuery(() => db.outbox.where("status").equals("queued").count(), [], 0);
  const needsAttention = useLiveQuery(() => db.outbox.where("status").equals("needs_attention").count(), [], 0);

  return (
    <div className="flex flex-wrap items-center gap-3 text-xs text-soft">
      <span className="inline-flex items-center gap-1.5">
        <span className={`h-2 w-2 rounded-full ${online ? "bg-leaf" : "bg-murram"}`} />
        {online ? "Online" : "Offline — saved on this phone"}
      </span>
      {pending > 0 && <span className="tabular">{pending} queued</span>}
      {needsAttention > 0 && <Pill tone="murram">{needsAttention} need attention</Pill>}
      <Button variant="ghost" onClick={() => void syncNow()} className="px-2 py-1">
        Sync now
      </Button>
    </div>
  );
}

function RegisterFarmerForm() {
  const villages = useLiveQuery(() => db.villages.toArray(), [], []);
  const register = useRegisterFarmer();
  const [fullName, setFullName] = useState("");
  const [villageId, setVillageId] = useState("");
  const [sex, setSex] = useState("F");
  const [phone, setPhone] = useState("");

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const village = villages.find((v) => v.id === Number(villageId));
    if (!village) return;
    register.mutate({ full_name: fullName, village_id: village.id, village_name: village.name, sex, phone: phone || undefined });
    setFullName("");
    setPhone("");
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-3 rounded-lg bg-panel p-4">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-soft">Register a farmer</h2>
      <Field label="Full name" required value={fullName} onChange={(e) => setFullName(e.target.value)} />
      <Select label="Village" required value={villageId} onChange={(e) => setVillageId(e.target.value)}>
        <option value="">Select village…</option>
        {villages.map((v) => (
          <option key={v.id} value={v.id}>
            {v.name}
          </option>
        ))}
      </Select>
      <Select label="Sex" value={sex} onChange={(e) => setSex(e.target.value)}>
        <option value="F">Female</option>
        <option value="M">Male</option>
      </Select>
      <Field label="Phone (optional)" value={phone} onChange={(e) => setPhone(e.target.value)} />
      <Button type="submit" disabled={register.isPending}>
        Register — saves on this phone, syncs when possible
      </Button>
    </form>
  );
}

function DeclareHarvestRow({ farmerId }: { farmerId: number }) {
  const crops = useLiveQuery(() => db.crops.toArray(), [], []);
  const declare = useDeclareHarvest();
  const [cropId, setCropId] = useState("");
  const [bags, setBags] = useState("");

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!cropId || !bags) return;
    declare.mutate({ farmer_id: farmerId, crop_id: Number(cropId), bags: Number(bags) });
    setBags("");
  }

  return (
    <form onSubmit={onSubmit} className="mt-2 flex items-end gap-2">
      <Select label="Crop" required value={cropId} onChange={(e) => setCropId(e.target.value)} className="text-sm">
        <option value="">Crop…</option>
        {crops.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
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
        className="w-20"
      />
      <Button type="submit" variant="secondary" disabled={declare.isPending} className="px-3 py-2 text-sm">
        Declare
      </Button>
    </form>
  );
}

function FarmerList() {
  const farmers = useLiveQuery(() => db.farmers.toArray(), [], []);

  if (farmers.length === 0) return <EmptyState title="No farmers registered on this device yet." />;

  return (
    <ul className="flex flex-col gap-3">
      {farmers.map((f) => (
        <li key={f.id} className="rounded border border-rule p-3">
          <div className="flex items-center gap-2">
            <span className="font-medium text-ink">{f.full_name}</span>
            {f.pending && <Pill tone="grain">saved on this phone</Pill>}
            {f.needs_attention && <Pill tone="murram">needs attention — {f.reason}</Pill>}
          </div>
          <p className="text-xs text-soft">{f.village_name}</p>
          {!f.pending && !f.needs_attention && <DeclareHarvestRow farmerId={f.id} />}
        </li>
      ))}
    </ul>
  );
}

function OpenLots() {
  const lots = useLiveQuery(() => db.lots.toArray(), [], []);
  if (lots.length === 0) return null;
  return (
    <section className="flex flex-col gap-3 rounded-lg bg-panel p-4">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-soft">Open lots</h2>
      {lots.map((lot) => (
        <Meter key={lot.id} value={lot.bags} target={lot.min_bags} label={lot.crop} />
      ))}
    </section>
  );
}

function AgentRoute() {
  const logout = useLogout();

  useEffect(() => {
    void bootstrap();
  }, []);

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6 p-4">
      <header className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-ink">Agent</h1>
        <Button variant="ghost" onClick={() => logout.mutate()} disabled={logout.isPending}>
          Sign out
        </Button>
      </header>
      <SyncStatus />
      <OpenLots />
      <RegisterFarmerForm />
      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-soft">Farmers on this device</h2>
        <FarmerList />
      </section>
    </div>
  );
}

export const Component = AgentRoute;
