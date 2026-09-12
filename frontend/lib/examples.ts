/**
 * Hand-verified buggy examples.
 *
 * Every `actualOutput` below was produced by running the snippet through a real
 * CPython 3 interpreter, not guessed. They are baked in so the Run button is
 * instant and needs no network: the live demo can never be broken by the code
 * execution service rate-limiting us. Piston is only used for code the student
 * has actually edited or pasted.
 *
 * No input() anywhere on purpose -- it would mean wiring stdin for nothing.
 */

export interface Example {
  id: string;
  label: string;
  /** For our reference. Never shown to the student before the naming rung. */
  concept: string;
  code: string;
  /** What the student meant to get. */
  expectedOutput: string;
  /** What it actually prints. Verified. */
  actualOutput: string;
  /** Seeds the "what's wrong?" field so the diagnosis pass has context. */
  studentQuestion: string;
}

export const EXAMPLES: Example[] = [
  {
    id: "type-coercion",
    label: "The price is wrong",
    concept: "sequence multiplication / str is not int",
    code: `def total_price(quantity, price):
    return quantity * price

quantity = "3"          # came straight from a form field
print(total_price(quantity, 5))
`,
    expectedOutput: "15",
    actualOutput: "33333",
    studentQuestion:
      "Three items at 5 each should be 15, but I get 33333 and there is no error.",
  },
  {
    id: "off-by-one",
    label: "The sum is short",
    concept: "off-by-one / exclusive upper bound",
    code: `def sum_up_to(n):
    """Sum of 1 to n, inclusive."""
    total = 0
    for i in range(n):
        total += i
    return total

print(sum_up_to(5))
`,
    expectedOutput: "15",
    actualOutput: "10",
    studentQuestion: "1+2+3+4+5 is 15, so why does this print 10?",
  },
  {
    id: "mutable-default",
    label: "The cart remembers",
    concept: "mutable default argument",
    code: `def add_to_cart(item, cart=[]):
    cart.append(item)
    return cart

print(add_to_cart("apple"))
print(add_to_cart("bread"))
`,
    expectedOutput: "['apple']\n['bread']",
    actualOutput: "['apple']\n['apple', 'bread']",
    studentQuestion:
      "These are two separate calls, so why does the second one still contain the apple?",
  },
];

export function findExample(code: string): Example | undefined {
  return EXAMPLES.find((e) => e.code.trim() === code.trim());
}
