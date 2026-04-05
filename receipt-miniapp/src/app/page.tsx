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
import { ConfirmItems } from "./_components/ConfirmItems";
import { IndividualItems } from "./_components/IndividualItems";
import { SharedItems } from "./_components/SharedItems";
import { Receipt, TempReceiptPayload } from "./api/receipts/schema";
import { clamp, formatMoney, getUserIndivSplits } from "@/lib/utils";
import { ItemSummary, UserIndivSplit } from "@/lib/types";

const blankReceipt: Receipt = {
  items: [{ name: "", quantity: 1, subtotal: 0, indiv: [], shared: [] }],
  subtotal: 0,
  service_charge: 0,
  gst: 0,
  total: 0,
  currency: "SGD",
};

export default function Home() {
  const [groupId, setGroupId] = useState<string | null>(null);
  const [users, setUsers] = useState<string[]>([]);
  const [receipt, setReceipt] = useState<Receipt>(blankReceipt);
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [selectedUserStep2, setSelectedUserStep2] = useState<string | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [sharedSelections, setSharedSelections] = useState<string[][]>([]);
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

        const data: TempReceiptPayload = await response.json();
        const receipt = data.last_receipt.receipt ?? blankReceipt;
        setReceipt(receipt);

        const users = data.last_receipt.users;

        setUsers(users);
        if (users.length > 0) {
          setSelectedUserStep2(users[0]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load data");
      } finally {
        setLoading(false);
      }
    };

    fetchReceipt();
  }, [groupId]);

  const userIndivSplits: UserIndivSplit[] = useMemo(
    () => getUserIndivSplits(receipt, users),
    [receipt, users],
  );

  const itemSummaries: ItemSummary[] = useMemo(() => {
    return receipt.items.map((item, index) => {
      const indivsQty = item.indiv.reduce((sum, i) => sum + i.quantity, 0);
      const sharedQty = Math.max(0, item.quantity - indivsQty);
      const unitPrice = item.quantity > 0 ? item.subtotal / item.quantity : 0;
      return { item, index, indivsQty, sharedQty, unitPrice };
    });
  }, [receipt.items]);

  const saveData = async (payload: TempReceiptPayload) => {
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
    setReceipt((cur) => {
      const nextItems = [...cur.items];
      const editItem = nextItems[index];
      if (field === "name") editItem.name = value;
      if (field === "quantity") editItem.quantity = Number(value);
      if (field === "subtotal") editItem.subtotal = Number(value);

      const subtotal = nextItems.reduce((sum, item) => sum + item.subtotal, 0);
      const total = subtotal + cur.service_charge + cur.gst;
      return { ...cur, items: nextItems, subtotal, total };
    });
  };

  const updateStep1Meta = (
    field: "currency" | "service_charge" | "gst",
    value: string,
  ) => {
    setReceipt((cur) => {
      const next = { ...cur };
      if (field === "currency") {
        next.currency = value;
      } else {
        next[field] = Number(value);
      }
      next.total = next.subtotal + next.service_charge + next.gst;
      return next;
    });
  };

  const addStep1Item = () => {
    setReceipt((cur) => ({
      ...cur,
      items: [
        ...cur.items,
        { name: "<New Item>", quantity: 1, subtotal: 1, indiv: [], shared: [] },
      ],
    }));
  };

  const removeStep1Items = (indices: number[]) => {
    const toDelete = new Set(indices);
    setReceipt((cur) => {
      const items = cur.items.filter((_, idx) => !toDelete.has(idx));
      const subtotal = items.reduce((sum, item) => sum + item.subtotal, 0);
      const total = subtotal + cur.service_charge + cur.gst;
      return { ...cur, items, subtotal, total };
    });
  };

  // Delta is either +1 or -1
  const updateIndivItemQtyByDelta = (itemIndex: number, delta: number) => {
    if (!selectedUserStep2) return;

    const selectedUser = selectedUserStep2;

    setReceipt((cur) => {
      if (!cur.items[itemIndex]) return cur;

      const nextItems = [...cur.items];
      const editItem = {
        ...nextItems[itemIndex],
        indiv: [...nextItems[itemIndex].indiv],
      };
      const assignmentIndex = editItem.indiv.findIndex(
        (entry) => entry.username === selectedUser,
      );
      const curQty =
        assignmentIndex >= 0 ? editItem.indiv[assignmentIndex].quantity : 0;
      const othersQty = editItem.indiv.reduce(
        (sum, entry, index) =>
          index === assignmentIndex ? sum : sum + entry.quantity,
        0,
      );
      const maxAllowed = Math.max(0, editItem.quantity - othersQty);
      const nextQty = clamp(curQty + delta, 0, maxAllowed);

      if (nextQty <= 0) {
        if (assignmentIndex >= 0) {
          editItem.indiv = editItem.indiv.filter(
            (_, index) => index !== assignmentIndex,
          );
        }
      } else if (assignmentIndex >= 0) {
        editItem.indiv[assignmentIndex] = {
          ...editItem.indiv[assignmentIndex],
          quantity: nextQty,
        };
      } else {
        editItem.indiv.push({ username: selectedUser, quantity: nextQty });
      }

      nextItems[itemIndex] = editItem;
      return { ...cur, items: nextItems };
    });
  };

  const openSplitModal = (itemIndex: number) => {
    setModalSelection(sharedSelections[itemIndex] ?? []);
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

  const selectedItemAssignments =
    userIndivSplits.find((entry) => entry.username === selectedUserStep2)
      ?.indivSplit ?? null;

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
                formatMoney={formatMoney}
                onUpdateItem={updateStep1Item}
                onUpdateMeta={updateStep1Meta}
                onAddItem={addStep1Item}
                onRemoveItems={removeStep1Items}
                onNext={() => setStep(2)}
              />
            ) : null}
            {step === 2 ? (
              <IndividualItems
                users={users}
                selectedUser={selectedUserStep2}
                selectedItemAssignments={selectedItemAssignments}
                itemSummaries={itemSummaries}
                currency={receipt.currency}
                formatMoney={formatMoney}
                onSelectUser={setSelectedUserStep2}
                onAdjustQuantity={updateIndivItemQtyByDelta}
                onBack={() => setStep(1)}
                onNext={() => setStep(3)}
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
                onSave={() =>
                  saveData({
                    last_confirmation: true,
                    last_receipt: { users, receipt },
                  })
                }
              />
            ) : null}
          </>
        )}
      </div>
    </main>
  );
}
