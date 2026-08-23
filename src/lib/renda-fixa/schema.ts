import { z } from "zod";
import { FixedIncomeType } from "@prisma/client";
import { brlToCents } from "@/lib/currency";

const optionalString = z.preprocess(
  (value) =>
    typeof value === "string" && value.trim() === "" ? undefined : value,
  z.string().trim().optional(),
);

const optionalDate = z.preprocess(
  (value) =>
    typeof value === "string" && value.trim() === "" ? undefined : value,
  z.coerce.date().optional(),
);

const moneyAmountCents = z
  .string()
  .trim()
  .min(1, "Valor é obrigatório")
  .transform((value, ctx) => {
    let cents: bigint;
    try {
      cents = brlToCents(value);
    } catch {
      ctx.addIssue({ code: "custom", message: "Valor monetário inválido" });
      return z.NEVER;
    }
    if (cents <= 0n) {
      ctx.addIssue({
        code: "custom",
        message: "Valor deve ser maior que zero",
      });
      return z.NEVER;
    }
    return cents;
  });

// Form fields carry the BRL string under the plain name (`appliedAmount`,
// `amount`); the object-level transform below both converts it to cents
// and renames the key to match the Prisma column (`appliedAmountCents`,
// `amountCents`) so `parsed.data` can be passed straight to Prisma.
export const positionInputSchema = z
  .object({
    institution: z.string().trim().min(1, "Instituição é obrigatória"),
    type: z.enum(FixedIncomeType, { message: "Tipo de título inválido" }),
    description: optionalString,
    appliedAt: z.coerce.date({ message: "Data de aplicação inválida" }),
    appliedAmount: moneyAmountCents,
    contractedRate: optionalString,
    maturityDate: optionalDate,
  })
  .transform(({ appliedAmount, ...rest }) => ({
    ...rest,
    appliedAmountCents: appliedAmount,
  }));

export type PositionInput = z.infer<typeof positionInputSchema>;

export const valueUpdateInputSchema = z
  .object({
    positionId: z.string().trim().min(1),
    amount: moneyAmountCents,
    asOf: z.coerce.date({ message: "Data inválida" }),
  })
  .transform(({ amount, ...rest }) => ({ ...rest, amountCents: amount }));

export type ValueUpdateInput = z.infer<typeof valueUpdateInputSchema>;
