"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { deletePosition } from "@/app/renda-fixa/actions";

export function DeletePositionButton({ positionId }: { positionId: string }) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  function handleClick() {
    if (
      !window.confirm(
        "Excluir esta posição de renda fixa? Essa ação não pode ser desfeita.",
      )
    ) {
      return;
    }
    startTransition(async () => {
      await deletePosition(positionId);
      router.refresh();
    });
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isPending}
      className="text-sm text-red-700 underline disabled:opacity-50 dark:text-red-400"
    >
      {isPending ? "Excluindo…" : "Excluir"}
    </button>
  );
}
