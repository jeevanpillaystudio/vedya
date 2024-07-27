"use client";

import { cn } from "@/lib/utils";
import BinaryLoading from "./binary-loading";
import Animation from "@/components/animation";

export default function Index() {
  return (
    <main className={cn("relative h-screen w-screen")}>
      <BinaryLoading />
      <Animation />
    </main>
  );
}
