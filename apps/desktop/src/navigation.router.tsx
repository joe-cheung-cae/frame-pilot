import type { ComponentPropsWithoutRef, ReactNode } from "react";
import { Link as RouterLink, useLocation, useNavigate, useSearchParams } from "react-router-dom";

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
    <RouterLink to={href} {...rest}>
      {children}
    </RouterLink>
  );
}

export function useNavigator(): Navigator {
  const navigate = useNavigate();
  return {
    push(href: string) {
      navigate(href);
    },
  };
}

export function useQueryParams(): URLSearchParams {
  const [searchParams] = useSearchParams();
  return new URLSearchParams(searchParams.toString());
}

export function usePathname(): string {
  return useLocation().pathname;
}
