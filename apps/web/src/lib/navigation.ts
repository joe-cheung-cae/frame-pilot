import type { ComponentPropsWithoutRef, ReactNode } from "react";

export type LinkProps = Omit<ComponentPropsWithoutRef<"a">, "href"> & {
  href: string;
  prefetch?: boolean;
  children?: ReactNode;
};

export type Navigator = {
  push: (href: string) => void;
};

export { Link, useNavigator, usePathname, useQueryParams } from "./navigation.next";
