import Link from "next/link";
import { centsToBRL } from "@/lib/currency";
import { FIXED_INCOME_TYPE_LABELS } from "@/lib/renda-fixa/labels";
import type {
  PositionWithLatestValue,
  computeTotals,
} from "@/lib/renda-fixa/queries";
import { DeletePositionButton } from "@/components/renda-fixa/delete-position-button";
import { UpdateValueForm } from "@/components/renda-fixa/update-value-form";

type PositionTableProps = {
  positions: PositionWithLatestValue[];
  totals: ReturnType<typeof computeTotals>;
};

const dateFormatter = new Intl.DateTimeFormat("pt-BR");

export function PositionTable({ positions, totals }: PositionTableProps) {
  if (positions.length === 0) {
    return (
      <p className="text-black/60 dark:text-white/60">
        Nenhuma posição cadastrada ainda.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-black/10 text-left dark:border-white/15">
            <th className="py-2 pr-4 font-medium">Instituição</th>
            <th className="py-2 pr-4 font-medium">Tipo</th>
            <th className="py-2 pr-4 font-medium">Valor aplicado</th>
            <th className="py-2 pr-4 font-medium">Valor atual</th>
            <th className="py-2 pr-4 font-medium">Vencimento</th>
            <th className="py-2 pr-4 font-medium">Ações</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((position) => (
            <tr
              key={position.id}
              className="border-b border-black/5 dark:border-white/10"
            >
              <td className="py-3 pr-4">{position.institution}</td>
              <td className="py-3 pr-4">
                {FIXED_INCOME_TYPE_LABELS[position.type]}
              </td>
              <td className="py-3 pr-4">
                {centsToBRL(position.appliedAmountCents)}
              </td>
              <td className="py-3 pr-4">
                {centsToBRL(
                  position.latestValueUpdate?.amountCents ??
                    position.appliedAmountCents,
                )}
              </td>
              <td className="py-3 pr-4">
                {position.maturityDate
                  ? dateFormatter.format(position.maturityDate)
                  : "—"}
              </td>
              <td className="py-3 pr-4">
                <div className="flex flex-wrap items-center gap-3">
                  <Link
                    href={`/renda-fixa/${position.id}/editar`}
                    className="text-sm underline"
                  >
                    Editar
                  </Link>
                  <UpdateValueForm positionId={position.id} />
                  <DeletePositionButton positionId={position.id} />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="font-medium">
            <td className="pt-3 pr-4" colSpan={2}>
              Total
            </td>
            <td className="pt-3 pr-4">{centsToBRL(totals.appliedCents)}</td>
            <td className="pt-3 pr-4">{centsToBRL(totals.currentCents)}</td>
            <td className="pt-3 pr-4" colSpan={2} />
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
