import Link from "next/link";
import { PositionForm } from "@/components/renda-fixa/position-form";

export default function NovaPosicaoRendaFixaPage() {
  return (
    <div>
      <Link
        href="/renda-fixa"
        className="mb-4 inline-block text-sm text-black/60 dark:text-white/60"
      >
        ← Voltar
      </Link>
      <h1 className="mb-6 text-2xl font-semibold">
        Nova posição de Renda Fixa
      </h1>
      <PositionForm mode="create" />
    </div>
  );
}
