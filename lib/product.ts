// Everything shown on the page comes from the stock file. Nothing here is typed in by hand.
import rawRows from "@/data/nike_pegasus_size_stock.json";

export type StockStatus = "in_stock" | "low_stock" | "sold_out";

export interface SizeRow {
  sku: string;
  style_code: string;
  product_name: string;
  colorway: string;
  price: number;
  size_label: string;
  size_us_men: number;
  size_us_women: number;
  size_eu: string;
  display_order: number;
  in_stock: boolean;
  stock_quantity: number;
  stock_status: StockStatus;
  launch_date: string;
}

const rows = rawRows as SizeRow[];

if (rows.length === 0) {
  throw new Error("nike_pegasus_size_stock.json has no rows");
}

// Product-level values repeat on every row. Read them once and fail the build
// if the file ever disagrees with itself, so the page can't show a wrong value.
function sharedValue<K extends keyof SizeRow>(key: K): SizeRow[K] {
  const values = new Set(rows.map((row) => row[key]));
  if (values.size !== 1) {
    throw new Error(
      `Expected one ${String(key)} across all rows, found: ${[...values].join(", ")}`,
    );
  }
  return rows[0][key];
}

export const product = {
  name: sharedValue("product_name"),
  colorway: sharedValue("colorway"),
  price: sharedValue("price"),
  styleCode: sharedValue("style_code"),
};

/** All sizes, small to big, in the order set by display_order. */
export const sizes: SizeRow[] = [...rows].sort(
  (a, b) => a.display_order - b.display_order,
);

/** 140 -> "140.00" (JSON drops the trailing zeros). */
export function formatPrice(price: number): string {
  return price.toFixed(2);
}
