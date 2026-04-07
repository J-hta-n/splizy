import { ItemSummary } from "@src/lib/types";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Stack,
  Typography,
} from "@mui/material";
import { formatMoney } from "@/lib/utils";

type SharedItemsProps = {
  users: string[];
  itemSummaries: ItemSummary[];
  currency: string;
  saving: boolean;
  splitModalItemIndex: number | null;
  modalSelection: string[];
  modalValidationError: string | null;
  areAllUsersSelected: boolean;
  onOpenSplitModal: (itemIndex: number) => void;
  onCloseSplitModal: () => void;
  onToggleModalUser: (user: string) => void;
  onToggleAllModalUsers: () => void;
  onConfirmSplitSelection: () => void;
  isConfirmDisabled: boolean;
  onBack: () => void;
  onSave: () => void;
};

export function SharedItems({
  users,
  itemSummaries,
  currency,
  saving,
  splitModalItemIndex,
  modalSelection,
  modalValidationError,
  areAllUsersSelected,
  onOpenSplitModal,
  onCloseSplitModal,
  onToggleModalUser,
  onToggleAllModalUsers,
  onConfirmSplitSelection,
  isConfirmDisabled,
  onBack,
  onSave,
}: SharedItemsProps) {
  const shareableItems = itemSummaries.filter((entry) => entry.sharedQty > 0);

  const currentModalItem =
    splitModalItemIndex === null
      ? null
      : shareableItems.find((entry) => entry.index === splitModalItemIndex);

  return (
    <>
      <Stack spacing={2.5}>
        <Card sx={{ backgroundColor: "#e8f5e9" }}>
          <CardContent>
            <Typography fontWeight={700}>
              Step 3/3: Please assign shared items
            </Typography>
            <Typography variant="body2" mt={1}>
              For all remaining shared items, tap &quot;Split among&quot; to
              choose the users involved.
            </Typography>
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent>
            <Stack spacing={1.25}>
              {shareableItems.length === 0 ? (
                <Card variant="outlined" sx={{ borderStyle: "dashed" }}>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">
                      No shared items left. Everything has already been assigned
                      in Step 2.
                    </Typography>
                  </CardContent>
                </Card>
              ) : (
                shareableItems.map(({ item, sharedQty, index }) => {
                  const selected = item.shared;
                  const displaySelected =
                    sharedQty > 0 && selected.length === 0 ? users : selected;
                  const isAllUsersDefault =
                    users.length > 0 && displaySelected.length === users.length;
                  return (
                    <Box
                      key={index}
                      sx={{
                        display: "grid",
                        gridTemplateColumns: {
                          xs: "58% 42%",
                          sm: "60% 40%",
                        },
                        alignItems: "stretch",
                        gap: 1.25,
                      }}
                    >
                      <Box
                        sx={{
                          border: "1px solid #f0c48a",
                          backgroundColor: "#fff3e0",
                          borderRadius: 2,
                          px: 1.5,
                          py: 1.25,
                        }}
                      >
                        <Typography fontWeight={700}>
                          {item.name || "Unnamed item"}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          qty left: {sharedQty}, total {currency}{" "}
                          {formatMoney(item.subtotal ?? 0)}
                        </Typography>
                      </Box>
                      <Box
                        component="button"
                        type="button"
                        onClick={() => onOpenSplitModal(index)}
                        sx={{
                          width: "100%",
                          minHeight: 88,
                          textAlign: "left",
                          borderRadius: 2,
                          border: "1px solid",
                          borderColor: "divider",
                          backgroundColor: "#fff",
                          px: 1,
                          py: 0.75,
                          cursor: "pointer",
                          display: "flex",
                          flexDirection: "column",
                          gap: 0.75,
                          "&:hover": {
                            borderColor: "primary.main",
                            backgroundColor: "#f8fbff",
                          },
                        }}
                      >
                        <Typography variant="caption" color="text.secondary">
                          Split among
                        </Typography>
                        {displaySelected.length > 0 ? (
                          <Box
                            sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}
                          >
                            {isAllUsersDefault ? (
                              <Chip
                                label="All users"
                                size="small"
                                color="info"
                                variant="filled"
                              />
                            ) : (
                              displaySelected.map((user) => (
                                <Chip
                                  key={user}
                                  label={user}
                                  size="small"
                                  sx={{
                                    maxWidth: "100%",
                                    "& .MuiChip-label": {
                                      overflow: "hidden",
                                      textOverflow: "ellipsis",
                                    },
                                  }}
                                />
                              ))
                            )}
                          </Box>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            Select users
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  );
                })
              )}
            </Stack>
          </CardContent>
        </Card>

        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={1.5}
          pb={5}
          justifyContent="space-between"
        >
          <Button
            variant="contained"
            onClick={onSave}
            disabled={saving || users.length === 0}
          >
            Submit expense
          </Button>
          <Button variant="outlined" onClick={onBack}>
            Back
          </Button>
        </Stack>
      </Stack>

      <Dialog
        open={Boolean(currentModalItem)}
        onClose={onCloseSplitModal}
        fullWidth
        maxWidth="xs"
      >
        <DialogTitle>
          Select users for {currentModalItem?.item.name || "item"}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" mb={1}>
            Leftover qty: {currentModalItem?.sharedQty ?? 0}
          </Typography>
          <Stack>
            <FormControlLabel
              control={
                <Checkbox
                  checked={areAllUsersSelected}
                  onChange={onToggleAllModalUsers}
                />
              }
              label={areAllUsersSelected ? "Deselect all" : "Select all"}
            />
            {users.map((user) => {
              const checked = modalSelection.includes(user);
              return (
                <FormControlLabel
                  key={user}
                  control={
                    <Checkbox
                      checked={checked}
                      onChange={() => onToggleModalUser(user)}
                    />
                  }
                  label={user}
                />
              );
            })}
          </Stack>
          {isConfirmDisabled || modalValidationError ? (
            <Typography color="error.main" variant="body2" mt={1}>
              {modalValidationError ||
                "Please select at least 2 users to share this item."}
            </Typography>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={onCloseSplitModal}>Cancel</Button>
          <Button
            variant="contained"
            onClick={onConfirmSplitSelection}
            disabled={isConfirmDisabled}
          >
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
