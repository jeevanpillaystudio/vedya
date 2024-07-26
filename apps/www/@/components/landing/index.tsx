"use client";

import { cn } from "@/lib/utils";
import BinaryLoading from "./binary-loading";
import DebugAnimationControl from "../debug/debug-animation-control";

export default function Index() {
  return (
    <main className={cn("relative h-screen w-screen")}>
      <BinaryLoading />
      <DebugAnimationControl />
    </main>
  );
}
