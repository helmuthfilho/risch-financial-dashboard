"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { addValueUpdate } from "@/app/renda-fixa/actions";

export function UpdateValueForm({ positionId }: { positionId: string }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="text-sm underline"
      >
        Atualizar valor
      </button>
    );
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const data = { positionId, ...Object.fromEntries(formData.entries()) };
    startTransition(async () => {
      const result = await addValueUpdate(data);
      if (!result.success) {
        setError(result.error);
        return;
      }
      setOpen(false);
      setError(null);
      router.refresh();
    });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2">
      {error ? (
        <p className="text-xs text-red-700 dark:text-red-300">{error}</p>
      ) : null}
      <div className="flex items-center gap-2">
        <input
          name="amount"
          inputMode="decimal"
          placeholder="Valor atual (R$)"
          required
          autoFocus
          className="input w-32 text-xs"
        />
        <input
          type="date"
          name="asOf"
          required
          defaultValue={new Date().toISOString().slice(0, 10)}
          className="input w-36 text-xs"
        />
        <button
          type="submit"
          disabled={isPending}
          className="text-sm underline disabled:opacity-50"
        >
          {isPending ? "Salvando…" : "OK"}
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="text-sm text-black/60 dark:text-white/60"
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}
