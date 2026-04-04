"use client";

import { useEffect, useMemo, useState } from "react";

type ReceiptItem = {
  name: string;
  quantity: number;
  subtotal: number | null;
};

type LastReceipt = {
  items: ReceiptItem[];
  subtotal: number;
  service_charge: number;
  gst: number;
  total: number;
  currency: string;
};

type IndividualAssignment = {
  user: string;
  quantities: Record<string, number>;
};

type SharedAssignment = {
  user: string;
  quantities: Record<string, number>;
};

type ReceiptRow = {
  id: number;
  created_at: string;
  group_id: number | null;
  last_receipt: LastReceipt | null;
  last_indiv: IndividualAssignment[] | null;
  last_shared: SharedAssignment[] | null;
  last_confirmation: boolean | null;
};

const blankReceipt: LastReceipt = {
  items: [{ name: "", quantity: 1, subtotal: 0 }],
  subtotal: 0,
  service_charge: 0,
  gst: 0,
  total: 0,
  currency: "USD",
};

const formatMoney = (value: number) => {
  return Number.isFinite(value) ? value.toFixed(2) : "0.00";
};

const clamp = (value: number, min: number, max: number) => {
  return Math.max(min, Math.min(max, value));
};

const unique = (values: string[]) => {
  return [...new Set(values.map((value) => value.trim()).filter(Boolean))];
};

const normalizeAssignments = (
  users: string[],
  existing: IndividualAssignment[] | SharedAssignment[] | null | undefined,
) => {
  return users.map((user) => {
    const found = existing?.find((entry) => entry.user === user);
    return {
      user,
      quantities: { ...(found?.quantities ?? {}) },
    };
  });
};

