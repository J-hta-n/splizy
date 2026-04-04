"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Box,
  Card,
  CardContent,
  Step,
  StepLabel,
  Stepper,
  Typography,
} from "@mui/material";
import { ConfirmItems } from "./views/ConfirmItems";
import { IndividualItems } from "./views/IndividualItems";
import { SharedItems } from "./views/SharedItems";
import { ItemSummary } from "./views/types";
import {
  IndividualAssignment,
  Receipt,
  ReceiptBillSplit,
  SharedAssignment,
} from "./api/receipts/schema";
import { clamp, formatMoney, normalizeAssignments, unique } from "@/lib/utils";

const blankReceipt: Receipt = {
  items: [{ name: "", quantity: 1, subtotal: 0 }],
  subtotal: 0,
  service_charge: 0,
  gst: 0,
  total: 0,
  currency: "USD",
};

export default function Home() {
  const [groupId, setGroupId] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<Receipt>(blankReceipt);
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

        const data: ReceiptBillSplit = await response.json();
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

  const itemSummaries: ItemSummary[] = useMemo(() => {
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

  const saveData = async (payload: ReceiptBillSplit) => {
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

      await response.json();
      setMessage("Saved successfully.");
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save data");
      return false;
    } finally {
      setSaving(false);
    }
  };

  const updateStep1Item = (
    index: number,
    field: "name" | "quantity" | "subtotal",
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

  const removeStep1Items = (indices: number[]) => {
    const toDelete = new Set(indices);
    setReceipt((current) => {
      const items = current.items.filter((_, idx) => !toDelete.has(idx));
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
    { step: 1, title: "Confirm" },
    { step: 2, title: "Individual" },
    { step: 3, title: "Shared" },
  ];

  return (
    <main className="min-h-screen bg-[#eceff3] px-3 py-5 text-slate-900 sm:px-5">
      <div className="mx-auto w-full max-w-2xl space-y-4">
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
            <Card variant="outlined" sx={{ borderRadius: 3 }}>
              <CardContent sx={{ px: { xs: 1.5, sm: 3 }, py: 2 }}>
                <Stepper activeStep={step - 1} alternativeLabel>
                  {stepLabels.map((entry) => (
                    <Step key={entry.step} completed={step > entry.step}>
                      <StepLabel
                        onClick={() => setStep(entry.step as 1 | 2 | 3)}
                        sx={{ cursor: "pointer" }}
                      >
                        <Box>
                          <Typography fontWeight={700}>
                            Step {entry.step}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {entry.title}
                          </Typography>
                        </Box>
                      </StepLabel>
                    </Step>
                  ))}
                </Stepper>
              </CardContent>
            </Card>
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
            {step === 1 ? (
              <ConfirmItems
                receipt={receipt}
                saving={saving}
                formatMoney={formatMoney}
                onUpdateItem={updateStep1Item}
                onUpdateMeta={updateStep1Meta}
                onAddItem={addStep1Item}
                onRemoveItems={removeStep1Items}
                onSave={() => saveStep(1)}
              />
            ) : null}
            {step === 2 ? (
              <IndividualItems
                users={users}
                selectedUser={selectedUserStep2}
                selectedUserIndiv={selectedUserIndiv}
                itemSummaries={itemSummaries}
                currency={receipt.currency}
                saving={saving}
                formatMoney={formatMoney}
                onSelectUser={setSelectedUserStep2}
                onAdjustQuantity={updateIndividualQtyByDelta}
                onBack={() => setStep(1)}
                onSave={() => saveStep(2)}
              />
            ) : null}
            {step === 3 ? (
              <SharedItems
                users={users}
                itemSummaries={itemSummaries}
                currency={receipt.currency}
                saving={saving}
                sharedSelections={sharedSelections}
                splitModalItemIndex={splitModalItemIndex}
                modalSelection={modalSelection}
                formatMoney={formatMoney}
                onOpenSplitModal={openSplitModal}
                onCloseSplitModal={() => setSplitModalItemIndex(null)}
                onToggleModalUser={toggleModalUser}
                onConfirmSplitSelection={confirmSplitSelection}
                onBack={() => setStep(2)}
                onSave={() => saveStep(3)}
              />
            ) : null}
          </>
        )}
      </div>
    </main>
  );
}
