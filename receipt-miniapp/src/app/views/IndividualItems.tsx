import { IndividualAssignment, ItemSummary } from "./types";

type IndividualItemsProps = {
  users: string[];
  selectedUser: string | null;
  selectedUserIndiv: IndividualAssignment | null;
  itemSummaries: ItemSummary[];
  currency: string;
  saving: boolean;
  formatMoney: (value: number) => string;
  onSelectUser: (user: string) => void;
  onAdjustQuantity: (itemIndex: number, delta: number) => void;
  onBack: () => void;
  onSave: () => void;
};

const UserCards = ({
  users,
  selectedUser,
  onSelectUser,
}: {
  users: string[];
  selectedUser: string | null;
  onSelectUser: (user: string) => void;
}) => {
  if (users.length === 0) {
    return (
      <div className="rounded-2xl border-2 border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
        No fixed users found in saved assignments.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      {users.map((user) => {
        const active = selectedUser === user;
        return (
          <button
            key={user}
            type="button"
            onClick={() => onSelectUser(user)}
            className={`rounded-2xl border-2 px-3 py-3 text-sm font-semibold ${
              active
                ? "border-emerald-700 bg-emerald-200 text-emerald-950"
                : "border-emerald-300 bg-emerald-100 text-emerald-900"
            }`}
          >
            {active ? `${user} (viewing)` : user}
          </button>
        );
      })}
    </div>
  );
};

const QuantityControl = ({
  value,
  onMinus,
  onPlus,
}: {
  value: number;
  onMinus: () => void;
  onPlus: () => void;
}) => (
  <div className="inline-flex items-center rounded-2xl border-2 border-slate-400 bg-amber-100">
    <button
      type="button"
      onClick={onMinus}
      className="px-4 py-2 text-xl font-bold text-slate-700"
    >
      -
    </button>
    <div className="min-w-10 border-x-2 border-slate-400 px-3 py-2 text-center font-bold text-slate-800">
      {value}
    </div>
    <button
      type="button"
      onClick={onPlus}
      className="px-4 py-2 text-xl font-bold text-slate-700"
    >
      +
    </button>
  </div>
);

export function IndividualItems({
  users,
  selectedUser,
  selectedUserIndiv,
  itemSummaries,
  currency,
  saving,
  formatMoney,
  onSelectUser,
  onAdjustQuantity,
  onBack,
  onSave,
}: IndividualItemsProps) {
  return (
    <section className="space-y-4">
      <div className="rounded-3xl border-2 border-emerald-300 bg-emerald-200 p-4 text-emerald-950">
        <p className="font-semibold">
          Step 2/3: Please assign non-shared items
        </p>
        <p className="mt-2 text-sm">
          Currently viewing for: {selectedUser ?? "-"}
        </p>
      </div>

      <UserCards
        users={users}
        selectedUser={selectedUser}
        onSelectUser={onSelectUser}
      />

      <div className="rounded-3xl border-2 border-slate-300 bg-white p-3 sm:p-4">
        <div className="mb-2 grid grid-cols-[1fr_auto] gap-3 text-sm font-semibold text-slate-700">
          <div className="rounded-2xl border-2 border-slate-300 bg-amber-100 px-3 py-2">
            Item, unit price
          </div>
          <div className="rounded-2xl border-2 border-slate-300 bg-amber-100 px-3 py-2">
            - | Qty | +
          </div>
        </div>

        <div className="space-y-2">
          {itemSummaries.map(({ item, index, key, unitPrice }) => {
            const currentQty = selectedUserIndiv?.quantities[key] ?? 0;
            return (
              <div
                key={key}
                className="grid grid-cols-[1fr_auto] items-center gap-3"
              >
                <div className="rounded-2xl border-2 border-slate-300 bg-amber-100 px-3 py-3 text-slate-900">
                  <div className="font-semibold">
                    {item.name || `Item ${index + 1}`}
                  </div>
                  <div className="text-sm text-slate-600">
                    {currency} {formatMoney(unitPrice)} | total qty{" "}
                    {item.quantity}
                  </div>
                </div>
                <QuantityControl
                  value={currentQty}
                  onMinus={() => onAdjustQuantity(index, -1)}
                  onPlus={() => onAdjustQuantity(index, 1)}
                />
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
          {saving ? "Saving..." : "Save step 2"}
        </button>
      </div>
    </section>
  );
}
