"use client";

import dynamic from "next/dynamic";
import type { DistrictGlobeProps } from "@/components/dashboard/DistrictGlobe";

export const DistrictGlobeLazy = dynamic<DistrictGlobeProps>(
  () => import("@/components/dashboard/DistrictGlobe").then((m) => m.DistrictGlobe),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[520px] bg-surface-container-highest animate-pulse rounded-none" aria-hidden />
    ),
  }
);
