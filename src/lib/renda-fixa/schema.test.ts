import { describe, expect, it } from "vitest";
import {
  positionInputSchema,
  valueUpdateInputSchema,
} from "@/lib/renda-fixa/schema";

const validPosition = {
  institution: "Banco XP",
  type: "CDB",
  appliedAt: "2026-01-15",
  appliedAmount: "1000.00",
};

describe("positionInputSchema", () => {
  it("accepts a minimal valid position", () => {
    const result = positionInputSchema.safeParse(validPosition);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.appliedAmountCents).toBe(100000n);
    }
  });

  it("accepts optional fields when provided", () => {
    const result = positionInputSchema.safeParse({
      ...validPosition,
      description: "CDB pós-fixado",
      contractedRate: "110% CDI",
      maturityDate: "2027-01-15",
    });
    expect(result.success).toBe(true);
  });

  it("treats empty-string optional fields as absent", () => {
    const result = positionInputSchema.safeParse({
      ...validPosition,
      description: "",
      contractedRate: "",
      maturityDate: "",
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.description).toBeUndefined();
      expect(result.data.maturityDate).toBeUndefined();
    }
  });

  it("rejects a missing institution", () => {
    const { type, appliedAt, appliedAmount } = validPosition;
    expect(
      positionInputSchema.safeParse({ type, appliedAt, appliedAmount }).success,
    ).toBe(false);
  });

  it("rejects a type outside the enum", () => {
    const result = positionInputSchema.safeParse({
      ...validPosition,
      type: "DEBENTURE",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a non-numeric amount", () => {
    const result = positionInputSchema.safeParse({
      ...validPosition,
      appliedAmount: "not-a-number",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a negative amount", () => {
    const result = positionInputSchema.safeParse({
      ...validPosition,
      appliedAmount: "-100.00",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a zero amount", () => {
    const result = positionInputSchema.safeParse({
      ...validPosition,
      appliedAmount: "0",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid applied date", () => {
    const result = positionInputSchema.safeParse({
      ...validPosition,
      appliedAt: "not-a-date",
    });
    expect(result.success).toBe(false);
  });
});

describe("valueUpdateInputSchema", () => {
  it("accepts a valid value update", () => {
    const result = valueUpdateInputSchema.safeParse({
      positionId: "pos_1",
      amount: "1050.30",
      asOf: "2026-02-01",
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.amountCents).toBe(105030n);
    }
  });

  it("rejects a missing positionId", () => {
    const result = valueUpdateInputSchema.safeParse({
      amount: "1050.30",
      asOf: "2026-02-01",
    });
    expect(result.success).toBe(false);
  });
});
