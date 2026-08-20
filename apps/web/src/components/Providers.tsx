"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { applyShellDataset } from "@/lib/shell";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  applyShellDataset();
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
