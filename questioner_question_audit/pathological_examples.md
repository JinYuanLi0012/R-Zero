# Pathological Examples From Questioner Data

These are real rows from the filtered datasets used for solver training.

Source files:

- `round1_questioner_v1_for_solver_v1.jsonl`
- `round2_questioner_v2_for_solver_v2.jsonl`

The `score` field is the solver majority-agreement score used by the pipeline before filtering. These examples were still admitted into the filtered training datasets.

## Round 1, ID 0001

Score: `0.3333333333333333`  
Stored answer: `1`

Problem:

> In a small village, there are 20 houses, each with a unique number from 1 to 20. One day, the village decides to paint each house a color based on the sum of its house number's digits. If the sum is even, the house is painted blue; if odd, it's painted red. Additionally, if a house number's digits sum to a multiple of 5, it gets painted green. How many houses are painted green?

Issue:

The digit sums from 1 to 20 that are multiples of 5 occur at house numbers `5`, `14`, and `19`, with digit sums `5`, `5`, and `10`. So the answer should be `3`, not `1`.

Why it matters:

This is a straightforward arithmetic/counting error in the pseudo-label.

## Round 1, ID 0043

Score: `0.3333333333333333`  
Stored answer: `3`

Problem:

> A cubic polynomial \(p(x)\) with real coefficients satisfies \(p(0) = -1\), \(p(1) = -5\), and has a local extremum at \(x = -1\). Find \(p(2)\).

Issue:

Let \(p(x)=ax^3+bx^2+cx+d\). The constraints give:

- \(d=-1\)
- \(a+b+c=-4\)
- \(p'(-1)=3a-2b+c=0\)

There are only three independent constraints for four coefficients, so \(p(2)\) is not determined. For example, solving leaves a free parameter \(a\), and \(p(2)\) changes with it.

Why it matters:

The question is underdetermined, but the training data assigns a single answer.

## Round 1, ID 0046

Score: `0.4444444444444444`  
Stored answer: `25`

Problem:

> In the Cartesian coordinate system, a circle is defined by the equation \(x^2 + y^2 = 25\). A point \(P\) lies on this circle. If the tangent line at \(P\) intersects the x-axis at point \(A\) and the y-axis at point \(B\), find the area of triangle \(AOB\) where \(O\) is the origin. Express your answer in simplest radical form.

Issue:

The area depends on the location of \(P=(x_0,y_0)\). The tangent is \(x x_0 + y y_0 = 25\), with intercepts \(25/x_0\) and \(25/y_0\), so the area is \(625/(2|x_0 y_0|)\). This is not constant over the circle.

Why it matters:

The problem is under-specified. A single numeric answer like `25` is not justified.

## Round 1, ID 0052

Score: `0.5`  
Stored answer: `4`

Problem:

> What is the smallest positive integer \(n\) for which the equation \(x^2 - n = 0\) has exactly two distinct integer solutions, both of which are positive?

Issue:

If \(n\) is a perfect square, the integer solutions are \(x=\sqrt n\) and \(x=-\sqrt n\). They are distinct, but one is negative. There cannot be two distinct positive integer solutions to \(x^2=n\).

Why it matters:

The question is impossible as written, but the stored answer `4` corresponds to the solutions `2` and `-2`, not two positive solutions.

## Round 2, ID 0004

Score: `0.3333333333333333`  
Stored answer: `20`

Problem:

> In the complex plane, the vertices of a regular icosagon (20-sided polygon) are located at the 20th roots of unity. Let \(P\) be a point inside the icosagon such that the sum of the distances from \(P\) to each vertex is minimized. Determine the coordinates of \(P\) and the minimum sum of distances from \(P\) to the vertices.

Issue:

By symmetry, the minimizing point should be the origin. The minimum sum is the sum of distances from the origin to the 20 roots of unity, which is `20`. The stored answer only gives `20`, omitting the requested coordinates of \(P\).

Why it matters:

The answer is incomplete relative to the requested output. This can train the solver to emit partial answers that satisfy a weak boxed-answer check.

## Round 2, ID 0021

Score: `0.3333333333333333`  
Stored answer: `0`

Problem:

> Let \(P(x) = x^3 + ax^2 + bx + c\) be a cubic polynomial with real coefficients. Suppose \(P(1) = P(2) = P(3) = P(4) = P(5) = P(6) = 0\). If \(P(7) = k\), where \(k\) is a positive integer, find the value of \(k\).

Issue:

A nonzero cubic polynomial cannot have six distinct roots. The only polynomial of degree at most three with roots at `1,2,3,4,5,6` is the zero polynomial, but then \(P(7)=0\), contradicting the statement that \(k\) is positive.

Why it matters:

The problem is internally inconsistent. The stored answer `0` also contradicts the condition that \(k\) is positive.

## Round 2, ID 0028

Score: `0.4444444444444444`  
Stored answer: `25`

Problem:

> In a right triangle ABC, with angle C being the right angle, the lengths of the legs AB and BC are integers. A circle is inscribed in triangle ABC, touching AB at D, BC at E, and AC at F. If the radius of the inscribed circle is 5, and the perimeter of the triangle is twice the radius, find the area of the triangle.

Issue:

If angle \(C\) is the right angle, then the legs should be \(AC\) and \(BC\), not \(AB\) and \(BC\). More seriously, an inradius of `5` and perimeter `10` is impossible for a nondegenerate triangle: area \(K = r s = 5 \cdot 5 = 25\), but a triangle with perimeter 10 cannot have inradius 5.

Why it matters:

The stored answer `25` appears to come from \(K=rs\), but the geometric conditions are impossible.

## Round 2, ID 0041

Score: `0.4444444444444444`  
Stored answer: `1`

Problem:

> Find the smallest positive integer \(n\) such that there exists a function \(f: \mathbb{Z}^+ \to \mathbb{Z}^+\) satisfying the following conditions for all positive integers \(a\) and \(b\): 1. \(f(a + b) = f(a) + f(b) - 2f(ab)\) 2. \(f(n) = 2023\)

Issue:

Set \(a=b=1\). Then \(f(2)=f(1)+f(1)-2f(1)=0\). But the codomain is \(\mathbb{Z}^+\), so \(f(2)\) must be positive. No such function exists.

Why it matters:

The problem is inconsistent, yet it is assigned a concrete answer.

## Round 2, ID 0045

Score: `0.4444444444444444`  
Stored answer: `10`

Problem:

> In a certain country, there are \(n\) cities connected by a network of roads, where each road connects two distinct cities. The government decides to color each road either red or blue, such that no three cities form a triangle with all three sides of the same color. What is the maximum possible number of roads in this network?

Issue:

The maximum number of roads depends on \(n\). Since \(n\) is not specified and the requested answer is a function of \(n\), a fixed answer `10` is not well-defined.

Why it matters:

This is another under-specified problem that can still produce a boxed pseudo-label.