export default function Home() {
  const [groupId, setGroupId] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<LastReceipt>(blankReceipt);
  const [lastIndiv, setLastIndiv] = useState<IndividualAssignment[]>([]);
  const [lastShared, setLastShared] = useState<SharedAssignment[]>([]);
  const [users, setUsers] = useState<string[]>([]);
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [selectedUserStep2, setSelectedUserStep2] = useState<string | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [sharedSelections, setSharedSelections] = useState<
    Record<string, string[]>
  >({});
  const [splitModalItemIndex, setSplitModalItemIndex] = useState<number | null>(
    null,
  );
  const [modalSelection, setModalSelection] = useState<string[]>([]);

  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    setGroupId(query.get("group_id"));
  }, []);

  useEffect(() => {
    if (!groupId) {
      setLoading(false);
      return;
    }

    const fetchReceipt = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(
          `/api/receipts?group_id=${encodeURIComponent(groupId)}`,
        );
        if (!response.ok) {
          const body = await response.json();
          throw new Error(body.error || "Failed to load receipt row");
        }

        const data: ReceiptRow = await response.json();
        const nextReceipt = data.last_receipt ?? blankReceipt;
        setReceipt(nextReceipt);

        const serverUsers = unique([
          ...(data.last_indiv?.map((entry) => entry.user) ?? []),
          ...(data.last_shared?.map((entry) => entry.user) ?? []),
        ]);

        setUsers(serverUsers);
        if (serverUsers.length > 0) {
          setSelectedUserStep2(serverUsers[0]);
        }

        const nextIndiv = normalizeAssignments(serverUsers, data.last_indiv);
        const nextShared = normalizeAssignments(serverUsers, data.last_shared);
        setLastIndiv(nextIndiv);
        setLastShared(nextShared);

        const selections: Record<string, string[]> = {};
        nextReceipt.items.forEach((_, index) => {
          const key = String(index);
          selections[key] = nextShared
            .filter((entry) => (entry.quantities[key] ?? 0) > 0)
            .map((entry) => entry.user);
        });
        setSharedSelections(selections);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load data");
      } finally {
        setLoading(false);
      }
    };

    fetchReceipt();
  }, [groupId]);

  const itemSummaries = useMemo(() => {
    return receipt.items.map((item, index) => {
      const key = String(index);
      const indivTotal = lastIndiv.reduce(
        (sum, entry) => sum + (entry.quantities[key] ?? 0),
        0,
      );
      const leftover = Math.max(0, item.quantity - indivTotal);
      const unitPrice =
        item.quantity > 0 ? (item.subtotal ?? 0) / item.quantity : 0;
      return { item, index, key, indivTotal, leftover, unitPrice };
    });
  }, [receipt.items, lastIndiv]);

  const saveData = async (payload: {
    last_receipt?: LastReceipt;
    last_indiv?: IndividualAssignment[];
    last_shared?: SharedAssignment[];
  }) => {
    if (!groupId) {
      setError("Missing group_id query parameter");
      return null;
    }

    setSaving(true);
    setError(null);
    setMessage(null);

    try {
      const response = await fetch(
        `/api/receipts?group_id=${encodeURIComponent(groupId)}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        },
      );
      if (!response.ok) {
        const body = await response.json();
        throw new Error(body.error || "Failed to save receipt row");
      }

      const data: ReceiptRow = await response.json();
      setMessage("Saved successfully.");
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save data");
      return null;
    } finally {
      setSaving(false);
    }
  };

  const updateStep1Item = (
    index: number,
    field: keyof ReceiptItem,
    value: string,
  ) => {
    setReceipt((current) => {
      const nextItems = [...current.items];
      const nextItem = { ...nextItems[index] };
      if (field === "name") nextItem.name = value;
      if (field === "quantity")
        nextItem.quantity = Number.isFinite(Number(value)) ? Number(value) : 0;
      if (field === "subtotal")
        nextItem.subtotal = value === "" ? null : Number(value);
      nextItems[index] = nextItem;

      const subtotal = nextItems.reduce(
        (sum, item) => sum + (item.subtotal ?? 0),
        0,
      );
      const total = subtotal + current.service_charge + current.gst;
      return { ...current, items: nextItems, subtotal, total };
    });
  };

  const updateStep1Meta = (
    field: "currency" | "service_charge" | "gst",
    value: string,
  ) => {
    setReceipt((current) => {
      const next = { ...current };
      if (field === "currency") {
        next.currency = value;
      } else {
        next[field] = Number.isFinite(Number(value)) ? Number(value) : 0;
      }
      next.total = next.subtotal + next.service_charge + next.gst;
      return next;
    });
  };

  const addStep1Item = () => {
    setReceipt((current) => ({
      ...current,
      items: [...current.items, { name: "", quantity: 1, subtotal: 0 }],
    }));
  };

  const removeStep1Item = (index: number) => {
    setReceipt((current) => {
      const items = current.items.filter((_, idx) => idx !== index);
      const subtotal = items.reduce(
        (sum, item) => sum + (item.subtotal ?? 0),
        0,
      );
      return {
        ...current,
        items,
        subtotal,
        total: subtotal + current.service_charge + current.gst,
      };
    });
  };

  const updateIndividualQtyByDelta = (itemIndex: number, delta: number) => {
    if (!selectedUserStep2) return;

    const selectedUser = selectedUserStep2;

    setLastIndiv((current) => {
      const next = normalizeAssignments(users, current);
      const targetIndex = next.findIndex(
        (entry) => entry.user === selectedUser,
      );
      if (targetIndex < 0) return next;

      const key = String(itemIndex);
      const currentValue = next[targetIndex].quantities[key] ?? 0;
      const othersTotal = next
        .filter((entry) => entry.user !== selectedUser)
        .reduce((sum, entry) => sum + (entry.quantities[key] ?? 0), 0);
      const maxAllowed = Math.max(
        0,
        receipt.items[itemIndex].quantity - othersTotal,
      );
      const nextValue = clamp(currentValue + delta, 0, maxAllowed);

      next[targetIndex] = {
        ...next[targetIndex],
        quantities: {
          ...next[targetIndex].quantities,
          [key]: nextValue,
        },
      };

      return next;
    });
  };

  const buildSharedAssignments = () => {
    const base = normalizeAssignments(users, lastShared).map((entry) => ({
      user: entry.user,
      quantities: {} as Record<string, number>,
    }));

    itemSummaries.forEach(({ key, leftover }) => {
      const selected = sharedSelections[key] ?? [];
      if (leftover <= 0 || selected.length === 0) return;

      const perUserBase = Math.floor(leftover / selected.length);
      let remainder = leftover % selected.length;

      selected.forEach((user) => {
        const idx = base.findIndex((entry) => entry.user === user);
        if (idx < 0) return;
        const extra = remainder > 0 ? 1 : 0;
        if (remainder > 0) remainder -= 1;
        base[idx].quantities[key] = perUserBase + extra;
      });
    });

    return base;
  };

  const openSplitModal = (itemIndex: number) => {
    const key = String(itemIndex);
    setModalSelection(sharedSelections[key] ?? []);
    setSplitModalItemIndex(itemIndex);
  };

  const confirmSplitSelection = () => {
    if (splitModalItemIndex === null) return;
    const key = String(splitModalItemIndex);
    setSharedSelections((current) => ({ ...current, [key]: modalSelection }));
    setSplitModalItemIndex(null);
  };

  const toggleModalUser = (user: string) => {
    setModalSelection((current) =>
      current.includes(user)
        ? current.filter((name) => name !== user)
        : [...current, user],
    );
  };

  const saveStep = async (stepNumber: 1 | 2 | 3) => {
    if (stepNumber === 1) {
      const ok = await saveData({ last_receipt: receipt });
      if (ok) setStep(2);
      return;
    }

    if (stepNumber === 2) {
      const normalized = normalizeAssignments(users, lastIndiv);
      setLastIndiv(normalized);
      const ok = await saveData({ last_indiv: normalized });
      if (ok) setStep(3);
      return;
    }

    const computedShared = buildSharedAssignments();
    setLastShared(computedShared);
    await saveData({ last_shared: computedShared });
  };

  const selectedUserIndiv =
    lastIndiv.find((entry) => entry.user === selectedUserStep2) ?? null;

  const stepLabels = [
    { step: 1, title: "Confirm receipt" },
    { step: 2, title: "Assign non-shared" },
    { step: 3, title: "Assign shared" },
  ];

  const renderStepHeader = () => (
    <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
      {stepLabels.map((entry) => (
        <button
          key={entry.step}
          type="button"
          onClick={() => setStep(entry.step as 1 | 2 | 3)}
          className={`rounded-2xl border-2 px-4 py-2 text-sm font-semibold transition ${
            step === entry.step
              ? "border-emerald-700 bg-emerald-200 text-emerald-950"
              : "border-slate-300 bg-white text-slate-700"
          }`}
        >
          {entry.step}. {entry.title}
        </button>
      ))}
    </div>
  );

  const renderStepOne = () => (
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
                  updateStep1Item(index, "name", event.target.value)
                }
                placeholder="Item name"
                className="rounded-2xl border-2 border-slate-300 px-3 py-2"
              />
              <input
                type="number"
                min="0"
                value={item.quantity}
                onChange={(event) =>
                  updateStep1Item(index, "quantity", event.target.value)
                }
                className="rounded-2xl border-2 border-slate-300 px-3 py-2"
              />
              <input
                type="number"
                min="0"
                step="0.01"
                value={item.subtotal ?? ""}
                onChange={(event) =>
                  updateStep1Item(index, "subtotal", event.target.value)
                }
                className="rounded-2xl border-2 border-slate-300 px-3 py-2"
              />
              <button
                type="button"
                onClick={() => removeStep1Item(index)}
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
            onChange={(event) =>
              updateStep1Meta("currency", event.target.value)
            }
            placeholder="Currency"
            className="rounded-2xl border-2 border-slate-300 px-3 py-2"
          />
          <input
            type="number"
            min="0"
            step="0.01"
            value={receipt.service_charge}
            onChange={(event) =>
              updateStep1Meta("service_charge", event.target.value)
            }
            placeholder="Service charge"
            className="rounded-2xl border-2 border-slate-300 px-3 py-2"
          />
          <input
            type="number"
            min="0"
            step="0.01"
            value={receipt.gst}
            onChange={(event) => updateStep1Meta("gst", event.target.value)}
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
          onClick={addStep1Item}
          className="rounded-2xl border-2 border-slate-300 bg-white px-4 py-3 font-semibold text-slate-800"
        >
          Add item
        </button>
        <button
          type="button"
          onClick={() => saveStep(1)}
          disabled={saving}
          className="rounded-2xl border-2 border-emerald-700 bg-emerald-200 px-5 py-3 font-semibold text-emerald-950 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save step 1"}
        </button>
      </div>
    </section>
  );

  const renderUserCards = (
    selectedUser: string | null,
    onSelect: (user: string) => void,
    showViewing = true,
  ) => {
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
              onClick={() => onSelect(user)}
              className={`rounded-2xl border-2 px-3 py-3 text-sm font-semibold ${
                active
                  ? "border-emerald-700 bg-emerald-200 text-emerald-950"
                  : "border-emerald-300 bg-emerald-100 text-emerald-900"
              }`}
            >
              {showViewing && active ? `${user} (viewing)` : user}
            </button>
          );
        })}
      </div>
    );
  };

  const renderQuantityControl = (
    value: number,
    onMinus: () => void,
    onPlus: () => void,
  ) => (
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

  const renderStepTwo = () => (
    <section className="space-y-4">
      <div className="rounded-3xl border-2 border-emerald-300 bg-emerald-200 p-4 text-emerald-950">
        <p className="font-semibold">
          Step 2/3: Please assign non-shared items
        </p>
        <p className="mt-2 text-sm">
          Currently viewing for: {selectedUserStep2 ?? "-"}
        </p>
      </div>

      {renderUserCards(selectedUserStep2, setSelectedUserStep2)}

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
          {itemSummaries.map(({ item, index, unitPrice }) => {
            const key = String(index);
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
                    {receipt.currency} {formatMoney(unitPrice)} | total qty{" "}
                    {item.quantity}
                  </div>
                </div>
                {renderQuantityControl(
                  currentQty,
                  () => updateIndividualQtyByDelta(index, -1),
                  () => updateIndividualQtyByDelta(index, 1),
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:justify-between">
        <button
          type="button"
          onClick={() => setStep(1)}
          className="rounded-2xl border-2 border-slate-300 bg-white px-4 py-3 font-semibold text-slate-800"
        >
          Back
        </button>
        <button
          type="button"
          onClick={() => saveStep(2)}
          disabled={saving || users.length === 0}
          className="rounded-2xl border-2 border-emerald-700 bg-emerald-200 px-5 py-3 font-semibold text-emerald-950 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save step 2"}
        </button>
      </div>
    </section>
  );

  const renderStepThree = () => (
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
          {itemSummaries.map(({ item, key, leftover }) => {
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
                    qty left: {leftover}, total {receipt.currency}{" "}
                    {formatMoney(item.subtotal ?? 0)}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => openSplitModal(Number(key))}
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
          onClick={() => setStep(2)}
          className="rounded-2xl border-2 border-slate-300 bg-white px-4 py-3 font-semibold text-slate-800"
        >
          Back
        </button>
        <button
          type="button"
          onClick={() => saveStep(3)}
          disabled={saving || users.length === 0}
          className="rounded-2xl border-2 border-emerald-700 bg-emerald-200 px-5 py-3 font-semibold text-emerald-950 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save step 3"}
        </button>
      </div>
    </section>
  );

  const currentModalItem =
    splitModalItemIndex === null
      ? null
      : itemSummaries.find((entry) => entry.index === splitModalItemIndex);

  return (
    <main className="min-h-screen bg-[#eceff3] px-3 py-5 text-slate-900 sm:px-5">
      <div className="mx-auto w-full max-w-2xl space-y-4">
        <div className="rounded-3xl border-2 border-slate-400 bg-white p-4">
          <h1 className="text-3xl font-bold">Receipt miniapp</h1>
          <p className="mt-1 text-slate-700">
            Simple 3-step flow for receipt split.
          </p>
        </div>

        {!groupId ? (
          <div className="rounded-3xl border-2 border-rose-300 bg-rose-50 p-4 text-rose-900">
            Missing group_id in URL.
          </div>
        ) : loading ? (
          <div className="rounded-3xl border-2 border-slate-300 bg-white p-4">
            Loading...
          </div>
        ) : (
          <>
            {renderStepHeader()}
            {error ? (
              <div className="rounded-3xl border-2 border-rose-300 bg-rose-50 p-4 text-rose-900">
                {error}
              </div>
            ) : null}
            {message ? (
              <div className="rounded-3xl border-2 border-emerald-300 bg-emerald-50 p-4 text-emerald-900">
                {message}
              </div>
            ) : null}
            {step === 1 && renderStepOne()}
            {step === 2 && renderStepTwo()}
            {step === 3 && renderStepThree()}
          </>
        )}
      </div>

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
                      onChange={() => toggleModalUser(user)}
                      className="h-5 w-5"
                    />
                  </label>
                );
              })}
            </div>

            <div className="mt-4 flex gap-2">
              <button
                type="button"
                onClick={() => setSplitModalItemIndex(null)}
                className="flex-1 rounded-2xl border-2 border-slate-300 bg-white px-4 py-2 font-semibold text-slate-700"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmSplitSelection}
                className="flex-1 rounded-2xl border-2 border-emerald-700 bg-emerald-200 px-4 py-2 font-semibold text-emerald-950"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}
