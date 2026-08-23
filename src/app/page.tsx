import Link from "next/link";
import { CreditCard, PiggyBank, TrendingUp, type LucideIcon } from "lucide-react";

const SECTIONS: {
  href: string;
  label: string;
  description: string;
  icon: LucideIcon;
}[] = [
  {
    href: "/renda-variavel",
    label: "Renda Variável",
    description: "Ações, FIIs, ETFs e cripto.",
    icon: TrendingUp,
  },
  {
    href: "/renda-fixa",
    label: "Renda Fixa",
    description: "CDB, Tesouro Direto, LCI/LCA e debêntures.",
    icon: PiggyBank,
  },
  {
    href: "/gastos",
    label: "Gastos",
    description: "Cartão de crédito, PIX e categorização de despesas.",
    icon: CreditCard,
  },
];

export default function Home() {
  return (
    <div>
      <div className="hero-pattern relative mb-8 overflow-hidden rounded-2xl border border-brand/20 bg-brand/5 p-8">
        <h1 className="text-2xl font-semibold mb-2 text-brand">
          Dashboard Financeiro
        </h1>
        <p className="text-black/60 dark:text-white/60">
          Escolha uma área para começar.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        {SECTIONS.map((section) => {
          const Icon = section.icon;
          return (
            <Link
              key={section.href}
              href={section.href}
              className="group block rounded-lg border border-black/10 dark:border-white/15 p-4 transition-all hover:-translate-y-0.5 hover:border-brand/50 hover:shadow-lg hover:shadow-brand/10"
            >
              <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-brand/10 text-brand transition-colors group-hover:bg-brand-strong group-hover:text-brand-foreground">
                <Icon className="h-5 w-5" aria-hidden="true" />
              </div>
              <div className="font-medium mb-1">{section.label}</div>
              <div className="text-sm text-black/60 dark:text-white/60">
                {section.description}
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
