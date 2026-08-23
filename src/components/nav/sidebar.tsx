"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/renda-variavel", label: "Renda Variável" },
  { href: "/renda-fixa", label: "Renda Fixa" },
  { href: "/gastos", label: "Gastos" },
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="w-56 shrink-0 border-r border-black/10 dark:border-white/15 px-4 py-6">
      <Link href="/" className="block font-semibold mb-6">
        Dashboard Financeiro
      </Link>
      <ul className="space-y-1">
        {NAV_ITEMS.map((item) => {
          const active = pathname.startsWith(item.href);
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={`block rounded px-3 py-2 text-sm transition-colors ${
                  active
                    ? "bg-brand-strong text-brand-foreground font-medium"
                    : "hover:bg-brand/10 hover:text-brand"
                }`}
              >
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
