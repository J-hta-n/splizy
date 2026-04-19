"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Step,
  StepLabel,
  Stepper,
  Stack,
  Typography,
} from "@mui/material";
import { ConfirmItems } from "./_components/ConfirmItems";
import { IndividualItems } from "./_components/IndividualItems";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { SharedItems } from "./_components/SharedItems";
import {
  PatchTempReceiptSchema,
  TempReceiptRow,
} from "./api/expenses/tempReceipt/schema";
import {
  clamp,
  formatMoney,
  getItemIndivsQty,
  getUserIndivSplits,
  normaliseSharedItems,
} from "@/lib/utils";
import { ItemSummary, UserIndivSplit } from "@/lib/types";
import { Expense, PostExpenseSchema, Receipt } from "./api/expenses/schema";
import { getPayeesFromReceipt } from "@/lib/db/utils";

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
  const [expenseId, setExpenseId] = useState<string | null>(null);
  const [users, setUsers] = useState<string[]>([]);
  const [receipt, setReceipt] = useState<Receipt>(blankReceipt);
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [expenseTitle, setExpenseTitle] = useState("");
  const [paidBy, setPaidBy] = useState("");
  const [selectedUserStep2, setSelectedUserStep2] = useState<string | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [step1GuardError, setStep1GuardError] = useState<string | null>(null);
  const [initialFetchedTotal, setInitialFetchedTotal] = useState<number | null>(
    null,
  );

  const [splitModalItemIndex, setSplitModalItemIndex] = useState<number | null>(
    null,
  );
  const [modalSelection, setModalSelection] = useState<string[]>([]);
  const [modalValidationError, setModalValidationError] = useState<
    string | null
  >(null);
  const [submitConfirmOpen, setSubmitConfirmOpen] = useState(false);
  const [submittedSuccessfully, setSubmittedSuccessfully] = useState(false);

  const recomputeReceiptTotals = (input: Receipt): Receipt => {
    const subtotal = input.items.reduce(
      (sum, item) => sum + Number(item.subtotal || 0),
      0,
    );
    const serviceCharge = Number(input.service_charge || 0);
    const gst = Number(input.gst || 0);
    return {
      ...input,
      subtotal,
      service_charge: serviceCharge,
      gst,
      total: subtotal + serviceCharge + gst,
    };
  };

  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    const groupId = query.get("group_id");
    const expenseId = query.get("expense_id");
    setGroupId(groupId);
    setExpenseId(expenseId);
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
        let receipt: Receipt;
        let users: string[];
        let expenseTitle: string;
        let paidBy: string;
        if (expenseId) {
          const response = await fetch(
            `/api/expenses/${encodeURIComponent(expenseId)}`,
          );
          if (!response.ok) {
            const body = await response.json();
            throw new Error(
              body.error || "Failed to fetch receipt expense for editing",
            );
          }

          const data: Expense = await response.json();
          receipt = data.receipt;
          users = data.payees.map((payee) => payee.user);
          expenseTitle = data.title;
          paidBy = data.paid_by;
        } else {
          const response = await fetch(
            `/api/expenses/tempReceipt?group_id=${encodeURIComponent(groupId)}`,
          );
          if (!response.ok) {
            const body = await response.json();
            throw new Error(
              body.error || "Failed to fetch new receipt for adding expense",
            );
          }

          const data: TempReceiptRow = await response.json();
          receipt = data.last_receipt.receipt;
          users = data.last_receipt.users;
          expenseTitle = data.title ?? "";
          paidBy = data.paid_by ?? users[0] ?? "";
        }

        setInitialFetchedTotal(Number(receipt.total || 0));
        setReceipt(recomputeReceiptTotals(receipt));
        setUsers(users);
        setExpenseTitle(expenseTitle);
        setPaidBy(paidBy);
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
  }, [groupId, expenseId]);

  useEffect(() => {
    if (users.length === 0) {
      setPaidBy("");
      return;
    }

    setPaidBy((current) => (users.includes(current) ? current : users[0]));
  }, [users]);

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

  const normalizedReceiptForSubmit: Receipt = useMemo(
    () => ({
      ...receipt,
      items: normaliseSharedItems(receipt, users),
    }),
    [receipt, users],
  );

  const payees = useMemo(
    () => getPayeesFromReceipt(users, normalizedReceiptForSubmit),
    [normalizedReceiptForSubmit, users],
  );

  const saveData = async () => {
    if (!groupId) {
      setError("Missing group_id. Unable to submit.");
      return null;
    }

    if (!paidBy) {
      setError("Please select who paid before submitting.");
      return null;
    }

    setSaving(true);
    setError(null);
    setMessage(null);

    try {
      if (expenseId) {
        const expensePayload: PostExpenseSchema = {
          title: expenseTitle.trim() || "Untitled expense",
          paid_by: paidBy,
          group_id: Number(groupId),
          users,
          receipt: normalizedReceiptForSubmit,
        };
        const response = await fetch(`/api/expenses/${expenseId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(expensePayload),
        });
        if (!response.ok) {
          const body = await response.json();
          throw new Error(body.error || "Failed to update expense");
        }
      } else {
        const expensePayload: PostExpenseSchema = {
          title: expenseTitle.trim() || "Untitled expense",
          paid_by: paidBy,
          group_id: Number(groupId),
          users,
          receipt: normalizedReceiptForSubmit,
        };
        const postResponse = await fetch(`/api/expenses`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(expensePayload),
        });
        const postBody = await postResponse.json();
        if (!postResponse.ok) {
          throw new Error(postBody.error || "Failed to submit expense");
        }
        const expenseId = postBody.expense?.id;
        if (!expenseId) {
          throw new Error("Failed to submit expense");
        }

        const tempReceiptPayload: PatchTempReceiptSchema = {
          title: expenseTitle.trim() || "Untitled expense",
          paid_by: paidBy,
          expense_id: expenseId,
          last_receipt: {
            receipt: normalizedReceiptForSubmit,
            users,
          },
        };
        const patchResponse = await fetch(
          `/api/expenses/tempReceipt?group_id=${encodeURIComponent(groupId)}`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(tempReceiptPayload),
          },
        );
        if (!patchResponse.ok) {
          const body = await patchResponse.json();
          throw new Error(body.error || "Failed to save receipt row");
        }
      }
      setMessage("Saved successfully.");
      setSubmittedSuccessfully(true);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save data");
      setSubmitConfirmOpen(false);
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

  const confirmAndSubmit = async () => {
    const success = await saveData();
    if (!success) return;
    setSubmitConfirmOpen(false);
  };

  const selectedItemAssignments =
    userIndivSplits.find((entry) => entry.username === selectedUserStep2)
      ?.indivSplit ?? null;

  const missingStep1Fields: string[] = [];
  if (!expenseTitle.trim()) {
    missingStep1Fields.push("expense title");
  }
  if (!paidBy.trim() || !users.includes(paidBy)) {
    missingStep1Fields.push("paid by");
  }
  if (!receipt.currency.trim()) {
    missingStep1Fields.push("currency");
  }

  const isStep1Valid = missingStep1Fields.length === 0;

  const step1GuardErrorMessage = `Please fill in the following fields: ${missingStep1Fields.join(", ")}`;

  const goToStep = (nextStep: 1 | 2 | 3) => {
    if (nextStep > 1 && !isStep1Valid) {
      setStep1GuardError(step1GuardErrorMessage);
      setStep(1);
      return;
    }

    setStep1GuardError(null);
    setStep(nextStep);
  };

  useEffect(() => {
    if (isStep1Valid) {
      setStep1GuardError(null);
    }
  }, [isStep1Valid]);

  const stepLabels = [
    { step: 1, title: "Confirm" },
    { step: 2, title: "Individual" },
    { step: 3, title: "Shared" },
  ];

  const hasInitialTotalMismatch =
    initialFetchedTotal !== null &&
    Math.abs(initialFetchedTotal - receipt.total) > 0.009;

  const totalMismatchWarning = hasInitialTotalMismatch
    ? `Detected mismatch in parsed receipt total. Initial total was ${formatMoney(initialFetchedTotal ?? 0)} ${receipt.currency}, but computed total from items + charges is ${formatMoney(receipt.total)} ${receipt.currency}. Please review the item subtotals and charges before proceeding.`
    : null;

  return (
    <main className="min-h-screen bg-[#eceff3] px-3 py-5 text-slate-900 sm:px-5">
      <div className="mx-auto w-full max-w-2xl space-y-4">
        {!groupId ? (
          <LoadingSpinner />
        ) : loading ? (
          <Box
            sx={{
              minHeight: "calc(100vh - 56px)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              px: 1,
            }}
          >
            <LoadingSpinner />
          </Box>
        ) : submittedSuccessfully ? (
          <Box
            sx={{
              minHeight: "calc(100vh - 56px)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Card variant="outlined" sx={{ borderRadius: 3, width: "100%" }}>
              <CardContent sx={{ textAlign: "center", py: 4 }}>
                <Typography fontWeight={700} fontSize={20} color="success.main">
                  Expense submitted successfully to Splizy!
                </Typography>
                <Typography variant="body2" color="text.secondary" mt={1}>
                  You may close this miniapp browser and continue using Splizy
                  in the chat interface.
                </Typography>
              </CardContent>
            </Card>
          </Box>
        ) : (
          <>
            {error ? (
              <div className="rounded-3xl border-2 border-rose-300 bg-rose-50 p-4 text-rose-900">
                {error}
              </div>
            ) : null}
            <Card variant="outlined" sx={{ borderRadius: 3 }}>
              <CardContent sx={{ px: { xs: 1.5, sm: 3 }, py: 2 }}>
                <Stepper activeStep={step - 1} alternativeLabel>
                  {stepLabels.map((entry) => (
                    <Step key={entry.step} completed={step > entry.step}>
                      <StepLabel
                        onClick={() => goToStep(entry.step as 1 | 2 | 3)}
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
            {message ? (
              <div className="rounded-3xl border-2 border-emerald-300 bg-emerald-50 p-4 text-emerald-900">
                {message}
              </div>
            ) : null}
            {step === 1 ? (
              <ConfirmItems
                receipt={receipt}
                users={users}
                expenseTitle={expenseTitle}
                paidBy={paidBy}
                step1GuardError={step1GuardError}
                totalMismatchWarning={totalMismatchWarning}
                onUpdateExpenseTitle={setExpenseTitle}
                onUpdatePaidBy={setPaidBy}
                onUpdateItem={updateStep1Item}
                onUpdateMeta={updateStep1Meta}
                onAddItem={addStep1Item}
                onRemoveItems={removeStep1Items}
                onNext={() => goToStep(2)}
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
                onSave={() => setSubmitConfirmOpen(true)}
              />
            ) : null}
          </>
        )}
      </div>

      <Dialog
        open={submitConfirmOpen}
        onClose={() => setSubmitConfirmOpen(false)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>Confirm Final Details</DialogTitle>
        <DialogContent dividers sx={{ maxHeight: "70vh" }}>
          <Stack spacing={1.5}>
            <Typography>
              Please confirm the following details (inclusive of GST and service
              charges) before submission.
            </Typography>
            <Box
              sx={{
                backgroundColor: "#fff3e0",
                border: "1px solid #f0c48a",
                borderRadius: 2,
                px: 1.5,
                py: 1.25,
              }}
            >
              <Stack spacing={1.1}>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 1,
                    alignItems: "flex-start",
                  }}
                >
                  <Typography fontWeight={700} color="#ad5a00">
                    Total
                  </Typography>
                  <Typography color="#ad5a00" textAlign="right">
                    {normalizedReceiptForSubmit.currency}{" "}
                    {formatMoney(normalizedReceiptForSubmit.total)}
                  </Typography>
                </Box>

                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 1,
                    alignItems: "center",
                  }}
                >
                  <Typography fontWeight={700} color="#ad5a00">
                    Paid by
                  </Typography>
                  <Typography color="#ad5a00">{paidBy || "-"}</Typography>
                </Box>

                <Box
                  sx={{
                    borderTop: "1px solid #f0c48a",
                    mt: 0.5,
                    pt: 1,
                  }}
                >
                  <Typography fontWeight={700} color="#ad5a00" mb={0.5}>
                    User spendings
                  </Typography>
                  <Stack spacing={0.5}>
                    {payees.map((payee) => (
                      <Box
                        key={payee.user}
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          gap: 1,
                        }}
                      >
                        <Typography color="#ad5a00">{payee.user}</Typography>
                        <Typography color="#ad5a00">
                          {normalizedReceiptForSubmit.currency}{" "}
                          {formatMoney(payee.amount ?? 0)}
                        </Typography>
                      </Box>
                    ))}
                  </Stack>
                </Box>
              </Stack>
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSubmitConfirmOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={confirmAndSubmit}
            disabled={saving}
          >
            {saving ? "Submitting..." : "Submit"}
          </Button>
        </DialogActions>
      </Dialog>
    </main>
  );
}
