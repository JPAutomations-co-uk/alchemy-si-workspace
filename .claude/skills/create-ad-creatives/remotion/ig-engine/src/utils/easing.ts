import { Easing } from "remotion";

/** Magnetic snap: fast start, graceful settle, no overshoot */
export const magneticSnap = Easing.bezier(0.2, 0, 0, 1.0);

/** Hero reveal: smooth luxury entrance (from JP Automations site) */
export const heroReveal = Easing.bezier(0.16, 1, 0.3, 1);

/** Luxury ease: refined general-purpose curve */
export const luxEase = Easing.bezier(0.22, 0.61, 0.36, 1);

/** Back out with slight overshoot (for card scale-in pop) */
export const backOut = Easing.bezier(0.34, 1.56, 0.64, 1);

/** Sharp out for scatter/explosion */
export const sharpOut = Easing.bezier(0.33, 1, 0.68, 1);
