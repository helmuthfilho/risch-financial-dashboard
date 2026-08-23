import { FixedIncomeType } from "@prisma/client";

export const FIXED_INCOME_TYPE_LABELS: Record<FixedIncomeType, string> = {
  CDB: "CDB",
  TREASURY_DIRECT: "Tesouro Direto",
  LCI_LCA: "LCI/LCA",
};

export const FIXED_INCOME_TYPE_OPTIONS = Object.entries(
  FIXED_INCOME_TYPE_LABELS,
).map(([value, label]) => ({ value: value as FixedIncomeType, label }));
