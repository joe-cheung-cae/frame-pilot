"use client";

import NextLink from "next/link";
import { usePathname as useNextPathname, useRouter, useSearchParams } from "next/navigation";
import type { LinkProps, Navigator } from "./navigation";

export function Link({ href, prefetch, children, ...rest }: LinkProps) {
  return (
    <NextLink href={href} prefetch={prefetch} {...rest}>
      {children}
    </NextLink>
  );
}

export function useNavigator(): Navigator {
  const router = useRouter();
  return {
    push(href: string) {
      void router.push(href);
    },
  };
}

export function useQueryParams(): URLSearchParams {
  const searchParams = useSearchParams();
  return new URLSearchParams(searchParams.toString());
}

export function usePathname(): string {
  return useNextPathname();
}
