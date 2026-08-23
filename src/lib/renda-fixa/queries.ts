import { prisma } from "@/lib/prisma";
import type {
  FixedIncomePosition,
  FixedIncomeValueUpdate,
} from "@prisma/client";

export type PositionWithLatestValue = FixedIncomePosition & {
  latestValueUpdate: FixedIncomeValueUpdate | null;
};

/* v8 ignore start -- touches Prisma/Postgres; validated via the browser driver (docs/adr/0004), not a unit test */
export async function getPositionsWithLatestValue(): Promise<
  PositionWithLatestValue[]
> {
  const positions = await prisma.fixedIncomePosition.findMany({
    orderBy: { appliedAt: "desc" },
    include: {
      valueUpdates: { orderBy: { asOf: "desc" }, take: 1 },
    },
  });
  return positions.map(({ valueUpdates, ...position }) => ({
    ...position,
    latestValueUpdate: valueUpdates[0] ?? null,
  }));
}
/* v8 ignore stop */

export function computeTotals(positions: PositionWithLatestValue[]) {
  return positions.reduce(
    (totals, position) => ({
      appliedCents: totals.appliedCents + position.appliedAmountCents,
      currentCents:
        totals.currentCents +
        (position.latestValueUpdate?.amountCents ??
          position.appliedAmountCents),
    }),
    { appliedCents: 0n, currentCents: 0n },
  );
}
