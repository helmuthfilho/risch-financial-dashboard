"use server";

import { revalidatePath } from "next/cache";
import type { ZodError } from "zod";
import { prisma } from "@/lib/prisma";
import {
  positionInputSchema,
  valueUpdateInputSchema,
} from "@/lib/renda-fixa/schema";

export type ActionResult =
  { success: true } | { success: false; error: string };

function firstIssueMessage(error: ZodError): string {
  return error.issues[0]?.message ?? "Dados inválidos";
}

export async function createPosition(raw: unknown): Promise<ActionResult> {
  const parsed = positionInputSchema.safeParse(raw);
  if (!parsed.success) {
    return { success: false, error: firstIssueMessage(parsed.error) };
  }
  await prisma.fixedIncomePosition.create({ data: parsed.data });
  revalidatePath("/renda-fixa");
  return { success: true };
}

export async function updatePosition(
  id: string,
  raw: unknown,
): Promise<ActionResult> {
  const parsed = positionInputSchema.safeParse(raw);
  if (!parsed.success) {
    return { success: false, error: firstIssueMessage(parsed.error) };
  }
  await prisma.fixedIncomePosition.update({ where: { id }, data: parsed.data });
  revalidatePath("/renda-fixa");
  return { success: true };
}

export async function deletePosition(id: string): Promise<ActionResult> {
  await prisma.fixedIncomePosition.delete({ where: { id } });
  revalidatePath("/renda-fixa");
  return { success: true };
}

export async function addValueUpdate(raw: unknown): Promise<ActionResult> {
  const parsed = valueUpdateInputSchema.safeParse(raw);
  if (!parsed.success) {
    return { success: false, error: firstIssueMessage(parsed.error) };
  }
  await prisma.fixedIncomeValueUpdate.create({ data: parsed.data });
  revalidatePath("/renda-fixa");
  return { success: true };
}
