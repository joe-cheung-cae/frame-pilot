import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

const desktopRoot = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(desktopRoot, "../web");
const webSrc = path.resolve(webRoot, "src");
const navigationNext = path.resolve(webSrc, "lib/navigation.next.tsx");
const navigationNextBare = navigationNext.replace(/\.tsx$/, "");
const navigationRouter = path.resolve(desktopRoot, "src/navigation.router.tsx");
const webNativeFs = path.resolve(webSrc, "lib/nativeFs.ts");
const webNativeFsBare = webNativeFs.replace(/\.ts$/, "");
const desktopNativeFs = path.resolve(desktopRoot, "src/lib/nativeFs.ts");
const webDetachedPreview = path.resolve(webSrc, "lib/detachedPreview.ts");
const webDetachedPreviewBare = webDetachedPreview.replace(/\.ts$/, "");
const desktopDetachedPreview = path.resolve(desktopRoot, "src/lib/detachedPreview.ts");
const reactPkg = path.resolve(desktopRoot, "node_modules/react");
const reactDomPkg = path.resolve(desktopRoot, "node_modules/react-dom");

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function isNavigationNext(id: string): boolean {
  const normalized = id.replace(/\\/g, "/");
  const nextPath = navigationNext.replace(/\\/g, "/");
  const nextBare = navigationNextBare.replace(/\\/g, "/");
  return (
    normalized === nextPath ||
    normalized === nextBare ||
    normalized.endsWith("/lib/navigation.next") ||
    normalized.endsWith("/lib/navigation.next.tsx")
  );
}

function aliasNavigationNext(): Plugin {
  return {
    name: "alias-navigation-next",
    enforce: "pre",
    resolveId(source, importer) {
      if (isNavigationNext(source)) {
        return navigationRouter;
      }
      if (!importer) {
        return null;
      }
      if (source === "./navigation.next" || source === "./navigation.next.tsx") {
        const resolved = path.resolve(path.dirname(importer), source);
        if (isNavigationNext(resolved)) {
          return navigationRouter;
        }
      }
      return null;
    },
  };
}

function isWebNativeFs(id: string): boolean {
  const normalized = id.replace(/\\/g, "/");
  const nativePath = webNativeFs.replace(/\\/g, "/");
  const nativeBare = webNativeFsBare.replace(/\\/g, "/");
  return (
    normalized === nativePath ||
    normalized === nativeBare ||
    normalized.endsWith("/web/src/lib/nativeFs") ||
    normalized.endsWith("/web/src/lib/nativeFs.ts")
  );
}

function aliasNativeFs(): Plugin {
  return {
    name: "alias-native-fs",
    enforce: "pre",
    resolveId(source, importer) {
      if (isWebNativeFs(source)) {
        return desktopNativeFs;
      }
      if (!importer) {
        return null;
      }
      if (source === "./nativeFs" || source === "./nativeFs.ts") {
        const resolved = path.resolve(path.dirname(importer), source);
        if (isWebNativeFs(resolved)) {
          return desktopNativeFs;
        }
      }
      return null;
    },
  };
}

function isWebDetachedPreview(id: string): boolean {
  const normalized = id.replace(/\\/g, "/");
  const previewPath = webDetachedPreview.replace(/\\/g, "/");
  const previewBare = webDetachedPreviewBare.replace(/\\/g, "/");
  return (
    normalized === previewPath ||
    normalized === previewBare ||
    normalized.endsWith("/web/src/lib/detachedPreview") ||
    normalized.endsWith("/web/src/lib/detachedPreview.ts")
  );
}

function aliasDetachedPreview(): Plugin {
  return {
    name: "alias-detached-preview",
    enforce: "pre",
    resolveId(source, importer) {
      if (isWebDetachedPreview(source)) {
        return desktopDetachedPreview;
      }
      if (!importer) {
        return null;
      }
      if (source === "./detachedPreview" || source === "./detachedPreview.ts") {
        const resolved = path.resolve(path.dirname(importer), source);
        if (isWebDetachedPreview(resolved)) {
          return desktopDetachedPreview;
        }
      }
      return null;
    },
  };
}

export default defineConfig({
  plugins: [react(), aliasNavigationNext(), aliasNativeFs(), aliasDetachedPreview()],
  clearScreen: false,
  resolve: {
    alias: [
      {
        find: new RegExp(`^${escapeRegExp(navigationNextBare)}(?:\\.tsx)?$`),
        replacement: navigationRouter,
      },
      { find: navigationNext, replacement: navigationRouter },
      {
        find: new RegExp(`^${escapeRegExp(webNativeFsBare)}(?:\\.ts)?$`),
        replacement: desktopNativeFs,
      },
      { find: webNativeFs, replacement: desktopNativeFs },
      {
        find: new RegExp(`^${escapeRegExp(webDetachedPreviewBare)}(?:\\.ts)?$`),
        replacement: desktopDetachedPreview,
      },
      { find: webDetachedPreview, replacement: desktopDetachedPreview },
      { find: "@", replacement: webSrc },
      { find: /^react$/, replacement: reactPkg },
      { find: /^react-dom$/, replacement: reactDomPkg },
    ],
    dedupe: ["react", "react-dom"],
  },
  define: {
    "process.env.NEXT_PUBLIC_API_BASE_URL": JSON.stringify(process.env.NEXT_PUBLIC_API_BASE_URL ?? ""),
  },
  server: {
    port: 1420,
    strictPort: true,
    fs: {
      allow: [desktopRoot, webRoot],
    },
    watch: {
      ignored: ["**/src-tauri/**"],
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
