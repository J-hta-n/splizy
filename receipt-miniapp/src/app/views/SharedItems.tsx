import { ItemSummary } from "./types";
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
      <Stack spacing={2.5}>
        <Card sx={{ backgroundColor: "#e8f5e9" }}>
          <CardContent>
            <Typography fontWeight={700}>
              Step 3/3: Please assign shared items
            </Typography>
            <Typography variant="body2" mt={1}>
              Tap "Split among" for each item to choose users sharing it.
            </Typography>
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent>
            <Stack spacing={1.25}>
              {itemSummaries.map(({ item, key, leftover, index }) => {
                const selected = sharedSelections[key] ?? [];
                return (
                  <Box
                    key={key}
                    sx={{
                      display: "grid",
                      gridTemplateColumns: {
                        xs: "minmax(0, 1fr) 11rem",
                        sm: "minmax(0, 1fr) 14rem",
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
                        qty left: {leftover}, total {currency}{" "}
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
                      {selected.length > 0 ? (
                        <Box
                          sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}
                        >
                          {selected.map((user) => (
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
                          ))}
                        </Box>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          Select users
                        </Typography>
                      )}
                    </Box>
                  </Box>
                );
              })}
            </Stack>
          </CardContent>
        </Card>

        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={1.5}
          justifyContent="space-between"
        >
          <Button variant="outlined" onClick={onBack}>
            Back
          </Button>
          <Button
            variant="contained"
            onClick={onSave}
            disabled={saving || users.length === 0}
          >
            {saving ? "Saving..." : "Save step 3"}
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
            Leftover qty: {currentModalItem?.leftover ?? 0}
          </Typography>
          <Stack>
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
        </DialogContent>
        <DialogActions>
          <Button onClick={onCloseSplitModal}>Cancel</Button>
          <Button variant="contained" onClick={onConfirmSplitSelection}>
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
