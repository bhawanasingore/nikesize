import SizePicker from "@/components/SizePicker";
import { formatPrice, product, sizes } from "@/lib/product";
import styles from "./page.module.css";

export default function ProductPage() {
  return (
    <main className={styles.page} data-testid="product-page">
      {/* 1. Name, price and colourway: shown once, above the size grid. */}
      <header className={styles.header} data-testid="product-header">
        <h1 className={styles.name} data-testid="product-name">
          {product.name}
        </h1>
        <p className={styles.meta}>
          <span className={styles.price} data-testid="product-price">
            {formatPrice(product.price)}
          </span>
          <span className={styles.colorway} data-testid="product-colorway">
            {product.colorway}
          </span>
        </p>
      </header>

      {/* 2. Main photo area (placeholder until product photos are supplied). */}
      <div
        className={styles.photo}
        data-testid="main-photo"
        role="img"
        aria-label={`${product.name} in ${product.colorway}. Photo coming soon.`}
      >
        <span className={styles.photoNote} aria-hidden="true">
          Photo coming soon
        </span>
      </div>

      {/* 3. Size grid, starting on the lower part of the first screen. */}
      <SizePicker sizes={sizes} />
    </main>
  );
}
