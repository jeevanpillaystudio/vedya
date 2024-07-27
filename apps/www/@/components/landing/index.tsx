"use client";

import { cn } from "@/lib/utils";
import BinaryLoading from "./binary-loading";
import AnimationControlPanel from "../animation/animation-control-panel";

export default function Index() {
  return (
    <main className={cn("relative h-screen w-screen")}>
      <BinaryLoading />
      <AnimationControlPanel />
    </main>
  );
}
