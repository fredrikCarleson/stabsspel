# CSS-refaktorering (historisk anteckning)

Tre filer (`design-system.css`, `style.css`, `admin.css`) slogs ihop till **`static/app.css`** plus **`static/print.css`**. De gamla filerna finns inte längre.

Det här dokumentet är **inte** en stilguide för ny kod. Titta i `app.css` och i befintlig HTML.

## Nuvarande läge

| Fil | Ungefär | Användning |
|-----|---------|------------|
| `static/app.css` | ~2000 rader | All skärm-CSS (tokens, knappar, GM-konsol, modaler, startsida) |
| `static/print.css` | ~225 rader | `@media print` |

Knappar är **inte** BEM `btn btn--primary`. HTML använder element + modifierare:

```html
<button class="primary">…</button>
<button class="danger sm">Ta bort</button>
<a class="secondary" href="…">…</a>
```

Vanliga klasser: `primary`, `success`, `warning`, `danger`, `info`, `secondary`, `sm`, `lg`, `ghost`. Notiser: `.notification.success` / `.error` (inte `notification--success`). Modaler: `.modal`, `.modal-content`.

Design tokens ligger i `:root` (`--c-primary`, `--t-alfa`, `--radius-8`, …). Färgvärdena i den ursprungliga refaktorloggen är inaktuella.

Bakgrundsbilder hör hemma i `static/backgrounds/` och refereras som `/static/backgrounds/<filnamn>`.
