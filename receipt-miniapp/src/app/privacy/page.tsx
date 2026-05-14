import type { Metadata } from "next";
import {
  Avatar,
  Box,
  Card,
  CardContent,
  Divider,
  Link,
  Stack,
  Typography,
} from "@mui/material";

export const metadata: Metadata = {
  title: "Privacy Policy - Splizy",
  description: "Privacy policy for the Splizy Telegram bot and Mini App.",
};

export default function PrivacyPage() {
  return (
    <Box
      component="main"
      sx={{
        minHeight: "100vh",
        px: { xs: 2, sm: 3 },
        py: { xs: 3, sm: 5 },
        background:
          "linear-gradient(180deg, #eff6ff 0%, #f8fafc 46%, #eef2ff 100%)",
      }}
    >
      <Card
        variant="outlined"
        sx={{
          width: "100%",
          maxWidth: 860,
          mx: "auto",
          borderRadius: 3,
          borderColor: "rgba(15, 23, 42, 0.12)",
          backgroundColor: "rgba(255, 255, 255, 0.94)",
          backdropFilter: "blur(2px)",
        }}
      >
        <CardContent sx={{ p: { xs: 2.5, sm: 4 } }}>
          <Stack spacing={2.5}>
            <Stack spacing={0.75} alignItems="flex-start">
              <Stack direction="row" spacing={1.25} alignItems="center">
                <Avatar
                  src="/assets/splizy.png"
                  alt="Splizy"
                  sx={{ width: 50, height: 50 }}
                />
                <Box>
                  <Typography
                    variant="h5"
                    fontWeight={800}
                    letterSpacing={-0.4}
                  >
                    Privacy Policy
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Splizy Telegram bot and miniapp
                  </Typography>
                </Box>
              </Stack>
              <Typography variant="caption" color="text.secondary">
                Last updated: 14 May 2026
              </Typography>
            </Stack>

            <Divider />

            <Stack spacing={1}>
              <Typography variant="h6" fontWeight={700}>
                1. Overview
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                lineHeight={1.75}
              >
                This policy explains how Splizy, an open-source hobby project
                meant for casual use during group trips to split bills easily,
                protects the privacy and security of its users. Please contact
                us if you have any concerns or suggestions.
              </Typography>
            </Stack>

            <Stack spacing={1}>
              <Typography variant="h6" fontWeight={700}>
                2. Data Collected
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                lineHeight={1.75}
              >
                We only collect and store the following data required to operate
                core bill-splitting features:
              </Typography>
              <Box component="ul" sx={{ m: 0, pl: 2.75 }}>
                <Typography
                  component="li"
                  variant="body2"
                  color="text.secondary"
                  lineHeight={1.75}
                >
                  Telegram usernames
                </Typography>
                <Typography
                  component="li"
                  variant="body2"
                  color="text.secondary"
                  lineHeight={1.75}
                >
                  Telegram group IDs
                </Typography>
                <Typography
                  component="li"
                  variant="body2"
                  color="text.secondary"
                  lineHeight={1.75}
                >
                  Expense data submitted in the app, such as expense name,
                  currency, and amounts
                </Typography>
              </Box>
              <Typography
                variant="body2"
                color="text.secondary"
                lineHeight={1.75}
              >
                Splizy does not collect or store Telegram user IDs, Telegram
                group names, or receipt photos. It also does not access any
                group messages apart from user inputs to Splizy commands.
              </Typography>
            </Stack>

            <Stack spacing={1}>
              <Typography variant="h6" fontWeight={700}>
                3. Purpose of Processing
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                lineHeight={1.75}
              >
                We use this data solely to provide bill-splitting core
                functionalities, including managing expense records and
                calculating final transfers.
              </Typography>
            </Stack>

            <Stack spacing={1}>
              <Typography variant="h6" fontWeight={700}>
                4. Storage and Disclosure
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                lineHeight={1.75}
              >
                Data is stored securely by Supabase with RLS policies set.
                Deployment is handled by Vercel and Railway with secure HTTPS
                connections. Data is neither sold nor shared with third parties
                or affiliates, except where disclosure is required by law.
              </Typography>
            </Stack>

            <Stack spacing={1}>
              <Typography variant="h6" fontWeight={700}>
                5. Contact
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                lineHeight={1.75}
              >
                For privacy concerns, deletion requests, or general feedback and
                enquiry, please contact:
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                lineHeight={1.75}
              >
                - Email:{" "}
                <Link href="mailto:jh.tan.dev@gmail.com" underline="hover">
                  jh.tan.dev@gmail.com
                </Link>
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                lineHeight={1.75}
              >
                For feature requests or bug reports, please raise a ticket:
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                lineHeight={1.75}
              >
                - GitHub:{" "}
                <Link
                  href="https://github.com/J-hta-n/splizy/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                  underline="hover"
                >
                  github.com/J-hta-n/splizy/issues
                </Link>
              </Typography>
            </Stack>

            <Divider />

            <Stack spacing={0.5} sx={{ pt: 0.5 }}>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ lineHeight: 1.4 }}
              >
                Splizy Icon Attribution:
              </Typography>
              <Typography
                variant="caption"
                color="text.secondary"
                lineHeight={1.2}
              >
                <Link
                  href="https://www.flaticon.com/free-icons/accounting"
                  title="accounting icons"
                  target="_blank"
                  rel="noopener noreferrer"
                  underline="hover"
                >
                  Accounting icons created by zero_wing - Flaticon
                </Link>
              </Typography>
            </Stack>

            <Typography
              variant="caption"
              color="text.disabled"
              textAlign="center"
            >
              Thanks for checking Splizy out, hope you found this app useful! :)
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}
