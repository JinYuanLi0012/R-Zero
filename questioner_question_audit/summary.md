# Questioner Generated Questions Audit

These are the filtered question sets uploaded by the solver training runs. Round 1 means `questioner_v1 -> solver_v1`; round 2 means `questioner_v2 -> solver_v2`. Scores are Solver majority-answer agreement rates; lower/mid values are harder or less stable for the Solver.

## round1_questioner_v1_for_solver_v1

- Source dataset: `jinyuan222/qwen3_4b_fullrun_authorsettings_solver_v1`
- Count: 1816
- Score: min 0.333, median 0.500, mean 0.521, max 0.778
- Problem length: median 219 chars, mean 241.5 chars
- Heuristic topic counts:
  - geometry: 701
  - number_theory: 638
  - algebra: 222
  - combinatorics: 115
  - other: 108
  - logic_puzzle: 22
  - sequence: 10
- Score value counts:
  - 0.333: 461
  - 0.375: 63
  - 0.4: 1
  - 0.429: 10
  - 0.444: 340
  - 0.5: 58
  - 0.556: 284
  - 0.571: 5
  - 0.625: 31
  - 0.667: 295
  - 0.714: 4
  - 0.75: 26
  - 0.778: 238

### First 10 Examples

- `0000` score=0.667, geometry, ans=`5`: A right triangle has a hypotenuse of length 10 and one of its acute angles is twice the size of the other. What is the length of the shorter leg of the triangle?
- `0001` score=0.333, number_theory, ans=`1`: In a small village, there are 20 houses, each with a unique number from 1 to 20. One day, the village decides to paint each house a color based on the sum of its house number's digits. If the sum is even, the house is painted blue; if odd, it's painted red. A...
- `0002` score=0.556, geometry, ans=`96 - 25\pi`: A circle with radius 5 cm is inscribed in a right-angled triangle with legs of lengths 12 cm and 16 cm. What is the area of the region inside the triangle but outside the circle? Express your answer in terms of \(\pi\).
- `0003` score=0.556, number_theory, ans=`3`: Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) is divisible by the polynomial \( Q(x) = x^2 - x + 1 \).
- `0004` score=0.667, number_theory, ans=`1`: ** What is the smallest positive integer \( n \) such that \( 2^n + 3^n \) is divisible by 5?
- `0005` score=0.333, combinatorics, ans=`7560`: How many distinct arrangements of the letters in the word "MATHEMATICS" are there such that all vowels (A, E, A, I) appear consecutively and the two 'M's are not next to each other?
- `0006` score=0.778, number_theory, ans=`1525`: Let \( f \) be a function defined on the set of integers such that \( f(1) = 1 \) and for all integers \( n \geq 1 \), \[ f(n+1) = 2f(n) + n. \] Find the value of \( f(10) \).
- `0007` score=0.667, number_theory, ans=`16`: Let \( S \) be the set of all positive integers \( n \) such that \( n \) can be expressed as the sum of two distinct positive integers, each of which is a product of two distinct primes. For example, \( 10 = 2 \times 3 + 1 \times 5 \). Find the smallest elem...
- `0008` score=0.333, number_theory, ans=`13`: Given the sequence \( a_1, a_2, a_3, \ldots \) defined by \( a_1 = 1 \) and \( a_{n+1} = a_n + \frac{1}{a_n} \) for \( n \geq 1 \), find the smallest integer \( k \) such that \( a_k > 5 \).
- `0009` score=0.333, geometry, ans=`\frac{1}{3}`: In the complex plane, consider the points $A$, $B$, and $C$ representing the complex numbers $1+2i$, $-1+i$, and $2+3i$ respectively. Let $O$ be the origin. A complex number $z$ is chosen at random such that $|z| = 1$. Find the probability that the angle betw...

## round2_questioner_v2_for_solver_v2

- Source dataset: `jinyuan222/qwen3_4b_fullrun_authorsettings_solver_v2`
- Count: 2039
- Score: min 0.333, median 0.444, mean 0.518, max 0.778
- Problem length: median 246 chars, mean 263.9 chars
- Heuristic topic counts:
  - number_theory: 1051
  - geometry: 644
  - algebra: 197
  - other: 67
  - combinatorics: 66
  - logic_puzzle: 8
  - sequence: 4
  - calculus: 2
- Score value counts:
  - 0.333: 524
  - 0.375: 9
  - 0.429: 1
  - 0.444: 498
  - 0.5: 9
  - 0.556: 395
  - 0.625: 3
  - 0.667: 329
  - 0.75: 5
  - 0.778: 266

### First 10 Examples

- `0000` score=0.333, number_theory, ans=`15`: Find the smallest positive integer \( n \) such that the number of ordered triples \((a, b, c)\) where \(a, b,\) and \(c\) are integers satisfying \(1 \leq a, b, c \leq n\) and \(a + b + c\) is a multiple of 3 is exactly 1000.
- `0001` score=0.444, number_theory, ans=`2`: Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) has a root modulo any prime \( p \).
- `0002` score=0.444, geometry, ans=`0`: Find all positive integers \( n \) such that \( n^2 + 3n + 2 \) is a perfect square.
- `0003` score=0.333, number_theory, ans=`675`: Find the smallest positive integer \( n \) such that there exist positive integers \( a_1, a_2, \ldots, a_n \) satisfying the following conditions: 1. \( a_1 + a_2 + \cdots + a_n = 2023 \), 2. Each \( a_i \) is divisible by \( 3 \) but not by \( 9 \), 3. For ...
- `0004` score=0.333, geometry, ans=`20`: In the complex plane, the vertices of a regular icosagon (20-sided polygon) are located at the 20th roots of unity. Let \( P \) be a point inside the icosagon such that the sum of the distances from \( P \) to each vertex is minimized. Determine the coordinat...
- `0005` score=0.778, geometry, ans=`2\sqrt{2} r^2`: Consider a regular octagon $ABCDEFGH$ inscribed in a circle of radius $r$. Let $P$ be a point inside the octagon such that $PA = PB = PC = PD = PE = PF = PG = PH$. Determine the area of the octagon as a function of $r$ and $P$’s coordinates. Specifically, if ...
- `0006` score=0.556, geometry, ans=`1000000`: In the complex plane, let $P$ be a point with coordinates $(a, b)$, where $a$ and $b$ are positive integers. Define a sequence of complex numbers $\{z_n\}_{n \geq 0}$ as follows: - $z_0 = P$. - For each $n \geq 1$, $z_n$ is the midpoint of the line segment jo...
- `0007` score=0.444, number_theory, ans=`29`: In the complex plane, let \( z_1 \) and \( z_2 \) be the roots of the polynomial \( x^2 - 2x + 13 \). Define a sequence \( \{a_n\} \) such that \( a_1 = 2 \), \( a_2 = 3 \), and for \( n \geq 3 \), \( a_n \) is the smallest positive integer such that \( a_n \...
- `0008` score=0.444, number_theory, ans=`3`: Find all positive integers \( n \) such that \( n^2 + n + 1 \) divides \( 2019^n + 1 \).
- `0009` score=0.444, number_theory, ans=`2`: Let \( S \) be a set of \( n \) distinct integers. Define a function \( f: S \to S \) such that for any two distinct elements \( a, b \in S \), the value \( f(a) - f(b) \) divides \( a - b \). Find the maximum possible value of \( n \) for which such a functi...

