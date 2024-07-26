/**
 * A utility function to build type-safe UI components; taking away all the worries of class names and StyleSheet composition.
 */
import type { VariantProps } from "class-variance-authority";
import { cva } from "class-variance-authority";
import type { ClassValue } from "clsx";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * A utility function to merge class names and tailwind classes. We use tailwind-merge to merge
 * tailwind classes WITHOUT style conflicts
 *
 * @param inputs The class names to merge
 * @returns The merged class names
 */
const cn = (...inputs: ClassValue[]): string => {
  return twMerge(clsx(inputs));
};

export { cn, cva };
export type { ClassValue, VariantProps };