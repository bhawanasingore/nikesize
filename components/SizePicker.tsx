"use client";

import { useState } from "react";
import type { SizeRow } from "@/lib/product";
import styles from "./SizePicker.module.css";

type SizeSystem = "men" | "women";

const SYSTEMS: { id: SizeSystem; label: string; prefix: string }[] = [
  { id: "men", label: "Men's", prefix: "US Men's" },
  { id: "women", label: "Women's", prefix: "US Women's" },
];

// 4 -> "4", 9.5 -> "9.5"
function formatSize(value: number): string {
  return String(value);
}

export default function SizePicker({ sizes }: { sizes: SizeRow[] }) {
  const [system, setSystem] = useState<SizeSystem>("men");
  const [selectedSku, setSelectedSku] = useState<string | null>(null);
  const prefix = SYSTEMS.find((s) => s.id === system)!.prefix;

  return (
    <section
      className={styles.section}
      data-testid="size-section"
      aria-labelledby="size-heading"
    >
      <div className={styles.head}>
        <h2 id="size-heading" className={styles.title}>
          Select size
        </h2>
        <div
          className={styles.toggle}
          role="group"
          aria-label="Size system"
          data-testid="size-system-toggle"
        >
          {SYSTEMS.map((option) => (
            <button
              key={option.id}
              type="button"
              className={styles.toggleButton}
              aria-pressed={system === option.id}
              data-testid={`size-toggle-${option.id}`}
              onClick={() => setSystem(option.id)}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <ul className={styles.grid} data-testid="size-grid" data-size-system={system}>
        {sizes.map((size) => {
          const value = system === "men" ? size.size_us_men : size.size_us_women;
          const label = formatSize(value);
          const soldOut = !size.in_stock || size.stock_status === "sold_out";
          const lowStock = !soldOut && size.stock_status === "low_stock";
          const selected = selectedSku === size.sku;
          const status = soldOut ? "sold_out" : lowStock ? "low_stock" : "in_stock";

          return (
            <li key={size.sku} className={styles.cell} data-testid="size-cell">
              <button
                type="button"
                className={styles.size}
                disabled={soldOut}
                aria-pressed={soldOut ? undefined : selected}
                aria-label={`${prefix} ${label}${
                  soldOut ? ", sold out" : lowStock ? ", low stock" : ""
                }`}
                data-testid={soldOut ? "size-button-sold-out" : "size-button"}
                data-sku={size.sku}
                data-status={status}
                data-size-men={formatSize(size.size_us_men)}
                data-size-women={formatSize(size.size_us_women)}
                onClick={() => setSelectedSku(size.sku)}
              >
                {label}
              </button>
              {lowStock && (
                <span
                  className={styles.lowTag}
                  data-testid="low-stock-tag"
                  aria-hidden="true"
                >
                  🔥 Low stock
                </span>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
