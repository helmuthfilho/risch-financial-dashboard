"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import type { FixedIncomeType } from "@prisma/client";
import { createPosition, updatePosition } from "@/app/renda-fixa/actions";
import { centsToInputValue } from "@/lib/currency";
import { toDateInputValue } from "@/lib/renda-fixa/dates";
import { FIXED_INCOME_TYPE_OPTIONS } from "@/lib/renda-fixa/labels";

type PositionFormProps = {
  mode: "create" | "edit";
  positionId?: string;
  defaultValues?: {
    institution: string;
    type: FixedIncomeType;
    description: string | null;
    appliedAt: Date;
    appliedAmountCents: bigint;
    contractedRate: string | null;
    maturityDate: Date | null;
  };
};

export function PositionForm({
  mode,
  positionId,
  defaultValues,
}: PositionFormProps) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = Object.fromEntries(
      new FormData(event.currentTarget).entries(),
    );
    startTransition(async () => {
      const result =
        mode === "create"
          ? await createPosition(data)
          : await updatePosition(positionId!, data);
      if (!result.success) {
        setError(result.error);
        return;
      }
      router.push("/renda-fixa");
      router.refresh();
    });
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-md space-y-4">
      {error ? (
        <p className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      ) : null}

      <Field label="Instituição">
        <input
          name="institution"
          required
          defaultValue={defaultValues?.institution}
          className="input"
        />
      </Field>

      <Field label="Tipo">
        <select
          name="type"
          required
          defaultValue={defaultValues?.type ?? ""}
          className="input"
        >
          <option value="" disabled>
            Selecione
          </option>
          {FIXED_INCOME_TYPE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Descrição (opcional)">
        <input
          name="description"
          defaultValue={defaultValues?.description ?? ""}
          className="input"
        />
      </Field>

      <Field label="Data de aplicação">
        <input
          type="date"
          name="appliedAt"
          required
          defaultValue={toDateInputValue(defaultValues?.appliedAt)}
          className="input"
        />
      </Field>

      <Field label="Valor aplicado (R$)">
        <input
          name="appliedAmount"
          inputMode="decimal"
          placeholder="0.00"
          required
          defaultValue={
            defaultValues
              ? centsToInputValue(defaultValues.appliedAmountCents)
              : undefined
          }
          className="input"
        />
      </Field>

      <Field label="Taxa contratada (opcional)">
        <input
          name="contractedRate"
          placeholder="ex.: 110% CDI"
          defaultValue={defaultValues?.contractedRate ?? ""}
          className="input"
        />
      </Field>

      <Field label="Data de vencimento (opcional)">
        <input
          type="date"
          name="maturityDate"
          defaultValue={toDateInputValue(defaultValues?.maturityDate)}
          className="input"
        />
      </Field>

      <div className="flex gap-3 pt-2">
        <button
          type="submit"
          disabled={isPending}
          className="rounded bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-white dark:text-black"
        >
          {isPending ? "Salvando…" : "Salvar"}
        </button>
      </div>
    </form>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium">{label}</span>
      {children}
    </label>
  );
}
