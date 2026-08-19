import type { ComponentPropsWithoutRef, ReactNode } from "react";

type LinkProps = Omit<ComponentPropsWithoutRef<"a">, "href"> & {
  href: string;
  prefetch?: boolean;
  children?: ReactNode;
};

type Navigator = {
  push: (href: string) => void;
};

export function Link({ href, prefetch: _prefetch, children, ...rest }: LinkProps) {
  return (
    <a href={href} {...rest}>
      {children}
    </a>
  );
}

export function useNavigator(): Navigator {
  return {
    push(href: string) {
      window.location.assign(href);
    },
  };
}

export function useQueryParams(): URLSearchParams {
  if (typeof window === "undefined") {
    return new URLSearchParams();
  }
  return new URLSearchParams(window.location.search);
}
