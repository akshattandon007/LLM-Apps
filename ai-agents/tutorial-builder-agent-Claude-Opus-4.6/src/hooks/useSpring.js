import { useState, useEffect, useRef } from 'react';

/**
 * Custom hook that animates a value using spring physics.
 * Creates the bouncy, organic feel inspired by Duolingo characters.
 *
 * @param {number} target    - The target value to animate towards
 * @param {number} stiffness - Spring stiffness (0-1). Higher = snappier
 * @param {number} damping   - Spring damping (0-1). Higher = less bounce
 * @returns {number} The current animated value
 *
 * @example
 * const scale = useSpring(isExcited ? 1.3 : 1.0, 0.12, 0.65);
 * // scale will bounce towards 1.3 when isExcited is true
 */
export function useSpring(target, stiffness = 0.15, damping = 0.7) {
  const ref = useRef({ value: target, velocity: 0 });
  const [value, setValue] = useState(target);

  useEffect(() => {
    let raf;
    const step = () => {
      const s = ref.current;
      const force = (target - s.value) * stiffness;
      s.velocity = (s.velocity + force) * damping;
      s.value += s.velocity;

      if (Math.abs(s.velocity) < 0.001 && Math.abs(target - s.value) < 0.001) {
        s.value = target;
        s.velocity = 0;
        setValue(target);
        return; // stop animating once settled
      }

      setValue(s.value);
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, stiffness, damping]);

  return value;
}
