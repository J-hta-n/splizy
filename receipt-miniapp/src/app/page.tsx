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
import {
  clamp,
  getItemIndivsQty,
  getUserIndivSplits,
  normaliseSharedItems,
} from "@/lib/utils";
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

  const [splitModalItemIndex, setSplitModalItemIndex] = useState<number | null>(
    null,
  );
  const [modalSelection, setModalSelection] = useState<string[]>([]);
  const [modalValidationError, setModalValidationError] = useState<
    string | null
  >(null);

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
      const indivsQty = getItemIndivsQty(item);
      const sharedQty = Math.max(0, item.quantity - indivsQty);
      const unitPrice = item.quantity > 0 ? item.subtotal / item.quantity : 0;
      return { item, index, indivsQty, sharedQty, unitPrice };
    });
  }, [receipt.items]);

  const saveData = async () => {
    if (!groupId) {
      setError("Missing group_id query parameter");
      return null;
    }

    const normalizedReceipt: Receipt = {
      ...receipt,
      items: normaliseSharedItems(receipt, users),
    };

    const payload: TempReceiptPayload = {
      last_receipt: {
        receipt: normalizedReceipt,
        users,
      },
      last_confirmation: true,
    };

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
      nextItems[itemIndex] = editItem;

      const assignmentIndex = editItem.indiv.findIndex(
        (entry) => entry.username === selectedUser,
      );

      const curQty =
        assignmentIndex >= 0 ? editItem.indiv[assignmentIndex].quantity : 0;
      const othersQty = editItem.indiv
        .filter((entry) => entry.username !== selectedUser)
        .reduce((sum, entry) => sum + entry.quantity, 0);
      const maxAllowed = Math.max(0, editItem.quantity - othersQty);
      const nextQty = clamp(curQty + delta, 0, maxAllowed);

      if (nextQty <= 0) {
        editItem.indiv = editItem.indiv.filter(
          (entry) => entry.username !== selectedUser,
        );
      } else if (assignmentIndex >= 0) {
        editItem.indiv[assignmentIndex] = {
          ...editItem.indiv[assignmentIndex],
          quantity: nextQty,
        };
      } else {
        editItem.indiv.push({ username: selectedUser, quantity: nextQty });
      }

      // If indiv now covers all quantity, there is nothing left to share
      const newIndivsQty = othersQty + (nextQty - curQty);
      if (newIndivsQty >= editItem.quantity) {
        editItem.shared = [];
      }

      return { ...cur, items: nextItems };
    });
  };

  const openSplitModal = (itemIndex: number) => {
    const currentShared = receipt.items[itemIndex]?.shared ?? [];
    setModalSelection(currentShared.length >= 2 ? currentShared : users);
    setModalValidationError(null);
    setSplitModalItemIndex(itemIndex);
  };

  const closeSplitModal = () => {
    setSplitModalItemIndex(null);
    setModalValidationError(null);
  };

  const confirmSplitSelection = () => {
    if (splitModalItemIndex === null) return;

    if (modalSelection.length < 2) {
      setModalValidationError(
        "Please select at least 2 users to share this item.",
      );
      return;
    }

    const newShared = [...modalSelection];
    setReceipt((cur) => {
      if (!cur.items[splitModalItemIndex]) return cur;
      const nextItems = [...cur.items];
      nextItems[splitModalItemIndex] = {
        ...nextItems[splitModalItemIndex],
        shared: newShared,
      };
      return { ...cur, items: nextItems };
    });
    setModalValidationError(null);
    setSplitModalItemIndex(null);
  };

  const toggleModalUser = (user: string) => {
    setModalValidationError(null);
    setModalSelection((current) =>
      current.includes(user)
        ? current.filter((name) => name !== user)
        : [...current, user],
    );
  };

  const toggleAllModalUsers = () => {
    setModalValidationError(null);
    setModalSelection((current) =>
      current.length === users.length ? [] : [...users],
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
                splitModalItemIndex={splitModalItemIndex}
                modalSelection={modalSelection}
                modalValidationError={modalValidationError}
                areAllUsersSelected={
                  users.length > 0 && modalSelection.length === users.length
                }
                onOpenSplitModal={openSplitModal}
                onCloseSplitModal={closeSplitModal}
                onToggleModalUser={toggleModalUser}
                onToggleAllModalUsers={toggleAllModalUsers}
                onConfirmSplitSelection={confirmSplitSelection}
                isConfirmDisabled={modalSelection.length < 2}
                onBack={() => setStep(2)}
                onSave={saveData}
              />
            ) : null}
          </>
        )}
      </div>
    </main>
  );
}
