import { useEffect, useRef, useState } from "react";

interface Options {
  /** Milliseconds per character while typing. */
  speed?: number;
  /** Milliseconds per character while erasing — deliberately faster. */
  deleteSpeed?: number;
  /** Total time one phrase owns the line, typing and erasing included. */
  cycleMs?: number;
  /** Delay before the first character appears. */
  startDelay?: number;
  /** Shortest pause on a finished phrase, if the cycle budget runs out. */
  minHoldMs?: number;
}

/**
 * Types each phrase out, holds it, erases it, then moves to the next — looping.
 *
 * Every phrase occupies the same `cycleMs` regardless of length: the hold is
 * whatever is left after typing and erasing. A fixed hold instead would make
 * short phrases fly past and long ones linger.
 *
 * With reduced motion requested, the first phrase is shown in full and nothing
 * moves — the effect is decoration, and decoration is never worth withholding
 * content or spinning timers for.
 */
export function useTypewriter(phrases: string[], options: Options = {}) {
  const { speed = 45, deleteSpeed = 22, cycleMs = 7000, startDelay = 400, minHoldMs = 900 } = options;

  const prefersReduced =
    typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

  const [text, setText] = useState(prefersReduced ? (phrases[0] ?? "") : "");
  const [typing, setTyping] = useState(false);

  // Timers are collected so a language switch or unmount cancels all of them.
  const timers = useRef<number[]>([]);

  useEffect(() => {
    const clearAll = () => {
      timers.current.forEach(window.clearTimeout);
      timers.current = [];
    };

    if (prefersReduced || phrases.length === 0) {
      setText(phrases[0] ?? "");
      setTyping(false);
      return clearAll;
    }

    let phraseIndex = 0;
    let cancelled = false;

    const schedule = (fn: () => void, ms: number) => {
      const id = window.setTimeout(() => {
        if (!cancelled) fn();
      }, ms);
      timers.current.push(id);
    };

    const runPhrase = () => {
      // Every timer from the previous phrase has fired by now; drop the ids so
      // the array does not grow for as long as the loop runs.
      timers.current = [];

      const phrase = phrases[phraseIndex];
      const typeMs = phrase.length * speed;
      const deleteMs = phrase.length * deleteSpeed;
      const hold = Math.max(minHoldMs, cycleMs - typeMs - deleteMs);

      setTyping(true);

      for (let i = 1; i <= phrase.length; i += 1) {
        schedule(() => setText(phrase.slice(0, i)), i * speed);
      }

      schedule(() => setTyping(false), typeMs);

      for (let i = phrase.length - 1; i >= 0; i -= 1) {
        const step = phrase.length - i;
        schedule(() => {
          if (step === 1) setTyping(true);
          setText(phrase.slice(0, i));
        }, typeMs + hold + step * deleteSpeed);
      }

      schedule(() => {
        phraseIndex = (phraseIndex + 1) % phrases.length;
        runPhrase();
      }, typeMs + hold + deleteMs + 120);
    };

    schedule(runPhrase, startDelay);

    return () => {
      cancelled = true;
      clearAll();
    };
    // `phrases` is rebuilt when the language changes, which restarts the loop.
  }, [phrases, speed, deleteSpeed, cycleMs, startDelay, minHoldMs, prefersReduced]);

  return { text, typing, animated: !prefersReduced };
}
