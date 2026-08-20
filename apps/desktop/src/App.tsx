import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { BrowserRouter } from "react-router-dom";
import { applyShellDataset } from "@/lib/shell";
import { AppRoutes } from "./router";

export function App() {
  const [queryClient] = useState(() => new QueryClient());
  applyShellDataset();
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
