import Link from "next/link";
import { notFound } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { PositionForm } from "@/components/renda-fixa/position-form";

export default async function EditarPosicaoRendaFixaPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const position = await prisma.fixedIncomePosition.findUnique({
    where: { id },
  });
  if (!position) {
    notFound();
  }

  return (
    <div>
      <Link
        href="/renda-fixa"
        className="mb-4 inline-block text-sm text-black/60 dark:text-white/60"
      >
        ← Voltar
      </Link>
      <h1 className="mb-6 text-2xl font-semibold">
        Editar posição de Renda Fixa
      </h1>
      <PositionForm
        mode="edit"
        positionId={position.id}
        defaultValues={position}
      />
    </div>
  );
}
