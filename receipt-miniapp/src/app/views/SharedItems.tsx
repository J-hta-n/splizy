import { ItemSummary } from "./types";

type SharedItemsProps = {
  users: string[];
  itemSummaries: ItemSummary[];
  currency: string;
  saving: boolean;
  sharedSelections: Record<string, string[]>;
  splitModalItemIndex: number | null;
  modalSelection: string[];
  formatMoney: (value: number) => string;
  onOpenSplitModal: (itemIndex: number) => void;
  onCloseSplitModal: () => void;
  onToggleModalUser: (user: string) => void;
  onConfirmSplitSelection: () => void;
  onBack: () => void;
  onSave: () => void;
};

export function SharedItems({
  users,
  itemSummaries,
  currency,
  saving,
  sharedSelections,
  splitModalItemIndex,
  modalSelection,
  formatMoney,
  onOpenSplitModal,
  onCloseSplitModal,
  onToggleModalUser,
  onConfirmSplitSelection,
  onBack,
  onSave,
}: SharedItemsProps) {
  const currentModalItem =
    splitModalItemIndex === null
      ? null
      : itemSummaries.find((entry) => entry.index === splitModalItemIndex);

  return (
    <>
      <section className="space-y-4">
        <div className="rounded-3xl border-2 border-emerald-300 bg-emerald-200 p-4 text-emerald-950">
          <p className="font-semibold">Step 3/3: Please assign shared items</p>
          <p className="mt-2 text-sm">
            Tap "Split among" for each item to choose users sharing it.
          </p>
        </div>

        <div className="rounded-3xl border-2 border-slate-300 bg-white p-3 sm:p-4">
          <div className="mb-2 grid grid-cols-[1fr_auto] gap-3 text-sm font-semibold text-slate-700">
            <div className="rounded-2xl border-2 border-slate-300 bg-amber-100 px-3 py-2">
              Item, qty, total cost
            </div>
            <div className="rounded-2xl border-2 border-slate-300 bg-amber-100 px-3 py-2">
              Split among
            </div>
          </div>

          <div className="space-y-2">
            {itemSummaries.map(({ item, key, leftover, index }) => {
              const selected = sharedSelections[key] ?? [];
              return (
                <div
                  key={key}
                  className="grid grid-cols-[1fr_auto] items-center gap-3"
                >
                  <div className="rounded-2xl border-2 border-slate-300 bg-amber-100 px-3 py-3 text-slate-900">
                    <div className="font-semibold">
                      {item.name || "Unnamed item"}
                    </div>
                    <div className="text-sm text-slate-700">
                      qty left: {leftover}, total {currency}{" "}
                      {formatMoney(item.subtotal ?? 0)}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => onOpenSplitModal(index)}
                    className="rounded-2xl border-2 border-slate-300 bg-amber-100 px-3 py-3 text-left text-sm font-semibold text-slate-800"
                  >
                    {selected.length > 0 ? selected.join(", ") : "Select users"}
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row sm:justify-between">
          <button
            type="button"
            onClick={onBack}
            className="rounded-2xl border-2 border-slate-300 bg-white px-4 py-3 font-semibold text-slate-800"
          >
            Back
          </button>
          <button
            type="button"
            onClick={onSave}
            disabled={saving || users.length === 0}
            className="rounded-2xl border-2 border-emerald-700 bg-emerald-200 px-5 py-3 font-semibold text-emerald-950 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save step 3"}
          </button>
        </div>
      </section>

      {currentModalItem ? (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/45 p-4 sm:items-center">
          <div className="w-full max-w-md rounded-3xl border-2 border-slate-300 bg-white p-4 shadow-xl">
            <h3 className="text-lg font-bold">
              Select users for {currentModalItem.item.name || "item"}
            </h3>
            <p className="mt-1 text-sm text-slate-600">
              Leftover qty: {currentModalItem.leftover}
            </p>

            <div className="mt-3 space-y-2">
              {users.map((user) => {
                const checked = modalSelection.includes(user);
                return (
                  <label
                    key={user}
                    className="flex cursor-pointer items-center justify-between rounded-2xl border-2 border-slate-300 bg-slate-50 px-3 py-2"
                  >
                    <span className="font-medium text-slate-800">{user}</span>
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => onToggleModalUser(user)}
                      className="h-5 w-5"
                    />
                  </label>
                );
              })}
            </div>

            <div className="mt-4 flex gap-2">
              <button
                type="button"
                onClick={onCloseSplitModal}
                className="flex-1 rounded-2xl border-2 border-slate-300 bg-white px-4 py-2 font-semibold text-slate-700"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={onConfirmSplitSelection}
                className="flex-1 rounded-2xl border-2 border-emerald-700 bg-emerald-200 px-4 py-2 font-semibold text-emerald-950"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
