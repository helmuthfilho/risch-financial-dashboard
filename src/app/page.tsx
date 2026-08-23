import Link from "next/link";

const SECTIONS = [
  {
    href: "/renda-variavel",
    label: "Renda Variável",
    description: "Ações, FIIs, ETFs e cripto.",
  },
  {
    href: "/renda-fixa",
    label: "Renda Fixa",
    description: "CDB, Tesouro Direto, LCI/LCA e debêntures.",
  },
  {
    href: "/gastos",
    label: "Gastos",
    description: "Cartão de crédito, PIX e categorização de despesas.",
  },
] as const;

export default function Home() {
  return (
    <div>
      <h1 className="text-2xl font-semibold mb-2">Dashboard Financeiro</h1>
      <p className="text-black/60 dark:text-white/60 mb-8">
        Escolha uma área para começar.
      </p>
      <div className="grid gap-4 sm:grid-cols-3">
        {SECTIONS.map((section) => (
          <Link
            key={section.href}
            href={section.href}
            className="block rounded-lg border border-black/10 dark:border-white/15 p-4 hover:bg-black/5 dark:hover:bg-white/10"
          >
            <div className="font-medium mb-1">{section.label}</div>
            <div className="text-sm text-black/60 dark:text-white/60">
              {section.description}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
