import { Card, CardContent, CircularProgress, Typography } from "@mui/material";

export function LoadingSpinner() {
  return (
    <Card
      variant="outlined"
      sx={{
        borderRadius: 3,
        width: "100%",
        maxWidth: 320,
      }}
    >
      <CardContent
        sx={{
          py: 4,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 1.5,
          textAlign: "center",
        }}
      >
        <CircularProgress size={36} thickness={4.5} />
        <Typography fontWeight={700}>Loading receipt...</Typography>
        <Typography variant="body2" color="text.secondary">
          Preparing the receipt review for this group.
        </Typography>
      </CardContent>
    </Card>
  );
}
