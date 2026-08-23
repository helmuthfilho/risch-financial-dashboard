import Link from "next/link";
import {
  getPositionsWithLatestValue,
  computeTotals,
} from "@/lib/renda-fixa/queries";
import { PositionTable } from "@/components/renda-fixa/position-table";

// Without this, `next build` prerenders this page once statically at build
// time, baking in whatever positions exist then — force-dynamic guarantees
// every request re-reads the database.
export const dynamic = "force-dynamic";

export default async function RendaFixaPage() {
  const positions = await getPositionsWithLatestValue();
  const totals = computeTotals(positions);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Renda Fixa</h1>
        <Link
          href="/renda-fixa/nova"
          className="rounded bg-black px-4 py-2 text-sm font-medium text-white dark:bg-white dark:text-black"
        >
          Nova posição
        </Link>
      </div>
      <PositionTable positions={positions} totals={totals} />
    </div>
  );
}
