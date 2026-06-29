// All money is kobo (integers). 100 kobo = ₦1. Floating point never touches money.

export function naira(kobo: number): string {
  const sign = kobo < 0 ? "-" : "";
  const whole = Math.abs(kobo) / 100;
  return `${sign}₦${whole.toLocaleString("en-NG", {
    minimumFractionDigits: whole % 1 === 0 ? 0 : 2,
    maximumFractionDigits: 2,
  })}`;
}

export function nairaCompact(kobo: number): string {
  return `₦${(kobo / 100).toLocaleString("en-NG")}`;
}

/**
 * Proration, exactly as the PRD specifies — all integer kobo arithmetic.
 * credit = old/days_in_period * days_remaining
 * charge = new/days_in_period * days_remaining
 * net    = charge - credit
 */
export function prorate(
  oldAmount: number,
  newAmount: number,
  daysInPeriod: number,
  daysRemaining: number,
): { credit: number; charge: number; net: number } {
  const credit = Math.round((oldAmount / daysInPeriod) * daysRemaining);
  const charge = Math.round((newAmount / daysInPeriod) * daysRemaining);
  return { credit, charge, net: charge - credit };
}
