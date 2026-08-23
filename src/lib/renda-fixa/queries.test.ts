import { describe, expect, it } from "vitest";
import {
  computeTotals,
  type PositionWithLatestValue,
} from "@/lib/renda-fixa/queries";

function position(
  appliedAmountCents: bigint,
  latestValueUpdate: PositionWithLatestValue["latestValueUpdate"],
): PositionWithLatestValue {
  return {
    id: "pos_1",
    institution: "Banco XP",
    type: "CDB",
    description: null,
    appliedAt: new Date("2026-01-01"),
    appliedAmountCents,
    contractedRate: null,
    maturityDate: null,
    createdAt: new Date("2026-01-01"),
    updatedAt: new Date("2026-01-01"),
    latestValueUpdate,
  };
}

function valueUpdate(
  amountCents: bigint,
): NonNullable<PositionWithLatestValue["latestValueUpdate"]> {
  return {
    id: "upd_1",
    positionId: "pos_1",
    amountCents,
    asOf: new Date("2026-02-01"),
    createdAt: new Date("2026-02-01"),
  };
}

describe("computeTotals", () => {
  it("returns zero totals for an empty list", () => {
    expect(computeTotals([])).toEqual({ appliedCents: 0n, currentCents: 0n });
  });

  it("falls back to the applied amount when a position has no value update", () => {
    const totals = computeTotals([position(100000n, null)]);
    expect(totals).toEqual({ appliedCents: 100000n, currentCents: 100000n });
  });

  it("uses the latest value update as the current amount when present", () => {
    const totals = computeTotals([position(100000n, valueUpdate(105030n))]);
    expect(totals).toEqual({ appliedCents: 100000n, currentCents: 105030n });
  });

  it("sums a mix of positions with and without value updates", () => {
    const totals = computeTotals([
      position(100000n, valueUpdate(105030n)),
      position(50000n, null),
    ]);
    expect(totals).toEqual({ appliedCents: 150000n, currentCents: 155030n });
  });
});
