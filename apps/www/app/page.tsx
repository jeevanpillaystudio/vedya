import BinaryLoading from "@/components/landing/binary-loading";
import Animation from "@/components/animation";
import { cn } from "@/lib/utils";

export default function Home() {
  return (
    <main className={cn("relative h-screen w-screen")}>
      <BinaryLoading />
      <Animation />
    </main>
  );
}
