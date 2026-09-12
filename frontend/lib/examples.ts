/** Pre-loaded buggy snippet per language — same algorithm, different bug, so the demo flows quickly. */
export const STARTERS: Record<string, string> = {
  python: `def average(scores):
    total = 0
    for s in scores:
        total += s
    return total / len(score)   # bug is here

print(average([85, 92, 78, 90, 88]))
`,

  javascript: `function average(scores) {
  let total = 0;
  for (let i = 0; i <= scores.length; i++) {   // bug is here
    total += scores[i];
  }
  return total / scores.length;
}

console.log(average([85, 92, 78, 90, 88]));
`,

  java: `public class Main {
    static double average(int[] scores) {
        int total = 0;
        for (int s : scores) {
            total += s;
        }
        return total / scores.length;   // bug is here
    }

    public static void main(String[] args) {
        int[] scores = {85, 92, 78, 90, 88};
        System.out.println(average(scores));
    }
}
`,

  cpp: `#include <iostream>
#include <vector>
using namespace std;

double average(vector<int> scores) {
    int total = 0;
    for (int s : scores) {
        total += s;
    }
    return total / scores.size();   // bug is here
}

int main() {
    vector<int> scores = {85, 92, 78, 90, 88};
    cout << average(scores) << endl;
    return 0;
}
`,
};

/** Fallback for unknown languages */
export const STARTER = STARTERS["python"];
