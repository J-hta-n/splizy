import { LastReceipt } from "./types";

type ConfirmItemsProps = {
  receipt: LastReceipt;
  saving: boolean;
  formatMoney: (value: number) => string;
  onUpdateItem: (
    index: number,
    field: "name" | "quantity" | "subtotal",
    value: string,
  ) => void;
  onUpdateMeta: (
    field: "currency" | "service_charge" | "gst",
    value: string,
  ) => void;
  onAddItem: () => void;
  onRemoveItem: (index: number) => void;
  onSave: () => void;
};

export function ConfirmItems({
  receipt,
  saving,
  formatMoney,
  onUpdateItem,
  onUpdateMeta,
  onAddItem,
  onRemoveItem,
  onSave,
}: ConfirmItemsProps) {
  return (
    <section className="space-y-4">
      <div className="rounded-3xl border-2 border-slate-300 bg-white p-4">
        <h2 className="text-xl font-bold text-slate-900">
          Step 1/3: Confirm receipt items
        </h2>
      </div>

      <div className="rounded-3xl border-2 border-slate-300 bg-white p-3 sm:p-4">
        <div className="space-y-3">
          {receipt.items.map((item, index) => (
            <div
              key={String(index)}
              className="grid grid-cols-1 gap-2 sm:grid-cols-[2fr_1fr_1fr_auto]"
            >
              <input
                value={item.name}
                onChange={(event) =>
                  onUpdateItem(index, "name", event.target.value)
                }
                placeholder="Item name"
                className="rounded-2xl border-2 border-slate-300 px-3 py-2"
              />
              <input
                type="number"
                min="0"
                value={item.quantity}
                onChange={(event) =>
                  onUpdateItem(index, "quantity", event.target.value)
                }
                className="rounded-2xl border-2 border-slate-300 px-3 py-2"
              />
              <input
                type="number"
                min="0"
                step="0.01"
                value={item.subtotal ?? ""}
                onChange={(event) =>
                  onUpdateItem(index, "subtotal", event.target.value)
                }
                className="rounded-2xl border-2 border-slate-300 px-3 py-2"
              />
              <button
                type="button"
                onClick={() => onRemoveItem(index)}
                className="rounded-2xl border-2 border-rose-300 bg-rose-100 px-4 py-2 font-semibold text-rose-700"
              >
                Delete
              </button>
            </div>
          ))}
        </div>

        <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-3">
          <input
            value={receipt.currency}
            onChange={(event) => onUpdateMeta("currency", event.target.value)}
            placeholder="Currency"
            className="rounded-2xl border-2 border-slate-300 px-3 py-2"
          />
          <input
            type="number"
            min="0"
            step="0.01"
            value={receipt.service_charge}
            onChange={(event) =>
              onUpdateMeta("service_charge", event.target.value)
            }
            placeholder="Service charge"
            className="rounded-2xl border-2 border-slate-300 px-3 py-2"
          />
          <input
            type="number"
            min="0"
            step="0.01"
            value={receipt.gst}
            onChange={(event) => onUpdateMeta("gst", event.target.value)}
            placeholder="GST / tax"
            className="rounded-2xl border-2 border-slate-300 px-3 py-2"
          />
        </div>

        <div className="mt-4 rounded-2xl border-2 border-slate-300 bg-slate-50 p-3 text-sm text-slate-700">
          Subtotal: {formatMoney(receipt.subtotal)} {receipt.currency} | Total:{" "}
          {formatMoney(receipt.total)} {receipt.currency}
        </div>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:justify-between">
        <button
          type="button"
          onClick={onAddItem}
          className="rounded-2xl border-2 border-slate-300 bg-white px-4 py-3 font-semibold text-slate-800"
        >
          Add item
        </button>
        <button
          type="button"
          onClick={onSave}
          disabled={saving}
          className="rounded-2xl border-2 border-emerald-700 bg-emerald-200 px-5 py-3 font-semibold text-emerald-950 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save step 1"}
        </button>
      </div>
    </section>
  );
}
