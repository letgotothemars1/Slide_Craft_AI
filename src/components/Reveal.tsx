import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

interface Props {
  children: React.ReactNode;
  /** Milliseconds to hold before revealing — used to stagger a row of cards. */
  delay?: number;
  className?: string;
  as?: "div" | "section" | "article" | "li";
}

/**
 * Fades its children up when they scroll into view.
 *
 * Uses IntersectionObserver rather than a scroll listener: the browser does the
 * work off the main thread, and there is nothing to throttle. Reveals once and
 * then disconnects — re-animating on every scroll direction change is the
 * fastest way to make a page feel restless.
 *
 * Motion itself lives in CSS (`.reveal` / `.is-revealed` in index.css), which is
 * also where `prefers-reduced-motion` is honoured.
 */
export default function Reveal({ children, delay = 0, className, as = "div" }: Props) {
  const ref = useRef<HTMLElement | null>(null);
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    // Without IntersectionObserver the content must still be visible.
    if (typeof IntersectionObserver === "undefined") {
      setRevealed(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        observer.disconnect();
        if (delay) {
          window.setTimeout(() => setRevealed(true), delay);
        } else {
          setRevealed(true);
        }
      },
      // Fire slightly before the element is fully in view, so the motion has
      // finished by the time the reader's eye arrives.
      { threshold: 0.1, rootMargin: "0px 0px -8% 0px" },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [delay]);

  const Tag = as as React.ElementType;

  return (
    <Tag ref={ref} className={cn("reveal", revealed && "is-revealed", className)}>
      {children}
    </Tag>
  );
}
