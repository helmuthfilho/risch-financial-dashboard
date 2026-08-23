const brl = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

// Display-only formatting — money is stored/calculated as bigint cents, never float (docs/adr/0003-dinheiro-como-inteiro-em-centavos.md).
export function formatCurrencyBRL(value: number): string {
  return brl.format(value);
}

// Plain "1234.50"-style string — no currency symbol/grouping — safe to drop
// straight into an editable form input (round-trips through brlToCents).
export function centsToInputValue(cents: bigint): string {
  const negative = cents < 0n;
  const abs = negative ? -cents : cents;
  const whole = abs / 100n;
  const fraction = (abs % 100n).toString().padStart(2, "0");
  return `${negative ? "-" : ""}${whole}.${fraction}`;
}

export function centsToBRL(cents: bigint): string {
  return formatCurrencyBRL(Number(centsToInputValue(cents)));
}

const MONEY_INPUT_PATTERN = /^(-?\d+)(?:[.,](\d{1,2}))?$/;

// Parses over the string's digits directly — never `Math.round(Number(input) * 100)`,
// which can misround (e.g. 19.99 * 100 === 1998.9999999997).
export function brlToCents(input: string): bigint {
  const match = MONEY_INPUT_PATTERN.exec(input.trim());
  if (!match) {
    throw new Error(`valor monetário inválido: "${input}"`);
  }
  const [, whole, fraction = ""] = match;
  const negative = whole.startsWith("-");
  const centsFromFraction = BigInt(fraction.padEnd(2, "0"));
  return (
    BigInt(whole) * 100n + (negative ? -centsFromFraction : centsFromFraction)
  );
}
