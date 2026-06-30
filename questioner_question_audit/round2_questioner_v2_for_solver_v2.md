# round2_questioner_v2_for_solver_v2

Source: `jinyuan222/qwen3_4b_fullrun_authorsettings_solver_v2`  
Total: 2039

## 0000 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the number of ordered triples \((a, b, c)\) where \(a, b,\) and \(c\) are integers satisfying \(1 \leq a, b, c \leq n\) and \(a + b + c\) is a multiple of 3 is exactly 1000.

Answer: `15`

## 0001 | score=0.444 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) has a root modulo any prime \( p \).

Answer: `2`

## 0002 | score=0.444 | geometry

Find all positive integers \( n \) such that \( n^2 + 3n + 2 \) is a perfect square.

Answer: `0`

## 0003 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that there exist positive integers \( a_1, a_2, \ldots, a_n \) satisfying the following conditions:

1. \( a_1 + a_2 + \cdots + a_n = 2023 \),
2. Each \( a_i \) is divisible by \( 3 \) but not by \( 9 \),
3. For any subset \( S \subseteq \{1, 2, \ldots, n\} \), the sum of the elements in \( S \) is not divisible by \( 5 \).

Determine the remainder when \( n \) is divided by \( 1000 \).

Answer: `675`

## 0004 | score=0.333 | geometry

In the complex plane, the vertices of a regular icosagon (20-sided polygon) are located at the 20th roots of unity. Let \( P \) be a point inside the icosagon such that the sum of the distances from \( P \) to each vertex is minimized. Determine the coordinates of \( P \) and the minimum sum of distances from \( P \) to the vertices.

Answer: `20`

## 0005 | score=0.778 | geometry

Consider a regular octagon $ABCDEFGH$ inscribed in a circle of radius $r$. Let $P$ be a point inside the octagon such that $PA = PB = PC = PD = PE = PF = PG = PH$. Determine the area of the octagon as a function of $r$ and $P$’s coordinates. Specifically, if $P$ is located at a distance $d$ from the center of the octagon, find the area of the octagon in terms of $r$ and $d$.

Answer: `2\sqrt{2} r^2`

## 0006 | score=0.556 | geometry

In the complex plane, let $P$ be a point with coordinates $(a, b)$, where $a$ and $b$ are positive integers. Define a sequence of complex numbers $\{z_n\}_{n \geq 0}$ as follows:
- $z_0 = P$.
- For each $n \geq 1$, $z_n$ is the midpoint of the line segment joining $z_{n-1}$ and its reflection over the origin, and then translated by the vector $i \cdot n$, where $i$ is the imaginary unit.

Let $S$ be the set of all points $P$ for which the sequence $\{z_n\}$ is periodic with a period dividing $2023$. Determine the number of elements in $S$ that satisfy $1 \leq a \leq 1000$ and $1 \leq b \leq 1000$.

Answer: `1000000`

## 0007 | score=0.444 | number_theory

In the complex plane, let \( z_1 \) and \( z_2 \) be the roots of the polynomial \( x^2 - 2x + 13 \). Define a sequence \( \{a_n\} \) such that \( a_1 = 2 \), \( a_2 = 3 \), and for \( n \geq 3 \), \( a_n \) is the smallest positive integer such that \( a_n \) is coprime to all previous terms in the sequence and \( a_n \) satisfies the equation
\[ a_n z_1^n + a_n z_2^n = a_{n-1} z_1^{n-1} + a_{n-1} z_2^{n-1} + \cdots + a_2 z_1^2 + a_2 z_2^2 + a_1 z_1 + a_1 z_2. \]
Find the value of \( a_{10} \).

Answer: `29`

## 0008 | score=0.444 | number_theory

Find all positive integers \( n \) such that \( n^2 + n + 1 \) divides \( 2019^n + 1 \).

Answer: `3`

## 0009 | score=0.444 | number_theory

Let \( S \) be a set of \( n \) distinct integers. Define a function \( f: S \to S \) such that for any two distinct elements \( a, b \in S \), the value \( f(a) - f(b) \) divides \( a - b \). Find the maximum possible value of \( n \) for which such a function \( f \) exists.

Answer: `2`

## 0010 | score=0.778 | algebra

Let \( P(x) \) be a polynomial of degree 4 such that \( P(1) = 1 \), \( P(2) = 2 \), \( P(3) = 3 \), \( P(4) = 4 \), and \( P(5) = 5 \). Find the value of \( P(6) \).

Answer: `6`

## 0011 | score=0.778 | geometry

Consider a regular polygon with 1025 sides. Each vertex of this polygon is assigned a unique integer from 1 to 1025. A sequence of vertices \(v_1, v_2, \ldots, v_{1025}\) is defined such that the sum of the integers assigned to any consecutive three vertices is a prime number. Find the number of such sequences.

Answer: `0`

## 0012 | score=0.375 | number_theory

What is the smallest positive integer \( n \) such that there exist three distinct integers \( a, b, c \) satisfying \( a^n + b^n = c^n \) and \( a + b + c = 2023 \)?

Answer: `1`

## 0013 | score=0.556 | other

In a mystical forest, there are three types of magical trees: Silver, Gold, and Bronze. The number of Silver trees is double the number of Gold trees, and the number of Bronze trees is one-third the number of Gold trees. If the total number of trees in the forest is 260, how many trees of each type are there?

Answer: `26`

## 0014 | score=0.333 | geometry

Let \( ABCD \) be a square with side length 1. Points \( E \) and \( F \) lie on sides \( AB \) and \( BC \) respectively, such that \( AE = BF \). A semicircle with diameter \( EF \) is drawn inside the square, tangent to sides \( AD \) and \( CD \). Find the length of \( EF \).

Answer: `\sqrt{2}`

## 0015 | score=0.667 | number_theory

Find all positive integers \( n \) such that \( n^2 + n + 1 \) divides \( 2^n - 1 \).

Answer: `5`

## 0016 | score=0.778 | geometry

A convex polyhedron \(P\) with 2024 faces is given, and it is known that each face is either a triangle or a quadrilateral. If the total number of edges in \(P\) is 5000, find the number of vertices in \(P\).

Answer: `2978`

## 0017 | score=0.667 | number_theory

Find the number of ordered triples $(a, b, c)$ of positive integers such that $a, b,$ and $c$ are pairwise coprime, and $abc$ divides $a^4 + b^4 + c^4$.

Answer: `1`

## 0018 | score=0.556 | geometry

In the plane, let \( P \) be a set of \( n \) points, no three of which are collinear. Define a "colorful convex hull" as a convex polygon that passes through at least one point of \( P \) of each color. Suppose \( P \) is colored such that there are \( r \) colors, with at least \( k \) points of each color. Determine the minimum number of colorful convex hulls required to cover all \( n \) points of \( P \), as a function of \( n \), \( r \), and \( k \).

Answer: `\left\lceil \frac{n}{r} \right\rceil`

## 0019 | score=0.778 | geometry

A sequence of positive integers \( a_1, a_2, \ldots, a_n \) has the property that for any positive integer \( k \), the sum of the first \( k \) terms is a perfect square. If \( a_1 = 1 \) and \( a_{100} = 200 \), find the smallest possible value of \( n \).

Answer: `100`

## 0020 | score=0.667 | number_theory

Let $P(x) = x^3 - 6x^2 + 11x - 6$ be a polynomial with integer coefficients. Suppose $a, b,$ and $c$ are the roots of $P(x)$. Define a sequence $(x_n)$ by $x_1 = a + b + c$ and $x_{n+1} = x_n^2 - 2x_n + 2$ for $n \geq 1$. Find the smallest positive integer $k$ such that $x_k$ is an integer.

Answer: `1`

## 0021 | score=0.333 | number_theory

Let $P(x) = x^3 + ax^2 + bx + c$ be a cubic polynomial with real coefficients. Suppose $P(1) = P(2) = P(3) = P(4) = P(5) = P(6) = 0$. If $P(7) = k$, where $k$ is a positive integer, find the value of $k$.

Answer: `0`

## 0022 | score=0.667 | number_theory

Find all prime numbers \( p \) such that the equation \( x^3 - px^2 + (p+1)x - 1 = 0 \) has three integer roots.

Answer: `3`

## 0023 | score=0.556 | geometry

Let \( ABCD \) be a convex quadrilateral with \( AB = a \), \( BC = b \), \( CD = c \), and \( DA = d \). Suppose that the diagonals \( AC \) and \( BD \) intersect at point \( E \) such that \( AE \) and \( CE \) are equal, as are \( BE \) and \( DE \). If the area of triangle \( ABE \) is \( 15 \), the area of triangle \( BCE \) is \( 20 \), the area of triangle \( CDE \) is \( 10 \), and the area of triangle \( DAE \) is \( x \), find the value of \( x \).

Answer: `15`

## 0024 | score=0.667 | geometry

In the complex plane, let $A,$ $B,$ and $C$ be points corresponding to the complex numbers $a,$ $b,$ and $c$ respectively. Suppose $|a| = |b| = |c| = 1$ and $a + b + c = 0.$ If the circle with diameter $AB$ intersects the circumcircle of $\triangle ABC$ at a point $P$ distinct from $A$ and $B,$ find the value of $\frac{1}{|a - c|^2} + \frac{1}{|b - c|^2}.$

Answer: `\frac{2}{3}`

## 0025 | score=0.778 | number_theory

Given that \( p \) is a prime number, find all positive integers \( n \) for which the number of integers \( 0 \le k < n \) satisfying the congruence \( \binom{n}{k} \equiv 0 \pmod{p^2} \) is exactly \( n - \varphi(n) \), where \( \varphi \) denotes Euler's totient function.

Answer: `p`

## 0026 | score=0.778 | algebra

Let $f(x)$ be a continuous function on the interval $[0, 1]$ such that
\[ \int_0^1 x^2 f(x) \,dx = \frac{1}{6}. \]
Find the minimum value of
\[ \int_0^1 (f(x))^2 \,dx. \]

Answer: `\frac{5}{36}`

## 0027 | score=0.667 | number_theory

Find the smallest positive integer \( n \) such that for all positive integers \( k \leq n \), the polynomial \( P(x) = x^3 - kx^2 + kx - 1 \) has at least one integer root.

Answer: `1`

## 0028 | score=0.444 | geometry

In a right triangle ABC, with angle C being the right angle, the lengths of the legs AB and BC are integers. A circle is inscribed in triangle ABC, touching AB at D, BC at E, and AC at F. If the radius of the inscribed circle is 5, and the perimeter of the triangle is twice the radius, find the area of the triangle.

Answer: `25`

## 0029 | score=0.556 | geometry

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^3 - 3x + n \) has three distinct integer roots, and the sum of the squares of these roots is exactly 14.

Answer: `6`

## 0030 | score=0.556 | number_theory

In a mystical village, there are seven distinct types of magical flowers, each with a unique property that can be represented by a prime number. One day, the village elder decides to create a magical spell by selecting a subset of these flowers and multiplying their properties together. To ensure the spell is effective, the elder requires that the product of the selected flowers' properties must be exactly 120. How many different spells can the elder create? Note that the empty subset is not considered.

Answer: `1`

## 0031 | score=0.556 | number_theory

Let \( S \) be the set of all positive integers that can be represented as the sum of two or more consecutive positive integers. Find the smallest positive integer that is not in \( S \).

Answer: `1`

## 0032 | score=0.444 | geometry

Find all positive integers \( n \) such that there exists a set of \( n \) points in the plane, no three of which are collinear, with the following property: for any two distinct points \( A \) and \( B \) in the set, there is a point \( C \) in the set such that the area of triangle \( ABC \) is equal to \( n \). Furthermore, prove that for these values of \( n \), the set of points must form a regular polygon.

Answer: `3`

## 0033 | score=0.333 | geometry

In a plane, let \(P\) be a point inside a square \(ABCD\) with side length 1. Let \(E\) and \(F\) be the midpoints of \(AB\) and \(CD\) respectively, and let \(G\) be the intersection of lines \(AE\) and \(CF\). If the area of triangle \(BPG\) is \(\frac{1}{12}\), find the distance from \(P\) to the center of the square.

Answer: `\frac{1}{6}`

## 0034 | score=0.556 | geometry

In the complex plane, consider the regular 2023-gon $P_1P_2\ldots P_{2023}$ with vertices $P_k = \cos\left(\frac{2\pi k}{2023}\right) + i\sin\left(\frac{2\pi k}{2023}\right)$ for $k = 1, 2, \ldots, 2023$. A complex number $z$ is chosen uniformly at random from the interior of this polygon. Let $Q$ be the expected value of the product $z \cdot z^*$, where $z^*$ denotes the complex conjugate of $z$. Find the greatest integer less than or equal to $Q$.

Answer: `0`

## 0035 | score=0.444 | number_theory

Consider a sequence of integers \( a_1, a_2, a_3, \ldots, a_{2023} \) where each \( a_i \) is either 1 or -1. Define a function \( S_k \) as the sum of the first \( k \) terms of the sequence, i.e., \( S_k = a_1 + a_2 + \cdots + a_k \) for \( 1 \leq k \leq 2023 \). Determine the number of distinct sequences for which \( S_k \) is never zero for any \( k \) in the range \( 1 \leq k \leq 2023 \).

Answer: `2`

## 0036 | score=0.444 | number_theory

Let $S$ be the set of all ordered triples $(a,b,c)$ of positive integers such that $a \leq b \leq c$ and $a + b + c = 2023$. Find the number of distinct prime factors of the sum of the elements in all ordered triples in $S$.

Answer: `3`

## 0037 | score=0.556 | geometry

Find all prime numbers \(p\) and \(q\) such that both \(p^2 + 8pq + q^2\) and \(p^2 - 8pq + q^2\) are perfect squares. Determine the sum of all such distinct prime pairs \((p, q)\).

Answer: `0`

## 0038 | score=0.444 | algebra

Consider a 3x3 grid where each cell contains either a 0 or a 1. A configuration of this grid is considered valid if it satisfies the following condition: for every pair of adjacent cells (sharing a side), the product of their values is equal to the value of the cell diagonally opposite to them. For example, if the top-left corner cell has a value of 1, then the bottom-right corner cell must also have a value of 1. How many valid configurations are there?

Answer: `2`

## 0039 | score=0.333 | geometry

In a tetrahedron $ABCD$, the edges $AB$, $AC$, and $AD$ are pairwise perpendicular, and they have lengths 3, 4, and 5 respectively. A point $P$ inside the tetrahedron is such that the sum of its distances to the faces of the tetrahedron is constant. If the sum of these distances is 9, find the coordinates of point $P$ in terms of the coordinates of the vertices $A$, $B$, $C$, and $D$.

Answer: `\left(\frac{3}{4}, 1, \frac{5}{4}\right)`

## 0040 | score=0.556 | geometry

Let \( A \), \( B \), and \( C \) be the angles of a triangle such that \( A + B + C = 180^\circ \). Given the equation
\[
\cos A \cos B + \cos B \cos C + \cos C \cos A = \frac{1}{2},
\]
determine the measure of angle \( A \).

Answer: `90^\circ`

## 0041 | score=0.444 | number_theory

Find the smallest positive integer \( n \) such that there exists a function \( f: \mathbb{Z}^+ \to \mathbb{Z}^+ \) satisfying the following conditions for all positive integers \( a \) and \( b \):
1. \( f(a + b) = f(a) + f(b) - 2f(ab) \)
2. \( f(n) = 2023 \)

Answer: `1`

## 0042 | score=0.556 | number_theory

Find the smallest positive integer \( n \) such that \( 2^n + 1 \) is divisible by \( n \).

Answer: `3`

## 0043 | score=0.333 | geometry

In triangle $ABC$, point $D$ lies on side $BC$ such that $AD$ is the angle bisector of $\angle BAC$. Let $E$ be the foot of the perpendicular from $D$ to $AB$, and let $F$ be the foot of the perpendicular from $D$ to $AC$. Given that $BD = 3$, $DC = 5$, $AB = 10$, and $AC = 14$, find the length of $EF$.

Answer: `4`

## 0044 | score=0.333 | number_theory

Find the number of ordered triples $(a,b,c)$ of positive integers such that $a+b+c=100$, where $a$ is odd, $b$ is even, and $c$ is divisible by 5.

Answer: `255`

## 0045 | score=0.444 | geometry

In a certain country, there are \( n \) cities connected by a network of roads, where each road connects two distinct cities. The government decides to color each road either red or blue, such that no three cities form a triangle with all three sides of the same color. What is the maximum possible number of roads in this network?

Answer: `10`

## 0046 | score=0.333 | number_theory

Find all positive integers \( n \) for which the equation
\[ x^2 + y^2 + z^2 = n(x + y + z) \]
has an infinite number of solutions in integers \( x, y, z \) such that \( x, y, z \) are not all zero.

Answer: `3`

## 0047 | score=0.333 | number_theory

Find all integer solutions to the equation \(x^3 - 3xy^2 + y^3 = 1\) where \(x\) and \(y\) are integers.

Answer: `(0, 1), (1, 0), (1, 3), (2, -1), (-1, -1)`

## 0048 | score=0.444 | geometry

Let \( S \) be the set of all triangles \( ABC \) in the plane with integer side lengths \( AB, BC, \) and \( CA \) such that the perimeter of \( ABC \) is less than or equal to 2023. Find the sum of the areas of all triangles \( ABC \) in \( S \).

Answer: `0`

## 0049 | score=0.778 | geometry

Find the smallest positive integer \( n \) such that the sum of the first \( n \) terms of the sequence defined by \( a_k = k^2 - 3k + 4 \) is a perfect square.

Answer: `2`

## 0050 | score=0.444 | geometry

In the triangular grid shown below, each small triangle has an area of 1 square unit. A path is defined as a sequence of moves from one vertex to another, where each move must be along the edge of a triangle and the path must not revisit any vertex. Given that the path starts at the bottom-left vertex and ends at the top vertex, find the number of distinct paths that consist of exactly 6 moves, where each move is along a horizontal or vertical edge.

Answer: `20`

## 0051 | score=0.333 | combinatorics

In the three-dimensional space, a sphere is inscribed in a cube whose edges are of length 1. A point P is chosen uniformly at random within the cube. What is the probability that the distance from P to the center of the sphere is less than the distance from P to the nearest face of the cube?

Answer: `\frac{1}{8}`

## 0052 | score=0.667 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + 2x^{n-1} + 3x^{n-2} + \cdots + (n-1)x + n \) has a root that is a rational number.

Answer: `1`

## 0053 | score=0.444 | number_theory

Let \( P(x) \) be a polynomial of degree 4 with integer coefficients such that \( P(1) = 10 \), \( P(2) = 20 \), \( P(3) = 30 \), and \( P(4) = 40 \). Find the smallest possible value of \( P(5) \).

Answer: `74`

## 0054 | score=0.667 | geometry

In triangle \( ABC \), point \( D \) lies on side \( BC \) such that \( BD:DC = 2:1 \). Point \( E \) lies on side \( AC \) such that \( AE:EC = 1:2 \). The line segment \( DE \) intersects the circumcircle of triangle \( ABC \) again at point \( F \). If \( AB = 3 \), \( BC = 4 \), and \( AC = 5 \), find the length of segment \( DF \).

Answer: `2`

## 0055 | score=0.333 | number_theory

Let \( f(n) \) be the number of ways to write \( n \) as a sum of positive integers where the summands are in non-decreasing order and the first term is at least 2. For example, \( f(3) = 1 \) because the only way is \( 3 = 2 + 1 \). Find the smallest positive integer \( n \) such that \( f(n) \) is divisible by 1000.

Answer: `1000`

## 0056 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers. A subset \( T \) of \( S \) is called *pretty* if for every pair of distinct elements \( a, b \in T \), the sum \( a + b \) is not divisible by 3. Find the largest possible number of elements in a pretty subset of \( S \) where the elements are all less than 2023.

Answer: `675`

## 0057 | score=0.556 | number_theory

What is the largest integer $n$ such that there exists an integer $k$ for which the polynomial $P(x) = x^4 + kx^3 + 2013x^2 - 1006x + 503$ can be expressed as the product of two non-constant polynomials with integer coefficients, and $n$ divides the sum of the coefficients of one of the factors?

Answer: `503`

## 0058 | score=0.500 | number_theory

Let \( p \) be a prime number greater than 3, and let \( \mathbb{F}_p \) be the finite field with \( p \) elements. Consider the polynomial \( f(x) = x^3 - x + 1 \) over \( \mathbb{F}_p \). Determine the number of distinct elements \( a \in \mathbb{F}_p \) such that \( f(a) \) is a quadratic residue modulo \( p \).

Answer: `\frac{p-1}{2}`

## 0059 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the equation \( x^2 + y^2 + z^2 + w^2 = n \) has exactly 24 solutions in integers \( (x, y, z, w) \), where the order of \( x, y, z, w \) does not matter.

Answer: `24`

## 0060 | score=0.556 | geometry

Let \( S \) be a set of 2023 distinct positive integers, none of which are perfect squares or perfect cubes. Prove that there exists a subset \( T \subseteq S \) of size 10, such that the product of any two distinct elements of \( T \) is not a perfect square or a perfect cube.

Answer: `10`

## 0061 | score=0.778 | geometry

In the coordinate plane, consider an equilateral triangle \( ABC \) with side length \( s \) and one vertex at the origin \( A(0,0) \). Let \( D \) be the midpoint of side \( BC \), and let \( E \) be a point on the extension of \( AD \) such that \( DE = AD \). If the area of triangle \( ADE \) is \( \frac{3\sqrt{3}}{2} s^2 \), find the ratio of the area of triangle \( ADE \) to the area of the original equilateral triangle \( ABC \).

Answer: `6`

## 0062 | score=0.556 | geometry

In the plane, a set of points \( P \) is chosen such that no three points are collinear. For each pair of points \( (A, B) \) in \( P \), let \( f(A, B) \) be the minimum distance between a point in \( P \) and the line segment \( AB \). Define \( M = \max_{A, B \in P} f(A, B) \). Prove that there exist two points \( X \) and \( Y \) in \( P \) such that the distance \( XY \) is less than or equal to \( 2M \).

Answer: `2M`

## 0063 | score=0.444 | number_theory

Find all positive integers \( n \) such that the equation
\[ x^3 + y^3 + z^3 = nxyz \]
has a solution in positive integers \( x, y, z \) where \( x, y, z \) are pairwise coprime.

Answer: `3`

## 0064 | score=0.556 | geometry

Let $ABC$ be a triangle with circumcircle $\Gamma$. Let $D$ be a point on the minor arc $AB$ of $\Gamma$. The line through $D$ parallel to $BC$ intersects the line $AC$ at $E$. The line through $D$ parallel to $AC$ intersects the line $BC$ at $F$. Let $M$ be the midpoint of $EF$. Prove that the line through $M$ perpendicular to $AD$ passes through the center of $\Gamma$.

Answer: `O`

## 0065 | score=0.778 | geometry

A convex hexagon has internal angles that are in arithmetic progression, with the smallest angle being 120 degrees and the largest angle being 150 degrees. Find the measure of the smallest angle of the hexagon that is not an endpoint of the arithmetic progression.

Answer: `126`

## 0066 | score=0.556 | number_theory

Find all positive integers \( n \) such that there exists a function \( f : \mathbb{Z} \to \{1, 2, \ldots, n\} \) satisfying the following conditions:
1. For all integers \( a \) and \( b \), \( f(a + b) = f(ab) \).
2. The function \( f \) is not constant.

Answer: `1`

## 0067 | score=0.333 | geometry

Let $ABC$ be an acute triangle with circumcenter $O$ and orthocenter $H$. Points $D$ and $E$ are chosen on sides $AB$ and $AC$ respectively such that $\angle AOD = \angle AOE = 90^\circ$. Let $P$ be the intersection of lines $DE$ and $BC$. If $AD = 4$, $AE = 6$, and $AP = 5$, find the area of triangle $ABC$.

Answer: `48`

## 0068 | score=0.556 | geometry

In a finite-dimensional vector space \( V \) over the field of real numbers \( \mathbb{R} \), let \( T: V \to V \) be a linear transformation. Suppose there exists a basis \( \mathcal{B} = \{v_1, v_2, \ldots, v_n\} \) of \( V \) such that the matrix representation of \( T \) with respect to \( \mathcal{B} \) is given by
\[
A = \begin{pmatrix}
1 & 1 & 0 & \cdots & 0 \\
0 & 1 & 1 & \cdots & 0 \\
0 & 0 & 1 & \cdots & 0 \\
\vdots & \vdots & \vdots & \ddots & \vdots \\
0 & 0 & 0 & \cdots & 1
\end{pmatrix}.
\]
Let \( P \) be the projection matrix onto the subspace spanned by \( v_1 \), and let \( Q \) be the matrix representing the linear transformation \( T - P \) with respect to the same basis \( \mathcal{B} \). Find the determinant of \( Q \).

Answer: `1`

## 0069 | score=0.444 | number_theory

Let \( p \) be a prime number greater than 3. Consider the polynomial \( P(x) = x^p + x^2 + 1 \). Prove that there exists at least one integer \( x \) such that \( P(x) \) is divisible by \( p^2 \).

Answer: `x`

## 0070 | score=0.778 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a continuous function such that \( f(x) = f(2x) + f(x-1) \) for all \( x \in \mathbb{R} \). Prove that \( f(x) = 0 \) for all \( x \in \mathbb{R} \).

Find all such functions \( f \).

Answer: `f(x) = 0`

## 0071 | score=0.333 | geometry

Find all positive integers \( n \) such that \( n \) divides \( 2^n + 1 \) and \( n \) is a perfect square.

Answer: `1, 9`

## 0072 | score=0.556 | number_theory

What is the sum of the digits of the largest three-digit number \( N \) such that \( N \) is divisible by 11 and the sum of its digits is equal to 11?

Answer: `11`

## 0073 | score=0.444 | logic_puzzle

Consider a 4x4 grid, with four rows and four columns. Each cell in the grid can be either black or white. A configuration of the grid is called "unique" if there are no two distinct rows that have the same pattern of black and white cells, and no two distinct columns that have the same pattern of black and white cells.

How many unique configurations are there for the 4x4 grid?

Answer: `43680`

## 0074 | score=0.333 | geometry

In the complex plane, consider three points \(A\), \(B\), and \(C\) such that \(A = 1 + i\), \(B = -1 - i\), and \(C\) lies on the unit circle. If \(C\) is chosen so that the area of triangle \(ABC\) is maximized, determine the coordinates of \(C\). Additionally, find the maximum area of triangle \(ABC\).

Answer: `2`

## 0075 | score=0.444 | geometry

A regular hexagon is inscribed in a circle of radius \(r\). Each side of the hexagon is then divided into three equal segments. Triangles are constructed outside the hexagon such that each triangle's base is one of these segments and its apex is the center of the circle. If the area of the original hexagon is \(A\), find the total area of the six newly constructed triangles in terms of \(A\).

Answer: `\frac{2A}{3\sqrt{3}}`

## 0076 | score=0.444 | number_theory

Find all positive integers \( n \) such that there exists a polynomial \( P(x) \) with integer coefficients satisfying
\[ P(1) = n, \quad P(2) = 2n, \quad P(3) = 3n, \quad \text{and} \quad P(4) = 4n. \]

Answer: `1`

## 0077 | score=0.556 | number_theory

What is the minimum number of positive integers less than 2023 that must be selected so that some three of them have a sum that is a multiple of 3?

Answer: `7`

## 0078 | score=0.556 | geometry

Find all positive integers \( n \) such that \( n^3 + 2n^2 + 2n + 1 \) is a perfect square.

Answer: `0`

## 0079 | score=0.333 | number_theory

A set of integers \( S \) is defined such that for every \( n \in S \), the set \( S \) satisfies the property that \( n + k \) is also in \( S \) for all \( k \in S \) where \( n + k < 2024 \). Given that the sum of all elements in \( S \) is \( 2023 \), determine the smallest possible number of elements in \( S \).

Answer: `2`

## 0080 | score=0.444 | geometry

Find all integers $n$ such that $n^2 + 5n + 19$ is the square of a prime number.

Answer: `-15, -6, 1, 10`

## 0081 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the number of divisors of \( n \) is equal to the sum of the digits of \( n \), and \( n \) can be expressed as the sum of two positive integers in exactly three different ways where each pair is relatively prime. Additionally, show that \( n \) is a semiprime (a product of two prime numbers).

Answer: `22`

## 0082 | score=0.333 | geometry

In a triangular park, three paths form the sides of the triangle. The length of the path from A to B is 15 meters, from B to C is 20 meters, and from C to A is 25 meters. A fountain is placed at the centroid of the triangle. Calculate the shortest distance from the fountain to the perimeter of the park. Express your answer in simplest radical form.

Answer: `4`

## 0083 | score=0.444 | algebra

In a regular tetrahedron, the vertices are labeled A, B, C, and D. A point P is chosen inside the tetrahedron such that the sum of the distances from P to the faces is a constant. If the side length of the tetrahedron is \( s \), find the sum of the distances from P to the faces in terms of \( s \).

Answer: `\sqrt{\frac{2}{3}} s`

## 0084 | score=0.333 | geometry

Let \( S \) be the set of all non-degenerate triangles with integer side lengths and a perimeter of 12. Determine the number of such triangles \( S \) that have an area that is an integer, and express your answer as a fraction of the total number of triangles in \( S \).

Given the condition that the side lengths \( a, b, c \) (with \( a \leq b \leq c \)) satisfy \( a + b + c = 12 \) and the area is an integer, find the fraction \( \frac{n}{m} \), where \( n \) is the count of triangles meeting the integer area condition and \( m \) is the total number of triangles in \( S \).

Express the final answer as \( \frac{n}{m} \) in simplest form.

Answer: `\frac{1}{3}`

## 0085 | score=0.556 | geometry

Given a regular hexagon $ABCDEF$ with side length $s$, let $P$ be the point inside the hexagon such that $\angle APB = 90^\circ$ and $\angle CPB = 120^\circ$. Find the length of segment $BP$ in terms of $s$.

Answer: `s`

## 0086 | score=0.667 | number_theory

Find all pairs of positive integers \((a, b)\) such that \(a^2 + b^2 = 3ab - 1\) and \(a < b\).

Answer: `(1, 2)`

## 0087 | score=0.667 | number_theory

What is the smallest positive integer $n$ such that $n$ divides the number of ways to arrange 10 distinct books on a shelf, where the books are in such a configuration that no two adjacent books are of the same color if the books are colored in a repeating pattern of red, green, blue, red, green, blue, and so on?

Answer: `1`

## 0088 | score=0.333 | geometry

Find all positive integers \( n \) such that the number \( n^2 + 3n + 2 \) is a perfect square.

Answer: `0`

## 0089 | score=0.444 | combinatorics

In the mystical land of Symmetryville, there exists a peculiar tree known as the Graph Tree. Each day, the tree's leaves rearrange themselves in a unique configuration, forming a graph with $2n$ vertices. The challenge of Symmetryville is to find the day when the graph formed by the leaves is a perfect matching, that is, a set of edges that covers every vertex exactly once. A perfect matching is considered special if every edge in the matching has a distinct pair of leaves at its ends. Given that the number of vertices is always even, determine the smallest number of days $n$ required to guarantee that a perfect matching with distinct pairs exists, assuming the tree is well-mannered and does not repeat its configuration on any day until all possible configurations have been visited.

Answer: `2`

## 0090 | score=0.556 | number_theory

Find the number of ordered quadruples $(a, b, c, d)$ of positive integers such that $a^2 + b^2 + c^2 + d^2 = 2023$ and $a, b, c, d$ are pairwise relatively prime.

Answer: `0`

## 0091 | score=0.556 | geometry

In the coordinate plane, let $A(0,0)$, $B(14,0)$, and $C(14,14)$ be the vertices of a right triangle $ABC$. A point $P(x,y)$ inside the triangle satisfies the condition that the sum of its distances to the three vertices is minimized. Find the value of $x+y$.

Answer: `14`

## 0092 | score=0.500 | combinatorics

A regular octahedron has its vertices labeled with the numbers 1 through 8. The octahedron is rotated in space, and you are allowed to rotate it around any of its three axes of symmetry (one through the centers of opposite faces and two through the midpoints of opposite edges). Prove that there exists a sequence of at most 7 rotations that will return the octahedron to its original position, regardless of its starting orientation. Additionally, find the minimum number of such rotations needed for the octahedron to return to its original orientation.

Answer: `7`

## 0093 | score=0.444 | geometry

A regular tetrahedron with side length 2 is divided into four congruent pyramids, each having a base that is an equilateral triangle of side length 1. One pyramid is removed, leaving three pyramids. The remaining pyramids are then filled with water. If each pyramid is filled to half its height, what is the height of the water level in the tallest pyramid?

Answer: `\frac{\sqrt{6}}{12}`

## 0094 | score=0.444 | algebra

设 \(f(x)\) 是一个定义在实数集上的连续函数，满足以下性质：
对于所有的 \(x \in \mathbb{R}\)，有 \(f(x) + f(-x) = 2\) 且 \(f(x) > 0\)。
已知 \(f(0) = 1\) 并且 \(f(x)\) 在 \(x=0\) 处可导。

求证：存在唯一一个正实数 \(a\) 使得 \(f(a) = a\)，并计算 \(f'(0)\)。

Answer: `0`

## 0095 | score=0.667 | number_theory

Find all positive integers \( n \) such that the sum of the divisors of \( n \) (including 1 and \( n \) itself) is equal to \( n + \tau(n) + 2 \), where \( \tau(n) \) denotes the number of divisors of \( n \).

Answer: `6`

## 0096 | score=0.556 | number_theory

A function \( f \) is defined for all positive integers such that \( f(1) = 1 \) and for \( n > 1 \), \( f(n) \) is the smallest integer greater than \( f(n-1) \) that is not a divisor of \( n \). Find the value of \( f(2023) \).

Answer: `2024`

## 0097 | score=0.667 | number_theory

In the infinite sequence \(a_n\), where \(a_1 = 1\) and \(a_{n+1} = \frac{1}{2}(a_n + \frac{1}{a_n})\) for all \(n \geq 1\), find the smallest positive integer \(k\) such that \(a_k\) is within \(0.01\) of \(a_{k+1}\). Additionally, prove that the sequence converges to a limit.

Answer: `1`

## 0098 | score=0.778 | number_theory

Consider a sequence of positive integers \(a_1, a_2, a_3, \ldots, a_n\) such that each term after the first is the least common multiple (LCM) of the preceding terms. If \(a_1 = 2\) and \(a_{10} = 200\), find the number of possible values for \(a_5\).

Answer: `1`

## 0099 | score=0.556 | number_theory

Consider a sequence of positive integers \(a_1, a_2, a_3, \ldots\) where \(a_1 = 1\) and for all positive integers \(n\), \(a_{n+1}\) is the smallest integer greater than \(a_n\) such that the set \(\{a_1, a_2, \ldots, a_{n+1}\}\) does not contain any three distinct elements \(x, y, z\) such that \(x + y = z\). Find \(a_{2023}\).

Answer: `2023`

## 0100 | score=0.556 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a continuous function such that for all real numbers \( x \) and \( y \),
\[ f(x+y) = f(x) \cdot f(y) + f(x) + f(y). \]
Given that \( f(1) = 2 \), find the value of \( f(100) \).

Answer: `3^{100} - 1`

## 0101 | score=0.333 | geometry

Let $ABC$ be an isosceles triangle with $AB = AC$. The angle bisectors of $\angle BAC$ and $\angle ABC$ intersect at point $D$. If $AD = 2BD$ and $BC = 10$, find the area of triangle $ABC$.

Answer: `25\sqrt{3}`

## 0102 | score=0.556 | number_theory

Find all real numbers \( x \) such that the expression \( \sqrt{x - \sqrt{x + 1}} + \sqrt{x + \sqrt{x + 1}} \) is an integer. Justify your answer.

Answer: `\frac{5}{3}`

## 0103 | score=0.444 | geometry

In triangle \(ABC\), the angles satisfy \(\angle A + \angle B = 3\angle C\). Let \(D\) be a point on side \(BC\) such that \(\angle BAD = \angle CAD\). The circumcircle of \(\triangle ABD\) intersects line \(AC\) again at point \(E\). If \(BD = 6\) and \(DC = 3\), find the length of segment \(BE\).

Answer: `6`

## 0104 | score=0.333 | number_theory

Let \( f(x) \) be a polynomial of degree 4 with integer coefficients such that \( f(1) = 10 \), \( f(2) = 20 \), and \( f(3) = 30 \). Determine the sum of the roots of the equation \( f(x) = 0 \).

Given that the polynomial \( f(x) \) satisfies \( f(1) = 10 \), \( f(2) = 20 \), and \( f(3) = 30 \), and knowing that \( f(x) \) is of the form \( f(x) = ax^4 + bx^3 + cx^2 + dx + e \) with integer coefficients, find the sum of the roots of the polynomial equation \( f(x) = 0 \).

Answer: `6`

## 0105 | score=0.444 | combinatorics

In a game, a player starts with a single token and can perform the following moves:
1. Add 1 token to the current total.
2. Double the current total number of tokens.
If the player can only make a total of 5 moves, how many different ways can the player end up with exactly 11 tokens?

Answer: `2`

## 0106 | score=0.444 | geometry

In triangle $ABC$, point $D$ is on side $BC$ such that $BD = 2CD$. Point $E$ is on side $AC$ such that $AE = \frac{2}{3}EC$. The line segment $AD$ intersects the line segment $BE$ at point $F$. If the area of triangle $ABC$ is 18, find the area of triangle $ABF$.

Answer: `6`

## 0107 | score=0.333 | geometry

Find all positive integers \( n \) such that there exists a sequence \( a_1, a_2, \ldots, a_n \) of positive integers satisfying the following conditions:
1. \( a_1 = 1 \) and \( a_n = n \),
2. For each \( k = 1, 2, \ldots, n-1 \), \( a_{k+1} = a_k + 1 \) or \( a_{k+1} = a_k - 1 \), and
3. The sum \( S = a_1 + a_2 + \cdots + a_n \) is a perfect square.

Answer: `1`

## 0108 | score=0.333 | number_theory

Let \( f(x) \) be a polynomial with integer coefficients such that \( f(1) = 2024 \) and \( f(2024) = 1 \). Determine the largest possible value of \( |f(2023)| \).

Answer: `2023`

## 0109 | score=0.667 | algebra

In the complex plane, let \( z \) be a root of the equation
\[ z^{10} - z^6 + z^2 - 1 = 0 \]
which satisfies \( \operatorname{Re}(z) > 0 \) and \( \operatorname{Im}(z) > 0 \). Find the value of \( \left| z^4 + z^{-4} \right| \).

Answer: `2`

## 0110 | score=0.667 | number_theory

Find all positive integers \( n \) such that \( n^3 + n^2 + n + 1 \) divides \( 3n^3 + 2n^2 + 3n + 2 \).

Answer: `1`

## 0111 | score=0.444 | geometry

In a small town, there are 100 houses arranged in a circle. Each house is painted one of three colors: red, blue, or green. The town council decides that no two adjacent houses can have the same color. Moreover, every third house, starting with the first, must be painted red. Given these conditions, determine the total number of distinct ways the houses can be painted.

Answer: `2^{67}`

## 0112 | score=0.556 | algebra

Let \( f(x) \) be a polynomial with real coefficients such that \( f(x) \) has a degree of \( 4 \) and satisfies the equation \( f(x) = f(2 - x) \) for all real numbers \( x \). Given that \( f(x) \) has a root at \( x = 1 \), determine the number of distinct real roots of the equation \( f(x) = 0 \).

Answer: `2`

## 0113 | score=0.444 | number_theory

Find all triples of integers \((a, b, c)\) such that \(a^2 + b^2 + c^2 = ab + bc + ca + 1\), and each of \(a\), \(b\), and \(c\) is a multiple of 7.

Answer: `(0, 0, 0)`

## 0114 | score=0.333 | number_theory

Let \( P(x) \) be a polynomial of degree 5 with integer coefficients such that \( P(1) = 2 \) and \( P(2) = 3 \). Additionally, suppose that \( P(x) \) has exactly one real root and this root is an irrational number. Determine the number of possible values of \( P(3) \).

Answer: `2`

## 0115 | score=0.444 | other

泰迪熊小镇的街道呈正方形网格布局，每个街区的边长均为一英里。泰迪需要从家出发，经过至少两个不同的街区，回家。泰迪最多可以走多少英里才能回到家中？

Answer: `4`

## 0116 | score=0.333 | geometry

Find all positive integers \( n \) such that \( n \) divides the sum of the squares of the first \( n \) natural numbers. That is, find all \( n \) such that \( n \mid (1^2 + 2^2 + \cdots + n^2) \).

Answer: `1`

## 0117 | score=0.778 | geometry

A sequence of positive integers \( a_1, a_2, a_3, \ldots \) is defined recursively by:
\[
a_{n+1} = a_n^2 - a_{n-1}^2 + n^2
\]
for \( n \geq 2 \), with initial conditions \( a_1 = 1 \) and \( a_2 = 2 \). Determine the smallest positive integer \( k \) such that \( a_k \) is a perfect square.

Answer: `1`

## 0118 | score=0.333 | geometry

Let \( ABC \) be an equilateral triangle with side length 1. Points \( D \) and \( E \) are chosen on sides \( AB \) and \( AC \) respectively such that \( AD = AE \). The line through \( D \) perpendicular to \( AB \) intersects the line through \( E \) perpendicular to \( AC \) at point \( F \). Find the length of the segment \( AF \).

Answer: `\frac{\sqrt{3}}{2}`

## 0119 | score=0.667 | number_theory

A finite sequence of positive integers starts with a 1 and ends with a 2. The sequence has the property that every number except the first one is the sum of the preceding number and the number that follows it. For instance, a sequence could be 1, 3, 1, 2. Given that the sum of the sequence is 50, find the number of terms in the sequence.

Answer: `10`

## 0120 | score=0.556 | number_theory

Consider a sequence of positive integers where each term after the first two is the smallest integer greater than the previous term that is relatively prime to all the preceding terms. What is the 100th term of this sequence?

Answer: `541`

## 0121 | score=0.556 | geometry

Let \( S \) be the set of all positive integers. Consider a function \( f: S \to S \) defined by the rule:
\[ f(n) = n^2 + 2n + 1. \]
Define \( T \) as the set of all \( n \in S \) such that \( f(n) \) is a perfect square. Find the number of elements in \( T \) that are less than 1000.

Answer: `999`

## 0122 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) can be written as the product of two non-constant polynomials with integer coefficients.

Answer: `3`

## 0123 | score=0.778 | geometry

In the plane, consider a set of \( n \) distinct points \( P_1, P_2, \ldots, P_n \), where no three points are collinear. Define a "triangular region" as the interior of a triangle formed by three of these points. What is the maximum possible number of triangular regions that can be formed by these \( n \) points?

Answer: `\frac{n(n-1)(n-2)}{6}`

## 0124 | score=0.667 | number_theory

Let \( S \) be the set of all positive integers that can be expressed as the sum of three distinct positive integers, each of which is a prime number. If \( n \) is the smallest element in \( S \) that is greater than 100, find \( n \) and the three prime numbers that sum up to \( n \).

Answer: `102`

## 0125 | score=0.333 | geometry

In a circle with center \(O\), let \(AB\) and \(CD\) be two chords intersecting at a point \(P\) inside the circle. Suppose \(AP = 3\), \(BP = 7\), and \(CP = 5\). If \(DP\) is extended to meet the circle again at \(Q\), find the length of \(DQ\) given that \(CQ = 12\). Express your answer as a simplified fraction.

Answer: `\dfrac{56}{5}`

## 0126 | score=0.556 | number_theory

Let \( f: \mathbb{Z} \rightarrow \mathbb{Z} \) be a function satisfying the following properties for all integers \( n \):
1. \( f(n) + f(n+1) = n^2 \)
2. \( f(n) + f(n+2) = (n+1)^2 \)
3. \( f(0) = 0 \)

Find \( f(2023) \).

Answer: `2045253`

## 0127 | score=0.667 | algebra

Let \( f(x) \) be a function defined on the interval \([0,1]\) such that for all \( x \in [0,1] \), the following inequality holds:
\[ f(x)^2 + f(1-x) \geq 1. \]
Determine the maximum possible value of \( \int_0^1 f(x) \, dx \).

Answer: `1`

## 0128 | score=0.556 | number_theory

What is the minimum possible value of the expression \(a^2 + ab + b^2\) for integers \(a\) and \(b\) such that \(|a| + |b| = 20\)?

Answer: `100`

## 0129 | score=0.556 | number_theory

Let $p$ be a prime number greater than 3. Define $a_n = p^{n+1} - p^n$ for all $n \geq 1$. Prove that for all $n$, the sum of the digits of $a_n$ is a multiple of $p-1$.

Answer: `p - 1`

## 0130 | score=0.556 | geometry

Let $S$ be the set of all positive integers $n$ such that $n^2 + 12n - 2007$ is a perfect square. Find the sum of all elements in $S$ that are less than 1000.

Answer: `448`

## 0131 | score=0.444 | number_theory

A sequence of positive integers \(a_1, a_2, a_3, \ldots\) is defined by the following rules:
1. \(a_1 = 1\)
2. For \(n \geq 1\), \(a_{n+1} = a_n^2 + 2\)
Find the number of positive divisors of \(a_{2024}\).

Answer: `2`

## 0132 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) is divisible by \( x^2 + 1 \) and \( n \) is a multiple of both 3 and 5.

Answer: `15`

## 0133 | score=0.556 | number_theory

Let \( S \) be a set of \( n \) distinct positive integers. Define a **good subset** of \( S \) as a subset where no element divides any other element in the subset. For example, in the set \( \{1, 2, 3, 4\} \), the subsets \( \{2, 3\} \) and \( \{1, 4\} \) are good subsets, but \( \{1, 2, 3\} \) is not because \( 3 \) divides \( 2 \).

Given a set \( S \) of \( n \) distinct positive integers, find the maximum possible number of good subsets of \( S \).

Answer: `2^n`

## 0134 | score=0.333 | number_theory

Let \( f(n) \) be the number of ways to write \( n \) as a sum of positive integers, where the order of the summands does not matter. For example, \( f(3) = 3 \) because \( 3 = 3 \), \( 3 = 2+1 \), and \( 3 = 1+2 \) are the only ways to write 3 as a sum of positive integers. Define a sequence \( \{a_n\} \) where \( a_n = f(n) + f(n-1) \) for \( n \geq 2 \) and \( a_1 = 1 \). Find the smallest positive integer \( n \) such that \( a_n \) is divisible by 100.

Answer: `98`

## 0135 | score=0.444 | number_theory

Let $S$ be the set of all positive integers $n$ such that $\frac{n^3 + 2n^2 + n + 1}{n^2 + n + 1}$ is an integer. Find the sum of all elements in $S$.

Answer: `0`

## 0136 | score=0.333 | algebra

设 \( f(x) \) 是一个从正整数到正整数的函数，满足对于所有正整数 \( x \)，\( f(x+1) = f(x) + f(\sqrt{x}) \)，且 \( f(1) = 1 \)。求 \( f(100) \)。

Answer: `100`

## 0137 | score=0.556 | number_theory

Find all positive integers \( n \) such that there exist positive integers \( a_1, a_2, \ldots, a_n \) satisfying the following conditions:
1. \( a_1 + a_2 + \cdots + a_n = 2023 \),
2. \( a_1^2 + a_2^2 + \cdots + a_n^2 = 2023^2 - 1 \).

Answer: `2`

## 0138 | score=0.444 | number_theory

Consider a sequence of positive integers \(a_1, a_2, a_3, \ldots, a_n\) such that the sum of any three consecutive terms is always a prime number. If \(a_1 = 2\), \(a_2 = 3\), and \(a_3 = 5\), find the smallest possible value of \(n\) for which \(a_n = 1\).

Answer: `6`

## 0139 | score=0.444 | number_theory

Find all positive integers \( n \) such that the equation \( \sigma(n) = 2n - 1 \) holds, where \( \sigma(n) \) denotes the sum of the divisors of \( n \). Additionally, prove that for such \( n \), the number of distinct prime factors of \( n \) is at most 2.

Answer: `2`

## 0140 | score=0.667 | geometry

Let $ABC$ be a triangle with $AB = AC$ and $\angle BAC = 20^\circ$. Point $D$ lies on segment $BC$ such that $BD = AC$. Point $E$ lies on segment $AD$ such that $\angle BED = 60^\circ$. Determine the measure of $\angle AEC$.

Answer: `100`

## 0141 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + nx + 1 \) is divisible by \( Q(x) = x^2 - x - 1 \).

Answer: `2`

## 0142 | score=0.333 | algebra

Find all real solutions to the equation \[ \sin(x) \cdot \cos(x) = \frac{1}{4} \sin(2x) \] in the interval \([0, 2\pi]\).

Prove that there exists a unique real number \( a \) such that the equation \[ \sin(a) \cdot \cos(a) = \frac{1}{4} \sin(2a) \] holds true in the interval \([0, 2\pi]\). Also, determine the value of \( a \).

Answer: `\frac{\pi}{2}`

## 0143 | score=0.333 | geometry

A tetrahedron has vertices at the points $(0,0,0)$, $(1,0,0)$, $(0,1,0)$, and $(0,0,1)$. Find the radius of the sphere that is tangent to all four faces of the tetrahedron.

Answer: `\frac{\sqrt{3}}{6}`

## 0144 | score=0.667 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that there exists a sequence \( a_1, a_2, \ldots, a_n \) of distinct positive integers satisfying the following condition: For any \( k \) with \( 1 \leq k \leq n \), the sum of the first \( k \) terms of the sequence, \( a_1 + a_2 + \cdots + a_k \), is divisible by \( k \). Find the smallest \( n \) such that \( S \) contains exactly 10 elements.

Answer: `10`

## 0145 | score=0.667 | number_theory

A sequence of integers \(a_1, a_2, a_3, \ldots, a_n\) is defined as follows: \(a_1 = 1\) and for each \(k \geq 2\), \(a_k\) is the smallest positive integer such that for all \(i < k\), the sum \(a_i + a_k\) is not divisible by 3. Find the smallest value of \(n\) for which \(a_n = 3\).

Answer: `3`

## 0146 | score=0.444 | geometry

Let \(ABC\) be an isosceles triangle with \(AB = AC\). A circle centered at \(C\) with radius \(CA\) intersects the extension of \(AB\) beyond \(A\) at point \(D\). The perpendicular from \(D\) to \(AB\) meets \(AC\) at \(E\). If \(BD = 20\) and \(DE = 10\), find the length of \(BC\).

Answer: `20`

## 0147 | score=0.333 | number_theory

Let $P(x)$ be a polynomial with integer coefficients such that $P(100) = 100$, and for every integer $n$, $P(n)$ divides $n^4 + n^2 + 1$. Find the largest possible value of $P(0)$.

Answer: `100`

## 0148 | score=0.667 | geometry

Let \( ABCD \) be a cyclic quadrilateral with circumradius \( R \) and area \( K \). Suppose that the diagonals \( AC \) and \( BD \) intersect at point \( P \), and let \( M \) and \( N \) be the midpoints of \( AB \) and \( CD \) respectively. If the ratio of the area of triangle \( MPN \) to the area of quadrilateral \( ABCD \) is given by \( \frac{K_{\Delta MPN}}{K} = \frac{1}{8} \), find the length of the diagonal \( AC \) in terms of \( R \).

Answer: `2R`

## 0149 | score=0.556 | number_theory

Find the smallest positive integer \( n \) such that the equation  
\[
\left\lfloor \frac{n}{2} \right\rfloor + \left\lfloor \frac{n}{3} \right\rfloor + \left\lfloor \frac{n}{4} \right\rfloor = 100
\]  
has no solution.

Answer: `94`

## 0150 | score=0.444 | number_theory

In a sequence of numbers, each term is the product of the previous term and an increasing prime number, starting with 2 and ending with the 2023rd prime number. What is the largest prime factor of the 2023rd term in this sequence?

Answer: `p_{2023}`

## 0151 | score=0.778 | algebra

Let \( f: \mathbb{R} \rightarrow \mathbb{R} \) be a function such that for all real numbers \( x \) and \( y \), \( f(x + f(y)) = f(x) + f(y) + 2xy \). If \( f \) is continuous and \( f(0) = 0 \), determine the number of possible values for \( f(1) \).

Then find the function \( f(x) \) that satisfies the given conditions and show that it is unique.

Answer: `1`

## 0152 | score=0.556 | geometry

In the complex plane, consider the polynomial $P(z) = z^6 + 6az^5 + (10a^2 + b)z^4 + (10a^3 + 6ab)z^3 + (10a^4 + 6a^2b + b^2)z^2 + (6a^5 + 5a^3b + a^2b^2)z + a^6$ where $a$ and $b$ are complex numbers. If all the roots of $P(z)$ lie on the unit circle, find the values of $a$ and $b$.

Answer: `0`

## 0153 | score=0.556 | number_theory

Consider a sequence of positive integers \(a_1, a_2, a_3, \ldots\) defined by the recurrence relation \(a_{n+1} = 3a_n + 2\) for \(n \geq 1\), with \(a_1 = 1\). Define a new sequence \(b_n\) as the number of distinct prime factors of \(a_n\). Find the smallest positive integer \(k\) such that \(b_k = 2\) and \(b_{k+1} = 3\).

Answer: `5`

## 0154 | score=0.444 | algebra

Let $f(x)$ be a function defined for all $x \geq 0$ such that $f(0) = 1$ and for all $x \geq 0$, the following holds: \[f'(x) = \frac{1}{x + 1} \cdot f(x)^2.\] If $f(1) = 2$, find the value of $f(2) + \frac{1}{f(2)}$.

Answer: `2`

## 0155 | score=0.667 | geometry

A regular hexagon \( ABCDEF \) has side length \( 1 \). Point \( G \) is the midpoint of side \( AB \), and point \( H \) is the midpoint of side \( CD \). The line segment \( GH \) is extended to intersect the extension of side \( DE \) at point \( I \). Find the length of \( GH \).

Answer: `\frac{3}{2}`

## 0156 | score=0.444 | algebra

Let $P(x)$ be a polynomial of degree 4 such that $P(n) = \frac{1}{n}$ for $n = 1, 2, 3, 4$. Find $P(5)$.

Answer: `\frac{6}{5}`

## 0157 | score=0.556 | number_theory

Let \( S \) be the set of all functions \( f: \mathbb{Z} \to \mathbb{Z} \) such that for any integers \( a, b, c \) with \( a + b + c = 0 \), the equation \( f(a) + f(b) + f(c) = 0 \) holds. Find the number of functions in \( S \).

Answer: `\infty`

## 0158 | score=0.333 | geometry

A circle is inscribed in a square with side length 10 units. A point P is chosen at random inside the square. What is the probability that the distance from P to the closest side of the square is greater than the distance from P to the circle's circumference?

Answer: `1 - \frac{\pi}{4}`

## 0159 | score=0.333 | number_theory

A sequence of positive integers \( a_1, a_2, a_3, \ldots \) is defined by the following properties:

1. \( a_1 = 1 \).
2. For \( n \geq 2 \), \( a_n \) is the smallest positive integer such that \( a_n \) does not divide \( a_1 + a_2 + \cdots + a_{n-1} \).

Let \( S \) be the sum of the first 2024 terms of the sequence. Determine the remainder when \( S \) is divided by 1000.

Answer: `300`

## 0160 | score=0.333 | geometry

Given a circle with radius \( r \) and a point \( P \) inside the circle such that the distance from \( P \) to the center of the circle is \( d \) where \( 0 < d < r \), consider the set of all chords passing through \( P \). Let \( A \) be the area of the region inside the circle that is not covered by any of these chords. Express \( A \) in terms of \( r \) and \( d \).

Answer: `\pi (r^2 - d^2)`

## 0161 | score=0.444 | number_theory

Let $f(x)$ be a polynomial with real coefficients such that $f(0) = 1$ and for every positive integer $n$, the polynomial $f(x^n)$ has exactly $n$ distinct real roots. Prove that there exists a positive integer $m$ such that $f(x) = x^m$.

Answer: `m`

## 0162 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that the equation \( x^2 + y^2 + z^2 = nxyz \) has a solution in positive integers \( x, y, \) and \( z \).

Answer: `3`

## 0163 | score=0.556 | algebra

Determine all continuous functions \( f: \mathbb{R} \to \mathbb{R} \) such that for all real numbers \( x \) and \( y \), the following equation holds:
\[ f(x + y) = f(x) + f(y) - 2f(xy) + 2. \]

Answer: `f(x) = 2`

## 0164 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) has a root that is also a root of its derivative \( P'(x) \).

Answer: `2`

## 0165 | score=0.778 | geometry

What is the smallest positive integer \( n \) such that \( n^3 - 27 \) can be expressed as a sum of two non-negative perfect squares?

Answer: `3`

## 0166 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that \( n^{111} \) has exactly 111 digits in base 10.

Answer: `10`

## 0167 | score=0.444 | geometry

In a mystical forest, there are $n$ distinct magical trees, each producing a unique kind of fruit. The forest spirit has devised a game where participants must collect fruits from these trees. The game has the following rules:
1. Each participant starts with an empty basket.
2. A participant can pick a fruit from any tree in the forest.
3. Once a fruit is picked, the participant cannot pick any fruit from that tree again during the same game.
4. The game ends when a participant has picked a fruit from every tree in the forest.
The forest spirit wants to ensure that no participant feels disadvantaged or favored. To achieve this, the spirit decides that each tree must produce a certain number of fruits, such that the total number of fruits available is a perfect square.
Given that there are $n$ trees, find the smallest possible value of $n$ such that it is possible to distribute the fruits so that the total number of fruits is a perfect square and no participant can feel disadvantaged or favored.

Answer: `2`

## 0168 | score=0.333 | geometry

Let $ABC$ be an acute-angled triangle with circumcircle $\Gamma$. Let $P$ be a point inside $\triangle ABC$ such that $\angle PAB = \angle PBC = \angle PCA$. The line through $P$ parallel to $BC$ intersects $AC$ at $D$, and the line through $P$ parallel to $AC$ intersects $AB$ at $E$. If $AD = 3$, $BD = 4$, and $CE = 5$, find the length of $AE$. Your answer should be in the form of a simplified radical expression.

Answer: `5`

## 0169 | score=0.556 | number_theory

Let $S$ be the set of all positive integers $n$ such that $n$ can be expressed as $n = a^2 + b^2 + c^2 + d^2$ for some positive integers $a, b, c,$ and $d$. Determine the smallest positive integer $k$ such that $k$ is not in $S$, and for every integer $n \geq k$, there exist positive integers $a, b, c,$ and $d$ such that $n = a^2 + b^2 + c^2 + d^2$.

Answer: `7`

## 0170 | score=0.333 | other

设 \(D\) 为曲线 \(r = 1 + \sin(\theta)\) 和 \(r = 1 - \sin(\theta)\) 所围成的区域。计算函数 \(f(r, \theta) = r^2 \cos(\theta)\) 在区域 \(D\) 上的双重积分 \(\iint_D f(r, \theta) \, dA\)。

Answer: `0`

## 0171 | score=0.556 | number_theory

Find all prime numbers \( p \) and \( q \) such that the equation \( p^2 - q^2 + 1 = p + q \) holds. Express your answer in the form of an ordered pair \((p, q)\).

Answer: `(3, 2)`

## 0172 | score=0.778 | number_theory

Let $a$, $b$, and $c$ be positive integers such that $a < b < c$. Define the sequence $(x_n)$ as follows:
$$
x_n = \frac{a^n + b^n + c^n}{a^n + b^n + c^{n+1}}
$$
Prove that there exists a positive integer $N$ such that for all $n \geq N$, $x_n$ is strictly less than $\frac{2}{3}$.

Answer: `N`

## 0173 | score=0.667 | geometry

Find all positive integers $n$ such that the sum of the first $n$ terms of the sequence defined by $a_k = 3^k + 2k$ is a perfect square.

Answer: `1`

## 0174 | score=0.556 | algebra

Let \( f(x) \) be a polynomial of degree 3 such that \( f(1) = 10, f(2) = 20, f(3) = 30, \) and \( f(4) = 40 \). Find the value of \( f(5) \).

Answer: `50`

## 0175 | score=0.444 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + (x+2)^n + 2^n \) has no real roots.

Answer: `2`

## 0176 | score=0.333 | number_theory

Find all integer solutions to the equation \( x^3 + y^3 = z^2 + 2 \), where \( x, y, \) and \( z \) are non-negative integers.

Answer: `(0, 3, 5), (3, 0, 5), (1, 1, 0)`

## 0177 | score=0.444 | geometry

In the complex plane, let $A$, $B$, and $C$ be the points represented by the complex numbers $1$, $1 + i$, and $-i$, respectively. A point $P$ moves around a circle centered at $A$ with radius $1$. For each position of $P$, let $Q$ be the point such that $BQ = 2AQ$ and $\angle PBQ = 90^\circ$. Find the area of the region swept out by $Q$ as $P$ moves around the circle.

Answer: `4\pi`

## 0178 | score=0.444 | number_theory

Consider a sequence of positive integers \( a_1, a_2, a_3, \ldots, a_{100} \) such that for each \( n \) from 1 to 100, \( a_n \) is the smallest integer greater than \( a_{n-1} \) that satisfies the condition that the sum of the digits of \( a_n \) is equal to the sum of the digits of \( n \). Given that \( a_1 = 1 \), find the value of \( a_{100} \).

Answer: `100`

## 0179 | score=0.444 | geometry

A convex quadrilateral \( ABCD \) has sides \( AB = 5 \), \( BC = 7 \), \( CD = 9 \), and \( DA = 11 \). The diagonals \( AC \) and \( BD \) intersect at point \( E \) such that \( AE : EC = 2 : 3 \) and \( BE : ED = 3 : 2 \). Find the area of quadrilateral \( ABCD \).

Answer: `84`

## 0180 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers \( n \) for which there exists a positive integer \( k \) such that the polynomial \( P(x) = x^k + n \) has at least one root in the set of rational numbers. Determine the smallest positive integer \( m \) such that \( S \) contains exactly \( m \) elements.

Answer: `1`

## 0181 | score=0.333 | number_theory

Find all pairs of positive integers $(x, y)$ such that:
\[ x^3 + 2y^3 = 3(x^2 y + y^2 x). \]

Answer: `(1, 1)`

## 0182 | score=0.333 | combinatorics

In the complex plane, consider a regular heptagon \(ABCDEFG\) with vertices at \(1, 2, 3, 4, 5, 6,\) and \(7\), respectively. A particle moves from vertex \(1\) to vertex \(7\) by jumping along the edges of the heptagon in a fixed order. Each jump has a probability of \(\frac{1}{3}\) to continue straight, \(\frac{1}{3}\) to turn right, and \(\frac{1}{3}\) to turn left. What is the probability that after exactly 6 jumps, the particle returns to vertex \(1\)?

Answer: `\frac{20}{729}`

## 0183 | score=0.444 | geometry

Let \( S \) be the set of all integers \( n \) such that \( 100 \leq n \leq 200 \). For each \( n \in S \), consider the polynomial \( P_n(x) = x^2 + nx + 100 \). Find the sum of all distinct values of \( x \) for which \( P_n(x) \) is a perfect square for some \( n \in S \).

Answer: `0`

## 0184 | score=0.778 | number_theory

Let \( f(x) \) be a polynomial with integer coefficients such that \( f(0) = 0 \) and \( f(1) = 1 \). For each positive integer \( n \), let \( S_n \) be the set of all positive integers \( k \) such that \( f(k) \equiv 0 \pmod{n} \). Find the number of distinct prime divisors of \( |S_n| \) when \( n = 2023 \).

Answer: `2`

## 0185 | score=0.333 | number_theory

Consider a polynomial \( P(x) \) with integer coefficients such that \( P(0) = 1 \) and \( P(1) = 3 \). Let \( n \) be the smallest positive integer such that \( P(n) \) is divisible by 1000. Determine the remainder when \( n \) is divided by 1000.

Answer: `500`

## 0186 | score=0.667 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^6 - 4x^3 + 4 \) is divisible by the polynomial \( Q(x) = x^2 + x + 1 \) raised to the power \( n \).

Answer: `2`

## 0187 | score=0.667 | geometry

Find all triples of positive integers \((a, b, c)\) such that \(a^2 + b^2 = c^2\) and \(a^2 + b^2 + c^2\) is divisible by 5. Additionally, prove that there exists at least one such triple where \(a, b,\) and \(c\) form the sides of a right triangle.

Answer: `(3, 4, 5)`

## 0188 | score=0.444 | number_theory

Let \( S \) be the set of all polynomials \( P(x) \) with real coefficients such that \( P(0) = 0 \) and for every integer \( n \geq 1 \), the polynomial \( P(x) \) has \( n \) distinct real roots. Determine the maximum possible number of such polynomials \( P(x) \) of degree \( 2023 \) whose coefficients are integers and whose leading coefficient is \( 1 \).

Answer: `1`

## 0189 | score=0.444 | algebra

Let $a,$ $b,$ $c$ be the roots of the polynomial $x^3 - 3x^2 + 4x - 1 = 0.$ Compute the value of \[
\sum_{cyc} \frac{a^3 + 1}{a^2 + 1}.
\]

Answer: `3`

## 0190 | score=0.444 | number_theory

Find all positive integers \( n \) such that there exist \( n \) distinct positive integers \( a_1, a_2, \ldots, a_n \) satisfying the following conditions:
1. For any two distinct integers \( i \) and \( j \) from \( 1 \) to \( n \), \( a_i \) and \( a_j \) are coprime.
2. For any integer \( k \) from \( 1 \) to \( n \), \( a_1 + a_2 + \cdots + a_n \) is divisible by \( k \).

Answer: `1`

## 0191 | score=0.444 | combinatorics

In how many ways can you arrange \( n \) distinct books on a shelf if exactly \( k \) of them must be placed at the ends of the shelf, where \( 1 \leq k \leq n \)?

Answer: `n!`

## 0192 | score=0.333 | geometry

Let $S$ be the set of all positive integers that can be expressed as the sum of two distinct positive perfect squares. Find the smallest positive integer $n$ such that $n$ is not in $S$ and there exist distinct positive integers $a$ and $b$ such that $n + a^2$ and $n + b^2$ are both in $S$.

Answer: `1`

## 0193 | score=0.778 | number_theory

Find all positive integers $n$ such that the equation
\[x^4 - 4x^3 + 6x^2 - 4x + n = 0\]
has four distinct real roots that form an arithmetic sequence. Prove that there are no other such integers $n$.

Answer: `1`

## 0194 | score=0.556 | number_theory

Let \( f: \mathbb{R} \to \mathbb{R} \) be a continuous function such that for every positive integer \( n \), the function \( f^n(x) = f(f(\ldots f(x) \ldots)) \) (composed \( n \) times) has exactly \( n \) distinct fixed points in the interval \( [0, 1] \). If \( f(0) = 0 \) and \( f(1) = 1 \), prove that there exists a positive integer \( m \) such that \( f^m(x) = x \) for all \( x \in [0, 1] \).

Answer: `m`

## 0195 | score=0.778 | number_theory

Consider a set of integers from 1 to 100. A subset is chosen such that no two elements differ by exactly 3 or 7. What is the maximum number of elements in such a subset?

Answer: `50`

## 0196 | score=0.556 | number_theory

Find the smallest positive integer \( n \) such that \( 2^n - 1 \) is divisible by both \( 2015 \) and \( 2017 \).

Answer: `10080`

## 0197 | score=0.556 | number_theory

Let \( f(x) \) be a polynomial with integer coefficients such that \( f(1) = 3 \) and \( f(3) = 7 \). If \( f(x) \) has a root at \( x = 2 \), find the smallest possible positive value of \( f(5) \).

Answer: `51`

## 0198 | score=0.333 | geometry

Let \( ABC \) be a triangle with \( AB = AC \). Let \( D \) be a point on \( BC \) such that \( BD = 2 \) and \( DC = 1 \). Let \( E \) be a point on \( AD \) such that \( AE = 3 \). If \( BE = \sqrt{13} \), find the area of \( \triangle ABC \).

Answer: `6`

## 0199 | score=0.667 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a function that is continuous on \(\mathbb{R}\) and satisfies the condition:
\[ f(x + y) = f(x)f(y) - f(x) + f(y) - xy \]
for all real numbers \( x \) and \( y \). Prove that \( f(x) = 1 + x \) for all \( x \in \mathbb{R} \).

Answer: `f(x) = 1 + x`

## 0200 | score=0.444 | number_theory

Find all positive integers \( n \) for which there exists a positive integer \( k \) such that both \( n \) and \( n^2 + k \) are powers of 2 and \( k \) is a prime number.

Answer: `1`

## 0201 | score=0.556 | number_theory

Find all triples of positive integers \((a, b, c)\) such that
\[ a^2 + b^2 + c^2 = 3abc + 1. \]

Answer: `(1, 1, 1)`

## 0202 | score=0.667 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a function that satisfies the following properties:
1. \( f(x + y) = f(x) + f(y) \) for all \( x, y \in \mathbb{R} \).
2. \( f(1) = 2 \).
3. \( f(x^2) = f(x)^2 \) for all \( x \in \mathbb{R} \).

Find all possible values of \( f(5) \).

Answer: `10`

## 0203 | score=0.556 | number_theory

Let $S$ be the set of all positive integers $n$ for which there exists a positive integer $k$ such that the product of all positive integers from $1$ to $n$ (denoted as $n!$) is divisible by $2^k$. Find the remainder when the sum of all elements in $S$ that are less than $1000$ is divided by $1000$.

Answer: `499`

## 0204 | score=0.333 | number_theory

Consider a sequence of positive integers \(a_1, a_2, \ldots, a_n\) where each \(a_i\) is distinct and satisfies the condition \(a_i \leq i\). Define the function \(f(n)\) as the number of such sequences. Find the value of \(f(20)\).

Answer: `20!`

## 0205 | score=0.333 | geometry

In the coordinate plane, consider the region defined by the inequalities $0 \leq x \leq 1$, $0 \leq y \leq 1$, and $x + y \geq 0.5$. Let $S$ be the set of all points $(x, y)$ in this region such that $x$ and $y$ are both rational numbers and $x^2 + y^2$ is also a rational number. Determine the number of elements in $S$ that have a rational square root.

Answer: `2`

## 0206 | score=0.444 | geometry

Let \( P \) be a point inside an equilateral triangle \( ABC \) with side length \( 6 \). The distances from \( P \) to the sides \( BC, CA, \) and \( AB \) are \( d_1, d_2, \) and \( d_3 \) respectively. If \( d_1 + d_2 + d_3 = 6 \), find the maximum possible value of the sum of the squares of these distances, i.e., find the maximum value of \( d_1^2 + d_2^2 + d_3^2 \).

Answer: `36`

## 0207 | score=0.667 | number_theory

A sequence of positive integers \((a_n)\) is defined recursively by \(a_1 = 1\), \(a_2 = 2\), and \(a_{n+2} = a_{n+1} + a_n\) for all \(n \geq 1\). For a positive integer \(k\), let \(S_k\) be the set of all \(n\) such that \(a_n\) is divisible by \(k\). Determine the smallest positive integer \(k > 1\) such that \(|S_k| = 2023\).

Answer: `2023`

## 0208 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^4 - nx^3 + (n+1)x^2 - nx + 1 \) has all its roots as real numbers.

Answer: `5`

## 0209 | score=0.333 | number_theory

In the complex plane, let \( z \) be a complex number such that \( |z| = 1 \) and \( \arg(z) = \theta \). Define a sequence \( \{z_n\} \) by \( z_1 = z \) and \( z_{n+1} = z_n^2 + i \) for \( n \geq 1 \). Find the smallest positive integer \( k \) such that \( z_k = z_1 \).

Answer: `4`

## 0210 | score=0.333 | geometry

Let $ABC$ be a triangle with $AB = 13$, $BC = 14$, and $CA = 15$. Let $D$ be the foot of the altitude from $A$ to $BC$, and let $E$ be the midpoint of $AD$. If $P$ is a point on segment $BC$ such that $BP:PC = 3:2$, find the length of $EP$.

Answer: `\frac{\sqrt{1189}}{5}`

## 0211 | score=0.778 | combinatorics

In a magical forest, there are 1000 unique trees. Each tree has a number of fruits ranging from 1 to 1000, with no two trees having the same number of fruits. A group of 10 elves wants to select a subset of these trees such that no tree in the subset has twice as many fruits as another tree in the subset. What is the maximum number of trees they can select?

Answer: `500`

## 0212 | score=0.333 | geometry

Let \( f(n) \) be a function defined on the positive integers such that \( f(1) = 1 \) and for all positive integers \( n \),
\[ f(n+1) = f(n) + \left\lfloor \sqrt{f(n)} \right\rfloor. \]
Find the smallest positive integer \( n \) for which \( f(n) \) is a perfect square greater than 1.

Answer: `4`

## 0213 | score=0.444 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) is divisible by \( Q(x) = x^5 + 1 \).

Answer: `5`

## 0214 | score=0.333 | geometry

A sequence of integers $a_1, a_2, a_3, \dots$ is defined by $a_1 = 1$ and for $n \geq 1$, $a_{n+1}$ is the smallest positive integer such that $a_{n+1} > a_n$ and the sum $a_{n+1} + a_n$ is a perfect square. Find the value of $a_{2023}$.

Answer: `2047276`

## 0215 | score=0.667 | geometry

In a small town, there are 10 houses arranged in a circle. Each house is painted either blue or green. It is known that no two adjacent houses are painted the same color. How many different ways can the houses be painted such that the first and the tenth house are also painted the same color?

Answer: `2`

## 0216 | score=0.556 | number_theory

A sequence of positive integers \(a_1, a_2, a_3, \ldots, a_{10}\) is defined such that for all \(i\) from 1 to 9, \(a_{i+1}\) is the smallest positive integer greater than \(a_i\) that is coprime with \(a_i\). Given that \(a_1 = 2\) and \(a_{10} = 50\), find the value of \(a_4\).

Answer: `5`

## 0217 | score=0.667 | geometry

Let \( ABCD \) be a cyclic quadrilateral with \( AB = 3 \), \( BC = 4 \), \( CD = 5 \), and \( DA = 6 \). Let \( E \) be a point on the arc \( BC \) of the circumcircle of \( ABCD \) that does not contain \( A \). Given that \( AE = 7 \), find the length of \( DE \).

Answer: `8`

## 0218 | score=0.667 | number_theory

Find the smallest positive integer \( n \) such that for any \( n \)-element subset \( A \) of the set \(\{1, 2, \ldots, 2n-1\}\), there exist two distinct elements \( a, b \in A \) with \( a + b = 2n \).

Answer: `3`

## 0219 | score=0.667 | geometry

Find all real numbers \(x\) such that the series
\[
\sum_{n=1}^{\infty} \frac{x^n}{n! + n^k}
\]
converges for any fixed positive integer \(k\). Determine the convergence radius of the series and identify any exceptional points.

Answer: `\infty`

## 0220 | score=0.556 | number_theory

Find all prime numbers \( p \) and \( q \) such that \( p \) divides \( q^2 + 4 \) and \( q \) divides \( p^2 + 4 \).

Answer: `(2, 2)`

## 0221 | score=0.556 | geometry

There exists a positive integer $n$ such that there are $n$ distinct integers $a_1, a_2, \ldots, a_n$ satisfying the following conditions:

1. Each $a_i$ is between 1 and 1000 inclusive.
2. For each pair $(i, j)$ with $1 \leq i < j \leq n$, the sum $a_i + a_j$ is not a perfect square.
3. The set $\{a_i + a_j : 1 \leq i < j \leq n\}$ has exactly 2009 elements.

Find the maximum possible value of $n$.

Answer: `64`

## 0222 | score=0.444 | number_theory

Let $f(x) = x^3 - 3x + 1$. Define the sequence $a_n = f(n)$ for $n \in \mathbb{Z}^+$, where $\mathbb{Z}^+$ denotes the set of positive integers. If $S$ is the set of all possible values of $k$ for which the equation $a_n = k$ has at least one solution, find the sum of all elements in $S$.

Determine the value of $k$ for which $a_n = k$ has exactly three solutions, $n_1, n_2,$ and $n_3$, where $n_1 < n_2 < n_3$. Then, find the value of $a_{n_1} + a_{n_2} + a_{n_3}$.

Answer: `3`

## 0223 | score=0.333 | geometry

A square grid of side length 100 is divided into 10000 smaller squares of side length 1. Starting from any square, you can move to any adjacent square (sharing a side). How many distinct paths can you take from the bottom-left corner to the top-right corner, visiting each square at most once, and not crossing any diagonal line drawn from the bottom-left corner to the top-right corner?

Answer: `\frac{1}{101} \binom{200}{100}`

## 0224 | score=0.778 | geometry

Let \( \mathbf{v}_1, \mathbf{v}_2, \mathbf{v}_3 \) be vectors in a four-dimensional vector space \( V \) over the field of real numbers, such that \( \mathbf{v}_1 \) is orthogonal to \( \mathbf{v}_2 \), and \( \mathbf{v}_2 \) is orthogonal to \( \mathbf{v}_3 \). If the norm of \( \mathbf{v}_1 \) is 2, the norm of \( \mathbf{v}_2 \) is 3, and the norm of \( \mathbf{v}_3 \) is 4, find the maximum possible value of \( \langle \mathbf{v}_1, \mathbf{v}_3 \rangle \).

Answer: `8`

## 0225 | score=0.556 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(0) = 1 \) and \( P(1) = 3 \). Suppose that for every prime \( p \), the number of distinct prime factors of \( P(p) \) is equal to the number of distinct prime factors of \( P(p+1) \). Determine all possible values of \( P(10) \).

Answer: `21`

## 0226 | score=0.778 | geometry

Find all positive integers \( n \) such that the sum of the squares of the first \( n \) positive integers is divisible by \( n^2 + 1 \).

Answer: `2`

## 0227 | score=0.444 | geometry

In the coordinate plane, let \( A = (0, 0) \) and \( B = (10, 0) \). A point \( P \) moves such that its distance to line \( AB \) is always twice its distance to the y-axis. Find the area enclosed by the path traced by \( P \) and the line segments \( PA \) and \( PB \).

Answer: `100`

## 0228 | score=0.667 | geometry

In the complex plane, consider the equation \( z^4 + 16 = 0 \). Let \( z_1, z_2, z_3, z_4 \) be the four roots of this equation. If a regular polygon is formed by connecting these roots in the order \( z_1, z_2, z_3, z_4 \), what is the area of this polygon?

Answer: `8`

## 0229 | score=0.444 | number_theory

Find all positive integers \( n \) such that the equation
\[ \sum_{k=0}^{n-1} \left( \binom{n}{k} \cdot k! \cdot (n-k)! \right) = 3^n \]
holds true. Justify your answer rigorously.

Answer: `1`

## 0230 | score=0.444 | number_theory

Let \( f: \mathbb{Z}^+ \to \mathbb{Z}^+ \) be a function defined by \( f(n) = n^2 + n + 1 \). Find all positive integers \( m \) such that \( f(m) \) divides \( f(f(m)) \).

Answer: `1`

## 0231 | score=0.667 | number_theory

Find all positive integers \( n \) such that \( n \) divides \( \lfloor n/2 \rfloor + 1 \).

Answer: `1, 2`

## 0232 | score=0.667 | number_theory

Let \( f: \mathbb{Z} \rightarrow \mathbb{Z} \) be a function satisfying the following conditions:
1. \( f(f(n)) = n + 2 \) for all integers \( n \),
2. \( f(n + 2) = f(n) + 2 \) for all integers \( n \),
3. \( f(0) = 0 \).

Find all possible values of \( f(10) \).

Answer: `10`

## 0233 | score=0.333 | combinatorics

In a mystical land, there are 5 distinct magical trees, each bearing a unique fruit: apple, banana, cherry, date, and elderberry. A wizard must pick exactly 4 trees each day to prepare a powerful potion. However, the wizard has a peculiar requirement: he cannot pick more than 2 trees of the same type in any given day. How many different ways can the wizard select the trees to prepare his potion?

Answer: `30`

## 0234 | score=0.667 | number_theory

Find the smallest positive integer \( n \) such that \( n^{2024} - 1 \) is divisible by \( 2024! \).

Answer: `1`

## 0235 | score=0.556 | number_theory

Let \( S \) be the set of all integers \( n \) such that \( 1 \leq n \leq 2023 \), and \( n \) is not divisible by \( 3 \) or \( 5 \). For each \( n \in S \), define \( f(n) \) to be the smallest positive integer \( k \) such that the sequence \( n, n + k, n + 2k, n + 3k, \ldots \) contains a term that is divisible by both \( 3 \) and \( 5 \). Find the sum of all \( f(n) \) for \( n \in S \).

Answer: `16185`

## 0236 | score=0.667 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a function such that for all real numbers \( x \) and \( y \), the equation \( f(x + y) + f(x - y) = 2f(x) + 2f(y) \) holds. Prove that there exists a real number \( c \) such that \( f(x) = cx^2 \) for all \( x \).

Answer: `f(x) = cx^2`

## 0237 | score=0.667 | number_theory

Find the smallest positive integer \( n \) such that \( n! \) (n factorial) has exactly 12 trailing zeros in its decimal representation. Additionally, determine if \( n \) is a prime number or not.

Answer: `50`

## 0238 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that \( n \) can be expressed as \( n = a^2 + b^2 + c^2 \) where \( a, b, c \) are positive integers satisfying \( a + b + c = n - 3 \). Determine the number of distinct primes \( p \) that divide at least one element of \( S \). Prove your answer.

Answer: `2`

## 0239 | score=0.333 | number_theory

A sequence of positive integers \(a_1, a_2, a_3, \ldots\) is defined by \(a_1 = 1\) and \(a_{n+1} = a_n^2 - 2\) for \(n \geq 1\). Find the smallest positive integer \(k\) such that \(a_k\) is divisible by 1000.

Answer: `1`

## 0240 | score=0.333 | geometry

In the coordinate plane, let  $P_1^{}=(-1,1), P_2=(1,1), P_3=(-2,-1),$  and  $P_4=(2,-1),$  and for  $n\geq 5,$  let  $P_n=(n, |P_{n-2} P_{n-1}|).$  Can you determine the area of the region enclosed by  $\mathcal{R}_1,$  formed by the points  $P_n$  (expressed in terms of  $n$ )?

Answer: `2`

## 0241 | score=0.333 | algebra

Find all functions \( f: \mathbb{R} \to \mathbb{R} \) such that for all real numbers \( x \) and \( y \),
\[ f(x^3) - f(y^3) = (x^2 + xy + y^2)(f(x) - f(y)). \]

Answer: `f(x) = cx`

## 0242 | score=0.556 | geometry

In triangle \(ABC\), let \(D\) and \(E\) be points on sides \(AB\) and \(AC\) respectively such that \(DE\) is parallel to \(BC\). Suppose \(AD = 3\), \(DB = 2\), and \(AE = 4\). If the area of triangle \(ADE\) is 12, find the area of triangle \(ABC\).

What is the area of triangle \(ABC\)?

Answer: `\frac{100}{3}`

## 0243 | score=0.333 | geometry

Let $p$ be a prime number such that $p \equiv 1 \pmod{4}$. Prove that the product of the quadratic non-residues modulo $p$ is a perfect square. Moreover, show that there exists an integer $k$ such that $k^2 \equiv 2 \pmod{p}$ if and only if $p \equiv 1 \pmod{4}$.

Answer: `1`

## 0244 | score=0.333 | other

在一个边长为1的正方形内部随机选择一个点P，求使得以P为圆心，以P到正方形四边中点距离的最大值为半径的圆完全覆盖该正方形的概率。

Answer: `0`

## 0245 | score=0.778 | geometry

In the complex plane, let \( z \) be a complex number such that \( z \neq 0 \) and \( z^4 = \overline{z} \). How many distinct solutions are there to this equation, and what is the product of all such solutions?

Answer: `1`

## 0246 | score=0.444 | number_theory

Let \( S \) be a set of positive integers such that no element divides any other element of \( S \). Suppose that \( S \) has exactly 2021 elements. Prove that the sum of the reciprocals of all elements in \( S \) is strictly less than 2.

Answer: `2`

## 0247 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers that can be expressed as the sum of exactly two positive integer cubes, i.e., \( S = \{a^3 + b^3 \mid a, b \in \mathbb{N} \} \). Prove that there exists a positive integer \( n \) such that \( n \) and \( n+1 \) are both elements of \( S \). Furthermore, find the smallest such \( n \).

Answer: `1729`

## 0248 | score=0.333 | number_theory

Let $S$ be the set of all positive integers $n$ such that $n$ can be expressed as the sum of distinct powers of 3. For example, $10 = 3^2 + 3^0$ is in $S$. Find the number of elements in $S$ that are less than 1000 and can also be expressed as the sum of distinct powers of 2.

Answer: `10`

## 0249 | score=0.667 | number_theory

There exists a magical land where each person has a unique power, represented by a positive integer. On a special day, every person casts a spell that doubles the power of every person who lives in the same village as them. The villagers are not only power-laden but also organized, with each village containing exactly three inhabitants, and no two villages have the same combination of powers among their inhabitants. If the total power of the villagers in each village equals 12 after the day's spells, find the maximum possible power of a single individual in the land.

Answer: `4`

## 0250 | score=0.556 | number_theory

Let \( f(n) \) be a function defined for all positive integers \( n \) such that \( f(n) \) is the smallest positive integer \( k \) for which the sum of the digits of \( k! \) (k factorial) is divisible by \( n \). Find \( f(2023) \).

Answer: `2023`

## 0251 | score=0.333 | number_theory

Let $S$ be the set of all positive integers $n$ such that $n^2 + 1$ is divisible by $n + 1$ and $n - 1$. Find the sum of all elements in $S$ that are less than 1000.

Hint: Consider the polynomial division and the properties of the divisors.

Answer: `3`

## 0252 | score=0.556 | geometry

In the complex plane, the vertices of an equilateral triangle are represented by the complex numbers \( z_1, z_2, \) and \( z_3 \). If the centroid of the triangle is \( G \), and the center of mass \( M \) of three particles located at \( z_1, z_2, \) and \( z_3 \) is given by \( M = \frac{z_1 + 2z_2 + z_3}{4} \), find the ratio of the distance from \( M \) to the origin to the distance from \( G \) to the origin.

Answer: `\frac{3}{4}`

## 0253 | score=0.333 | number_theory

Read the following question on the Helicopter door gun camera question and provide an answer in 150 words. ```<question>
Let \( P(x) \) be a monic polynomial of degree 4 with integer coefficients such that \( P(1) = 17 \) and \( P(2) = 34 \). Find the number of possible values for \( P(0) \) given that \( P(x) \) has two distinct integer roots.

Answer: `2`

## 0254 | score=0.444 | number_theory

Find all integers $n \geq 3$ such that the product of the first $n$ positive integers (i.e., $n!$) is divisible by the sum of the first $n$ positive integers (i.e., $1 + 2 + \dots + n$).

Answer: `n \geq 3`

## 0255 | score=0.667 | geometry

Let \( p \) be a prime number and \( n \) be a positive integer such that \( p \) divides \( n^2 + 1 \). Define \( m = \frac{n^2 + 1}{p} \). Find the smallest prime \( p \) for which \( m \) is a perfect square and \( n \) is also a prime number.

Answer: `5`

## 0256 | score=0.556 | algebra

Let $f(x)$ be a continuous function defined on the interval $[0, 1]$ such that for all $x \in [0, 1]$ and all $n \in \mathbb{N}$, $f(x) \leq n \cdot x^n$. Furthermore, suppose there exists a sequence $\{a_n\}_{n=1}^{\infty}$ of positive real numbers such that $\sum_{n=1}^{\infty} a_n$ converges and for all $n \in \mathbb{N}$, $f\left(\frac{1}{n}\right) \geq a_n$. Prove that $\lim_{x \to 0^+} \frac{f(x)}{x} = 0$.

Answer: `0`

## 0257 | score=0.667 | algebra

Let \( f(x) \) be a function defined for all real numbers \( x \) such that \( f(x) + f(1-x) = 1 \) and \( f(x) - f(1-x) = x. \) Find \( f\left(\frac{1}{2}\right). \)

Answer: `\frac{3}{4}`

## 0258 | score=0.667 | number_theory

Find the number of ordered pairs of integers \((x, y)\) such that \(x^2 - 5xy + 6y^2 = x - y + 1\).

Answer: `1`

## 0259 | score=0.333 | number_theory

Find all positive integers \( n \) such that the sum of the digits of \( n \) in base 10, when added to the sum of the digits of \( n^2 \) in base 10, equals \( n \). Provide your answer in ascending order, separated by commas.

Answer: `0`

## 0260 | score=0.444 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) is divisible by \( Q(x) = x^2 - 3x + 2 \).

Answer: `3`

## 0261 | score=0.778 | geometry

Let \( ABC \) be an isosceles triangle with \( AB = AC \) and \(\angle BAC = 20^\circ\). Point \( D \) is on \( AB \) such that \( \angle BCD = 70^\circ \), and point \( E \) is on \( AC \) such that \( \angle CBE = 60^\circ \). Determine the measure of \( \angle BED \).

Answer: `30^\circ`

## 0262 | score=0.667 | number_theory

Find all positive integers \( n \) such that the equation \( x^2 + y^2 + z^2 = nxyz \) has infinitely many solutions in positive integers \( x, y, \) and \( z \).

Answer: `3`

## 0263 | score=0.444 | number_theory

Let \( f: \mathbb{Z} \to \mathbb{Z} \) be a function satisfying the following conditions:
1. \( f(1) = 1 \)
2. For all integers \( x \) and \( y \), \( f(xy) = f(x)f(y) - xy \).

Find the value of \( f(100) \).

Answer: `-100`

## 0264 | score=0.444 | number_theory

Find all positive integers \( n \) for which the number \( 2^{n-1} - 1 \) is divisible by \( n \).

Answer: `1, 3`

## 0265 | score=0.778 | algebra

Let $f(x)$ be a polynomial of degree 5 such that $f(1) = 1$, $f(2) = 2$, $f(3) = 3$, $f(4) = 4$, $f(5) = 5$, and $f(6) = 6$. Determine the value of $f(7)$.

Answer: `7`

## 0266 | score=0.444 | number_theory

Let \( n \) be a positive integer. A sequence of \( n \) positive integers \( a_1, a_2, \ldots, a_n \) is called "super-balanced" if for every positive integer \( k \) with \( 1 \leq k \leq n \), the sum of the first \( k \) terms of the sequence is divisible by \( k \) and also by \( k^2 \). Find the number of super-balanced sequences \( (a_1, a_2, \ldots, a_n) \) such that each \( a_i \) is an integer between 1 and 100 inclusive.

Answer: `1`

## 0267 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + ax^{n-1} + bx^{n-2} + \ldots + cx + d \) with integer coefficients \( a, b, c, \ldots, d \) has the property that for any prime \( p \), the polynomial \( P(x) \) modulo \( p \) has a root in the field \( \mathbb{Z}/p\mathbb{Z} \).

Answer: `1`

## 0268 | score=0.333 | geometry

Let \( ABCD \) be a convex quadrilateral with \( AB = 7 \), \( BC = 11 \), \( CD = 10 \), and \( DA = 8 \). Suppose that the diagonals \( AC \) and \( BD \) intersect at point \( P \) such that \( \angle APB = \angle CPD = 90^\circ \). Find the length of the segment \( AC \).

Express your answer in the form \( \sqrt{m} \), where \( m \) is an integer.

Answer: `\sqrt{149}`

## 0269 | score=0.333 | number_theory

Let $p(x) = x^4 + ax^3 + bx^2 + cx + d$ be a polynomial with integer coefficients such that $p(1) = 17$, $p(2) = 34$, $p(3) = 51$, and $p(4) = 68$. If $r$ is the remainder when $p(10)$ is divided by $1000$, determine the value of $r$.

Answer: `194`

## 0270 | score=0.444 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a continuous function such that \( f(x) + f(-x) = 2 \) for all \( x \in \mathbb{R} \), and \( f \) satisfies the functional equation \( f(x+y) = f(x) + f(y) - xy \) for all \( x, y \in \mathbb{R} \). Find the value of \( f(2024) \).

Answer: `2025`

## 0271 | score=0.667 | number_theory

Find the smallest positive integer \( n \) such that there exist integers \( a \), \( b \), and \( c \) satisfying the equation \( a^2 + b^2 + c^2 + n = abc \), and \( a \), \( b \), and \( c \) are all prime numbers.

Answer: `2`

## 0272 | score=0.444 | number_theory

Let \( S \) be the set of all non-empty subsets of \(\{1, 2, \ldots, n\}\). For each subset \( A \in S \), define \( f(A) \) as the number of elements in \( A \) that are relatively prime to the product of all elements in \( A \). Determine the sum of \( f(A) \) over all subsets \( A \) of \(\{1, 2, \ldots, n\}\).

Answer: `n \cdot 2^{n-1}`

## 0273 | score=0.778 | number_theory

In the mystical town of Numerica, there's a peculiar clock that chimes not once per hour but follows a unique pattern every hour. This pattern is determined by the function f(n) = 3n^2 - 5n + 2, where n is the hour of the day (0 to 23). The number of times the clock chimes is equal to the value of this function. If the town decides to introduce a new rule: the clock only chimes if f(n) is a prime number, how many times will the clock have chimed after 24 hours, starting at hour 0? Assume the clock starts chiming immediately at hour 0.

Answer: `1`

## 0274 | score=0.444 | geometry

A square grid of size \( n \times n \) is colored such that each cell is either red or blue. A move consists of selecting a row or a column and flipping the color of all cells in that row or column (i.e., changing red to blue and blue to red). The goal is to transform the grid into a checkerboard pattern using the minimum number of moves. For which values of \( n \) can this be achieved with exactly 4 moves, and what is the smallest value of \( n \) for which this is possible?

Answer: `4`

## 0275 | score=0.333 | number_theory

Find all positive integers \( n \) for which the equation
\[ x^2 + (n + 1)x + n = 0 \]
has integer roots, and the sum of the absolute values of these roots is divisible by 3.

Answer: `2, 5, 8, 11, \ldots`

## 0276 | score=0.444 | number_theory

Find all positive integers \( n \) such that there exists a permutation \( \sigma \) of the set \( \{1, 2, \dots, n\} \) satisfying the condition:
\[ \sigma(1) + \sigma(2) = 2023, \]
and for all \( i = 3, 4, \dots, n-1 \), the sum \( \sigma(i) + \sigma(i+1) \) is a prime number. Determine the number of such positive integers \( n \).

Answer: `1`

## 0277 | score=0.556 | geometry

In the complex plane, consider the set of points \(z\) such that the distance from \(z\) to the point \(1 + 2i\) is equal to the distance from \(z\) to the point \(-1 - i\). This set forms a straight line. Find the value of the product of the real and imaginary parts of the point on this line that is closest to the origin.

Answer: `\frac{27}{338}`

## 0278 | score=0.556 | number_theory

Let \( S \) be a set of 2023 distinct positive integers. Suppose that for every pair of distinct elements \( a, b \in S \), there exists a positive integer \( c \) such that \( a \mid bc \) and \( b \mid ac \). Find the minimum possible value of the largest element in \( S \).

Answer: `2^{2022}`

## 0279 | score=0.667 | number_theory

What is the smallest positive integer \( n \) such that \( n! \) has at least 100 trailing zeroes, and \( n \) itself is a prime number?

Answer: `409`

## 0280 | score=0.556 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + ax^{n-1} + bx^{n-2} + \ldots + c \) with integer coefficients satisfies \( P(1) = 100 \) and \( P(-1) = -98 \).

Answer: `2`

## 0281 | score=0.333 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(1) = 2 \) and \( P(2) = 5 \). If \( P(x) \) has degree 3, find the minimum possible value of \( P(3) \).

Answer: `10`

## 0282 | score=0.778 | number_theory

A sequence of numbers starts with \(a_1 = 1\). Each subsequent number \(a_{n+1}\) is the smallest integer greater than \(a_n\) such that for every pair of distinct primes \(p\) and \(q\) (where \(p < q\)), \(a_{n+1}\) is not the sum of any two previous terms \(a_i\) and \(a_j\) (with \(i, j \leq n\)) that satisfy \(p|a_i\) and \(q|a_j\). Find the 10th term of this sequence, \(a_{10}\).

Answer: `10`

## 0283 | score=0.444 | geometry

In the coordinate plane, consider a set of points \(P\) such that for any three points \((x_1, y_1), (x_2, y_2), (x_3, y_3) \in P\), the equation \[ \left| x_1^2 + y_1^2 - (x_2^2 + y_2^2) \right| + \left| x_1 + y_1 - (x_2 + y_2) \right| = \left| x_1^2 + y_1^2 - (x_3^2 + y_3^2) \right| + \left| x_1 + y_1 - (x_3 + y_3) \right| \] holds. If \((1,0), (0,1),\) and \((-1,0)\) are elements of \(P\), how many additional integer points \((x, y)\) with \(-10 \leq x, y \leq 10\) can be added to \(P\) without violating the given property?

Answer: `0`

## 0284 | score=0.444 | geometry

In a convex quadrilateral \(ABCD\), diagonals \(AC\) and \(BD\) intersect at point \(O\). Let \(M\) and \(N\) be the midpoints of sides \(AD\) and \(BC\) respectively. Suppose that the line segment \(MN\) intersects diagonal \(AC\) at point \(P\) such that \(AP:PC = 2:3\). If the area of triangle \(AMN\) is 18 square units, find the area of quadrilateral \(ABCD\).

Answer: `72`

## 0285 | score=0.556 | algebra

Let \( f: \mathbb{N} \to \mathbb{N} \) be a function defined by \( f(n) = n^2 + n + 1 \). Suppose that for every \( k \in \mathbb{N} \), there exists an \( m \in \mathbb{N} \) such that \( f(m) \) divides \( k! \). Find the smallest possible value of \( k \) for which this condition holds.

Answer: `3`

## 0286 | score=0.556 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a function such that for all real numbers \( x \) and \( y \), the equation \( f(x + f(y)) = f(x) + 2x f(y) + y^2 f(x) \) holds. Prove that there exists a constant \( k \) such that \( f(x) = kx^2 \) for all real numbers \( x \).

Answer: `f(x) = kx^2`

## 0287 | score=0.778 | geometry

Find all pairs of positive integers $(x, y)$ such that $x^2 + 3y$ and $y^2 + 3x$ are both perfect squares.

Answer: `(1, 1)`

## 0288 | score=0.333 | algebra

设\( p(x) = x^3 - 3ax^2 + bx + c \)是一个三次多项式，其中\( a, b, c \)为实数。已知\( p(x) \)在\( x = 1 \)处有一个极小值，并且当\( x \)趋向于正无穷大时，\( p(x) \)也趋向于正无穷大。如果\( p(x) \)的三个根（可能相同）分别是\( r_1, r_2, r_3 \)，且满足\( r_1 + r_2 + r_3 = 3a \)，\( r_1r_2 + r_2r_3 + r_3r_1 = b \)，\( r_1r_2r_3 = -c \)。问：是否存在这样的\( a, b, c \)使得\( p(x) \)在\( x = 0 \)处也有一个极小值？如果存在，给出一个满足条件的\( a, b, c \)的值；如果不存在，请给出理由。

Answer: `a = \frac{1}{2}, b = 0, c = 0`

## 0289 | score=0.333 | other

设 \( f(n) \) 是一个定义在正整数上的函数，满足以下条件：
对于任意的正整数 \( n \)，\( f(n+1) \) 等于 \( f(n) \) 的最小质因数与 \( n \) 本身之和。
已知 \( f(1) = 2 \)，求 \( f(2023) \) 的值。

Answer: `2023`

## 0290 | score=0.333 | number_theory

Let \( f: \mathbb{Z} \to \mathbb{Z} \) be a function such that for all integers \( x \) and \( y \),
\[ f(x + y) + f(xy) = f(x)f(y) + f(x + yxy). \]
Prove that there exists a function \( g: \mathbb{Z} \to \mathbb{Z} \) such that \( f(x) = g(x^2) \) for all integers \( x \).

Answer: `g(x) = 1`

## 0291 | score=0.444 | number_theory

Given a set of positive integers \( S = \{1, 2, 3, \ldots, n\} \), define a function \( f(S) \) as follows: for each pair of distinct elements \( a \) and \( b \) in \( S \), calculate \( \gcd(a, b) \), and then sum these gcd values. Let \( g(n) \) be the number of different values that \( f(S) \) can take as \( S \) varies over all subsets of \( \{1, 2, 3, \ldots, n\} \). Find \( g(10) \).

Answer: `10`

## 0292 | score=0.778 | number_theory

Let $S$ be the set of all positive integers $n$ such that $\sqrt[3]{n} + \sqrt[3]{n+1}$ is rational. How many elements of $S$ are there such that $1 \leq n \leq 1000$?

Answer: `0`

## 0293 | score=0.778 | number_theory

Let \( f: \mathbb{N} \rightarrow \mathbb{N} \) be a function such that for every positive integer \( n \),
\[ f(n+1) > f(f(n)) \]
and \( f(n+2) > f(n+1) \). If \( f(1) = 1 \), determine the smallest possible value of \( f(100) \).

Answer: `100`

## 0294 | score=0.667 | number_theory

In a non-standard arithmetic operation, let 'star' denote the operation A★B = 3A - 2B for any two integers A and B. Given that X★(Y★Z) = 17 and Y★Z = 7, find the value of X★Y★Z.

Answer: `17`

## 0295 | score=0.333 | number_theory

Let $f(n)$ be a function that returns the smallest positive integer $k$ such that the product of the first $k$ positive integers (i.e., $k!$) is divisible by $n$. For example, $f(10) = 5$ since $5! = 120$ is the smallest factorial divisible by $10$. Find the sum of all positive integers $n$ less than $1000$ such that $f(n) = n$.

Answer: `76127`

## 0296 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that there exists a set of \( n \) integers, no two of which have a difference that is a power of 2. Prove your answer.

Answer: `3`

## 0297 | score=0.667 | geometry

Find the smallest positive integer \( n \) such that the sum of the squares of its digits is equal to \( n \), and also the product of its digits minus 1 is a perfect square.

Answer: `1`

## 0298 | score=0.333 | geometry

In the coordinate plane, let $P$ be a point chosen uniformly at random from the interior of a unit square centered at the origin with vertices $(1,0), (0,1), (-1,0), (0,-1)$. Let $D$ be the set of points within a distance of $\frac{1}{2}$ of $P$. Compute the expected area of the intersection of $D$ with the boundary of the square.

Answer: `1`

## 0299 | score=0.333 | number_theory

Find all positive integers \( n \) such that \( n \) divides \( 2^n - 2 \), and prove that there exists a unique prime \( p \) for which \( p^2 \) divides \( 2^p - 2 \), but \( p \) does not divide \( 2^{p-1} - 1 \). Determine the value of \( p \) and show that no other primes \( q \neq p \) satisfy these conditions.

Answer: `1093`

## 0300 | score=0.556 | geometry

In triangle \(ABC\), point \(D\) lies on side \(BC\) such that \(BD = 3\) and \(DC = 7\). The incircle of triangle \(ABD\) touches \(BD\) at point \(P\), and the incircle of triangle \(ADC\) touches \(DC\) at point \(Q\). If the incircles of triangles \(ABD\) and \(ADC\) are externally tangent to each other at point \(R\), find the length of \(PQ\).

Answer: `10`

## 0301 | score=0.333 | geometry

Given a set of \( n \) distinct points in the plane, no three of which are collinear, let \( S(n) \) denote the maximum number of triangles that can be formed using these points as vertices such that no two triangles share a side. Find a general formula for \( S(n) \) for \( n \geq 3 \).

Answer: `\left\lfloor \frac{n}{3} \right\rfloor`

## 0302 | score=0.333 | number_theory

Find all positive integers \( n \) such that the equation \( x^2 - ny^2 = 2n \) has integer solutions \( (x, y) \).

Answer: `2`

## 0303 | score=0.444 | geometry

In a triangular lattice of points where each point is equidistant from its nearest neighbors, how many distinct squares can be formed by connecting points such that each square's side length is equal to the distance between two consecutive lattice points and its vertices lie on lattice points? Consider only those squares that do not have any vertices coinciding with the vertices of a triangle formed by the lattice's bases.

Answer: `0`

## 0304 | score=0.667 | number_theory

Find all positive integers \( n \) such that the equation \( x^2 + y^2 + z^2 = n(xy + yz + zx) \) has at least one non-trivial integer solution \( (x, y, z) \) where not all of \( x, y, z \) are zero.

Answer: `1`

## 0305 | score=0.556 | geometry

A regular hexagon \(ABCDEF\) is inscribed in a circle of radius \(r\). Points \(P\) and \(Q\) lie on segments \(AB\) and \(CD\) respectively, such that \(AP = CQ\). The lines \(EP\) and \(FQ\) intersect at point \(R\). Find the length of segment \(PR\) in terms of \(r\).

Answer: `\frac{r}{2}`

## 0306 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the equation \( x^3 + y^3 + z^3 = n \) has no solutions in non-negative integers \( x, y, \) and \( z \). Prove your answer.

Answer: `42`

## 0307 | score=0.778 | algebra

Let \( f(x) \) be a polynomial of degree 3 with real coefficients such that \( f(x) = x^3 + ax^2 + bx + c \). Given that the roots of \( f(x) \) are \( \alpha, \beta, \gamma \), and that these roots satisfy the equations \( \alpha + \beta + \gamma = 3 \), \( \alpha^2 + \beta^2 + \gamma^2 = 7 \), and \( \alpha^3 + \beta^3 + \gamma^3 = 5 \), determine the value of \( f(4) \).

Answer: `\frac{73}{3}`

## 0308 | score=0.750 | number_theory

Find the smallest positive integer \( n \) such that the number of distinct prime factors of \( n \) plus the number of distinct prime factors of \( n+1 \) equals 4.

Answer: `14`

## 0309 | score=0.667 | number_theory

Find the number of ordered pairs of integers \((a, b)\) such that \(1 \leq a, b \leq 50\) and the equation
\[a^2 - b^2 = 45\]
has integer solutions for \(a\) and \(b\).

Answer: `3`

## 0310 | score=0.667 | geometry

Consider a regular octagon \(ABCDEFGH\) inscribed in a unit circle centered at \(O\). Points \(P\) and \(Q\) are chosen on the extensions of sides \(AB\) and \(BC\) respectively, such that \(AP = BQ = \sqrt{2}\). Let \(X\) be the intersection of \(PQ\) and \(AH\). Find the length of \(AX\).

Answer: `1`

## 0311 | score=0.444 | geometry

Find all positive integers \( n \) such that \( 2^n + 3^n + 6^n + 7^n \) is a perfect square.

Answer: `0`

## 0312 | score=0.333 | geometry

Let $ABC$ be an isosceles triangle with $AB=AC$ and let $D$ be the foot of the altitude from $A$ to $BC$. Let $E$ be a point on $AB$ such that $DE$ is perpendicular to $AB$, and let $F$ be a point on $AC$ such that $DF$ is perpendicular to $AC$. If the area of triangle $ABC$ is 120 and the area of triangle $DEF$ is 20, find the length of $DE$.

Answer: `4`

## 0313 | score=0.667 | number_theory

Find the smallest positive integer \( n \) such that the equation \( \sum_{k=1}^{n} \left\lfloor \frac{k^2}{4} \right\rfloor = 100 \) holds true.

Answer: `11`

## 0314 | score=0.778 | geometry

Let \( P(x) \) be a polynomial with integer coefficients such that for any positive integer \( n \), the expression \( P(n) \) is a perfect square. Prove that there exist integers \( a \) and \( b \) such that \( P(x) = ax^2 + b \) for all \( x \).

Answer: `P(x) = ax^2 + b`

## 0315 | score=0.667 | number_theory

Find all pairs of positive integers \((a, b)\) such that the equation
\[ a^2 + b^2 = ab(a + b) \]
holds true.

Answer: `(1, 1)`

## 0316 | score=0.667 | geometry

Let \( ABC \) be an acute triangle with circumcenter \( O \) and orthocenter \( H \). The circle passing through \( A \), \( B \), and \( O \) intersects the circumcircle of \( ABC \) again at \( P \). The line \( HP \) intersects the circumcircle of \( ABC \) again at \( Q \). Prove that the line \( PQ \) is perpendicular to \( OH \).

Answer: `PQ \perp OH`

## 0317 | score=0.556 | geometry

Let \( \triangle ABC \) be a triangle with \( AB = AC \) and \( \angle BAC = 20^\circ \). Point \( D \) is on \( BC \) such that \( BD = AC \). Find the measure of \( \angle ADB \) in degrees.

Answer: `50`

## 0318 | score=0.333 | number_theory

Consider a sequence of integers where each term after the first is generated by adding the previous term to a non-zero integer $k$. If the sum of the first $n$ terms of the sequence is $S_n$, and it is known that $S_4 = 60$ and $S_{12} = 1440$, determine the value of $k$ and the sum of the first 20 terms of the sequence.

Answer: `4500`

## 0319 | score=0.778 | algebra

Find all real numbers \(x\) such that the equation
\[ \sqrt{x + \sqrt{2x + \sqrt{3x}}} = x \]
holds. Provide a proof for your solution.

Answer: `0`

## 0320 | score=0.556 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(0) = 0 \), \( P(1) = 2 \), and \( P(2) = 8 \). If \( Q(x) = P(x) - x^3 \), find the sum of all possible integer values of \( x \) for which \( Q(x) = 0 \).

Answer: `2`

## 0321 | score=0.556 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a continuous function such that for all \( x, y \in \mathbb{R} \), the function satisfies the inequality \( f(x+y) \leq f(x) + f(y) + xy \). Prove that \( f \) is a polynomial function and find its degree.

Answer: `2`

## 0322 | score=0.667 | number_theory

Determine all positive integers \( n \) such that there exists a sequence \( a_1, a_2, \ldots, a_n \) of non-negative integers where \( a_1 = 1 \), \( a_n = 2024 \), and for each \( i \) with \( 1 \leq i \leq n-1 \), the following conditions hold:
1. \( a_{i+1} = a_i + k \) for some integer \( k \) with \( 1 \leq k \leq 3 \).
2. \( a_{i+1} \neq a_j + 2 \) for all \( j \) with \( 1 \leq j \leq i \).

Find the largest possible value of \( n \).

Answer: `675`

## 0323 | score=0.667 | number_theory

A sequence of numbers \(a_1, a_2, a_3, \ldots\) is defined recursively by \(a_1 = 1\) and for \(n \geq 1\), \(a_{n+1} = a_n + \frac{1}{a_n}\). Find the smallest positive integer \(k\) such that \(a_k > 100\).

Answer: `5001`

## 0324 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers less than \( 2^{2024} \) that are coprime to \( 2^{2024} \). Consider the function \( f : S \to S \) defined by \( f(x) = 2024 \cdot \left\lfloor \frac{x}{2024} \right\rfloor \). Find the number of elements in the set \( \{x \in S : f(x) \equiv x \pmod{2024}\} \).

Answer: `0`

## 0325 | score=0.778 | geometry

Given a square grid of side length n, where each cell contains a unique integer from 1 to n^2, determine the maximum number of cells that can be selected such that no two selected cells are adjacent horizontally, vertically, or diagonally. The side length of the grid is n = 10.

Answer: `50`

## 0326 | score=0.556 | number_theory

Let \( S \) be the set of all positive integers that can be represented as the sum of three distinct prime numbers. Define \( T \) as the set of all integers \( n \) such that \( n \) is the smallest element of \( S \) that can be written in the form \( n = p_1^2 + p_2^2 + p_3^2 \) where \( p_1, p_2, \) and \( p_3 \) are distinct primes. Find the smallest element of \( T \).

Answer: `38`

## 0327 | score=0.333 | number_theory

Find all positive integers \( n \) such that the equation \( x^3 + y^3 + z^3 = n \) has no integer solutions \((x, y, z)\) where \( x, y, \) and \( z \) are pairwise relatively prime.

Answer: `1`

## 0328 | score=0.333 | combinatorics

A sequence of numbers \(a_n\) is defined as follows: \(a_1 = 1\), \(a_2 = 2\), and for \(n \geq 3\), \(a_n = a_{n-1} + a_{n-2} + (-1)^n\). Find the sum of the first 20 terms of this sequence.

Answer: `24475`

## 0329 | score=0.333 | algebra

在一个平面直角坐标系中，有一系列点 \((x_1, y_1), (x_2, y_2), \ldots, (x_n, y_n)\) 分别位于不同的象限。已知点 \((x_1, y_1)\) 位于第一象限，而点 \((x_2, y_2)\) 位于第二象限，且点 \((x_n, y_n)\) 位于第四象限。如果点 \((x_2, y_2)\) 到原点的距离是点 \((x_1, y_1)\) 到原点距离的两倍，同时，点 \((x_n, y_n)\) 到原点的距离比点 \((x_1, y_1)\) 到原点的距离少4个单位。求点 \((x_1, y_1)\) 到原点的距离。

此外，已知这些点满足以下线性关系：
\[ ax_1 + by_1 + c = 0 \]
\[ dx_2 + ey_2 + f = 0 \]
\[ gx_n + hy_n + k = 0 \]
其中，\(a, b, c, d, e, f, g, h, k\) 是非零整数，且没有共同的除1以外的因子。给定 \(a=1, b=2, c=-3, d=2, e=-3, f=5, g=1, h=3, k=-7\)，求解 \((x_1, y_1)\) 到原点的距离。

Answer: `\sqrt{2}`

## 0330 | score=0.556 | number_theory

Consider a sequence of integers where the $n$-th term, $a_n$, is defined as $a_n = n^2 - 2n + 3$. Define $S_k$ as the sum of the first $k$ terms of this sequence, where $k$ is a positive integer. Find the smallest value of $k$ for which $S_k$ exceeds 1000.

Answer: `15`

## 0331 | score=0.667 | number_theory

Let \( f: \mathbb{Z} \to \mathbb{Z} \) be a function such that for all integers \( m \) and \( n \),
\[ f(mn) + f(m + n) = f(m)f(n) + 1. \]
Given that \( f(0) = 1 \), find the value of \( f(1) \).

Answer: `1`

## 0332 | score=0.444 | number_theory

Let \( f(n) \) be the number of ways to partition the set \( \{1, 2, \dots, n\} \) into disjoint non-empty subsets such that each subset contains exactly one prime number. For example, \( f(3) = 2 \) since we can partition the set \( \{1, 2, 3\} \) as \( \{\{1, 2\}, \{3\}\} \) or \( \{\{1, 3\}, \{2\}\} \). Find \( f(10) \).

Answer: `812`

## 0333 | score=0.556 | number_theory

Let \( P(x) \) be a polynomial with real coefficients such that \( P(1) = 0 \) and \( P(x) = x^n + a_{n-1}x^{n-1} + \cdots + a_1x + a_0 \) for some integer \( n \geq 1 \). Suppose that \( P(x) \) has the property that for every real number \( x \), \( P(x) \) is an integer if and only if \( x \) is an integer. Determine the largest possible value of \( n \).

Answer: `1`

## 0334 | score=0.444 | algebra

Find all real numbers \( x \) such that the equation
\[ \log_2(x^2 - 5x + 6) + \log_2(x - 2) = 3 \]
holds. Express your answer in interval notation.

Answer: `(3, \infty)`

## 0335 | score=0.556 | number_theory

Let $S$ be the set of all positive integers. A subset $T$ of $S$ is called "harmonious" if it satisfies the following conditions:
1. For any two elements $a, b \in T$, the greatest common divisor $\gcd(a, b) = 1$.
2. For any element $x \in T$, if $y$ is any other element of $T$ such that $y \neq x$ and $x < y$, then $x$ divides $y$.

Find the number of harmonious subsets of $S$ that contain exactly 3 elements and do not contain any prime number.

Answer: `1`

## 0336 | score=0.556 | number_theory

Find all positive integers \( n \) such that \( n \) divides \( 2^n + 1 \) and \( n \) is less than 1000. Prove your answer.

Answer: `1, 3, 9, 27, 81, 243, 729`

## 0337 | score=0.444 | number_theory

Find all positive integers \( n \) such that \( 2^n + 3^n \equiv 0 \pmod{n} \).

Answer: `5`

## 0338 | score=0.444 | combinatorics

Let $f: \mathbb{R} \to \mathbb{R}$ be a continuous, differentiable function such that $f(0) = 0$ and $f'(x) > 0$ for all $x \in \mathbb{R}$. Define a sequence of functions $\{g_n\}_{n \geq 1}$ by $g_n(x) = \frac{1}{n} \sum_{k=1}^n f\left(\frac{kx}{n}\right)$. Prove that for any $a \in \mathbb{R}$, there exists a sequence of points $\{x_n\}_{n \geq 1}$ in the interval $[0, a]$ such that $\lim_{n \to \infty} x_n = a$ and $\lim_{n \to \infty} g_n(x_n) = f(a)$.

Answer: `\lim_{n \to \infty} g_n(x_n) = f(a)`

## 0339 | score=0.556 | combinatorics

In a kingdom, there are 2023 cities, and each pair of cities is connected by exactly one road. A traveler starts from a city and visits some other cities, returning to the starting city, without visiting any city more than once except the starting city. The traveler notices that the sum of the degrees of the cities visited (excluding the starting city) is always even. What is the maximum number of cities the traveler can visit?

Answer: `2023`

## 0340 | score=0.667 | number_theory

Consider a sequence of positive integers \( a_1, a_2, a_3, \ldots, a_n \) such that for each \( k \geq 3 \), \( a_k \) is the smallest positive integer not appearing earlier in the sequence that can be expressed as the sum of any two distinct previous terms. For example, starting with \( a_1 = 1 \) and \( a_2 = 2 \), the next term \( a_3 \) is \( 3 \) because it can be expressed as \( 1 + 2 \). Given that \( a_{10} = 17 \), determine the smallest possible value of \( a_1 \).

Answer: `1`

## 0341 | score=0.444 | algebra

Find all real numbers \(x\) such that \(\frac{x^3 - 3x + 2}{x^2 - 1} = 4\). Determine the sum of all such \(x\).

Answer: `3`

## 0342 | score=0.556 | geometry

In the coordinate plane, consider a circle \( C \) centered at the origin with radius \( r \), and a point \( P \) on the circle such that \( \angle POP' = 120^\circ \), where \( P' \) is another point on the circle. Let \( Q \) be the midpoint of the arc \( PP' \) that does not contain the origin. If the line segment \( OQ \) intersects the circle again at point \( R \), determine the length of the chord \( PR \) in terms of \( r \).

Answer: `r\sqrt{3}`

## 0343 | score=0.667 | geometry

Let \( S \) be the set of all positive integers less than 1000 that are both perfect squares and perfect cubes. Define the function \( f(n) \) as the sum of the digits of \( n \). Find the smallest positive integer \( k \) such that \( f(k) \) is equal to the number of elements in \( S \).

Answer: `3`

## 0344 | score=0.444 | number_theory

Find the number of ways to write 2023 as a sum of positive integers such that the largest part has exactly 7 occurrences, and the second-largest part has exactly 5 occurrences. (Note that the order of parts does not matter, so (7, 7, 7, 5, 5, 5, 5, 5) is the same as (5, 5, 5, 5, 5, 7, 7, 7)).

Answer: `1`

## 0345 | score=0.444 | combinatorics

There are 10 distinct books on a shelf. How many ways can you arrange these books such that no two adjacent books are published in the same year? Assume that 5 of the books were published in 2020, 3 in 2021, and 2 in 2022.

Answer: `1440`

## 0346 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the product of the first \( n \) positive integers (i.e., \( n! \)) is divisible by \( 2^{n} + 1 \).

Answer: `10`

## 0347 | score=0.778 | geometry

Consider a sequence of positive integers \(a_1, a_2, a_3, \ldots\) where each term \(a_n\) is defined as the sum of the squares of the digits of \(n\). For example, \(a_5 = 5^2 = 25\) and \(a_{23} = 2^2 + 3^2 = 13\). Define \(S\) as the smallest integer such that \(a_S\) is a perfect square. What is the value of \(S\)?

Answer: `1`

## 0348 | score=0.667 | number_theory

Consider a sequence of positive integers \(a_1, a_2, a_3, \ldots\) where each term \(a_n\) is defined as the smallest integer greater than \(a_{n-1}\) such that \(a_n\) is not a multiple of any of the previous terms in the sequence. Given that \(a_1 = 1\), determine the value of \(a_{20}\).

Answer: `20`

## 0349 | score=0.556 | algebra

Let $P$ be a polynomial of degree 4 such that $P(1) = 1$, $P(2) = 2$, $P(3) = 3$, $P(4) = 4$, and $P(5) = 0$. Find the value of $P(6)$.

Answer: `-19`

## 0350 | score=0.556 | number_theory

Let \( f(x) \) be a polynomial with integer coefficients such that for any positive integer \( n \), the number \( f(n) \) is divisible by the \( n \)-th prime number \( p_n \). Prove that \( f(x) \) must be the zero polynomial.

Answer: `0`

## 0351 | score=0.667 | algebra

Let $p(x)$ be a monic polynomial of degree 5 with real coefficients such that the polynomial has exactly one real root and four non-real complex roots. Suppose the real root is $r$. It is given that the sum of the real and imaginary parts of each non-real root is equal to $r$. Find the number of possible values for $r$.

Answer: `1`

## 0352 | score=0.444 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a continuous function such that for all real numbers \( x \) and \( y \), the following functional equation holds:
\[ f(x^2 + y^2) = f(x)^2 + f(y)^2 + 2f(x)f(y). \]
Prove that there exists a constant \( c \in \mathbb{R} \) such that \( f(x) = c(x^2 + 1) \) for all \( x \in \mathbb{R} \).

Answer: `f(x) = c(x^2 + 1)`

## 0353 | score=0.333 | other

In a magical land, there are three types of coins: gold, silver, and bronze. A gold coin is worth 3 silver coins, and a silver coin is worth 5 bronze coins. A wizard has a bag containing a total of 100 coins, and the value of these coins in bronze coin units is 200. The wizard wants to distribute these coins equally among his three apprentices in such a way that each apprentice receives the same number of coins and the same total value in bronze coin units. How many bronze coins does each apprentice receive?

Answer: `67`

## 0354 | score=0.667 | number_theory

There exists a sequence of positive integers \( a_1, a_2, a_3, \ldots \) defined by \( a_1 = 1 \) and \( a_{n+1} = a_n^2 + 1 \) for all \( n \geq 1 \). Determine the largest positive integer \( k \) such that for every \( n \in \mathbb{N} \), the greatest common divisor of \( a_n \) and \( a_{n+k} \) is 1.

Answer: `1`

## 0355 | score=0.444 | number_theory

Find all triples of positive integers \((a, b, c)\) such that \(a + b + c = 1000\), and there exists a polynomial \(P(x)\) with integer coefficients for which \(P(n) = n^2\) for all \(n = a, b, c\). Additionally, prove that there are no other triples that satisfy these conditions.

Answer: `(333, 333, 334)`

## 0356 | score=0.444 | geometry

Find the smallest positive integer \( n \) such that the sum of the digits of \( n \) is a perfect square, and the product of the digits of \( n \) is also a perfect square.

Answer: `1`

## 0357 | score=0.333 | number_theory

Find all positive integers \( n \) such that there exist two positive integers \( a \) and \( b \) satisfying both of the following conditions:
1. \( a^2 + b^2 + 1 \) is a prime number,
2. \( a^2 + b^2 + 1 \) divides \( a^n + b^n \).

Answer: `1`

## 0358 | score=0.778 | number_theory

Consider a sequence of positive integers \(a_1, a_2, a_3, \ldots\) defined as follows: \(a_1 = 2\), and for \(n \geq 2\), \(a_n\) is the smallest integer greater than \(a_{n-1}\) that is relatively prime to all previous terms in the sequence. Let \(S_n = \sum_{k=1}^{n} a_k\). Find the remainder when \(S_{100}\) is divided by 1000.

Answer: `133`

## 0359 | score=0.444 | algebra

In the complex plane, let \( z \) be a complex number such that \( |z| = 1 \). Let \( w = z^2 + \frac{1}{z^2} \). If \( w \) is a real number, determine the number of distinct possible values for \( w \) as \( z \) varies over all possible complex numbers with magnitude 1.

Answer: `\infty`

## 0360 | score=0.333 | geometry

In triangle ABC, AB = AC and angle A is 36 degrees. Point D lies on BC such that AD is perpendicular to BC. If the area of triangle ABC is 36 square units, find the length of BC.

Answer: `12`

## 0361 | score=0.333 | geometry

Find all positive integers \( n \) such that there exists a positive integer \( m \) for which the sum of the first \( n \) terms of the arithmetic sequence starting with 1 and having a common difference of \( m \) is a perfect square.

Answer: `1`

## 0362 | score=0.333 | number_theory

In a mysterious city, there exists a unique type of fruit tree that bears fruits in distinct sequences based on the year it was planted. The sequence for each tree is defined by a polynomial \(P(n) = an^2 + bn + c\), where \(n\) is the year since planting. This year, a botanist noticed that a particular tree, which was planted in year 2000, bore fruits in a sequence that could be described by a polynomial with integer coefficients. Intrigued, the botanist also observed that in the year 2002, the tree bore fruits in the 6th spot of its sequence (i.e., the 6th term when \(n = 2002\)). Furthermore, the botanist deduced that the sum of the coefficients \(a + b + c\) of the polynomial is a prime number. What is the smallest possible value for \(c\) in the polynomial \(P(n)\)?

Answer: `1`

## 0363 | score=0.667 | algebra

Let \( f(x) = x^3 - 3x^2 + 2x + 1 \). Find the sum of all real solutions to the equation \( f(f(x)) = 0 \).

Answer: `3`

## 0364 | score=0.556 | algebra

Let $a, b, c$ be positive real numbers such that $a + b + c = 1$. Find the minimum value of
\[
\frac{a}{1 + b^2} + \frac{b}{1 + c^2} + \frac{c}{1 + a^2}.
\]

Answer: `\frac{9}{10}`

## 0365 | score=0.444 | sequence

The sequence \\(a_n\\) is defined as follows: \\(a_1 = 1\\), and for all \\(n \geq 1\\), \\[a_{n+1} = a_n^2 + \frac{1}{a_n}.\]
Find the value of \\(a_{2023} - a_{2022}.\]

Answer: `0`

## 0366 | score=0.444 | algebra

在平面直角坐标系中，有一系列由正整数组成的点集合 \( S = \{ (x, y) | x, y \in \mathbb{Z}^+, x + y \leq 100 \} \)，其中 \( \mathbb{Z}^+ \) 表示所有正整数的集合。现在从集合 \( S \) 中随机选择三个不同的点 \( A(x_1, y_1) \), \( B(x_2, y_2) \) 和 \( C(x_3, y_3) \)。设这三个点组成的三角形面积为 \( T \)。求 \( T \) 为整数的概率。

Answer: `1`

## 0367 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + ax^{n-1} + bx^{n-2} + \cdots + k \) has the property that \( P(1) = 2024 \) and \( P(-1) = 2023 \), where \( a, b, \ldots, k \) are real numbers satisfying \( a + b + \cdots + k = 2022 \). Additionally, determine the number of such polynomials \( P(x) \) for each valid \( n \).

Answer: `1`

## 0368 | score=0.778 | number_theory

What is the smallest positive integer \( n \) for which the equation \( n^2 - 10n + 21 = k^2 \) holds for some integer \( k \)?

Answer: `3`

## 0369 | score=0.556 | geometry

Let \( ABC \) be a triangle with circumcircle \( \omega \). Let \( P \) and \( Q \) be distinct points on the circumcircle such that \( \angle APQ = \angle BPQ = \angle CPQ \). If the tangents to \( \omega \) at \( A \) and \( B \) intersect at \( X \), and the tangents to \( \omega \) at \( B \) and \( C \) intersect at \( Y \), prove that the line \( PQ \) is the radical axis of the circumcircles of triangles \( AXY \) and \( BYC \).

Answer: `PQ`

## 0370 | score=0.667 | geometry

Find the smallest positive integer $n$ for which there exist $n$ distinct positive integers $a_1, a_2, \dots, a_n$ such that the sum of any two consecutive integers in the sequence, when each is squared, equals a perfect square. That is, find the minimum $n$ for which:
\[
\forall i \in \{1, 2, \dots, n-1\}, \quad a_i^2 + a_{i+1}^2 \text{ is a perfect square.}
\]

Answer: `2`

## 0371 | score=0.333 | geometry

Find all positive integers \( n \) such that the sum of the squares of the first \( n \) positive integers is equal to the sum of the squares of the first \( m \) positive integers for some positive integer \( m \neq n \). That is, solve the equation:
\[ 1^2 + 2^2 + 3^2 + \cdots + n^2 = 1^2 + 2^2 + 3^2 + \cdots + m^2 \]
where \( m \neq n \).

Answer: `24`

## 0372 | score=0.333 | number_theory

Let \( S \) be the set of all positive integers. Consider the function \( f: S \to S \) defined by the rule that for each positive integer \( n \), \( f(n) \) is the smallest positive integer \( m \) such that the sum of the digits of \( m \) equals \( n \). For example, \( f(1) = 1 \), \( f(2) = 2 \), \( f(3) = 3 \), \( f(10) = 19 \), and \( f(19) = 199 \). Find the smallest positive integer \( n \) such that \( f(f(f(n))) = n \).

Answer: `1`

## 0373 | score=0.556 | number_theory

There are 10 identical balls, each of which can be assigned one of three colors: red, green, or blue, such that the number of balls of each color is divisible by 3. How many distinct ways can you color these balls, considering rotations and reflections as identical?

Answer: `0`

## 0374 | score=0.556 | geometry

Find the sum of all positive integers \( n \) less than 1000 such that \( n^2 + 3n + 2 \) is a perfect square.

Answer: `0`

## 0375 | score=0.556 | number_theory

Find all positive integers \( n \) such that the equation \( x^n + y^n = z^n \) has no integer solutions for \( x, y, z \) with \( x, y, z > 0 \).

Answer: `n \geq 3`

## 0376 | score=0.444 | number_theory

Let \( f(x) = x^2 + ax + b \) be a quadratic polynomial with integer coefficients. Suppose that for every integer \( n \), \( f(n) \) divides \( n^3 + 1 \). Determine the sum of all possible values of \( f(1) \).

Answer: `0`

## 0377 | score=0.778 | number_theory

Find all prime numbers \( p \) such that \( p^3 - p^2 + p - 1 \) is also a prime number.

Answer: `2`

## 0378 | score=0.333 | geometry

In the coordinate plane, consider a triangle \(ABC\) with vertices at \(A(0, 0)\), \(B(14, 0)\), and \(C(x, y)\) where \(x > 0\) and \(y > 0\). Let \(D\) be the foot of the altitude from \(A\) to \(BC\), and let \(E\) be the midpoint of \(AC\). If the area of triangle \(ABC\) is 84 square units, find the coordinates of \(C\) such that the length of \(DE\) is minimized.

Answer: `(14, 12)`

## 0379 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + nx + 1 \) is divisible by \( Q(x) = x^2 + x + 1 \).

Answer: `2`

## 0380 | score=0.444 | number_theory

In the kingdom of Mathoria, there are $n$ cities connected by a network of $n$ one-way roads, each road connects exactly two cities and no two roads connect the same pair of cities. A traveler decides to embark on a journey where he wishes to visit each city exactly once, starting from the capital city $A$ and ending at the capital city $B$, with the condition that he cannot visit city $A$ or $B$ during the journey. The traveler's path is chosen randomly from all possible paths that adhere to these rules. If the probability that the traveler's randomly chosen path does not revisit any city visited before, except possibly city $B$, is $\frac{p}{q}$ in simplest form, find the remainder when $p+q$ is divided by $1000$ for $n=10$.

Answer: `10`

## 0381 | score=0.778 | geometry

Let $ABC$ be an acute triangle with $\angle BAC = 60^\circ$. Let $D$ be the foot of the altitude from $A$ to $BC$, and let $E$ be the point on $AC$ such that $BD = DE$. If $AB = 2AD$, find the measure of $\angle AEB$ in degrees.

Answer: `90`

## 0382 | score=0.375 | number_theory

Let \( f: \mathbb{N} \to \mathbb{N} \) be a function satisfying the following properties:
1. \( f(1) = 1 \)
2. For all \( n \geq 1 \), \( f(n+1) = f(n) + f\left(\left\lfloor \frac{n}{2} \right\rfloor \right) \), where \( \left\lfloor x \right\rfloor \) denotes the floor function.
Find the smallest positive integer \( n \) such that \( f(n) \) is divisible by 2024.

Answer: `2023`

## 0383 | score=0.667 | geometry

Determine the smallest positive integer \( n \) such that there exist \( n \) points in the plane, no three collinear, where the areas of all triangles formed by any three of these points are equal to integers, but the side lengths of no such triangle are integers.

Answer: `4`

## 0384 | score=0.333 | algebra

设有一个拼图比赛，共有 \( n \) 名学生参与。假设每名学生的完成拼图所需时间为 \( T_i \)，且 \( T_i \) 服从参数为 \( \lambda_i \) 的指数分布。已知 \( \lambda_i \) 是不同的，并且对于所有 \( i \)，\( \lambda_i > 0 \)。

设 \( X \) 表示所有学生完成拼图所需时间的总和。请计算 \( X \) 的数学期望 \( E[X] \) 和方差 \( Var(X) \)。

为了求解这个问题，你需要考虑如何从给定的独立指数分布出发，通过组合数学的方法来计算 \( X \) 的期望值和方差。

Answer: `\sum_{i=1}^n \frac{1}{\lambda_i^2}`

## 0385 | score=0.444 | geometry

In the complex plane, let \( P \) be a point that moves along the unit circle centered at the origin. Let \( Q \) be a fixed point at \( (2, 0) \). The line segment \( PQ \) intersects the y-axis at a point \( R \). As \( P \) moves along the unit circle, find the maximum value of the area of triangle \( PQR \).

Answer: `1`

## 0386 | score=0.444 | number_theory

Let \( P(x) = x^3 + ax^2 + bx + c \) be a polynomial with integer coefficients. Suppose that \( P(x) \) has three distinct roots, all of which are integers. Moreover, for every integer \( n \), the value of \( P(n) \) is divisible by 2023. Find the smallest possible positive value of \( |a + b + c| \).

Answer: `1`

## 0387 | score=0.778 | number_theory

Let \( f: \mathbb{Z}^+ \to \mathbb{Z}^+ \) be a function such that for all positive integers \( m \) and \( n \),

\[
f(m + n) = f(m) + f(n) + 2mn.
\]

Suppose that \( f(1) = 1 \). Determine \( f(2024) \).

Answer: `4096576`

## 0388 | score=0.444 | geometry

What is the minimum number of distinct rectangles that can be drawn on a 4x4 grid such that no two rectangles share a common area, and the total area of the rectangles is exactly half the area of the grid?

Answer: `2`

## 0389 | score=0.778 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) divides \( x^{2023} - 1 \) without leaving a remainder.

Answer: `6, 16, 118, 288, 2022`

## 0390 | score=0.556 | geometry

In a geometric configuration where \(ABCD\) is a cyclic quadrilateral inscribed in a circle with center \(O\), and \(P\) is the intersection of the diagonals \(AC\) and \(BD\). If \(\angle APD = 130^\circ\) and the measure of arc \(AD\) (not containing \(B\) and \(C\)) is \(100^\circ\), find the measure of \(\angle BPC\).

Answer: `50^\circ`

## 0391 | score=0.667 | number_theory

In a sequence of positive integers \(a_1, a_2, \ldots, a_{2023}\), each term \(a_n\) satisfies \(a_n = n^2 + k\) for some fixed integer \(k\). It is known that for each \(n\), \(a_n\) divides the product of the first \(n\) terms of the sequence, \(a_1 a_2 \cdots a_n\). Find the number of distinct possible values of \(k\).

Answer: `1`

## 0392 | score=0.444 | number_theory

Let \( P(x) \) be a polynomial of degree 3 with integer coefficients such that \( P(1) = 5 \), \( P(2) = 10 \), and \( P(3) = 17 \). Suppose \( P(x) \) can be factored as \( P(x) = (x-a)(x-b)(x-c) \) where \( a, b, \) and \( c \) are distinct integers. Find the value of \( P(4) \).

Answer: `32`

## 0393 | score=0.556 | number_theory

Find all positive integers \( n \) such that there exist \( n \) non-zero integers \( a_1, a_2, \ldots, a_n \) where the sum of their pairwise products, \( \sum_{1 \leq i < j \leq n} a_i a_j \), equals \( n^2 \).

Answer: `2`

## 0394 | score=0.444 | other

在一个平面直角坐标系中，有一个圆 \(C\) 的中心在点 \((1, 1)\)，半径为 1。已知点 \(P_0 = (2, 2)\)，每次操作将 \(P_0\) 沿直线 \(y=x\) 平移一个单位到新的点 \(P_1\)，然后将 \(P_1\) 沿直线 \(y=-x+2\) 平移一个单位到新的点 \(P_2\)。这一过程不断重复，直到 \(P_n\) 点与圆 \(C\) 相切或相交。求最小的正整数 \(n\) 使得 \(P_n\) 点满足上述条件。

Answer: `4`

## 0395 | score=0.556 | number_theory

Find all positive integers \( n \) such that \( n^2 + 1 \) is divisible by \( n + 1 \) and \( n^2 - 1 \) is not divisible by \( n - 1 \).

Answer: `1`

## 0396 | score=0.556 | number_theory

Find all positive integers \( n \) such that the equation \( x^2 + y^2 + z^2 = nxyz \) has a solution in positive integers \( x, y, z \).

Answer: `3`

## 0397 | score=0.667 | number_theory

Let \(a, b,\) and \(c\) be positive integers such that \(a \leq b \leq c\). Find the number of ordered triples \((a, b, c)\) that satisfy the equation
\[a^2 + b^2 + c^2 = ab + bc + ca + 1.\]

Answer: `1`

## 0398 | score=0.444 | geometry

In a regular octagon ABCDEFGH, let M be the midpoint of AB, N be the midpoint of CD, and P be the midpoint of EF. The diagonals AE and BH intersect at point Q. If the area of triangle QMN is 16 square units, find the area of the octagon. Express your answer in simplest radical form.

Answer: `128`

## 0399 | score=0.556 | number_theory

Find the smallest positive integer $n$ for which there exists a positive integer $m$ such that the sum of the first $m$ terms of the arithmetic sequence starting at $1$ with a common difference of $n$ is equal to the product of the first $n$ terms of the geometric sequence starting at $2$ with a common ratio of $3$.

Answer: `1`

## 0400 | score=0.778 | combinatorics

In a certain game, a player starts with a bag containing $10$ marbles, $5$ of which are red and $5$ are blue. The player draws marbles one at a time without replacement until all marbles of one color are drawn. What is the probability that the player draws all $5$ red marbles before drawing any blue marbles? Express your answer as a common fraction.

Answer: `\frac{1}{252}`

## 0401 | score=0.778 | number_theory

Find the number of ordered triples $(a, b, c)$ of positive integers such that $a, b, c \leq 100$ and the equation $a + \frac{1}{b} + \frac{1}{c} = \frac{1}{2}$ holds true.

Answer: `0`

## 0402 | score=0.444 | number_theory

Find all integers $n$ such that the quadratic expression $x^2 + nx + 16$ can be factored over the integers, and both factors have at least one integer root.

Answer: `\{-17, -10, -8, 8, 10, 17\}`

## 0403 | score=0.333 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that \( n \) can be expressed as the sum of two or more consecutive positive integers in exactly three distinct ways. For example, \( 9 = 4 + 5 = 2 + 3 + 4 = 1 + 2 + 3 + 3 \). Find the smallest element of \( S \).

Answer: `15`

## 0404 | score=0.556 | number_theory

Find the number of distinct positive integers \( n \) such that the equation \( x^2 - nx + 2024 = 0 \) has integer solutions, and \( n \) is also a prime number.

Answer: `0`

## 0405 | score=0.444 | number_theory

Let $p$ be a prime number and $n$ be a positive integer. A function $f:\mathbb{Z}_p\rightarrow\mathbb{Z}_p$ is called "prime-friendly" if for any $x\in\mathbb{Z}_p$, there exists a unique $y\in\mathbb{Z}_p$ such that $f(y)=x$ and the sum of the coefficients in the polynomial expression of $f$ (considered as a polynomial in $\mathbb{Z}[x]$) is equal to $n$. How many prime-friendly functions are there from $\mathbb{Z}_p$ to $\mathbb{Z}_p$?

Answer: `(p-1)! \times p`

## 0406 | score=0.667 | number_theory

A finite sequence of non-zero digits is formed by concatenating all positive integers in increasing order, i.e., "123456789101112..." Continue this sequence infinitely. What is the 1000th digit of this sequence?

Answer: `3`

## 0407 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that \( n! \) (n factorial) is divisible by the product of the first \( n \) prime numbers. That is, determine the smallest \( n \) for which \( n! \) is divisible by \( 2 \times 3 \times 5 \times \cdots \times p_n \), where \( p_n \) is the \( n \)-th prime number.

Answer: `7`

## 0408 | score=0.333 | geometry

Let \( ABC \) be an acute-angled triangle with \( AB < AC \). Let \( D \) be the foot of the altitude from \( A \) to \( BC \), and let \( E \) and \( F \) be points on segments \( BD \) and \( CD \), respectively, such that \( AE = AF \). Suppose that the circumcircle of \( \triangle DEF \) intersects the circumcircle of \( \triangle ABC \) at a point \( G \) distinct from \( A \). If \( \angle BAC = 60^\circ \) and \( BC = 1 \), find the length of \( AG \).

Answer: `1`

## 0409 | score=0.444 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a continuous function such that for every real number \( x \), the equation \( f(x) = x^3 + ax^2 + bx + c \) holds, where \( a, b, \) and \( c \) are constants. If \( f(f(x)) = x \) for all real numbers \( x \), find the values of \( a, b, \) and \( c \).

Additionally, let \( g: \mathbb{R} \to \mathbb{R} \) be defined as \( g(x) = f(x) - x \). Show that \( g(x) \) is an odd function and find the value of \( g(1) + g(-1) \).

Finally, determine the number of solutions to the equation \( f(x) = x \) in the interval \( [0, 1] \).

Answer: `1`

## 0410 | score=0.333 | number_theory

Find all prime numbers \( p \) such that \( p^2 + 11 \) has at least three distinct prime divisors, each of which is less than 20.

Answer: `7, 11, 13, 17`

## 0411 | score=0.778 | number_theory

Find all positive integers \( n \) such that \( n^2 + 4n + 4 \) is divisible by \( n^2 + 4 \).

Answer: `2`

## 0412 | score=0.556 | number_theory

Let \( n \) be a positive integer such that \( n \leq 100 \). Define a sequence \( a_1, a_2, a_3, \ldots \) by the rule:
\[ a_{k+1} = \left\lfloor \frac{2a_k}{3} \right\rfloor + \left\lfloor \frac{a_k}{3} \right\rfloor \]
for all \( k \geq 1 \), with the initial term \( a_1 = n \). Find the sum of all distinct positive integers \( n \) for which the sequence \( a_k \) eventually becomes constant.

Answer: `1683`

## 0413 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that the number \( 2^n + 3^n \) is divisible by 5. Determine the smallest positive integer \( k \) for which there exists a positive integer \( m \) such that \( 2^m + 3^m \equiv 0 \pmod{5} \) and \( m + k \) is a multiple of 6.

Answer: `3`

## 0414 | score=0.333 | number_theory

Let \( S \) be the set of all ordered triples of positive integers \( (a, b, c) \) such that \( a \leq b \leq c \leq 100 \) and \( abc \) is divisible by \( a + b + c \). Find the remainder when the number of elements in \( S \) is divided by 1000.

Answer: `0`

## 0415 | score=0.333 | algebra

Let $a, b, c$ be positive real numbers such that $a + b + c = 1$ and $abc = 3^{10}$. Find the minimum value of \[\frac{a}{1+a} + \frac{b}{1+b} + \frac{c}{1+c}.\]

Answer: `\frac{3}{4}`

## 0416 | score=0.333 | number_theory

Let \( n \) be a positive integer such that \( n^2 + n + 1 \) is divisible by 5. Find all possible remainders when \( n \) is divided by 15.

Answer: `2, 3, 7, 8, 12, 13`

## 0417 | score=0.667 | geometry

What is the least positive integer \( n \) such that the polynomial \( P(x) = x^n - 1 \) has exactly \( n \) distinct complex roots, including multiplicities, that can all be expressed as \( a + bi \) where \( a \) and \( b \) are integers, and \( a^2 + b^2 \) is a perfect square?

Answer: `4`

## 0418 | score=0.444 | number_theory

Find all pairs of positive integers \((a, b)\) such that \(a^2 + b^2\) is divisible by \(ab + 1\). How many such pairs exist?

Answer: `1`

## 0419 | score=0.778 | geometry

In the complex plane, the vertices of a regular hexagon are the points \(1, i, -1, -i, -1-i, 1-i\). Find the sum of the squares of the distances from the origin to each vertex. Express your answer in the form \(a+bi\), where \(a\) and \(b\) are real numbers.

Answer: `8`

## 0420 | score=0.556 | combinatorics

In the complex plane, consider a sequence of points \( P_1, P_2, \ldots, P_{2023} \) such that \( P_1 \) is at \( 1+i \) and \( P_{n+1} \) is the reflection of \( P_n \) across the real axis if \( n \) is odd, and the reflection across the imaginary axis if \( n \) is even. What is the sum of the imaginary parts of all \( P_n \)?

Answer: `1`

## 0421 | score=0.444 | number_theory

A sequence of positive integers \( a_1, a_2, \ldots, a_n \) is defined as follows: \( a_1 = 1 \) and for all \( k \geq 2 \), \( a_k \) is the smallest integer greater than \( a_{k-1} \) that is relatively prime to all previous terms in the sequence. Find the sum of all distinct primes \( p \) such that there exists an \( n \) for which \( a_n = p \cdot q \) where \( p \) and \( q \) are distinct primes.

Answer: `0`

## 0422 | score=0.333 | algebra

In the complex plane, let \( z \) be a root of the polynomial \( P(z) = z^5 - 3z^3 + 2z - 1 \). Determine the maximum possible value of \( |z| \), the magnitude of \( z \).

Answer: `2`

## 0423 | score=0.444 | geometry

A convex polygon with \(n\) sides has the property that the sum of the interior angles at any three consecutive vertices is always a constant \(S\). If \(n = 10\), find the value of \(S\).

Answer: `432`

## 0424 | score=0.667 | number_theory

Let $S$ be a set of integers such that for any two elements $a$ and $b$ in $S$, the expression $a^2 + ab + b^2$ is divisible by 5. Given that $S$ contains exactly 10 distinct elements, what is the maximum number of elements in $S$ that can be multiples of 5?

Answer: `10`

## 0425 | score=0.333 | geometry

In the Cartesian plane, consider a hyperbola with its transverse axis along the x-axis and its foci at (5, 0) and (-5, 0). Let P be a point on the hyperbola such that the distance from P to the right focus is twice the distance from P to the left focus. If the area of the triangle formed by the two foci and point P is 40 square units, find the equation of the hyperbola in the standard form \(\frac{x^2}{a^2} - \frac{y^2}{b^2} = 1\).

Answer: `\frac{x^2}{9} - \frac{y^2}{16} = 1`

## 0426 | score=0.333 | geometry

In an advanced exploration of geometric series and sequences, consider a sequence where each term is derived from the square of a corresponding term in a geometric progression with the first term 1 and common ratio \(\frac{2}{3}\). Find the least integer value of \(n > 1\) for which the sum of the first \(n\) terms of this derived sequence exceeds 100. Present your answer as the next greatest integer after your computation.

Answer: `5`

## 0427 | score=0.333 | other

Consider a regular hexagon $ABCDEF$ with side length $10$. Each vertex is connected to every other vertex by a diagonal. Find the number of diagonals that intersect the interior of the hexagon, passing through more than two vertices. Additionally, determine the length of the longest diagonal that does not pass through more than two vertices.

Answer: `10\sqrt{3}`

## 0428 | score=0.444 | combinatorics

What is the minimum number of colors needed to color the vertices of a regular octagon such that no two vertices of the same color are adjacent and the sum of the colors of any two adjacent vertices is not equal to 7?

Answer: `2`

## 0429 | score=0.667 | number_theory

Find the smallest positive integer \( n \) such that the sum of the digits of \( n \) in base 10 is equal to the sum of the digits of \( 2n \) in base 10, and both sums are prime numbers.

Answer: `7`

## 0430 | score=0.667 | number_theory

Let \(a_1, a_2, \ldots, a_n\) be positive integers such that \(\sum_{i=1}^n a_i = 100\). Find the maximum possible value of \(\sum_{1 \leq i < j \leq n} a_i a_j\).

Answer: `4950`

## 0431 | score=0.444 | number_theory

Find all positive integers \( n \) such that the number of ways to partition the set \(\{1, 2, \ldots, n\}\) into two non-empty subsets of equal size (in terms of the number of elements) is equal to the sum of the first \( n \) positive integers. 

Formally, determine all \( n \in \mathbb{N} \) for which
\[ \frac{\binom{n}{n/2}}{2} = \sum_{k=1}^{n} k. \]

Answer: `0`

## 0432 | score=0.667 | algebra

Find the minimum value of the expression
\[ \frac{x^2 + y^2}{(x - y)^2} \]
for real numbers \(x\) and \(y\) such that \(x \neq y\).

Answer: `\frac{1}{2}`

## 0433 | score=0.667 | number_theory

Consider a sequence \(a_n\) defined for all positive integers \(n\) such that \(a_1 = 1\) and for \(n > 1\),
\[a_n = a_{n-1} + \frac{a_{n-1}}{n}.\]
Determine the smallest positive integer \(m\) such that \(a_m > 10\).

Answer: `20`

## 0434 | score=0.556 | geometry

Find the smallest positive integer \( n \) such that for any set of \( n \) distinct points on a circle, it is possible to draw a line through the center of the circle that divides the circle into two parts, each containing exactly \( \left\lfloor \frac{n}{2} \right\rfloor \) points (where \(\lfloor x \rfloor\) denotes the floor function, the greatest integer less than or equal to \( x \)).

Answer: `4`

## 0435 | score=0.556 | number_theory

Determine all triples \((a, b, c)\) of positive integers such that
\[ a^2 + b^2 + c^2 + 3abc + 1 = 4(ab + bc + ca). \]

Answer: `(1, 1, 1)`

## 0436 | score=0.778 | algebra

Find all real numbers \( x \) such that \( x^3 - 3x^2 + 4 = 0 \) and determine the sum of all such \( x \).

Answer: `3`

## 0437 | score=0.556 | other

Let \( ABCD \) be a convex quadrilateral with \( AB = 6 \), \( BC = 7 \), \( CD = 8 \), and \( DA = 9 \). The diagonals \( AC \) and \( BD \) intersect at point \( E \), such that \( AE : EC = 1 : 2 \) and \( BE : ED = 1 : 1 \). Determine the length of the diagonal \( BD \).

Answer: `10`

## 0438 | score=0.444 | geometry

In triangle \( ABC \), let \( P \) be a point inside the triangle such that the distances from \( P \) to the sides \( BC, CA, \) and \( AB \) are \( x, y, \) and \( z \) respectively. If the area of triangle \( ABC \) is \( S \) and the circumradius is \( R \), prove that:
\[ \frac{1}{x^2} + \frac{1}{y^2} + \frac{1}{z^2} = \frac{4}{S^2} \left( \frac{R}{r} \right)^2 \]
where \( r \) is the inradius of triangle \( ABC \).

Answer: `\frac{1}{x^2} + \frac{1}{y^2} + \frac{1}{z^2} = \frac{4}{S^2} \left( \frac{R}{r} \right)^2`

## 0439 | score=0.556 | number_theory

Let \( S \) be the set of all positive integers \( n \) for which the sum of the digits of \( n \) is equal to the sum of the digits of \( n^2 \). Find the number of elements in the set \( S \) that are less than 1000 and are also prime numbers.

Answer: `1`

## 0440 | score=0.444 | number_theory

Let $S$ be the set of all positive integers $n$ such that $n$ can be expressed as the sum of two or more consecutive positive integers. For example, $9$ is in $S$ because $9 = 4 + 5$ and $15$ is in $S$ because $15 = 7 + 8$. Let $T$ be the set of all positive integers $m$ such that $m$ is a prime number and $m^2$ is in $S$. Find the sum of all elements in $T$.

Answer: `2`

## 0441 | score=0.444 | geometry

In a certain geometry competition, a unique triangle is defined as a triangle with integer side lengths, where the inradius is exactly half the circumradius. Determine the number of unique triangles that can be formed with a perimeter less than 1000 units.

Answer: `333`

## 0442 | score=0.556 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + (n-1)x + (n-1) \) is divisible by another polynomial \( Q(x) = x^2 + x + 1 \).

Answer: `2`

## 0443 | score=0.333 | geometry

Let \(ABC\) be a triangle with \(\angle BAC = 60^\circ\), and let \(D\) be a point on side \(BC\) such that \(AD\) bisects \(\angle BAC\). If \(BD = 4\), \(DC = 6\), and \(AD = 5\), find the area of triangle \(ABC\). Express your answer in simplest radical form.

Answer: `\frac{49\sqrt{3}}{4}`

## 0444 | score=0.444 | number_theory

Find all positive integers \( n \) for which the equation
\[ n^2 + 3n + 2 = 2^k \]
has integer solutions for \( k \).

Answer: `1`

## 0445 | score=0.556 | algebra

Find all functions \( f : \mathbb{R} \to \mathbb{R} \) such that for all real numbers \( x, y, z \), the equation \( f(x + y) + f(y + z) + f(z + x) = f(x + y + z) + f(x) + f(y) + f(z) \) holds.

Answer: `f(x) = cx`

## 0446 | score=0.556 | combinatorics

In a kingdom, there are 100 towns connected by roads. Each road connects exactly two towns, and no two roads connect the same pair of towns. A traveler starts at a particular town and wishes to visit every town exactly once before returning to the starting town. The traveler notices that in the kingdom, for any three towns, the sum of the roads connecting these three towns is always even. What is the minimum number of roads that must be built to ensure the traveler can always complete the journey as described, and prove that this number is indeed the minimum?

Answer: `2500`

## 0447 | score=0.333 | algebra

In a 3-dimensional space, there exists a solid formed by connecting the vertices of a regular tetrahedron to the midpoint of the opposite face. If the side length of the original tetrahedron is \( s \), find the volume of this new solid as a function of \( s \).

Answer: `\frac{s^3 \sqrt{2}}{24}`

## 0448 | score=0.444 | number_theory

Consider a sequence of positive integers \(a_1, a_2, a_3, \ldots\) defined as follows: \(a_1 = 2\), and for each \(n \geq 2\), \(a_n\) is the smallest integer greater than \(a_{n-1}\) that is relatively prime to \(a_{n-1}\). Define the set \(S = \{a_1, a_2, \ldots, a_{10}\}\). Find the sum of all distinct prime factors of the product of all elements in \(S\).

Answer: `129`

## 0449 | score=0.333 | number_theory

Let \( S \) be a set of integers such that for any three distinct elements \( a, b, c \in S \), the expression \( a^2 + b^2 + c^2 \) is divisible by \( 2024 \). Determine the maximum possible size of \( S \) under these conditions.

Answer: `3`

## 0450 | score=0.667 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(1) = 4 \) and \( P(4) = 121 \). If \( P(x) \) has the form \( P(x) = ax^2 + bx + c \), find the maximum possible value of \( a \).

Answer: `7`

## 0451 | score=0.333 | geometry

Find all prime numbers \(p\) and \(q\) such that \(p^2 + pq + q^2\) is a perfect square.

Answer: `(3, 5), (5, 3)`

## 0452 | score=0.778 | geometry

Let \( ABCD \) be a convex quadrilateral inscribed in a circle \( \Gamma \) with \( AB = a \), \( BC = b \), \( CD = c \), and \( DA = d \). Suppose that the diagonals \( AC \) and \( BD \) intersect at point \( P \) such that \( AP = 3 \), \( PC = 7 \), \( BP = 4 \), and \( PD = 6 \). If the area of quadrilateral \( ABCD \) is \( 60 \), find the radius of the circle \( \Gamma \).

Answer: `5`

## 0453 | score=0.667 | geometry

Let \(ABC\) be an acute triangle with circumradius \(R\) and inradius \(r\). Let \(O\) be the circumcenter of \(ABC\) and \(H\) be the orthocenter. If the length of the segment \(OH\) is equal to \(3R\), determine the minimum possible value of the ratio \(\frac{R}{r}\).

Answer: `2`

## 0454 | score=0.333 | geometry

Let $ABCDEF$ be a regular hexagon with side length $s$. Points $P, Q, R, S, T,$ and $U$ are the midpoints of sides $AB, BC, CD, DE, EF$, and $FA$, respectively. If lines are drawn from each vertex of the hexagon to the points that are not midpoints of the adjacent sides, and the area of the hexagon is given by $A$, find the total area of the hexagons formed inside the original hexagon. Express your answer as a fraction of $A$.

Answer: `\frac{1}{4}`

## 0455 | score=0.667 | number_theory

Let $f: \mathbb{N} \rightarrow \mathbb{N}$ be a function defined by $f(n) = n^2 + n + 1$. Consider the set $S = \{f(n) : n \in \mathbb{N}\}$. How many positive integers less than or equal to $100$ can be expressed as the product of two distinct elements of $S$?

Answer: `5`

## 0456 | score=0.444 | number_theory

What is the smallest positive integer n such that n^3 - 7n^2 + 11n - 5 is divisible by 1000?

Answer: `1`

## 0457 | score=0.778 | number_theory

Find all positive integers \(n\) such that \(n^3 + n^2 + 1\) divides \(n^4 + 2n^3 + 3n^2 + 4n + 5\).

Answer: `1`

## 0458 | score=0.444 | geometry

In the coordinate plane, a circle with radius $r$ is centered at $(h,k)$. A tangent line to the circle at a point $P$ intersects the x-axis at $Q$ and the y-axis at $R$. If the coordinates of $P$ are $(h + r, k)$, determine the area of $\triangle OQR$ in terms of $r$, where $O$ is the origin.

Answer: `\frac{1}{2} r^2`

## 0459 | score=0.556 | geometry

In triangle \( ABC \), \( \angle A = 90^\circ \) and \( AB = AC \). The point \( D \) is on \( BC \) such that \( BD = 3DC \). The point \( E \) is the midpoint of \( AD \). Find the ratio of the area of triangle \( BDE \) to the area of triangle \( ABC \).

Answer: `\frac{3}{8}`

## 0460 | score=0.556 | number_theory

Find the smallest positive integer \( n \) such that the sum of the digits of \( 2^n \) is equal to \( n \) and \( 2^n \) ends in 2.

Answer: `5`

## 0461 | score=0.667 | algebra

Let \( P(x) \) be a polynomial of degree 5 with real coefficients such that \( P(1) = 1, P(2) = 4, P(3) = 9, P(4) = 16, \) and \( P(5) = 25. \) Determine the value of \( P(6). \)

Answer: `36`

## 0462 | score=0.444 | geometry

In a convex pentagon $ABCDE$, the diagonals $AC$ and $BD$ intersect at point $F$. The lengths of the sides are given by $AB = 5$, $BC = 6$, $CD = 7$, $DE = 8$, and $EA = 9$. If the area of the pentagon $ABCDE$ is 180 square units, determine the length of diagonal $BD$.

Answer: `10`

## 0463 | score=0.333 | geometry

Let $a, b, c$ be the side lengths of a triangle such that $a + b + c = 1$ and $a^2 + b^2 + c^2 = \frac{1}{2}$. Find the maximum possible value of $\sqrt{a} + \sqrt{b} + \sqrt{c}$.

Answer: `\sqrt{3}`

## 0464 | score=0.778 | geometry

In the town of Polygonville, there are two types of roads: straight roads that connect city hall to every park, and circular roads that encircle the town's lake. If there are 10 parks and the circular road around the lake can be traversed in exactly 30 minutes, how many unique routes can a person take starting from city hall, visiting each park exactly once, and then returning to city hall through the circular road?

Answer: `3628800`

## 0465 | score=0.333 | geometry

In triangle \(ABC\), point \(D\) is on side \(BC\) such that \(BD = 2CD\). Let \(E\) be the midpoint of \(AD\). If \(AB = 3\), \(AC = 4\), and \(BC = 5\), find the length of \(BE\).

Answer: `2.83`

## 0466 | score=0.556 | geometry

Consider a regular 2024-gon inscribed in a unit circle. Each vertex is connected to its immediate neighbors by chords. Let \( P \) be a point on the circumference of the circle. Compute the sum of the lengths of the chords from \( P \) to all vertices of the 2024-gon.

Answer: `2024`

## 0467 | score=0.333 | combinatorics

In a magical land, there are three types of coins: gold (G), silver (S), and bronze (B). A gold coin is worth 5 silver coins, and a silver coin is worth 5 bronze coins. A wealthy merchant has a chest containing exactly 2023 coins, which could be any combination of G, S, and B. If the total value of the coins is equivalent to 3035 silver coins, how many bronze coins does the merchant have in his chest?

Answer: `0`

## 0468 | score=0.556 | geometry

In triangle $ABC$, point $D$ lies on $BC$ such that $BD:DC = 1:3$. If $E$ is the midpoint of $AD$ and $F$ is the point on $AB$ such that $AF:FB = 3:1$, find the ratio of the area of triangle $AEF$ to the area of triangle $ABC$.

Answer: `\frac{1}{8}`

## 0469 | score=0.556 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(1) = 2023 \) and \( P(2023) = 1 \). Determine the maximum possible number of distinct integer roots of \( P(x) \).

Answer: `2`

## 0470 | score=0.778 | geometry

Find the smallest positive integer \( n \) such that the product of all positive integers less than or equal to \( n \) and greater than 1, divided by the sum of the squares of all positive integers less than or equal to \( n \), is an integer. That is, find the smallest \( n \) for which \(\frac{n!}{1^2 + 2^2 + \cdots + n^2}\) is an integer.

Answer: `1`

## 0471 | score=0.667 | geometry

Let \( S \) be a set of \( n \) points in the plane, where no three points are collinear. Define a "good triangle" as a triangle formed by three points in \( S \) such that no other point in \( S \) lies inside the triangle. Determine the maximum number of good triangles that can be formed from any set of \( n \) points.

Answer: `\binom{n}{3}`

## 0472 | score=0.444 | geometry

In a convex pentagon \(ABCDE\), the interior angles satisfy \(\angle A + \angle B + \angle C = 360^\circ\) and \(\angle D + \angle E = 360^\circ\). If the side lengths \(AB = BC = CD = DE = 5\) and \(EA = 12\), find the length of the diagonal \(AC\).

Answer: `13`

## 0473 | score=0.556 | logic_puzzle

In a magical forest, there are three types of trees: oak, maple, and pine. Oak trees can magically duplicate themselves every year, maple trees can magically triple themselves every two years, and pine trees can magically quintuple themselves every three years. Initially, there are 10 oak trees, 5 maple trees, and 3 pine trees. After how many years will the total number of trees be exactly 123? Assume no trees are lost or relocated and each type of tree follows its unique magical growth pattern.

Answer: `3`

## 0474 | score=0.667 | algebra

Let $f(x)$ be a polynomial of degree 3 such that $f(1) = 2$, $f(2) = 3$, $f(3) = 4$, and $f(4) = 5$. Find the value of $f(5) + f(6)$.

Answer: `13`

## 0475 | score=0.333 | number_theory

Let $p$, $q$, and $r$ be distinct prime numbers, and let $S$ be the set of all integers of the form $p^a q^b r^c$, where $a$, $b$, and $c$ are non-negative integers. Determine the number of subsets $T$ of $S$ such that the product of any two distinct elements in $T$ is not divisible by the product of any three elements in $T$.

Answer: `8`

## 0476 | score=0.556 | geometry

In the complex plane, let $A$, $B$, and $C$ be points corresponding to complex numbers $a$, $b$, and $c$ respectively, such that $a$, $b$, and $c$ are vertices of an equilateral triangle. If $a = 1 + i$, $b = 3 + 2i$, and $c$ is in the third quadrant, find the area of the triangle formed by the midpoints of segments $AB$, $BC$, and $CA$.

Answer: `\frac{5\sqrt{3}}{16}`

## 0477 | score=0.333 | geometry

A square of side length 1 is placed inside a circle. A smaller circle is inscribed in one of the corners of the square. What is the radius of the smaller circle if the larger circle has a radius of 1?

Answer: `\frac{1}{2}`

## 0478 | score=0.444 | number_theory

What is the largest integer n such that there exist positive integers a, b, c, d satisfying the equation 1/a + 1/b + 1/c + 1/d = 1/n?

Answer: `1`

## 0479 | score=0.556 | number_theory

Let \( p \) and \( q \) be distinct odd prime numbers. Consider the set \( S \) of all positive integers \( n \) such that \( n \) can be expressed in the form \( n = kp + lq \) where \( k \) and \( l \) are non-negative integers and \( k + l \leq 5 \). Determine the number of distinct elements in the set \( S \).

Answer: `21`

## 0480 | score=0.333 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a function defined by \( f(x) = x^3 - 3x + 1 \). Suppose \( f \) has three distinct real roots \( a, b, c \) such that \( a + b + c = 0 \). Define \( g(x) = f(x)f(-x) \). Determine the number of real roots of \( g(x) \) in the interval \( (-\infty, 0) \).

Answer: `2`

## 0481 | score=0.667 | number_theory

Find all positive integers \( n \) such that the equation \( x^3 + y^3 + z^3 = 3n^3 \) has a solution in positive integers \( x, y, z \) with \( x, y, z \) pairwise coprime.

Answer: `1`

## 0482 | score=0.778 | geometry

在平面直角坐标系 \(xOy\) 中，设 \(A\)、\(B\)、\(C\) 三点位于第一象限内，满足以下条件：
1. 点 \(A\) 的坐标为 \((a, 0)\)，其中 \(a > 0\)；
2. 点 \(B\) 的坐标为 \((0, b)\)，其中 \(b > 0\)；
3. 线段 \(AB\) 上存在一点 \(P\)，使得 \(PA : PB = 1 : 2\)；
4. 线段 \(AC\) 上存在一点 \(Q\)，使得 \(AQ : QC = 2 : 1\)；
5. 线段 \(BC\) 上存在一点 \(R\)，使得 \(BR : RC = 1 : 2\)；
6. 直线 \(QR\) 与线段 \(AB\) 相交于点 \(S\)。

求证：\(\angle OSB = 90^\circ\)。

Answer: `\angle OSB = 90^\circ`

## 0483 | score=0.778 | geometry

A circular dartboard has a radius of 10 units. Points scored on the dartboard are determined by the area of the region where the dart lands. If a dart lands within a smaller concentric circle of radius 6 units, it scores 10 points. If it lands within the ring between the radii 6 and 8 units, it scores 5 points. If it lands within the ring between the radii 8 and 10 units, it scores 2 points. Finally, if it lands outside these regions, it scores 1 point. What is the expected score if the dart is thrown at random?

Answer: `5.72`

## 0484 | score=0.444 | number_theory

Let $P(x)$ be a monic polynomial of degree $n$ with complex coefficients such that $P(1) = P(2) = \cdots = P(n+1) = 0$ and $P(n+2) = 2^{n+2}$. Find the remainder when $P(x)$ is divided by $x^{n+1} - (n+1)!x^n + \cdots + (-1)^{n+1}(n+1)!$.

Answer: `0`

## 0485 | score=0.556 | number_theory

Find all positive integers \( n \) such that there exists a polynomial \( P(x) \) of degree \( n \) with integer coefficients satisfying the equation \( P(k) = k^2 \) for exactly \( n \) distinct integer values of \( k \).

Answer: `1`

## 0486 | score=0.333 | number_theory

In the sequence of positive integers \(a_1, a_2, a_3, \ldots\), \(a_1 = 2021\), and each subsequent term \(a_{n+1}\) is obtained by deleting the digits of \(a_n\) if they are even, and by appending the number 1 if no such digits can be deleted. Determine the value of \(a_{2021}\).

Answer: `111\ldots1`

## 0487 | score=0.556 | number_theory

Let $f(x) = \sin(x) + \cos(x)$ for $x \in [0, \pi]$. Find the smallest positive integer $n$ such that $f(x)$ can be expressed as a polynomial of degree $n$ with real coefficients satisfying $f(x) = 0$ for exactly two values of $x$ in the interval $[0, \pi]$.

Answer: `2`

## 0488 | score=0.444 | number_theory

Consider a sequence of complex numbers \( \{z_n\} \) defined recursively by \( z_1 = 1 + i \) and \( z_{n+1} = z_n^2 + c \), where \( c \) is a fixed complex number. Find the number of distinct values of \( c \) such that the sequence \( \{z_n\} \) is bounded (i.e., the modulus of each \( z_n \) is less than or equal to 100) and the real part of \( z_{10} \) is an integer.

Answer: `1`

## 0489 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that \( n! \) (n factorial) is divisible by \( 10^{100} \).

Answer: `405`

## 0490 | score=0.333 | number_theory

Find all positive integers \( n \) such that there exist positive integers \( a \), \( b \), and \( c \) satisfying \( n = a^2 + b^2 + c^2 \) and \( n^2 = abc(a+b+c) \).

Answer: `6`

## 0491 | score=0.667 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) can be expressed as the product of two non-constant polynomials with integer coefficients.

Answer: `3`

## 0492 | score=0.556 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a function such that for all real numbers \( x \) and \( y \), the following equation holds:
\[ f(x + y) = f(x)f(y) - f(x) + f(y) - xy. \]
If \( f(0) = 2 \), determine the value of \( f(1) \).

Answer: `2`

## 0493 | score=0.444 | number_theory

Find all positive integers \( n \) such that the equation \( x^n + y^n = z^n + 1 \) has infinitely many solutions in positive integers \( x, y, \) and \( z \).

Answer: `1, 2`

## 0494 | score=0.444 | number_theory

Find all pairs of integers $(x, y)$ such that the equation $x^2 - 2xy + 3y^2 = 12$ has a solution.

Answer: `(0, 2),\ (4, 2),\ (0, -2),\ (-4, -2)`

## 0495 | score=0.556 | algebra

In the complex plane, consider the region \( D \) defined by the inequality \( |z - 1| \leq 2 \). Let \( f(z) = \frac{1}{z^3 - 1} \). Determine the number of points in \( D \) where \( f(z) \) has singularities, and find the sum of the residues of \( f(z) \) at those points.

Answer: `-\frac{1}{3}`

## 0496 | score=0.556 | number_theory

Let \( f: \mathbb{Z}^+ \rightarrow \mathbb{Z}^+ \) be a function such that \( f(1) = 1 \) and for all positive integers \( n \),

\[ f(n + 1) = f(n)^2 + f(n). \]

Find the smallest positive integer \( k \) for which \( f(f(k)) = 2f(k) + 2 \).

Answer: `2`

## 0497 | score=0.778 | geometry

Let \( ABC \) be an isosceles triangle with \( AB = AC \) and \( \angle BAC = 20^\circ \). Let \( D \) be a point on \( AC \) such that \( AD = BC \). Find the measure of \( \angle BDC \).

Answer: `30^\circ`

## 0498 | score=0.333 | number_theory

What is the smallest positive integer \( n \) such that the number of ways to partition the set \(\{1, 2, \ldots, n\}\) into two non-empty subsets with the property that the sum of the elements in one subset is a multiple of the sum of the elements in the other subset is at least 100?

Answer: `20`

## 0499 | score=0.444 | number_theory

Find all positive integers \( n \) such that \( n \) divides \( 2^n + 1 \).

Answer: `1, 3`

## 0500 | score=0.333 | number_theory

Find all triples of positive integers $(a, b, c)$ such that $a + b + c = 300$ and $a^2 + b^2 + c^2 + ab + bc + ca = 70000$. Additionally, determine the maximum value of the product $abc$ among these triples.

Answer: `1000000`

## 0501 | score=0.444 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + 4x^{n-1} + 6x^{n-2} + \cdots + 4x + 1 \) can be factored into two non-constant polynomials with integer coefficients.

Answer: `4`

## 0502 | score=0.333 | number_theory

Given a sequence of positive integers \(a_1, a_2, \ldots, a_n\) where each \(a_i\) is a power of a prime number, and the sum \(S = a_1 + a_2 + \cdots + a_n\) is less than \(2023\), find the number of distinct sequences \((a_1, a_2, \ldots, a_n)\) such that \(S\) is also a prime number.

Answer: `306`

## 0503 | score=0.556 | geometry

In triangle ABC, let D be the midpoint of side AB. Line segments AD and BC intersect at point P. If the length of AD is 18 units, the length of BD is 6 units, and the ratio of the areas of triangles APC and BPD is 4:3, find the length of BC.

You may use the concept of similar triangles and properties of medians in your solution.

Answer: `24`

## 0504 | score=0.444 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(1) = 5 \) and \( P(5) = 1 \). If \( P(n) = n \) for some integer \( n \), determine all possible values of \( n \).

Answer: `3`

## 0505 | score=0.444 | number_theory

Let \( S \) be the set of all ordered triples \( (a, b, c) \) of positive integers such that \( a + b + c = 2023 \). For each triple \( (a, b, c) \), define the weight \( w(a, b, c) \) as the number of distinct prime factors of the product \( abc \). Find the maximum possible value of \( w(a, b, c) \) over all triples in \( S \).

Answer: `3`

## 0506 | score=0.444 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + 1 \) can be expressed as the product of two non-constant polynomials with real coefficients.

Answer: `3`

## 0507 | score=0.444 | number_theory

Let $f: \mathbb{Z} \rightarrow \mathbb{Z}$ be a function satisfying the equation:
$$
f(m) + f(n) = f(m + n) + f(mn - 1)
$$
for all integers $m, n$. Given that $f(0) = 1$, determine the value of $f(2024)$.

Answer: `1`

## 0508 | score=0.667 | geometry

A sequence of positive integers \(a_1, a_2, a_3, \ldots\) is defined as follows: \(a_1 = 1\), and for \(n \geq 1\),
\[a_{n+1} = a_n + \text{the smallest prime factor of } a_n.\]

Determine the smallest positive integer \(m\) such that \(a_m\) is a perfect square.

For example, the first few terms of the sequence are:
\[a_1 = 1, a_2 = 1 + 1 = 2, a_3 = 2 + 2 = 4, a_4 = 4 + 2 = 6, a_5 = 6 + 2 = 8, \ldots\]

Answer: `9`

## 0509 | score=0.333 | geometry

In the complex plane, let \(P\) be the point corresponding to the complex number \(z = 3 + 4i\). A line \(L\) passes through the origin and intersects the circle centered at the origin with radius \(5\) at points \(A\) and \(B\), distinct from \(P\). If \(Q\) is the foot of the perpendicular from \(P\) to line \(L\), find the length of segment \(PQ\). Express your answer as a simplified fraction.

Answer: `\frac{12}{5}`

## 0510 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the number of distinct prime factors of \( n^2 + n + 41 \) is equal to the number of distinct prime factors of \( 2021n + 1 \).

Answer: `2`

## 0511 | score=0.778 | geometry

Let \( ABC \) be an acute triangle with \( AB \neq AC \). Let \( D \) be the foot of the altitude from \( A \) to \( BC \), and let \( E \) be the foot of the altitude from \( D \) to \( AB \). Suppose \( AE = EC \) and \( \angle BAC = 60^\circ \). Find the measure of \( \angle BDE \).

Answer: `30^\circ`

## 0512 | score=0.444 | number_theory

Consider a finite sequence of positive integers \( a_1, a_2, ..., a_n \) where \( n \geq 3 \). This sequence has the property that for any \( 1 \leq i < j < k \leq n \), the expression \( a_i \cdot a_j \cdot a_k \) is divisible by the sum \( a_i + a_j + a_k \). Find all possible values of \( n \) for which such a sequence can exist, and give an example sequence for each valid \( n \).

Answer: `3`

## 0513 | score=0.667 | geometry

In the coordinate plane, consider the set of points \( (x, y) \) that satisfy the following system of equations:
\[ x^2 + y^2 = 25 \]
\[ x^3 + y^3 = 91 \]
Find the maximum value of \( x \) for the points in this set.

Answer: `4`

## 0514 | score=0.444 | number_theory

Let $f(x)$ be a polynomial with integer coefficients such that $f(0) = 1$ and $f(1) = 2$. Define a sequence of polynomials $g_n(x)$ by the recurrence relation:
$$g_1(x) = f(x)$$
$$g_{n+1}(x) = g_n(x)^2 + x$$
for all $n \geq 1$. If $g_{2023}(10)$ is a multiple of $1000$, what is the smallest possible degree of $f(x)$?

Answer: `2`

## 0515 | score=0.444 | geometry

Let $ABC$ be a triangle with $AB = 13$, $BC = 14$, and $CA = 15$. Let $D$ be a point on side $BC$ such that $AD$ is the angle bisector of $\angle BAC$. Let $E$ and $F$ be points on sides $AC$ and $AB$, respectively, such that $DE$ is parallel to $AB$ and $DF$ is parallel to $AC$. If the area of triangle $DEF$ is $\frac{m}{n}$ for relatively prime positive integers $m$ and $n$, find $m + n$.

Answer: `535`

## 0516 | score=0.556 | algebra

Find all real numbers \( x \) that satisfy the inequality \( \left| \frac{x^2 - 3x + 2}{x - 1} \right| < 2 \). Determine the sum of all such \( x \).

Answer: `3`

## 0517 | score=0.667 | number_theory

A sequence of positive integers \(a_1, a_2, a_3, \ldots\) is defined by the recurrence relation \(a_{n+1} = a_n + d_n\), where \(d_n\) is the greatest common divisor of \(a_n\) and \(n\). Given that \(a_1 = 2\) and the first six terms of the sequence are \(2, 3, 5, 7, 11, 13\), find the smallest value of \(n\) for which \(a_n\) is divisible by \(2023\).

Answer: `2023`

## 0518 | score=0.333 | number_theory

Consider a sequence of positive integers \(a_1, a_2, a_3, \ldots, a_n\) such that for each \(k\) where \(1 \leq k \leq n\), the sum \(S_k = a_1 + a_2 + \cdots + a_k\) satisfies the inequality \(S_k \leq 2^k\). If \(a_1 = 1\) and \(a_n = 100\), find the maximum possible value of \(n\).

Answer: `7`

## 0519 | score=0.556 | number_theory

Find the number of ordered triples $(a, b, c)$ of positive integers such that $a^2 + b^2 + c^2 = 2024$ and $a, b, c$ are all distinct.

Answer: `0`

## 0520 | score=0.778 | geometry

In the convex quadrilateral $ABCD$, the sides $AB$ and $CD$ are parallel, and the diagonals $AC$ and $BD$ intersect at point $E$. Given that the length of side $AB$ is 12 units, the length of $CD$ is 16 units, and the area of triangle $AED$ is 36 square units, find the area of triangle $BEC$.

Answer: `64`

## 0521 | score=0.333 | number_theory

Find all pairs of positive integers $(a, b)$ such that the equation
\[ x^2 + ax + b = 0 \]
has two distinct integer roots, and the equation
\[ y^2 + by + a = 0 \]
also has two distinct integer roots.

Answer: `(6, 8)`

## 0522 | score=0.778 | geometry

In triangle ABC, the lengths of the sides are given as AB = 13 units, BC = 14 units, and CA = 15 units. Point D lies on side BC such that angle BAD is equal to angle CAD. If the area of triangle ABD is half the area of triangle ACD, find the length of BD.

Answer: `6.5`

## 0523 | score=0.444 | algebra

Find all real numbers \( x \) such that \(\left(\frac{1}{3}\right)^x + \left(\frac{1}{2}\right)^x = \frac{31}{6}\).

Answer: `2`

## 0524 | score=0.556 | geometry

There are $n$ points in a plane, no three of which are collinear. How many distinct triangles can be formed by selecting 3 of these points, such that the triangle formed does not contain any of the other points inside it? Find a general formula for this number in terms of $n$.

Answer: `\binom{n}{3}`

## 0525 | score=0.444 | geometry

There exists a sequence of positive integers \((a_n)_{n=1}^{\infty}\) defined by \(a_1 = 1\) and for all \(n \geq 2\),
\[a_n = \left\lfloor \sqrt{a_{n-1}^2 + 3n} \right\rfloor.\]
Prove that there is a positive integer \(k\) such that \(a_k\) is a perfect square.

Answer: `1`

## 0526 | score=0.333 | number_theory

Let \( P(x) \) be a monic polynomial of degree 6 with integer coefficients such that \( P(1) = 2024 \), \( P(2) = 2025 \), \( P(3) = 2026 \), \( P(4) = 2027 \), \( P(5) = 2028 \), and \( P(6) = 2029 \). Determine the value of \( P(7) \).

Answer: `2750`

## 0527 | score=0.778 | number_theory

Let \( f(x) \) be a polynomial of degree 4 with integer coefficients such that \( f(1) = 5 \), \( f(2) = 11 \), \( f(3) = 21 \), and \( f(4) = 35 \). If \( r \) is a real root of \( f(x) = 0 \), find the minimum possible value of \( |r| \).

Answer: `1`

## 0528 | score=0.333 | number_theory

Let $S$ be a set of positive integers, and let $f: S \rightarrow \mathbb{N}$ be a function such that $f(n) = n^2$ for all $n \in S$. If $S$ contains exactly $k$ elements, and the sum of $f(n)$ for all $n \in S$ is $110$, find the maximum possible value of $k$.

Answer: `4`

## 0529 | score=0.778 | geometry

In the coordinate plane, consider a circle with center at the origin $(0, 0)$ and radius $r$. For a given point $P(a, b)$ inside this circle, let $d$ be the distance from $P$ to the closest point on the circle's boundary. Define the function $f(a, b)$ as the maximum value of $d$ over all points $(a, b)$ that lie on the circle. If $r = 2023$, find the value of $f(a, b)$.

Answer: `2023`

## 0530 | score=0.778 | algebra

Let $f: \mathbb{R} \to \mathbb{R}$ be a continuous function such that for all $x \in \mathbb{R}$ and any $\epsilon > 0$, there exists a polynomial $P(x)$ such that $|f(x) - P(x)| < \epsilon$. Moreover, assume that $f(x)$ satisfies the functional equation $f(x + y) = f(x) + f(y)$ for all $x, y \in \mathbb{R}$.

Prove that there exists a real number $a$ such that $f(x) = ax$ for all $x \in \mathbb{R}$.

Answer: `f(x) = ax`

## 0531 | score=0.667 | number_theory

Find the smallest positive integer \( n \) such that \( \sqrt[n]{2 \sqrt{3} + 3 \sqrt{2}} + \sqrt[n]{2 \sqrt{3} - 3 \sqrt{2}} \) is rational.

Answer: `6`

## 0532 | score=0.333 | other

在一个直角三角形ABC中，∠C为直角，边AB=12厘米。点D位于边BC上，使得BD:DC = 3:1。如果从点D向边AC作垂线交于点E，求DE的长度。假设E点在AC上使得AE:EC = 1:3。如何利用几何关系及比例知识求解此问题？

Answer: `3`

## 0533 | score=0.556 | number_theory

Let $f: \mathbb{N} \to \mathbb{N}$ be a function defined by $f(n) = n^2 - 4n + 4$. Define a sequence $a_n$ by $a_1 = 1$ and $a_{n+1} = f(a_n)$ for all $n \geq 1$. Find the smallest positive integer $k$ such that $a_k = 1$.

Answer: `2`

## 0534 | score=0.778 | geometry

Let \( S \) be a set of \( n \) distinct points in the plane, no three of which are collinear. Define a *happy triangle* as a triangle formed by three points in \( S \) such that the centroid of the triangle lies inside the triangle. Determine the maximum number of happy triangles that can be formed by selecting \( k \) points from \( S \), where \( k \) is a positive integer less than \( n \).

Answer: `\binom{k}{3}`

## 0535 | score=0.333 | geometry

Find the smallest positive integer \( n \) such that \( n \) can be expressed as the sum of two distinct squares in exactly two different ways, and both pairs of squares consist of integers between 1 and 20 inclusive. Prove that your answer is correct.

Answer: `65`

## 0536 | score=0.444 | geometry

Find all positive integers \( n \) for which the sum of the squares of the first \( n \) odd numbers is divisible by the product of the first \( n \) primes.

Answer: `1`

## 0537 | score=0.556 | number_theory

In the realm of complex numbers, let $z_1 = 1 + i\sqrt{3}$ and $z_2 = 2 - i\sqrt{2}$. Define $w_n = z_1^n + z_2^n$ for all positive integers $n$. Determine the smallest positive integer $n$ for which $w_n$ is a real number.

Answer: `6`

## 0538 | score=0.667 | other

In a mystical land, there are three types of magical stones: Ruby, Sapphire, and Emerald. Each stone has a unique power: Ruby doubles the number of gems you have, Sapphire triples it, and Emerald adds 5 more gems. You start with 10 gems. If you can use each type of stone exactly once, what is the maximum number of gems you can have after using them?

Answer: `90`

## 0539 | score=0.556 | number_theory

Find all positive integers \( n \) such that there exists a sequence of \( n \) positive integers \( a_1, a_2, \ldots, a_n \) with the property that for every \( i \) (\( 1 \leq i \leq n \)), the following conditions hold:
1. \( a_i \) is a divisor of \( a_{i+1} \) (with \( a_{n+1} = a_1 \)), and
2. \( a_i \) is not a divisor of \( a_{i+2} \).

Answer: `3`

## 0540 | score=0.333 | number_theory

Find all positive integers \( n \) such that the number of positive divisors of \( n \) is equal to \( 3 + \left\lfloor \frac{n}{10} \right\rfloor \), where \( \left\lfloor x \right\rfloor \) denotes the greatest integer less than or equal to \( x \).

Answer: `4, 9, 10, 14, 15`

## 0541 | score=0.556 | number_theory

A sequence of numbers \(a_1, a_2, a_3, \ldots\) is defined recursively by \(a_1 = 1\) and for all \(n \geq 1\), \(a_{n+1} = \frac{a_n^2 + 1}{2a_n}\). Determine the smallest positive integer \(k\) such that \(a_k\) is an integer and \(a_{k+1} = \frac{a_k^2 + 1}{2a_k}\) is not an integer.

Answer: `1`

## 0542 | score=0.444 | number_theory

Find all positive integers \(n\) such that the expression
\[
\frac{n^3 + 3n^2 + 8n + 4}{n^2 + 1}
\]
is an integer, and prove that these are the only solutions.

Answer: `1`

## 0543 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that the number of distinct positive divisors of \( n \) is exactly 16 and \( n \) is a product of distinct prime numbers.

Answer: `210`

## 0544 | score=0.444 | geometry

A function \( f: \mathbb{Z} \to \mathbb{Z} \) satisfies the recurrence relation \( f(n+1) = f(n) + 3n \) for all integers \( n \), and it is known that \( f(1) = 1 \). Find the smallest positive integer \( k \) such that \( f(k) \) is a perfect square.

Answer: `1`

## 0545 | score=0.444 | algebra

Let $S$ be the set of all continuous functions $f: \mathbb{R} \rightarrow \mathbb{R}$ such that for all $x \in \mathbb{R}$,
\[ f(x) + f(x + 1) + f(x + 2) = 0. \]
Determine the dimension of the vector space spanned by $S$.

Answer: `3`

## 0546 | score=0.667 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + ax^{n-1} + bx^{n-2} + \cdots + k \) has at least one real root, where \( a, b, \ldots, k \) are real numbers with the property that the sum of any non-empty subset of these coefficients is not zero.

Answer: `1`

## 0547 | score=0.778 | number_theory

Let $f(x)$ be a polynomial with integer coefficients such that $f(0) = 1$, $f(1) = 2$, and $f(2) = 5$. If $f(n) = n^3 + 3n^2 + n + 1$ for all integers $n$, find the number of integer values of $x$ for which $f(f(x)) = x^3 + 3x^2 + x + 1$.

Answer: `0`

## 0548 | score=0.333 | number_theory

Consider the sequence \( \{a_n\} \) defined by the recurrence relation \( a_{n+1} = a_n + \frac{1}{a_n} \) with the initial term \( a_1 = 1 \). Determine the smallest positive integer \( n \) such that \( a_n > 100 \).

Answer: `5001`

## 0549 | score=0.667 | algebra

Let $p(x) = x^3 - 3x^2 + 4$ and $q(x) = x^3 - 3x + 2$. Find the number of distinct real solutions to the equation $p(q(x)) = 0$.

Answer: `4`

## 0550 | score=0.556 | number_theory

In a town, there are 100 houses, each with a unique number from 1 to 100. Each house is connected to exactly one other house with a cable, and no two houses are connected more than once. Additionally, for every house \(i\), the house with the number \(i^2 \mod 100\) is also connected to it. What is the minimum number of cables required to connect all the houses according to these rules?

Answer: `50`

## 0551 | score=0.444 | geometry

In the complex plane, let \(A, B,\) and \(C\) be the vertices of an equilateral triangle with side length \(2\sqrt{3}\). Let \(P\) be a point inside the triangle such that the distances from \(P\) to the sides of the triangle are \(d_1, d_2,\) and \(d_3\). Given that \(d_1^2 + d_2^2 + d_3^2 = 6\), find the area of the triangle formed by the points of tangency of the incircle of triangle \(ABC\) with the sides of triangle \(ABC\).

Answer: `\sqrt{3}`

## 0552 | score=0.444 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n - x^{n-1} - \cdots - x + 1 \) has at least one rational root. Prove your answer.

Answer: `1`

## 0553 | score=0.333 | number_theory

Find all positive integers \( n \) such that \( n^2 + n + 1 \) divides \( 19n^2 + 13n + 12 \).

Answer: `6`

## 0554 | score=0.778 | geometry

Consider a regular tetrahedron with edge length \(a\). A point \(P\) is chosen inside the tetrahedron such that the distances from \(P\) to the four vertices are \(d_1, d_2, d_3,\) and \(d_4\), respectively. Given that the sum of the squares of these distances is \(3a^2\), find the value of \(d_1^2 + d_2^2 + d_3^2 + d_4^2\).

Answer: `3a^2`

## 0555 | score=0.333 | geometry

Let \(ABC\) be an isosceles triangle with \(AB = AC\). A point \(P\) lies inside the triangle such that the line segment \(AP\) intersects \(BC\) at point \(D\) and \(BP\) intersects \(AC\) at point \(E\), with \(PE\) being perpendicular to \(BC\). If \(PD = 4\), \(DE = 8\), and \(PB = 6\), find the length of \(PE\).

Answer: `4`

## 0556 | score=0.444 | geometry

In the complex plane, let \( S \) be the set of points \( z \) that satisfy \( |z| < 1 \) and let \( P \) be the set of points \( z \) that satisfy \( |z - 1| < 1 \). Find the area of the region that is contained in both \( S \) and \( P \).

Answer: `\frac{2\pi}{3} - \frac{\sqrt{3}}{2}`

## 0557 | score=0.667 | algebra

Find all real numbers \( x \) such that the equation \( \left( x^2 - 1 \right)^4 + 4 \left( x^2 - 1 \right)^3 + 4 \left( x^2 - 1 \right)^2 + 1 = 0 \) has exactly one solution. Prove your answer.

Answer: `0`

## 0558 | score=0.778 | number_theory

Find all integers \( n \) such that \( 2^n + 2 \) is divisible by \( n^2 \).

Answer: `1`

## 0559 | score=0.333 | other

In a magical kingdom, there are two types of creatures: goblins and giants. The goblins are known for their small size, and each goblin has exactly 3 heads. Giants, on the other hand, are much larger and each giant has exactly 5 heads. The kingdom has a total of 48 heads among its creatures. If the number of goblins is greater than the number of giants, how many goblins and how many giants are there in the kingdom?

Answer: `(11, 3)`

## 0560 | score=0.778 | sequence

In the sequence \( \{a_n\} \) defined by \( a_1 = 1 \) and \( a_{n+1} = \frac{a_n}{2} + \frac{1}{a_n} \) for all \( n \geq 1 \), find the value of \( a_{10} \). Additionally, determine the limit of the sequence as \( n \) approaches infinity.

Answer: `\sqrt{2}`

## 0561 | score=0.333 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that \( n \) can be expressed in the form
\[ n = a^2 + b^2 + c^2 \]
for some non-negative integers \( a \), \( b \), and \( c \). Furthermore, \( n \) must satisfy the following conditions:
1. \( a \neq 0 \), \( b \neq 0 \), and \( c \neq 0 \).
2. \( a \), \( b \), and \( c \) are pairwise coprime (i.e., the greatest common divisor of any two of them is 1).

Determine the smallest positive integer that is not in \( S \). If no such integer exists, prove that the set \( S \) contains all positive integers.

Answer: `2`

## 0562 | score=0.778 | number_theory

Find all triples of positive integers \((a, b, c)\) such that \(a^2 + b^2 + c^2 = abc + 2\) and \(a, b, c\) are pairwise coprime.

Answer: `(1, 1, 1)`

## 0563 | score=0.333 | number_theory

Find the smallest positive integer $n$ such that $\left(\frac{3+i\sqrt{3}}{2}\right)^n + \left(\frac{3-i\sqrt{3}}{2}\right)^n$ is a real number and divisible by 4.

Answer: `6`

## 0564 | score=0.667 | algebra

Find all functions \( f: \mathbb{R} \rightarrow \mathbb{R} \) that satisfy the functional equation
\[ f(x^2 + yf(z)) = xf(x) + zf(y) \]
for all real numbers \( x, y, \) and \( z \).

Answer: `f(x) = 0`

## 0565 | score=0.444 | number_theory

Consider a sequence of positive integers \(a_n\) defined by \(a_1 = 1\), \(a_2 = 2\), and for all \(n \geq 3\), \(a_n = a_{n-1}^2 + a_{n-2}\). Find the remainder when \(a_{2023}\) is divided by \(2023\).

Answer: `0`

## 0566 | score=0.750 | geometry

Let \( f(n) \) be a function defined for all positive integers \( n \), where \( f(n) = n^2 + n + 1 \). Consider the sequence \( a_n \) defined by \( a_1 = 1 \) and \( a_{n+1} = f(a_n) \) for \( n \geq 1 \). Determine the smallest positive integer \( k \) such that \( a_k \) is a perfect square.

Answer: `1`

## 0567 | score=0.778 | number_theory

Let \( A \) and \( B \) be two finite sets of real numbers with \( |A| = n \) and \( |B| = m \) respectively, where \( n, m \in \mathbb{N} \) and \( n \geq m \). Define \( S \) as the set of all possible sums of the form \( a + b \) where \( a \in A \) and \( b \in B \). Prove that if \( A \) and \( B \) are both arithmetic progressions with common differences \( d_A \) and \( d_B \) respectively, then the number of distinct elements in \( S \) is \( n + m - \gcd(n, m) \).

Answer: `n + m - \gcd(n, m)`

## 0568 | score=0.667 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(1) = 5 \) and \( P(2) = 11 \). If \( P(x) \) is also known to be a quadratic polynomial, determine the coefficient of the \( x^2 \) term.

Answer: `1`

## 0569 | score=0.556 | number_theory

Let \( f: \mathbb{Z} \to \mathbb{Z} \) be a function such that for all integers \( x \) and \( y \), the following properties hold:
1. \( f(x + y) = f(x) + f(y) + xy \)
2. \( f(1) = 1 \)

Find the value of \( f(2023) \).

Answer: `2047276`

## 0570 | score=0.667 | number_theory

Find all positive integers \( n \) such that \( n \) divides \( 2^n + 1 \).

Answer: `1, 3`

## 0571 | score=0.333 | geometry

Find all positive integers \( n \) for which \( n^3 - 14n^2 + 53n - 72 \) is a perfect square.

Answer: `9`

## 0572 | score=0.556 | number_theory

Find all positive integers \(n\) for which the expression
\[
\frac{n^2 + 2n + 2}{n^2 + n + 1}
\]
is an integer.

Answer: `1`

## 0573 | score=0.333 | geometry

A regular octahedron is inscribed in a sphere of radius \( R \). Each face of the octahedron is an equilateral triangle. If a point is chosen at random inside the sphere, what is the probability that it lies inside one of the eight faces of the octahedron?

Note: The volume of a regular octahedron with side length \( a \) is given by \( V_{\text{octahedron}} = \frac{\sqrt{2}}{3} a^3 \).

Answer: `\frac{\sqrt{3}}{\pi}`

## 0574 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that \( \frac{1}{2} + \frac{1}{3} + \frac{1}{4} + \cdots + \frac{1}{n} \) exceeds 2.

Answer: `11`

## 0575 | score=0.556 | geometry

Find the smallest positive integer \( n \) such that the sum of the squares of the first \( n \) positive integers is divisible by \( n \) itself. In other words, determine \( n \) where:
\[
\sum_{k=1}^{n} k^2 \equiv 0 \pmod{n}
\]

Answer: `1`

## 0576 | score=0.556 | number_theory

Find the number of ways to arrange the digits 1, 2, 3, 4, 5, 6, 7, 8, 9, and 0 in a row such that no two even digits are adjacent and the sum of the first five digits is divisible by 5.

Answer: `86400`

## 0577 | score=0.778 | number_theory

In the complex plane, let $z_1 = e^{2\pi i/5}$ and $z_2 = e^{6\pi i/5}$. Consider the sequence of points $P_n$ defined recursively by $P_1 = z_1 + z_2$ and for $n \geq 2$, $P_n = P_{n-1} + \frac{P_{n-1} - z_1}{z_2 - z_1}$. Find the smallest positive integer $k$ such that $P_k$ is a real number.

Answer: `5`

## 0578 | score=0.444 | algebra

Let \(a, b,\) and \(c\) be positive real numbers such that \(a + b + c = 1\) and \(a, b, c\) form an arithmetic sequence. Determine the maximum value of \(a^2 + b^2 + c^2\).

Answer: `\frac{5}{9}`

## 0579 | score=0.444 | geometry

In the coordinate plane, a set of points $P$ contains all lattice points $(x, y)$ with $0 \leq x, y \leq 100$. A "Diophantine triangle" is formed by selecting three points from $P$ such that the distances between any two points are rational numbers. Determine the maximum number of points that can be selected from $P$ to form a set $T$ where no Diophantine triangle can be formed among the points in $T$.

Answer: `101`

## 0580 | score=0.556 | algebra

In the complex plane, let \( z \) be a complex number such that \( |z| = 1 \). Define the function \( f(z) = \frac{z^4 + z^2 + 1}{z^2 + z + 1} \). Find the maximum value of \( |f(z)| \) over all complex numbers \( z \) with \( |z| = 1 \).

Answer: `3`

## 0581 | score=0.444 | number_theory

A sequence of positive integers \( a_1, a_2, \dots, a_n \) satisfies the condition that for every \( k \geq 2 \), \( a_k \) is the smallest positive integer not appearing among \( a_1, a_2, \dots, a_{k-1} \) and not equal to \( a_{k-1} \). If the sum of the first 100 terms of this sequence is 2023, determine the value of \( a_{100} \).

Answer: `100`

## 0582 | score=0.444 | number_theory

Find the number of ordered triples \((a, b, c)\) of positive integers such that \(a \leq b \leq c\), \(abc = 2024\), and \(a + b + c\) is divisible by 3.

Answer: `1`

## 0583 | score=0.556 | geometry

Consider a function \( f: \mathbb{Z} \to \mathbb{Z} \) defined by \( f(n) = n^3 - 3n^2 + 3n - 1 \). Find the number of integers \( n \) in the range \( -100 \leq n \leq 100 \) such that \( f(n) \) is a perfect square.

Answer: `19`

## 0584 | score=0.444 | number_theory

Find all pairs of positive integers \((x, y)\) such that \(x^3 + y^3 = (x + y)^2\).

Answer: `(1, 2), (2, 1)`

## 0585 | score=0.778 | number_theory

Find all positive integers \( n \) such that the equation \( x^2 - nx + n = 0 \) has integer solutions for \( x \), and additionally, the product of the solutions is less than \( n^2 \).

Answer: `4`

## 0586 | score=0.556 | number_theory

Let \( S \) be a finite set of positive integers. Define a function \( f: S \times S \to \mathbb{Z} \) such that for any \( x, y \in S \), \( f(x, y) \) is the smallest positive integer that cannot be expressed as \( ax + by \) for any non-negative integers \( a, b \). Prove that if \( S \) contains at least two elements, then \( f(S, S) \) is bounded above by \( |S| \cdot \max(S) \).

Answer: `|S| \cdot \max(S)`

## 0587 | score=0.444 | geometry

Consider a sequence of \( n \) distinct points on a circle, labeled \( P_1, P_2, \dots, P_n \). A "jump" is defined as moving from one point to the next in the clockwise direction. A "walk" is a sequence of jumps where no three consecutive jumps are in the same direction. For example, \( P_1 \to P_2 \to P_3 \to P_4 \) is a walk, but \( P_1 \to P_2 \to P_3 \to P_4 \to P_5 \to P_6 \to P_7 \to P_1 \) is not, because it has seven jumps in the same direction.

Let \( W(n) \) be the number of distinct walks that start and end at \( P_1 \) after exactly \( n \) jumps. Find the remainder when \( W(2023) \) is divided by \( 1000 \).

Answer: `0`

## 0588 | score=0.667 | number_theory

Find the smallest positive integer \( n \) such that the equation \( n^2 + (n+1)^2 + (n+2)^2 = k^3 \) has no solution in positive integers \( k \).

Answer: `1`

## 0589 | score=0.333 | other

在整数 \(n\) 的某个表示中，\(n\) 是由 \(k\) 个非零数字组成，其中每个数字都可以取值为 \(1, 2, 3, 4, 5, 6, 7, 8, 9\)。这些数字的和被记为 \(S\)，而这些数字乘积的最后一位数字也被记为 \(P\)。已知对于所有的 \(n\)，\(S\) 和 \(P\) 都能被 \(k\) 整除。求满足条件的最小的 \(n\) 的值。

Answer: `1`

## 0590 | score=0.333 | number_theory

Find all positive integers $n$ such that the number of divisors of $n$ equals $n/2$, and $n$ is the sum of the cubes of its proper divisors. Additionally, prove that there are no other solutions for $n$ within the range of $1$ to $1000000$.

Answer: `28`

## 0591 | score=0.333 | number_theory

Let \( f: \mathbb{N} \to \mathbb{N} \) be a function such that for all positive integers \( n \),
\[ f(n) = n^2 + 10n + 21 \]
and for all positive integers \( a \) and \( b \),
\[ f(ab) = f(a)f(b). \]
Find the smallest positive integer \( m \) such that \( f(m) = m^2 \).

Answer: `1`

## 0592 | score=0.333 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(1) = 2 \) and \( P(2) = 3 \). Suppose there exists an integer \( n \) such that \( P(n) = 2023 \). Prove that there exists an integer \( m \) such that \( P(m) = 2024 \).

Answer: `m`

## 0593 | score=0.667 | number_theory

Let \( S \) be the set of all positive integers. A function \( f: S \to S \) is defined such that for all \( n \in S \), \( f(f(n)) = 3n \). Determine the number of possible values of \( f(1) \) such that \( f \) is a well-defined function on \( S \).

Answer: `1`

## 0594 | score=0.444 | geometry

Find all pairs of positive integers \((a, b)\) such that both \(a + b\) and \(ab\) are perfect squares. Prove that these are the only possible solutions.

Answer: `(2, 2)`

## 0595 | score=0.556 | geometry

Find all positive integers \( n \) such that the equation
\[ x^n + y^n + z^n = 2015 \]
has no solutions in positive integers \( x, y, z \) with \( x + y + z \) being a perfect square.

Answer: `2`

## 0596 | score=0.778 | number_theory

Find all positive integers \( n \) such that the equation
\[ x^3 - y^3 = n^2 \]
has a solution in integers \( x \) and \( y \), where \( x \neq y \) and \( \gcd(x, y) = 1 \).

Answer: `1`

## 0597 | score=0.333 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(0) = 1 \) and \( P(1) = 5 \). Suppose that \( P(x) \) has exactly one real root, which is an integer. Find the number of possible values of the leading coefficient of \( P(x) \).

Answer: `2`

## 0598 | score=0.333 | number_theory

Let \( S \) be a set of positive integers such that for any two distinct elements \( a \) and \( b \) in \( S \), the sum \( a + b \) is not divisible by either \( a \) or \( b \). Find the maximum number of elements that \( S \) can contain.

Answer: `3`

## 0599 | score=0.444 | geometry

In the complex plane, consider the transformation \(T(z) = e^{i\theta}z + a\), where \(\theta\) is a fixed real number and \(a\) is a complex number with \(|a| = 1\). Let \(S\) be the set of all points \(z\) in the complex plane such that after applying \(T\) three times, the point returns to its original position. If \(\theta = \frac{\pi}{3}\) and \(a = e^{i\pi/6}\), find the area of the smallest closed polygon that can be formed by connecting all points in \(S\).

Answer: `\frac{3\sqrt{3}}{2}`

## 0600 | score=0.667 | algebra

Let \( P(x) \) be a polynomial of degree \( n \) with real coefficients such that \( P(x) \geq 0 \) for all real \( x \). Suppose further that \( P(x) \) has no repeated roots and \( P'(x) \) (the derivative of \( P(x) \)) also has no repeated roots. Prove that \( n \) must be even and find the smallest possible value of \( n \) for which such a polynomial exists.

Answer: `2`

## 0601 | score=0.667 | geometry

In triangle $ABC$, points $D$ and $E$ lie on sides $AB$ and $AC$, respectively, such that $DE$ is parallel to $BC$. If $AD = 3$, $DB = 4$, and the area of triangle $ADE$ is 12 square units, find the area of triangle $ABC$.

Answer: `65 \frac{1}{3}`

## 0602 | score=0.667 | algebra

Let $a, b, c$ be positive real numbers such that $a + b + c = 1$. Find the maximum value of the expression:
\[
\frac{a}{1 + bc} + \frac{b}{1 + ca} + \frac{c}{1 + ab}.
\]

Answer: `\frac{9}{10}`

## 0603 | score=0.333 | number_theory

Let \( P(x) \) be a monic polynomial with integer coefficients such that \( P(1) = 2024 \). Suppose \( P(x) \) has a root \( \alpha \) that is a complex number with real part strictly between 0 and 1. Define the sequence \( \{a_n\} \) by \( a_n = P(n) \) for all integers \( n \). Determine the smallest possible positive integer value of \( N \) such that \( a_N = 0 \).

Answer: `2`

## 0604 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the equation \[ x_1^2 + x_2^2 + \cdots + x_n^2 = 2023 \] has no solution in integers \( x_i \).

Answer: `8`

## 0605 | score=0.333 | number_theory

Let \( f \) be a function defined on the positive integers such that \( f(n) = n^2 + 1 \). Define \( S \) as the set of all positive integers \( n \) for which \( f(n) \) is a prime number. Find the number of elements in \( S \) that are less than 100.

Answer: `5`

## 0606 | score=0.556 | number_theory

Find the number of ways to arrange the numbers 1 through 9 in a 3x3 grid such that each number is greater than the number directly above it and the number to its left, if they exist. Additionally, ensure that the sum of the numbers in each row, column, and diagonal is a multiple of 3.

Answer: `1`

## 0607 | score=0.556 | geometry

A circle with radius $r$ is inscribed in a square, and another smaller circle with radius $s$ is inscribed in one of the right triangles formed by the diagonal of the square. If the area of the smaller circle is exactly one-fourth of the area of the larger circle, find the ratio of the side length of the square to the diameter of the smaller circle. Express your answer in simplest radical form.

Answer: `2`

## 0608 | score=0.333 | combinatorics

In a peculiar town, there are three types of houses: red, blue, and green. Each house is painted either with a unique color combination from red and blue, red and green, or blue and green. The town has a peculiar rule for painting new houses: no two adjacent houses can share the same color combination. On a certain street with 10 houses, how many distinct color combinations for the first house result in at least one pair of adjacent houses with the same color combination if the houses are painted according to this rule?

Answer: `57513`

## 0609 | score=0.444 | geometry

Find all positive integers \( n \) such that the sum of the cubes of the first \( n \) positive integers equals the square of the sum of the first \( n \) positive integers. That is, solve the equation \( \left( \sum_{k=1}^n k \right)^2 = \sum_{k=1}^n k^3 \).

Answer: `1, 2, 3, \ldots`

## 0610 | score=0.333 | geometry

Let \(ABC\) be an acute triangle with \(AB < AC\). Let \(M\) be the midpoint of \(BC\), and \(H\) the orthocenter of triangle \(ABC\). The circle \(\omega\) centered at \(M\) and passing through \(A\) intersects \(BH\) and \(CH\) at points \(X\) and \(Y\) respectively, other than \(H\). Prove that the circumcircle of triangle \(AXY\) passes through a fixed point as \(A\) varies over all positions of \(ABC\) with \(AB < AC\).

Answer: `D`

## 0611 | score=0.444 | geometry

In triangle $ABC$, let $D$, $E$, and $F$ be the midpoints of sides $BC$, $CA$, and $AB$, respectively. The medians $AD$, $BE$, and $CF$ intersect at the centroid $G$. If the area of triangle $ABC$ is 144 square units, find the area of triangle $GDE$. Express your answer as a common fraction.

Answer: `12`

## 0612 | score=0.333 | number_theory

Let \( S \) be the set of all positive integers that can be expressed as the sum of two or more consecutive positive integers. Determine the smallest positive integer \( n \) such that \( n \notin S \) and \( n+1 \in S \).

Answer: `1`

## 0613 | score=0.444 | number_theory

What is the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n - 5x^{n-1} + 10x^{n-2} - 10x^{n-3} + 5x^{n-4} - x^{n-5} \) has exactly five distinct real roots?

Answer: `6`

## 0614 | score=0.333 | other

在二维平面上有一个由n个不同位置的点组成的集合S，这些点构成了一个三角形集合T。从T中随机选择一个三角形移除，直到T为空。请问，在保证每个点至少被选中一次的前提下，S中最多可能有多少个点？

Answer: `n`

## 0615 | score=0.667 | combinatorics

In a magical kingdom, there are four cities, each named after a cardinal direction: Northville, Eastton, Southburg, and Westwood. The king has decided to build a network of roads connecting all these cities such that each city is connected to exactly three others, forming a graph. One day, a mischievous wizard casts a spell that reverses the direction of exactly one of these roads. How many distinct ways can the wizard choose which road to reverse so that the resulting network remains a connected graph?

Answer: `6`

## 0616 | score=0.444 | combinatorics

A fair six-sided die is rolled repeatedly. Let \( X \) be the number of rolls until the first 6 appears, and let \( Y \) be the number of rolls until the first 5 appears. Find the probability that \( X \) is even and \( Y \) is odd.

Answer: `\frac{30}{121}`

## 0617 | score=0.778 | number_theory

Let $f(x)$ be a polynomial with real coefficients such that $f(0) = 1$ and $f(n)$ is an integer for all integers $n$. Prove that there exists a positive integer $N$ such that $f(n)$ is divisible by $N$ for all integers $n$.

Answer: `N`

## 0618 | score=0.333 | geometry

Consider a sequence of integers $a_1, a_2, a_3, \ldots, a_n$ such that each $a_i$ is a positive integer and $a_i \leq a_{i+1}$. Given that $a_1 + a_2 + \cdots + a_n = 1000$ and the product of any three consecutive terms in the sequence is a perfect square, find the maximum possible value of $n$.

Answer: `1000`

## 0619 | score=0.444 | geometry

Find all positive integers \( n \) such that \( n! \) can be expressed as the sum of two positive integer squares and the sum of \( n \) consecutive positive integers.

Answer: `2`

## 0620 | score=0.333 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that the equation \( x^3 + y^3 + z^3 = n \) has positive integer solutions \( (x, y, z) \) where \( x + y + z = 10 \). Determine the sum of all elements in \( S \).

Answer: `1946`

## 0621 | score=0.333 | number_theory

Find all positive integers \( n \) such that \( n \) divides \( 2^{n} - 2 \), and \( n \) is not a power of 2.

Answer: `3`

## 0622 | score=0.778 | geometry

In the complex plane, let $A$, $B$, and $C$ be three distinct points such that the midpoint of the line segment joining $A$ and $B$ lies on the unit circle, and the midpoint of the line segment joining $B$ and $C$ also lies on the unit circle. If the centroid of triangle $ABC$ lies on the line $y = x$, determine the maximum possible value of the product of the distances from the origin to points $A$, $B$, and $C$.

Answer: `8`

## 0623 | score=0.444 | geometry

Let \( ABCD \) be a convex quadrilateral inscribed in a circle with radius \( r \). Let \( P \) be a point inside \( ABCD \) such that the areas of triangles \( \triangle ABP, \triangle BCP, \triangle CDP, \) and \( \triangle DAP \) are all equal. Given that the sum of the distances from \( P \) to the sides \( AB, BC, CD, \) and \( DA \) is \( 2r \), find the ratio of the area of quadrilateral \( ABCD \) to the area of the circle.

Answer: `\frac{2}{\pi}`

## 0624 | score=0.556 | geometry

Let $ABC$ be an acute-angled triangle with $AB \neq AC$. Let $D$ be the foot of the altitude from $A$ to $BC$, and let $E$ and $F$ be the feet of the perpendiculars from $D$ to $AB$ and $AC$, respectively. Suppose that $M$ and $N$ are the midpoints of $BC$ and $EF$, respectively. Prove that the line $MN$ passes through the circumcenter of triangle $ABC$.

Answer: `O`

## 0625 | score=0.444 | geometry

In the xy-plane, let \( P \) be a point that lies on the line \( x + y = 10 \). Suppose \( P \) is also on the circle with radius 5 centered at the origin. Determine the maximum possible distance from \( P \) to the point \( (5, 0) \).

Answer: `10`

## 0626 | score=0.778 | number_theory

A sequence of numbers is defined by $a_1 = 2$, and for all $n \geq 2$, $a_n = a_{n-1}^2 - a_{n-1} + 1$. Determine the smallest positive integer $k$ such that $a_k$ is a prime number.

Answer: `2`

## 0627 | score=0.667 | geometry

In the complex plane, let $P$ be the point representing the complex number $z = 1 + i$. For any point $Q$ on the circle centered at the origin with radius $3$, define the function $f(Q) = \arg(z \cdot \overline{Q})$, where $\overline{Q}$ is the complex conjugate of $Q$. Find the maximum possible value of $f(Q)$ for $Q$ on the circle.

Answer: `\frac{\pi}{4}`

## 0628 | score=0.556 | number_theory

In the sequence \( a_n \) defined by \( a_1 = 1 \) and \( a_{n+1} = a_n + \frac{1}{a_n} \) for all \( n \geq 1 \), determine the integer part of the sum \( \sum_{k=1}^{100} \left( \frac{1}{a_k + a_{k+1}} \right)^2 \).

Answer: `0`

## 0629 | score=0.667 | number_theory

Let $S$ be the set of all positive integers $n$ such that $\sqrt{n}$ is an integer and $10000 \leq n \leq 20000$. If $n$ is randomly chosen from $S$, what is the probability that $n$ has exactly $4$ distinct prime factors?

Answer: `0`

## 0630 | score=0.444 | number_theory

Find all positive integers \( n \) such that the equation \( x^n + y^n + z^n = w^n \) has integer solutions \( (x, y, z, w) \) with \( x, y, z, w \) being distinct and \( n \) being a prime number greater than 2.

Answer: `3`

## 0631 | score=0.556 | other

In a city, there are exactly $2021$ non-empty households. Each household has a unique number of members, ranging from $1$ to $2021$. A friendly neighborhood policy states that each household must form a committee consisting of exactly two other households, but the households must be chosen such that no two chosen households share the same number of members as any other household on the committee. Assuming this policy is followed strictly, find the minimum number of households that will not be able to form such a committee.

Answer: `1`

## 0632 | score=0.667 | number_theory

Let \( S \) be the set of all positive integers that can be expressed as the sum of two or more consecutive positive integers. Determine how many elements of \( S \) are less than or equal to 1000, and prove that the set of all integers that are not elements of \( S \) is precisely the set of powers of 2.

Answer: `990`

## 0633 | score=0.556 | geometry

There is a magical tree that produces fruit every day. On the first day, it produces 1 fruit. Each subsequent day, the number of fruits it produces is the sum of the cubes of the number of fruits produced on the previous day and the day number itself. For example, on the second day, it produces \(1^3 + 2 = 3\) fruits, on the third day it produces \(3^3 + 3 = 30\) fruits, and so on. What is the smallest day number \(n\) such that the total number of fruits produced up to that day is a perfect square?

Answer: `2`

## 0634 | score=0.333 | number_theory

A sequence of positive integers \(a_1, a_2, a_3, \ldots\) is defined by \(a_1 = 2\) and \(a_{n+1} = a_n^2 - a_n + 1\) for all \(n \geq 1\). Find the smallest positive integer \(k\) such that \(a_k\) is divisible by \(1001\).

Answer: `7`

## 0635 | score=0.778 | number_theory

Let $f : \mathbb{Z} \to \mathbb{Z}$ be a function satisfying the following conditions:
1. $f(1) = 1$,
2. $f(x+y) = f(x) + f(y) - 2f(xy)$ for all integers $x$ and $y$,
3. $f(x^2) = [f(x)]^2$ for all integers $x$.
Find the sum of all possible values of $f(3)$.

Answer: `1`

## 0636 | score=0.333 | geometry

In triangle \(ABC\), the incircle touches sides \(BC\), \(CA\), and \(AB\) at points \(D\), \(E\), and \(F\) respectively. If the area of triangle \(ABC\) is \(60\) square units, and the lengths of \(BD\), \(DC\), and \(CF\) are \(6\), \(8\), and \(10\) respectively, find the perimeter of triangle \(ABC\).

Answer: `40`

## 0637 | score=0.667 | number_theory

A sequence of positive integers \(a_1, a_2, a_3, \ldots\) is defined recursively as follows: \(a_1 = 1\), \(a_2 = 2\), and for \(n \geq 3\), \(a_n = a_{n-1} + a_{n-2}\) if \(n\) is odd, and \(a_n = a_{n-1} \cdot a_{n-2}\) if \(n\) is even. Find the remainder when \(a_{100}\) is divided by 10.

Answer: `6`

## 0638 | score=0.444 | geometry

In the coordinate plane, consider a square with vertices at \((0,0)\), \((1,0)\), \((1,1)\), and \((0,1)\). Let \(P\) be a point inside the square such that the distance from \(P\) to each side of the square is a positive integer. If the sum of these distances is 4, find the number of possible distinct points \(P\) can be located.

Answer: `0`

## 0639 | score=0.778 | number_theory

Consider a sequence of numbers defined as follows: \(a_1 = 1\), and for \(n \geq 2\), \(a_n\) is the smallest positive integer such that \(a_n\) does not divide \(a_{n-1}\). For example, \(a_2 = 2\), \(a_3 = 3\), and \(a_4 = 4\). Determine the smallest value of \(n\) for which \(a_n = 2024\).

Answer: `2024`

## 0640 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers that can be expressed as the sum of two or more consecutive positive integers. For example, \( 3 = 1 + 2 \) and \( 5 = 2 + 3 \), so \( 3 \) and \( 5 \) are in \( S \). How many integers in the range \( 1 \) to \( 100 \) are not in \( S \)?

(A) 0
(B) 1
(C) 2
(D) 3
(E) 4

Answer: `4`

## 0641 | score=0.556 | geometry

In the complex plane, consider the function \( f(z) = z^3 - 3z^2 + 2z \). Let \( \gamma \) be the circle \( |z| = 2 \) traversed counterclockwise. Using the argument principle, determine the number of zeros of \( f(z) \) inside \( \gamma \), counting multiplicities.

Answer: `3`

## 0642 | score=0.778 | number_theory

Find all positive integers $n$ such that there exists a positive integer $k$ for which the equation \[n^2 + k^2 + (n+k)^2 = (2023)^2\] holds true. How many such $n$ are there?

Answer: `0`

## 0643 | score=0.444 | combinatorics

A sequence of numbers \(a_1, a_2, a_3, \ldots\) is defined recursively as follows: \(a_1 = 1\), \(a_2 = 1\), and for \(n \geq 3\), \(a_n = a_{n-1} + a_{n-2} - a_{n-3}\). What is the value of \(a_{2023}\)?

Answer: `1`

## 0644 | score=0.667 | number_theory

Consider a sequence of positive integers \(a_1, a_2, a_3, \ldots\) defined recursively as follows:
\[ a_1 = 1, \]
\[ a_{n+1} = a_n^2 - 2a_n + 3 \text{ for } n \geq 1. \]
Determine the smallest integer \(k\) such that \(a_k > 2024\).

Answer: `7`

## 0645 | score=0.444 | number_theory

Let $f:\mathbb{Z}^+ \to \mathbb{Z}^+$ be a function defined by $f(n) = n^2 + 2n + 3$. Find the number of positive integers $n$ less than 100 such that $f(n)$ divides $f(f(n))$.

Answer: `99`

## 0646 | score=0.333 | number_theory

Let \( S \) be a set of integers from 1 to 2023, inclusive. We define a function \( f: S \to S \) such that for any \( n \in S \), the value \( f(n) \) is the number of integers in \( S \) that are less than \( n \) and are relatively prime to \( n \). Determine the maximum possible value of \( f(n) \) for some \( n \in S \).

Answer: `2016`

## 0647 | score=0.333 | number_theory

A sequence of positive integers \(a_1, a_2, a_3, \ldots\) is defined by \(a_1 = 1\), \(a_2 = 2\), and for \(n \geq 3\), \(a_n\) is the smallest integer greater than \(a_{n-1}\) that does not share any prime factors with either \(a_{n-1}\) or \(a_{n-2}\). Find the value of \(a_{1000}\).

Answer: `1000`

## 0648 | score=0.667 | geometry

In a game of complex chess, a knight moves in a spiral pattern starting from the center of an infinite chessboard. The knight makes its first move to one of the eight adjacent squares, then to the next outer ring, and so on, spiraling outward. If each move increases the distance from the center by one square, what is the number of moves required for the knight to reach a distance of 10 squares from the center? Assume the knight always makes a move in the shortest possible distance to the next square in the spiral.

Answer: `10`

## 0649 | score=0.556 | geometry

In a triangular array of squares, each square contains a fraction as follows: each row starts with the fraction \(\frac{1}{2}\) and each subsequent square in the row contains the sum of the fractions in the two squares directly above it. Find the fraction in the lowest square of a row that has 101 squares.

Answer: `\frac{1}{2^{100}}`

## 0650 | score=0.444 | geometry

In the hyperbolic plane, consider a regular polygon \( P \) with \( n \) sides, where \( n > 6 \). The polygon \( P \) is inscribed in a circle with radius \( R \). The area \( A \) of \( P \) can be expressed as \( A = \frac{nR^2}{2} \sin\left(\frac{2\pi}{n}\right) \). Now, imagine a similar polygon \( Q \) that is also regular, has \( 2n \) sides, and is inscribed in a circle with radius \( R \). Calculate the ratio of the area of \( P \) to the area of \( Q \), and simplify your answer as much as possible. Also, determine for which values of \( n \), the ratio of the areas will be an integer.

Answer: `\cos\left(\frac{\pi}{n}\right)`

## 0651 | score=0.444 | geometry

Find all positive integers \( n \) such that the expression
\[ n^4 + 4n^3 + 5n^2 + 4n + 1 \]
is a perfect square of an integer.

Answer: `1`

## 0652 | score=0.333 | combinatorics

Find the number of ways to arrange the letters in the word "MATHEMATICS" such that no two vowels are adjacent to each other.

Answer: `1058400`

## 0653 | score=0.333 | number_theory

What is the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n - 2x^{n-1} + 3x^{n-2} - \ldots + (-1)^n \cdot n \) has a root in the interval \( (0, 1) \)?

Answer: `3`

## 0654 | score=0.444 | number_theory

Let $p_n$ denote the $n$th prime number. Consider the sequence defined by $a_k = \frac{p_k + p_{k+1}}{2}$ for $k \geq 1$. Determine the smallest positive integer $n$ such that the product $\prod_{k=1}^{n} a_k$ is greater than $10^{100}$.

Answer: `100`

## 0655 | score=0.333 | number_theory

Find all positive integers \( n \) such that the equation
\[
\left\lfloor \frac{n}{10} \right\rfloor + \left\lfloor \frac{n}{100} \right\rfloor + \left\lfloor \frac{n}{1000} \right\rfloor = \frac{n}{9}
\]
has at least one solution.

(Note: \( \lfloor x \rfloor \) denotes the floor function, the greatest integer less than or equal to \( x \).)

Answer: `90`

## 0656 | score=0.333 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a continuous function satisfying the following functional equation:
\[ f(x + y) = f(x) \cdot f(y) + f(x) + f(y) + xy \]
for all real numbers \( x \) and \( y \). Find all possible values of \( f(2) \).

Answer: `-1`

## 0657 | score=0.444 | number_theory

Let \( P(x) \) be a polynomial of degree 5 with integer coefficients such that \( P(1) = 0 \) and \( P(2) = 1 \). Suppose there exists a positive integer \( n \) for which \( P(n) = 2n \). Determine the number of possible values of \( n \) that satisfy this condition.

Answer: `1`

## 0658 | score=0.667 | number_theory

In the finite field \(\mathbb{F}_{p}\), where \(p\) is a prime number, let \(P(x) = x^{p-1} - 1\). Define the set \(S = \{P(0), P(1), \ldots, P(p-2)\}\). Determine the number of distinct elements in \(S\), denoted as \(|S|\).

Answer: `2`

## 0659 | score=0.667 | number_theory

Find the smallest positive integer $n$ such that there exists a sequence of positive integers $b_1, b_2, \ldots, b_n$ satisfying the following conditions:
1. $b_1 = 1$,
2. $b_n = 2023$,
3. For each $i$ from 1 to $n-1$, $b_{i+1} = b_i + d$ for some positive integer $d$ such that $d$ is a divisor of $b_i$ and $d < b_i$.

Answer: `2023`

## 0660 | score=0.667 | algebra

Let \( P(x) \) be a polynomial of degree 5 with real coefficients such that \( P(1) = 10 \), \( P(2) = 20 \), \( P(3) = 30 \), \( P(4) = 40 \), and \( P(5) = 50 \). Additionally, \( P(x) \) has a double root at \( x = 6 \). Find the value of \( P(6) \).

Answer: `60`

## 0661 | score=0.667 | number_theory

There is a sequence of integers defined as follows: \( a_1 = 1 \), and for all \( n \geq 2 \), \( a_n = a_{n-1} + n^2 \). Let \( S = \{ a_1, a_2, a_3, \ldots, a_{20} \} \). Find the largest integer \( k \) such that \( k \) divides the sum of all elements in \( S \).

Answer: `16170`

## 0662 | score=0.333 | geometry

Find all positive integers \( n \) such that \( 2^n + 3^n \) is a perfect square.

Answer: `0`

## 0663 | score=0.333 | geometry

Consider a regular hexagon ABCDEF inscribed in a circle with radius \( R \). Point \( P \) is selected at random inside the hexagon. The distances from \( P \) to sides \( AB \), \( BC \), \( CD \), \( DE \), \( EF \), and \( FA \) are denoted as \( d_1, d_2, d_3, d_4, d_5, \) and \( d_6 \) respectively. What is the expected value of the sum \( d_1 + d_2 + d_3 + d_4 + d_5 + d_6 \)?

Answer: `3\sqrt{3} R`

## 0664 | score=0.444 | geometry

Let \( ABCD \) be a cyclic quadrilateral inscribed in a circle with radius \( R \). The diagonals \( AC \) and \( BD \) intersect at point \( P \). Given that \( AB = 7 \), \( BC = 8 \), \( CD = 9 \), and \( DA = 10 \), find the value of \( R \) if the area of \( \triangle APB \) is equal to the area of \( \triangle CPD \).

Answer: `5`

## 0665 | score=0.778 | number_theory

Find the number of positive integers $n$ such that the equation $n^2 + 15n + 56 = x^3$ has a solution in positive integers $x$.

Answer: `0`

## 0666 | score=0.556 | geometry

Consider a sequence of positive integers \( a_1, a_2, a_3, \ldots, a_n \) such that each term after the first is the sum of the squares of the digits of the previous term. For example, if \( a_1 = 29 \), then \( a_2 = 2^2 + 9^2 = 85 \), \( a_3 = 8^2 + 5^2 = 89 \), and so on. Determine the smallest positive integer \( a_1 \) for which the sequence eventually enters a cycle that includes the number 145. That is, find \( a_1 \) such that for some \( k \), \( a_k = 145 \), and after this, the sequence repeats a cycle that includes 145.

Answer: `2`

## 0667 | score=0.667 | geometry

Given the polynomial equation \(P(x) = x^5 - 5x^4 + 10x^3 - 10x^2 + 5x - 1\), let \(\alpha, \beta, \gamma, \delta,\) and \(\epsilon\) be its roots. If the sum of the squares of the differences of these roots taken two at a time is 40, find the value of \(\alpha^3 + \beta^3 + \gamma^3 + \delta^3 + \epsilon^3\).

Answer: `5`

## 0668 | score=0.556 | algebra

In the complex plane, consider a regular hexagon \(ABCDEF\) centered at the origin with vertices at the \(k\)-th roots of unity. Let \(P\) be a point inside the hexagon such that \(P\) is equidistant from two adjacent vertices, say \(A\) and \(B\). If \(P\) can be expressed as \(\frac{z_1 + z_2}{2}\) where \(z_1\) and \(z_2\) are complex numbers representing points on the hexagon, find the number of possible values for \(z_1\) and \(z_2\) such that \(P\) remains inside the hexagon.

Answer: `6`

## 0669 | score=0.556 | number_theory

Let $p(x)$ be a polynomial with integer coefficients such that $p(1) = 2$ and $p(2) = 3$. If $p(0) = 0$ and $p(3) = 12$, determine the smallest possible degree of $p(x)$.

Additionally, prove that for any positive integer $n$, the polynomial $q(x) = p(x) - x^n$ has at least one real root.

Answer: `3`

## 0670 | score=0.444 | number_theory

In a finite field \( \mathbb{F}_{p} \) of prime order \( p \), let \( f(x) = x^{p-1} - 1 \) be a polynomial. Given that \( a, b, c \in \mathbb{F}_{p} \) are distinct elements and \( f(a) = f(b) = f(c) = 0 \), determine the number of possible triples \( (a, b, c) \) such that \( a + b + c = 0 \) modulo \( p \).

Answer: `(p-1)(p-2)`

## 0671 | score=0.778 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that the product of the digits of \( n \) equals \( \frac{1}{2}n \). For example, 22 is in \( S \) because \( 2 \times 2 = \frac{1}{2} \times 22 \). How many elements are in \( S \)?

Answer: `1`

## 0672 | score=0.667 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that the sum of the digits of \( n \) is equal to the sum of the digits of \( 10n \). Find the number of elements in \( S \) that are less than 1000.

Answer: `999`

## 0673 | score=0.333 | number_theory

Consider a sequence of positive integers \(a_n\) defined by \(a_1 = 1\) and for \(n \geq 2\),
\[a_n = a_{\lfloor \frac{n}{2} \rfloor} + a_{\lfloor \frac{n}{3} \rfloor} + a_{\lfloor \frac{n}{4} \rfloor} + a_{\lfloor \frac{n}{6} \rfloor}.\]
What is the smallest positive integer \(k\) such that \(a_k = 2023\)?

Answer: `2023`

## 0674 | score=0.333 | combinatorics

Determine the number of ways to color the vertices of a regular octahedron with three colors, red, blue, and green, such that no two adjacent vertices share the same color. Additionally, rotations of the octahedron that result in the same coloring pattern should be considered identical.

Answer: `2`

## 0675 | score=0.333 | number_theory

Find all positive integers \( n \) such that \( n \) divides the sum \( 1^{20} + 2^{20} + 3^{20} + \cdots + n^{20} \).

Answer: `1`

## 0676 | score=0.333 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that \( n \) can be expressed in the form
\[ n = a^2 + b^2 + c^2 + d^2 \]
where \( a, b, c, \) and \( d \) are positive integers satisfying \( a + b + c + d = n \). Determine the largest possible value of \( n \) that belongs to \( S \) and can be represented in this form using each positive integer from 1 to 8 exactly once.

Answer: `36`

## 0677 | score=0.333 | number_theory

Determine the sum of all positive integers \( n \) for which the polynomial \( P(x) = x^4 - (2n+1)x^2 + n^2 \) has four distinct real roots.

Answer: `\infty`

## 0678 | score=0.333 | geometry

Let $ABC$ be an acute triangle with circumcircle $\omega$. Let $D$ be the foot of the altitude from $A$ to $BC$, and let $P$ be a point on $\omega$ such that $PD$ is perpendicular to $BC$. If the area of triangle $ABC$ is $60$ square units and $BC = 20$ units, find the length of $AD$.

Additionally, determine the ratio of the area of triangle $APD$ to the area of triangle $ABC$.

Answer: `\frac{1}{2}`

## 0679 | score=0.778 | algebra

Let $A$ be an $n \times n$ matrix where $n \geq 3$ and every entry $a_{ij}$ is either 1 or -1. If the determinant of $A$ is non-zero, prove that the sum of the absolute values of all entries in $A$ is at least $n^2$.

Answer: `n^2`

## 0680 | score=0.444 | number_theory

Let \( P(x) \) be a polynomial of degree \( n \) with integer coefficients such that \( P(0) = 1 \), and \( P(1) = P(2) = \cdots = P(n) = 0 \). Determine the smallest possible positive value of \( n \) such that \( P(n+1) \) is divisible by \( n \).

Answer: `1`

## 0681 | score=0.444 | number_theory

Let \( f: \mathbb{Z} \to \mathbb{Z} \) be a function satisfying the following conditions:
1. \( f(n) + f(n+1) = f(n+2) \) for all integers \( n \).
2. \( f(0) = 0 \) and \( f(1) = 1 \).
3. \( f \) is multiplicative in the sense that \( f(mn) = f(m)f(n) \) for all coprime integers \( m \) and \( n \).

Find the value of \( f(2023) \).

Answer: `2023`

## 0682 | score=0.556 | combinatorics

You have a deck of \(n\) distinct cards numbered from 1 to \(n\). You shuffle the deck and lay out the cards in a row. What is the probability that no card is in its original position (i.e., no card is in the position that matches its number)? For example, if \(n = 3\), the valid arrangements are (2, 3, 1) and (3, 1, 2). Express your answer as a fraction in lowest terms.

Answer: `\sum_{k=0}^{n} \frac{(-1)^k}{k!}`

## 0683 | score=0.778 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that \( \sqrt{n} + \sqrt{n+1} < 10 \). Find the sum of all elements in \( S \).

Answer: `300`

## 0684 | score=0.444 | number_theory

Let \( S \) be a set of integers such that every non-empty subset of \( S \) has a median that is an integer. Given that \( S \) contains exactly 10 elements, determine the number of distinct possible sets \( S \).

Answer: `1`

## 0685 | score=0.556 | number_theory

AIME_2021_P6
Let [math]S[/math] be the set of all positive integer divisors of [math]100,000.[/math] How many numbers are the product of two distinct elements of [math]S?[/math]

Answer: `630`

## 0686 | score=0.444 | number_theory

Find all triples of positive integers $(a, b, c)$ such that $a^2 + b^2 + c^2 = 2023$ and $a + b + c = 80$. Determine the number of distinct solutions for $(a, b, c)$.

Answer: `0`

## 0687 | score=0.667 | number_theory

A sequence of positive integers \(a_1, a_2, a_3, \ldots\) is defined recursively by the following conditions: \(a_1 = 1\), \(a_2 = 2\), and for \(n \geq 3\), \(a_n\) is the smallest positive integer that does not divide any of the previous terms in the sequence. Find the value of \(a_{100}\).

Answer: `100`

## 0688 | score=0.667 | number_theory

What is the sum of all positive integers \( n \) such that \(\dfrac{n}{125}\) is a fifth power of an integer and \(\dfrac{5n}{125}\) is the cube of an integer?

Answer: `390625`

## 0689 | score=0.556 | geometry

In a triangular park ABC, the sides measure 13 meters, 14 meters, and 15 meters. A fountain is to be placed at a point P inside the park such that the sum of the squares of the distances from P to the vertices A, B, and C is minimized. Determine the coordinates of P in terms of the Cartesian coordinate system where A is at the origin (0, 0), B is at (14, 0), and C lies on the y-axis at (0, y) where y is positive. The answer should be in the simplest form.

Answer: `\left( \frac{14}{3}, \frac{y}{3} \right)`

## 0690 | score=0.667 | geometry

Given the polynomial \( P(x) = x^4 - 4x^3 + 6x^2 - 4x + 1 \), determine the sum of the squares of all real roots of the polynomial \( Q(x) = P(x)P(-x) - P(x^2) \).

Answer: `0`

## 0691 | score=0.556 | geometry

Let \( ABC \) be a triangle with circumradius \( R \). The incircle of \( \triangle ABC \) touches \( BC \) at \( D \), \( CA \) at \( E \), and \( AB \) at \( F \). Let \( I \) be the incenter of \( \triangle ABC \). Points \( P \) and \( Q \) are chosen on \( AD \), \( BE \), and \( CF \) respectively such that \( AP = BQ = CR \). Find the maximum possible value of \( |PQ|^2 \) in terms of \( R \), where \( |PQ| \) denotes the distance between points \( P \) and \( Q \).

Answer: `4R^2`

## 0692 | score=0.444 | number_theory

Determine the smallest positive integer \( n \) for which the expression \( 3^n + 1 \) is divisible by 2019.

Answer: `336`

## 0693 | score=0.556 | other

In a convex quadrilateral ABCD, point E lies on AD such that BE is perpendicular to AD. Let P be the intersection of AC and BE. If AB = 13, BC = 14, CD = 15, and DA = 16, find the length of BP.

Answer: `12`

## 0694 | score=0.667 | number_theory

Find all pairs of positive integers (a, b) such that a^2 + b^2 is a prime number and a + b is the smallest positive integer that satisfies this condition.

Answer: `(1, 1)`

## 0695 | score=0.444 | number_theory

Let \( a, b, c, d \) be positive integers such that \( a^2 + b^2 + c^2 + d^2 = 1234 \). If \( ab + ac + ad + bc + bd + cd = 100 \), find the sum \( a + b + c + d \).

Answer: `38`

## 0696 | score=0.778 | number_theory

In a sequence of positive integers \( a_1, a_2, a_3, \ldots \), each term \( a_n \) is defined as the smallest integer greater than \( a_{n-1} \) that is not relatively prime to any of the previous terms. Given that \( a_1 = 2 \), find the smallest integer \( k \) such that \( a_k \) is a multiple of 6.

Answer: `3`

## 0697 | score=0.444 | geometry

Find the smallest positive integer \( n \) such that the sum of the squares of the first \( n \) odd positive integers is equal to the sum of the squares of the next \( n \) even positive integers.

Answer: `7`

## 0698 | score=0.667 | number_theory

Let \( S \) be the set of all non-empty subsets of \(\{1, 2, 3, \ldots, 10\}\). For each subset \( A \in S \), define the function \( f(A) \) as the product of all elements in \( A \). Determine the remainder when the sum of all values of \( f(A) \) for \( A \in S \) is divided by 11.

Answer: `0`

## 0699 | score=0.333 | geometry

A rectangular garden has a length that is twice its width. A path of uniform width surrounds the garden, increasing both the length and width by the same amount. If the area of the garden plus the path is twice the area of the garden alone, what is the ratio of the width of the path to the width of the garden?

Answer: `\frac{\sqrt{17} - 3}{4}`

## 0700 | score=0.778 | algebra

Let \( f(x) \) be a polynomial of degree 3 such that \( f(0) = 0 \), \( f(1) = 1 \), and \( f(2) = 8 \). Find the number of distinct real roots of the equation \( f(f(x)) = x \).

Answer: `3`

## 0701 | score=0.556 | algebra

In the complex plane, let \( z \) be a complex number such that \( |z| = 1 \). Define \( w = z^3 + \frac{1}{z^3} \). If \( w \) is a real number, find the number of possible values for \( w \).

Answer: `\infty`

## 0702 | score=0.667 | number_theory

Find all positive integers \( n \) such that there exists a positive integer \( k \) for which the sum of the digits of \( k \) is equal to \( n \) and the sum of the digits of \( k^2 \) is also equal to \( n \). Determine the smallest such \( n \) and provide a proof of your solution.

Answer: `1`

## 0703 | score=0.444 | geometry

Consider a regular nonagon (9-sided polygon) inscribed in a circle of radius 1. Find the sum of the lengths of all the diagonals that can be drawn from a single vertex. Express your answer in simplest radical form.

Answer: `9`

## 0704 | score=0.444 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + a_{n-1}x^{n-1} + \cdots + a_1x + a_0 \) with integer coefficients satisfies \( P(100) = 100 \) and \( P(200) = 200 \).

Answer: `2`

## 0705 | score=0.444 | number_theory

Consider a sequence of complex numbers \( z_1, z_2, \ldots, z_n \) where \( z_i = a_i + b_i i \) and \( a_i, b_i \in \mathbb{Z} \). Define the transformation \( T(z) = z^2 + c \) where \( c \) is a complex constant. Suppose there exists a positive integer \( n \) such that after \( n \) iterations of \( T \) starting from any \( z_1 \in \mathbb{C} \), the sequence eventually enters a cycle of length 4. Find the smallest possible value of \( n \) for which this is possible.

Answer: `4`

## 0706 | score=0.444 | number_theory

In the complex plane, let \( z_1 \) and \( z_2 \) be the roots of the equation \( z^2 - (1 + i)z + 2 = 0 \). Define the sequence \( \{z_n\} \) by \( z_1 = z_1 \), \( z_2 = z_2 \), and \( z_{n+2} = z_{n+1} + z_n \) for all \( n \geq 1 \). Find the smallest positive integer \( k \) such that \( |z_k| \) is an integer.

Answer: `5`

## 0707 | score=0.333 | geometry

Let $ABC$ be a triangle with side lengths $AB = 13$, $BC = 14$, and $CA = 15$. A circle is inscribed in triangle $ABC$, touching $BC$ at $D$, $CA$ at $E$, and $AB$ at $F$. Let $G$ be the midpoint of $AD$. Find the area of quadrilateral $BEGF$.

Answer: `28`

## 0708 | score=0.444 | number_theory

Find all triples of positive integers \((x, y, z)\) such that \(x^3 + y^3 + z^3 = 3xyz + 3\).

Answer: `(1, 1, 1)`

## 0709 | score=0.444 | geometry

Find the smallest positive integer \( n \) such that the product \( 1575 \cdot n \) is a perfect square and \( n \) is a perfect cube.

Answer: `343`

## 0710 | score=0.333 | number_theory

Find all pairs of positive integers \((a, b)\) such that the equation \(a^2 + b^2 = 5ab + 1\) holds.

Answer: `(1, 5), (5, 1)`

## 0711 | score=0.778 | number_theory

What is the smallest positive integer \( n \) such that \( n! \) (n factorial) ends in exactly 24 zeros?

Answer: `100`

## 0712 | score=0.333 | geometry

Let \( S \) be the set of all positive integers \( n \) such that the sum of the squares of the first \( n \) positive integers is divisible by \( n \). Find the number of elements in the set \( S \) that are less than or equal to \( 1000 \).

\[
S = \{ n \in \mathbb{Z}^+ : \sum_{k=1}^{n} k^2 \text{ is divisible by } n \}
\]

Answer: `166`

## 0713 | score=0.444 | number_theory

A polynomial \( P(x) \) with integer coefficients satisfies \( P(1) = 1234 \) and \( P(2) = 2345 \). What is the minimum possible positive value of \( P(0) \)?

Answer: `123`

## 0714 | score=0.667 | geometry

Let \( ABCD \) be a convex quadrilateral with \( AB = a \), \( BC = b \), \( CD = c \), and \( DA = d \). Suppose that the diagonals \( AC \) and \( BD \) intersect at point \( E \), and that the length of \( AC \) is \( m \) and the length of \( BD \) is \( n \). Given that \( AE \cdot EC = BE \cdot ED \) and that the area of triangle \( ABE \) is \( k \), determine the area of the quadrilateral \( ABCD \) in terms of \( a, b, c, d, m, n, \) and \( k \).

Answer: `2k`

## 0715 | score=0.667 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + ax^{n-1} + bx^{n-2} + \cdots + kx + l \) with integer coefficients and roots \( \alpha, \beta, \gamma \) satisfies \( \alpha + \beta + \gamma = 3 \), \( \alpha^2 + \beta^2 + \gamma^2 = 9 \), and \( \alpha^3 + \beta^3 + \gamma^3 = 27 \).

Answer: `3`

## 0716 | score=0.556 | number_theory

Find all positive integers $n$ such that the product of their digits is equal to $n^2 - 10n - 22$.

Answer: `12`

## 0717 | score=0.556 | number_theory

Let \( f(x) \) be a polynomial with integer coefficients such that \( f(1) = 2023 \) and \( f(2023) = 1 \). If \( p \) is a prime number that divides \( f(2024) \), find the smallest possible value of \( p \).

Answer: `7`

## 0718 | score=0.333 | geometry

在正方形 $ABCD$ 内部取一点 $P$，使得 $\angle APB = \angle BPC = \angle CPA = 120^\circ$。设 $AB = 1$，求 $\triangle APB$ 的面积。

Answer: `\frac{\sqrt{3}}{4}`

## 0719 | score=0.333 | number_theory

Let \( f: \mathbb{Z} \to \mathbb{Z} \) be a function satisfying the following properties:
1. For all integers \( x \) and \( y \), \( f(xy) = f(x)f(y) \).
2. \( f(x+y) = f(x) + f(y) + 2024 \) for all integers \( x \) and \( y \).

Determine the value of \( f(2024) \).

Answer: `-2024`

## 0720 | score=0.778 | geometry

Let \( f: \mathbb{Z} \to \mathbb{Z} \) be a function defined by \( f(n) = n^3 - 3n^2 + 2n \). Determine all integers \( n \) such that \( f(n) \) is a perfect square.

Answer: `0, 1, 2`

## 0721 | score=0.444 | number_theory

Find all positive integers \( n \) such that \( n \cdot \phi(n) = p^k \), where \( p \) is a prime number and \( k \) is a positive integer.

Answer: `2`

## 0722 | score=0.556 | algebra

In a small town, there is a peculiar tradition where every year, on the first day of summer, the mayor throws a party. This year, the mayor decides to create a unique guest list. The guest list is determined by a special algorithm: if a person is invited, every person who is directly connected to them on a social graph (meaning they have interacted with them at least once) is also invited. However, to keep the party size manageable, the mayor adds a twist: if a person is invited more than once, they will only be counted once in the final guest list. 

Given a list of people (let's call them nodes) and their connections (edges), can you determine the final size of the guest list at the mayor's party? Specifically, how many unique people will be invited if the algorithm is applied? 

To solve this, you need to know the following information:
- The number of people (n) in the town.
- A list of (m) direct connections between people.
- The mayor's starting point (the first person who will be invited).

For example, if there are 5 people in the town (1, 2, 3, 4, 5) and the direct connections are [(1, 2), (2, 3), (3, 4), (4, 5), (5, 1)], and the mayor starts with person 1, the guest list would be all 5 people because each person is connected to the next person in the cycle.

You need to write a function that takes in the number of people, the list of connections, and the starting person, and returns the size of the final guest list.

Answer: `5`

## 0723 | score=0.667 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(0) = 0 \), \( P(1) = 1 \), and for every prime \( p \), \( P(p) \equiv 0 \pmod{p} \). Determine the number of distinct polynomials \( P(x) \) satisfying these conditions.

Answer: `1`

## 0724 | score=0.778 | combinatorics

There are 12 different books arranged on a shelf. In how many ways can we choose three books such that no two of them are consecutive?

Answer: `120`

## 0725 | score=0.556 | algebra

Let $a, b, c$ be positive real numbers such that $a + b + c = 1$. Determine the maximum value of the expression $(a - b)^2 + (b - c)^2 + (c - a)^2$.

Answer: `2`

## 0726 | score=0.667 | number_theory

Find the smallest positive integer \( n \) such that \( n \) is a multiple of 3, \( n+1 \) is a multiple of 4, \( n+2 \) is a multiple of 5, and \( n+3 \) is a multiple of 6.

Answer: `3`

## 0727 | score=0.444 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(1) = 2 \), \( P(2) = 4 \), and \( P(3) = 10 \). Given that \( P(x) \) has degree at least 3, determine the smallest possible degree of \( P(x) \) and find \( P(0) \).

Answer: `-2`

## 0728 | score=0.778 | algebra

Find all real numbers \( x \) and \( y \) such that \( x^3 + y^3 = x - y \) and \( x^2y + xy^2 = 0 \).

Answer: `(0, 0), (1, 0), (-1, 0)`

## 0729 | score=0.667 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + nx^{n-1} + n(n-1)x^{n-2} + \cdots + n! \) has exactly one real root. Prove your answer.

Answer: `1`

## 0730 | score=0.778 | geometry

Find the number of distinct polynomials \( P(x) \) with real coefficients that satisfy the following conditions:
1. \( P(x) \) has degree 3.
2. \( P(x) \) has three real roots, one of which is \( 2 \).
3. The sum of the squares of the roots of \( P(x) \) is \( 18 \).
4. \( P(1) = 6 \).

Answer: `2`

## 0731 | score=0.556 | geometry

In the coordinate plane, consider a square \(ABCD\) with vertices \(A(0, 0)\), \(B(a, 0)\), \(C(a, a)\), and \(D(0, a)\), where \(a > 0\). A point \(P(x, y)\) is chosen inside the square such that the distances from \(P\) to the sides of the square are equal. Find the value of \(a\) if the coordinates of \(P\) satisfy the equation \(x^2 + y^2 = 10x + 6y + 10\).

Answer: `8 + 2\sqrt{21}`

## 0732 | score=0.333 | geometry

Let $f(x) = x^4 - 6x^3 + 13x^2 - 12x + 4$. Define $S$ as the set of all positive integers $n$ such that $f(n)$ is a perfect square. Find the sum of all elements in $S$.

Answer: `10`

## 0733 | score=0.333 | algebra

Find the coefficient of \(x^{10}\) in the expansion of \((1 + x + x^2 + \cdots + x^{10})(1 + x + x^2 + \cdots + x^5)^2.\)

Answer: `36`

## 0734 | score=0.444 | geometry

A regular pentagon and a regular hexagon share a common side. Find the measure of the interior angle at the vertex where the two polygons meet, expressed in degrees.

Answer: `132^\circ`

## 0735 | score=0.444 | number_theory

Find all integers \( n \) for which there exists an integer \( m \) such that \( n^2 + 3n + 2 = m^3 - m \).

Answer: `-2, -1, 1`

## 0736 | score=0.556 | other

In a magical realm, there are three types of mystical trees: Silver, Golden, and Emerald. Each type of tree has a unique number of leaves on its branches. The total number of leaves on a Silver tree is 5 times the number of leaves on a Golden tree plus 10. The total number of leaves on a Golden tree is 3 times the number of leaves on an Emerald tree plus 5. If the combined total of leaves on one Silver tree, one Golden tree, and one Emerald tree is 79, find the number of leaves on a Golden tree.

Answer: `11`

## 0737 | score=0.556 | algebra

Let \( P(x) \) be a polynomial of degree 3 with real coefficients such that \( P(x) = x^3 - ax^2 + bx - c \) and \( P(1) = P(2) = 0 \). Find the value of \( a + b + c \).

Answer: `5`

## 0738 | score=0.667 | number_theory

Let \( f(x) \) be a polynomial of degree 3 such that \( f(x) = ax^3 + bx^2 + cx + d \), where \( a \), \( b \), \( c \), and \( d \) are integers. It is known that \( f(1) = 10 \), \( f(2) = 20 \), \( f(3) = 30 \), and \( f(4) = 40 \). Determine the value of \( f(5) \).

Answer: `50`

## 0739 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that \( 2^n + 3^n + 5^n \) is divisible by 11.

Hints:
1. Consider the modular behavior of \( 2^n, 3^n, \) and \( 5^n \) modulo 11.
2. Look for patterns in the units digits of these powers modulo 11.

Answer: `5`

## 0740 | score=0.444 | number_theory

Find the number of ordered triples $(a, b, c)$ of positive integers such that $a^2 + b^2 + c^2 = 2023$, and $a < b < c$.

Answer: `0`

## 0741 | score=0.778 | algebra

Let $a$, $b$, and $c$ be positive real numbers such that $a + b + c = 1$ and $a \geq b \geq c$. Find the minimum value of \[ S = \frac{a^2}{b+c} + \frac{b^2}{a+c} + \frac{c^2}{a+b}. \]

Answer: `\frac{1}{2}`

## 0742 | score=0.333 | number_theory

Consider a sequence of positive integers \( a_1, a_2, \ldots, a_{10} \) such that each term is either a prime number or the product of two distinct prime numbers. If the sum of the first five terms is 100, and the sum of the last five terms is 110, determine the minimum possible value of \( a_6 \).

Given the constraints:
1. Each \( a_i \) is a prime number or the product of two distinct prime numbers.
2. \( a_1 + a_2 + a_3 + a_4 + a_5 = 100 \).
3. \( a_6 + a_7 + a_8 + a_9 + a_{10} = 110 \).

What is the smallest possible value of \( a_6 \)?

Answer: `2`

## 0743 | score=0.333 | number_theory

Let \( f: \mathbb{Z} \rightarrow \mathbb{Z} \) be a function satisfying \( f(n + 1) = f(n) + 3 \) and \( f(n^2 + 1) = f(n)^2 + 1 \) for all integers \( n \). Find the value of \( f(100) \).

Answer: `300`

## 0744 | score=0.556 | geometry

Let \( f(n) \) be a function defined on the positive integers such that \( f(n) = n^2 + 2023n + 1234 \). Find the number of positive integers \( n \leq 1000 \) for which \( f(n) \) is a perfect square.

Answer: `0`

## 0745 | score=0.333 | number_theory

Let $P(x) = x^3 - 3x + 1$. Define the sequence $(a_n)$ by $a_1 = 2$ and $a_{n+1} = P(a_n)$ for all $n \geq 1$. Find the smallest positive integer $n$ such that $a_n$ is divisible by $10$.

Answer: `10`

## 0746 | score=0.333 | algebra

Let \( f(x) \) be a function defined on the interval \([0, 1]\) such that \( f(0) = 0 \) and for all \( x \) in \([0, 1]\), \( f(x) \) satisfies the differential equation \( f'(x) = x^2 + f(x)^2 \). Determine the value of \( f(1) \).

Answer: `1`

## 0747 | score=0.556 | number_theory

Let \( S \) be the set of all positive integers less than 2024. Define a function \( f : S \to S \) such that for any \( n \in S \), \( f(n) \) is the smallest positive integer that can be expressed as the sum of \( n \) distinct positive integers. Determine the number of distinct integers in the set \( \{ f(n) \mid n \in S \} \).

Answer: `2023`

## 0748 | score=0.444 | geometry

A convex polygon \(P\) with \(n\) sides has a special property: every interior angle of \(P\) is either \(120^\circ\) or \(150^\circ\). Furthermore, there are exactly \(k\) angles of \(150^\circ\) in \(P\). Determine the maximum possible value of \(n\) in terms of \(k\), assuming \(k < \frac{n}{2}\) and \(n\) is a positive integer.

Answer: `n = 7`

## 0749 | score=0.444 | number_theory

Find all positive integers \( n \) such that the number \( 12^n - 1 \) is divisible by \( n^2 \).

Answer: `1`

## 0750 | score=0.444 | number_theory

Find all pairs of positive integers \((a, b)\) such that \(a^b + b^a = 100\).

Answer: `(1, 99), (2, 6)`

## 0751 | score=0.556 | geometry

Let \( S \) be the set of all positive integers that can be expressed as the sum of distinct powers of 3. Define \( f(n) \) as the number of elements in the set \( S \) that are less than or equal to \( n \). For instance, \( f(9) = 3 \) because the elements of \( S \) less than or equal to 9 are \( 1, 3, \) and \( 9 \). Determine the smallest positive integer \( n \) such that \( f(n) \) is a perfect square and \( n \) is also a perfect square.

Answer: `9`

## 0752 | score=0.556 | geometry

A square garden has side length \(10\) meters. Each side of the garden is bordered by a fence that is \(1\) meter high, running \(1\) meter wide. What is the total length of the fencing used around the garden including the strips running along the sides, and what is the area of the garden excluding the strips of fencing?

Answer: `64`

## 0753 | score=0.333 | geometry

A positive integer \( n \) is chosen such that \( n^2 + 2019n + 2020 \) is a perfect square. Find all possible values of \( n \).

Answer: `2019`

## 0754 | score=0.444 | number_theory

Let $P(x) = x^3 - 3x^2 + 2x + 1$ be a polynomial with real coefficients. Suppose that $r_1, r_2,$ and $r_3$ are the roots of $P(x)$. Define $S_n = r_1^n + r_2^n + r_3^n$ for all positive integers $n$. Find the value of $S_6 + S_5 - 2S_4$.

Answer: `-34`

## 0755 | score=0.333 | number_theory

Find all positive integers \( n \) such that the equation \( n^2 + n + 1 = m^3 \) has integer solutions for \( m \).

Answer: `0`

## 0756 | score=0.667 | geometry

Find all positive integers \( n \) such that there exists a positive integer \( k \) for which \( n^k + n - 1 \) is a perfect square.

Answer: `1`

## 0757 | score=0.333 | number_theory

Find all positive integers \( n \) such that \( n \) divides the sum \( S_n = \sum_{k=1}^{n} k^2 \cdot 2^k \).

Answer: `1, 2, 3`

## 0758 | score=0.778 | geometry

In the complex plane, consider a set of points \( P \) that satisfy the equation \[ \left| z - \frac{1}{z} \right| = 1 \] for some complex number \( z \). If we let \( P \) be the region of all points that lie on the boundary of the circle centered at the origin with radius 1, or on the boundary of the circle centered at the origin with radius 2, what is the area of the region formed by the intersection of these two circles?

Given that the area of the region formed by the intersection of the two circles is \(\pi\sqrt{3}\), find the value of the smallest positive integer \( n \) such that \( n \) divides this area.

Answer: `1`

## 0759 | score=0.667 | number_theory

Find all triples of integers $(x, y, z)$ such that $x^2 + y^2 + z^2 = 2xyz + 1$ and $x, y, z \geq 1$.

Answer: `(1, 1, 1)`

## 0760 | score=0.667 | geometry

Let \( f: \mathbb{Z} \to \mathbb{Z} \) be a function defined by \( f(n) = n^3 - 3n^2 + 3n - 1 \). Determine all integers \( n \) such that \( f(n) \) is a perfect square.

Answer: `m^2 + 1`

## 0761 | score=0.444 | other

在一个正六边形中，从中心点向六个顶点分别画线，将正六边形分割成若干个等边三角形。现在，假设我们随机选取三个顶点，求这三个点中恰好有两个点是相邻顶点的概率是多少？

Answer: `\frac{3}{5}`

## 0762 | score=0.333 | algebra

Let $f(x) = x^3 - 3x + 1$. Find the number of distinct real roots of the equation $f(f(f(x))) = 0$.

Answer: `9`

## 0763 | score=0.333 | number_theory

What is the smallest positive integer \( n \) such that the sum of the first \( n \) terms of the sequence defined by \( a_k = \frac{1}{k(k+1)(k+2)} \) for \( k = 1, 2, 3, \ldots, n \) is greater than \( \frac{1}{4} \)?

Answer: `2`

## 0764 | score=0.444 | geometry

In the realm of non-Euclidean geometry, consider a spherical triangle with angles α, β, and γ, where α + β + γ = 2π/3. Prove that the area of this spherical triangle, measured in steradians, is equal to the product of its three angles divided by π.

Answer: `\frac{\alpha \beta \gamma}{\pi}`

## 0765 | score=0.444 | number_theory

Find all positive integers \( n \) such that there exist positive integers \( a_1, a_2, \ldots, a_n \) satisfying the equation
\[ a_1^2 + a_2^2 + \cdots + a_n^2 = (a_1 + a_2 + \cdots + a_n)^2. \]
Additionally, determine the minimal number of terms required to satisfy this equation if \( n \) is even.

Answer: `1`

## 0766 | score=0.333 | number_theory

Let $f(x)$ be a polynomial with integer coefficients such that $f(1) = 2021$ and $f(2021) = 2022$. Find the maximum possible value of $f(0)$.

Answer: `2021`

## 0767 | score=0.333 | algebra

Let \( f: \mathbb{R}^2 \to \mathbb{R} \) be a continuous function such that for all \( (x, y) \in \mathbb{R}^2 \), the following condition holds:

\[ f(x + y, f(x, y)) = f(x, y) + 2xy. \]

Moreover, assume that \( f \) is differentiable at the origin with \( f(0, 0) = 0 \). Determine the general form of the function \( f(x, y) \).

Answer: `xy`

## 0768 | score=0.444 | number_theory

Find all pairs of positive integers \((a, b)\) such that both \(a^3 + 3b^3\) and \(b^3 + 3a^3\) are perfect cubes.

Answer: `(1, 1)`

## 0769 | score=0.333 | number_theory

Find all integer solutions $(x, y)$ to the equation $x^2 + 4y^2 - 4xy - 16 = 0$ such that $x^2 + y^2 < 100$.

Answer: `(-6, -5), (-4, -4), (-2, -3), (0, -2), (2, -1), (4, 0), (6, 1), (8, 2), (-8, -2), (-6, -1), (-4, 0), (-2, 1), (0, 2), (2, 3), (4, 4), (6, 5)`

## 0770 | score=0.333 | number_theory

Find all positive integers \( n \) and \( k \) such that \( n^2 + 3^n \equiv k^2 \pmod{2^n} \) and \( n^2 + 3^n + k^2 \) is divisible by \( 2^{n+1} \).

Answer: `(1, 2)`

## 0771 | score=0.556 | geometry

Find the radius of the seventh circle that is tangent to six circles of radius \(r\) arranged in a circle, each tangent to its neighbors.

Answer: `r`

## 0772 | score=0.556 | combinatorics

What is the minimum number of colors required to color all the vertices of a regular dodecahedron such that no two adjacent vertices share the same color? Consider that each face of the dodecahedron is a regular pentagon, and every vertex is connected to three others.

Answer: `3`

## 0773 | score=0.333 | geometry

In the complex plane, let $A$ be the point corresponding to $3+4i$ and $B$ the point corresponding to $1-2i$. Define the set $S$ as the set of all complex numbers $z$ such that $z$ can be expressed in the form $z = \alpha A + \beta B$ where $\alpha$ and $\beta$ are complex numbers satisfying $|\alpha| + |\beta| = 1$. Determine the area of the region enclosed by the boundary formed by $S$ in the complex plane.

Answer: `20`

## 0774 | score=0.333 | other

Given a regular hexagon with side length 1, let \( P \) be a point inside the hexagon such that the distances from \( P \) to three consecutive vertices \( A, B, \) and \( C \) are \( a, b, \) and \( c \) respectively. Find the maximum possible value of \( a^2 + b^2 + c^2 \).

Answer: `3`

## 0775 | score=0.444 | number_theory

Let $a$, $b$, and $c$ be positive integers such that $a \leq b \leq c$ and $a + b + c = 2021$. Consider the polynomial $P(x) = x^3 - 3x^2 + bx + a$ which has three distinct integer roots $r_1, r_2,$ and $r_3$. Find the sum of all possible values of $c$.

Answer: `2019`

## 0776 | score=0.444 | geometry

In the coordinate plane, let \( P \) be a point chosen uniformly at random from the interior of the unit square with vertices at \((0,0)\), \((1,0)\), \((1,1)\), and \((0,1)\). Let \( Q \) be the point on the line segment from \((1,0)\) to \((0,1)\) such that \( PQ \) is perpendicular to the line segment. Find the probability that the distance between \( P \) and \( Q \) is less than \(\frac{1}{2}\).

Answer: `\frac{1}{2}`

## 0777 | score=0.333 | number_theory

Let \( a, b, c \) be positive integers such that \( a + b + c = 2024 \). Find the maximum possible value of the expression:
\[
\left\lfloor \frac{a^2}{b+c} \right\rfloor + \left\lfloor \frac{b^2}{a+c} \right\rfloor + \left\lfloor \frac{c^2}{a+b} \right\rfloor
\]
where \( \left\lfloor x \right\rfloor \) denotes the greatest integer less than or equal to \( x \).

Answer: `2044242`

## 0778 | score=0.333 | number_theory

Let $f(x)$ be a polynomial with integer coefficients such that $f(1) = 2023$. Define $S$ as the set of all integers $n$ such that $f(n)$ is a prime number. If $|S| = 10$, what is the smallest possible degree of $f(x)$?

Answer: `10`

## 0779 | score=0.444 | number_theory

Find all positive integers \( n \) such that there exists a polynomial \( P(x) \) with integer coefficients satisfying \( P(1) = n \), \( P(2) = 2n \), and \( P(3) = 3n \).

Answer: `1`

## 0780 | score=0.778 | algebra

Let \( f(x) \) be a continuous function defined on the interval \([0,1]\) such that \( f(0) = 0 \) and \( f(1) = 1 \). Define \( g(x) = \int_0^x (f(t) - t) \, dt \). Given that \( g(x) \) is also continuous on \([0,1]\) and differentiable on \((0,1)\), prove that there exists a point \( c \) in \((0,1)\) such that \( f'(c) = 1 \).

Answer: `f'(c) = 1`

## 0781 | score=0.556 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that \( n \) can be expressed as the sum of two or more consecutive positive integers. For example, \( 9 = 4 + 5 \) and \( 15 = 1 + 2 + 3 + 4 + 5 \). Prove that the number of elements in the set \( S \) that are less than or equal to 1000 is equal to the number of prime numbers less than or equal to 1000.

Answer: `168`

## 0782 | score=0.444 | number_theory

What is the smallest positive integer \( n \) such that \( n^{100} - 1 \) is divisible by \( 1979 \) and \( n^{101} - 1 \) is divisible by \( 2017 \)? Furthermore, show that the resulting \( n \) satisfies the condition that \( n^{1000} - 1 \) is divisible by \( 3 \times 5 \times 7 \times 11 \)?

Answer: `1`

## 0783 | score=0.667 | geometry

A sequence of positive integers \(a_1, a_2, a_3, \ldots\) is defined by \(a_1 = 1\) and for \(n \geq 2\), \(a_n\) is the smallest positive integer not already in the sequence such that the sum of the first \(n\) terms is a perfect square. Find the 2023rd term of the sequence, \(a_{2023}\).

Answer: `4045`

## 0784 | score=0.667 | geometry

Let \( f: \mathbb{Z} \to \mathbb{Z} \) be a function such that \( f(1) = 1 \) and \( f(n+1) = f(n) + \left\lfloor \sqrt{f(n)} \right\rfloor \) for all \( n \geq 1 \). Determine the smallest positive integer \( m \) such that \( f(m) \) is a perfect square.

Answer: `4`

## 0785 | score=0.444 | geometry

Let \(ABC\) be an acute triangle with orthocenter \(H\) and circumcenter \(O\). Let \(D, E,\) and \(F\) be the feet of the altitudes from \(A, B,\) and \(C\) respectively. If \(M\) is the midpoint of \(BC\) and \(N\) is the midpoint of \(AD\), find the ratio \(\frac{ON}{OM}\) given that the circumradius \(R\) of \(\triangle ABC\) is 10 units.

Answer: `1`

## 0786 | score=0.444 | number_theory

Find the sum of all positive integers \( n \) less than 1000 such that \( n \) divides the number formed by writing \( n \) in reverse order, and the number formed by squaring \( n \) also divides this reversed number.

Answer: `1`

## 0787 | score=0.556 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that the equation \( x^2 + y^2 = nz \) has a solution in positive integers \( x, y, \) and \( z \). Find the number of elements in the set \( S \) that are less than or equal to 2024.

Answer: `2024`

## 0788 | score=0.333 | geometry

Let \( ABC \) be a triangle with \( AB = 13 \), \( BC = 14 \), and \( CA = 15 \). Let \( D \) be the foot of the altitude from \( A \) to \( BC \), and let \( E \) and \( F \) be the points where the incircle of \( \triangle ABC \) is tangent to \( BC \), \( CA \), and \( AB \), respectively. Compute the area of the quadrilateral \( ADEF \).

Answer: `42`

## 0789 | score=0.667 | geometry

Let \( S \) be the set of all positive integers \( n \) such that \( \sqrt{n} \) is an integer and \( n \) can be expressed as the sum of two squares of integers. Determine the smallest positive integer \( m \) such that there exist distinct elements \( a, b, c \in S \) satisfying \( a + b + c = m \).

Answer: `14`

## 0790 | score=0.667 | number_theory

Let \( f(x) \) be a polynomial with integer coefficients such that \( f(0) = 1 \) and \( f(1) = 3 \). Suppose further that there exists a positive integer \( n \) such that \( f(n) = n^3 + 3 \). Find the smallest possible value of \( n \) for which such a polynomial \( f(x) \) exists.

Answer: `2`

## 0791 | score=0.429 | geometry

Find all positive integers \( n \) such that the sum of the squares of the divisors of \( n \) is equal to \( 3n^2 \). Express your answer in the form of a list, separated by commas.

Answer: `1`

## 0792 | score=0.667 | geometry

In a right triangle $ABC$ with $\angle C = 90^\circ$, $AB = 13$, $BC = 5$. A point $D$ is on $AB$ such that $\angle ACD = 45^\circ$. Find the length of $CD$.

Answer: `\frac{60\sqrt{2}}{17}`

## 0793 | score=0.778 | number_theory

Find all positive integers \( n \) such that there exist positive integers \( a, b, c \) with \( \gcd(a, b, c) = 1 \) and the equation
\[ a^n + b^n + c^n = n! \cdot (a + b + c). \]

Answer: `1`

## 0794 | score=0.444 | geometry

In triangle $ABC$, let $D$, $E$, and $F$ be the feet of the altitudes from $A$, $B$, and $C$ respectively. Suppose that $AD = 13$, $BD = 14$, and $CD = 15$. Find the area of triangle $DEF$.

Answer: `84`

## 0795 | score=0.778 | number_theory

Find all positive integers \( n \) such that \( n^2 + n + 1 \) divides \( 2^n - 1 \).

Answer: `5`

## 0796 | score=0.444 | number_theory

Find all prime numbers \( p \) such that the equation \( x^3 + y^3 = px^2y^2 \) has integer solutions \((x, y)\) where \( x \neq y \) and \( x, y > 0 \).

Answer: `2`

## 0797 | score=0.444 | number_theory

Let $P(x)$ be a polynomial with real coefficients. Suppose that $P(x)$ has the following property: For every positive integer $n$, there exists a polynomial $Q_n(x)$ of degree $n$ such that $P(x) = Q_n(x) + R_n(x)$, where $R_n(x)$ is a polynomial of degree less than $n$. Moreover, for each $n$, the polynomial $Q_n(x)$ has exactly $n$ distinct real roots. Find the number of possible values of $\deg(P)$, i.e., the degree of $P(x)$.

Answer: `\infty`

## 0798 | score=0.333 | geometry

Consider a sequence of numbers \(a_1, a_2, a_3, \ldots\) where \(a_1 = 1\), and for \(n \geq 2\), \(a_n\) is defined as the smallest positive integer not yet in the sequence such that the sum \(a_1 + a_2 + \cdots + a_n\) is a perfect square. Find \(a_{2023}\).

Answer: `4045`

## 0799 | score=0.333 | number_theory

Let $f(x)$ be a polynomial of degree $4$ such that $f(0) = 1$, $f(1) = 3$, $f(2) = 5$, and $f(3) = 7$. If $f(100) = k + \sqrt{m}$ for integers $k$ and $m$, determine the ordered pair $(k, m)$.

Answer: `(201, 0)`

## 0800 | score=0.333 | number_theory

A sequence of positive integers \( a_1, a_2, a_3, \dots, a_n \) is defined by \( a_1 = 1 \) and for \( n \geq 2 \), \( a_n \) is the smallest positive integer such that the product \( a_1 \cdot a_2 \cdot \dots \cdot a_n \) is not divisible by \( n \). Find the value of \( a_{100} \).

Answer: `100`

## 0801 | score=0.556 | geometry

Let \( S \) be the set of all positive integers \( n \) such that the sum of the digits of \( n \) in base 10 is equal to \( 10 \). Find the smallest positive integer \( k \) for which the sum of the digits of \( k \cdot n \) for all \( n \in S \) is a perfect square.

Answer: `9`

## 0802 | score=0.667 | geometry

Find the smallest positive integer \( n \) such that the sum of the squares of the first \( n \) odd integers is a perfect cube. Prove your answer.

Answer: `1`

## 0803 | score=0.333 | number_theory

Find all functions \( f: \mathbb{N} \to \mathbb{N} \) that satisfy the following conditions:
1. For all \( x, y \in \mathbb{N} \), \( f(xy) = f(x)f(y) \).
2. For all \( x, y \in \mathbb{N} \) with \( x + y \) being a prime number, \( f(x) + f(y) = 1 \).

Answer: `f(n) = 1`

## 0804 | score=0.444 | geometry

Let $S$ be the set of all positive integers $n$ such that $n$ has exactly 15 positive divisors, and the product of these divisors is a perfect square. How many elements does $S$ have?

Answer: `0`

## 0805 | score=0.333 | geometry

Let \( f(x) \) be a polynomial with integer coefficients such that \( f(100) = 100 \) and for every integer \( n \), \( f(n) \) is a perfect square. Prove that there exists a polynomial \( g(x) \) with integer coefficients such that \( f(x) = g(x)^2 \).

Answer: `g(x)`

## 0806 | score=0.667 | other

In a magical forest, there are three types of trees: spruce, pine, and birch. Every year, the spruce tree increases its height by 20%, the pine tree by 30%, and the birch tree by 15%. If initially the spruce tree is 100 feet tall, the pine tree is 80 feet tall, and the birch tree is 90 feet tall, after how many years will the height of the pine tree first exceed the height of the spruce tree by at least 20%?

Answer: `6`

## 0807 | score=0.667 | geometry

A circle with center \( O \) is inscribed in a square of side length 10 units. A point \( P \) is chosen at random inside the square. What is the probability that the distance from \( P \) to \( O \) is greater than 3 units?

Answer: `\frac{100 - 9\pi}{100}`

## 0808 | score=0.444 | geometry

In the complex plane, consider three distinct complex numbers \( z_1, z_2, z_3 \) such that \( |z_1| = |z_2| = |z_3| = 1 \). These numbers are vertices of an isosceles triangle inscribed in the unit circle. If \( z_1 + z_2 + z_3 = 0 \), find the maximum possible value of \( |z_1^2 + z_2^2 + z_3^2| \).

Answer: `2`

## 0809 | score=0.667 | geometry

There is a set of 20 distinct positive integers, each less than 100. It is known that for any three distinct numbers \(a, b, c\) in this set, there exists a fourth number \(d\) in the set such that \(a + b + c - d\) is a perfect square. Determine the minimum possible size of this set.

Answer: `20`

## 0810 | score=0.444 | geometry

A regular hexagon with side length \( s \) is inscribed in a circle. A smaller hexagon is then inscribed in the same circle such that each of its vertices touches the midpoint of the sides of the larger hexagon. If the side length of the smaller hexagon is \( t \), express \( t \) in terms of \( s \).

Answer: `\frac{s\sqrt{3}}{2}`

## 0811 | score=0.444 | number_theory

Let $S$ be the set of all positive integers that can be represented as the sum of three or fewer distinct powers of $3$. For example, $3^0 + 3^1 + 3^2 = 13$ is in $S$. Find the number of elements in $S$ that are less than $1000$.

Answer: `63`

## 0812 | score=0.444 | number_theory

Determine the smallest positive integer \(n\) such that \(n^2 - 1\) is divisible by \(2^4 \cdot 3^2 \cdot 5\).

Answer: `1`

## 0813 | score=0.444 | number_theory

Let \( f: \mathbb{N} \rightarrow \mathbb{N} \) be a function such that for all positive integers \( n \),
\[ f(n) + f(n+1) = 2n + 2f(n)^2. \]
Given that \( f(1) = 1 \), find the value of \( f(2023) \).

Answer: `4090507`

## 0814 | score=0.778 | geometry

In a 3D coordinate system, points A, B, and C form the vertices of an equilateral triangle with side length 6 units. Point D is located such that it creates another equilateral triangle ABD with side length 6 units, outside the plane of triangle ABC. If E is the midpoint of BD, what is the distance from point E to the plane containing triangle ABC? Express your answer as a simplified radical.

Answer: `\frac{3\sqrt{3}}{2}`

## 0815 | score=0.778 | number_theory

Find all functions \( f: \mathbb{Z} \to \mathbb{Z} \) such that for all integers \( a \) and \( b \), the following equality holds:
\[ f(a^2 + b^2 + c^2) = f(a)^2 + f(b)^2 + f(c)^2 + 2f(ab + bc + ca) \]
Additionally, show that if \( f \) is such a function, then there exists an integer \( k \) for which \( f(n) = n^2 + k \) for all integers \( n \).

Answer: `f(n) = n^2`

## 0816 | score=0.444 | number_theory

Find all prime numbers \( p \) for which the equation
\[ x^2 - 2px + 10 = 0 \]
has integer solutions.

Answer: `3`

## 0817 | score=0.778 | number_theory

In the realm of complex numbers, consider the function \( f(z) = z^2 + c \), where \( z \) is a complex number and \( c \) is a fixed complex number. Let \( c = -1 + \frac{\sqrt{3}}{2}i \). Define the sequence of complex numbers \( z_1, z_2, z_3, \ldots \) by the recurrence relation \( z_{n+1} = f(z_n) \) for \( n \geq 1 \), with \( z_1 = 0 \).

Determine the smallest positive integer \( N \) such that \( |z_N| > 2 \), where \( |z| \) denotes the magnitude of the complex number \( z \).

Answer: `4`

## 0818 | score=0.667 | number_theory

Find all positive integers \( n \) such that the equation \( x^2 + y^2 + z^2 = nxyz \) has at least one solution in positive integers \( x, y, z \).

Answer: `3`

## 0819 | score=0.333 | geometry

Let \( ABC \) be a triangle with \( \angle BAC = 90^\circ \). Let \( D \) be a point on \( BC \) such that \( AD \) is the altitude from \( A \) to \( BC \). Let \( E \) and \( F \) be points on \( AB \) and \( AC \) respectively, such that \( DE \perp AB \) and \( DF \perp AC \). If \( AD = 3 \), \( BD = 4 \), and \( DC = 5 \), find the length of \( EF \).

Answer: `3`

## 0820 | score=0.778 | algebra

Let $f(x)$ be a polynomial of degree 4 such that $f(0) = 1$, $f(1) = 2$, $f(2) = 5$, $f(3) = 10$, and $f(4) = 17$. Determine the value of $f(5)$.

Answer: `26`

## 0821 | score=0.778 | number_theory

Let $P(x)$ be a polynomial with integer coefficients such that $P(2023) = 2023$, $P(2024) = 2024$, and $P(2025) = 2025$. Determine the largest possible value of $P(2022)$.

Answer: `2028`

## 0822 | score=0.444 | geometry

In the Cartesian plane, let $A = (0, 0)$, $B = (10, 0)$, and $C = (10, 20)$. A point $P$ inside $\triangle ABC$ is selected such that the lines $AP$, $BP$, and $CP$ are all extended to meet the opposite sides of the triangle at points $D$, $E$, and $F$ respectively. If the area of $\triangle DEF$ is $100$ square units, find the coordinates of $P$ assuming it lies on the line segment joining the midpoints of $AB$ and $BC$.

Answer: `\left( \frac{20}{3}, \frac{20}{3} \right)`

## 0823 | score=0.444 | algebra

Let \( f(x) = x^3 - 3x^2 + 2x \) and \( g(x) = x^2 - 4x + 3 \). Consider the function \( h(x) = f(x) \cdot g(x) \). Determine the sum of all distinct real numbers \( x \) such that \( h(h(x)) = h(x) \).

Answer: `6`

## 0824 | score=0.556 | combinatorics

Let \( S \) be a set of \( n \) distinct real numbers. Define a sequence of sets \( T_1, T_2, \ldots, T_k \) such that each \( T_i \) is formed by removing exactly one element from \( T_{i-1} \) and adding a new distinct element from \( S \) that is not already in \( T_{i-1} \), where \( k \) is the total number of elements removed from \( S \). If the sequence \( T_1, T_2, \ldots, T_k \) includes all possible subsets of \( S \) with exactly \( m \) elements, find the number of distinct sequences \( T_1, T_2, \ldots, T_k \) for a given \( n \) and \( m \).

Answer: `\binom{n}{m}`

## 0825 | score=0.778 | number_theory

Find all positive integers \( n \) such that \( n \) divides \( 2^n + 1 \).

Answer: `1, 3`

## 0826 | score=0.444 | algebra

In the Cartesian plane, consider a set of \(n\) points \(P = \{P_1, P_2, \ldots, P_n\}\), where each point \(P_i\) is located at \((x_i, y_i)\). Let \(D_i\) be the distance from \(P_i\) to the origin, and define \(D_{\min}\) as the minimum distance among all points in \(P\). We call a point \(P_i\) special if there exists a point \(P_j\) (with \(i \neq j\)) such that \(D_i = D_j\) and \(D_i = 2D_{\min}\).

Given that \(n \geq 4\) and \(P\) contains exactly 10 special points, find the minimum possible value of \(n\).

Answer: `11`

## 0827 | score=0.556 | number_theory

Find the smallest positive integer \( n \) such that \[ \frac{1}{n} = \sum_{k=1}^{\infty} \frac{1}{k(k+1)^2} \] and provide a proof for your answer.

Answer: `1`

## 0828 | score=0.444 | number_theory

Find all positive integers \( n \) such that \( n^3 + 1 \) divides \( n^4 + n^2 + 1 \).

Answer: `1`

## 0829 | score=0.444 | number_theory

What is the smallest positive integer $n$ such that the sum of the reciprocals of the first $n$ positive integers is greater than $10$?

Answer: `12367`

## 0830 | score=0.375 | number_theory

In a group of 2023 students, each student is assigned a unique positive integer. The teacher decides to play a game where she selects two distinct students at random, $A$ and $B$, and calculates the product of their assigned numbers. She then performs the following operation: if the product is even, she multiplies it by 2; if the product is odd, she divides it by 2. She repeats this process with all pairs of distinct students in the group. After completing the operations, she finds that the total sum of all the numbers obtained from the operations is 1011511. Determine the sum of the original numbers assigned to the students.

Answer: `2023`

## 0831 | score=0.556 | geometry

Find all positive integers \( n \) such that \( n^3 + 3n^2 + 3n + 1 \) is a perfect square.

Answer: `3`

## 0832 | score=0.333 | geometry

In the Cartesian plane, a point \( P \) is said to be *excellent* if there exists a circle centered at \( P \) that intersects the x-axis and y-axis at exactly three points each. Let \( S \) be the set of all excellent points. Determine the number of points in \( S \) that lie inside the unit square with vertices at \((0,0)\), \((1,0)\), \((1,1)\), and \((0,1)\). Each point in \( S \) must have both coordinates as rational numbers.

Answer: `0`

## 0833 | score=0.375 | number_theory

Find all positive integers \( n \) such that the equation
\[ x^n + (x+1)^n + (x+2)^n = (x+3)^n \]
has at least one integer solution for \( x \).

Answer: `1, 3`

## 0834 | score=0.333 | geometry

In triangle \(ABC\), point \(D\) is chosen on side \(AB\) such that \(AD : DB = 1 : 3\). Point \(E\) is chosen on side \(AC\) such that \(AE : EC = 2 : 3\). The line segments \(DE\) and \(BC\) intersect at point \(F\). If the area of triangle \(ADE\) is 6 square units, find the area of quadrilateral \(BCED\).

Answer: `54`

## 0835 | score=0.444 | geometry

There are 10 points in a plane, with no three points being collinear. Each pair of points is connected by a segment. A selection of these segments is called a "triangle-free path" if no three segments form a triangle. Find the maximum possible number of segments in a triangle-free path.

Answer: `9`

## 0836 | score=0.556 | algebra

Let \( f(x) = \frac{x^3 + 2x^2 + x + 1}{x^2 + 1} \). Determine the limit of \( f(x) \) as \( x \) approaches infinity, and then find the value of \( k \) such that the equation \( f(x) = k \) has exactly one real root.

Answer: `1`

## 0837 | score=0.667 | algebra

In the complex plane, consider the set of all points \( z \) such that \( |z - 1| = 2|z + 1| \). If a point \( w \) lies on this set and also satisfies \( w = a + bi \) where \( a \) and \( b \) are real numbers, find the maximum possible value of \( a^2 + b^2 \).

Answer: `9`

## 0838 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the equation
\[ \sum_{k=1}^{n} \frac{1}{k} = 2.99 \]
has a solution for the sequence of \( n \) distinct positive integers.

Answer: `10`

## 0839 | score=0.333 | number_theory

Let $S$ be the set of all positive integers $n$ such that $n$ has exactly three digits and the product of its digits is equal to $216$. Find the number of elements in the set $S$.

Answer: `6`

## 0840 | score=0.556 | number_theory

Let \( A = (a_1, a_2, \ldots, a_n) \) be a sequence of positive integers such that \( a_1 + a_2 + \cdots + a_n = 1000 \) and for each \( i = 1, 2, \ldots, n-1 \), the sum of any subset of \( A \) containing \( a_i \) but not \( a_{i+1} \) is not divisible by \( a_{i+1} \). Find the maximum possible value of \( n \).

Answer: `44`

## 0841 | score=0.333 | geometry

In triangle \( ABC \), let \( D \) be the foot of the altitude from \( A \) to \( BC \). Let \( E \) be a point on \( AC \) such that \( DE \) is perpendicular to \( AC \). If \( \angle BAC = 30^\circ \), \( AD = 4 \), and \( AE = 6 \), find the length of \( BE \).

Answer: `2\sqrt{7}`

## 0842 | score=0.333 | number_theory

Let \( f(n) \) denote the sum of the cubes of the digits of a positive integer \( n \). Starting with any positive integer \( n \), repeatedly apply \( f \) until a single-digit number is obtained. For instance, starting with \( n = 123 \) leads to the sequence \( 123, 36, 27, 12, 8 \). 

**Part A:** Find the smallest positive integer \( n \) such that the sequence starting with \( n \) eventually reaches the single-digit number 7.

**Part B:** Determine how many distinct single-digit numbers can be reached by this process for any positive integer \( n \).

Answer: `9`

## 0843 | score=0.778 | number_theory

Consider a sequence of integers \( a_1, a_2, a_3, \ldots \) defined by \( a_1 = 1 \) and for \( n \geq 1 \), \( a_{n+1} \) is the smallest integer greater than \( a_n \) such that \( \text{gcd}(a_{n+1}, a_n) = 1 \). Find the 100th term of this sequence, \( a_{100} \).

Answer: `100`

## 0844 | score=0.444 | geometry

In triangle $ABC$, $AB = 13$, $BC = 14$, and $AC = 15$. Let $D$ be a point on side $AC$ such that $AD = 5$ and $DC = 10$. Let $E$ be the midpoint of $BD$, and let $F$ be the intersection of line $AE$ and the circumcircle of triangle $ABC$ other than $A$. Find the length of segment $AF$.

Answer: `12`

## 0845 | score=0.444 | number_theory

Let $f(x)$ be a polynomial with real coefficients such that $f(x)^2 + 1$ is divisible by $x^2 + x + 1$. Find the smallest possible degree of $f(x)$.

Answer: `1`

## 0846 | score=0.556 | number_theory

Find the smallest positive integer \( n \) such that \( n \) has exactly 10 positive divisors and the product of these divisors is \( 2^{10} \cdot 3^5 \).

Answer: `48`

## 0847 | score=0.333 | other

在三维空间中，给定两个向量 \(\vec{a} = (1, 2, 3)\) 和 \(\vec{b} = (4, -1, 2)\)。求过原点且与这两个向量均垂直的平面方程，并进一步求出该平面上任意一点到直线 \(\vec{r} = t(1, 1, 1)\) 的最小距离。

Answer: `0`

## 0848 | score=0.556 | number_theory

Consider a sequence of positive integers \( a_1, a_2, \ldots, a_n \) such that for every integer \( k \) (where \( 1 \leq k \leq n \)), the number \( a_k \) is the sum of the previous \( k \) terms of the sequence. Given that \( a_1 = 1 \) and \( a_2 = 3 \), find the value of \( a_{10} \).

Answer: `512`

## 0849 | score=0.556 | geometry

In a geometric configuration where a regular pentagon \(ABCDE\) is inscribed in a circle and a regular decagon \(FGBHICJDKLE\) is also inscribed in the same circle, find the ratio of the area of triangle \(EFG\) to the area of the pentagon \(ABCDE\). Express your answer as a simplified fraction.

Answer: `\frac{1}{5}`

## 0850 | score=0.333 | geometry

Find all prime numbers \( p \) such that the sum of the squares of the first \( p \) positive integers is divisible by \( p^2 \).

Answer: `3`

## 0851 | score=0.778 | number_theory

Let \( f(x) \) be a polynomial with integer coefficients such that \( f(0) = 1 \), \( f(1) = 2 \), and \( f(2) = 5 \). If \( p \) is the smallest positive integer such that \( f(p) = 100 \), find the value of \( p \).

Answer: `10`

## 0852 | score=0.556 | number_theory

Let \( f: \mathbb{Z} \to \mathbb{Z} \) be a function such that for any integers \( a \) and \( b \),
\[ f(f(a) + b) = f(a) + f(b) + ab \]
and for any integer \( n \), \( f(n) \neq 0 \). Find all possible values of \( f(2023) \).

Answer: `2023`

## 0853 | score=0.667 | other

Let \( S \) be a finite set of points in the plane, and let \( T \) be the set of all points that are the midpoints of segments with endpoints in \( S \). If \( |S| = n \), determine the maximum possible number of points in \( T \).

Answer: `\frac{n(n-1)}{2}`

## 0854 | score=0.333 | number_theory

A sequence of numbers \(a_1, a_2, a_3, \ldots\) is defined by the recurrence relation \(a_{n+1} = a_n^2 - a_n + 1\) with the initial term \(a_1 = 2\). Find the smallest integer \(k\) such that \(a_k > 10^{2023}\).

Answer: `14`

## 0855 | score=0.333 | geometry

In the coordinate plane, let \( A \) be the point at \( (0, 1) \) and \( B \) be the point at \( (2, 0) \). There is a point \( P \) inside the unit square with vertices at \( (0, 0) \), \( (1, 0) \), \( (1, 1) \), and \( (0, 1) \) such that the distances from \( P \) to both \( A \) and \( B \) are equal. If the coordinates of \( P \) are given by \( \left( \frac{p}{q}, \frac{r}{s} \right) \), where \( p, q, r, \) and \( s \) are positive integers with no common factors other than 1, find the value of \( p + q + r + s \).

Answer: `8`

## 0856 | score=0.556 | geometry

Find all positive integers \( n \) such that \( n^3 + 2n^2 + 3n + 4 \) is a perfect square.

Answer: `0`

## 0857 | score=0.556 | geometry

Find all pairs of positive integers (a, b) such that \(a^2 + ab + b^2\) is a perfect square and \(a < b < 2a\).

Answer: `(3, 5)`

## 0858 | score=0.667 | number_theory

Find the number of ordered pairs $(x,y)$ of integers such that the equation $x^2 + y^2 = 10x - 2y - 10$ is satisfied. How does your solution change if the equation is modified to $x^2 + y^2 = 10x - 2y - 11$?

Answer: `0`

## 0859 | score=0.667 | geometry

Find all positive integers \( n \) such that \( n^3 - 4n^2 + 5n - 1 \) is a perfect square.

Answer: `1, 2, 5`

## 0860 | score=0.778 | number_theory

Find all prime numbers $p$ such that the equation $x^3 - y^3 = p$ has a solution in integers $(x, y)$ where $x$ and $y$ are not multiples of $p$.

Answer: `7`

## 0861 | score=0.556 | number_theory

Let \( P \) be a polynomial with integer coefficients such that \( P(0) = 0 \) and \( P(1) = 1 \). Suppose that for every integer \( k \geq 2 \), the number \( P(k) \) is divisible by \( k \). Determine all possible polynomials \( P \).

Answer: `P(x) = x`

## 0862 | score=0.778 | geometry

A sequence of integers \(a_1, a_2, a_3, \ldots, a_{10}\) is defined such that \(a_1 = 1\) and for \(n \geq 2\), \(a_n\) is the smallest positive integer not already in the sequence such that \(a_n \cdot a_{n-1}\) is not a perfect square. Find the last term \(a_{10}\) of this sequence.

Answer: `10`

## 0863 | score=0.667 | algebra

Let \( f(x) \) be a function defined for all real numbers \( x \) such that \( f(x) = \sin(x) \cdot \cos(2x) \). Determine the number of critical points of \( f(x) \) in the interval \( [0, 2\pi] \).

Answer: `6`

## 0864 | score=0.444 | geometry

In the coordinate plane, let $P$ be a point with integer coordinates $(x, y)$ such that $0 < x < 100$ and $0 < y < 100$. Define the "sum distance" $S_P$ of $P$ as the sum of the distances from $P$ to all other lattice points $(a, b)$ with $0 < a < 100$ and $0 < b < 100$, where each distance is counted twice (once for each direction). For how many points $P$ is $S_P$ an integer multiple of $2023$?

Answer: `9801`

## 0865 | score=0.444 | number_theory

Let \( f(x) \) be a polynomial with integer coefficients such that \( f(1) = 3 \), \( f(2) = 7 \), and \( f(3) = 13 \). Suppose \( f(x) \) has a root at \( x = k \) where \( k \) is a positive integer greater than 3. Determine the smallest possible value of \( k \).

Answer: `4`

## 0866 | score=0.667 | geometry

Let $ABC$ be an acute triangle with circumcenter $O$ and incenter $I$. Let $D$ be the foot of the altitude from $A$ to $BC$, and let $E$ be the reflection of $D$ over $BC$. The line through $I$ parallel to $BC$ intersects $AD$ at $F$ and $AE$ at $G$. Prove that the circumcircle of triangle $OFG$ passes through the midpoint of $BC$.

Answer: `M`

## 0867 | score=0.556 | number_theory

Let \( f \) be a function defined on the set of integers such that for all \( n \),

\[
f(n) = 
\begin{cases} 
n + 1 & \text{if } n \text{ is even}, \\
n - 1 & \text{if } n \text{ is odd}.
\end{cases}
\]

For how many integers \( n \), where \( 1 \leq n \leq 2024 \), does there exist a positive integer \( k \) such that \( f^k(n) = 1 \)?

Answer: `1012`

## 0868 | score=0.778 | number_theory

A sequence of numbers \(a_1, a_2, a_3, \ldots\) is defined such that \(a_1 = 1\), \(a_2 = 2\), and for \(n \geq 3\), \(a_n\) is the smallest positive integer that does not divide any of the previous terms in the sequence. For example, \(a_3\) cannot be 3 because it divides \(a_2\), but \(a_3 = 4\) is valid since 4 does not divide \(a_1\) or \(a_2\). Find the sum of the first 20 terms of this sequence.

Answer: `210`

## 0869 | score=0.444 | number_theory

Find all positive integers $n$ such that there exist distinct positive integers $a_1, a_2, \ldots, a_n$ satisfying
$$
\sum_{i=1}^n \frac{a_i}{i^2} = n.
$$

Answer: `1`

## 0870 | score=0.778 | geometry

A right triangle \( ABC \) has an angle \( \theta \) at vertex \( A \), with \( \theta = 30^\circ \). Point \( D \) lies on \( BC \) such that \( BD = DC \). If \( AD \) is perpendicular to \( BC \), find the ratio of the area of triangle \( ABD \) to the area of triangle \( ACD \). Express your answer as a common fraction.

Answer: `1`

## 0871 | score=0.556 | geometry

Find all positive integers \( n \) such that \( n^4 - 5n^2 + 4 \) is a perfect square.

Answer: `1`

## 0872 | score=0.778 | geometry

Let $S$ be a finite set of points in the plane such that for any two distinct points $P, Q \in S$, there exists a point $R \in S$ that is not collinear with $P$ and $Q$. Furthermore, no three points in $S$ are collinear. Determine the maximum possible number of points in $S$ if the area of the convex hull of $S$ is exactly $1$.

Answer: `4`

## 0873 | score=0.333 | number_theory

In a regular nonagon \( P \), each vertex is connected to every other vertex by a segment. A frog starts at vertex \( A \) and makes hops from one vertex to another, following these rules: 
1. In every hop, the frog moves to an adjacent vertex (one step in any direction).
2. The frog can never make two consecutive hops in the same direction.

Let \( n \) be the total number of ways the frog can visit all vertices of \( P \) exactly once, returning to vertex \( A \) at the end. Find the remainder when \( n \) is divided by 1000.

Answer: `160`

## 0874 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + nx + n - 1 \) can be expressed as a product of two non-constant polynomials with integer coefficients.

Answer: `2`

## 0875 | score=0.556 | geometry

What is the sum of all positive integers \( n \) such that \( \frac{n^2 + 2018}{n} \) is a perfect square?

Answer: `0`

## 0876 | score=0.556 | geometry

Find all positive integers \( n \) such that \( n^3 + 20n + 1 \) is a perfect square. Prove that your solution is complete.

Answer: `2`

## 0877 | score=0.556 | geometry

In a convex pentagon \(ABCDE\), the angles \(\angle A\), \(\angle B\), and \(\angle C\) are equal to \(120^\circ\) each, while \(\angle D\) and \(\angle E\) are right angles. If the side \(AB\) is equal to the side \(CD\), and the side \(BC\) is equal to the side \(DE\), find the ratio of the lengths of the sides \(AD\) to \(AE\).

Answer: `1`

## 0878 | score=0.778 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a continuous function such that \( f(x + y) = f(x) f(y) \) for all \( x, y \in \mathbb{R} \). Suppose \( f(1) = 2 \) and \( f(2) = 4 \). Find the value of \( f(3) \).

Answer: `8`

## 0879 | score=0.778 | number_theory

Find all positive integers \( n \) such that the equation
\[ n^2 + 3n + 7 = x^2 \]
has an integer solution \( x \).

Answer: `3`

## 0880 | score=0.333 | number_theory

Let \( f: \mathbb{Z}^+ \to \mathbb{Z}^+ \) be a function satisfying
\[ f(n) = \begin{cases} 
2n & \text{if } n \text{ is even} \\
n + 1 & \text{if } n \text{ is odd and } n \equiv 1 \pmod{3} \\
n - 1 & \text{if } n \text{ is odd and } n \equiv 2 \pmod{3}
\end{cases} \]
Find all positive integers \( k \) such that \( f^{(k)}(1) = 1 \), where \( f^{(k)} \) denotes the \( k \)-fold composition of \( f \).

Answer: `1`

## 0881 | score=0.778 | number_theory

Let $P(x)$ be a monic polynomial of degree $4$ with integer coefficients, and let $r$ be a real number such that $P(r) = 0$. If $r^3 + r^2 + r + 1 = 0$, find the sum of all possible values of $P(0)$.

Answer: `0`

## 0882 | score=0.333 | number_theory

What is the minimum number of distinct integer labels required to label all vertices of a regular octahedron such that the sum of the labels on any pair of opposite faces is the same, and no two adjacent vertices have the same label?

Answer: `3`

## 0883 | score=0.444 | number_theory

Let \( S \) be the set of all integers \( n \) such that \( 1 \leq n \leq 1000 \) and \( n \) has exactly three distinct prime factors. Find the sum of the reciprocals of the smallest element of each of these sets \( S \).

Answer: `\frac{1}{30}`

## 0884 | score=0.333 | geometry

In the coordinate plane, let $P$ be a point with integer coordinates such that the distance from $P$ to the origin is $17$ units. Find the number of possible integer coordinates for $P$.

Answer: `8`

## 0885 | score=0.444 | algebra

In the complex plane, let $P(z) = z^5 + 10z^4 + 40z^3 + 80z^2 + 160z + 256$. Given that $P(z)$ has five distinct complex roots, $z_1, z_2, z_3, z_4,$ and $z_5$, find the value of
\[|z_1^3 z_2^2 z_3 z_4 z_5^2|.\]

Answer: `512`

## 0886 | score=0.333 | algebra

Let \( P(x) \) be a polynomial of degree 4 with real coefficients such that \( P(1) = 2 \), \( P(2) = 5 \), and \( P(3) = 10 \). Additionally, it is known that \( P(x) \) has a double root at \( x = 4 \). Find the value of \( P(0) \).

Answer: `0`

## 0887 | score=0.778 | algebra

Let $f: \mathbb{R} \to \mathbb{R}$ be a function defined by $f(x) = x^3 - 3x + 1$. Consider the set $S = \{x \in \mathbb{R} : f(f(x)) = 0\}$. Determine the number of elements in $S$ and prove your answer.

Answer: `9`

## 0888 | score=0.444 | number_theory

Find all integers \( n \) such that the polynomial \( P(x) = x^n + 3x^{n-1} + 6x^{n-2} + \cdots + \frac{n(n-1)\cdots 3 \cdot 2}{2!} x + n! \) has at least one integer root.

Answer: `1, 2`

## 0889 | score=0.333 | geometry

Given a finite set of points in the plane, each point has integer coordinates. It is known that for any three points, the area of the triangle formed by them is an integer. If the number of points in the set is 10, find the maximum possible value of the area of the convex hull (the smallest convex polygon that contains all the points).

Answer: `25`

## 0890 | score=0.333 | number_theory

Consider a sequence of positive integers \(a_1, a_2, a_3, \ldots\) defined by the recurrence relation \(a_{n+1} = a_n^2 - 2a_n + 2\) for \(n \geq 1\), with the initial term \(a_1 = 3\). Determine the smallest positive integer \(k\) such that \(a_k\) is divisible by 1000.

Answer: `10`

## 0891 | score=0.667 | geometry

Find the smallest positive integer \( n \) such that \( \sin(n\theta) \) is an integer for some \( \theta \) in radians, where \( \theta \) is an acute angle.

Answer: `2`

## 0892 | score=0.444 | number_theory

Let $S$ be the set of all integers $n$ such that $1 \leq n \leq 1000$ and $n$ can be expressed as the sum of two or more consecutive positive integers. Find the number of integers in $S$ that are divisible by 3.

Answer: `333`

## 0893 | score=0.778 | number_theory

Find the number of positive integers n such that 1 ≤ n ≤ 2023, where n^3 + n^2 + n + 1 has exactly 7 positive integer divisors.

Answer: `0`

## 0894 | score=0.444 | number_theory

Consider the sequence defined by \( a_1 = 1 \) and \( a_{n+1} = a_n + \frac{1}{a_n} \) for \( n \geq 1 \). Prove that there exists a positive integer \( k \) such that \( a_k > \sqrt{2k} \).

Answer: `k`

## 0895 | score=0.778 | number_theory

Find all positive integers \( n \) such that the equation \( x^2 + y^2 + z^2 = nxyz \) has positive integer solutions for \( x, y, \) and \( z \).

Answer: `3`

## 0896 | score=0.778 | geometry

Find all pairs of positive integers \((m, n)\) such that both \(m^2 + 3n\) and \(n^2 + 3m\) are perfect squares.

Answer: `(1, 1)`

## 0897 | score=0.778 | number_theory

Find all positive integers \( n \) such that the equation \( x^n + y^n = z^n \) has at least one solution in positive integers \( x, y, z \) with \( x, y, z \) pairwise coprime.

Answer: `1, 2`

## 0898 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers that can be expressed as the sum of exactly two distinct powers of 2. How many elements of \( S \) are less than 2024?

(A) 16
(B) 17
(C) 18
(D) 19
(E) 20

Answer: `17`

## 0899 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) can be expressed as the product of two non-constant polynomials with integer coefficients.

Answer: `3`

## 0900 | score=0.444 | geometry

Let \( S \) be the set of all positive integers \( n \) such that \( \sqrt{n} \) is an integer and \( n \) can be expressed as the sum of the squares of two distinct positive integers. Find the number of elements in the set \( S \) that are less than 1000.

Answer: `1`

## 0901 | score=0.333 | geometry

In the complex plane, let \( z_1, z_2, \) and \( z_3 \) be distinct complex numbers such that \( z_1^2 + z_2^2 + z_3^2 = 0 \) and \( z_1 + z_2 + z_3 = 3 + 4i \). If \( z_1, z_2, \) and \( z_3 \) are vertices of an equilateral triangle centered at the origin, find the value of \( |z_1|^2 + |z_2|^2 + |z_3|^2 \).

Answer: `25`

## 0902 | score=0.500 | geometry

In a hyperbolic plane, consider a regular heptagon \(H\) with side length \(s\). Let \(P\) be a point inside \(H\) such that the distances from \(P\) to each vertex of \(H\) are integers. Given that the area of \(H\) is \(\frac{7}{2} \sqrt{7 + 2\sqrt{7}}\), find the smallest possible sum of the distances from \(P\) to each vertex of \(H\).

Answer: `7`

## 0903 | score=0.556 | geometry

In a triangular park, the vertices are located at points \( A \), \( B \), and \( C \). The park authorities decide to install a single water fountain that must be equidistant from all three vertices to ensure fair usage of water. The coordinates of the vertices are \( A(1, 2) \), \( B(5, 2) \), and \( C(3, 6) \). Determine the coordinates of the location where the fountain should be installed.

Answer: `\left( 3, \frac{7}{2} \right)`

## 0904 | score=0.333 | number_theory

What is the smallest positive integer \( n \) such that the number \( 1234567890_{10} \) in base \( 10 \) can be expressed in base \( n \) with exactly \( 100 \) digits?

Answer: `2`

## 0905 | score=0.556 | number_theory

Let $S$ be the set of all positive integers $n$ such that $n$ can be expressed as $n = a^2 + b^2 + c^2 + d^2$ for some positive integers $a, b, c,$ and $d$. If $N$ is the smallest positive integer that is not in $S$, find the value of $N$.

Answer: `7`

## 0906 | score=0.444 | geometry

Let \( A \) be a \( 4 \times 4 \) matrix with real entries such that \( A^4 = I \) (the identity matrix). Suppose that the minimal polynomial of \( A \) is not linear. Determine the possible minimal polynomials of \( A \) and prove that each polynomial corresponds to a unique such matrix \( A \).

Answer: `x^2 + 1`

## 0907 | score=0.333 | geometry

In the plane, consider an equilateral triangle \( ABC \) with side length \( s \). Points \( D, E, \) and \( F \) are chosen on sides \( BC, CA, \) and \( AB \) respectively, such that \( AD, BE, \) and \( CF \) are concurrent at point \( P \). If the ratio of the area of triangle \( DEF \) to the area of triangle \( ABC \) is given by \( \frac{1}{4} \), find the ratio of the lengths \( BD \) to \( DC \), \( CE \) to \( EA \), and \( AF \) to \( FB \).

Answer: `\frac{1}{2}`

## 0908 | score=0.333 | geometry

Let \( S \) be a set of \( 2023 \) distinct positive integers. Determine the smallest positive integer \( k \) such that for any \( k \)-element subset \( T \) of \( S \), there exists a non-empty subset of \( T \) whose elements sum to a perfect square.

Answer: `2023`

## 0909 | score=0.333 | geometry

Find the number of ways to tile a $2 \times 2n$ rectangle with $2 \times 1$ dominoes if each row must have exactly one pair of dominoes that share a vertical edge, and the rest of the dominoes must be placed horizontally.

Answer: `2^n`

## 0910 | score=0.444 | number_theory

What is the least positive integer  $n$  such that there exists a convex polyhedron with  $n$  vertices,  $2n$  faces of three different types, and  $3n$  edges, where each type of face has a different number of edges and no two faces of the same type are adjacent to each other?

Answer: `6`

## 0911 | score=0.333 | number_theory

Determine the smallest positive integer \( n \) such that there exists a polynomial \( P(x) \) with integer coefficients satisfying the following conditions:
1. \( P(0) = 1 \)
2. For all integers \( k \) from 1 to \( n \), \( P(k) = k \)
3. \( P(n+1) = n+2 \)

Answer: `2`

## 0912 | score=0.444 | number_theory

A sequence of positive integers \(a_1, a_2, a_3, \ldots, a_n\) is defined by \(a_1 = 1\), \(a_2 = 2\), and for \(n \geq 3\), \(a_n\) is the smallest positive integer such that \(a_n\) is not a divisor of \(a_1 \cdot a_2 \cdot \ldots \cdot a_{n-1}\) and \(a_n\) is not a divisor of any \(a_i\) for \(i < n\). If \(a_5 = 11\), find \(a_6\).

Answer: `7`

## 0913 | score=0.333 | geometry

Find all positive integers \( n \) such that \( n^3 + 2n^2 + 2017n \) is a perfect square.

Answer: `1`

## 0914 | score=0.556 | number_theory

Given the set \(S\) of all positive integers less than 37, consider the equation \(x^2 + x + 1 \equiv 0 \pmod{37}\). Determine the number of distinct solutions \(x\) this equation has, where \(x \in S\).

Answer: `2`

## 0915 | score=0.778 | number_theory

Consider a sequence of functions \( f_n : \mathbb{R} \to \mathbb{R} \) defined by \( f_n(x) = \sin(n \pi x) \). For a given real number \( a \), determine the number of distinct positive integers \( k \leq 100 \) such that the equation \( f_k(a) = 0 \) has at least one solution for \( x \) in the interval \( [0, 1] \).

Answer: `100`

## 0916 | score=0.444 | geometry

Find all positive integers \(n\) such that the sum of the squares of the first \(n\) positive integers is divisible by the sum of the first \(n\) positive integers.

Answer: `1, 4, 7, 10, \ldots`

## 0917 | score=0.444 | geometry

Find the number of ordered pairs of integers $(m,n)$ with $1\leq m\leq 100$ and $n\geq 0$ such that the polynomial $x^2+mx+n$ can be factored into the product of two (not necessarily distinct) linear factors with integer coefficients, and also determine the conditions under which the discriminant of the polynomial is a perfect square.

Answer: `5050`

## 0918 | score=0.444 | geometry

Find the smallest positive integer \( n \) such that \( n \) is not expressible as the sum of two or more distinct perfect squares and \( n \) is not a perfect square.

Answer: `2`

## 0919 | score=0.556 | other

Let \( G \) be a finite, simple, and connected graph with \( n \) vertices and \( m \) edges. Suppose that for any two distinct vertices \( u \) and \( v \), the number of vertices adjacent to both \( u \) and \( v \) is at least 1. Find the minimum possible value of \( m \) in terms of \( n \).

Answer: `n`

## 0920 | score=0.444 | number_theory

Find all positive integers \( n \) such that the equation
\[ x^2 - nx + n - 1 = 0 \]
has exactly two distinct integer solutions for \( x \), and one of the solutions is the sum of the other two. (Note: A solution is defined as distinct if it is not repeated across the roots of the equation.)

Answer: `3`

## 0921 | score=0.556 | number_theory

Find all positive integers \(n\) such that \(n^2 + n + 1\) divides \(3^n + 2^n + 1\).

Answer: `1, 2`

## 0922 | score=0.333 | number_theory

Consider the sequence of integers defined by \(a_1 = 1\), \(a_2 = 2\), and for \(n \geq 3\), \(a_n = a_{n-1} + a_{n-2} + \text{digit-sum}(a_{n-1})\), where \(\text{digit-sum}(k)\) denotes the sum of the digits of \(k\). Find the remainder when \(a_{2023}\) is divided by 100.

Answer: `61`

## 0923 | score=0.667 | geometry

A convex polygon \( P \) with \( n \) vertices is inscribed in a circle of radius \( R \). The vertices are labeled \( A_1, A_2, \ldots, A_n \) in order. A point \( B \) is chosen inside the circle such that the distance from \( B \) to the center of the circle is \( r \). Consider the line segments \( B A_1, B A_2, \ldots, B A_n \). 

Define \( S \) as the sum of the lengths of all such line segments:
\[ S = \sum_{k=1}^{n} B A_k \]

Determine the maximum possible value of \( S \) as a function of \( n \) and \( R \).

Answer: `n (R + r)`

## 0924 | score=0.333 | algebra

Let $f(x) = x^5 + ax^4 + bx^3 + cx^2 + dx + e$ be a polynomial with real coefficients such that $f(1) = 1$, $f(2) = 2$, $f(3) = 3$, and $f(4) = 4$. Find the value of $a + b + c + d + e$.

Answer: `0`

## 0925 | score=0.556 | combinatorics

Determine the number of ways to color the vertices of a regular pentagon using 3 colors such that no two adjacent vertices share the same color.

Answer: `30`

## 0926 | score=0.333 | number_theory

Let \( P(x) \) be a polynomial of degree 4 with integer coefficients, such that \( P(1) = 17 \), \( P(2) = 34 \), \( P(3) = 51 \), \( P(4) = 68 \), and \( P(5) = 85 \). Find the largest integer \( n \) such that \( P(n) = n^2 + n + 1 \).

Answer: `5`

## 0927 | score=0.444 | number_theory

Consider a sequence of positive integers \( a_1, a_2, a_3, \ldots \) defined as follows:
\[ a_1 = 1, \]
\[ a_{n+1} = a_n^2 - 2 \text{ for all } n \geq 1. \]
Prove that for any positive integer \( k \), the number \( a_k \) is a factor of \( a_{2k} \).

Answer: `a_k \mid a_{2k}`

## 0928 | score=0.556 | number_theory

Consider the infinite sequence defined by \(a_n = n^2 + n + 1\). Determine all pairs of positive integers \((x, y)\) such that \(a_x\) divides \(a_y\) and \(x < y\). Further, find the sum of all distinct values of \(y\) for which such a pair exists.

Answer: `13`

## 0929 | score=0.625 | geometry

In a magical forest, there are $100$ trees arranged in a circle. Each tree has a unique integer label from $1$ to $100$. A fairy starts at tree $1$ and moves clockwise around the circle. At each tree $n$, the fairy flips a biased coin that lands heads with probability $\frac{n}{100}$. If the coin lands heads, the fairy moves to the next tree; if tails, she stays at the current tree. Find the expected number of trees the fairy visits before returning to tree $1$.

Answer: `100`

## 0930 | score=0.333 | number_theory

Let \( f(x) \) be a polynomial of degree 4 with integer coefficients such that \( f(1) = 2, f(2) = 5, f(3) = 10, \) and \( f(4) = 17. \) Find the smallest positive integer \( n \) for which \( f(n) = n^2. \)

Answer: `5`

## 0931 | score=0.556 | geometry

Determine all positive integers \( n \) for which there exists a finite set of \( n \) points in the plane, satisfying the following conditions: every three points out of the \( n \) points are vertices of a non-obtuse triangle, and given any four points out of the \( n \) points, no three lie on a line and one of these four points lies inside the triangle formed by the other three.

Answer: `3, 4`

## 0932 | score=0.556 | geometry

Consider the function \(f(x) = \frac{1}{x^2 + 1}\) defined on the interval \([0, \infty)\). Let \(A\) be the area under the curve of \(f(x)\) from \(x = 0\) to \(x = \infty\). 

Define a sequence \((a_n)\) as follows: \(a_1 = A\), and for \(n \geq 2\), \(a_n = \frac{1}{n} \sum_{k=1}^{n-1} a_k\). Prove that the sequence \((a_n)\) converges and find its limit.

Answer: `\frac{\pi}{2}`

## 0933 | score=0.556 | number_theory

Let \( f(x) \) be a polynomial of degree 3 with integer coefficients such that \( f(1) = 10 \), \( f(2) = 20 \), and \( f(3) = 30 \). Find the value of \( f(4) \).

Answer: `40`

## 0934 | score=0.556 | geometry

In the complex plane, consider the points \(A, B, C\) representing the roots of the polynomial \(z^3 - 3z^2 + 5z - 7 = 0\). Let \(D\) be the midpoint of \(AC\). If the angle \(\angle BOD = 90^\circ\), where \(O\) is the origin, find the real part of the product of the coordinates of point \(D\).

Answer: `1`

## 0935 | score=0.444 | number_theory

Let \( p(x) = x^5 - 5x^4 + 10x^3 - 10x^2 + 5x - 1 \). Find the smallest positive integer \( k \) such that \( p(p(k)) = k \).

Answer: `1`

## 0936 | score=0.333 | geometry

Find the smallest positive integer \( n \) such that the equation
\[
x^4 - 10x^3 + nx^2 + 10x + 1 = 0
\]
has four distinct real roots, where the sum of the squares of these roots equals 120.

Answer: `10`

## 0937 | score=0.667 | algebra

Let $f(x)$ be a real-valued function satisfying the property that for any real number $x$, $f(x + 1) + f(x) = 2x^2 - 4x + 1$.
Find the sum of all possible values of $f(100) + f(101)$, expressed as a simplified fraction or a simple radical.

Answer: `19601`

## 0938 | score=0.556 | number_theory

Consider a sequence of positive integers \(a_1, a_2, a_3, \ldots, a_n\) such that \(a_1 = 1\) and for all \(k \geq 2\), \(a_k\) is the smallest integer greater than \(a_{k-1}\) that is relatively prime to \(a_{k-1}\). Determine the value of \(a_{100}\).

Answer: `100`

## 0939 | score=0.556 | geometry

In a coordinate plane, consider a sequence of points \( P_1, P_2, P_3, \ldots \) where \( P_n \) has coordinates \( (n, a_n) \). The points are constructed such that the line segment from \( P_{n-1} \) to \( P_n \) forms a right angle with the line segment from \( P_n \) to \( P_{n+1} \), and all segments have the same length \( d \). If \( P_1 \) is at \( (1, 0) \), determine the sum of the \( y \)-coordinates of the first 2024 points in the sequence.

### Note
You may use any mathematical tools and concepts at your disposal to solve this problem.

Answer: `0`

## 0940 | score=0.667 | geometry

Let \( f(x) \) be a polynomial with integer coefficients satisfying \( f(0) = f(1) = 1 \) and \( f(n) > 0 \) for all integers \( n \). Find the minimum possible degree of \( f(x) \) such that there exists an integer \( k \) for which \( f(k) \) is a perfect square.

Answer: `2`

## 0941 | score=0.333 | geometry

Find all positive integers \( n \) such that the number of positive divisors of \( n \) is equal to the number of digits in the decimal representation of \( n \). Prove that if \( n \) satisfies this condition, then \( n \) must be a perfect square or twice a perfect square.

Answer: `1, 11, 13, 17, 19`

## 0942 | score=0.333 | number_theory

Let \(S\) be the set of all non-empty subsets of \(\{1, 2, 3, \ldots, 10\}\). For each subset \(A \in S\), define \(f(A)\) as the sum of all elements in \(A\). How many subsets \(A\) of \(S\) exist such that \(f(A)\) is divisible by 5?

Answer: `512`

## 0943 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \ldots + x + 1 \) can be written as the product of two non-constant polynomials with integer coefficients.

Answer: `3`

## 0944 | score=0.556 | geometry

Let \( f(n) \) be a function defined on the positive integers such that \( f(1) = 1 \) and for \( n \geq 1 \), \( f(n+1) = f(n) + \left\lfloor \sqrt{f(n)} \right\rfloor \). Find the smallest positive integer \( m \) such that \( f(m) \) is a perfect square greater than 1.

Answer: `4`

## 0945 | score=0.556 | algebra

Let $a$, $b$, $c$, and $d$ be real numbers such that $a + b + c + d = 4$. Find the minimum value of
\[
\frac{a^2}{1 + a^2} + \frac{b^2}{1 + b^2} + \frac{c^2}{1 + c^2} + \frac{d^2}{1 + d^2}.
\]

Answer: `\frac{16}{17}`

## 0946 | score=0.444 | number_theory

Find the smallest positive integer \( n \) such that the product of all prime numbers less than \( n \) is congruent to 1 modulo \( n \). That is, find the smallest \( n \) for which \(\prod_{p < n, p \text{ prime}} p \equiv 1 \pmod{n}\).

Answer: `2`

## 0947 | score=0.778 | geometry

Find all pairs of positive integers (m, n) such that 3^m + 4^n is a perfect square.

Answer: `(2, 2)`

## 0948 | score=0.444 | geometry

Find all integers \( n \geq 3 \) such that there exists a convex \( n \)-sided polygon \( P_1P_2\ldots P_n \) with the following properties:
1. The side lengths of \( P_1P_2\ldots P_n \) are distinct integers.
2. There is a point \( M \) inside \( P_1P_2\ldots P_n \) such that for each \( k \) from 1 to \( n \), the line segment \( M P_k \) is perpendicular to the side \( P_k P_{k+1} \) (where \( P_{n+1} = P_1 \)).

If no such integers \( n \) exist, state that explicitly. Otherwise, for each valid \( n \), specify the side lengths of the polygon.

Answer: `3`

## 0949 | score=0.667 | number_theory

Let \( f: \mathbb{Z} \rightarrow \mathbb{Z} \) be a function such that for all integers \( x \) and \( y \), we have
\[ f(x^2 - y^2) = (f(x))^2 - (f(y))^2. \]
If \( f(1) = 2 \), find all possible values of \( f(2024) \).

Answer: `4048`

## 0950 | score=0.556 | number_theory

Let \( S \) be the set of all integers \( n \) such that \( 1 \leq n \leq 100 \) and \( n \) is a product of distinct primes. Define \( f(n) \) as the number of distinct ways to express \( n \) as a product of two positive integers \( a \) and \( b \) where \( a \leq b \). Find the number of integers \( n \) in \( S \) for which \( f(n) \) is odd.

Answer: `0`

## 0951 | score=0.667 | geometry

Let $ABC$ be an acute triangle with circumcenter $O$ and orthocenter $H$. Let $D$, $E$, and $F$ be the feet of the altitudes from $A$, $B$, and $C$ respectively. The line through $D$ parallel to $BC$ intersects $EF$ at $P$. If $M$ is the midpoint of $BC$ and $N$ is the reflection of $M$ over $EF$, find the ratio of the area of triangle $PNO$ to the area of triangle $ABC$.

Answer: `\frac{1}{4}`

## 0952 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + 1 \) has no real roots and \( P(x) \) divides \( x^{2023} + 1 \).

Answer: `7`

## 0953 | score=0.444 | geometry

In a unique town, the streets are laid out in a perfect grid. The town square is at the center, and the streets are labeled with numbers representing their distance from the town square. If a person starts at the town square and wants to reach the corner of the 5th street and the 7th street, but they can only move north or east, how many different paths can they take that never go above the diagonal path from the town square to the destination?

Answer: `42`

## 0954 | score=0.333 | geometry

Let \( \triangle ABC \) be a triangle with sides \( AB = 13 \), \( BC = 14 \), and \( CA = 15 \). Let \( D \) be a point on \( BC \) such that \( AD \) is an altitude. Points \( E \) and \( F \) are on \( AB \) and \( AC \) respectively, such that \( DE \) and \( DF \) are angle bisectors of \( \angle ADC \). If the area of \( \triangle DEF \) is \( \frac{1}{n} \) of the area of \( \triangle ABC \), find the value of \( n \).

Answer: `4`

## 0955 | score=0.444 | number_theory

What is the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + ax^{n-1} + bx^{n-2} + \cdots + k \) with integer coefficients has a root that is a rational number and the product of the roots of \( P(x) \) is \(-120\), where \( a, b, \ldots, k \) are integers?

Answer: `1`

## 0956 | score=0.556 | number_theory

Determine all positive integers \( n \) for which the equation \( n^2 + n + 1 = k^2 \) holds for some integer \( k \).

Answer: `0`

## 0957 | score=0.556 | geometry

Given a convex quadrilateral \(ABCD\) with \(AB = 3\), \(BC = 4\), \(CD = 5\), and \(DA = 6\). Let \(M\), \(N\), \(P\), and \(Q\) be the midpoints of \(AB\), \(BC\), \(CD\), and \(DA\), respectively. The quadrilateral \(MNPQ\) is formed by connecting these midpoints. If the area of quadrilateral \(MNPQ\) is equal to the area of triangle \(ABC\), find the length of diagonal \(BD\).

Answer: `5`

## 0958 | score=0.333 | number_theory

Let \( P(x) \) be a polynomial of degree 4 with integer coefficients such that \( P(1) = 2024 \), \( P(2) = 2026 \), and \( P(3) = 2028 \). If \( P(x) \) has exactly two distinct integer roots, find the sum of these roots.

Answer: `3`

## 0959 | score=0.778 | number_theory

Find all integers \( n \) such that the polynomial \( P(x) = x^3 - nx + n \) has at least one integer root.

Answer: `0, 8`

## 0960 | score=0.556 | other

In the complex plane, let \( z \) be a complex number such that \( z^4 = 1 \) and \( z^2 \neq 1 \). Find the value of
\[ \frac{z}{1 + z^3} + \frac{z^2}{1 + z^6} + \frac{z^3}{1 + z^9}. \]

Answer: `-1`

## 0961 | score=0.333 | number_theory

Find the number of ordered pairs \((a, b)\) of positive integers such that \(a, b \leq 100\) and \(ab = \left\lfloor \frac{a}{b} \right\rfloor + \left\lfloor \frac{b}{a} \right\rfloor\).

Answer: `0`

## 0962 | score=0.778 | algebra

Let \(a, b, c\) be positive real numbers such that \(a + b + c = 1\). Prove that:
\[
\frac{a}{1 + b^3} + \frac{b}{1 + c^3} + \frac{c}{1 + a^3} \geq \frac{3}{4}.
\]

Answer: `\frac{3}{4}`

## 0963 | score=0.444 | geometry

Find all positive integers \( n \) for which the sum of the digits of \( n \) in base 10 is equal to the product of the digits of \( n \) in base 10, and additionally, \( n \) is a perfect square.

Answer: `1, 4, 9`

## 0964 | score=0.444 | geometry

In triangle \( ABC \), points \( D \) and \( E \) are on sides \( AB \) and \( AC \) respectively, such that \( DE \) is parallel to \( BC \). If the length of \( AD \) is one-third the length of \( AB \) and the length of \( AE \) is one-fourth the length of \( AC \), find the ratio of the area of triangle \( ADE \) to the area of triangle \( ABC \). Express your answer as a common fraction.

Answer: `\frac{1}{12}`

## 0965 | score=0.333 | geometry

In a small town, there are 12 houses arranged in a circle. Each house is uniquely numbered from 1 to 12. Every day, a mail carrier delivers a letter to every house, but the delivery sequence changes based on a special rule. The mail carrier starts at house 1 and moves in a clockwise direction, delivering a letter to the current house. After delivering to a house, the mail carrier skips an increasing number of houses equal to the day of the month. For example, on the 1st of the month, the mail carrier skips 1 house, on the 2nd, 2 houses, and so on. If the mail carrier starts on the 1st of the month and continues this pattern, after 12 days, how many different houses will have received a letter on each of those days?

Answer: `12`

## 0966 | score=0.556 | number_theory

A sequence of positive integers \(\{a_n\}\) is defined by \(a_1 = 1\), \(a_2 = 2\), and for all \(n \geq 3\), \(a_n\) is the smallest positive integer such that no three distinct terms \(a_i, a_j, a_k\) (where \(i < j < k\)) satisfy \(a_i + a_j + a_k = a_n\). Find the value of \(a_{100}\).

Answer: `100`

## 0967 | score=0.778 | geometry

A sequence of integers \(a_1, a_2, a_3, \ldots\) is defined by \(a_1 = 2\) and \(a_{n+1} = 2a_n + 3n\) for \(n \geq 1\). Find the smallest positive integer \(k\) such that \(a_k\) is a perfect square.

Answer: `4`

## 0968 | score=0.778 | geometry

Let \( ABC \) be a triangle with \( \angle BAC = 60^\circ \). Let \( D \) be the foot of the altitude from \( B \) to \( AC \), and let \( E \) be the foot of the altitude from \( C \) to \( AB \). The circumcircle of triangle \( ADE \) intersects \( BC \) again at \( F \). Prove that \( \angle BFD = 90^\circ \).

Answer: `90^\circ`

## 0969 | score=0.556 | number_theory

Let \( S \) be a set of integers from 1 to 100 inclusive. A subset \( A \) of \( S \) is called "special" if the sum of any two distinct elements of \( A \) is not divisible by 5. Determine the maximum possible size of a special subset \( A \) of \( S \).

Find the value of \( n \), where \( n \) is the maximum possible size of \( A \).

Answer: `60`

## 0970 | score=0.333 | number_theory

Find all integers \( n \) such that the sum of the digits of \( n^2 \) is equal to \( n \).

Answer: `1, 2, 3, 9`

## 0971 | score=0.556 | geometry

Let $S$ be a finite set of points in the plane, with no three points collinear. For each pair of points $P$ and $Q$ in $S$, draw the circle with diameter $PQ$. Prove that there exists a point $X$ in the plane such that at least half of the circles drawn pass through $X$.

Answer: `X`

## 0972 | score=0.333 | combinatorics

A sequence of numbers \(a_1, a_2, a_3, \ldots\) is defined by \(a_1 = 1\) and for \(n \geq 2\), \(a_n = \frac{a_{n-1}}{2}\) if \(n\) is even, and \(a_n = a_{n-1} + \frac{1}{2^n}\) if \(n\) is odd. Find the value of \(a_{2023}\).

Answer: `1`

## 0973 | score=0.333 | geometry

In the Cartesian coordinate system, consider a circle \(C\) with radius \(r\) centered at the origin. A point \(P\) moves along the circumference of \(C\) with constant angular velocity \(\omega\). Let \(Q\) be a fixed point on the circumference of \(C\) that does not coincide with \(P\). At any given time \(t\), the line segment \(PQ\) is extended to intersect the circle \(C\) again at point \(R\). Find the value of \(t\) for which the area of triangle \(PQR\) is maximized. Express your answer in terms of \(r\) and \(\omega\).

Answer: `\frac{\pi}{2\omega}`

## 0974 | score=0.778 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + ax + b \) has exactly one real root, where \( a \) and \( b \) are positive real numbers. Prove your answer.

Answer: `1`

## 0975 | score=0.667 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that the equation \( x^2 + y^2 = n \) has no integer solutions. Find the smallest positive integer \( k \) for which there exist exactly \( k \) consecutive integers \( a, a+1, \ldots, a+k-1 \) such that none of these integers belong to \( S \).

Answer: `4`

## 0976 | score=0.667 | geometry

In the complex plane, consider a triangle \(ABC\) with vertices at \(A = 1\), \(B = i\), and \(C = -1\). Let \(D\) be the midpoint of \(BC\). The circle centered at \(D\) passing through \(C\) intersects the real axis at points \(P\) and \(Q\) (with \(P\) to the left of \(Q\)). Find the length of \(PQ\).

Answer: `1`

## 0977 | score=0.778 | geometry

A regular octagon is inscribed in a circle of radius 1. Let P be a point inside the circle such that the sum of the squares of its distances from the vertices of the octagon is minimized. Find the value of this minimum sum, expressed in the form \(a + b\sqrt{c}\), where \(a\), \(b\), and \(c\) are integers, and \(c\) is not divisible by any prime squared. Determine \(a + b + c\).

Answer: `9`

## 0978 | score=0.778 | number_theory

Find all positive integers \( n \) for which the equation
\[ x_1^2 + x_2^2 + \cdots + x_n^2 = n \]
has a solution in integers \( x_1, x_2, \ldots, x_n \) such that \( x_1, x_2, \ldots, x_n \) are all distinct.

Answer: `1`

## 0979 | score=0.444 | geometry

In the coordinate plane, consider the ellipse defined by the equation \(\frac{x^2}{a^2} + \frac{y^2}{b^2} = 1\) where \(a > b > 0\). A line through the point \((0, 1)\) intersects the ellipse at two points \(P\) and \(Q\). Let \(O\) be the origin. If the product of the distances from \(O\) to \(P\) and from \(O\) to \(Q\) is a constant \(k\), find the value of \(k\) in terms of \(a\) and \(b\).

Answer: `b^2`

## 0980 | score=0.444 | algebra

Find all real numbers \( x \) that satisfy the equation \( \sin(x) + \sin(2x) + \sin(3x) = 0 \) and \( 0 \leq x < 2\pi \).

Answer: `0, \pi, \frac{\pi}{2}, \frac{3\pi}{2}, \frac{2\pi}{3}, \frac{4\pi}{3}`

## 0981 | score=0.444 | other

在三维空间中，给定四个点A(0,0,0)，B(1,0,0)，C(0,1,0)，D(0,0,1)。求是否存在一个点P，使得P到这四个点的距离之和最小？如果存在，求出该点P的坐标。

Answer: `\left( \frac{1}{4}, \frac{1}{4}, \frac{1}{4} \right)`

## 0982 | score=0.333 | number_theory

Let $S$ be the set of all ordered triples of integers $(a_1, a_2, a_3)$ with $1 \leq a_i \leq 10$ for all $1 \leq i \leq 3$. Each ordered triple in $S$ generates a sequence according to the rule $a_n=a_{n-1}\cdot |a_{n-2}-a_{n-3}|$ for all $n\geq 4$. Find the number of such sequences for which $a_n=0$ for some $n$.

Answer: `280`

## 0983 | score=0.333 | geometry

Let \( ABC \) be a triangle with circumradius \( R \) and inradius \( r \). Let \( D \) be a point on the circumcircle of \( \triangle ABC \) such that \( AD \) is a diameter of the circumcircle. Let \( P \) and \( Q \) be the points of tangency of the incircle of \( \triangle ABC \) with sides \( AB \) and \( AC \) respectively. Prove that the line \( PQ \) intersects the segment \( BC \) at a point \( T \) such that the area of \( \triangle ABT \) is equal to the area of \( \triangle ACT \). Find the length of \( AT \) in terms of \( R \) and \( r \).

Answer: `\sqrt{R^2 - r^2}`

## 0984 | score=0.333 | number_theory

Let $P(x)$ be a polynomial of degree 4 with integer coefficients such that $P(1) = 5$, $P(2) = 11$, $P(3) = 19$, and $P(4) = 29$. If the polynomial also satisfies $P(0) = 1$, find the sum of all possible values of $P(5)$.

Answer: `41`

## 0985 | score=0.444 | number_theory

Find all positive integers \( n \) such that the number of positive divisors of \( n^2 \) is equal to \( n \).

Answer: `1`

## 0986 | score=0.556 | geometry

In the plane, consider a set of \( n \) points \( P_1, P_2, \ldots, P_n \) such that no three points are collinear. For each point \( P_i \), define a function \( f_i(x) \) as the number of points \( P_j \) for which the area of the triangle \( \triangle P_iP_jP_k \) (where \( P_k \) is any point not equal to \( P_i \) or \( P_j \)) is an integer. If \( n = 6 \), find the maximum possible value of the sum \( f_1(1) + f_2(2) + \cdots + f_6(6) \).

Answer: `30`

## 0987 | score=0.444 | number_theory

Find all positive integers \( n \) such that the sum of the divisors of \( n \), excluding \( n \) itself, equals \( n \times \left\lfloor \frac{n}{10} \right\rfloor \).

Answer: `1`

## 0988 | score=0.333 | geometry

Let $f(x)$ be a polynomial with integer coefficients such that $f(100) = 2023$. Suppose that for some integer $n > 1$, the polynomial $f(x)$ can be expressed as a product of two non-constant polynomials with integer coefficients, each of degree less than $n$. If $f(x)$ has the property that for any integer $a$, $f(a)$ is a perfect square if and only if $a$ is a perfect square, find the smallest possible value of $n$.

Answer: `3`

## 0989 | score=0.750 | geometry

In the coordinate plane, let $A = (0, 0)$, $B = (3, 0)$, $C = (7, 0)$, and $D = (10, 0)$. Let $E$, $F$, $G$, and $H$ be points on segments $BC$, $CD$, $DA$, and $AB$, respectively, such that $BE = CF = DG = AH = 2$. Find the area of quadrilateral $EFGH$.

Answer: `0`

## 0990 | score=0.333 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(2) = 3 \) and \( P(5) = 7 \). If \( P(x) \) has a degree of 3, and \( P(n) \) is prime for some integer \( n > 5 \), find the smallest possible value of \( n \).

Answer: `6`

## 0991 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the sum of the first \( n \) terms of the sequence defined by \( a_k = k^3 - 3k^2 + 2k \) is a multiple of 100.

Answer: `25`

## 0992 | score=0.444 | number_theory

What is the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n - 2x^{n-1} + 3x^{n-2} - \cdots + (-1)^{n-1} nx - (-1)^n n \) has a real root greater than \( 1 \)?

Answer: `3`

## 0993 | score=0.556 | algebra

Find all functions \( f : \mathbb{R} \to \mathbb{R} \) such that for all real numbers \( x \) and \( y \), the following holds:
\[ f(x + f(y)) = f(x) + y^2. \]

Answer: `f(x) = x`

## 0994 | score=0.444 | number_theory

Find all integers \( n \) such that the polynomial \( P(x) = x^3 - 3nx^2 + (n^2 + 4)x - n \) has three distinct real roots that are all integers.

Answer: `2`

## 0995 | score=0.556 | geometry

Given an isosceles triangle $ABC$ with $AB = AC = 10$, and a point $P$ inside the triangle such that $\angle PBC = \angle PCA$. If $BP = 6$, find the length of $CP$.

Answer: `6`

## 0996 | score=0.444 | logic_puzzle

There exists a magical plant that doubles its size every day. If it starts at a height of 1 centimeter, on which day will its height exceed 10 meters? Assume no growth occurs overnight. The answer should be expressed in terms of the day number.

Answer: `10`

## 0997 | score=0.667 | number_theory

Define an arithmetic sequence $(a_n)$ by $a_0 = 0$ and $a_{n+1} = a_n + n + 1$ for all $n \geq 0$. Consider the sequence of partial sums $S_k = \sum_{i=0}^k a_i$. Show that there exists a positive integer $m$ such that $S_m$ is divisible by $2024$ and find the smallest such $m$.

Answer: `22`

## 0998 | score=0.778 | number_theory

Consider a sequence of integers \(a_1, a_2, a_3, \ldots\) defined by the recursive relation \(a_{n+1} = 2a_n + n^2\) for all integers \(n \geq 1\). Given that \(a_1 = 1\), find the remainder when \(a_{2024}\) is divided by \(2024\).

Answer: `1`

## 0999 | score=0.667 | number_theory

Let \( P(x) \) be a monic polynomial of degree \( 6 \) such that \( P(1) = 1 \), \( P(2) = 2 \), and \( P(3) = 3 \). If \( P(x) \) has integer roots, what is the sum of all possible values of \( P(0) \)?

Answer: `0`

## 1000 | score=0.556 | number_theory

Let \( f(x) = x^3 - 3x + 1 \). Prove that for any integer \( k \), the equation \( f(x) = k \) has at most three distinct real solutions. Additionally, determine the conditions under which the equation has exactly three distinct real solutions.

Answer: `-1 < k < 3`

## 1001 | score=0.333 | number_theory

A sequence of positive integers \( a_1, a_2, a_3, \ldots \) is defined as follows:
\[ a_1 = 1 \]
\[ a_{n+1} = a_n + d_n \]
where \( d_n \) is the smallest positive integer greater than \( a_n \) that is relatively prime to \( a_n \). Find the smallest positive integer \( k \) such that \( a_k \) is a prime number greater than 100.

Answer: `7`

## 1002 | score=0.333 | geometry

A convex quadrilateral $ABCD$ has side lengths $AB = 6$, $BC = 7$, $CD = 8$, and $DA = 9$. If the diagonals $AC$ and $BD$ intersect at point $P$ such that $\frac{AP}{PC} = \frac{2}{3}$ and $\frac{BP}{PD} = \frac{1}{3}$, find the area of quadrilateral $ABCD$.

Answer: `42`

## 1003 | score=0.444 | geometry

In a high-dimensional space, consider a sequence of points \(P_1, P_2, \ldots, P_n\) such that the distance between any two consecutive points \(P_i\) and \(P_{i+1}\) is exactly \(1\). For every \(i\), let \(d_i\) be the Euclidean distance from \(P_1\) to \(P_i\) in the plane defined by the coordinates of the first three points \(P_1, P_2, P_3\). Determine the maximum possible value of \(d_4\) if \(P_1\) is at the origin \((0,0)\), \(P_2\) is at \((1,0)\), and \(P_3\) is at \((\frac{1}{2}, \frac{\sqrt{3}}{2})\).

Answer: `2`

## 1004 | score=0.333 | number_theory

Let $S$ be the set of all positive integers that can be expressed as the sum of two positive integers $a$ and $b$ such that $a^2 + b^2 = n^2$ for some positive integer $n$. Find the smallest positive integer $k$ such that there exists a positive integer $n$ for which $n$ can be expressed as the sum of $k$ distinct elements of $S$.

Answer: `2`

## 1005 | score=0.778 | algebra

In the town of Polyvago, there is a unique bookstore called "Elemental Parchment." This bookstore sells math books with intricate designs, each representing a different mathematical concept. There are three types of math books: Algebric Sphinxes, Geometric Pyramids, and Numerical Cubes. Each Algebric Sphinx costs $15, each Geometric Pyramid costs $20, and each Numerical Cube costs $25.

On one particular day, the bookstore sold a total of 30 books and earned $620. It is known that the number of Algebric Sphinxes sold was equal to the sum of the Geometric Pyramids and Numerical Cubes sold. How many Numerical Cubes were sold?

Answer: `19`

## 1006 | score=0.778 | geometry

Given a triangle \( ABC \) with sides \( a, b, c \) opposite to angles \( A, B, C \) respectively, and an area \( K \), if \( a^2 + b^2 + c^2 = 8K \sqrt{3} \), determine the angles \( A, B, \) and \( C \).

Answer: `60^\circ, 60^\circ, 60^\circ`

## 1007 | score=0.333 | geometry

Let \( ABC \) be an acute triangle with circumcircle \( \Gamma \). Let \( D \) be the foot of the altitude from \( A \) to \( BC \), and let \( E \) and \( F \) be the points where the tangents to \( \Gamma \) at \( B \) and \( C \) intersect \( AD \). If \( AE = 6 \), \( AF = 10 \), and \( DE = 2 \), find the length of \( BC \).

Answer: `8`

## 1008 | score=0.444 | number_theory

Find all positive integers \( n \) such that the equation \( x^n + y^n = z^n + 1 \) has a solution in positive integers \( x, y, z \) with \( x, y, z \) being pairwise coprime.

Answer: `1`

## 1009 | score=0.778 | geometry

In triangle $ABC$, let $D$ be a point on side $BC$ such that $BD:DC = 2:3$. Let $E$ be a point on side $AB$ such that $AE:EB = 3:2$. If the area of triangle $ABC$ is 1, find the area of triangle $ADE$.

Answer: `\frac{6}{25}`

## 1010 | score=0.556 | geometry

Consider a sequence of numbers \( a_1, a_2, a_3, \ldots \) defined by the recurrence relation \( a_{n+2} = a_{n+1} + a_n \) for all \( n \geq 1 \), with initial conditions \( a_1 = 1 \) and \( a_2 = 2 \). Let \( S(k) \) denote the sum of the first \( k \) terms of this sequence. Determine the smallest positive integer \( k \) such that \( S(k) \) is a perfect square.

Answer: `1`

## 1011 | score=0.556 | other

In a certain town, there are 100 houses numbered from 1 to 100. A cat is playing a game where it starts at house number 1 and can move to any adjacent house (house number n can move to house number n-1 or n+1, except for house number 1, which can only move to house number 2, and house number 100, which can only move to house number 99). The cat makes exactly 100 moves and ends up at house number 50. How many distinct paths could the cat have taken to reach house number 50 after 100 moves?

Answer: `0`

## 1012 | score=0.444 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n - x^{n-1} + x^{n-2} - \cdots + x - 1 \) can be written as a product of two non-constant polynomials with integer coefficients.

Answer: `3`

## 1013 | score=0.444 | number_theory

Find all positive integers \( n \) such that \( n \) divides \( 2^n + 1 \).

Answer: `1, 3`

## 1014 | score=0.333 | geometry

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + (x+1)^n + (x+2)^n \) can be expressed as the sum of two squares of polynomials with integer coefficients.

Answer: `2`

## 1015 | score=0.444 | number_theory

Let \( f(x) \) be a polynomial with integer coefficients such that \( f(100) = 100 \) and \( f(0) = 2023 \). Find the smallest positive integer \( n \) such that \( f(n) \) is divisible by \( n \).

Answer: `1`

## 1016 | score=0.333 | geometry

A sequence of integers \(a_1, a_2, a_3, \ldots\) is defined by \(a_1 = 1\) and for \(n \geq 2\), \(a_n\) is the smallest positive integer such that \(a_n \cdot a_{n-1}\) is a perfect square and \(a_n\) has not appeared before in the sequence. Find the remainder when \(a_{2024}\) is divided by 1000.

Answer: `576`

## 1017 | score=0.778 | geometry

Find all positive integers \( n \) such that the sum of the squares of the first \( n \) positive integers is divisible by \( n^3 \).

Answer: `1`

## 1018 | score=0.556 | number_theory

In the kingdom of Numeria, there exists a peculiar tax system where the tax rate $t$ for an individual's income $I$ is determined by the sum of the digits of $I^2$. For instance, if someone earns an income of $235$, their tax rate is calculated as the sum of the digits of $235^2 = 55225$, which is $5 + 5 + 2 + 2 + 5 = 19$. Given that the maximum income for which an individual can earn in Numeria is $999$ numeraria units, find the income that maximizes the tax rate $t$. If there are multiple such incomes, provide the smallest one.

Answer: `999`

## 1019 | score=0.778 | geometry

Let \( S \) be a finite set of points in the plane such that no three points in \( S \) are collinear. For each point \( P \) in \( S \), define \( D(P) \) as the sum of the distances from \( P \) to all other points in \( S \). Let \( \mathcal{S} \) be the set of all such distances. Determine the maximum possible number of distinct distances in \( \mathcal{S} \), expressed in terms of the number of points \( n \) in \( S \).

Answer: `\frac{n(n-1)}{2}`

## 1020 | score=0.333 | number_theory

Find all positive integers \( n \) such that \( n \) divides \( 2^n + 3^n + 4^n \) and \( n \) is not divisible by any prime less than \( 10 \).

Answer: `1`

## 1021 | score=0.333 | geometry

What is the minimum number of unit cubes needed to construct a convex polyhedron with exactly 12 vertices, 18 edges, and 8 faces, such that each vertex is a 3-valent vertex and each face is a polygon with at most 4 sides?

Answer: `8`

## 1022 | score=0.556 | other

在一个无限序列 \{a_n\} 中，项满足 \(a_{n+1} = \frac{2a_n^2 + 3a_n + 1}{a_n^2 + 2}\)。已知 \(a_1 = 1\)，求 \(a_{2023}\) 的值。

Answer: `2`

## 1023 | score=0.778 | number_theory

Let \( S \) be the set of all positive integers that can be expressed as \( n^2 + 25n + 125 \) for some positive integer \( n \). Determine the smallest positive integer \( m \) such that no element of \( S \) is divisible by \( m \).

Answer: `2`

## 1024 | score=0.333 | number_theory

Find all positive integers \( n \) such that \( n \) divides \( 2^n + 1 \) and \( n+1 \) divides \( 2^{n+1} + 1 \). Prove your solution.

Answer: `1`

## 1025 | score=0.333 | number_theory

Let $S$ be the set of all positive integers that can be expressed as the sum of distinct powers of 3, where each power is less than or equal to $3^5$. If a number $N$ is chosen at random from $S$, what is the probability that $N$ is divisible by 11? Express your answer as a common fraction.

Answer: `\frac{1}{2}`

## 1026 | score=0.667 | number_theory

Let $f(x)$ be a polynomial with integer coefficients. Suppose that for every integer $n$, $f(n)$ is divisible by $f(n+1) - f(n)$. If $f(0) = 1$ and $f(1) = 2$, find the minimum possible value of $f(10)$.

Answer: `11`

## 1027 | score=0.444 | number_theory

Find all positive integers \( n \) such that the equation
\[
\frac{1}{n} + \frac{1}{n+1} + \frac{1}{n+2} + \frac{1}{n+3} = \frac{m}{n(n+1)(n+2)(n+3)}
\]
has a solution in positive integers \( m \) and \( n \).

Answer: `1`

## 1028 | score=0.667 | algebra

Let \( f(x) \) be a continuous function defined on the interval \( [0, 1] \) such that \( f(0) = 0 \) and \( f(1) = 1 \). Suppose \( g(x) = f(x) + \int_0^x f(t) \, dt \). Prove that there exists a unique \( c \in (0, 1) \) such that \( g(c) = c \).

Answer: `c`

## 1029 | score=0.667 | algebra

Let \( f(x) \) be a polynomial of degree 4 such that \( f(x) = x^4 + ax^3 + bx^2 + cx + d \), and it satisfies the conditions:
1. \( f(1) = 2 \)
2. \( f(2) = 4 \)
3. \( f(3) = 6 \)
4. \( f(4) = 8 \)
Find the value of \( f(5) \).

Answer: `34`

## 1030 | score=0.667 | geometry

Let $ABC$ be an acute triangle with circumcircle $\omega$. Let $D$ be the midpoint of arc $BC$ of $\omega$ not containing $A$. Suppose that the circle through $D$ tangent to $BC$ at $E$ intersects $\omega$ again at $F$. Let $G$ be the reflection of $D$ over $EF$. If $AD = 10$, $AB = 13$, and $AC = 14$, find the length of $BG$.

Answer: `10`

## 1031 | score=0.778 | combinatorics

A deck of 52 standard playing cards is shuffled. What is the probability that the first two cards drawn form a "full house" in terms of rank (i.e., they have the same rank, but not the same suit)? Express your answer as a common fraction in lowest terms.

Answer: `\frac{1}{17}`

## 1032 | score=0.444 | geometry

In the complex plane, let \( P(z) = z^4 + 2z^3 + 3z^2 + 2z + 1 \). Find the number of distinct complex numbers \( z \) such that \( |P(z)| = 1 \) and \( z \) lies on the unit circle.

Answer: `4`

## 1033 | score=0.667 | number_theory

In a certain game, a set of \( n \) distinct positive integers \( \{a_1, a_2, \ldots, a_n\} \) is used. A move consists of selecting a number \( a_i \) and replacing it with \( a_i + 1 \), \( a_i - 1 \), or leaving it unchanged. The game ends when all numbers in the set are equal. Determine the minimum number of moves required to make all numbers equal for the set \( \{2, 4, 6, 8, 10, 12, 14, 16, 18, 20\} \).

Answer: `50`

## 1034 | score=0.667 | algebra

Let \( f(x) = x^3 + ax^2 + bx + c \) be a cubic polynomial with real coefficients such that \( f(1) = 0 \), \( f(2) = 0 \), and \( f(-1) = 6 \). Determine the value of \( f(3) \).

Answer: `10`

## 1035 | score=0.778 | geometry

In a nonagon inscribed in a circle, each side length is uniquely determined by the angle it subtends at the center of the circle. Suppose the side lengths of the nonagon are represented by \(a_1, a_2, \ldots, a_9\) where \(a_i\) corresponds to the length of the side subtending an angle of \(\frac{i\pi}{9}\) radians at the center. Given that the area of the nonagon can be expressed as \(A = k \cdot r^2\), where \(r\) is the radius of the circle and \(k\) is a constant, find the value of \(k\).

(Continuation from the previous question, aiming to create a more complex problem)

If the nonagon is instead an equiangular nonagon (where all internal angles are equal), and the side lengths are given by \(b_1, b_2, \ldots, b_9\), find the ratio \(\frac{A}{k \cdot r^2}\) for this equiangular nonagon, where \(A\) is the area and \(k\) is the same constant from the original problem.

Answer: `1`

## 1036 | score=0.444 | algebra

A function $f: \mathbb{N} \to \mathbb{N}$ is called super-recursive if for any natural number $n$, $f(n+1) > f(n)$ and $f(n) > n$ for all $n > 1$. If $f(1) = 1$, find the number of such super-recursive functions $f$ that satisfy $f(10) < 100$.

Answer: `89`

## 1037 | score=0.778 | geometry

Let $f(x)$ be a function defined on the interval $[0, 1]$ such that $f(x) = x^3 - 3x^2 + 2x$. Let $S$ be the set of all points $(x, y)$ on the coordinate plane where $y = f(x)$ and $x$ is an irrational number in $[0, 1]$. If a point $P(x, y)$ is chosen uniformly at random from $S$, what is the probability that $P$ lies in the region where $y \geq 0$?

Answer: `1`

## 1038 | score=0.444 | number_theory

Let \( S \) be a set of positive integers. Define \( T(S) \) as the set of all positive integers that are not the sum of two elements of \( S \). Suppose \( S \) is the set of all positive integers greater than 2023. Determine the number of elements in the set \( T(S) \) that are less than or equal to 4046.

Answer: `4046`

## 1039 | score=0.444 | number_theory

In the Cartesian plane, a particle moves from the origin \( (0, 0) \) to the point \( (n, n) \) by taking unit steps either right or up, and then from \( (n, n) \) to \( (2n, 0) \) by taking unit steps either left or down. Let \( P_n \) be the number of distinct paths the particle can take. Prove that \( P_n \) is divisible by \( n+1 \).

Answer: `n+1`

## 1040 | score=0.333 | geometry

In the complex plane, let \( z_1 \) and \( z_2 \) be the roots of the equation \( z^2 - (2 + i)z + (1 - 3i) = 0 \). Find the area of the triangle formed by the points \( z_1 \), \( z_2 \), and the origin in the complex plane.

Answer: `\dfrac{3}{2}`

## 1041 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that when \( n \) is written in base 10, it contains exactly three distinct digits, and the sum of these digits is equal to \( 12 \). Find the number of elements in the set \( S \) that are less than 1000.

**Hint**: Consider the properties of the digits and their combinations.

Answer: `42`

## 1042 | score=0.556 | algebra

Let \(a, b, c\) be positive real numbers such that \(a + b + c = 1\). Find the minimum value of the expression
\[
\frac{a}{b^2 + c^2} + \frac{b}{a^2 + c^2} + \frac{c}{a^2 + b^2}.
\]

Answer: `\frac{9}{2}`

## 1043 | score=0.556 | number_theory

Consider a sequence of integers \(\{a_n\}_{n=1}^{\infty}\) defined by \(a_1 = 1\), and for \(n > 1\), \(a_n\) is the smallest positive integer such that no three of the first \(n\) terms form an arithmetic progression.

Let \(S\) be the set of all such sequences \(\{a_n\}_{n=1}^{\infty}\). Determine the number of elements in \(S\) that have exactly 2023 distinct terms.

Answer: `1`

## 1044 | score=0.667 | geometry

In triangle \( ABC \), point \( D \) lies on \( BC \) such that \( BD = 2DC \). Let \( E \) be the point where the angle bisector of \( \angle BAC \) intersects \( BC \). Prove that the ratio \( \frac{AE}{ED} \) is equal to \( \frac{AB}{AC} \).

Answer: `\frac{AB}{AC}`

## 1045 | score=0.556 | combinatorics

Let G be a labeled graph with n vertices. For each edge {u, v} in G, let p_{uv} = \frac{1}{2}. Define P(G) as the probability that, for every edge {u, v} in G, both endpoints u and v have the same color in a random 2-coloring of the vertices. Find the largest possible value of P(G) over all labeled graphs with n vertices.

Answer: `1`

## 1046 | score=0.667 | geometry

In the complex plane, consider a regular heptagon inscribed in a circle centered at the origin with radius 1. If we label the vertices of the heptagon as complex numbers \(z_1, z_2, \ldots, z_7\) such that they form the vertices in counterclockwise order, determine the minimum value of \(|z_i - \overline{z_j}|\) for \(i \neq j\).

Answer: `2 \sin \left( \frac{\pi}{7} \right)`

## 1047 | score=0.667 | geometry

What is the smallest positive integer \( n \) such that \( n \) is divisible by exactly 12 distinct positive integers, and \( n \) is a perfect square?

Answer: `144`

## 1048 | score=0.556 | number_theory

Let \( f(x) \) be a polynomial with integer coefficients such that \( f(1) = 17 \) and \( f(7) = 101 \). If \( f(x) \) has degree 2 and \( f(x) \equiv ax^2 + bx + c \pmod{7} \), where \( a, b, \) and \( c \) are integers, find the value of \( a + b + c \).

Answer: `17`

## 1049 | score=0.444 | combinatorics

In a small town, there are 5 houses in a row, each painted with a unique color. The colors used are red, blue, green, yellow, and purple. The conditions are as follows:
1. The red house is next to the blue house.
2. The green house is not next to the purple house.
3. The yellow house is not next to the green house.
4. The purple house is at one end of the row.
Determine the order of the houses from left to right.

Answer: `Purple, Red, Blue, Green, Yellow`

## 1050 | score=0.444 | other

In a certain high school, each student takes at least one of the subjects: mathematics, science, or history. It is known that the number of students taking only mathematics is 20, only science is 15, and only history is 10. Moreover, 30 students take both mathematics and science, 25 take both science and history, and 20 take both mathematics and history. If the total number of students in the school is 120, how many students take all three subjects?

Answer: `0`

## 1051 | score=0.444 | geometry

Find all pairs of positive integers $(a, b)$ such that $a^2 + b^2$ is a perfect square and $a^3 + b^3$ is a cube of a prime number.

Answer: `(3, 4)`

## 1052 | score=0.778 | geometry

Let \( f(n) \) be a function that counts the number of positive integer divisors of \( n \) that are also perfect squares. For a positive integer \( m \), define the sequence \( \{a_n\} \) by \( a_1 = m \) and \( a_{n+1} = f(a_n) \). If \( a_{2023} = 2023 \), find the smallest possible value of \( m \).

Answer: `2023`

## 1053 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the number of ordered pairs \((a, b)\) of integers satisfying \(a^2 + b^2 = n\) and \(a + b = 10\) is exactly 2.

Answer: `52`

## 1054 | score=0.556 | number_theory

Let $f: \mathbb{Z} \to \mathbb{Z}$ be a function defined by $f(n) = n^3 - n$. Determine the number of distinct values of $k$ such that there exist integers $m$ and $n$ satisfying both $f(m) = k$ and $f(n) = k + 1$.

Answer: `0`

## 1055 | score=0.667 | geometry

\nFind all positive integers \( n \) such that \( n^3 - 7n + 6 \) is a perfect square.\n

Answer: `1`

## 1056 | score=0.778 | number_theory

In a triangular grid, each cell can contain either a 0 or a 1. Starting from the topmost cell, each cell is filled with the sum of the two cells directly above it (mod 2). If the bottommost row consists of n cells all filled with 0, determine the number of distinct possible top cells if the second row contains 3 ones and 1 zeros.

Answer: `1`

## 1057 | score=0.778 | number_theory

Let \( f: \mathbb{Z}^+ \to \mathbb{Z}^+ \) be a function satisfying the following conditions for all positive integers \( x \) and \( y \):
1. \( f(xy) = f(x)f(y) \),
2. \( f(x) + f(y) = f(x + y) + 1 \) if \( x + y \) is a prime number.

Find all possible values of \( f(2023) \).

Answer: `1`

## 1058 | score=0.333 | number_theory

Let \( f: \mathbb{Z} \to \mathbb{Z} \) be a function satisfying the functional equation:  
\[ f(n) + f(n + 1) + f(n + 2) = 3n + 2 \]  
for all integers \( n \). If \( f(0) = 1 \), find the value of \( f(2023) \).

Answer: `2024`

## 1059 | score=0.556 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that \( n \) can be expressed as the sum of two or more consecutive positive integers. For example, \( 15 \) can be written as \( 7 + 8 \) or \( 4 + 5 + 6 \).  

Determine the smallest positive integer \( k \) such that there exists a subset \( T \subseteq S \) with \( |T| = k \), where the sum of any two distinct elements in \( T \) is not in \( S \).

Answer: `3`

## 1060 | score=0.778 | number_theory

Let \( f(x) = x^3 + ax^2 + bx + c \) be a cubic polynomial with real coefficients. Suppose that \( f(1) = 0 \) and the roots of \( f(x) \) are \( 1, \alpha, \) and \( \beta \), where \( \alpha \) and \( \beta \) are integers such that \( \alpha + \beta = -5 \). Find the value of \( a + b + c \).

Answer: `-1`

## 1061 | score=0.444 | algebra

A function $f(x)$ is defined for all real numbers $x$ and satisfies the following properties:
1. $f(1) = 1$.
2. For all $x, y$ in the domain of $f$, $f(x + y) = f(x) \cdot f(y)$.
3. The function $f(x)$ is strictly increasing.

Determine the value of $f(0)$ and find a possible formula for $f(x)$.

Answer: `1`

## 1062 | score=0.778 | number_theory

Find the smallest positive integer $n$ such that there exist integers $a$, $b$, and $c$ with $1 \leq a, b, c \leq 100$, satisfying the equation:
\[ n = a^3 + b^3 + c^3 - 3abc. \]

Answer: `4`

## 1063 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the equation \( x^3 - nx^2 + (n-1)x - n = 0 \) has exactly one real root. What is the sum of the real parts of the non-real roots of the polynomial?

Answer: `2`

## 1064 | score=0.444 | number_theory

Find the number of ordered pairs of positive integers (a, b) such that the equation x^2 - (a + b)x + ab = 0 has integral roots and the sum of the roots is less than 20.

Answer: `171`

## 1065 | score=0.667 | geometry

In triangle $ABC$, $D$ and $E$ are points on sides $AB$ and $AC$, respectively, such that $AD:DB = 1:2$ and $AE:EC = 1:3$. If the area of triangle $ABC$ is $36$ square units, find the area of triangle $ADE$.

Answer: `3`

## 1066 | score=0.444 | number_theory

Consider the function \( f(x) = x^5 + ax^4 + bx^3 + cx^2 + dx + e \) where \( a, b, c, d, \) and \( e \) are real numbers. It is given that for any positive real numbers \( p \) and \( q \) such that \( pq = 1 \), \( f(p) \) and \( f(q) \) are both integers. Determine all possible values of \( f(2) \).

Answer: `32`

## 1067 | score=0.778 | geometry

Let \( S \) be the set of all positive integers \( n \) such that \( 1 \leq n \leq 100 \) and \( n \) is a perfect square or a perfect cube. Find the sum of all distinct elements in the set \( S \).

Answer: `420`

## 1068 | score=0.333 | geometry

Find the smallest positive integer \( n \) such that \( n \) can be expressed as the sum of two squares in exactly three different ways, where the squares are positive integers and each representation is distinct. For example, 5 can be expressed as \( 1^2 + 2^2 \) and \( 2^2 + 1^2 \), but it is considered the same representation.

Answer: `50`

## 1069 | score=0.556 | algebra

Find all real numbers $x$ such that
\[
\frac{1}{x+1} + \frac{1}{x+2} = \frac{1}{x+3} + \frac{1}{x+4}.
\]

Answer: `\frac{-5 + \sqrt{3}}{2}, \frac{-5 - \sqrt{3}}{2}`

## 1070 | score=0.444 | geometry

In triangle \(ABC\), let \(D\) and \(E\) be points on sides \(AB\) and \(AC\) respectively such that \(BD = DE = EC\). Let \(P\) be the intersection of lines \(BE\) and \(CD\). If the area of triangle \(ABC\) is \(36\) square units, determine the ratio of the area of triangle \(BPE\) to the area of quadrilateral \(CDEP\).

Answer: `\frac{1}{2}`

## 1071 | score=0.444 | combinatorics

In a group of 2023 people, every pair of individuals either knows each other or is strangers. We define a "network" as a subset of these people such that within this subset, there exists a group of 506 people where any two individuals in this group either all know each other or are all strangers to each other. What is the minimum number of people that must be in the entire group to guarantee the existence of at least one such network?

Answer: `R(506, 506)`

## 1072 | score=0.556 | geometry

Find all pairs of positive integers $(a, b)$ such that $a^2 + 3b$ and $b^2 + 3a$ are both perfect squares. Additionally, prove that there are infinitely many such pairs.

Answer: `(1, 1)`

## 1073 | score=0.333 | geometry

Let \( S \) be the set of all positive integers \( n \) such that \( n \) can be expressed as the sum of two positive integers \( a \) and \( b \) where \( a \) and \( b \) are both perfect squares and \( a + b \) is also a perfect square. Find the smallest element of \( S \) that is greater than 1000.

Answer: `1024`

## 1074 | score=0.556 | number_theory

Consider a function \( f: \mathbb{Z}^+ \to \mathbb{Z}^+ \) such that for any positive integers \( a \) and \( b \), the following properties hold:
1. \( f(ab) = f(a)f(b) \)
2. \( f(a + b) \geq f(a) + f(b) \)

Find the minimum possible value of \( f(2024) \).

Answer: `2024`

## 1075 | score=0.667 | geometry

In a convex quadrilateral $ABCD$, the diagonals $AC$ and $BD$ intersect at point $P$. Given that $AP:PC = 3:2$ and $BP:PD = 1:4$, find the ratio of the area of $\triangle ABP$ to the area of $\triangle CPD$.

Answer: `\frac{3}{8}`

## 1076 | score=0.444 | number_theory

Find the smallest positive integer n such that there exist distinct positive integers a, b, c, d, and e satisfying the following conditions:

1. aⁿ + bⁿ = cⁿ
2. cⁿ + dⁿ = eⁿ
3. a < b < c < d < e
4. a + b + c + d + e < 1000

What is the smallest taxicab number that satisfies all these conditions?

Answer: `2`

## 1077 | score=0.778 | algebra

Find the number of ordered quadruples $(a,b,c,d)$ of real numbers such that $a\cdot b\cdot c\cdot d = 1$ and $a^2 + b^2 + c^2 + d^2 = 4$ with $a \ge b \ge c \ge d$.

Answer: `1`

## 1078 | score=0.444 | number_theory

Find the smallest positive integer \( n \) such that the equation \( x^3 - 3x + 1 = n \) has at least one real root \( x \) that is not an integer, and the derivative \( x^2 - 1 \) does not equal zero at that root.

Answer: `1`

## 1079 | score=0.333 | geometry

In triangle \(ABC\), let \(D\) be the foot of the perpendicular from \(A\) to side \(BC\). Let \(E\) be a point on line segment \(AC\) such that \(\angle ADE = \angle ABC\). If \(BD = 9\), \(DC = 16\), and \(AE = 12\), find the length of \(BE\).

Answer: `15`

## 1080 | score=0.667 | geometry

Let \( \mathbf{v} \) and \( \mathbf{w} \) be vectors in the plane such that \( \|\mathbf{v}\| = 3 \), \( \|\mathbf{w}\| = 4 \), and the angle between \( \mathbf{v} \) and \( \mathbf{w} \) is \( \theta \). Suppose there exists a linear transformation \( T \) represented by the matrix 
\[ 
\begin{pmatrix}
2 & -1 \\
1 & 3
\end{pmatrix}
\]
such that \( T(\mathbf{v}) = 7 \mathbf{v} \) and \( T(\mathbf{w}) = 7 \mathbf{w} \). Given that \( \cos \theta = \frac{3}{7} \), find the area of the triangle formed by the vectors \( T(\mathbf{v}) \), \( T(\mathbf{w}) \), and the zero vector.

Answer: `84\sqrt{10}`

## 1081 | score=0.333 | number_theory

A sequence of integers \(a_1, a_2, a_3, \ldots\) is defined as follows: \(a_1 = 1\) and for \(n \geq 2\), \(a_n\) is the smallest positive integer greater than \(a_{n-1}\) that satisfies the following condition: the set \(\{a_1, a_2, \ldots, a_n\}\) contains no three elements that are in arithmetic progression. Find the 100th term of the sequence.

Answer: `100`

## 1082 | score=0.556 | geometry

Let $ABC$ be an equilateral triangle with side length 1. Point $P$ is chosen inside the triangle such that the distances from $P$ to the sides $AB$, $BC$, and $CA$ are $x$, $y$, and $z$ respectively. Given that $x + y + z = \frac{\sqrt{3}}{3}$, determine the maximum possible area of the triangle $PBC$.

Answer: `\frac{\sqrt{3}}{6}`

## 1083 | score=0.778 | algebra

Let \( f(x) \) be a polynomial of degree 4 with real coefficients such that \( f(1) = 1 \), \( f(2) = 2 \), \( f(3) = 3 \), and \( f(4) = 4 \). Determine the value of \( f(5) + f(6) \).

Answer: `11`

## 1084 | score=0.667 | logic_puzzle

In a small town, there are $n$ houses in a row, numbered from $1$ to $n$. The mayor has decided to install surveillance cameras at these houses to monitor the town. Each camera can monitor exactly one house and can also monitor the house directly next to it in either direction. To ensure the entire town is covered without any redundancy, what is the minimum number of cameras required if the town has exactly $n$ houses? Formulate a general formula for the minimum number of cameras in terms of $n$.

Answer: `\left\lceil \frac{n}{2} \right\rceil`

## 1085 | score=0.444 | number_theory

Let $S$ be the set of all positive integers that can be expressed as the sum of distinct powers of 3, where each power is at most $3^4$. For example, $3^3 + 3^1 + 3^0 = 27 + 3 + 1 = 31$ is such a sum. Find the number of elements in $S$ that are divisible by 5.

Answer: `6`

## 1086 | score=0.444 | geometry

Find all positive integers \( n \) such that \( n^3 + 2n^2 + 3n + 4 \) is a perfect square.

Answer: `0`

## 1087 | score=0.444 | algebra

Consider the function \( f(x) \) defined for all real numbers \( x \) such that:
\[ f(x) = \begin{cases} 
      x^3 + 1 & \text{if } x \leq 0 \\
      \sqrt{x + 1} & \text{if } x > 0 
   \end{cases}
\]
Let \( g(x) = f(f(x)) \). Determine the number of distinct real solutions to the equation \( g(x) = x \).

Answer: `1`

## 1088 | score=0.667 | geometry

In a convex hexagon \(ABCDEF\), the diagonals \(AD\), \(BE\), and \(CF\) are concurrent at point \(G\). If \(AB = CD = EF = x\) and the perimeter of triangle \(AGC\) is \(3x + 10\), find the ratio of the area of triangle \(AGC\) to the area of hexagon \(ABCDEF\).

Answer: `\frac{1}{6}`

## 1089 | score=0.778 | other

In the realm of complex numbers, let \( z \) be a complex number such that \( z^3 = -1 \) and \( z \neq -1 \). If \( S = z + z^2 \), find the value of \( S^3 + 3S \).

Answer: `0`

## 1090 | score=0.556 | geometry

Find all positive integers \( n \) such that the sum of the squares of the first \( n \) odd positive integers is equal to the sum of the cubes of the first \( n \) even positive integers.

Answer: `1`

## 1091 | score=0.333 | number_theory

How many positive integers less than 1,000,000 contain the digit 5 at least once?

Answer: `468558`

## 1092 | score=0.778 | geometry

In the coordinate plane, consider a triangle \( \triangle ABC \) with vertices \( A(1, 2) \), \( B(4, 6) \), and \( C(6, 2) \). A point \( P \) is chosen inside the triangle such that the sum of the areas of triangles \( \triangle ABP \), \( \triangle BCP \), and \( \triangle CAP \) is minimized. Find the coordinates of point \( P \) and compute the minimum sum of these areas.

Answer: `10`

## 1093 | score=0.778 | number_theory

Let \( f: \mathbb{Z} \to \mathbb{Z} \) be a function such that for all integers \( x \) and \( y \), the following equation holds:
\[ f(x^2 + y^2) = f(x)^2 + f(y)^2. \]
Given that \( f(1) = 1 \), find the number of possible values of \( f(100) \).

Answer: `1`

## 1094 | score=0.667 | number_theory

Find the number of ordered pairs of positive integers \((a, b)\) such that \(a^2 + b^2 = ab(a + b)\) and \(a < b < 1000\).

Answer: `0`

## 1095 | score=0.333 | geometry

In a triangle \(ABC\), point \(D\) lies on side \(BC\) such that \(BD = 2CD\). The incircle of triangle \(ABC\) touches \(BC\) at point \(P\). If the area of triangle \(ABD\) is 36 and the area of triangle \(ABP\) is 24, find the length of \(BC\).

Assume all necessary lengths and areas are in the standard units of measurement.

Answer: `9`

## 1096 | score=0.667 | combinatorics

Given a regular hexagon with side length 1, color each vertex either red or blue. For each coloring, calculate the number of distinct pairs of vertices of the same color. How many distinct colorings result in exactly 6 pairs of vertices of the same color?

Answer: `2`

## 1097 | score=0.667 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(1) = 5 \) and \( P(2) = 10 \). Find the smallest positive integer \( n \) for which \( P(n) = n^2 \).

Answer: `5`

## 1098 | score=0.556 | algebra

Let \( f(x) \) be a continuous and differentiable function defined on the interval \([0, 1]\) such that \( f(0) = 0 \) and \( f(1) = 1 \). Additionally, let \( g(x) = \int_0^x f(t) \, dt \). Prove that there exists a point \( c \in (0, 1) \) such that \( f(c) = 2c \) and \( g(c) = c^2 \).

Answer: `c`

## 1099 | score=0.778 | number_theory

Determine the number of ordered pairs of integers \((x, y)\) such that \(x^2 + 4xy + 4y^2 + 3x + 6y - 2 = 0\).

Answer: `0`

## 1100 | score=0.667 | number_theory

Find all positive integers \( n \) such that \( n \) divides \( 3^n + 1 \).

Answer: `1, 2`

## 1101 | score=0.333 | geometry

In the coordinate plane, consider a square with vertices at \((0,0)\), \((1,0)\), \((1,1)\), and \((0,1)\). A point \(P\) is chosen randomly within the square. Let \(r\) be the distance from \(P\) to the nearest side of the square. Define a function \(f(r) = r^2\). Compute the expected value of \(f(r)\).

Answer: `\frac{1}{24}`

## 1102 | score=0.778 | number_theory

Find all prime numbers \( p \) such that \( p^2 + 6 \) is also a prime number.

Answer: `5`

## 1103 | score=0.333 | number_theory

Find all pairs of positive integers \( (x, y) \) such that \( x^3 + y^3 = (x + y)^2 \) and \( x, y \leq 100 \).

Answer: `(1, 2), (2, 1), (2, 2)`

## 1104 | score=0.333 | number_theory

Find all positive integers \( n \) such that \( 2^n + 3^n = m^2 \) for some integer \( m \).

Answer: `0`

## 1105 | score=0.556 | geometry

Find all positive integers \( n \) for which the number \( 2^n + 3^n \) is a perfect square.

Answer: `0`

## 1106 | score=0.333 | geometry

A sequence of positive integers \(a_1, a_2, a_3, \ldots\) is defined by \(a_1 = 1\), and for \(n \geq 1\), \(a_{n+1}\) is the smallest positive integer such that \(a_{n+1} + a_n\) is a perfect square. Find the remainder when \(a_{2023}\) is divided by 1000.

Answer: `276`

## 1107 | score=0.333 | number_theory

Consider a sequence of positive integers $a_1, a_2, \dots, a_n$ such that for each $i$ with $1 \leq i \leq n$, $a_i$ is a divisor of $a_{i+1}$. Define $b_i = \frac{a_{i+1}}{a_i}$ for each $i$ with $1 \leq i \leq n-1$. If $b_1 + b_2 + \dots + b_{n-1} = 2023$ and $a_1 = 1$, find the smallest possible value of $n$.

Answer: `1012`

## 1108 | score=0.556 | geometry

In the complex plane, let $z$ be a complex number such that $|z| = 1$ and $z^5 + \overline{z}^5 = \frac{1}{2}.$  Find the sum of all possible values of $z^7 + \overline{z}^7.$

Answer: `0`

## 1109 | score=0.778 | algebra

Let \( f(x) \) be a polynomial of degree 4 such that \( f(1) = 1, f(2) = 2, f(3) = 3, f(4) = 4, \) and \( f(5) = 5. \) Find the value of \( f(6) \).

Answer: `6`

## 1110 | score=0.444 | geometry

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^3 - 3x^2 + 2x + n \) has three distinct integer roots, and the sum of the squares of these roots is equal to 10.

Answer: `2`

## 1111 | score=0.333 | number_theory

Determine the smallest positive integer n such that there exist n distinct positive integers a₁, a₂, ..., a_n with the property that their product is divisible by all integers from 1 to n.

Answer: `1`

## 1112 | score=0.444 | number_theory

What is the least positive integer $n$ such that $n^2 - 4$ is divisible by both 7 and 11?

Answer: `2`

## 1113 | score=0.444 | geometry

Find all pairs of positive integers $(m, n)$ such that $m^2 + n$ is a multiple of $mn$ and $m^2 + n$ is a perfect square.

Answer: `(1, 1)`

## 1114 | score=0.556 | geometry

Let \( S \) be the set of all positive integers \( n \) such that \( \frac{n}{1000} \) is a perfect square, and \( \frac{1000}{n} \) is a perfect cube. How many elements are in the set \( S \)?

Answer: `1`

## 1115 | score=0.556 | geometry

Find all positive integers \( n \) such that \( n^2 + 3n + 2015 \) is a perfect square.

Answer: `2011`

## 1116 | score=0.667 | number_theory

Find all pairs of positive integers \((a, b)\) such that \(a^2 + b^2\) divides \(ab(a + b) - 1\).

Answer: `(1, 2), (2, 1)`

## 1117 | score=0.556 | geometry

A right circular cone with base radius $r$ and height $h$ is filled with water and then inverted into a hemisphere of the same radius $r$. Assuming no spillage occurs and the water reaches the very top of the hemisphere, what fraction of the hemisphere's volume is filled with water? Express your answer as a common fraction.

Answer: `\frac{1}{2}`

## 1118 | score=0.667 | algebra

Let \( P(x) \) be a polynomial with real coefficients such that \( P(0) = 1 \) and \( P(x) \) has \( n \) distinct real roots. Define the function \( Q(x) \) as the product of the distances from \( x \) to all the roots of \( P(x) \). That is, if the roots of \( P(x) \) are \( r_1, r_2, \ldots, r_n \), then \( Q(x) = (x - r_1)(x - r_2) \cdots (x - r_n) \). Find the sum of the coefficients of \( Q(x) \) in terms of \( n \).

Answer: `1`

## 1119 | score=0.444 | number_theory

Consider a sequence of positive integers \( a_1, a_2, \ldots, a_n \) such that for every \( i \) (1-based index), the number of divisors of \( a_i \) is exactly equal to the sum of the digits of \( i \). Define \( f(n) \) as the number of such sequences of length \( n \). Find the remainder when \( f(2024) \) is divided by 1000.

Answer: `001`

## 1120 | score=0.444 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a continuous function such that for all real numbers \( x \) and \( y \), \( f(x+y) = f(x)f(y) + f(x) + f(y) \). Given that \( f(0) = 0 \) and \( f \) is not identically zero, find the value of \( f(1) \).

Answer: `1`

## 1121 | score=0.667 | number_theory

What is the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n - x^{n-1} - \cdots - x - 1 \) has all its roots as complex numbers with positive real parts?

Answer: `3`

## 1122 | score=0.333 | geometry

Given a convex pentagon $ABCDE$ with diagonals $AC$, $BD$, and $BE$ intersecting at a common point $P$, and the lengths of the diagonals $AC = 10$, $BD = 15$, and $BE = 20$, determine the ratio of the area of triangle $APC$ to the area of quadrilateral $CPDE$. Express your answer as a simplified fraction.

Answer: `\frac{1}{2}`

## 1123 | score=0.556 | algebra

Find all functions \( f: \mathbb{R} \to \mathbb{R} \) such that for all real numbers \( x \) and \( y \),
\[ f(xf(y) + y) = f(xy) + x \]

Answer: `f(x) = x + 1`

## 1124 | score=0.556 | number_theory

A sequence \( S \) is defined recursively as follows: \( S_1 = 1 \), and for all \( n \geq 2 \), \( S_n = S_{n-1} + 2n - 1 \). Let \( P(k) \) be the product of the first \( k \) terms of the sequence \( S \). Determine the smallest positive integer \( k \) for which \( P(k) \) is divisible by \( 10^6 \).

Answer: `15`

## 1125 | score=0.556 | number_theory

Let $S$ be the set of all polynomials $P(x)$ with integer coefficients such that $P(1) = 2023$ and $P(2023) = 1$. Find the number of polynomials $P(x) \in S$ for which there exists a positive integer $n$ such that $P(n) = n^2$.

Answer: `1`

## 1126 | score=0.667 | number_theory

Find the number of functions \( f : \mathbb{Z} \to \mathbb{Z} \) such that for all integers \( x \) and \( y \), the following equation holds:
\[ f(x^2 + y^2) = (f(x))^2 + (f(y))^2. \]

Answer: `2`

## 1127 | score=0.556 | geometry

In a right triangle \(ABC\) with \(\angle ACB = 90^\circ\), \(D\) is the midpoint of \(BC\). A circle with diameter \(AD\) intersects the hypotenuse \(AB\) at \(E\), and the altitude from \(C\) to \(AB\) at \(F\). If the area of \(\triangle ABC\) is \(90\) square units and the length of \(AC\) is \(15\) units, find the length of segment \(EF\).

Answer: `6`

## 1128 | score=0.556 | number_theory

Let \( p \) be a prime number, and \( f: \mathbb{Z} \to \mathbb{Z} \) be a polynomial function of degree \( n \) such that \( f(1) = 2p \) and \( f(k) = k^2 + 2p \) for all \( k = 2, 3, \ldots, p-1 \). Find the remainder when \( f(p) \) is divided by \( p \).

Answer: `0`

## 1129 | score=0.667 | number_theory

Let \(S\) be a set of distinct positive integers. A subset \(T\) of \(S\) is called "compact" if the sum of any two elements in \(T\) is not in \(S\). What is the maximum number of elements in a compact subset \(T\) of the set \(S = \{1, 2, 3, \ldots, 20\}\)?

Answer: `10`

## 1130 | score=0.333 | number_theory

Find all triples of positive integers \((x, y, z)\) that satisfy the equation \(x^3 + y^3 + z^3 = 3xyz\).

Answer: `(x, x, x)`

## 1131 | score=0.444 | number_theory

Find all positive integers \( n \) such that there exist integers \( a_1, a_2, \ldots, a_n \) with \( 1 \leq a_i \leq n \) for all \( i \), and for any \( 1 \leq i < j \leq n \), the equation
\[ a_i + a_j = 2k \]
has no integer solution for \( k \) between \( 1 \) and \( n \).

Answer: `1`

## 1132 | score=0.444 | number_theory

设有一组从1到\( n \)的整数，每次操作可以从这组数中选择任意两个不同的数\( a \)和\( b \)，并将它们替换为\( \gcd(a, b) \)和\( \text{lcm}(a, b) \)。经过若干次操作后，最终剩下的一组数的乘积记为\( P \)。

问题：对于给定的\( n \)，求\( P \)的最小可能值。

Answer: `n!`

## 1133 | score=0.778 | number_theory

Given a positive integer \( n \), let \( S(n) \) be the sum of the digits of \( n \). Find the smallest positive integer \( n \) such that \( S(n) = S(n^2) \).

Answer: `1`

## 1134 | score=0.778 | number_theory

Let \( f(x) \) be a polynomial of degree 5 with integer coefficients such that \( f(1) = 2 \), \( f(2) = 4 \), \( f(3) = 6 \), \( f(4) = 8 \), and \( f(5) = 10 \). Determine the value of \( f(6) \).

Answer: `12`

## 1135 | score=0.778 | geometry

In a triangular park, three friends, Alice, Bob, and Carol, decide to meet at a point inside the triangle. Alice starts at a vertex and walks at a speed of 2 units per minute, Bob starts from another vertex and walks at 3 units per minute, while Carol starts from the third vertex and walks at 4 units per minute. They all walk towards the center of the triangle, which is the centroid. If the park is an equilateral triangle with side length 6 units, how long will it take for all three friends to meet at the centroid?

Answer: `\sqrt{3}`

## 1136 | score=0.556 | number_theory

Find all positive integers \( n \) such that there exists a polynomial \( P(x) \) of degree \( n \) with integer coefficients that satisfies the equation \( P(k) = k^3 \) for \( k = 1, 2, \ldots, n+1 \).

Answer: `3`

## 1137 | score=0.333 | sequence

A sequence \( a_1, a_2, a_3, \ldots \) is defined by \( a_1 = 1 \), \( a_2 = 2 \), and for \( n \geq 3 \),
\[
a_n = \frac{a_{n-1} + a_{n-2}}{2} + \frac{1}{n}.
\]
Find the value of \( a_{2024} \).

Answer: `2`

## 1138 | score=0.333 | number_theory

In the sequence defined by \(a_n = n^2 + 11n + 19\), let \(S\) be the set of all integers \(n\) such that \(1 \leq n \leq 100\) and \(a_n\) is a prime number. Determine the sum of all elements in \(S\).

Answer: `8`

## 1139 | score=0.778 | number_theory

Consider a finite sequence of positive integers \(a_1, a_2, ..., a_n\) where \(n \geq 3\). Each term \(a_i\) is defined as follows: If \(i = 1\), then \(a_1 = 1\). For \(i > 1\), \(a_i\) is the smallest positive integer not appearing in the subsequence \(\{a_1, a_2, ..., a_{i-1}\}\) that is greater than \(a_{i-1}\) and has no common factors other than 1 with any \(a_j\) for \(1 \leq j < i\).

Define a sequence of operations on this sequence: an operation consists of choosing an index \(k\) such that \(2 \leq k \leq n\) and replacing \(a_k\) with the next prime number larger than \(a_{k-1}\) if such a prime number does not already appear in the subsequence \(\{a_1, a_2, ..., a_{k-1}\}\). An operation is considered successful if no such prime number exists or if replacing \(a_k\) with it results in the subsequence no longer satisfying the defined properties.

Let \(P\) be the set of all successful sequences of operations that can be performed on a sequence of length \(n\). For \(n = 7\), find the number of sequences in \(P\) that end with the number 31.

Answer: `1`

## 1140 | score=0.667 | geometry

In the complex plane, consider a triangle \(ABC\) with vertices at \(A = 1\), \(B = 2 + i\), and \(C = 2 - i\). Let \(D\) be a point on the circumcircle of triangle \(ABC\) such that \(\angle ADB = 90^\circ\). Find the area of the triangle formed by the points \(D\), \(B\), and \(C\).

Answer: `2`

## 1141 | score=0.333 | number_theory

A sequence of positive integers \(\{a_n\}\) satisfies the recurrence relation \(a_{n+1} = a_n + 2a_{n-1}\) for all \(n \geq 2\), with initial conditions \(a_1 = 1\) and \(a_2 = 3\). Let \(S\) be the set of all positive integers \(k\) such that \(a_k\) is divisible by \(7\). Determine the smallest positive integer \(m\) for which \(m \in S\) and \(a_m\) is also divisible by \(9\).

Answer: `8`

## 1142 | score=0.333 | geometry

In the coordinate plane, let \( A = (0, 0) \), \( B = (a, 0) \), \( C = (b, c) \), and \( D = (d, e) \) be four distinct points such that \( A \), \( B \), \( C \), and \( D \) are vertices of a convex quadrilateral. The diagonals \( AC \) and \( BD \) intersect at point \( P \). Given that the area of quadrilateral \( ABCD \) is 2024 square units and the area of triangle \( APD \) is 333 square units, find the area of triangle \( BPC \).

Answer: `1691`

## 1143 | score=0.667 | number_theory

Determine the number of functions \( f : \mathbb{Z} \to \mathbb{Z} \) such that
\[ f(a) - a \equiv 0 \pmod{2} \]
and
\[ f(f(a) + b) = f(a^2 - b) + 4f(a) + 4b \]
for all integers \( a \) and \( b \).

Answer: `1`

## 1144 | score=0.444 | geometry

Let \( S \) be the set of all integers \( n \) such that \( 1 \leq n \leq 1000 \) and \( n \) can be expressed as the sum of three distinct positive integers, each raised to the power of three. For example, \( n = 3^3 + 4^3 + 5^3 = 27 + 64 + 125 = 216 \) is in \( S \). Determine the number of elements in \( S \) that are also perfect squares.

Answer: `0`

## 1145 | score=0.333 | number_theory

In the mystical town of Numeria, there exists a peculiar fruit shop that sells magical apples. The price of an apple is determined by a unique formula: the price of the nth apple is given by the equation P(n) = 2n^2 - 3n + 5. On a particular day, the shopkeeper decides to sell apples in bundles, where each bundle contains exactly 3 consecutive apples. What is the maximum total price a customer could pay for a bundle of 3 apples? Additionally, if the total price of any bundle must be a prime number, how many such prime-numbered bundles can the customer purchase?

Answer: `3`

## 1146 | score=0.556 | geometry

A circle with radius \( r \) is inscribed in a square, and four identical circles with radius \( s \) are tangent to each other and to the larger circle, one at each corner of the square. If the area of the region outside the four smaller circles but inside the larger circle is equal to the sum of the areas of the four smaller circles, find the ratio \( \frac{r}{s} \).

Answer: `2\sqrt{2}`

## 1147 | score=0.444 | number_theory

Find the smallest positive integer \( n \) such that the equation \( x^2 + y^2 = 2024z \) has at least one solution in integers \( x, y, \) and \( z \). Additionally, determine the number of distinct solutions \((x, y, z)\) that satisfy this equation when \( z = 1 \).

Answer: `0`

## 1148 | score=0.667 | number_theory

Let $P(x)$ be a polynomial with integer coefficients such that $P(0) = P(1) = 2023$ and $P(2) = 2024$. What is the smallest possible degree of $P(x)$?

Answer: `2`

## 1149 | score=0.778 | number_theory

Let \( \{a_n\} \) be a sequence defined by \( a_1 = 1 \), \( a_2 = 2 \), and for \( n \geq 3 \), \( a_n = a_{n-1} + 2a_{n-2} \). Find the remainder when \( a_{2024} \) is divided by 7.

Answer: `2`

## 1150 | score=0.778 | algebra

Let \( P(x) = x^4 - 6x^3 + 11x^2 - 6x + 1 \). If \( P(a) = P(b) = 0 \) for some real numbers \( a \) and \( b \), and \( a < b \), find the value of \( a + b \).

Answer: `3`

## 1151 | score=0.556 | geometry

In the plane, a circle with radius \( r \) is inscribed in an equilateral triangle with side length \( s \). A point \( P \) is chosen at random inside the triangle. What is the probability that the distance from \( P \) to the center of the circle is less than or equal to \( \frac{r}{2} \)?

Answer: `\frac{\pi \sqrt{3}}{36}`

## 1152 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) can be expressed as the product of two non-constant polynomials with integer coefficients.

Answer: `3`

## 1153 | score=0.444 | geometry

Let $ABC$ be a triangle with $AB = AC = 13$ and $BC = 10$. Let $D$ be a point on $BC$ such that $BD = 7$ and $CD = 3$. Let $E$ and $F$ be points on $AC$ and $AB$, respectively, such that $DE$ and $DF$ are perpendicular to $AC$ and $AB$, respectively. If $DE = DF$, find the length of $EF$.

Answer: `12`

## 1154 | score=0.556 | number_theory

Let $P(x)$ be a polynomial of degree $6$ with integer coefficients such that $P(1) = P(2) = P(3) = P(4) = P(5) = 11$. Find the remainder when $P(0) + P(6)$ is divided by $1000$.

Answer: `22`

## 1155 | score=0.778 | geometry

Let \( ABC \) be a triangle with circumradius \( R \). The lengths of the sides are \( a = BC \), \( b = AC \), and \( c = AB \). Consider the expression:
\[ E = \frac{a^2 + b^2 + c^2}{R^2} + \frac{abc}{R^3} \]
Given that \( E = 10 \), find the value of \( R \) if \( a = 3 \), \( b = 4 \), and \( c = 5 \).

Answer: `3`

## 1156 | score=0.556 | other

在正整数中，存在一种特殊的数列，其中每个数都是前一个数的两倍加1。例如，这个数列的前几项为1, 3, 7, 15, 31, ...。现在，给定一个正整数N，请问是否存在这样的数列，使得数列中的某一项等于N？如果存在，请找出最小的k，使得第k项等于N；如果不存在，请返回-1。

例如，对于N = 31，答案是1；对于N = 10，答案是-1。

Answer: `-1`

## 1157 | score=0.667 | geometry

Let \( \triangle ABC \) be a triangle with integer side lengths \( AB = 13 \), \( BC = 14 \), and \( CA = 15 \). A circle is inscribed in \( \triangle ABC \) touching \( BC \) at \( D \), \( CA \) at \( E \), and \( AB \) at \( F \). Let \( s = AE + BF + CD \). If \( s = \frac{m}{n} \) for relatively prime positive integers \( m \) and \( n \), find the value of \( m + n \).

Answer: `22`

## 1158 | score=0.556 | number_theory

In the Cartesian plane, let $P$ be the set of points $(x, y)$ where $x$ and $y$ are positive integers such that $x^2 + y^2 \leq 100$. A "jump" is defined as moving from a point $(x, y)$ to a point $(x', y')$ in $P$ where $|x - x'| + |y - y'| = 1$. Starting at $(1, 1)$, how many distinct sequences of jumps can one make to reach the origin $(0, 0)$ exactly after $20$ jumps? Remember, a sequence is distinct if it leads to a different sequence of points, and the order of jumps matters.

Answer: `184756`

## 1159 | score=0.667 | number_theory

Find all pairs of positive integers $(a, b)$ such that $a^2 + b^2$ is divisible by $ab + 1$.

Answer: `(1, 1)`

## 1160 | score=0.333 | geometry

Given a convex pentagon ABCDE with integer side lengths such that AB = CD = EA = 5, BC = DE = 3, and the internal angles are all distinct and greater than 30 degrees, find the maximum possible area of the pentagon ABCDE.

Answer: `48`

## 1161 | score=0.556 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients, and let \( n \) be a positive integer such that \( P(n) = 100 \). Suppose that there exists a positive integer \( m \) such that \( P(m) = 200 \). Determine the largest possible value of \( n + m \).

Answer: `200`

## 1162 | score=0.556 | algebra

Let \( f(x) \) be a continuous function on the interval \([0, 1]\) such that \( f(0) = 0 \) and \( f(1) = 1 \). Define the function \( g(x) = \int_0^x f(t) \, dt \). Prove that there exists a unique \( c \in (0, 1) \) such that \( g(c) = \frac{1}{2} \).

Answer: `c \in (0, 1)`

## 1163 | score=0.444 | geometry

Let \( S \) be a set of 2024 points in the plane, where no three points are collinear. Each pair of points \( P \) and \( Q \) in \( S \) defines a line segment \( PQ \). Let \( f(P, Q) \) be the number of points in \( S \) that lie strictly inside the triangle formed by points \( P \), \( Q \), and another point \( R \) chosen randomly from \( S \) (with \( R \neq P \) and \( R \neq Q \)).

Find the expected value of \( f(P, Q) \) over all pairs of points \( (P, Q) \) in \( S \).

Answer: `1011`

## 1164 | score=0.444 | algebra

Let $p(x)$ be a polynomial of degree 3, with coefficients in $\mathbb{Q}$, such that $p(1) = 0$, $p(2) = 3$, and $p(3) = 8$. Suppose there exists a rational number $r$ such that $p(r) = 5$. What is the value of $r$?

Answer: `2`

## 1165 | score=0.333 | other

在一个无限长的直线上，有无限多个等距排列的点，每个点之间的距离均为1。现在有一只蚂蚁，从第一个点出发，每次随机选择一个方向（向左或向右）并以恒定速度向前爬行，爬行距离也是1。求蚂蚁在第一次经过第10个点之前经过第1个点的概率。

Answer: `0`

## 1166 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that \( \sqrt[n]{5^n + 6^n + 7^n} \) is an integer.

Answer: `3`

## 1167 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) can be expressed as the product of two non-constant polynomials with integer coefficients.

Answer: `3`

## 1168 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + ax^{n-1} + bx^{n-2} + \cdots + k \) with integer coefficients \( a, b, \ldots, k \) has the property that for every positive integer \( m \), the sum of the digits of \( P(m) \) is divisible by 9.

Answer: `2`

## 1169 | score=0.333 | number_theory

Consider a polynomial \(P(x) = x^{2023} + a_{2022}x^{2022} + \cdots + a_1x + a_0\) with integer coefficients, and let \(n\) be the number of distinct prime factors of \(P(2023)\). Find the maximum possible value of \(n\).

Given that \(P(1) = 2024\) and \(P(2) = 2048\), determine the maximum possible value of \(n\).

Answer: `2`

## 1170 | score=0.333 | geometry

In the complex plane, let \( S \) be the set of complex numbers \( z \) such that \( |z - 1| \leq 2 \) and \( |z + 1| \leq 2 \). Determine the area of the region enclosed by \( S \), and find the maximum value of \( |z| \) for all \( z \in S \). Express your answer as a fraction in lowest terms for the area and as a simplified radical for the maximum value of \( |z| \).

Answer: `2`

## 1171 | score=0.556 | number_theory

Let \( P(x) \) be a monic polynomial with integer coefficients such that \( P(1) = 0 \) and for all integers \( n \geq 2 \), \( P(n) \) is divisible by \( n^2 \). Determine the number of possible values of \( P(2) \).

Answer: `\infty`

## 1172 | score=0.333 | number_theory

In the magical realm of Numeralia, there exists a peculiar sequence of numbers known as the "Mystic Prime Sequence" denoted as \((a_n)\). This sequence starts with \(a_1 = 2\) and is defined recursively by \(a_{n+1} = a_n^2 - a_n + 1\) for all \(n \geq 1\). If \(a_7\) represents the product of the first \(k\) primes (including 1), find the value of \(k\).

Answer: `5`

## 1173 | score=0.667 | geometry

Find the smallest positive integer \( n \) such that the sum of the squares of the first \( n \) positive integers is a perfect cube.

Answer: `1`

## 1174 | score=0.333 | geometry

Consider a regular octagon \(ABCDEFGH\) inscribed in a circle of radius \(r\). Let \(P\) be the intersection of diagonals \(AC\) and \(BD\). If the area of the octagon is given by \(A = 2r^2(\sqrt{2} + 1)\), find the length of segment \(AP\) in terms of \(r\).

Answer: `r`

## 1175 | score=0.778 | geometry

Let $P(x)$ be a polynomial of degree $4$ with integer coefficients such that $P(1) = 17$, $P(2) = 34$, $P(3) = 51$, and $P(n)$ is a perfect square for some positive integer $n$. Determine the number of possible values of $P(0)$.

Answer: `1`

## 1176 | score=0.667 | number_theory

Let \( f: \mathbb{R} \to \mathbb{R} \) be a continuous function such that for all \( x, y \in \mathbb{R} \), the function \( g(x) = f(x + y) - f(x) - f(y) \) satisfies \( g(x) \geq 0 \) and \( g(x) = 0 \) if and only if \( x = 0 \). Suppose that \( f \) is not identically zero and that \( f(1) = 2 \). Prove that there exists a unique positive integer \( n \) such that \( f(n) = 2^n \).

Answer: `1`

## 1177 | score=0.333 | geometry

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(1) = 5 \), \( P(2) = 14 \), and \( P(3) = 33 \). Determine the smallest positive integer \( n \) for which \( P(n) \) is a perfect square.

Answer: `31`

## 1178 | score=0.667 | geometry

Let \( p \) be a prime number greater than 3, and let \( n \) be a positive integer. Prove that the sum of the squares of the first \( n \) terms of the arithmetic sequence \( 1, p, 2p, 3p, \ldots \) is divisible by \( p \).

More formally, prove that:
\[ 1^2 + p^2 + (2p)^2 + (3p)^2 + \cdots + (np)^2 \]
is divisible by \( p \).

Answer: `p`

## 1179 | score=0.667 | number_theory

There exists a sequence of positive integers \(a_1, a_2, \ldots, a_{10}\) such that for every \(i \neq j\), the greatest common divisor (gcd) of \(a_i\) and \(a_j\) is 1. If the sum of these ten numbers is 2023, what is the minimum possible value of \(a_1\)?

Answer: `2`

## 1180 | score=0.778 | other

In the realm of advanced combinatorics, consider a set of $n$ distinct points in the plane, where $n \geq 4$. A *compatible quadrilateral* is defined as a set of four points from this set that form a quadrilateral with no two sides parallel. Let $f(n)$ denote the number of compatible quadrilaterals that can be formed from this set of $n$ points. Determine the value of $f(10)$.

Answer: `210`

## 1181 | score=0.556 | other

在二维平面直角坐标系中，设有一个半径为 \( r \) 的圆 \( C \)，圆心位于原点 \( O(0, 0) \)。定义一条射线 \( L \) 从圆外一点 \( P(a, b) \) 出发，与圆 \( C \) 相交于点 \( A \)，使得 \( A \) 是 \( L \) 上离 \( P \) 最近的点。求当点 \( P \) 沿直线 \( y = mx \) 移动时，\( PA \) 长度的最小值。

Answer: `r`

## 1182 | score=0.444 | geometry

Let \( S \) be a set of \( n \) points in the plane, no three of which are collinear, such that for any point \( P \) in \( S \), there exists at least one point \( Q \) in \( S \) with the property that the line segment \( PQ \) contains exactly three points of \( S \). What is the maximum possible value of \( n \)?

Assume \( n \) is such that it is achievable and provide a proof for your answer.

Answer: `5`

## 1183 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + 2x^{n-1} + 3x^{n-2} + \cdots + (n+1)x + (n+2) \) has an integer root.

Answer: `0`

## 1184 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial
\[ P(x) = x^n + x^{n-1} + \cdots + x + 1 \]
can be expressed as the product of two non-constant polynomials with integer coefficients.

Answer: `3`

## 1185 | score=0.444 | number_theory

In a small town, the mayor has decided to plant trees along the streets in a pattern that follows a unique mathematical rule. The town has 10 straight streets running east to west and 10 streets running north to south, forming a grid. The mayor plans to plant trees such that no two trees are exactly 10 streets apart horizontally or vertically. Moreover, the number of trees planted on each street must be a prime number. Given these constraints, determine the minimum total number of trees that can be planted across the town.

Answer: `40`

## 1186 | score=0.556 | number_theory

Find all positive integers \( n \) such that there exists a polynomial \( P(x) \) with integer coefficients and degree \( n \) satisfying \( P(1) = 1 \) and \( P(k) \equiv 1 \pmod{k^2} \) for every prime number \( k \leq n \).

Answer: `1`

## 1187 | score=0.667 | geometry

In the triangular array shown below, each element in the array is the sum of the two elements directly above it in the previous row. The array has 20 rows and is filled with non-negative integers. If the first row consists of a single integer \(a\), and the last row has the sum of all elements being a perfect square, find the smallest possible value of \(a\) such that the total sum of the first \(n\) rows (where \(n\) is the smallest integer such that the sum is a perfect square) is less than 10,000.

Answer: `1`

## 1188 | score=0.444 | geometry

In the plane, point \( P \) is equidistant from three distinct points \( A, B, \) and \( C \). Let \( D \) be the point such that \( \triangle ABC \) and \( \triangle PCD \) are congruent. If \( AB = AC = 10 \) units and \( BC = 12 \) units, determine the length of \( PD \).

Answer: `10`

## 1189 | score=0.444 | geometry

A regular hexagon is inscribed in a circle with radius \( R \). Points \( A \), \( B \), and \( C \) are on the circle such that they form an equilateral triangle within the hexagon. Given that the side length of the hexagon is \( s \), express the length of the segment connecting the center of the circle to the centroid of triangle \( ABC \) in terms of \( R \) and \( s \).

Answer: `0`

## 1190 | score=0.556 | combinatorics

In a game of "Guess the Number," two players, Alex and Bella, each have a strategy for guessing the number chosen by a third player, Charlie. Charlie chooses a number between 1 and 100, inclusive. Alex's strategy is to guess a number that is the average of all the previous guesses made by both Alex and Bella. Bella's strategy is to always guess a number that is exactly half of the number previously guessed by Alex, rounding down if necessary. If the game starts with Alex guessing 50 and Bella guessing 25, what is the smallest number that Charlie can choose so that neither Alex nor Bella guesses it correctly after making 10 guesses?

Answer: `1`

## 1191 | score=0.444 | geometry

In the coordinate plane, a sequence of points \((P_n)\) is defined as follows: \(P_1 = (1, 1)\), and for \(n \geq 2\), \(P_n\) is the reflection of \(P_{n-1}\) over the line \(y = x\). Let \(Q_n\) be the midpoint of the segment connecting \(P_n\) and \(P_{n+1}\). If \(S\) is the set of all points \(Q_n\) for \(n \geq 1\), determine the smallest positive integer \(k\) such that the area enclosed by the convex hull of \(S\) and the line segments connecting consecutive points in \(S\) is greater than \(10^6\) square units.

Answer: `1`

## 1192 | score=0.556 | number_theory

Find all positive integers \( n \) for which the equation \( x^4 + y^4 + z^4 + 4 = 4xyz \) has integer solutions.

Answer: `0`

## 1193 | score=0.778 | geometry

In the coordinate plane, consider a set of points \(P\) such that each point has integer coordinates and lies on the line \(y = 3x + 5\). A line segment connects two points in \(P\) if and only if the sum of their \(x\)-coordinates is a prime number. Find the maximum number of line segments that can be formed connecting any two points in \(P\), assuming there are infinitely many points in \(P\).

Answer: `\infty`

## 1194 | score=0.444 | number_theory

Let $f: \mathbb{R} \to \mathbb{R}$ be a continuous function such that for every real number $x$, there exists a unique integer $n$ satisfying $x \in [n, n+1)$ and $f(x) = n^2 + f(n)$. Find the number of possible values for $f(0)$.

Answer: `1`

## 1195 | score=0.667 | number_theory

Let \( p \) be a prime number greater than 2. Define \( S_p \) as the set of all positive integers \( n \) such that \( n \) can be expressed as the sum of exactly two distinct powers of \( p \). Prove that there exists a positive integer \( k \) such that \( S_p \subseteq \{ p^k, p^k + 1, p^k + 2, \ldots, p^k + p - 1 \} \).

Answer: `k`

## 1196 | score=0.333 | geometry

A rectangle $ABCD$ has sides $AB = 12$ and $BC = 16$. Point $E$ lies on $AB$ such that $AE = 4$, and point $F$ lies on $CD$ such that $CF = 8$. Segments $AF$ and $CE$ intersect at $G$. What is the area of quadrilateral $AEGF$?

Answer: `32`

## 1197 | score=0.333 | geometry

Let \( f(n) \) be the number of ways to tile a \( 2 \times n \) rectangle with \( 1 \times 2 \) dominoes and \( 2 \times 2 \) squares, such that no two dominoes are adjacent. Find the remainder when \( f(10) \) is divided by 1000.

Answer: `089`

## 1198 | score=0.333 | number_theory

Find all triples of integers \((a, b, c)\) such that \(a^2 + b^2 + c^2 = abc + 2\) and \(a \leq b \leq c\).

Answer: `(0, 1, 1), (1, 1, 1)`

## 1199 | score=0.444 | number_theory

Find the smallest positive integer $n$ such that the remainder when $n^3 - n$ is divided by 7 is 5.

Answer: `5`

## 1200 | score=0.333 | number_theory

A fair six-sided die is rolled repeatedly until a six appears. Let \( X \) be the number of rolls needed to get the first six. Find the probability that \( X \) is a prime number.

Answer: `\frac{2605}{7776}`

## 1201 | score=0.333 | number_theory

Let \( f(x) \) be a polynomial with integer coefficients such that \( f(1) = 17 \) and \( f(4) = 41 \). Suppose that \( f(x) \) has a root at \( x = 3 \) and that the sum of all its integer roots is 15. Find the largest possible value of the absolute value of any integer root of \( f(x) \).

Answer: `12`

## 1202 | score=0.333 | number_theory

A sequence \( S \) is defined as follows: \( S_1 = 1 \), and for \( n \geq 2 \), \( S_n \) is the smallest positive integer such that \( S_n > S_{n-1} \) and the set \( \{S_1, S_2, \ldots, S_n\} \) contains no three elements that form an arithmetic progression. Find the value of \( S_{10} \).

Answer: `11`

## 1203 | score=0.333 | number_theory

Find all positive integers $n$ such that the polynomial $P(x) = x^n + x^{n-1} + \cdots + x + 1$ can be expressed as the product of two non-constant polynomials with integer coefficients. Prove that your solution is complete.

Answer: `3`

## 1204 | score=0.667 | algebra

Let \(a, b, c\) be positive real numbers such that \(a + b + c = 1\) and \(a \geq b \geq c\). Prove that
\[
\frac{a^2}{b} + \frac{b^2}{c} + \frac{c^2}{a} \geq \frac{2}{3}.
\]

Answer: `\frac{2}{3}`

## 1205 | score=0.667 | algebra

Find all functions \( f: \mathbb{R} \to \mathbb{R} \) such that for all real numbers \( x \) and \( y \),
\[ f(x^3 - y^3) = (x - y)(f(x^2) + xf(y) + yf(y)). \]

Answer: `f(x) = cx`

## 1206 | score=0.778 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a function that satisfies the functional equation
\[ f(x + f(y)) = f(x) + f(y) + 2xy \]
for all \( x, y \in \mathbb{R} \). Suppose further that \( f(0) = 0 \) and \( f \) is differentiable at \( x = 0 \). Determine all possible values of \( f(1) \).

Answer: `1`

## 1207 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that the equation \( x^3 - nx^2 + (n-1)x - n = 0 \) has at least one positive integer solution. Find the sum of all elements in \( S \) that are less than 100.

Answer: `2`

## 1208 | score=0.444 | geometry

A set of 10 distinct points is placed on a plane such that no three points are collinear. Each pair of points is connected by a straight line, and each line is colored either red or blue. Determine the minimum number of monochromatic triangles (triangles with all sides the same color) that must appear in this configuration.

Answer: `1`

## 1209 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers. Define a function \( f: S \to S \) such that for every \( n \in S \), \( f(n) \) is the smallest positive integer greater than \( n \) that is relatively prime to \( n \). Find the value of \( f(2024) \).

Answer: `2025`

## 1210 | score=0.333 | number_theory

Let \( n \) be a positive integer such that \( n \) is the smallest integer for which there exists a sequence of \( n \) positive integers \( a_1, a_2, \ldots, a_n \) satisfying the following conditions:
1. \( a_1 = 1 \)
2. For all \( i = 2, 3, \ldots, n \), \( a_i \) is the smallest positive integer not appearing among \( a_1, a_2, \ldots, a_{i-1} \) and not equal to \( a_j^2 \) for any \( j < i \).
Find the value of \( n \) for which the sum \( a_1 + a_2 + \cdots + a_n \) is divisible by 10.

Answer: `15`

## 1211 | score=0.667 | geometry

A sequence of numbers $a_n$ is defined for $n \geq 1$ by the recurrence relation $a_{n+1} = a_n^2 - 2a_n + 2$, with $a_1 = 3$. Prove that for all positive integers $k$, $a_k$ can be expressed as a sum of squares in exactly two different ways.

Answer: `2`

## 1212 | score=0.667 | number_theory

Let $S$ be the set of all positive integers $n$ such that $\frac{n^2}{n+10}$ is an integer. Determine the smallest prime number that does not belong to $S$.

Answer: `2`

## 1213 | score=0.444 | geometry

Find all integers \( n \geq 1 \) such that \( n^5 + 2n^4 + 4n^3 + n + 3 \) is a perfect square.

Answer: `0`

## 1214 | score=0.444 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a function such that \( f(x + f(y)) = f(x) + y \) for all real numbers \( x \) and \( y \). Suppose further that \( f(2) = 5 \). Find the value of \( f(1) \).

Answer: `4`

## 1215 | score=0.333 | number_theory

A positive integer \( n \) is chosen such that the product of its divisors equals \( 2^{2023} \cdot 3^{1515} \). What is the minimum possible value of \( n \)?

Answer: `2^{2023} \cdot 3^{1515}`

## 1216 | score=0.556 | algebra

In the complex plane, let $P(z)$ be the polynomial $P(z) = z^8 + (4\sqrt{3} + 6)z^4 - (4\sqrt{3} + 7)$. Suppose that $z_1, z_2, \ldots, z_8$ are the roots of $P(z)$. Find the minimum possible value of $|z_a - z_b|$, where $1 \leq a < b \leq 8$.

Answer: `2`

## 1217 | score=0.778 | number_theory

Find all integers \( n \) such that the polynomial \( P(x) = x^4 - 10x^3 + nx^2 - 20x + 16 \) has four real roots, and prove that for each \( n \), the roots can be expressed as \( a, a+b, a+2b, \) and \( a+3b \) where \( a \) and \( b \) are positive integers.

Answer: `35`

## 1218 | score=0.333 | number_theory

Let \( p \) be a prime number. Determine the number of ordered triples \( (a, b, c) \) of integers such that \( 1 \leq a, b, c \leq p-1 \) and \( a^2 + b^2 + c^2 \equiv 0 \pmod{p} \).

Answer: `(p-1)^2`

## 1219 | score=0.444 | other

在三维空间中，给定一个单位球，其内部包含一个正八面体，该正八面体的每个顶点都位于球面上。假设从该球内部随机选择两点，计算这两点之间的距离恰好等于正八面体的边长的概率。

Answer: `0`

## 1220 | score=0.778 | geometry

A finite set \( S \) of points in the plane has the following property: there are exactly 2019 points in \( S \) that lie on no line containing any other points of \( S \).  The remaining points of \( S \) lie on 1009 distinct lines, each of which contains exactly three points of \( S \).  Find the number of points in \( S \).

Answer: `5046`

## 1221 | score=0.778 | number_theory

Find all prime numbers \( p \) such that both \( p^2 + 2 \) and \( p^2 + 4 \) are also prime. Prove your answer is complete by considering the divisibility properties of these expressions.

Answer: `3`

## 1222 | score=0.444 | other

A point $P$ lies inside a regular hexagon $ABCDEF$. The distances from $P$ to three consecutive vertices $A, B, C$ are 10, 15, and 20 respectively. Find the side length of the hexagon.

Answer: `25`

## 1223 | score=0.444 | geometry

Given a circle with radius \( r \) and a square inscribed within it, find the maximum possible area of a rectangle that can be inscribed inside the square such that all its vertices lie on the sides of the square. Express your answer in terms of \( r \).

Answer: `r^2`

## 1224 | score=0.556 | geometry

Let $ABCDEF$ be a regular hexagon inscribed in a circle with radius $r$. Suppose that point $G$ is chosen randomly on the circumference of the circle such that it is not coincident with any vertex of the hexagon. If $P$ is the probability that the triangle $AGB$ has a greater area than each of the triangles $AGC$, $AGD$, $AGE$, and $AGF$, find $P$ in terms of $r$.

Answer: `\frac{1}{6}`

## 1225 | score=0.444 | geometry

Let $S$ be the set of all positive integers $n$ such that $\frac{1}{n} = 0.\overline{a_1a_2\ldots a_k}$, where $a_1, a_2, \ldots, a_k$ are digits, and $k$ is the smallest integer for which the decimal repeats. Determine the smallest $n > 1$ for which $n$ is in $S$ and $n$ can be expressed as the product of exactly three distinct primes. Find $n$.

Answer: `30`

## 1226 | score=0.667 | algebra

Find all real numbers \( x \) such that \[ \sqrt[3]{x^2} + 2\sqrt[3]{x} = \sqrt[3]{16x - 8}. \]

Answer: `8`

## 1227 | score=0.444 | algebra

Let \( P(x) \) be a polynomial of degree 6 such that \( P(x) = P(1-x) \) for all real \( x \). Given that \( P(0) = 0 \) and \( P(2) = 16 \), find the value of \( P(3) \).

Answer: `16`

## 1228 | score=0.444 | number_theory

Find all positive integers \( n \) for which there exists a positive integer \( k \) such that \( \sum_{i=1}^{n} \frac{1}{i!} = \frac{k}{n!} \).

Answer: `1`

## 1229 | score=0.444 | number_theory

Let \( f(x) \) be a polynomial with integer coefficients satisfying \( f(0) = 1 \) and \( f(1) = 2 \). Suppose there exists a positive integer \( k \) such that \( f(k) = f(k + 3) \). Find the smallest possible value of \( k \).

Answer: `3`

## 1230 | score=0.778 | number_theory

Let \( f(x) \) be a function defined for all positive integers \( x \) such that \( f(1) = 2 \) and \( f(x + y) = f(x) f(y) - xy \) for all positive integers \( x \) and \( y \). Find the value of \( f(2024) \).

Answer: `2025`

## 1231 | score=0.333 | number_theory

Let \( S \) be the set of all integers \( n \) such that \( 1 \leq n \leq 1000 \) and \( n^2 \) is divisible by both 24 and 35. Find the sum of all elements in \( S \).

Answer: `1260`

## 1232 | score=0.556 | geometry

A convex hexagon has vertices labeled $A, B, C, D, E,$ and $F$ in that order. The midpoints of the sides are labeled $M, N, O, P, Q,$ and $R$ in the same order. The lines connecting opposite midpoints, $MO$, $NP$, and $QR$, intersect at a single point $X$. If the area of the hexagon is 216 square units, find the area of triangle $XAB$.

Answer: `36`

## 1233 | score=0.556 | number_theory

A sequence of positive integers is defined by \( a_1 = 1 \), \( a_2 = 2 \), and for \( n \geq 3 \), \( a_n = a_{n-1} + a_{n-2} + d_n \), where \( d_n \) is the smallest positive integer not appearing earlier in the sequence that is also not a multiple of any previous \( a_i \). Find \( a_{10} \).

Answer: `342`

## 1234 | score=0.333 | number_theory

Let \( p \) be a prime number. Prove that there exists an integer \( x \) such that the sum \( x + x^2 + x^3 + \cdots + x^p \) is divisible by \( p^2 \).

Answer: `p`

## 1235 | score=0.333 | number_theory

Let \( f(x) = x^3 - 3x + 1 \). Define the sequence \( \{a_n\} \) by \( a_1 = 2 \) and \( a_{n+1} = f(a_n) \) for all \( n \geq 1 \). Find the smallest positive integer \( k \) such that \( a_k \) is an integer and \( a_k \) divides \( f(2024) \).

Answer: `3`

## 1236 | score=0.556 | number_theory

Find all integers \( n \) such that the polynomial \( P(x) = x^4 - nx^3 + (n-1)x^2 - x + 1 \) has at least one integer root.

Answer: `-1`

## 1237 | score=0.778 | number_theory

Find all positive integers \( n \) for which there exists a function \( f \colon \{1, 2, \ldots, n\} \to \{1, 2, \ldots, n\} \) such that \( f(f(k)) = k \) for all \( k \in \{1, 2, \ldots, n\} \), but for all \( k \neq f(k) \), \( f(k) \neq k \). Furthermore, determine the number of such functions \( f \) for \( n = 4 \).

Answer: `3`

## 1238 | score=0.556 | other

在一个3x3的网格中放置9个点，每个点可以选择红色或蓝色。要求任意两行中颜色排列都不完全相同。问有多少种不同的颜色排列方式？

Answer: `336`

## 1239 | score=0.667 | number_theory

Find all positive integers \( n \) such that the sum of the first \( n \) terms of the sequence defined by \( a_k = k^3 - 3k^2 + 3k - 1 \) is equal to the sum of the first \( n \) terms of the sequence defined by \( b_k = k^4 - 4k^3 + 6k^2 - 4k + 1 \).

Answer: `1`

## 1240 | score=0.333 | number_theory

A sequence \( a_1, a_2, a_3, \ldots \) is defined by \( a_1 = 1 \) and for all \( n \geq 1 \), \( a_{n+1} \) is the smallest positive integer that does not share a prime factor with \( a_n \) and has not appeared in the sequence before. Find \( a_{100} \).

Answer: `100`

## 1241 | score=0.778 | number_theory

Let \( f: \mathbb{R} \to \mathbb{R} \) be a function defined by \( f(x) = \lfloor x^2 \rfloor \), where \( \lfloor \cdot \rfloor \) denotes the floor function. For how many integers \( n \) between 1 and 1000 inclusive is it possible to find an integer \( k \) such that \( f(k) = n \)?

Answer: `31`

## 1242 | score=0.333 | geometry

In a triangular lattice of points, each point is connected to its six nearest neighbors by straight lines. A path is defined as a sequence of connected line segments, each segment connecting two adjacent points. Starting from any point, how many distinct paths of exactly 6 segments can be drawn such that no segment is retraced? Find the remainder when this number is divided by 1000.

Answer: `656`

## 1243 | score=0.778 | geometry

There are 2021 points distributed on the plane such that among any three points, at least one segment connecting two of the three points does not intersect any other segment, where the intersection is understood in the usual geometric sense, including endpoints. Show that there exists a line on the plane that passes through at least 2022 of these points.

Answer: `2022`

## 1244 | score=0.333 | combinatorics

Consider a sequence of numbers $a_1, a_2, a_3, \ldots, a_n$ where each $a_i$ is either 0 or 1. Define a function $f(S)$ for any subset $S$ of $\{1, 2, 3, \ldots, n\}$ as the sum of the elements $a_i$ for all $i$ in $S$. Let $N$ be the total number of subsets $S$ of $\{1, 2, 3, \ldots, n\}$ for which $f(S)$ is even. Prove that the sum of the binomial coefficients $\binom{n}{k}$ for $k$ ranging from 0 to $n$, with the even-indexed coefficients doubled, is equal to $2^{n-1} + 2^{n-1}$, and determine how this relates to $N$.

Answer: `2^{n-1}`

## 1245 | score=0.667 | number_theory

Find the smallest positive integer \( n \) such that the sum of the first \( n \) positive integers, each taken modulo 10, equals 2023. That is, find \( n \) where \(\left(1 + 2 + \cdots + n\right) \mod 10 = 2023 \mod 10\).

Answer: `2`

## 1246 | score=0.444 | geometry

Let $p(x) = x^3 + ax^2 + bx + c$ be a cubic polynomial with integer coefficients such that $p(0)$ and $p(1)$ are both prime numbers. If $p(2)$ and $p(3)$ are both squares of prime numbers, find the number of possible values for $p(4)$.

Answer: `2`

## 1247 | score=0.556 | geometry

In a finite, non-empty set of integers, each element \( a \) satisfies \( a^2 + a + 1 \) being a perfect square. Let \( S \) be such a set with the property that the sum of any two distinct elements is not a perfect square. Prove that the maximum possible size of \( S \) is 3.

Answer: `3`

## 1248 | score=0.333 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that \( n \) can be expressed as the sum of two or more consecutive positive integers. For example, \( 9 = 4 + 5 \), so \( 9 \in S \). Find the smallest positive integer \( m \) such that the equation \( x^2 + y^2 + z^2 = m \) has no solutions in distinct positive integers \( x, y, z \) where \( x, y, z \in S \).

Answer: `9`

## 1249 | score=0.556 | number_theory

Let \( P(x) = x^3 + ax^2 + bx + c \) be a polynomial with real coefficients such that the roots of \( P(x) \) are distinct positive integers. Additionally, it is given that \( P(1) = 10 \) and \( P(2) = 20 \). Find the product of all possible values of \( a + b + c \).

Answer: `0`

## 1250 | score=0.556 | number_theory

Find the smallest positive integer \( n \) such that the equation \( x^2 + y^2 = n \) has exactly four distinct integer solutions \((x, y)\) where \( x \) and \( y \) are both odd.

Answer: `10`

## 1251 | score=0.556 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a function such that for all real numbers \( x \) and \( y \), \( f(x + f(y)) = f(x) + y \). Given that \( f \) is continuous and \( f(1) = 2 \), find the value of \( f(4) \).

Additionally, let \( g: \mathbb{R} \to \mathbb{R} \) be defined by \( g(x) = f(x + 1) - f(x) \). Determine the value of \( g(2) \).

Answer: `1`

## 1252 | score=0.556 | geometry

Let $ABC$ be a triangle with $AB = 13$, $BC = 14$, and $CA = 15$. The incircle of $ABC$ touches $BC$, $CA$, and $AB$ at $D$, $E$, and $F$, respectively. The lines $AD$, $BE$, and $CF$ intersect at a single point, $P$. Find the radius of the incircle of $ABC$ and the length of segment $PD$.

Answer: `4`

## 1253 | score=0.667 | number_theory

Let $f(x)$ be a polynomial with integer coefficients such that $f(1) = 17$, $f(2) = 34$, and $f(3) = 51$. If $f(n)$ is divisible by $17$ for all integers $n \geq 4$, what is the smallest possible degree of $f(x)$?

Answer: `1`

## 1254 | score=0.333 | geometry

In a triangular park, three friends, Alice, Bob, and Charlie, decide to meet at a point that is equidistant from all three vertices of the triangular boundary of the park. The lengths of the sides of the triangle are 10 meters, 15 meters, and 17 meters. Alice stands at the vertex opposite the 10-meter side, Bob at the vertex opposite the 15-meter side, and Charlie at the vertex opposite the 17-meter side. Determine the distance from each friend's location to the meeting point, expressed in simplest radical form.

Answer: `\frac{425 \sqrt{154}}{616}`

## 1255 | score=0.444 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) can be expressed as the product of two non-constant polynomials with integer coefficients.

Answer: `3`

## 1256 | score=0.333 | combinatorics

In a game involving \( n \) players, each player rolls a standard six-sided die. If a player rolls a 6, they score double the number of points they would score for their roll. Otherwise, the number of points scored equals the roll. Players continue to roll the die until they either achieve a score greater than \( n \) or decide to stop. What is the expected number of points a player will score if they always choose to continue rolling until they achieve a score greater than \( n \)?

Answer: `n`

## 1257 | score=0.556 | geometry

Let $ABC$ be a triangle with circumcenter $O$ and orthocenter $H$. Let $D$, $E$, and $F$ be the feet of the altitudes from $A$, $B$, and $C$, respectively. Suppose that $AD = BD = CF$. If $R$ is the circumradius of triangle $ABC$ and $r$ is the inradius, prove that
\[
AH^2 = 2R^2 - 4r^2.
\]

Answer: `2R^2 - 4r^2`

## 1258 | score=0.444 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^3 - nx^2 + (n+3)x - n \) has three distinct integer roots.

Answer: `6`

## 1259 | score=0.333 | number_theory

Find all positive integers \( n \) such that there exist positive integers \( a_1, a_2, \ldots, a_n \) satisfying:
\[ a_1 + a_2 + \cdots + a_n = 100 \]
and
\[ a_1^2 + a_2^2 + \cdots + a_n^2 = 2023. \]

Answer: `5`

## 1260 | score=0.333 | number_theory

Let \( f: \mathbb{N} \to \mathbb{N} \) be a function such that for all positive integers \( n \) and \( m \),
\[ f(nm) = f(n)f(m) \]
if \( n \) and \( m \) are coprime. Suppose further that \( f(n) > n \) for all \( n \geq 2 \), and that \( f(p) = p + 1 \) for all primes \( p \). Determine the number of positive integers \( n \leq 2023 \) such that \( f(n) \) is prime.

Answer: `306`

## 1261 | score=0.778 | number_theory

Find the smallest positive integer $n$ such that there exist positive integers $a_1, a_2, \ldots, a_n$ satisfying $a_1^2 + a_2^2 + \cdots + a_n^2 = a_1 a_2 \cdots a_n + n^2$.

Answer: `2`

## 1262 | score=0.333 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that \( n \) can be expressed as the sum of two or more consecutive positive integers. For example, \( 9 = 4 + 5 \) and \( 15 = 1 + 2 + 3 + 4 + 5 \). Determine the smallest positive integer \( k \) for which there does not exist a positive integer \( n \) in the set \( S \) such that \( n \equiv k \pmod{12} \).

Answer: `4`

## 1263 | score=0.500 | geometry

In a plane, \(n\) points are placed such that no three points are collinear. A set of line segments are drawn between these points to form a complete graph. Each line segment is colored either red or blue such that no triangle in this graph is monochromatic (all three sides are the same color). Determine the maximum number of line segments that can be colored red, in terms of \(n\).

Answer: `\left\lfloor \frac{n^2}{4} \right\rfloor`

## 1264 | score=0.444 | number_theory

Let \( S \) be the set of all non-empty finite sequences of positive integers. For each sequence \( \sigma = (a_1, a_2, \ldots, a_n) \) in \( S \), define the function \( f(\sigma) \) as the sum of all possible products of pairs of distinct elements in \( \sigma \). For example, \( f((1,2)) = 1 \cdot 2 = 2 \), and \( f((1,2,3)) = 1 \cdot 2 + 1 \cdot 3 + 2 \cdot 3 = 11 \). Find the largest integer \( k \) such that for any sequence \( \sigma \in S \) with \( n = 5 \), there exists a partition of \( \sigma \) into two non-empty subsequences \( \sigma_1 \) and \( \sigma_2 \) such that \( f(\sigma_1) = k \cdot f(\sigma_2) \).

Answer: `4`

## 1265 | score=0.333 | other

在一个无限大的方形网格上，每个小方格都有一个高度。我们希望用一些单位高的方块（每个方块占据一个小方格）填满整行，使得每一行的高都严格递增。给定初始行中已经有了一些方块，请问有多少种不同的方式可以完成填满这一行？

初始情况如下：
第一行有五列，已经有三个方块，分别是位于第2、3、4列的方格。问有多少种方法可以填满第2、3、4列之后的列，使得每一行的高度严格递增。

Answer: `1`

## 1266 | score=0.333 | geometry

Find all prime numbers \( p \) such that \( p^2 + 2p + 1 \) is also a perfect square.

Answer: `2`

## 1267 | score=0.333 | other

在一个无限长的条形金属板上，以等间距排列着一系列可调节的光源。每个光源的强度可独立调整为一个非负整数，并且总强度不超过1000单位。当一个光源开启时，它会照亮距离自己不超过10单位的区域，且这些区域内的所有其他光源的强度将减少1单位。假设开始时所有光源都处于关闭状态，请求出存在一种配置方式使得整个金属板恰好被一个特定形状的区域（由x轴上的两点A(0,0)和B(100,0)，以及线段AB上两个点C(50,10)和D(50,-10)围成的四边形区域）完整照亮，同时使得剩余部分没有光源照亮或被过度照亮。求满足条件的所有可能的最大光源强度总和的最大值。

Answer: `1000`

## 1268 | score=0.444 | number_theory

In the mystical land of Numeria, there exists a mystical garden that blooms with special flowers. Each flower has a unique number of petals ranging from 1 to 10. There are exactly 100 flowers in the garden. It's known that if you select any four flowers from the garden, the total number of petals on these flowers is always divisible by 5. What is the maximum possible number of flowers in the garden that have 7 petals?

Answer: `20`

## 1269 | score=0.444 | combinatorics

In a small town, there are 100 houses numbered from 1 to 100. Each house has a unique color and a unique type of roof. The colors of the houses follow a pattern such that the color of any house is the sum of the colors of its two neighboring houses (considering that houses 1 and 100 wrap around). If the color of house 1 is 1 and the color of house 100 is 100, what is the color of house 50?

Answer: `50`

## 1270 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n - 1 \) can be factored into a product of non-constant polynomials with integer coefficients in at least three different ways, where each factorization is distinct up to permutation and scaling by units.

Answer: `12`

## 1271 | score=0.375 | geometry

Let \( ABC \) be an isosceles triangle with \( AB = AC \) and \( BC = 20 \). A circle with center \( O \) is inscribed in the triangle such that it touches all three sides. The circle also intersects \( BC \) at points \( D \) and \( E \) with \( D \) between \( B \) and \( E \). If the radius of the circle is 6, find the length of \( BD \).

Answer: `4`

## 1272 | score=0.778 | geometry

Let \(ABC\) be an isosceles triangle with \(AB = AC\) and incenter \(I\). A circle passing through \(I\) and tangent to \(AB\) at \(D\) and \(AC\) at \(E\) is drawn. Let \(F\) and \(G\) be the points where this circle intersects \(BC\) again, distinct from \(I\). If the area of triangle \(ABC\) is \(90\) and the length of \(BC\) is \(12\), find the area of quadrilateral \(IDEG\).

Answer: `45`

## 1273 | score=0.556 | algebra

Let \( f(x) \) be a continuous function defined on the interval \([0, 1]\) such that \( f(0) = 0 \) and \( f(1) = 1 \). Suppose there exists a constant \( c > 0 \) such that for all \( x \in [0, 1] \), the inequality \( |f(x) - f(x-c)| \leq |x - (x-c)| \) holds. Prove that there exists a point \( a \in [0, 1] \) such that \( f(a) = a \).

Answer: `a`

## 1274 | score=0.333 | number_theory

Let \( P(x) = x^4 - 2023x^3 + ax^2 + bx + c \) be a polynomial with integer coefficients such that \( P(1) = 1011 \), \( P(2) = 2022 \), and \( P(3) = 3033 \). Determine the largest possible value of \( P(0) \).

Answer: `12102`

## 1275 | score=0.667 | geometry

Consider a regular octahedron $ABCDEFG$ with side length $s$. A plane cuts through the octahedron parallel to one of its faces and divides it into two parts. The smaller part is a tetrahedron $ABCD$, and the larger part is a pyramid with a square base. If the volume of the tetrahedron $ABCD$ is $\frac{1}{3}V$, where $V$ is the volume of the original octahedron, find the height $h$ of the tetrahedron $ABCD$ from vertex $A$ to face $BCD$.

Answer: `\frac{4 \sqrt{6}}{9} s`

## 1276 | score=0.333 | number_theory

Find the smallest positive integer \(m\) for which the equation \(x^4 + y^4 + z^4 = m^2\) has solutions in integers \(x, y, z\).

Answer: `1`

## 1277 | score=0.444 | algebra

Let \( f(x) \) be a continuous function on the interval \([0, 1]\) such that \( f(0) = 0 \) and \( f(1) = 1 \). Define \( g(x) = \int_0^x f(t) \, dt \). Prove that there exists a point \( c \in (0, 1) \) such that \( g(c) = c \).

Answer: `c`

## 1278 | score=0.778 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a function satisfying \( f(x+y) = f(x) + f(y) + xy \) for all real numbers \( x \) and \( y \). If \( f(1) = 2 \), find the value of \( f(10) \).

Answer: `65`

## 1279 | score=0.556 | number_theory

Let \( f(x) \) be a polynomial with integer coefficients such that \( f(0) = 1 \) and \( f(1) = 2024 \). If \( f(n) \) is divisible by \( 3 \) for all integers \( n \) satisfying \( 1 \leq n \leq 100 \), determine the number of possible values of \( f(101) \).

Answer: `1`

## 1280 | score=0.778 | number_theory

Find the number of ways to distribute 120 candies among 8 children such that each child receives at least one candy, no child receives more than 15 candies, and the total number of candies each child receives is a prime number.

Answer: `0`

## 1281 | score=0.444 | other

In a small village, there are 100 houses. Each house has at least one resident. If every resident has exactly two friends in the village, and no two houses share exactly the same set of residents, what is the maximum number of residents that can live in the village?

Answer: `200`

## 1282 | score=0.444 | geometry

What is the smallest positive integer \( n \) such that \( n! \) (n factorial) is divisible by \( 10^{10} \), and if \( n \) is written as a sum of two perfect squares in exactly one way, what is \( n \)?

Answer: `50`

## 1283 | score=0.333 | geometry

Let \(ABC\) be a triangle with \(AB = 13\), \(BC = 14\), and \(CA = 15\). Let \(D\) be the foot of the altitude from \(A\) to \(BC\). Let \(E\) and \(F\) be points on \(AB\) and \(AC\) respectively, such that \(DE \parallel AC\) and \(DF \parallel AB\). The lines \(BE\) and \(CF\) intersect at point \(G\). Find the area of quadrilateral \(AEGF\).

Answer: `42`

## 1284 | score=0.333 | geometry

Let $S$ be the set of all integers $n$ such that $1 \leq n \leq 100$ and $n$ is a perfect square or a perfect cube, but not both. What is the sum of all elements in $S$?

Answer: `419`

## 1285 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \ldots + x + 1 \) can be expressed as the product of two non-constant polynomials with integer coefficients.

Answer: `3`

## 1286 | score=0.556 | number_theory

Find all integer solutions $(x, y)$ to the system of equations:

$$x^2 - xy + y^2 = 13x + y$$

$$x^2 + 3xy - y^2 = x - 3y$$

Answer: `(0, 0)`

## 1287 | score=0.333 | number_theory

In a sequence of positive integers, each term after the first is found by adding the previous two terms. The 5th term in this sequence is 15. What is the first term of the sequence if the sum of the first three terms is 13?

Answer: `\frac{9}{2}`

## 1288 | score=0.556 | number_theory

Find the smallest positive integer \( n \) such that the number of ways to partition \( n \) into distinct parts is equal to the number of ways to partition \( n \) into any combination of parts (allowing for repetition).

Answer: `1`

## 1289 | score=0.444 | geometry

Find all positive integers n such that both 2^n + 1 and 3^n + 1 are perfect squares.

Answer: `1`

## 1290 | score=0.556 | number_theory

Find all positive integers \( n \) such that \( n^3 + 3 \) divides \( n^4 + 2 \).

Answer: `1`

## 1291 | score=0.667 | geometry

Consider a function \( f : \mathbb{N} \to \mathbb{N} \) defined by \( f(n) = n^2 - 10n + 21 \). Let \( S \) be the set of all natural numbers \( n \) such that \( f(n) \) is a perfect square. Determine the sum of the elements of \( S \).

Answer: `10`

## 1292 | score=0.667 | number_theory

Find all functions \( f: \mathbb{Z} \to \mathbb{Z} \) such that for any integers \( x \) and \( y \), the following equation holds:
\[ f(x^2 + y^2) = f(x)^2 + f(y)^2 + f(2xy) \]

Answer: `f(x) = 0`

## 1293 | score=0.444 | number_theory

Find all positive integers \( n \) such that there exists a function \( f: \mathbb{Z} \to \mathbb{Z} \) satisfying the property that for any integers \( a, b, \) and \( c \) where \( a + b + c = n \), the equation \( f(a) + f(b) + f(c) = 0 \) holds. Prove your answer.

Answer: `3k`

## 1294 | score=0.778 | number_theory

Find all positive integers \( n \) such that \( n^3 + 2n^2 + 3n + 4 \) divides \( n^{1000} + 1 \).

Answer: `1`

## 1295 | score=0.667 | number_theory

What is the least positive integer $n$ such that when $n$ is divided by each of the integers 1 through 9, the remainder is $n - 1$?

Answer: `2519`

## 1296 | score=0.556 | algebra

Let \( f(x) \) be a polynomial of degree 4 such that \( f(1) = 1 \), \( f(2) = 2 \), \( f(3) = 3 \), and \( f(4) = 4 \). If the coefficient of \( x^2 \) in \( f(x) \) is \( -10 \), find the value of \( f(5) \).

Answer: `5`

## 1297 | score=0.444 | geometry

In a magical realm, there exists a sequence of numbers where each term after the first two is the sum of the squares of the two preceding terms. If the first two terms are \(a\) and \(b\), find the remainder when the 2023rd term of the sequence is divided by 1000, given that \(a\) and \(b\) are both less than 10.

Answer: `0`

## 1298 | score=0.333 | combinatorics

Consider a sequence of real numbers \(a_1, a_2, \ldots, a_n\) such that \(a_1 + a_2 + \cdots + a_n = 0\). Let \(S_k\) denote the sum of the first \(k\) terms of this sequence, i.e., \(S_k = a_1 + a_2 + \cdots + a_k\). Define a function \(f(k)\) as follows:
\[ f(k) = \max_{1 \leq i \leq j \leq k} |S_j - S_i| \]
Find the maximum value of \(f(k)\) over all possible sequences of length \(n\) that satisfy \(a_1 + a_2 + \cdots + a_n = 0\).

Answer: `1`

## 1299 | score=0.444 | calculus

In the complex plane, let $z_1$ and $z_2$ be the solutions to $z^2 - (3 + 4i)z + (5 + 12i) = 0$. Find the minimum value of $|z_1 - z_2|$, where $z_1$ and $z_2$ are distinct complex numbers.

Answer: `5`

## 1300 | score=0.667 | number_theory

There exists a function \( f : \mathbb{N} \to \mathbb{N} \) such that for any positive integers \( a \) and \( b \), the equation \( f(ab) = f(a)f(b) \) holds. Moreover, for all positive integers \( n \), \( f(n) \) is defined as the sum of the divisors of \( n \). Find the number of positive integers \( n \leq 1000 \) for which \( f(n) = n + 1 \).

Answer: `168`

## 1301 | score=0.667 | number_theory

Find all prime numbers \( p \) such that both \( p - 6 \) and \( p + 10 \) are also prime numbers.

Answer: `13, 19`

## 1302 | score=0.778 | geometry

In the complex plane, consider the regular polygon formed by the vertices of the ninth roots of unity, starting from \(1 + 0i\). Let \(P\) be a point on the real axis such that the distances from \(P\) to each of the vertices of the polygon are all integers. Find the smallest possible positive value of \(|P - 1|\).

Answer: `1`

## 1303 | score=0.667 | algebra

Let \( f(x) \) be a continuous function defined on the interval \([0, 1]\) such that \( f(0) = 0 \) and \( f(1) = 1 \). Consider the function \( g(x) = \int_0^x f(t) \, dt \). Suppose that \( h(x) = g(g(x)) \) is a bijection from \([0, 1]\) to \([0, 1]\). Determine all possible forms of \( f(x) \).

Answer: `f(x) = 1`

## 1304 | score=0.333 | geometry

Consider a circle with center $O$ and radius $r$. Let $A$ and $B$ be points on the circle such that the angle $AOB$ is $60^\circ$. Let $C$ be a point on the circle such that the angle $ACB$ is $90^\circ$. Let $D$ be the foot of the perpendicular from $C$ to the line segment $AB$. Let $x$ be the length of the line segment $CD$. Find the value of $x$ in terms of $r$.

Answer: `\frac{r\sqrt{3}}{2}`

## 1305 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) has a root that is also a root of the polynomial \( Q(x) = x^2 + x + 1 \).

Answer: `n \equiv 2 \pmod{3}`

## 1306 | score=0.667 | geometry

Let \( f: \mathbb{Z}^+ \to \mathbb{Z}^+ \) be a function defined by \( f(n) = n^2 + 20n + 12 \). Find the smallest positive integer \( k \) such that \( f(k) \) is a perfect square.

Answer: `13`

## 1307 | score=0.556 | combinatorics

In the complex plane, consider the set of all points \( z \) such that \( |z - 1| + |z + 1| = 4 \). Let \( w \) be a complex number chosen uniformly at random from this set. What is the probability that the real part of \( w \) is greater than 1?

Answer: `\frac{1}{2}`

## 1308 | score=0.556 | geometry

In triangle \(ABC\), the sides \(AB\) and \(AC\) are equal, and \(\angle BAC = 20^\circ\). Point \(D\) lies on \(AC\) such that \(\angle DBC = 10^\circ\), and point \(E\) lies on \(AB\) such that \(\angle ECB = 30^\circ\). Find the measure of \(\angle CDE\).

Answer: `30^\circ`

## 1309 | score=0.667 | number_theory

Let $P(x)$ be a polynomial with integer coefficients such that $P(100) = 100$ and $P(200) = 200$. Find the maximum possible value of $P(150)$.

Answer: `2650`

## 1310 | score=0.556 | number_theory

Find the smallest positive integer \( n \) such that the equation
\[ x^2 - nx + 36 = 0 \]
has integer solutions, and for each solution \( x \), \( x^3 - 3x + 1 = 0 \).

Answer: `12`

## 1311 | score=0.778 | number_theory

Consider a function \(f(x) = x^3 - 3x^2 + 3x - 1\). Let \(S\) be the set of all real numbers \(x\) such that \(0 \leq x \leq 3\) and \(f(x)\) is an integer. Find the number of elements in \(S\).

Answer: `4`

## 1312 | score=0.444 | algebra

Let \( p(x) \) be a polynomial of degree 4 such that \( p(n) = \frac{1}{n} \) for \( n = 1, 2, 3, 4, 5 \). Find \( p(6) \).

Answer: `\frac{1}{3}`

## 1313 | score=0.444 | number_theory

Let $f(x)$ be a polynomial with integer coefficients such that $f(0) = 1$ and $f(1) = 3$. Suppose that for every prime number $p$, there exists an integer $x$ such that $f(x) \equiv 0 \pmod{p}$. What is the smallest possible degree of $f(x)$?

Answer: `2`

## 1314 | score=0.778 | number_theory

Find all pairs of positive integers \((x, y)\) such that
\[ x^y + 1 = y^x. \]

Answer: `(1, 2), (2, 3)`

## 1315 | score=0.556 | number_theory

Find all positive integers \( n \) such that the equation \( x^2 + y^2 + z^2 = nxyz \) has at least one solution in positive integers \( x, y, \) and \( z \). Determine the set of all such \( n \).

Answer: `3`

## 1316 | score=0.444 | geometry

In the complex plane, let $z$ be a complex number such that $|z| = 5$. If $z$ also satisfies the equation $z^2 + \overline{z}^2 = 10$, find the value of $z^3 + \overline{z}^3$.

Answer: `-30\sqrt{15}`

## 1317 | score=0.444 | number_theory

Let \( \mathcal{P} \) be the set of all polynomials \( p(x) \) with integer coefficients such that \( p(1) = p(2) = \cdots = p(20) = 0 \) and \( p(21) = 1 \). Find the smallest positive integer \( n \) such that there exists a polynomial \( p(x) \in \mathcal{P} \) with degree \( n \) satisfying \( p(x) \equiv 1 \mod x^2 \) for all \( x \) in the set \( \{1, 2, \ldots, 20\} \).

Answer: `21`

## 1318 | score=0.667 | other

在森林里有一个环形小道，上面有200个车位。小道上原有的停满车。第一次，每辆车都会向前移动5个车位，空出的车位则回来原来的位置。第二次，每辆车再向前移动5个车位，空出的车位再回来原来的位置。以此类推，问多少次后原来的第一个车位还是第一个车位？

Answer: `40`

## 1319 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that \( 1000 \leq n \leq 9999 \) and \( n \) can be expressed as the sum of two distinct prime numbers. Find the number of elements in \( S \).

Answer: `4500`

## 1320 | score=0.333 | number_theory

Find all integers \( n \geq 2 \) for which there exist distinct positive integers \( a_1, a_2, \ldots, a_n \) such that
\[ a_1 + a_2 + \cdots + a_n = 2023 \]
and
\[ a_1^2 + a_2^2 + \cdots + a_n^2 = 2024^2 - 1. \]

Answer: `2023`

## 1321 | score=0.444 | number_theory

Let \( f: \mathbb{Z}^+ \to \mathbb{Z}^+ \) be a function such that for all positive integers \( a \) and \( b \), the following holds:

\[ f(ab) = f(a) \cdot f(b) \]
and
\[ f(a + b) = f(a) + f(b) \]

Given that \( f(2) = 3 \), find the value of \( f(2023) \).

Answer: `2023`

## 1322 | score=0.333 | geometry

In the triangle \(ABC\), let \(D\) be a point on \(BC\) such that \(AD\) bisects \(\angle BAC\). Suppose \(E\) is a point on \(AD\) such that \(BE\) is perpendicular to \(AD\). Let \(F\) be the intersection of the line through \(D\) parallel to \(BE\) and \(AC\). If the area of triangle \(ABE\) is 20 and the area of triangle \(AFE\) is 12, find the area of triangle \(ABC\).

Answer: `32`

## 1323 | score=0.333 | number_theory

Let \( n \) be a positive integer. A function \( f: \{1, 2, \ldots, n\} \to \{1, 2, \ldots, n\} \) is called *indecomposable* if it cannot be expressed as the composition of two non-trivial functions \( g: \{1, 2, \ldots, n\} \to \{1, 2, \ldots, m\} \) and \( h: \{1, 2, \ldots, m\} \to \{1, 2, \ldots, n\} \) for any integer \( m \) with \( 1 < m < n \). Find the number of indecomposable functions from \( \{1, 2, \ldots, n\} \) to itself.

Answer: `(n-1)!`

## 1324 | score=0.333 | number_theory

Find all integers \( n \) such that the equation
\[ x^4 - 6x^3 + (6 + n)x^2 - (n + 6)x + 4 = 0 \]
has four distinct integer roots. Determine the sum of all possible values of \( n \).

Answer: `0`

## 1325 | score=0.444 | number_theory

Find the number of ordered pairs \((a, b)\) of positive integers such that the equation \(a^3 + b^3 = a^2 + b^2 + ab + 1\) holds.

Answer: `0`

## 1326 | score=0.444 | combinatorics

Let $S$ be the set of all ordered triples $(x,y,z)$ of positive real numbers such that $x + y + z = 1$. Find the maximum value of
$$
\frac{x}{1 + x^2} + \frac{y}{1 + y^2} + \frac{z}{1 + z^2}
$$
over all elements $(x,y,z) \in S$.

Answer: `\frac{9}{10}`

## 1327 | score=0.333 | geometry

A circle of radius 1 is inscribed in a square. A point \( P \) is chosen at random inside the square. What is the probability that the distance from \( P \) to the nearest point on the circle is at least \( \frac{1}{2} \)?

Answer: `\frac{16 - \pi}{16}`

## 1328 | score=0.556 | number_theory

Let \( S \) be a set of integers such that for any two distinct elements \( a \) and \( b \) in \( S \), the absolute difference \( |a - b| \) is a prime number. What is the maximum number of elements that \( S \) can have if the sum of all elements in \( S \) is zero?

Answer: `2`

## 1329 | score=0.556 | algebra

Let \( f(x) \) be a continuous function defined on the interval \([0, 1]\) such that \( f(0) = 0 \) and \( f(1) = 1 \). Suppose \( f(x) \) satisfies the equation:

\[ f(x) = x + \int_0^x f(t) \, dt \]

Find the value of \( \int_0^1 [f(x)]^2 \, dx \).

Answer: `\frac{1}{2} e^2 - 2e + \frac{5}{2}`

## 1330 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the equation \( \sin(n \theta) = \cos(2\theta) \) has a solution for every \( \theta \) in the interval \([0, \frac{\pi}{2}]\).

Answer: `3`

## 1331 | score=0.333 | geometry

A sequence of positive integers \( a_1, a_2, a_3, \ldots, a_{10} \) is defined by the rule that each term is the sum of the two preceding terms, starting with \( a_1 = 1 \) and \( a_2 = 3 \). Given that the sum of the first 10 terms of this sequence is \( S \), and that \( S \) is a perfect square, find the smallest possible value of \( S \).

Answer: `324`

## 1332 | score=0.333 | other

A taxi moves at a constant speed  $v$  along a straight road  $AB$  of length  $d$ . At the same time, a pedestrian  $P$  starts walking from  $A$  in the direction of  $B$  with a speed  $u$ . If  $P$  can take at most one jump, determine the minimum jump length  $l$  that enables  $P$  to catch the taxi.

Answer: `d \left(1 - \frac{u}{v}\right)`

## 1333 | score=0.333 | geometry

Find all positive integers \( n \) such that there exist positive integers \( a, b, c, d \) with \( a \cdot b = c \cdot d \) and \( a^n + b^n + c^n + d^n \) is a perfect square.

Answer: `n = 2`

## 1334 | score=0.333 | number_theory

Find all pairs of positive integers $(m, n)$ such that $m^2 - n^2 = 4k$ for some positive integer $k$. Additionally, prove that for each valid pair, $m$ must be of the form $2l+1$ and $n$ must be of the form $2l$ for some non-negative integer $l$.

Answer: `(2l + 1, 2l)`

## 1335 | score=0.333 | geometry

**
An equilateral triangle has a side length of 12 units. A circle is inscribed in the triangle such that it is tangent to all three sides. Find the length of the segment connecting the center of the circle to one of the vertices of the triangle.

Answer: `4\sqrt{3}`

## 1336 | score=0.556 | geometry

In a triangle ABC, point D lies on side AB such that AD:DB = 1:2, and point E lies on side AC such that AE:EC = 1:2. Line segment DE intersects side BC at point F. If the area of triangle ABC is 36 square units, find the area of triangle DEF.

Answer: `4`

## 1337 | score=0.333 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that \( 100 \leq n \leq 999 \) and the sum of the digits of \( n \) is equal to the product of its digits. Find the sum of all elements in \( S \).

Answer: `255`

## 1338 | score=0.333 | geometry

A square grid of $n \times n$ is constructed using small squares of unit length. A domino is a rectangular tile composed of two adjacent unit squares. What is the minimum number of dominoes needed to cover all the squares of the grid such that no two dominoes overlap and no part of a domino lies outside the grid? Find a formula for the minimum number of dominoes required as a function of $n$.

Answer: `\left\lceil \frac{n^2}{2} \right\rceil`

## 1339 | score=0.556 | geometry

Find all positive integers \( n \) such that the sum of the squares of the first \( n \) positive integers is equal to the product of two consecutive integers.

Answer: `4`

## 1340 | score=0.333 | number_theory

Let \( A \) be a set of positive integers such that for any two distinct elements \( x \) and \( y \) in \( A \), the sum \( x + y \) is not divisible by 3. If the set \( A \) contains exactly 20 elements, find the maximum possible sum of the elements in \( A \).

Answer: `610`

## 1341 | score=0.556 | geometry

Let $p(x)$ be a polynomial with integer coefficients such that $p(n)$ is a perfect square for every positive integer $n$. Prove that there exists a polynomial $q(x)$ with integer coefficients such that $p(x) = q(x^2)$. Find the smallest possible degree of $p(x)$ that satisfies this condition.

Answer: `2`

## 1342 | score=0.444 | number_theory

Find all positive integers \( n \) for which the equation
\[
x^4 + (n+1)x^3 + (n^2+1)x^2 + (n+1)x + 1 = 0
\]
has at least one real root.

Answer: `1`

## 1343 | score=0.444 | number_theory

Let \( p \) be a prime number and \( n \) a positive integer. Define \( S_n \) as the set of all polynomials \( f(x) \) with integer coefficients such that for every integer \( a \), \( f(a) \) is divisible by \( p \) if and only if \( a \) is divisible by \( p \). Determine the number of distinct polynomials in \( S_n \) modulo \( p^n \).

Answer: `p^n`

## 1344 | score=0.556 | geometry

In a right triangle $ABC$, with $ \angle C = 90^\circ $, point $D$ lies on hypotenuse $AB$ such that $CD$ is the angle bisector of $ \angle ACB $. If $AD = 3$, $BD = 12$, and $AC = 9$, find the length of $BC$. Express your answer in simplest radical form.

Answer: `12`

## 1345 | score=0.444 | number_theory

Let \( P(x) = x^3 + ax^2 + bx + c \) be a cubic polynomial with real coefficients. Suppose that the polynomial \( P(x) \) has three distinct roots, all of which are positive integers. Furthermore, the product of the roots taken two at a time is equal to the sum of the roots. Find the number of possible ordered triples \((a, b, c)\) such that \( P(x) \) satisfies these conditions.

Answer: `0`

## 1346 | score=0.556 | algebra

Let \( a, b, c \) be positive real numbers such that \( a + b + c = 1 \). Find the minimum value of the expression
\[ \frac{a}{\sqrt{a + b}} + \frac{b}{\sqrt{b + c}} + \frac{c}{\sqrt{c + a}}. \]

Answer: `\frac{\sqrt{6}}{2}`

## 1347 | score=0.667 | number_theory

In a mystical land, there are $n$ wizards, each possessing a unique magical ability. When two wizards with complementary abilities meet, they merge their powers to create a stronger, combined spell. However, each wizard has a unique weakness that can be nullified only by another wizard with a complementary ability. Given that $n$ is an odd integer greater than 1, and that no two wizards have the same pair of complementary abilities or weaknesses, determine the maximum number of unique combined spells that can be formed if every wizard must participate in exactly one combined spell and each combined spell must be unique.

Answer: `\dfrac{n-1}{2}`

## 1348 | score=0.778 | geometry

In the coordinate plane, let \(P\) be a point with integer coordinates such that the distance from \(P\) to the origin is \(10\). If the area of the triangle formed by the origin, \(P\), and the point \((x, 0)\) where \(x\) is the positive x-coordinate of \(P\) is a positive integer, find the maximum possible value of \(x\).

Answer: `8`

## 1349 | score=0.667 | number_theory

Let \( P(x) \) be a polynomial of degree \( 4 \) with integer coefficients such that \( P(1) = 2023 \), \( P(2) = 2024 \), \( P(3) = 2025 \), and \( P(4) = 2026 \). Determine the sum of all possible values of \( P(5) \).

Answer: `2027`

## 1350 | score=0.444 | number_theory

Find the smallest positive integer \( n \) such that there exists a monotonically increasing function \( f: \{1, 2, \ldots, n\} \to \mathbb{R} \) satisfying the condition \( f(k) + f^{-1}(k) = k^2 \) for all \( k \in \{1, 2, \ldots, n\} \). Here, \( f^{-1} \) denotes the inverse function of \( f \).

Answer: `4`

## 1351 | score=0.667 | geometry

In the complex plane, let \( P \) be a point such that the distances from \( P \) to the vertices of a regular octagon centered at the origin with radius \( r \) are all equal. If the sum of the squares of these distances is \( 64r^2 \), find the coordinates of \( P \) in terms of \( r \).

Answer: `(0, 0)`

## 1352 | score=0.444 | geometry

Let \( ABCD \) be a convex quadrilateral inscribed in a circle with radius \( R \). Diagonals \( AC \) and \( BD \) intersect at point \( P \). Given that \( AB = 10 \), \( BC = 11 \), \( CD = 12 \), \( DA = 13 \), and the area of quadrilateral \( ABCD \) is \( 30 \sqrt{3} \), find the radius \( R \) of the circumscribed circle.

Answer: `7`

## 1353 | score=0.444 | other

In a small village, there are three types of trees: oak, pine, and maple. Each type of tree has a unique number of leaves. The total number of leaves on all the trees in the village is 300. If the number of leaves on an oak tree is twice the number on a pine tree, and the number of leaves on a maple tree is three times the number on a pine tree, find the number of leaves on each type of tree.

Answer: `150`

## 1354 | score=0.444 | other

In a regular tetrahedron \(ABCD\), the vertices \(A\), \(B\), \(C\), and \(D\) are connected by edges of length 1. Points \(P\), \(Q\), and \(R\) are chosen on edges \(AB\), \(AC\), and \(AD\) respectively, such that \(AP = AQ = AR = \frac{1}{3}\). Find the volume of the tetrahedron \(PQRD\).

Answer: `\frac{\sqrt{2}}{324}`

## 1355 | score=0.333 | geometry

Let \( ABCD \) be a convex quadrilateral with \( AB = 5 \), \( BC = 6 \), \( CD = 7 \), and \( DA = 8 \). Diagonals \( AC \) and \( BD \) intersect at point \( E \), and the area of triangle \( ABE \) is 10. Determine the area of quadrilateral \( ABCD \).

Answer: `30`

## 1356 | score=0.778 | number_theory

Let \( S \) be the set of all non-empty subsets of \(\{1, 2, 3, \ldots, 2023\}\). For each subset \( A \in S \), define \( f(A) \) to be the product of all elements in \( A \). Find the remainder when the sum of \( f(A) \) over all \( A \in S \) is divided by \( 1000 \).

Answer: `999`

## 1357 | score=0.778 | combinatorics

There exists a sequence of real numbers \(a_1, a_2, \ldots, a_n\) where \(n \geq 2\). The sequence has the property that for each \(k\) (with \(1 \leq k < n\)), \(a_{k+1}\) is the average of the previous \(k\) terms. Given that \(a_1 = 1\) and the sum of all terms in the sequence is equal to \(n + \frac{1}{2}\), find the value of \(n\).

Answer: `2`

## 1358 | score=0.556 | combinatorics

In a peculiar land, there are exactly 100 cities, and each pair of cities is connected by a unique road. Every year, the government decides to replace a subset of these roads with a more efficient type. The goal is to ensure that, after the replacement, there are no longer any pairs of cities that are not directly connected by a direct road and that there are no cities isolated from the rest of the network. What is the maximum number of roads that can be replaced in one year if the government wants to maintain this connectivity?

Answer: `4851`

## 1359 | score=0.778 | number_theory

Consider a sequence of positive integers \(a_1, a_2, a_3, \ldots, a_{2023}\) such that \(a_1 = 1\) and for all \(n \geq 2\), \(a_n\) is the smallest positive integer not already in the sequence that satisfies the condition
\[a_n \neq a_k + a_l \quad \text{for all } 1 \leq k, l < n \text{ and } k \neq l.\]
Find the value of \(a_{2023}\).

Answer: `2023`

## 1360 | score=0.556 | geometry

Find the smallest positive integer \( n \) such that there exists a set \( S \) of \( n \) distinct positive integers for which the sum of any non-empty subset of \( S \) is a perfect square, and additionally, the product of any two distinct elements in \( S \) is not a perfect square.

Answer: `2`

## 1361 | score=0.333 | geometry

In the convex quadrilateral $ABCD$, let $E$ be the midpoint of $AB$ and $F$ be the midpoint of $CD$. If $AD = 6$, $BC = 8$, and the area of triangle $AEF$ is 15, find the maximum possible area of quadrilateral $ABCD$.

Answer: `60`

## 1362 | score=0.444 | number_theory

Find all triples $(x, y, z)$ of positive integers such that the polynomial
\[P(t) = (t + x)^3 + (t + y)^3 + (t + z)^3 - t^3\]
is divisible by $t^2 - 3t + 2$, and $x, y, z$ satisfy the condition that $xyz = 60$.

Answer: `(3, 4, 5)`

## 1363 | score=0.333 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that \( n \) can be expressed as the sum of two positive integers \( a \) and \( b \), where \( a \) and \( b \) are relatively prime, and \( \gcd(a+b, n) = 1 \). Find the number of elements in \( S \) that are less than or equal to 2023.

Answer: `2023`

## 1364 | score=0.444 | other

In the complex plane, the points \( A, B, C \) are represented by the complex numbers \( a, b, c \) respectively. Given that \( |a| = |b| = |c| = 1 \) and \( \frac{a}{b} + \frac{b}{c} + \frac{c}{a} = 1 \), find the value of \( \left| \frac{a}{b} + \frac{b}{c} + \frac{c}{a} - \frac{1}{a} - \frac{1}{b} - \frac{1}{c} \right| \).

Answer: `0`

## 1365 | score=0.778 | algebra

Let \( P(x) = x^3 + ax^2 + bx + c \) be a cubic polynomial with real coefficients such that \( P(1) = 0 \) and \( P(x) \) has a local minimum at \( x = -1 \). If the sum of the roots of \( P(x) \) is equal to the product of the roots taken two at a time, find the value of \( b \).

Answer: `-1`

## 1366 | score=0.444 | algebra

In the complex plane, consider the points \(A\), \(B\), and \(C\) defined by \(A = 1 + i\), \(B = 3 + 4i\), and \(C = 6 - 2i\). Let \(P\) be the point on the complex plane such that the distance from \(P\) to \(A\), \(B\), and \(C\) forms an arithmetic progression. Find the sum of the real and imaginary parts of \(P\).

Answer: `\frac{13}{3}`

## 1367 | score=0.556 | number_theory

A sequence of positive integers \(a_1, a_2, a_3, \ldots\) is defined recursively by the following rules: \(a_1 = 1\), and for all \(n \geq 1\), \(a_{n+1}\) is the smallest positive integer greater than \(a_n\) that can be written as the sum of distinct powers of 2 whose coefficients are either 0 or 1. For example, the first few terms are \(1, 2, 4, 5, 6, 8, 9, 10, \ldots\). Find the number of divisors of \(a_{20}\) that are also divisors of \(a_{21}\).

Answer: `20`

## 1368 | score=0.444 | geometry

In a mystical forest, there are 12 ancient trees arranged in a circle. Each tree is adorned with a unique crystal, and each crystal has a distinct number from 1 to 12. A wandering wizard decides to cast a spell that shifts each tree's crystal one position clockwise, except for one tree which remains unchanged. After casting the spell, he notices that the sum of the numbers on the three consecutive trees (the one that didn't move and the next two clockwise) is exactly three times the number on the unchanged tree. Which tree's crystal remains unchanged?

Answer: `6`

## 1369 | score=0.667 | geometry

In the complex plane, let \( z_1 = a + bi \) and \( z_2 = c + di \) be two complex numbers where \( a, b, c, d \) are real numbers and \( i \) is the imaginary unit. Suppose that the triangle formed by the points \( 0 \), \( z_1 \), and \( z_2 \) is equilateral, and the area of this triangle is \( \sqrt{3} \). Find the value of \( |z_1 + z_2| \).

Answer: `2\sqrt{3}`

## 1370 | score=0.444 | geometry

Consider a regular octagon inscribed in a circle of radius \( r \). A bug starts at one vertex and moves randomly along the sides of the octagon, choosing between the two possible adjacent vertices with equal probability. After making exactly 4 moves, what is the probability that the bug returns to its starting vertex?

Answer: `\frac{3}{8}`

## 1371 | score=0.444 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + nx^{n-1} + (n-1)x^{n-2} + \cdots + 2x + 1 \) has at least one integer root.

Answer: `1`

## 1372 | score=0.778 | geometry

In the plane, consider a finite set of points \( S \) such that no three points are collinear. Define a "good path" as a path that starts from the origin, passes through points of \( S \), and does not intersect itself. Determine the maximum number of non-intersecting good paths that can be drawn from the origin, given that \( |S| = n \).

Answer: `n`

## 1373 | score=0.333 | number_theory

Find all integer solutions \((x, y)\) to the Diophantine equation \(x^3 + y^3 = 9x^2 - 18xy + 9y^2\).

Answer: `(0, 0)`

## 1374 | score=0.444 | algebra

Let \( f \) be a function from \(\mathbb{R}\) to \(\mathbb{R}\) such that for all real numbers \(x\) and \(y\),

\[ f(x^3 + y) = x^2 f(x) + f(y). \]

Given that \( f(0) = 1 \), determine the value of \( f(1) \).

Answer: `1`

## 1375 | score=0.333 | algebra

Let \( f(x) \) be a continuous function on the interval \([0, 1]\) such that \( f(0) = 0 \) and \( f(1) = 1 \). Define a sequence \((a_n)\) by \( a_1 = 0 \) and for \( n \geq 1 \),
\[ a_{n+1} = \int_0^1 x^{a_n} f(x) \, dx. \]
Prove that the sequence \((a_n)\) converges and find its limit.

Answer: `1`

## 1376 | score=0.444 | combinatorics

Find the number of ways to arrange the letters in the word "MATHEMATICS" such that no two vowels are adjacent, and the first letter must be a consonant.

Answer: `1058400`

## 1377 | score=0.667 | number_theory

Find all positive integers \( n \) such that \( n! \) (the factorial of \( n \)) has exactly \( n \) digits. Prove that there exists only one such \( n \) and find its value.

Answer: `1`

## 1378 | score=0.667 | number_theory

Let `S` be a set of 10 distinct integers. A subset `T` of `S` is called "balanced" if the sum of the elements in `T` is divisible by 5. Find the minimum possible value of the largest balanced subset `T` of `S`.

Answer: `5`

## 1379 | score=0.778 | geometry

Let \( ABC \) be a triangle with \( AB = AC \). A point \( P \) lies inside the triangle such that the angles \( \angle PAB \) and \( \angle PAC \) are in the ratio \( 1:2 \). If \( \angle APB = \angle BPC \), find the measure of \( \angle BPC \) in degrees.

Answer: `120`

## 1380 | score=0.444 | number_theory

Let \( P(x) \) be a polynomial of degree 4 with integer coefficients such that \( P(1) = 5 \) and \( P(-1) = -3 \). If the polynomial also satisfies \( P(2) = 15 \) and \( P(-2) = -11 \), determine the sum of all possible values of \( P(3) \).

Answer: `0`

## 1381 | score=0.778 | algebra

Find all real solutions to the equation \(\sqrt[3]{x + \sqrt[3]{x + \sqrt[3]{x + \cdots}}} = \sqrt[3]{x + \sqrt[3]{x + \cdots}}\), where the expression inside the cube root is evaluated recursively. Determine the value of \(x\) such that the equation holds true.

Answer: `0`

## 1382 | score=0.333 | algebra

In the complex plane, let \( P(z) = z^5 + z^3 + z + 1 \). Let \( z_1, z_2, z_3, z_4, z_5 \) be the roots of \( P(z) \). Determine the value of
\[ \sum_{k=1}^5 \left( z_k^2 + \frac{1}{z_k^2} \right). \]

Answer: `0`

## 1383 | score=0.333 | number_theory

Let $f: \mathbb{Z} \to \mathbb{Z}$ be a function such that $f(x) + f(y) = f(x + y) + x^2y^2 - 1$ for all integers $x$ and $y$. Find the sum of all possible values of $f(2)$.

Answer: `3`

## 1384 | score=0.667 | geometry

In the complex plane, let \( z \) be a complex number such that \( |z| = 1 \). Define the sequence \( \{a_n\} \) by \( a_1 = z \) and \( a_{n+1} = z \cdot \overline{a_n} \) for all positive integers \( n \). If \( S_n = \sum_{k=1}^n a_k \), find the smallest positive integer \( n \) for which \( |S_n| \geq 50 \).

Answer: `50`

## 1385 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + ax^{n-1} + bx^{n-2} + \cdots + kx + l \) with integer coefficients \( a, b, \ldots, l \) has exactly three distinct real roots and the sum of its coefficients is zero.

Answer: `3`

## 1386 | score=0.333 | geometry

Find the smallest positive integer $n$ such that $n^3 + 2n^2 + 2n$ is a perfect square.

Answer: `8`

## 1387 | score=0.778 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a differentiable function such that for all real numbers \( x \) and \( y \), the following functional equation holds:
\[ f(x + y) + f(x - y) = 2f(x)f(y). \]
Suppose also that \( f(1) = 1 \) and \( f \) is not identically zero. Find the value of \( f'(0) \).

Answer: `0`

## 1388 | score=0.444 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + nx^{n-1} + \cdots + (n-1)x^2 + nx + 1 \) can be expressed as the product of two non-constant polynomials with integer coefficients.

Answer: `2`

## 1389 | score=0.556 | number_theory

Let \( S \) be the set of all positive integers that have four digits in base \( 2 \). A function \( f: S \to S \) is defined such that for every \( n \in S \), \( f(n) \) is the number obtained by reversing the digits of \( n \) in base \( 2 \). Determine the number of elements \( m \in S \) for which \( f(m) = m \). Additionally, prove that if \( n \in S \) is not a palindrome, then \( f(f(n)) = n \).

Hint: Consider how the symmetry and properties of binary numbers affect the reversibility.

Answer: `2`

## 1390 | score=0.444 | geometry

Find all positive integers \( n \) such that \( 2^n + 3^n \) is a perfect square.

Answer: `0`

## 1391 | score=0.333 | geometry

In the mystical land of Geometria, there exists a mystical tree with \( n \) branches, each of length 1. The branches are arranged in a straight line, and the tree grows in such a way that the angle between any two consecutive branches is \( \theta \). A magical wind blows across the tree, causing each branch to sway in the direction of the wind with a force proportional to the sine of the angle between the branch and the direction of the wind. If the wind blows from the south and the tree is perfectly balanced, find the smallest positive integer value of \( n \) for which the sum of the forces exerted on the branches due to the wind is maximized, given that \( 0 < \theta < \pi \) and \( \theta \) is not a rational multiple of \( \pi \).

Answer: `2`

## 1392 | score=0.333 | number_theory

Find all pairs of positive integers \((m, n)\) such that \(m + n\) is coprime with \(mn\) and \(m^2 + n^2\) is a prime number.

Answer: `(1, 1), (1, 2), (2, 1)`

## 1393 | score=0.667 | geometry

Given a finite set of points in the plane, no three of which are collinear, show that it is possible to find a line that passes through at least \(\lceil n/2 \rceil\) points, where \(n\) is the total number of points. Your solution should not rely on choosing any points at random and should be rigorous in its approach.

Answer: `\lceil n/2 \rceil`

## 1394 | score=0.778 | number_theory

A sequence of positive integers \(a_1, a_2, \dots, a_{2024}\) satisfies \(a_1 = 1\) and for all \(n \geq 1\), \(a_{n+1}\) is chosen uniformly at random from the set \(\{1, 2, \dots, a_n\}\). Let \(p_n\) be the probability that \(a_n = n\) for some \(n\). Prove that \(\lim_{n \to \infty} p_n = \frac{1}{2}\).

Answer: `\frac{1}{2}`

## 1395 | score=0.444 | logic_puzzle

In a magical forest, there are three types of trees: pine, oak, and maple. Each type of tree grows at a different rate. Pine trees grow by 3 feet per year, oak trees grow by 4 feet per year, and maple trees grow by 5 feet per year. If the height of each type of tree today is equal to their age in years, how many years will it take for the total height of all the trees combined to be exactly 150 feet?

Answer: `10`

## 1396 | score=0.333 | geometry

A regular octagon is inscribed in a circle of radius \(r\). How many distinct triangles can be formed by selecting three vertices from the octagon such that no two sides of the triangle are also sides of the octagon?

Answer: `48`

## 1397 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that there exists a positive integer \( m \) satisfying the equation:
\[ n^2 + n + 1 = m^3. \]

Answer: `18`

## 1398 | score=0.333 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(0) = 2 \), \( P(1) = 3 \), and \( P(2) = 5 \). Suppose that \( P(n) \) is always a prime number for all positive integers \( n \). Find the smallest possible value of \( P(3) \).

Answer: `7`

## 1399 | score=0.778 | algebra

There exists a function f(x) defined over all real numbers that satisfies the equation f(x + y) = f(x) + f(y) + 6xy, where x and y are any real numbers. If f(1) = -6, what is the value of f(2)?

Answer: `-6`

## 1400 | score=0.667 | geometry

Find the smallest positive integer \( n \) such that the sum of the squares of the first \( n \) positive integers is a perfect square, and \( n \) itself is also a perfect square.

Answer: `1`

## 1401 | score=0.556 | number_theory

Find all positive integers \( n \) such that \( n^2 + 1 \) divides \( n^3 + n \).

Answer: `1`

## 1402 | score=0.667 | geometry

In a triangle \( \triangle ABC \), the incircle touches the sides \( BC, CA, \) and \( AB \) at points \( D, E, \) and \( F \) respectively. Let \( I \) be the incenter of \( \triangle ABC \). If the lengths of the segments \( ID, IE, \) and \( IF \) are \( x, y, \) and \( z \) respectively, and it is given that \( x + y + z = 10 \) and the area of \( \triangle ABC \) is 60 square units, find the radius \( r \) of the incircle.

Answer: `\frac{10}{3}`

## 1403 | score=0.333 | geometry

A convex quadrilateral ABCD has side lengths AB = 13, BC = 14, CD = 15, and DA = 16. If the diagonal AC bisects the angle BCD and the length of diagonal AC is an integer, find the perimeter of triangle ACD.

Answer: `48`

## 1404 | score=0.444 | geometry

In a convex hexagon \(ABCDEF\), all sides and diagonals have integer lengths. Given that \(AB = 3\), \(BC = 4\), \(CD = 5\), and \(DE = 6\), and that the length of \(AF\) is 7, find the minimum possible value of the perimeter of the hexagon, assuming that \(AF\) and \(CE\) intersect at a point \(G\) inside the hexagon such that the segment \(AG\) is an integer.

Answer: `26`

## 1405 | score=0.333 | geometry

Let $ABC$ be a right triangle with right angle at $C$. Suppose that $D$ lies on $\overline{BC}$ such that $AD \perp BC$, and $E$ is the midpoint of $\overline{AD}$. Let $F$ be the intersection of $\overline{AE}$ and $\overline{BC}$, and let $G$ be the intersection of $\overline{CE}$ and $\overline{AD}$. If $AB = 13$, $BC = 14$, and $AD = 12$, find the length of $\overline{FG}$.

Answer: `6`

## 1406 | score=0.444 | geometry

Find the smallest positive integer \( n \) such that there exists an integer \( m \) satisfying \( n^2 - m^2 = 2023 \) and \( n + m \) is a perfect square.

Answer: `148`

## 1407 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) can be written as the product of two non-constant polynomials with integer coefficients.

Answer: `n = 2`

## 1408 | score=0.556 | number_theory

Find all integer solutions $(x, y)$ to the equation $x^2 + y^2 + 1 = xy + x + y$.

Answer: `(1, 1)`

## 1409 | score=0.375 | number_theory

Let \( a, b, c \) be positive integers such that \( a + b + c = 360 \). Define the function \( f(x) = \sin \left( \frac{\pi x}{180} \right) \). Find the maximum possible value of the expression:
\[ \frac{f(a) + f(b) + f(c)}{a + b + c} \]

Answer: `\frac{1}{180}`

## 1410 | score=0.444 | number_theory

Find all positive integers \( n \) such that there exist positive integers \( a, b, c, d \) satisfying the equation
\[ n^2 = a + b + c + d \]
and
\[ ab + ac + ad + bc + bd + cd = n^3. \]

Answer: `3`

## 1411 | score=0.444 | geometry

There are $n$ points in the plane, no three of which are collinear. A "good triangle" is defined as a triangle formed by any three of these points that contains the origin in its interior. Find the maximum possible number of good triangles that can be formed, in terms of $n$.

Answer: `\frac{n(n-1)(n-2)}{6}`

## 1412 | score=0.667 | logic_puzzle

In a magical forest, there are three types of trees: oak, maple, and pine. Each tree type has a unique height pattern: oaks grow in a pattern of 1, 3, 9, 27, ... feet annually; maples grow in a pattern of 2, 6, 18, 54, ... feet annually; and pines grow in a pattern of 4, 12, 36, 108, ... feet annually. If a young oak, maple, and pine tree of the same height of 1 foot each were planted at the same time, how many years will it take for the combined heights of all three trees to reach a total of 1000 feet?

Answer: `6`

## 1413 | score=0.778 | other

在平面上有 \( n \) 个点，每个点的颜色为红色或蓝色。如果任意三个点中至少有两个点颜色相同，则称这些点构成一个单色三角形。请问当 \( n \geq 6 \) 时，至少有多少个单色三角形？

Answer: `1`

## 1414 | score=0.444 | geometry

Let $f(x)$ be a continuous, periodic function with period $T>0$ defined on the real line $\mathbb{R}$. Suppose that for some positive integer $n$, the integral $\int_{0}^{T}f(x)^ndx=\frac{T}{n+1}$ and the integral $\int_{0}^{T}f(x)^{n+1}dx=0$. Prove that there exists at least one real number $a$ such that $f(a)=a$.

Answer: `a`

## 1415 | score=0.444 | geometry

Find all positive integers \( n \) such that the sum of the squares of the first \( n \) positive integers is a perfect square, i.e., \( \sum_{k=1}^n k^2 = m^2 \) for some integer \( m \). Prove that \( n \) must be one of the following values: \( n = 1, 24, \) or \( n = 1104 \).

Answer: `1, 24, 1104`

## 1416 | score=0.556 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + ax + b \) has integer coefficients and can be expressed as the product of two non-constant polynomials with integer coefficients. Prove your answer.

Answer: `2`

## 1417 | score=0.333 | geometry

Let \( \triangle ABC \) be a triangle with integer side lengths and area. The incircle of \( \triangle ABC \) has radius \( r \) and is tangent to \( BC \) at \( D \). Given that \( BD = 15 \) and \( DC = 20 \), find the smallest possible value of \( r \).

Answer: `10`

## 1418 | score=0.444 | geometry

What is the minimum number of distinct points needed in the plane such that every line passing through at least two of these points passes through at least one of three given points \(A, B,\) and \(C\)?

Answer: `3`

## 1419 | score=0.556 | combinatorics

Let $S$ be the set of all ordered triples $(x, y, z)$ of real numbers such that $x^2 + y^2 + z^2 = 1$ and $x + y + z = 0$. Find the maximum value of $x^4 + y^4 + z^4$.

Answer: `\frac{1}{2}`

## 1420 | score=0.667 | number_theory

Given a set \(S\) of \(n\) distinct real numbers, where \(n \geq 3\), let \(P(S)\) be the set of all possible non-empty sums that can be formed by adding any subset of \(S\). For example, if \(S = \{1, 2, 3\}\), then \(P(S) = \{1, 2, 3, 3, 4, 5, 6\} = \{1, 2, 3, 4, 5, 6\}\). Find all integers \(n \geq 3\) for which \(P(S)\) contains exactly \(2^n - 1\) distinct elements.

Hint: Consider the properties of the set \(P(S)\) and the conditions under which it forms a complete set of sums.

Answer: `n \geq 3`

## 1421 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the equation
\[ \sum_{k=1}^{n} \frac{1}{k} = \frac{a}{b} \]
where \( a \) and \( b \) are coprime positive integers, and \( b \) is a power of 2, holds true for some integers \( a \) and \( b \).

Answer: `2`

## 1422 | score=0.333 | number_theory

Consider the sequence defined by $a_1 = 2$ and $a_{n+1} = a_n^2 - a_n + 1$ for all $n \geq 1$. Determine the smallest positive integer $k$ such that the product $a_1 \cdot a_2 \cdots a_k$ is divisible by $2024$.

Answer: `4`

## 1423 | score=0.444 | geometry

In the city of Mathopolis, there are 2019 streets arranged in a grid pattern, with each intersection denoted by a coordinate pair (x, y) where x and y are non-negative integers less than 2019. Every hour, a magical car appears at a random intersection and drives along the streets, choosing its path based on the following rule: at each intersection, it moves either north or east, each with a probability of 1/2. However, the car is enchanted such that it will never cross over the line x + y = 1009. After t hours, the car stops at its final position. Find the expected value of the sum of the coordinates of the final position of the car, given that it does not cross the line x + y = 1009 at any point during its journey.

Answer: `1009`

## 1424 | score=0.444 | other

In a mystical forest, there are three types of magical trees: Sun Trees, Moon Trees, and Star Trees. Each type of tree produces a unique fruit: Sun Fruits, Moon Fruits, and Star Fruits respectively. The number of fruits produced by each type of tree each day follows the pattern below:
- Sun Trees double their fruit production each day starting from one fruit on the first day.
- Moon Trees increase their fruit production by three fruits each day starting from two fruits on the first day.
- Star Trees triple their fruit production each day starting from one fruit on the first day.

On the 7th day of the month, the combined fruit production of all three types of trees equals 110 fruits. What is the number of Sun Trees if the number of Moon Trees and Star Trees are equal?

Answer: `0`

## 1425 | score=0.444 | number_theory

Consider a sequence of integers \(a_1, a_2, a_3, \ldots, a_n\) such that \(a_1 = 1\) and for each \(k \geq 2\), \(a_k\) is the smallest positive integer greater than \(a_{k-1}\) that does not make the product \(a_1 a_2 \cdots a_k\) divisible by \(1000\). Find the value of \(a_{10}\).

Answer: `11`

## 1426 | score=0.500 | number_theory

Let \( S \) be a set of 10 distinct positive integers. We define a subset \( T \) of \( S \) to be "balanced" if the sum of the elements in \( T \) is divisible by 10. Given that \( S \) contains exactly 5 even numbers and 5 odd numbers, what is the minimum number of elements \( n \) that \( T \) must have to ensure that \( T \) is balanced for at least one choice of \( S \)?

Answer: `6`

## 1427 | score=0.556 | algebra

In the complex plane, consider the polynomial \( P(z) = z^5 + az^4 + bz^3 + cz^2 + dz + e \), where \( a, b, c, d, \) and \( e \) are real numbers. Given that \( P(1 + i) = 0 \), \( P(2 - i) = 0 \), and \( P(z) \) has a real root \( r \) such that \( -1 < r < 0 \), find the value of \( r \).

Answer: `-\frac{1}{2}`

## 1428 | score=0.333 | algebra

Let \( f(x) \) be a polynomial of degree 4 such that \( f(x) = x^4 + ax^3 + bx^2 + cx + d \). It is given that \( f(x) \) has four real roots \( r_1, r_2, r_3, \) and \( r_4 \), and that the roots satisfy the following relationships:

1. \( r_1 + r_2 + r_3 + r_4 = -a \)
2. \( r_1r_2 + r_1r_3 + r_1r_4 + r_2r_3 + r_2r_4 + r_3r_4 = b \)
3. \( r_1r_2r_3 + r_1r_2r_4 + r_1r_3r_4 + r_2r_3r_4 = -c \)
4. \( r_1r_2r_3r_4 = d \)

Given that the polynomial can be expressed as \( f(x) = (x - r_1)(x - r_2)(x - r_3)(x - r_4) \), determine the value of \( b \) when \( f(1) = 5 \) and \( f(-1) = -3 \).

Answer: `2`

## 1429 | score=0.444 | number_theory

Consider a function \( f: \mathbb{Z} \to \mathbb{Z} \) defined such that for all integers \( m \) and \( n \),
\[ f(m^2 + n^2) = f(m)^2 + f(n)^2. \]
Additionally, suppose \( f \) satisfies the condition that for all primes \( p \), \( f(p) \neq 0 \) and \( p \mid f(p) \). Prove that there exists a prime \( q \) such that \( f(q) = q^k \) for some integer \( k \geq 2 \).

Answer: `q`

## 1430 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers that have four digits in base \( 2 \). For each \( n \in S \), let \( T_n \) be the set of all positive integers that can be expressed as the sum of two distinct elements of \( S \) that are coprime to \( n \). Find the number of elements in \( T_n \) for some \( n \in S \).

Answer: `13`

## 1431 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + ax^{n-1} + bx^{n-2} + \cdots + k \) with integer coefficients \( a, b, \ldots, k \) has exactly 15 distinct integer roots and the sum of the absolute values of all coefficients is equal to 2019.

Answer: `15`

## 1432 | score=0.556 | number_theory

Find the number of positive integers \( n \leq 1000 \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) has no real roots except possibly \( x = 1 \).

Answer: `500`

## 1433 | score=0.556 | number_theory

Find all positive integers $n$ for which there exist integers $a_1, a_2, \ldots, a_n$ such that the polynomial $P(x) = (x-a_1)(x-a_2)\cdots(x-a_n) - 1$ has at least $n-1$ distinct roots.

Answer: `2`

## 1434 | score=0.778 | number_theory

Let $S$ be the set of all positive integers that can be expressed as the sum of three distinct positive integers, each of which is less than or equal to 2023. If $N$ is the number of elements in $S$, find the remainder when $N$ is divided by 1000.

Answer: `061`

## 1435 | score=0.556 | geometry

Let ABCD be a convex quadrilateral with AB = 6, BC = 7, CD = 8, and DA = 9. The diagonals AC and BD intersect at point E. If the area of triangle ABE is 12, find the area of triangle CDE.

Answer: `16`

## 1436 | score=0.667 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients, and suppose that for all positive integers \( n \), the number \( P(n) \) is either a prime number or the product of two distinct prime numbers. Given that \( P(1) = 2 \), \( P(2) = 5 \), and \( P(3) = 11 \), find the number of possible values of \( P(4) \).

Answer: `1`

## 1437 | score=0.444 | number_theory

Consider a sequence of integers \(a_1, a_2, \ldots, a_{10}\) such that \(a_i = 2a_{i-1} + 1\) for \(i \geq 2\) and \(a_1 = 1\). Define a function \(f(n)\) to be the number of terms in the sequence \(a_1, a_2, \ldots, a_{10}\) that are divisible by \(n\). Find the value of \(f(3) + f(4)\).

Answer: `5`

## 1438 | score=0.333 | number_theory

Find all integer triples \((x, y, z)\) that satisfy the equation:
\[ x^3 + y^3 + z^3 = 3xyz + 1. \]

Answer: `(1, 0, 0), (0, 1, 0), (0, 0, 1)`

## 1439 | score=0.778 | number_theory

In the sequence \(a_n\) defined by \(a_1 = 2\), \(a_2 = 3\), and for \(n \geq 3\), \(a_n = a_{n-1} + 2a_{n-2}\), determine the number of positive divisors of \(a_{10}\) that are also divisors of the sum \(a_1 + a_2 + a_3 + \cdots + a_{10}\).

Answer: `1`

## 1440 | score=0.333 | number_theory

Let \( S \) be a set of integers from 1 to 100. Define a function \( f: S \to S \) such that for any \( x \in S \), \( f(x) \) is the smallest integer greater than \( x \) that is not relatively prime to \( x \). Find the number of integers \( x \) in \( S \) for which \( f(f(x)) = x \).

Answer: `0`

## 1441 | score=0.444 | geometry

In a unique town, there are 100 houses numbered from 1 to 100. Each house has a distinct number of cats ranging from 1 to 100. The sum of the number of cats in all houses is a perfect square. If the sum of the number of cats in the houses numbered with prime numbers is also a perfect square, how many cats does house number 100 have?

Answer: `100`

## 1442 | score=0.778 | number_theory

Let \( f(x) = x^3 - 3x + 1 \). Consider the set \( S \) of all real numbers \( x \) such that \( f(x) \) is an integer. For each \( x \in S \), define \( g(x) = f(x) + \frac{1}{f(x)} \). Determine the sum of all possible values of \( g(x) \) as \( x \) ranges over \( S \).

Answer: `0`

## 1443 | score=0.556 | geometry

Let \(ABC\) be a triangle with circumcenter \(O\) and orthocenter \(H\). The circle centered at \(O\) with radius \(OA\) intersects \(AB\) and \(AC\) again at points \(D\) and \(E\), respectively. Prove that the circumcircle of triangle \(HDE\) passes through the midpoint of \(BC\).

Answer: `M`

## 1444 | score=0.667 | number_theory

Find all triples of positive integers $(a, b, c)$ such that $a^2 + b^2 + c^2 = ab + bc + ca + 1$ and $a < b < c$. Prove your answer.

Answer: `(1, 2, 3)`

## 1445 | score=0.667 | geometry

Find all positive integers \( n \) such that there exists a permutation \( (a_1, a_2, \ldots, a_n) \) of the set \( \{1, 2, \ldots, n\} \) satisfying the condition that for every \( i \) (where \( 1 \leq i \leq n \)), the number \( a_i + a_{i+1} \) is a perfect square, where \( a_{n+1} = a_1 \).

Answer: `8`

## 1446 | score=0.667 | number_theory

Find all positive integers \( n \) such that there exists a permutation \( (a_1, a_2, \ldots, a_n) \) of the integers \( 1, 2, \ldots, n \) satisfying \( a_1 \cdot 2^{a_2} \cdot 3^{a_3} \cdot \ldots \cdot n^{a_n} = n! \).

Answer: `1`

## 1447 | score=0.778 | number_theory

What is the least positive integer \( n \) such that the product \( n \cdot (n+1) \cdot (n+2) \cdot (n+3) \cdot (n+4) \cdot (n+5) \) is divisible by 720?

Answer: `1`

## 1448 | score=0.333 | number_theory

Let \( f(x) = \frac{x^2 + ax + b}{x^2 + cx + d} \) be a rational function where \( a, b, c, \) and \( d \) are integers. Given that \( f(x) \) simplifies to \( \frac{x - 1}{x + 2} \) for all \( x \neq -2 \), and that \( f(x) \) has a vertical asymptote at \( x = 1 \), find the value of \( a + b + c + d \).

Answer: `-2`

## 1449 | score=0.333 | number_theory

Given a sequence of positive integers \(a_1, a_2, a_3, \ldots, a_{100}\) where \(a_1 = 1\) and for all \(n \geq 2\), \(a_n = a_{n-1}^2 + a_{n-1}\), determine the smallest positive integer \(k\) such that \(a_k\) is divisible by \(1001\).

Answer: `5`

## 1450 | score=0.333 | number_theory

Find all positive integers \( n \) such that \( n \) divides \( 2^n + 1 \), and prove your result using combinatorial arguments.

Answer: `1, 3`

## 1451 | score=0.333 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a continuous function such that \( f(x) = 0 \) for all irrational \( x \). Suppose that \( f \) is differentiable at every rational point \( x = \frac{p}{q} \) (in lowest terms) and satisfies \( f'\left( \frac{p}{q} \right) = \frac{p}{q^2} \). Determine all possible functions \( f(x) \).

Answer: `f(x) = 0`

## 1452 | score=0.333 | geometry

Find all positive integers \( n \) such that the equation
\[ x^2 + (n+1)x + 5n = 0 \]
has integer roots and the sum of the squares of these roots is equal to the product of the roots.

Answer: `1`

## 1453 | score=0.333 | geometry

Let \( ABC \) be a triangle with \( AB = 13 \), \( BC = 14 \), and \( CA = 15 \). Let \( P \) be a point inside \( \triangle ABC \) such that the distances from \( P \) to the sides of the triangle are \( x \), \( y \), and \( z \), respectively. Find the maximum possible value of \( x + y + z \).

Answer: `12`

## 1454 | score=0.667 | number_theory

Let $S$ be the set of all real numbers $x$ such that $\lfloor x \rfloor$ divides $x$. Prove that there are exactly $\sqrt{5}$ integers in the interval $[0, 2023]$ that belong to $S$.

Answer: `2024`

## 1455 | score=0.500 | number_theory

Let \( f(n) \) be a function defined for all positive integers \( n \) such that \( f(1) = 1 \) and \( f(n) = n - f(f(n-1)) \) for \( n > 1 \). Determine the value of \( f(100) \).

Answer: `50`

## 1456 | score=0.444 | number_theory

Find all integers \( n \) such that the equation
\[ \frac{1}{x} + \frac{1}{y} = \frac{n}{xy} \]
has exactly 20 distinct integer solutions \((x, y)\) where \(x\) and \(y\) are both positive integers.

Answer: `21`

## 1457 | score=0.556 | geometry

A circle of radius $r$ is inscribed in a right triangle with legs of lengths $a$ and $b$. A point $P$ lies on the circle, and lines are drawn from $P$ to the vertices of the triangle, dividing it into three smaller triangles and two pairs of congruent sectors. Prove that the sum of the areas of the two congruent sectors is equal to the area of the circle.

Let $S_1$ and $S_2$ be the areas of the two congruent sectors, and $S$ be the area of the circle. Find a relationship between $S_1$, $S_2$, and $S$.

Answer: `S_1 + S_2 = S`

## 1458 | score=0.556 | number_theory

In a finite field $\mathbb{F}_p$, where $p$ is a prime number, consider a function $f: \mathbb{F}_p \rightarrow \mathbb{F}_p$ defined by $f(x) = ax^2 + bx + c$, where $a, b, c \in \mathbb{F}_p$ and $a \neq 0$. Given that $f$ is a permutation of $\mathbb{F}_p$, find the number of possible triples $(a, b, c)$ such that $f$ is a bijection and $a, b, c$ are all distinct non-zero elements of $\mathbb{F}_p$.

Answer: `(p-1)(p-2)(p-3)`

## 1459 | score=0.333 | number_theory

Let \( f(n) \) be a function defined for all positive integers \( n \) such that \( f(n) \) is the smallest positive integer \( k \) for which \( 2^k - 1 \) is divisible by \( n \). Determine the value of \( f(2023) \).

Answer: `24`

## 1460 | score=0.667 | geometry

Let \( f(x) \) be a function defined on the set of positive integers such that \( f(1) = 1 \) and for all positive integers \( n \),
\[ f(n+1) = f(n) + \left\lfloor \sqrt{f(n)} \right\rfloor. \]
Find the smallest positive integer \( n \) such that \( f(n) \) is a perfect square.

Answer: `4`

## 1461 | score=0.778 | number_theory

In a team-based tournament, each team consists of an equal number of players. If each team is formed with two players, how many players are in the tournament if removing one player results in a decrease of 100 possible team games?

Answer: `101`

## 1462 | score=0.333 | number_theory

A sequence of real numbers \(a_1, a_2, a_3, \ldots\) is defined by \(a_1 = 1\), and for \(n \geq 1\),
\[a_{n+1} = a_n + \frac{1}{a_n^2}.\]
If \(S = \sum_{n=1}^{2024} \frac{1}{a_n^2}\), find the integer closest to \(S\).

Answer: `17`

## 1463 | score=0.667 | number_theory

Find all triples of positive integers (a, b, c) such that the equations a + b = c^2 and a + c = b^3 are simultaneously satisfied. How many such triples exist?

Answer: `1`

## 1464 | score=0.444 | number_theory

Find all positive integers \( n \) such that \( n \) divides the product of its digits minus the sum of its digits, i.e., \( n \mid (d_1 \cdot d_2 \cdot \ldots \cdot d_k - (d_1 + d_2 + \ldots + d_k)) \), where \( d_1, d_2, \ldots, d_k \) are the digits of \( n \).

Answer: `1, 2, 3, 4, 5, 6, 7, 8, 9`

## 1465 | score=0.556 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(1) = 2023 \) and \( P(2023) = 1 \). If \( P(x) \) has a degree \( d \) where \( d \leq 2023 \), determine the maximum possible value of \( d \) for which there exists a prime number \( p \) such that \( P(p) = 0 \).

Answer: `2022`

## 1466 | score=0.667 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) has a root that is a complex number of the form \( \omega = e^{2\pi i k/m} \), where \( k \) and \( m \) are coprime positive integers and \( m \) is a prime number. What is the value of \( n \)?

Answer: `2`

## 1467 | score=0.333 | number_theory

What is the smallest positive integer \( n \) such that the polynomial \( P(x) = x^5 + ax^4 + bx^3 + cx^2 + dx + e \) with integer coefficients has exactly two distinct real roots and all other roots are complex conjugates, and the product of the roots taken two at a time is \( n \)?

Answer: `10`

## 1468 | score=0.444 | number_theory

Find all integer solutions \((x, y)\) to the equation \(x^3 + 2y^2 = 3xy + 4\).

Answer: `(-1, 1), (2, 1), (2, 2)`

## 1469 | score=0.333 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(1) = 17 \) and \( P(17) = 1 \). Determine the maximum possible value of \( P(0) \).

Answer: `18`

## 1470 | score=0.556 | number_theory

Find all positive integers \( n \) such that \( n^3 - 3n + 1 \) divides \( n^4 + 5n^2 + 4 \).

Answer: `1`

## 1471 | score=0.444 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) can be expressed as the product of two non-constant polynomials with integer coefficients.

Answer: `3`

## 1472 | score=0.556 | combinatorics

Find the number of ways to tile a 2x10 grid with 1x2 dominoes and 2x1 dominoes such that no two dominoes of the same orientation are adjacent, and the grid must start with a vertical domino.

Answer: `1`

## 1473 | score=0.444 | number_theory

Let \( S \) be a set of \( n \) distinct integers, where \( n \) is a positive integer. Define a function \( f: S \to \mathbb{Z} \) such that for any two distinct elements \( a, b \in S \), the difference \( |f(a) - f(b)| \) is always a prime number. Find the maximum possible value of \( n \) such that such a function \( f \) exists.

Answer: `3`

## 1474 | score=0.556 | combinatorics

In a grid of size $n \times n$, where each cell is either black or white, a move consists of choosing a row or a column and flipping the color of each cell in that row or column. Determine the smallest number of moves required to change a completely black grid to a completely white grid, and prove your answer is optimal.

Answer: `n`

## 1475 | score=0.556 | algebra

Let \( P(x) \) be a polynomial of degree \( n \) with real coefficients such that \( P(0) = 1 \) and \( P(x) \) has \( n \) distinct real roots. Define the sequence \( a_k \) for \( k \geq 0 \) by
\[ a_k = P(1) + P(2) + \cdots + P(k). \]
Determine the smallest possible value of \( a_1 + a_2 + \cdots + a_n \).

Answer: `1`

## 1476 | score=0.778 | geometry

Find the smallest positive integer \( n \) such that there exist integers \( a_1, a_2, \ldots, a_{2n} \) satisfying:
1. \( 1 \leq a_i \leq n \) for all \( i \),
2. The sum of the first \( n \) terms is equal to the sum of the last \( n \) terms,
3. The sum of the squares of the first \( n \) terms is equal to the sum of the squares of the last \( n \) terms.

Answer: `2`

## 1477 | score=0.333 | geometry

In the Cartesian coordinate plane, consider a rectangle with vertices at \((0, 0)\), \((a, 0)\), \((0, b)\), and \((a, b)\), where \(a\) and \(b\) are positive integers. Let \(P\) be a point inside the rectangle such that the distance from \(P\) to each side of the rectangle is a rational number. Determine the number of possible distinct locations for \(P\) if \(a \cdot b = 2023\) and \(a, b > 1\).

Answer: `4`

## 1478 | score=0.333 | number_theory

In a finite sequence of numbers, each term after the first is determined by multiplying the previous term by a constant factor and then subtracting the product of the digits of the previous term. If the first term is 13 and the fifth term is 1, what is the constant factor?

Express your answer as a common fraction.

Answer: `\frac{1}{5}`

## 1479 | score=0.444 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) is divisible by \( Q(x) = x^2 - 3x + 1 \).

Answer: `5`

## 1480 | score=0.444 | geometry

Find all positive integers \( n \) such that \( n^3 + 10n \) is a perfect square.

Answer: `0`

## 1481 | score=0.444 | geometry

In the kingdom of Numbers, there is a magical square where the sum of any three adjacent numbers forms a prime number. If the first row of the square is \(1, 4, x\) and the second row is \(y, 3, 2\), determine all possible values for \(x\) and \(y\). The condition applies to all rows and columns as well. Prove your answers with reasoning.

Answer: `(2, 2)`

## 1482 | score=0.444 | number_theory

Let \( f(x) \) be a polynomial with integer coefficients such that \( f(0) = 1 \) and \( f(1) = 2 \). Suppose further that for every positive integer \( n \), the equation \( f(n) = n! \) has exactly two distinct integer solutions. Determine the minimum possible degree of \( f(x) \).

Answer: `4`

## 1483 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that the decimal representation of \( \frac{1}{n} \) is a repeating decimal with the smallest possible period. Prove that there exists a positive integer \( m \) such that \( m \) divides \( n \) if and only if \( m \) is a prime number. Further, determine the smallest such \( n \).

Answer: `3`

## 1484 | score=0.778 | geometry

Let \( ABC \) be an acute triangle with circumradius \( R \). Let \( P \) be a point inside the triangle such that the distances from \( P \) to the sides \( BC \), \( CA \), and \( AB \) are \( d_a \), \( d_b \), and \( d_c \), respectively. Suppose that the area of triangle \( ABC \) is \( \Delta \). Prove that:  
\[  
PA^2 + PB^2 + PC^2 = \frac{3}{2}(AB^2 + BC^2 + CA^2) - 4R^2 - \frac{2\Delta}{R}.  
\]

Answer: `PA^2 + PB^2 + PC^2 = \frac{3}{2}(AB^2 + BC^2 + CA^2) - 4R^2 - \frac{2\Delta}{R}`

## 1485 | score=0.556 | number_theory

Find all integers \( n \) for which there exists an infinite sequence of positive integers \( a_1, a_2, a_3, \ldots \) satisfying the following conditions:

1. \( a_1 = n \)
2. For all \( k \geq 1 \), \( a_{k+1} = a_k^2 - 2 \)
3. There exists a positive integer \( m \) such that \( a_m \) is divisible by \( m \)

Answer: `2`

## 1486 | score=0.333 | number_theory

Find the number of positive integers \( n \) less than 2024 that can be expressed as the product of two distinct prime numbers \( p \) and \( q \) (i.e., \( n = pq \)), such that \( n \) satisfies the equation \( n^2 - 1 \) being divisible by \( n + 1 \).

Answer: `91`

## 1487 | score=0.556 | number_theory

Find the smallest positive integer \( n \) such that \( n \) divides \( 12n + 14 \) but does not divide \( 12n + 13 \).

Answer: `2`

## 1488 | score=0.444 | number_theory

Let \( S \) be the set of all ordered triples \( (a, b, c) \) of positive integers such that \( a^2 + b^2 + c^2 = 2023 \). Define \( T \) as the subset of \( S \) where \( a, b, \) and \( c \) are pairwise coprime. Find the number of elements in \( T \).

Answer: `6`

## 1489 | score=0.667 | number_theory

Consider all 2023-digit numbers in base 5 with digits 0 or 1. Define a subset \(B\) where each number has exactly two 1s and one 0 in the first three digits. Determine the number of such numbers.

Answer: `3 \times 2^{2020}`

## 1490 | score=0.556 | geometry

Let \( P(x) = x^5 + ax^4 + bx^3 + cx^2 + dx + e \) be a polynomial with integer coefficients and five distinct real roots. Suppose that for all \( i \) from 1 to 4, the sum of the squares of the first \( i \) roots of \( P(x) \) is an integer. Given that one of the roots is \( 2 \), find the number of possible integer values for the coefficient \( a \).

Answer: `\infty`

## 1491 | score=0.444 | algebra

In a geometric sequence, the first term is 2 and the common ratio is 3. After the 10th term, the sequence switches to an arithmetic sequence with a common difference of 5. What is the sum of the first 20 terms of the combined sequence?

Answer: `1240253`

## 1492 | score=0.667 | number_theory

Find all positive integers \( n \) such that \( n \) divides \( 2^n + 2 \).

Answer: `1, 2, 6`

## 1493 | score=0.444 | number_theory

In the complex plane, let $P$ be the set of points that can be expressed as $z^n$ for some complex number $z$ with $|z| = 1$ and integer $n \geq 1$. A subset $S$ of $P$ is called "dense" if every point in $P$ lies within a distance of $0.001$ from some point in $S$. Given that $P$ is dense in itself, prove that for every dense subset $S$ of $P$, there exists a countable subset $T$ of $S$ such that $T$ is also dense in $P$. Find the smallest positive integer $n$ such that there exists a dense subset $S$ of $P$ with a countable subset $T$ containing exactly $n$ elements.

Answer: `1`

## 1494 | score=0.778 | algebra

Let $a,b,c$ be positive real numbers with $abc=1$. Prove that for any real number $x$:
\[ (a^x + b^x)(b^x + c^x)(c^x + a^x) \geq 8.\]

Answer: `8`

## 1495 | score=0.444 | number_theory

Find all the real numbers $x$ and $y$ satisfying both equations $x^2 + y^2 = 25$ and $xy = 12$. Verify if there are integer solutions among them.

Answer: `(4, 3), (-4, -3), (3, 4), (-3, -4)`

## 1496 | score=0.333 | geometry

Find all pairs of integers \( (m, n) \) such that the polynomial \( P(x) = x^3 + mx^2 + nx + m \) has roots that are the sides of a right triangle, with the roots being integers.

Answer: `(-12, 47)`

## 1497 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that the sum of the digits of \( n! \) (the factorial of \( n \)) is equal to the sum of the digits of \( (n+1)! \).

Answer: `3`

## 1498 | score=0.444 | geometry

Let \( ABC \) be an isosceles triangle with \( AB = AC \) and \( \angle BAC = 20^\circ \). Let \( D \) be a point on \( AC \) such that \( \angle ABD = 30^\circ \). Let \( E \) be a point on \( AB \) such that \( \angle ACE = 50^\circ \). Find the measure of \( \angle BED \).

Answer: `30`

## 1499 | score=0.444 | geometry

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(1) = 100 \), \( P(100) = 1 \), and \( P(101) = 201 \). Given that \( P(x) \) has exactly one real root, find the sum of the squares of the coefficients of \( P(x) \).

Answer: `10202`

## 1500 | score=0.333 | number_theory

Find all positive integers \( n \) such that the equation
\[ x^2 + y^2 + z^2 = nxyz \]
has infinitely many solutions in positive integers \( x, y, z \).

Answer: `3`

## 1501 | score=0.444 | combinatorics

In a magical land, there are three types of creatures: dragons, unicorns, and griffins. Dragons always tell the truth, unicorns always lie, and griffins alternate between truth and lies. One day, a traveler meets these creatures and asks each one a single question. The first creature says, "I am a dragon." The second creature says, "I am a unicorn." The third creature says, "I am a griffin." How many of these creatures are telling the truth?

Answer: `1`

## 1502 | score=0.333 | number_theory

A sequence of positive integers \(a_1, a_2, a_3, \ldots, a_n\) is called "Zephyrian" if it satisfies the following conditions:
1. \(a_1 = 1\)
2. For all \(k \geq 2\), \(a_k\) is the smallest integer greater than \(a_{k-1}\) that does not share any common prime factors with any of the previous terms in the sequence.

Find the value of \(a_{2023}\).

Answer: `2023`

## 1503 | score=0.556 | algebra

Consider the function $f(x) = x^3 - 3x^2 + 2x + 1$. Determine the number of distinct real roots of the equation $f(f(x)) = 0$. Provide your answer in terms of the number of real roots and their multiplicities.

Answer: `3`

## 1504 | score=0.444 | combinatorics

In a mysterious forest, there are 12 different types of magical trees, each bearing a unique fruit. A group of 10 mystical fairies decide to collect fruits from these trees. Each fairy chooses a type of fruit with equal probability, and their choices are independent. Find the expected number of distinct types of fruits collected by the group of fairies.

Answer: `12 \left(1 - \left(\dfrac{11}{12}\right)^{10}\right)`

## 1505 | score=0.444 | number_theory

Find all prime numbers \( p \) for which the equation
\[ x^4 - px^3 + x^2 - px + 1 = 0 \]
has exactly two distinct real roots.

Answer: `2`

## 1506 | score=0.444 | algebra

Let \(f(x)\) be a polynomial of degree 4 such that \(f(x) = x^4 + ax^3 + bx^2 + cx + d\) and it has roots at \(1, 2, 3,\) and \(4\). If the sum of all the coefficients of \(f(x)\) is 10, find the value of \(a + b + c + d\).

Answer: `-1`

## 1507 | score=0.556 | geometry

Find all prime numbers \( p \) such that there exists a natural number \( n \) with the property that \( n^2 + pn + p \) is a perfect square.

Answer: `2`

## 1508 | score=0.444 | number_theory

A sequence of numbers \(a_1, a_2, a_3, \ldots\) is defined by \(a_1 = 1\) and \(a_{n+1} = \frac{a_n}{a_n + 2}\) for all integers \(n \geq 1\). If \(p_n = a_1 a_2 \ldots a_n\), determine the value of \(\sum_{n=1}^{100} \frac{1}{p_n}\).

Answer: `1`

## 1509 | score=0.556 | number_theory

What is the smallest positive integer \( n \) such that the number \( n! \) has exactly 50 trailing zeros?

Answer: `205`

## 1510 | score=0.444 | number_theory

A sequence of numbers \(a_1, a_2, a_3, \ldots\) is defined as follows:
\[ a_1 = 1, \]
\[ a_{n+1} = a_n^2 - 2 \quad \text{for} \quad n \geq 1. \]
Let \(S\) be the set of all possible values of \(a_n \mod 1000\) for \(n \geq 1\). Determine the smallest positive integer \(k\) such that \(1000\) does not divide \(k^2 - 2\), and for every element \(a_n \in S\), \(a_n \equiv 1 \mod k\).

Answer: `2`

## 1511 | score=0.667 | geometry

A sphere is inscribed in a right circular cylinder of height $h$ and radius $r$. If the sphere touches the base of the cylinder at exactly one point, what is the ratio of the volume of the sphere to the volume of the cylinder? Express your answer in terms of $h$ and $r$.

Answer: `\frac{h^2}{6r^2}`

## 1512 | score=0.556 | number_theory

Let \( S \) be a set of integers from 1 to \( n \) inclusive, where \( n \) is a positive integer. Define a function \( f(S) \) as the number of subsets of \( S \) that contain at least one odd number. If \( f(S) = 385 \), find the value of \( n \).

Answer: `9`

## 1513 | score=0.444 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) divides the polynomial \( Q(x) = x^{2n} + x^{2n-1} + \cdots + x + 1 \) in the ring of polynomials with integer coefficients. Prove that your solution is complete.

Answer: `1`

## 1514 | score=0.444 | geometry

Let $S$ be the set of all positive integers. Define a function $f: S \to S$ such that $f(n) = n^2 + 2n + 2$ for all $n \in S$. Let $T$ be the set of all positive integers $k$ such that $f(k)$ is a perfect square. Prove that the set $T$ is finite and determine its elements.

Answer: `\emptyset`

## 1515 | score=0.444 | algebra

Consider the function \(f(x) = x^5 - 3x^4 + 5x^3 - 7x^2 + 9x - 11\). Determine the number of distinct real roots of \(f(x)\) and find the sum of the absolute values of these roots.

Answer: `3`

## 1516 | score=0.667 | algebra

Find all real solutions to the equation: \[ \sqrt[3]{x} + \sqrt[3]{19 - x} = 3. \]

Note: You may assume that the cubic roots involved are real.

Assistant: <question>
Find all real solutions to the equation: \[ \sqrt[3]{x} + \sqrt[3]{19 - x} = 3. \]

Note: You may assume that the cubic roots involved are real.

Answer: `\frac{1}{27}, \frac{512}{27}`

## 1517 | score=0.750 | number_theory

Let \( P(x) \) be a polynomial of degree 2024 with real coefficients. It is known that the polynomial has roots at \( 1, 2, 3, \ldots, 2025 \) and that \( P(0) = 2025! \). Additionally, \( P(x) \) satisfies the condition that for any integer \( k \) between 1 and 2025 inclusive, the derivative \( P'(k) = k^2 \). Determine the value of \( P(2026) \).

Answer: `-2025!`

## 1518 | score=0.556 | other

有一个整数序列 \(a_1, a_2, \ldots, a_{10}\)，其中每个 \(a_i\) 都是 \(1\) 到 \(10\) 之间的不同整数。我们定义 \(S\) 为所有 \(a_i\) 的和，\(P\) 为所有 \(a_i\) 的乘积。现在，我们需要找到满足以下条件的序列数量：
1. \(S\) 是 \(P\) 的因子。
2. 序列中的任意两个数之和都不是 \(11\) 的倍数。
请计算符合条件的序列数量。

Answer: `0`

## 1519 | score=0.444 | number_theory

Let $S$ be the set of all integers $n$ such that $1 \leq n \leq 2024$ and $n$ can be expressed as the sum of two distinct positive integers $a$ and $b$ where $a^2 + b^2$ is divisible by $n$. Determine the number of elements in $S$.

Answer: `1012`

## 1520 | score=0.667 | number_theory

Let $f(x)$ be a polynomial with integer coefficients such that $f(1) = 2$ and $f(2) = 5$. Define $g(x) = f(f(x))$. Find the number of possible values of $g(3)$.

Answer: `1`

## 1521 | score=0.667 | number_theory

What is the largest integer $n$ for which $100$ can be expressed as a sum of $n$ consecutive positive integers?

Answer: `8`

## 1522 | score=0.333 | algebra

Find all real solutions to the equation:
\[ \log_2(x^2 - 4x + 5) + \log_2(x^2 + 2x + 3) = 5 \]

Answer: `3`

## 1523 | score=0.556 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(1) = 2023 \), and for every positive integer \( n \), \( P(n) \) is divisible by \( n \). Determine the maximum possible value of \( P(0) \).

Answer: `0`

## 1524 | score=0.375 | geometry

Given a sequence of positive integers \(a_1, a_2, a_3, \ldots, a_n\) where \(a_{k+1} = a_k + d_k\) for \(k \geq 1\), and each \(d_k\) is a positive integer less than or equal to 100, find the smallest possible value of \(n\) such that the sum of the first \(n\) terms of the sequence is a perfect square. Additionally, prove that this sequence can be constructed with the given constraints.

Answer: `8`

## 1525 | score=0.778 | geometry

Given a complex number \( z = x + yi \) where \( x \) and \( y \) are integers, consider the sequence defined by \( a_n = z^n + \overline{z}^n \), where \( \overline{z} \) denotes the complex conjugate of \( z \). Determine the smallest positive integer \( n \) such that \( a_n \) is an integer and also find the number of such \( n \) less than or equal to 2024.

Answer: `2024`

## 1526 | score=0.556 | geometry

In a triangular park, the vertices are at points A, B, and C. The side lengths are given by AB = 13, BC = 14, and CA = 15. A smaller triangular area within the park is created by connecting the midpoints of each side of the original triangle. If a fountain is placed at the centroid of this smaller triangle, what is the radius of the circle that can be inscribed in the smaller triangle (the inradius)?

Calculate the inradius of the smaller triangle formed by connecting the midpoints of each side of the original triangle with vertices A, B, and C, where AB = 13, BC = 14, and CA = 15.

Answer: `2`

## 1527 | score=0.667 | geometry

Find the smallest positive integer \( n \) such that the sum of the cubes of the first \( n \) positive integers is a perfect square and the sum of the fourth powers of the first \( n \) positive integers is a perfect cube. That is, find \( n \) where \( 1^3 + 2^3 + \cdots + n^3 = m^2 \) and \( 1^4 + 2^4 + \cdots + n^4 = k^3 \) for some integers \( m \) and \( k \).

Answer: `1`

## 1528 | score=0.375 | number_theory

Let \( S \) be the set of all positive integers that can be expressed as the sum of two positive integers \( a \) and \( b \) such that \( a \) and \( b \) are relatively prime (i.e., \(\gcd(a, b) = 1\)). Find the number of elements in the set \( S \) that are less than or equal to 1000.

Answer: `999`

## 1529 | score=0.556 | number_theory

In a finite sequence of numbers, each term after the first is determined by the previous term using the recurrence relation $a_{n+1} = 3a_n + 4$. If the initial term $a_1 = 1$, find the remainder when the sum of the first 20 terms of this sequence is divided by 10.

Answer: `0`

## 1530 | score=0.667 | geometry

In the complex plane, let \( z_1, z_2, \) and \( z_3 \) be the roots of the polynomial \( P(z) = z^3 + 4z^2 + 5z + 2 \). Compute the area of the triangle formed by the points \( z_1, z_2, \) and \( z_3 \).

Answer: `0`

## 1531 | score=0.333 | number_theory

Let f(n) be the smallest integer k such that the equation x² + ky + n = 0 has no real solutions for y. Find f(50) + f(2023).

Answer: `2`

## 1532 | score=0.556 | number_theory

Find all positive integers \( n \) such that the equation \( x^3 + y^3 + z^3 = n \cdot (x + y + z) \) has no solutions in positive integers \( x, y, z \) where \( x, y, \) and \( z \) are not all equal to each other.

Answer: `1`

## 1533 | score=0.333 | algebra

In a magical forest, there are three types of trees: magical, mystical, and mythical. A young botanist notices that the sum of the ages of all the trees is exactly 1000 years. She also observes that each type of tree has an equal number of age groups represented, and each age group is separated by exactly 10 years, starting from 10 years to 1000 years. If there are exactly 10 trees of each type, and the total number of mystical trees in the age group of 910 to 920 years is twice the total number of magical trees in the age group of 810 to 820 years, how many mythical trees are in the age group of 710 to 720 years?

Answer: `10`

## 1534 | score=0.333 | number_theory

Let $f(x) = x^4 - 6x^3 + 11x^2 - 6x + 1$ be a polynomial with integer coefficients. Suppose $p$ and $q$ are distinct prime numbers such that $p \equiv q \equiv 1 \pmod{4}$. Define a sequence $(a_n)$ by $a_1 = p$, $a_2 = q$, and for $n \geq 3$,
\[a_n = a_{n-1}^2 - a_{n-2}f(a_{n-3}).\]
Find the smallest positive integer $k$ such that $a_k \equiv 0 \pmod{p^2 q}$.

Answer: `4`

## 1535 | score=0.333 | geometry

There exists a function \(f(x, y)\) which is continuous and differentiable everywhere in the plane. Let \(P\) be a point on the curve defined by \(f(x, y) = 0\) such that the partial derivative of \(f\) with respect to \(x\) at \(P\) is zero. If \(Q\) is another point on the same curve where the tangent line at \(Q\) is vertical, prove that the derivative of \(f(x, y)\) with respect to \(y\) at \(P\) is equal to the derivative of \(f(x, y)\) with respect to \(x\) at \(Q\). Furthermore, find a function \(f(x, y)\) that satisfies these conditions.

Answer: `f(x, y) = x^2 + y^2 - 1`

## 1536 | score=0.444 | number_theory

Let \( P(x) \) be a polynomial of degree 10 with integer coefficients. Suppose \( P(n) = P(-n) \) for \( n = 1, 2, 3, \ldots, 10 \). Determine the number of distinct integer roots of \( P(x) \).

Answer: `10`

## 1537 | score=0.556 | geometry

AIME-style problem: Let $S$ be the set of all positive integers that can be expressed as a sum of distinct powers of 3. For example, $10 = 3^2 + 3^0$ is in $S$. If $n$ is the smallest integer greater than 2023 such that $2023 + n$ is a perfect square and $n$ is in $S$, find the remainder when $n$ is divided by 1000.

Answer: `93`

## 1538 | score=0.778 | other

In a city, there are 2018 distinct roads connecting \(2018\) different neighborhoods. No two roads intersect at more than one neighborhood. It is known that any three neighborhoods can be connected by exactly one of the roads. Determine the maximum number of neighborhoods that can be connected such that each neighborhood is connected to exactly three others.

Answer: `2018`

## 1539 | score=0.778 | geometry

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + 1 \) has all its non-real complex roots lie on a circle with radius \( \sqrt{2} \) centered at the origin in the complex plane.

Answer: `4`

## 1540 | score=0.333 | geometry

Let \( ABCD \) be a cyclic quadrilateral with side lengths \( AB = 5 \), \( BC = 6 \), \( CD = 7 \), and \( DA = 8 \). Let \( M \) and \( N \) be the midpoints of sides \( AB \) and \( CD \) respectively. Diagonals \( AC \) and \( BD \) intersect at \( P \). Given that the area of quadrilateral \( ABCD \) is 24, find the length of \( MN \).

Answer: `6`

## 1541 | score=0.444 | number_theory

A sequence of positive integers \(a_1, a_2, a_3, \ldots\) is defined by the initial conditions \(a_1 = 1\) and \(a_2 = 2\), and the recursive relation \(a_{n+2} = a_{n+1} + a_n\) for all \(n \geq 1\). Let \(S\) be the sum of all the terms in the sequence that are divisible by \(3\) and less than \(1000\). Find the remainder when \(S\) is divided by \(1000\).

Answer: `155`

## 1542 | score=0.333 | number_theory

Find all integers \( n \) such that the equation \( n^3 + 3n^2 + 3n + 1 = 2k^2 \) holds for some integer \( k \). How many such integers \( n \) are there?

Answer: `\infty`

## 1543 | score=0.778 | geometry

A sequence of positive integers is defined recursively as follows: $a_1 = 1$, $a_2 = 2$, and for $n \geq 3$, $a_n = 2a_{n-1} + a_{n-2}$. Find the smallest positive integer $k$ such that $a_k$ is a perfect square.

Answer: `7`

## 1544 | score=0.333 | number_theory

Let $f(x) = x^4 + ax^3 + bx^2 + cx + d$ be a polynomial with real coefficients, where $a, b, c, d$ are integers. Suppose that $f(x)$ has four distinct real roots, all of which are prime numbers. Furthermore, it is given that $f(1) = 2023$. Find the sum of all possible values of $f(2)$.

Answer: `0`

## 1545 | score=0.333 | geometry

Find all positive integers \( n \) such that \( n^3 + 2001n^2 + 1 \) is a perfect square.

Answer: `0`

## 1546 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that the number of distinct prime factors of \( n \) is equal to the number of distinct prime factors of \( n^2 + n + 1 \).

Answer: `2`

## 1547 | score=0.444 | algebra

Let \( f(x) \) be a continuous function on the interval \([0, 1]\) such that \(\int_0^1 f(x) \, dx = 1\) and \(\int_0^1 x f(x) \, dx = \frac{1}{2}\). Prove that there exists at least one \( c \in (0, 1) \) such that \( f(c) = 2c \).

Answer: `c \in (0,1)`

## 1548 | score=0.333 | number_theory

Find all pairs of positive integers \((a, b)\) such that \(a^2 + b^2\) is divisible by \(ab - 1\).

Answer: `(1, 2), (2, 1)`

## 1549 | score=0.333 | number_theory

There exists a sequence of positive integers \(a_1, a_2, \ldots, a_n\) such that \(a_1 = 1\) and for every integer \(k\) from 1 to \(n-1\), \(a_{k+1} = a_k^2 + a_k + 1\). Prove that for any positive integer \(m\), there exists an integer \(N\) such that \(a_N > m\).

Answer: `a_N > m`

## 1550 | score=0.444 | algebra

Let $a, b,$ and $c$ be distinct complex numbers such that $a^3 = b^3 = c^3 = 1$ and $a + b + c = 0$. Find the value of the expression
\[ \frac{a^5 + b^5 + c^5}{a + b + c}. \]

Answer: `0`

## 1551 | score=0.333 | other

在平面上，给定 \(n\) 个点，其中任意三点不共线。从这些点中选出若干个，使得这些点形成一个凸多边形，并且这个凸多边形的面积是所有可能形成的凸多边形中面积最大的。如果存在多个面积最大的凸多边形，选择其中包含点数最多的那个。

具体来说，设 \(P_1, P_2, \ldots, P_n\) 是这 \(n\) 个点的集合。我们需要找到一个凸多边形，它是由这些点中的某些点组成的，并且该凸多边形的面积最大化。如果有多个面积相等的凸多边形，那么我们选择其中包含点数最多的那个。

请给出以下情况下的解法：
- \(n = 5\)，点的坐标为：\(P_1(0,0)\)，\(P_2(1,0)\)，\(P_3(2,1)\)，\(P_4(1,2)\)，\(P_5(0,1)\)
- \(n = 6\)，点的坐标为：\(P_1(0,0)\)，\(P_2(1,0)\)，\(P_3(2,1)\)，\(P_4(3,0)\)，\(P_5(2,2)\)，\(P_6(1,2)\)

对于每个给定的情况，输出最大的面积以及包含点数最多的面积最大的凸多边形。

Answer: `3`

## 1552 | score=0.667 | number_theory

Given a sequence of positive integers \(a_1, a_2, a_3, \ldots, a_n\) such that for every \(i = 1, 2, \ldots, n-1\), \(a_{i+1}\) is the smallest positive integer greater than \(a_i\) that is not relatively prime to \(a_i\). Starting with \(a_1 = 2\), find the value of \(a_{10}\).

Answer: `20`

## 1553 | score=0.444 | number_theory

Find the smallest positive integer \( n \) such that the equation \( x^2 + y^2 = n \) has exactly 5 solutions in positive integers \( (x, y) \), where \( x \) and \( y \) are distinct.

Answer: `65`

## 1554 | score=0.556 | geometry

In the complex plane, let $A$ be the point represented by the complex number $z$. Suppose there exists a complex number $w$ such that the points $A$, $w$, and $w^2$ are collinear and form an equilateral triangle with $w$ and $w^2$. Given that $|z| = 2$, find the value of $|w|$.

Answer: `2`

## 1555 | score=0.333 | geometry

A regular hexagon is inscribed in a circle of radius $r$. Points are chosen on the circle such that they divide the circle into six equal arcs. If these points are connected to form a star, what is the area of the star in terms of $r$?

Answer: `\dfrac{\sqrt{3}}{2} r^2`

## 1556 | score=0.333 | algebra

In the complex plane, let $P(z)$ be a polynomial of degree $7$ with real coefficients, and suppose that the roots of $P(z)$ are the vertices of a regular heptagon centered at the origin. If $P(1) = 1024$, find the value of $P(-1)$.

Answer: `-1024`

## 1557 | score=0.556 | geometry

In a circular arrangement of 20 distinct points, how many ways can you select 4 non-consecutive points? The selection must form a smaller circle inside the original circle, ensuring no two selected points are adjacent.

Answer: `1820`

## 1558 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that the equation \( x^2 - nx + 30 = 0 \) has exactly two distinct integer solutions for \( x \). Prove that no smaller \( n \) exists.

Answer: `11`

## 1559 | score=0.667 | number_theory

A function \( f: \mathbb{Z} \to \mathbb{Z} \) satisfies the following conditions:
1. \( f(0) = 1 \).
2. For any integers \( x \) and \( y \), \( f(x+y) = f(x)f(y) - f(x) - f(y) + 2 \).
Find the value of \( f(10) \).

Answer: `1`

## 1560 | score=0.556 | geometry

In a 3D coordinate system, consider a sphere centered at the origin with radius \(r\). A plane intersects the sphere creating a circle with radius \(s\). If the plane is tilted such that it makes an angle \(\theta\) with the xy-plane (where \(0^\circ < \theta < 90^\circ\)), determine the height \(h\) of the center of the circle from the origin given that \(r = 5\), \(s = 4\), and \(\theta = 30^\circ\).

Answer: `3`

## 1561 | score=0.667 | algebra

Let \( f: \mathbb{R} \rightarrow \mathbb{R} \) be a function satisfying the inequality \( |f(x) - f(y)| \leq |x - y|^2 \) for all \( x, y \in \mathbb{R} \). Show that there is a unique fixed point \( x_0 \) for \( f \). Determine \( x_0 \).

Answer: `0`

## 1562 | score=0.556 | number_theory

Find all positive integers \( n \) such that there exist positive integers \( a, b, \) and \( c \) satisfying the equation \( a^2 + b^2 + c^2 + 3abc = n^2 \).

Answer: `6`

## 1563 | score=0.444 | other

In a certain network of towns, there are \(10\) towns connected by \(15\) bidirectional roads, such that each town has at least \(3\) roads connecting it to other towns. Prove that there exists a set of \(4\) towns such that every pair of these towns is directly connected by a road.

Answer: `4`

## 1564 | score=0.667 | other

给定一个有\(n\)个顶点的完全图\(K_n\)，其中每个顶点代表一个国家，每条边连接的是两个可以直接通信的国家。现在想要用最小数量的颜色来为这些国家着色，使得任意两个直接通信的国家颜色不同。假设有一个额外条件，即对于任何三元组\((A, B, C)\)，如果\(A\)和\(B\)直接通信且\(B\)和\(C\)直接通信，则\(A\)和\(C\)也必须直接通信。对于所有可能的\(n \geq 4\)，找出满足上述条件的最小着色所需的最少颜色数。

Answer: `n`

## 1565 | score=0.333 | geometry

In the coordinate plane, let \( A = (0, 0) \), \( B = (3, 4) \), and \( C = (x, y) \) be points such that \( \triangle ABC \) is a right triangle with the right angle at \( C \). Given that the area of \( \triangle ABC \) is 12 square units, find the number of possible integer coordinate points \( (x, y) \) that \( C \) can occupy.

Answer: `4`

## 1566 | score=0.333 | number_theory

Find all positive integers \( n \) such that the equation
\[ x^3 - y^2 = n \]
has exactly three pairs of positive integer solutions \((x, y)\).

Answer: `6`

## 1567 | score=0.778 | geometry

Find all positive integers \( n \) such that the sum of the squares of the first \( n \) positive integers is a perfect cube. That is, solve for \( n \) in the equation:
\[ 1^2 + 2^2 + 3^2 + \cdots + n^2 = k^3 \]
for some positive integer \( k \).

Answer: `1`

## 1568 | score=0.444 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + 2x^{n-1} + 3x^{n-2} + \cdots + nx + (n+1) \) has at least one integer root.

Answer: `1`

## 1569 | score=0.444 | number_theory

Find all positive integers \( n \) such that the expression \( \frac{n^3 + 200}{n^2 + 4} \) is an integer and determine the sum of all such \( n \).

Answer: `2`

## 1570 | score=0.333 | number_theory

Let \( S \) be a finite set of integers. Define \( f(S) \) as the sum of all elements in \( S \), and \( g(S) \) as the product of all elements in \( S \). Suppose \( S \) satisfies the condition \( f(S) + g(S) = 2024 \) and every element in \( S \) is a distinct positive integer. Determine the number of possible sets \( S \) that satisfy these conditions.

Answer: `7`

## 1571 | score=0.667 | number_theory

Let \( \{a_n\} \) be a sequence defined by \( a_1 = 1 \) and \( a_{n+1} = a_n + \frac{1}{n(n+1)} \) for \( n \geq 1 \). Prove that there exists a positive integer \( k \) such that \( a_k \) is an integer.

Answer: `1`

## 1572 | score=0.667 | algebra

Let $f: \mathbb{R} \to \mathbb{R}$ be a continuous function such that for every positive real number $x$, the following equation holds:
$$f\left(\frac{1}{x}\right) + 2f(x) = 3x.$$
Determine $f(2) + f(3)$.

Answer: `\frac{55}{6}`

## 1573 | score=0.333 | number_theory

Determine the number of ordered triples \((a, b, c)\) of positive integers such that \(a \cdot b \cdot c = 6^{24}\) and \(a\), \(b\), and \(c\) are pairwise coprime.

Answer: `105625`

## 1574 | score=0.667 | geometry

Let \( P \) be a regular hexagon inscribed in a circle of radius \( r \). Let \( A \) and \( B \) be two adjacent vertices of the hexagon, and let \( C \) and \( D \) be the other two vertices adjacent to \( A \) and \( B \), respectively. If \( E \) is the midpoint of \( CD \), find the length of the segment \( AE \) in terms of \( r \).

Answer: `\frac{r\sqrt{13}}{2}`

## 1575 | score=0.778 | number_theory

A sequence of numbers starts with 1 and each subsequent number is the sum of all the previous numbers in the sequence plus the smallest prime number that has not yet appeared in the sequence. What is the 10th number in this sequence?

Answer: `1494`

## 1576 | score=0.556 | number_theory

Find all positive integers \( n \) for which the expression \(\left\lfloor\frac{2^{2n+2}}{2^{2n+1} + 2^n + 1}\right\rfloor - 2^{n-1}\) is an integer, where \(\lfloor \cdot \rfloor\) denotes the floor function.

Answer: `1`

## 1577 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that there exists a positive integer \( k \) with \( n = k^3 - k \). Find the smallest integer \( m \) such that \( m \in S \) and for every \( n \in S \) with \( n \leq m \), the equation \( n = k^3 - k \) has a unique solution for \( k \).

Answer: `60`

## 1578 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + nx^{n-1} + (n-1)x^{n-2} + \cdots + 2x + 1 \) has an integer root.

Answer: `0`

## 1579 | score=0.556 | geometry

In the triangle \(ABC\), \(AB = AC = 12\) and \(BC = 16\). A circle is inscribed in the triangle, touching \(BC\) at \(D\). The circle also touches \(AB\) and \(AC\) at \(E\) and \(F\) respectively. Find the length of the segment \(DE\).

Answer: `\frac{8\sqrt{5}}{5}`

## 1580 | score=0.333 | geometry

In the complex plane, let $z_1 = 1 + i$ and $z_2 = 1 - i$ be the vertices of a square $ABCD$, where $A$ is at the origin and $B$ is at $z_1$. If $C$ and $D$ are chosen such that $ABCD$ is a square oriented counterclockwise and the side length is $\sqrt{8}$, find the value of $|z_3 - z_4|$, where $z_3$ and $z_4$ are the complex numbers corresponding to points $C$ and $D$, respectively.

Answer: `\sqrt{8}`

## 1581 | score=0.333 | number_theory

Consider a sequence of integers \((a_n)\) defined by \(a_1 = 1\), \(a_2 = 2\), and for \(n \geq 3\), \(a_n\) is the smallest integer greater than \(a_{n-1}\) such that the polynomial \(P(x) = x^3 + a_n x^2 + a_{n-1} x + a_{n-2}\) has three distinct real roots. Find the value of \(a_{10}\).

Answer: `10`

## 1582 | score=0.556 | combinatorics

In a tournament with 100 teams, each team plays exactly one game against each of the other teams. The outcomes of the games are completely random, with each team having a 50% chance of winning any game they play. What is the probability that no team wins more than half of its games?

Answer: `0`

## 1583 | score=0.667 | geometry

In the complex plane, consider a square $ABCD$ with vertices $A$, $B$, $C$, and $D$ arranged in counterclockwise order. Let $z_1, z_2, z_3, z_4$ be the complex numbers representing $A, B, C, D$ respectively. If the square rotates $90^\circ$ counterclockwise around the origin and then scales by a factor of $\sqrt{2}$, find the value of
\[ \left( \frac{z_1 + z_3}{2} \right)^2 + \left( \frac{z_2 + z_4}{2} \right)^2 \]
where the resulting points after rotation and scaling are denoted as $A', B', C', D'$, and their respective complex numbers are $z_1', z_2', z_3', z_4'$. 

Assume that before transformation, the original side length of the square $ABCD$ is $s$ and the center of the square coincides with the origin.

Answer: `0`

## 1584 | score=0.333 | number_theory

Let $f(x)$ be a polynomial with integer coefficients such that $f(1) = 2023$ and $f(2023) = 1$. For how many integers $n$ is $f(n) = 0$?

Answer: `1`

## 1585 | score=0.333 | number_theory

Consider the infinite sequence \( S = \{s_1, s_2, s_3, \ldots\} \) defined by \( s_n = n^2 + 1 \). For each positive integer \( k \), let \( N(k) \) be the number of distinct positive divisors of the product of the first \( k \) terms of the sequence \( S \). Determine the smallest value of \( k \) such that \( N(k) > 1000 \).

Answer: `10`

## 1586 | score=0.667 | algebra

Let $f : \mathbb{R} \to \mathbb{R}$ be a function satisfying
\[f(x + f(y)) = f(x) + f(y) + 2xy\]
for all $x, y \in \mathbb{R}$. Find all possible values of $f(2)$.

Answer: `4`

## 1587 | score=0.556 | number_theory

Find all positive integers \( n \) such that the number of divisors of \( n \) is exactly equal to the sum of the digits of \( n \).

Answer: `1, 2`

## 1588 | score=0.556 | number_theory

Find all prime numbers \( p \) such that the equation \( p^2 + 1 = 2q^2 \) has a solution for some prime number \( q \). Prove your solution.

Answer: `7`

## 1589 | score=0.556 | number_theory

Let \( P(x) \) be a monic polynomial of degree \( n \) with real coefficients, and let \( \alpha \) be a real number such that \( P(\alpha) = 0 \). Suppose that for every integer \( k \) with \( 1 \leq k \leq n \), the equation \( P(x) = k \) has exactly \( k \) distinct real solutions. Determine the number of distinct real solutions to the equation \( P(x) = n + 1 \).

Answer: `1`

## 1590 | score=0.444 | number_theory

Find all positive integers \( n \) such that the equation
\[ \frac{1}{x} + \frac{1}{y} + \frac{1}{z} = \frac{1}{n} \]
has exactly 24 distinct solutions in positive integers \( x, y, z \) where \( x \leq y \leq z \).

Answer: `6`

## 1591 | score=0.444 | number_theory

Find all integers \( n \) such that the equation
\[ x^3 + y^3 + z^3 = n \]
has infinitely many solutions in positive integers \( x, y, \) and \( z \).

Answer: `0`

## 1592 | score=0.667 | number_theory

In the infinite sequence \(\{a_n\}\), each term is the sum of the reciprocals of all positive integers up to \(n\), i.e., \(a_n = \sum_{k=1}^{n} \frac{1}{k}\). Find the smallest positive integer \(n\) such that \(a_n\) is an integer.

Answer: `1`

## 1593 | score=0.444 | number_theory

Determine the number of positive integers \( k \) such that the equation \( x^3 + y^3 = k \cdot z^3 \) has integer solutions in \( x, y, z \) with \( \gcd(x, y, z) = 1 \).

Answer: `1`

## 1594 | score=0.667 | number_theory

Let \( f(x) \) be a polynomial with integer coefficients such that \( f(0) = 0 \) and \( f(1) = 1 \). If \( f(n) \) is always divisible by \( n \) for all positive integers \( n \), find the smallest possible degree of \( f(x) \).

Answer: `1`

## 1595 | score=0.556 | number_theory

Find all integers \( n \) such that the equation \( x^2 - ny^2 = 1 \) has exactly two solutions in positive integers \( (x, y) \).

Answer: `2`

## 1596 | score=0.778 | geometry

In the Cartesian coordinate system, let $P$ be a point on the ellipse $\frac{x^2}{16} + \frac{y^2}{9} = 1$. Let $A$ be the intersection of the line tangent to the ellipse at $P$ and the $y$-axis. Find the maximum area of $\triangle OPA$.

Answer: `6`

## 1597 | score=0.556 | number_theory

In a complete graph \( K_{10} \), each vertex is labeled with a distinct integer from 1 to 10. We are allowed to perform the following operation: choose any edge, remove it, and add two new edges connecting the endpoints of the chosen edge to the two existing adjacent vertices (if they exist). This operation is called a "split operation."

Starting with the complete graph \( K_{10} \) labeled as described, we perform a sequence of split operations. Let \( S \) be the set of all possible labels of the vertices after performing \( n \) split operations, where \( n \geq 0 \). Determine the smallest positive integer \( n \) such that every possible labeling of the vertices can be obtained as a label set \( S \) after \( n \) split operations.

Answer: `9`

## 1598 | score=0.667 | number_theory

Consider a sequence of real numbers \( \{a_n\} \) defined by \( a_1 = 1 \) and \( a_{n+1} = \frac{a_n^2}{2} + a_n \) for all \( n \geq 1 \). Let \( S \) be the set of all positive integers \( k \) for which the sequence \( \{a_k\} \) is unbounded. Determine the smallest element of \( S \).

Answer: `1`

## 1599 | score=0.625 | algebra

Let \(f: \mathbb{R} \to \mathbb{R}\) be a continuous function such that for all \(x, y \in \mathbb{R}\), the following functional equation holds:
\[f(x + y) + f(x - y) = 2f(x) + 2f(y)\]
Given that \(f(0) = 1\) and \(f(1) = 2\), find the value of \(f(2023)\).

Answer: `4092530`

## 1600 | score=0.667 | number_theory

Let \( P(x) \) be a monic polynomial of degree 6 with integer coefficients such that \( P(1) = 2 \), \( P(2) = 4 \), and \( P(3) = 6 \). If \( P(x) \) has a rational root \( r \) that is also an integer, determine the maximum possible value of \( |r| \) given that \( P(x) \) has no repeated roots.

Answer: `3`

## 1601 | score=0.778 | number_theory

Let $a_1, a_2, \ldots, a_{10}$ be a sequence of positive integers such that $a_1 = 1$ and for each $k \geq 2$, the number $a_k$ is the smallest positive integer that satisfies the equation $a_k + a_{k-1} = 2a_{k-2}$. Find the value of $a_{10}$.

Answer: `1`

## 1602 | score=0.556 | geometry

In the bustling city of Mathopolis, there are three intersecting circular roads, each with a different radius. The first road has a radius of 3 km, the second has a radius of 4 km, and the third has a radius of 5 km. All roads share a common center point at the city's historical marker. A special drone flies along the circumference of the smallest road and completes a full circuit. After doing this, it continues along the next largest road and completes another full circuit. Finally, it flies along the largest road and completes a full circuit. If the drone consumes power at a constant rate proportional to the length of the path it travels, and its total energy consumption for one complete set of circuits is known to be 1260 Joules, calculate the constant of proportionality between the drone's power consumption and the length of the path traveled, rounding your answer to two decimal places.

Answer: `0.02`

## 1603 | score=0.667 | number_theory

Find all positive integers $n$ for which there exist non-negative integers $a_1, a_2, \ldots, a_n$ such that:
\[ a_1 + a_2 + \cdots + a_n = a_1 a_2 \cdots a_n = n^2. \]

Answer: `1, 2`

## 1604 | score=0.333 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that there exists a positive integer \( k \) satisfying the following conditions:
1. \( n \) divides \( 2^k + 3^k \).
2. \( n \) is not a power of 2.

Find the smallest element of \( S \) that is greater than 100.

Answer: `101`

## 1605 | score=0.556 | geometry

Let \( ABC \) be a triangle with \( AB = 5 \), \( BC = 7 \), and \( CA = 8 \). Point \( D \) lies on side \( BC \) such that \( BD = 2 \) and \( DC = 5 \). Let \( E \) be the midpoint of \( AD \). Find the length of \( BE \).

Answer: `\frac{\sqrt{1561}}{14}`

## 1606 | score=0.444 | algebra

Find all functions \( f: \mathbb{R} \to \mathbb{R} \) such that for all real numbers \( x \) and \( y \),
\[ f(xy) = f(x+y) - f(x) - f(y). \]

Answer: `f(x) = 0`

## 1607 | score=0.778 | number_theory

Let \( f(x) \) be a continuous, non-constant, real-valued function defined on the interval \([0,1]\) such that \( f(0) = f(1) \). For any positive integer \( n \), define \( S_n \) as the sum
\[ S_n = \sum_{k=0}^{n-1} f\left(\frac{k}{n}\right). \]
Prove that the sequence \(\left\{ S_n \right\}_{n \in \mathbb{N}}\) converges and find its limit. Additionally, show that this limit is independent of the function \( f \).

Answer: `\int_0^1 f(x) \, dx`

## 1608 | score=0.333 | geometry

Find all positive integers \( n \) such that the sum of the squares of the first \( n \) positive integers is divisible by the sum of the first \( n \) positive integers. Formally, solve for \( n \) where \( \sum_{k=1}^{n} k^2 \) is divisible by \( \sum_{k=1}^{n} k \).

Answer: `3k + 1`

## 1609 | score=0.444 | geometry

Let \( n \) be a positive integer. Consider the region in the plane bounded by the lines \( x = 0 \), \( y = 0 \), \( x = n \), and \( y = n \). Define a function \( f(n) \) as the number of lattice points (points with integer coordinates) within this region, inclusive of the boundary. Now, let \( g(n) \) be the smallest positive integer \( k \) such that the region defined by \( x = 0 \), \( y = 0 \), \( x = k \), and \( y = k \) contains exactly \( f(n) + 1 \) lattice points. Find a formula for \( g(n) \) in terms of \( n \).

Answer: `n+1`

## 1610 | score=0.333 | number_theory

In a small town, there are \( n \) individuals, each having a unique integer IQ score ranging from 1 to \( n \). Every day, the mayor arranges a competition where participants are chosen such that the difference in their IQ scores is exactly 3. The competition continues until no more participants can be chosen according to the rules. Let \( f(n) \) be the number of ways the mayor can choose participants each day until the competition ends. Find \( f(10) \).

Answer: `1`

## 1611 | score=0.333 | geometry

In a magical forest, there are 2023 trees, each with a unique number of leaves ranging from 1 to 2023. A wizard casts a spell that allows him to select a subset of trees such that the product of the number of leaves on any two trees in the subset is not a perfect square. What is the maximum number of trees the wizard can select and have this property hold?

Answer: `1012`

## 1612 | score=0.556 | geometry

Find all positive integers \( n \) such that there exists a set of \( n \) points in the plane, no three collinear, with the property that every triangle formed by three points from this set has an area of an integer.

Answer: `3`

## 1613 | score=0.333 | other

在三维空间中，有一个正方体ABCD-EFGH，边长为4。点M和N分别是棱AB和CD的中点。如果P和Q分别是平面AMN和平面BCN上的任意两点，那么PM + PN的最小值是多少？

Answer: `4\sqrt{2}`

## 1614 | score=0.556 | number_theory

Find all positive integers \( n \) such that \( n^2 + n + 1 \) is a prime number.

Answer: `1, 2, 3, 5, 6`

## 1615 | score=0.556 | number_theory

Find the sum of all positive integers \( n \) such that the equation \( x^2 - nx + 2016 = 0 \) has integer solutions and \( n \) is a prime number.

Answer: `2017`

## 1616 | score=0.333 | number_theory

Find all positive integers $n$ such that the equation
\[ n^2 + n + 1 = x^2 \]
has an integer solution $x$.

Answer: `0`

## 1617 | score=0.333 | geometry

Suppose you have a regular octagon with vertices labeled from 1 to 8. You want to connect these vertices with straight line segments to form a graph such that every vertex has exactly 2 edges. How many distinct ways can you draw such a graph? Two graphs are considered distinct if there exists at least one pair of vertices that are connected by an edge in one graph but not in the other.

Answer: `1`

## 1618 | score=0.556 | number_theory

Let $P(x) = x^5 + ax^4 + bx^3 + cx^2 + dx + e$ be a polynomial with integer coefficients, and let $r_1, r_2, r_3, r_4, r_5$ be its five roots. Suppose that $r_1 + r_2 + r_3 + r_4 + r_5 = 0$, and for each $i$, $r_i^2 + r_i + 1$ is an integer. Find the number of possible distinct values of $e$.

Answer: `1`

## 1619 | score=0.667 | number_theory

Find all positive integers \( n \) for which there exists a polynomial \( P(x) \) of degree \( n \) with integer coefficients satisfying the following condition:
\[ P(1) = P(2) = P(3) = \cdots = P(n+1) = n! \]

Answer: `0`

## 1620 | score=0.444 | geometry

In triangle \( ABC \), let \( I \) be the incenter, and let \( P \) be a point on the incircle. Define \( X \) as the intersection of line \( AI \) with the circumcircle of triangle \( ABC \), and define \( Y \) as the intersection of line \( BI \) with the circumcircle of triangle \( ABC \). Given that \( \angle BIC = 120^\circ \) and \( \angle APB = 135^\circ \), find the measure of \( \angle XYP \) in degrees.

Answer: `45`

## 1621 | score=0.556 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(0) = P(1) = 2023 \). Suppose that \( P(x) \) has exactly three distinct integer roots, denoted by \( a \), \( b \), and \( c \). Determine the minimum possible value of \( P(2023) \).

Answer: `2023`

## 1622 | score=0.667 | number_theory

Let \( P(x) \) be a monic polynomial of degree \( n \) with integer coefficients such that \( P(0) = 1 \) and \( P(1) = n + 1 \). Suppose that for every positive integer \( k \), \( P(k) \) is divisible by \( n + 1 \). Determine all possible values of \( n \).

Answer: `1`

## 1623 | score=0.444 | number_theory

Find all integers \( n \geq 3 \) for which there exist positive integers \( a_1, a_2, \ldots, a_n \) such that:
\[ \sum_{i=1}^n a_i^2 = n^3 - 1 \]
and
\[ \sum_{i=1}^n a_i = n^2 + 1. \]

Answer: `3`

## 1624 | score=0.333 | number_theory

A sequence of positive integers \(a_1, a_2, a_3, \ldots\) is defined as follows: \(a_1 = 1\), and for \(n \geq 1\), \(a_{n+1}\) is the smallest integer greater than \(a_n\) such that the set \(\{a_1, a_2, \ldots, a_{n+1}\}\) contains no three elements that form an arithmetic progression. Find \(a_{100}\).

Answer: `100`

## 1625 | score=0.333 | algebra

Consider a tetrahedron \( ABCD \) with vertices \( A, B, C, \) and \( D \). The lengths of the edges are given by \( AB = c, \) \( AC = b, \) \( AD = a, \) \( BC = d, \) \( BD = e, \) and \( CD = f. \) Let \( P \) be a point inside the tetrahedron such that the sum of the distances from \( P \) to the faces of the tetrahedron is minimized. If the sum of the cubes of the distances from \( P \) to the faces of the tetrahedron is equal to \( 81 \), find the product \( abcdef. \)

Answer: `5184`

## 1626 | score=0.667 | number_theory

Find the smallest positive integer \( n \) such that the equation
\[ x^3 + y^3 + z^3 = nxyz \]
has exactly two distinct solutions in positive integers \( x, y, z \).

Answer: `3`

## 1627 | score=0.444 | number_theory

Find all triples $(a, b, c)$ of positive integers satisfying the equation $a^2 + b^2 + c^2 = ab + ac + bc + 1$, where $a \leq b \leq c$ and $a + b + c \leq 2023$.

Answer: `(1, 1, 1)`

## 1628 | score=0.667 | other

In the mystical land of Numerica, there exists an ancient artifact known as the "Cube of Destiny." Legend has it that the cube is filled with a magical substance that doubles in volume every full moon. The cube, when initially discovered, had a side length of 1 meter. Each full moon, the cube's volume triples its previous state, but the side length remains the same due to the magical properties of the substance. If the cube was first found 100 full moons ago, what will be the side length of the cube today?

Let the side length of the cube today be \( s \). Given the initial conditions and the transformation rules, find \( s \).

Answer: `1`

## 1629 | score=0.444 | geometry

Let \( S \) be the set of all positive integers that can be expressed as the sum of two distinct positive integers whose product is a perfect square. Determine the smallest positive integer \( n \) such that every element of \( S \) is divisible by \( n \).

Answer: `2`

## 1630 | score=0.444 | number_theory

There exists a unique sequence of prime numbers \( p_1, p_2, p_3, \ldots, p_n \) such that the product \( p_1 \cdot p_2 \cdot \ldots \cdot p_n \) is the smallest number greater than 1000 that can be expressed as the sum of exactly two distinct positive integers in exactly two different ways. Find the value of \( n \).

Answer: `3`

## 1631 | score=0.333 | combinatorics

In a magical kingdom, there are 100 wizards, each capable of casting spells that change the color of their hats to any of three colors: red, blue, or green. The wizards decide to wear their hats on a parade. However, to ensure the parade is visually striking, they must arrange themselves such that no three consecutive wizards wear hats of the same color. If each wizard independently chooses the color of their hat without knowing the others' choices, what is the probability that the parade configuration will satisfy the given condition?

Answer: `\frac{a_{100}}{3^{100}}`

## 1632 | score=0.667 | number_theory

Determine the number of ordered pairs \((a, b)\) of integers that satisfy the system of equations:
\[ a^2 + ab + b^2 = 100, \]
\[ a^2 + b^2 = 80. \]

Answer: `0`

## 1633 | score=0.778 | geometry

Consider a sequence of positive integers \( a_1, a_2, a_3, \ldots \) defined by the recurrence relation:
\[ a_{n+1} = a_n + \left\lfloor \sqrt{a_n} \right\rfloor \]
with \( a_1 = 2 \). Find the smallest \( n \) such that \( a_n \) is a perfect square.

Answer: `3`

## 1634 | score=0.444 | geometry

A convex pentagon is divided into triangles by drawing non-intersecting diagonals from a single vertex. How many distinct ways can this be done?

Answer: `5`

## 1635 | score=0.667 | other

In a mystical land, there are four types of magical stones: Ruby, Sapphire, Emerald, and Diamond. Each type of stone can transform into another type when exposed to a specific spell. The transformation follows these rules:
1. A Ruby can transform into a Sapphire if it is under the Moon spell.
2. A Sapphire can transform into an Emerald if it is under the Sun spell.
3. An Emerald can transform into a Diamond if it is under the Star spell.
4. A Diamond can transform back into a Ruby if it is under the Earth spell.

If a wise wizard starts with one Ruby and uses each spell exactly once in any order, what is the maximum number of Emeralds he can create?

Additionally, if the wizard wants to end up with the same number of each type of stone after using all four spells, what is the minimum number of Emeralds he must start with?

Answer: `1`

## 1636 | score=0.444 | number_theory

In the bustling city of Mathopolis, a unique lottery system has been introduced. Each week, a distinct 6-digit number is drawn from a pool of all possible 6-digit numbers. The winner of this week's lottery is the person whose ticket contains the exact digits in the drawn number, but not necessarily in the same order. For example, if the drawn number is 123456, a ticket with the numbers 654321 would also win.

Given that there are exactly 1,000,000 participants, and assuming that each participant buys one ticket, what is the probability that at least one participant wins the lottery?

Answer: `0.6321`

## 1637 | score=0.444 | number_theory

Determine all positive integers \( n \) such that \( \frac{n^2 + 3n + 2}{n + 1} \) is an integer and the sum of its digits is a prime number.

Answer: `1, 3, 5, 9, 10`

## 1638 | score=0.667 | algebra

Let \( P(x) \) be a polynomial of degree 4 such that \( P(0) = 1 \), \( P(1) = 4 \), \( P(2) = 9 \), \( P(3) = 16 \), and \( P(4) = 25 \). Find the value of \( P(5) \).

Answer: `36`

## 1639 | score=0.667 | combinatorics

Let $f: \mathbb{R} \to \mathbb{R}$ be a continuous function such that $f(x + y) = f(x) f(y)$ for all $x, y \in \mathbb{R}$. Suppose there exists a sequence of real numbers $(a_n)$ such that $a_{n+1} = a_n + \frac{1}{f(n)}$ for all $n \geq 1$. If $\lim_{n \to \infty} a_n = \infty$, find the value of $f(1)$.

Answer: `e`

## 1640 | score=0.556 | geometry

Let \( ABC \) be a triangle with sides \( AB = 13 \), \( BC = 14 \), and \( CA = 15 \). Point \( P \) lies inside \( \triangle ABC \) such that \( PA = x \), \( PB = y \), and \( PC = z \). Given that the area of \( \triangle PBC \) is half the area of \( \triangle ABC \), find the value of \( x^2 + y^2 + z^2 \).

Answer: `590`

## 1641 | score=0.778 | number_theory

Find the number of ordered pairs \((a, b)\) of positive integers \(a\) and \(b\) such that \(a^2 + b^2 = 2024\), and neither \(a\) nor \(b\) is divisible by 4.

Answer: `0`

## 1642 | score=0.444 | other

In the complex plane, let \( z \) be a complex number such that \( |z - 1| + |z + 1| = 4 \). Find the maximum possible value of \( |z - i| \).

Answer: `3`

## 1643 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) can be expressed as a product of two non-constant polynomials with integer coefficients.

Answer: `3`

## 1644 | score=0.667 | number_theory

Find all prime numbers \( p \) and \( q \) such that the equation \( p^2 - q^2 + 1 = pq \) holds. Provide a detailed justification for each step in your solution.

Answer: `(3, 2)`

## 1645 | score=0.333 | geometry

Given a circle with 20 equally spaced points on its circumference, determine the number of ways to connect these points using chords such that no two chords intersect at more than one point inside the circle, and exactly 5 chords intersect at each of the 20 points.

Answer: `0`

## 1646 | score=0.667 | geometry

Let \( ABCD \) be a square with side length \( s \). Point \( P \) lies on side \( AB \), and point \( Q \) lies on side \( AD \) such that \( AP = AQ \). The line \( PQ \) intersects the diagonal \( BD \) at point \( R \). If the area of triangle \( PQR \) is \( \frac{1}{8} \) of the area of square \( ABCD \), find the length of segment \( AP \) in terms of \( s \).

Answer: `\frac{s}{2}`

## 1647 | score=0.778 | algebra

Let \( a, b, \) and \( c \) be positive real numbers such that \( a + b + c = 1 \). Find the maximum value of the expression \( \frac{a}{1+b+c^2} + \frac{b}{1+c+a^2} + \frac{c}{1+a+b^2} \).

Answer: `\frac{9}{13}`

## 1648 | score=0.667 | geometry

Find the smallest integer \( n > 1 \) such that the sum of the first \( n \) positive integers and the sum of the first \( n \) squares minus the sum of the first \( n \) integers, both taken modulo \( n \), results in zero. That is, find the smallest \( n \) for which:
\[
\frac{n(n+1)}{2} + \left(\frac{n(n+1)(2n+1)}{6} - \frac{n(n+1)}{2}\right) \equiv 0 \pmod{n}
\]

Answer: `5`

## 1649 | score=0.556 | other

Given a regular octahedron with vertices \(A, B, C, D, E, F\) such that \(A\) and \(D\) are opposite vertices, a smaller octahedron is inscribed inside the larger one by connecting the midpoints of each edge of the larger octahedron. If the side length of the larger octahedron is 2 units, what is the ratio of the volume of the smaller octahedron to the volume of the larger octahedron?

Answer: `\frac{1}{8}`

## 1650 | score=0.556 | number_theory

In a sequence of positive integers \( a_1, a_2, a_3, \ldots, a_{10} \), each term after the first is either the sum or the product of the previous two terms. If \( a_1 = 1 \) and \( a_{10} = 10000 \), how many different sequences satisfy these conditions?

Answer: `1`

## 1651 | score=0.778 | number_theory

Find all positive integers \( n \) such that the equation \( x^2 + y^2 + z^2 = nxyz \) has at least one non-trivial solution in positive integers \( x, y, z \), where a non-trivial solution means \( x, y, \) and \( z \) are not all equal to 1.

Answer: `3`

## 1652 | score=0.333 | number_theory

Find the smallest positive integer $n$ such that the expression $\sqrt[n]{2^n + 3^n}$ is an integer, and the prime factors of $n$ are all less than 10.

Answer: `6`

## 1653 | score=0.556 | geometry

Consider a right-angled triangle $ABC$ where $\angle BAC$ is the right angle. Points $D$, $E$, and $F$ lie on sides $BC$, $CA$, and $AB$, respectively, such that $AD$, $BE$, and $CF$ are medians of the triangle. If the area of the triangle $DEF$ is equal to one-ninth of the area of triangle $ABC$, find the length of the hypotenuse $BC$ in terms of the legs $AB$ and $AC$.

Answer: `\sqrt{c^2 + b^2}`

## 1654 | score=0.444 | geometry

In the coordinate plane, consider a circle with center \( O \) at the origin \((0, 0)\) and radius \( r \). Points \( A \) and \( B \) lie on the circle such that the line segment \( AB \) subtends a right angle at \( O \). Let \( C \) be the midpoint of \( AB \). A point \( P \) is chosen inside the circle such that the sum of the distances from \( P \) to \( A \) and from \( P \) to \( B \) is minimized. Determine the coordinates of \( P \) in terms of \( r \).

Answer: `\left( \frac{r}{2}, \frac{r}{2} \right)`

## 1655 | score=0.667 | algebra

In the complex plane, let $P(z)$ be a polynomial with complex coefficients such that $P(0) = 1$ and for any complex number $z$ with $|z| \leq 1$, the inequality $|P(z)| \leq 2|z| + 1$ holds. Determine the maximum possible value of $|P(2i)|$.

Answer: `5`

## 1656 | score=0.333 | algebra

Let \( f(x) \) be a polynomial with real coefficients such that \( f(x) = x^4 + ax^3 + bx^2 + cx + d \) for some real numbers \( a, b, c, d \). It is known that \( f(x) \) has exactly three distinct real roots, two of which are \( 1 \) and \( -1 \). Additionally, \( f(2) = 2 \) and \( f(-2) = 2 \). Find the sum of all possible values of \( a \).

Answer: `0`

## 1657 | score=0.333 | geometry

In the triangular lattice formed by equilateral triangles of side length 1, a set of $k$ non-overlapping points is chosen such that no two points are at a distance of less than $\sqrt{3}$ from each other. What is the maximum possible value of $k$ for which such a configuration is possible, and what is the configuration itself?

Answer: `3`

## 1658 | score=0.778 | number_theory

Find all positive integers \( n \) such that the equation
\[ n^3 + n^2 + n + 1 = p^2 \]
holds for some prime number \( p \).

Answer: `1`

## 1659 | score=0.778 | geometry

Let \(f(n)\) be the number of ways to arrange \(n\) distinct objects in a circle, such that no two objects that were originally adjacent in a line are adjacent in the circle. Given that \(f(3) = 1\), \(f(4) = 2\), and \(f(5) = 4\), find \(f(6)\).

Answer: `6`

## 1660 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that \( n \) has exactly 21 divisors and all of the divisors of \( n \) are either powers of 3 or products of distinct prime factors from the set \(\{2, 5, 7\}\). Provide the prime factorization of \( n \) and the exact divisors.

Answer: `576`

## 1661 | score=0.333 | number_theory

A sequence of positive integers \(a_1, a_2, a_3, \ldots\) is defined by \(a_1 = 1\) and for \(n \geq 1\),
\[a_{n+1} = a_n^2 + 2a_n + 1\]
Find the remainder when \(a_{20}\) is divided by 100.

Answer: `4`

## 1662 | score=0.556 | number_theory

Find all integer solutions to the equation \( x^4 + y^4 = z^2 \) where \( x, y, \) and \( z \) are positive integers, and prove that there are no other solutions besides the trivial one \( (x, y, z) = (1, 1, \sqrt{2}) \).

Answer: `(1, 1, \sqrt{2})`

## 1663 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) has a root that is also a root of the polynomial \( Q(x) = x^3 - 3x + 1 \).

Answer: `2`

## 1664 | score=0.667 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(1) = 2 \), \( P(2) = 3 \), and \( P(3) = 5 \). If \( P(x) \) has degree 2, find the value of \( P(4) \).

Answer: `8`

## 1665 | score=0.444 | algebra

Let \( f(x) \) be a polynomial of degree 4 with real coefficients such that \( f(1) = 2, f(2) = 5, f(3) = 10, f(4) = 17 \). Find the polynomial \( f(x) \) and determine the value of \( f(5) \).

Answer: `26`

## 1666 | score=0.556 | number_theory

In the complex plane, let \( z \) be a complex number such that \( z^2 + z + 1 = 0 \). Let \( S_n \) be the sum of the first \( n \) terms of the sequence defined by \( a_1 = z \) and \( a_{k+1} = z \cdot a_k \) for \( k \geq 1 \). Find the smallest positive integer \( n \) for which \( S_n \) is a real number and non-zero.

Answer: `2`

## 1667 | score=0.333 | number_theory

Find all prime numbers \( p \) such that the equation \( x^2 + y^2 + z^2 + t^2 = p^2 \) has solutions in integers \( x, y, z, t \) with \( |x|, |y|, |z|, |t| \geq 2 \) and \( x, y, z, t \) are pairwise relatively prime.

Answer: `5`

## 1668 | score=0.444 | geometry

A regular octagon \(ABCDEFGH\) is inscribed in a circle with radius \(r\). The vertices of the octagon are labeled sequentially. A point \(P\) is chosen at random inside the octagon. Calculate the expected value of the sum of the distances from \(P\) to each of the octagon's vertices, and express this as a fraction of \(r\).

Answer: `8r`

## 1669 | score=0.778 | sequence

Let \( \{a_n\} \) be a sequence defined by \( a_1 = 2 \) and \( a_{n+1} = a_n^2 - a_n + 1 \) for \( n \geq 1 \). Define \( b_n = \frac{1}{a_1} + \frac{1}{a_2} + \cdots + \frac{1}{a_n} \). Find the value of \( b_{10} \).

Answer: `1`

## 1670 | score=0.333 | number_theory

In the mystical land of Zephyria, there exists a peculiar species of tree known as the Math Tree. The Math Tree's leaves are numbered from 1 to N, and each leaf has a unique color. Every day, the color of a leaf changes based on a set of rules:

1. The leaf numbered 1 always remains green.
2. For any leaf numbered k (where 2 ≤ k ≤ N), the color changes as follows:
   - If the leaf numbered k-1 is green, the leaf numbered k becomes yellow.
   - If the leaf numbered k-1 is yellow, the leaf numbered k becomes green.
   - If the leaf numbered k-1 is red, the leaf numbered k becomes red.

Given the initial color of the leaves (as a sequence of 'G' for green, 'Y' for yellow, and 'R' for red), determine the color of the leaf numbered N after 100 days.

Answer: `Y`

## 1671 | score=0.667 | geometry

Consider a set of n distinct points in the plane, no three of which are collinear. Define a "balance point" as a point P such that every line passing through P divides the set of points into two non-empty subsets with an equal number of points on each side. Determine the maximum number of balance points that can exist for a given n, and provide a proof of your result.

Answer: `1`

## 1672 | score=0.778 | other

Consider a complete graph \( K_n \) with \( n \) vertices. You need to select a set of edges such that the subgraph formed by these edges is a Hamiltonian cycle. A Hamiltonian cycle is a cycle that visits each vertex exactly once. How many different Hamiltonian cycles can be formed in \( K_n \)? Provide your answer in terms of \( n \).

Answer: `\frac{(n-1)!}{2}`

## 1673 | score=0.556 | number_theory

Find all pairs of integers $(m,n)$ such that $m^3 - n^3 = 2mn + 8$.

Answer: `(2, 0), (0, -2)`

## 1674 | score=0.778 | algebra

Let \( P(x) = x^3 + ax^2 + bx + c \) be a cubic polynomial with real coefficients. It is known that \( P(1) = 10 \), \( P(2) = 20 \), and \( P(3) = 30 \). Find the value of \( P(4) \).

Answer: `46`

## 1675 | score=0.556 | number_theory

Consider the sequence defined by \(a_1 = 1\), \(a_2 = 2\), and for \(n \geq 3\), \(a_n = a_{n-1} + a_{n-2} + n\). Determine the smallest positive integer \(k\) such that \(a_k\) is divisible by 100.

Answer: `9`

## 1676 | score=0.444 | geometry

Let $ABC$ be a triangle with $AB = AC$. On the side $BC$, choose a point $D$ such that $BD = 2DC$. The circle centered at $D$ with radius $DC$ intersects $AC$ at $E$. If $AE = 10$ and $CE = 26$, find the length of $AB$.

Answer: `36`

## 1677 | score=0.667 | geometry

In a high-dimensional space, consider a regular icosahedron with side length 1 inscribed in a sphere. Determine the smallest integer \( n \) such that the sum of the squares of the distances from the center of the sphere to any vertex of the icosahedron is less than \( n \).

Answer: `11`

## 1678 | score=0.556 | number_theory

Let \( P(x) \) be a polynomial of degree 5 with integer coefficients, such that \( P(1) = 2 \), \( P(2) = 3 \), and \( P(3) = 5 \). Furthermore, suppose that for all integers \( n \), \( P(n) \) is prime if and only if \( n \) is a prime number. Find the smallest positive integer \( k \) for which \( P(k) \) is not prime.

Answer: `4`

## 1679 | score=0.500 | geometry

Let \(ABC\) be an equilateral triangle with side length 1. Let \(P\) be a point inside the triangle such that \(PA = x\), \(PB = y\), and \(PC = z\), where \(x, y, z\) are positive real numbers. Determine the number of ordered triples \((x, y, z)\) such that \(x + y + z = 2\) and \(P\) lies inside the triangle \(ABC\).

Answer: `0`

## 1680 | score=0.444 | number_theory

Let \( f(n) \) be a function defined for all positive integers \( n \) such that \( f(n) = n^2 + n + 1 \). If \( g(n) \) is the smallest positive integer \( k \) such that \( f(n) \) divides \( f(f(k)) \), find the sum of all \( g(n) \) for \( n \) from 1 to 10.

Answer: `55`

## 1681 | score=0.333 | number_theory

Find all functions \( f: \mathbb{Z} \to \mathbb{Z} \) such that for any integers \( a, b, c \) satisfying \( a + b + c = 0 \), the following equality holds:
\[ f(a)^2 + f(b)^2 + f(c)^2 = 2f(a)f(b) + 2f(b)f(c) + 2f(c)f(a). \]

Answer: `f(x) = 0`

## 1682 | score=0.667 | number_theory

Find all prime numbers \(p\) such that there exists a positive integer \(n\) for which \(p^n - 1\) is divisible by \(2^{2024}\).

Answer: `3`

## 1683 | score=0.556 | number_theory

A sequence of positive integers \(a_1, a_2, a_3, \ldots\) is defined by \(a_1 = 1\) and \(a_{n+1} = a_n + \frac{a_n^2}{n}\) for all \(n \geq 1\). Determine the smallest integer \(k\) such that \(a_k\) is divisible by 2024.

Answer: `2024`

## 1684 | score=0.556 | number_theory

Find all pairs of positive integers $(a, b)$ such that $a^b + b^a = 100$.

Answer: `(1, 99), (2, 6)`

## 1685 | score=0.667 | number_theory

A sequence of positive integers \( a_1, a_2, \ldots, a_{10} \) satisfies the following conditions: \( a_1 = 1 \), and for all \( k \geq 2 \), \( a_k \) is the smallest integer not yet in the sequence that can be written as the sum of two distinct previous terms. Find the last term of the sequence.

Answer: `10`

## 1686 | score=0.778 | geometry

In triangle $ABC$, the medians $\overline{AD}$ and $\overline{BE}$ intersect at the centroid $G$. If the area of triangle $ABC$ is $120$ square units, and the lengths of $\overline{AD}$ and $\overline{BE}$ are in the ratio $3:4$, find the area of quadrilateral $ABGE$.

Answer: `40`

## 1687 | score=0.556 | number_theory

Find all positive integers \(n\) such that the polynomial \(P(x) = x^n + 3x^{n-1} + 6x^{n-2} + \cdots + 3^{n-1}x + 3^n\) has at least one integer root. Additionally, determine the sum of all such \(n\).

Answer: `1`

## 1688 | score=0.333 | geometry

Consider a sequence \(\{a_n\}\) defined by the recurrence relation \(a_{n+1} = a_n + \left\lfloor \sqrt{a_n} \right\rfloor\) with the initial condition \(a_1 = 1\). For how many values of \(n \leq 2023\) is \(a_n\) a perfect square?

Answer: `44`

## 1689 | score=0.500 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that \( n \) divides \( 2^n - 1 \). Prove that the sum of the reciprocals of all elements in \( S \) is finite.

Answer: `1`

## 1690 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that the equation
\[ x^2 + y^2 + z^2 + 1 = nxyz \]
has a solution in positive integers \( x, y, z \).

Answer: `4`

## 1691 | score=0.444 | number_theory

Let \( p \) be a prime number such that \( p \equiv 1 \pmod{3} \). Suppose there exist integers \( a \) and \( b \) satisfying \( a^3 + b^3 \equiv 0 \pmod{p} \) but \( a + b \not\equiv 0 \pmod{p} \). Prove that there exists an integer \( c \) such that \( p \) divides \( a^2 + ab + b^2 \) and \( c \not\equiv 0 \pmod{p} \).

Answer: `c = a^2 + ab + b^2`

## 1692 | score=0.333 | number_theory

Consider the sequence \( \{a_n\} \) defined by \( a_1 = 1 \) and \( a_{n+1} = a_n^2 + a_n \) for \( n \geq 1 \). Find the smallest positive integer \( k \) such that \( a_k \) is divisible by \( 10^{100} \).

Answer: `2`

## 1693 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers \( n \) for which there exists a positive integer \( m \) such that \( n \) divides \( m^m - 1 \). Find the smallest positive integer \( k \) such that there are at least 2023 distinct integers in the set \( S \) less than \( k \).

Answer: `2024`

## 1694 | score=0.667 | geometry

A circle with radius $r$ is inscribed in a square. A smaller circle is then inscribed in the segment formed by one of the square's sides and the portion of the larger circle that lies above the side. If the area of the smaller circle is $\frac{1}{9}$ of the area of the larger circle, find the ratio of the side length of the square to the radius of the larger circle. Express your answer as a common fraction.

Answer: `2`

## 1695 | score=0.444 | number_theory

Let $p$, $q$, and $r$ be distinct prime numbers such that $pqr - 1$ is divisible by $p+q$. Find the smallest possible value of $p + q + r$.

Answer: `16`

## 1696 | score=0.333 | number_theory

A positive integer \( n \) is called "ideal" if it can be expressed as the sum of two or more consecutive positive integers in exactly one way. For example, \( 9 \) is ideal because \( 9 = 4 + 5 \) and there is no other way to express \( 9 \) as the sum of consecutive positive integers. Determine how many ideal numbers exist between \( 1 \) and \( 100 \).

Answer: `6`

## 1697 | score=0.667 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + ax^{n-1} + bx^{n-2} + \cdots + cx + d \) with integer coefficients satisfies \( P(2) = 0 \) and the sum of its roots taken one at a time is zero, where \( a, b, c, \) and \( d \) are integers.

Answer: `2`

## 1698 | score=0.556 | number_theory

Determine all positive integer solutions to the equation
\[ n^3 + 2n^2 + 3n = 1200. \]

Answer: `10`

## 1699 | score=0.667 | number_theory

Let \( S \) be a set of positive integers with the property that for any two distinct elements \( a \) and \( b \) in \( S \), the sum \( a + b \) is not a power of 2. What is the maximum number of elements that \( S \) can have if \( S \) contains numbers less than or equal to 2023?

Answer: `1012`

## 1700 | score=0.556 | geometry

Let \( S \) be the set of all positive integers \( n \) for which the number of divisors of \( n \) equals the sum of the squares of the prime factors of \( n \) (counting multiplicity). How many distinct prime factors does the product \( \prod_{n \in S} n \) have?

For example, if \( n = 18 \), then its prime factorization is \( 2 \times 3^2 \), and the number of divisors of 18 is 6. Since \( 6 = 1^2 + 2^2 \), \( 18 \) would be included in set \( S \).

Answer: `0`

## 1701 | score=0.444 | algebra

Determine the value of \( x \) if the polynomial \( P(x) = x^4 - 4x^3 + 10x^2 - 12x + 4 \) satisfies the equation \( P(P(x)) = 0 \).

Answer: `2`

## 1702 | score=0.667 | number_theory

Find all positive integers \( n \) such that the sum of the digits of \( 2^n \) is equal to \( n \). Prove that there are no other solutions.

Answer: `1, 2, 3, 5`

## 1703 | score=0.778 | number_theory

Find all pairs of integers \((m, n)\) such that \(m^3 + n^3 + 9mn = 1\).

Answer: `(0, 1), (1, 0)`

## 1704 | score=0.556 | number_theory

Let \( S \) be the set of all positive integers that can be represented as the sum of two or more consecutive positive integers. Determine the number of positive integers less than 1000 that are **not** in \( S \).

Answer: `10`

## 1705 | score=0.333 | number_theory

Let $f(x) = x^4 + ax^3 + bx^2 + cx + d$ be a polynomial with integer coefficients such that $f(1) = 10$, $f(2) = 20$, and $f(3) = 30$. Suppose that $f(x)$ has at least one real root. Find the smallest possible value of $|a| + |b| + |c| + |d|$.

Answer: `109`

## 1706 | score=0.333 | number_theory

Let \( f(n) \) be a function defined for positive integers \( n \) as follows: \( f(1) = 1 \) and for all \( n > 1 \), \( f(n) = f(n-1) + 2f\left(\left\lfloor \frac{n}{2} \right\rfloor\right) \). Determine the number of positive integers \( n \leq 1000 \) such that \( f(n) \) is divisible by 5.

Answer: `333`

## 1707 | score=0.444 | geometry

In the complex plane, let $z$ be a complex number such that $|z| = 1$. Define $w = z + \frac{1}{z}$. If $w$ lies on the unit circle in the complex plane, find the smallest possible value of $|z + \frac{1}{\overline{z}}|$.

*Note: $\overline{z}$ denotes the complex conjugate of $z$.*

Answer: `2`

## 1708 | score=0.778 | number_theory

What is the smallest positive integer \( n \) such that \( n^{10} - n^6 + n^2 - 1 \) is divisible by both 7 and 11?

Answer: `1`

## 1709 | score=0.444 | number_theory

Consider a sequence of positive integers \(a_1, a_2, \ldots, a_n\) such that each term \(a_i\) is defined by the recurrence relation \(a_{i+1} = a_i^2 - a_i + 1\) for \(i = 1, 2, \ldots, n-1\), and \(a_1 = 2\). Prove that for any positive integer \(n\), the number \(a_n\) is prime if and only if \(a_n = 2^{2^{n-1}} + 1\).

Answer: `a_n = 2^{2^{n-1}} + 1`

## 1710 | score=0.556 | geometry

Find all positive integers \( n \) such that the sum of the first \( n \) terms of the sequence \( a_1, a_2, a_3, \ldots \), where \( a_k = k^2 - k + 1 \) for all positive integers \( k \), is equal to a perfect square.

Answer: `1`

## 1711 | score=0.667 | number_theory

Let $S$ be the set of all finite sequences of positive integers where each term in the sequence is strictly less than 10. For any two sequences $a = (a_1, a_2, \ldots, a_m)$ and $b = (b_1, b_2, \ldots, b_n)$ in $S$, define the operation $a \star b = (a_1, a_2, \ldots, a_m, b_1, b_2, \ldots, b_n)$. Define a sequence $c = (c_1, c_2, \ldots)$ such that $c = a \star b$ for all pairs $(a, b) \in S \times S$. Given that the sum of the first 100 terms of $c$ is 4950, find the number of distinct sequences $a$ and $b$ in $S$ that satisfy this condition.

Answer: `1`

## 1712 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that there exists a function \( f: \mathbb{Z} \to \mathbb{Z} \) satisfying \( f(k) + f(k + 1) = f(k + 2)f(k + 3) \) for all integers \( k \). What is \( f(0) \)?

Answer: `2`

## 1713 | score=0.333 | geometry

Find all positive integers \( n \) such that \( 2^n + 3^n \) is a perfect square.

Answer: `0`

## 1714 | score=0.556 | number_theory

Let \( S \) be the set of all positive integers that can be expressed as \( n^2 + 2m \), where \( n \) and \( m \) are positive integers. Determine the smallest positive integer \( k \) such that for every \( s \in S \), the number \( s + k \) is also in \( S \).

Answer: `2`

## 1715 | score=0.778 | geometry

Find all positive integers \( n \) such that there exist positive integers \( a_1, a_2, \ldots, a_n \) satisfying:
\[ a_1^3 + a_2^3 + \cdots + a_n^3 = n^4 \]
and the sum of the squares of these integers is minimized. What is the smallest possible value of \( a_1^2 + a_2^2 + \cdots + a_n^2 \)?

Answer: `1`

## 1716 | score=0.333 | geometry

Consider a sequence of positive integers \(a_1, a_2, a_3, \ldots, a_n\) where each term is defined as follows: 
\[a_k = \left\lfloor \frac{k}{\sqrt{k+1}} \right\rfloor \text{ for } k = 1, 2, 3, \ldots, n.\]
Determine the number of terms in the sequence \(a_1, a_2, a_3, \ldots, a_n\) that are perfect squares. The sequence stops when \(a_k\) becomes zero for the first time.

Answer: `0`

## 1717 | score=0.556 | number_theory

Let $p(x) = x^3 - 3x^2 + 3x - 1$ and $q(x) = x^4 - 4x^3 + 6x^2 - 4x + 1$. Find the smallest positive integer $n$ such that the polynomial $p^n(x) + q(x) = 0$ has at least one real root. Here, $p^n(x)$ denotes the polynomial $p(x)$ composed with itself $n$ times.

Answer: `1`

## 1718 | score=0.333 | number_theory

Find all positive integers \( n \) for which there exist positive integers \( a, b, c, d \) such that
\[ n^2 = a^2 + b^2 + c^2 + d^2 \]
and
\[ n \) is the product of four distinct prime numbers.\]

Answer: `210`

## 1719 | score=0.375 | other

在一个五边形ABCDE中，AB=BC=CD=DE=EA且∠ABC=∠BCD=∠CDE=∠DEA=∠EAB=108°。点P在BD上，使得∠APD=120°。求∠APB的度数。

Answer: `60^\circ`

## 1720 | score=0.667 | geometry

Find all prime numbers \( p \) such that there exists a positive integer \( n \) satisfying \( p^2 + 2^n + 1 \) is a perfect square.

Answer: `3`

## 1721 | score=0.556 | number_theory

Find all positive integers \( n \) such that the sum of the digits of \( n \) in base 10 is equal to the sum of the digits of \( n^2 \) in base 10. Additionally, prove that there exists no such \( n \) greater than 999 that satisfies the condition.

Answer: `1, 9, 10`

## 1722 | score=0.667 | number_theory

Consider a sequence of positive integers \(a_1, a_2, \ldots, a_n\) such that \(a_1 = 1\) and for all \(k \geq 2\), \(a_k\) is the smallest positive integer that is not a divisor of \(a_1 \cdot a_2 \cdots a_{k-1}\). Find the value of \(a_{100}\).

Answer: `100`

## 1723 | score=0.333 | number_theory

In a sequence of positive integers, each term after the first is equal to the sum of the cubes of the digits of the previous term. What is the smallest positive integer that is not a term in this sequence?

Answer: `16`

## 1724 | score=0.556 | number_theory

Find the smallest positive integer \( n \) such that \( 2^n + n \) is divisible by \( n \).

Answer: `1`

## 1725 | score=0.556 | geometry

In a 3D grid space defined by the coordinates (x, y, z) where 1 ≤ x, y, z ≤ 6, each point in the grid is connected to its neighboring points (those sharing a face). A particle starts at the origin (1,1,1) and moves towards the point (6,6,6) through a series of allowed moves: one unit up (U), one unit right (R), or one unit forward (F). The particle cannot revisit any grid point more than once. Let N be the number of distinct paths the particle can take to reach (6,6,6) without revisiting any grid point. Find the remainder when N is divided by 1000.

Answer: `756`

## 1726 | score=0.444 | number_theory

Let \( f(n) \) be the number of ordered pairs of positive integers \((a, b)\) such that \( a^b = n \) and \( b^a = n \). Find the sum of all positive integers \( n \) less than or equal to 1000 for which \( f(n) = 1 \).

Answer: `288`

## 1727 | score=0.556 | geometry

Let \( S \) be the set of all integers \( n \) such that \( 100 \leq n \leq 999 \) and the digits of \( n \) form an arithmetic sequence. Find the number of integers \( n \) in \( S \) that are also perfect squares.

Answer: `0`

## 1728 | score=0.778 | geometry

A sequence of positive integers \( a_1, a_2, a_3, \ldots \) is defined as follows: \( a_1 = 1 \), and for \( n \geq 2 \), \( a_n \) is the smallest positive integer such that the sum \( a_1 + a_2 + \ldots + a_n \) is a perfect square. Find the value of \( a_{2024} \).

Answer: `4047`

## 1729 | score=0.667 | number_theory

Let \( p \) be a prime number such that \( p \equiv 1 \pmod{4} \). Consider the set \( S \) of all positive integers \( n \) such that \( p \) divides \( n^2 + 1 \). Determine the number of elements in the set \( S \) for \( p \leq 100 \).

Answer: `22`

## 1730 | score=0.667 | number_theory

Find all real numbers \( x \) such that
\[
\left( \frac{x}{2} + \sqrt{\frac{x^2}{4} + 1} \right)^n + \left( \frac{x}{2} - \sqrt{\frac{x^2}{4} + 1} \right)^n = \left( \frac{x}{2} + \sqrt{\frac{x^2}{4} + 1} \right)^2 + \left( \frac{x}{2} - \sqrt{\frac{x^2}{4} + 1} \right)^2
\]
for some positive integer \( n \). Determine the smallest possible value of \( n \) for which there exists a solution.

Answer: `2`

## 1731 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the equation \( \frac{1}{x} + \frac{1}{y} = \frac{1}{n} \) has exactly 5 distinct solutions in positive integers \( (x, y) \).

Answer: `12`

## 1732 | score=0.444 | geometry

In the complex plane, consider the set of all complex numbers $z$ that satisfy the equation $|z^3 - 1| = 2|z - 1|$. Determine the number of such complex numbers $z$ that also lie on the circle centered at the origin with radius 2.

Answer: `6`

## 1733 | score=0.667 | number_theory

Find all pairs of positive integers \( (a, b) \) such that the equation
\[ a^3 + b^3 = (a + b)^2 \]
has exactly three distinct solutions in positive integers \( (a, b) \).

Answer: `(1, 2), (2, 1), (2, 2)`

## 1734 | score=0.444 | geometry

Let $ABC$ be a triangle with circumcircle $\Gamma$. A point $P$ inside $\triangle ABC$ is chosen such that the circumcircles of $\triangle ABP$ and $\triangle ACP$ intersect $\Gamma$ again at $D$ and $E$, respectively, and $BP = CP$. If $AD = 3$, $AE = 5$, and $BE = 2$, find the length of $CD$.

Answer: `4`

## 1735 | score=0.444 | geometry

Let \( f(x) \) be a polynomial with integer coefficients such that \( f(1) = 2 \), \( f(2) = 3 \), and \( f(3) = 5 \). If \( f(n) \) is prime for all \( n \in \mathbb{Z} \) except when \( n \) is a perfect square, find the smallest possible value of \( f(0) \).

Answer: `2`

## 1736 | score=0.667 | geometry

A circle with radius $r$ is inscribed in a square with side length $s$. The square is then inscribed in another circle with radius $R$. If the ratio of the area of the larger circle to the area of the smaller circle is given by $\frac{A_R}{A_r} = k$, express $k$ in terms of the ratio $\frac{s}{r}$.

Answer: `2`

## 1737 | score=0.444 | geometry

Let \(ABC\) be an acute triangle with circumcircle \(\Gamma\). Let \(D\), \(E\), and \(F\) be the feet of the altitudes from \(A\), \(B\), and \(C\) respectively. Let \(P\) be a point on the line \(EF\), and let \(Q\) be the isogonal conjugate of \(P\) with respect to triangle \(DEF\). The circumcircle of triangle \(BPQ\) intersects \(\Gamma\) again at \(X\). Prove that the circumcircle of triangle \(BXC\) passes through the midpoint of \(BC\).

Answer: `M`

## 1738 | score=0.444 | number_theory

A polynomial \(P(x)\) with integer coefficients satisfies \(P(0) = 2023\), \(P(1) = 2024\), and for some prime number \(p > 100\), \(P(p) = p^2\). Determine the maximum possible number of integer roots that \(P(x)\) can have.

Answer: `1`

## 1739 | score=0.444 | number_theory

Consider a sequence \( \{a_n\} \) defined by \( a_1 = 1 \) and for \( n \geq 2 \), \( a_n = a_{n-1} + \frac{1}{n(n+1)} \). Determine the smallest positive integer \( k \) such that \( a_k \) is an integer.

Answer: `1`

## 1740 | score=0.556 | number_theory

Consider a polynomial \( P(x) \) with integer coefficients such that \( P(1) = 3 \) and \( P(2) = 7 \). Furthermore, suppose that \( P(x) \) satisfies the recurrence relation \( P(x+1) - P(x) = 2x \) for all integers \( x \). Find the value of \( P(5) \).

Answer: `23`

## 1741 | score=0.667 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(1) = 2023 \). If there exist distinct positive integers \( a \) and \( b \) with \( a < b \) such that \( P(a) = P(b) \), find the smallest possible value of \( P(0) \).

Answer: `2023`

## 1742 | score=0.333 | number_theory

Determine the number of ordered triples of integers $(x, y, z)$ such that $1 \leq x, y, z \leq 10$, and there exists an integer $k$ for which $x^2 + y^2 + z^2 = k^2$ and $x + y + z = k$.

Answer: `0`

## 1743 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n - x + 1 \) is irreducible over the integers.\

Answer: `n \geq 2`

## 1744 | score=0.750 | number_theory

Let \( f: \mathbb{Z}^+ \to \mathbb{Z}^+ \) be a function satisfying the following conditions:
1. \( f(1) = 1 \)
2. For all positive integers \( n \), \( f(n+1) = f(n) + f(\gcd(n+1, f(n))) \), where \( \gcd \) denotes the greatest common divisor.
Find the smallest positive integer \( n \) such that \( f(n) \geq 2023 \).

Answer: `2023`

## 1745 | score=0.778 | geometry

Let \( \triangle ABC \) be a triangle with \( AB = 13 \), \( BC = 14 \), and \( CA = 15 \). Let \( D \) be the point where the incircle of \( \triangle ABC \) touches \( BC \). The circle with diameter \( AD \) intersects \( AB \) and \( AC \) at points \( E \) and \( F \) respectively. Determine the length of \( EF \).

Answer: `12`

## 1746 | score=0.333 | geometry

Consider a set \( S \) of \( n \) distinct positive integers, such that the sum of any two distinct elements in \( S \) is a perfect square. Determine the maximum possible value of \( n \) for which this is possible, and provide an example set \( S \) that achieves this maximum.

Answer: `2`

## 1747 | score=0.444 | number_theory

Find all integers \( n \geq 2 \) such that every pair of elements \( a, b \) in the set \( S = \{1, 2, \ldots, n\} \) satisfies the equation:
\[ a^3 + b^3 \equiv ab \pmod{n} \]

Answer: `2`

## 1748 | score=0.556 | number_theory

Find all pairs of integers \((a, b)\) such that the equation \(a^2 + ab + b^2 = 2024\) holds. Additionally, determine the number of distinct solutions \((a, b)\) where \(a\) and \(b\) are both prime numbers.

Answer: `0`

## 1749 | score=0.667 | geometry

Consider a regular octagon \(ABCDEFGH\) inscribed in a circle of radius 1. Let \(P\) be the point inside the octagon such that it is the intersection of the diagonals \(AC\), \(CE\), and \(EH\). Determine the distance from \(P\) to the center of the circle. Express your answer in simplest radical form.

Answer: `1`

## 1750 | score=0.444 | number_theory

In a finite set \( S \) of integers, define a *critical pair* as a pair of integers \( (a, b) \) such that \( a < b \) and the absolute difference \( |a - b| \) is the smallest among all distinct differences in \( S \). Given that the set \( S \) has 10 elements and the smallest critical pair has a difference of 4, find the maximum possible value of the largest element in \( S \).

Answer: `36`

## 1751 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers \( n \) such that the sum of the digits of \( n \) is equal to 10. Determine the smallest integer \( k \) for which there exist distinct elements \( a, b, c \in S \) satisfying the equation \( a + b = c \).

Answer: `3`

## 1752 | score=0.667 | number_theory

Let \( f: \mathbb{Z} \to \mathbb{Z} \) be a function such that for all integers \( a \) and \( b \),

\[ f(a^2 + b^2) = f(a)^2 + f(b)^2 \]

and \( f(1) = 2 \). Determine the value of \( f(2023) \).

Answer: `4046`

## 1753 | score=0.333 | geometry

In the Cartesian coordinate system, let \(A\) be the point \((0, 12)\), and \(B\) be a point on the positive x-axis. The line segment \(AB\) is rotated 90 degrees counterclockwise about point \(B\) to form segment \(BC\). If the area of triangle \(ABC\) is 96 square units, find the x-coordinate of point \(B\). Assume all points and the rotation are in the plane.

Answer: `4\sqrt{3}`

## 1754 | score=0.333 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(0) = 1 \) and \( P(1) = 2023 \). If \( P(x) \) has exactly three distinct real roots and all coefficients of \( P(x) \) are between \( -1000 \) and \( 1000 \) inclusive, find the maximum possible value of the product of the absolute values of the roots of \( P(x) \).

Answer: `1`

## 1755 | score=0.778 | algebra

Let \( P(x) \) be a polynomial of degree 6 with real coefficients, such that \( P(0) = 1 \), \( P(1) = 2 \), and \( P(-1) = 3 \). Suppose that \( P(x) \) has three distinct real roots, one of which is \( r \), and \( r \) is also a root of the polynomial \( Q(x) = x^3 + ax^2 + bx + c \), where \( a, b, \) and \( c \) are real numbers. Given that \( Q(r) = 0 \) and \( Q'(r) \neq 0 \), find the sum of all possible values of \( r \).

Answer: `0`

## 1756 | score=0.778 | number_theory

Let \( p \) be an odd prime number. Define the sequence \( \{a_n\} \) by \( a_1 = 2 \) and \( a_{n+1} \equiv 3a_n + 1 \pmod{p} \). Find the smallest positive integer \( k \) such that \( a_k \equiv 0 \pmod{p} \).

Answer: `p-1`

## 1757 | score=0.333 | geometry

Let \( \triangle ABC \) be a triangle with \( AB = 13 \), \( BC = 14 \), and \( CA = 15 \). Let \( D \) be the point on \( BC \) such that \( AD \) is the angle bisector of \( \angle BAC \). Let \( E \) be the point on \( AD \) such that \( BE \) is perpendicular to \( AD \). Find the length of \( BE \).

Answer: `12`

## 1758 | score=0.333 | number_theory

Find all integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) can be factored into two non-constant polynomials with integer coefficients.

Answer: `3`

## 1759 | score=0.778 | algebra

Let \( f(x) = x^3 + ax^2 + bx + c \) be a cubic polynomial with real coefficients, and suppose \( f(x) \) has three distinct real roots \( r_1, r_2, r_3 \) such that \( r_1 + r_2 + r_3 = 0 \) and \( r_1 r_2 r_3 = -8 \). Given that \( f(1) = 4 \), find the value of \( f(2) \).

Answer: `6`

## 1760 | score=0.444 | number_theory

Consider the sequence of numbers defined recursively by \(a_1 = 2\) and \(a_{n+1} = a_n^2 - a_n + 1\) for all \(n \geq 1\). Determine the smallest positive integer \(k\) such that \(a_k\) is divisible by \(3^{10}\).

Answer: `2`

## 1761 | score=0.667 | number_theory

Let \( S \) be the set of all positive integers less than 1000 that are multiples of 5 or 7 but not both. Determine the number of elements in \( S \).

Answer: `285`

## 1762 | score=0.333 | number_theory

In a magical forest, there exists a tree with \( n \) nodes, where each node is either a fairy or a dragon. A fairy can cast a spell on any adjacent node, turning it into a dragon if it is a fairy, or turning it into a fairy if it is a dragon. A dragon can only cast a spell on itself, turning it into a fairy. The spell can only be cast once per node. Initially, all nodes are fairies. If the tree is represented as a directed acyclic graph (DAG) with exactly one cycle, determine the minimum number of spells required to ensure that no cycle remains in the graph.

Assume the graph is described by an adjacency list. For example, given the following graph structure:

\[ \text{Adjacency List:} \]
\[ [0, 1, 2] \]
\[ [1, 3] \]
\[ [2, 4] \]
\[ [3, 2] \]
\[ [4, 1] \]

Determine the minimum number of spells needed to break the cycle and ensure no cycles remain in the graph.

Input:
- An integer \( n \) representing the number of nodes.
- An adjacency list of size \( n \).

Output:
- The minimum number of spells required to break all cycles in the graph.

Example Input:
```
5
[0, 1, 2]
[1, 3]
[2, 4]
[3, 2]
[4, 1]
```

Example Output:
```
2
```

Answer: `2`

## 1763 | score=0.333 | number_theory

Let $f: \mathbb{N} \rightarrow \mathbb{N}$ be a function such that $f(1) = 1$ and for all $n \geq 2$, $f(n) = n - f(f(n - 1))$. Define a sequence $\{a_k\}_{k=1}^{\infty}$ by $a_1 = f(10)$ and for all $k \geq 2$, $a_k = a_{k-1} + f(a_{k-1})$. Find the smallest $k$ for which $a_k$ is divisible by $2023$.

Answer: `2023`

## 1764 | score=0.444 | number_theory

Find all positive integers \( n \) such that \( n^2 - 1 \) divides \( n^n + 1 \).

Answer: `3`

## 1765 | score=0.444 | geometry

Let \( S \) be the set of all positive integers that can be represented as the sum of two distinct positive integers whose product is a perfect square. Define \( T \) as the set of all positive integers that can be represented as the sum of two distinct positive integers whose product is a perfect cube. Prove that the intersection \( S \cap T \) is a finite set and determine its size.

Answer: `1`

## 1766 | score=0.778 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a continuous function such that for all real numbers \( x \) and \( y \),
\[ f(x + y) = f(x) \cdot f(y) \]
and for \( x \neq 0 \), \( f(x) \neq 1 \). Prove that \( f \) is an exponential function of the form \( f(x) = a^x \) for some positive constant \( a \).

Answer: `f(x) = a^x`

## 1767 | score=0.667 | number_theory

Given a sequence of integers \(a_1, a_2, \ldots, a_n\) with \(n \geq 2\), define the function \(f(k)\) for \(1 \leq k \leq n\) as the number of ways to choose \(k\) distinct integers from this sequence such that the sum of these \(k\) integers is divisible by \(k\). Determine the minimum possible value of \(f(3)\) given that the sum of all elements in the sequence is 0 and no element is repeated.

Answer: `1`

## 1768 | score=0.778 | geometry

In the complex plane, let \( A = 1 + 2i \), \( B = 3 - i \), and \( C = -2 + 4i \). Find the number of distinct points \( P \) such that \( P \) is the centroid of triangle \( ABC \) when rotated about the origin by any angle \( \theta \) and the resulting triangle \( A'BC \) has an area that is exactly twice the area of triangle \( ABC \). Express your answer as a positive integer.

Answer: `0`

## 1769 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that there exist real numbers \( a_1, a_2, \ldots, a_n \) satisfying the following conditions:
1. \( a_1 + a_2 + \cdots + a_n = 0 \)
2. For any \( 1 \leq i \leq n \), \( a_i^3 = a_i \)
3. The product \( a_1 a_2 \cdots a_n \) is a non-zero integer.

Answer: `2`

## 1770 | score=0.333 | number_theory

Let \( f: \mathbb{Z} \rightarrow \mathbb{Z} \) be a function defined such that for all integers \( a, b, c \) satisfying \( a + b + c = 2024 \), the following holds:
\[ f(a) + f(b) + f(c) = abc + 170 \]

Determine all possible values of \( f(2024) \).

Answer: `170`

## 1771 | score=0.333 | geometry

In the coordinate plane, consider a regular hexagon with vertices at lattice points. Let \( A \) and \( B \) be two distinct vertices of the hexagon such that the line segment \( AB \) is parallel to one of the axes. A point \( P \) is chosen randomly inside the hexagon. Find the probability that the distance from \( P \) to the line segment \( AB \) is less than half the length of \( AB \).

Answer: `\frac{1}{2}`

## 1772 | score=0.778 | geometry

In the coordinate plane, consider a circle centered at the origin with radius 1. Let \( P \) be a point inside the circle such that the distance from \( P \) to the origin is \( \sqrt{\frac{3}{4}} \). A line passing through \( P \) intersects the circle at two points \( A \) and \( B \). If the angle \( \angle APB \) is \( 120^\circ \), find the length of the chord \( AB \).

Answer: `\sqrt{3}`

## 1773 | score=0.556 | geometry

In the coordinate plane, a line passing through the origin intersects the curve defined by $y = x^3 - 3x + 2$ at exactly two distinct points. Find the sum of all possible slopes of such lines.

Answer: `0`

## 1774 | score=0.556 | number_theory

Find all positive integers \( n \) such that the number \( 12345n \) is divisible by 3 and the number \( 123456789n \) is divisible by 9. Additionally, determine the smallest such \( n \) for which both conditions hold.

Answer: `9`

## 1775 | score=0.444 | number_theory

Find all positive integers \( n \) such that \( n \) divides \( 2^n + 1 \).

Answer: `1, 3`

## 1776 | score=0.444 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(0) = 1 \) and \( P(1) = 2023 \). Suppose there exists a positive integer \( n \) for which \( P(n) = 2024 \) and \( P(n+1) = 2025 \). Find the smallest possible value of \( n \).

Answer: `2`

## 1777 | score=0.444 | geometry

Find the smallest positive integer \( n \) such that the equation
\[ x^2 - nx + 2024 = 0 \]
has integer solutions and the product of these solutions is a perfect square.

Answer: `90`

## 1778 | score=0.667 | geometry

A point \( P \) is selected at random inside a square with side length 10. From point \( P \), a line segment is drawn perpendicular to each side of the square, forming four right triangles. If the sum of the lengths of these line segments is 20, find the expected value of the area of the quadrilateral formed by the midpoints of these four line segments.

Answer: `25`

## 1779 | score=0.556 | algebra

Find all real numbers \( x \) such that the equation
\[ x^3 - 3x^2 + 2x - 1 + \frac{1}{x-1} = 0 \]
holds. Prove that any solution must satisfy \( x \in [1, 3] \) and that there is exactly one solution in this interval.

Answer: `2`

## 1780 | score=0.444 | number_theory

What is the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) has a root modulo \( m \), where \( m \) is a positive integer greater than 1 and not a prime number?

Answer: `1`

## 1781 | score=0.333 | number_theory

What is the smallest positive integer \( n \) such that \( 2^n - 1 \) is divisible by 7 and the product of all positive integers less than \( n \) that are relatively prime to \( n \) is also divisible by 7?

Answer: `7`

## 1782 | score=0.778 | geometry

Consider a regular octahedron \(O\) with vertices \(A, B, C, D, E, F\) such that \(ABCD\) forms the lower base and \(ABEF\) the upper base. Let \(P\) be a point inside \(O\) such that the sum of the distances from \(P\) to each vertex is minimized. If the side length of the octahedron is \(s\), find the coordinates of \(P\) in the Cartesian coordinate system where \(A\) is at \((0, 0, -s/\sqrt{2})\), \(B\) at \((s, 0, -s/\sqrt{2})\), \(C\) at \((s/2, s\sqrt{3}/2, 0)\), \(D\) at \((-s/2, s\sqrt{3}/2, 0)\), \(E\) at \((0, 0, s/\sqrt{2})\), and \(F\) at \((-s, 0, s/\sqrt{2})\).

Answer: `(0, 0, 0)`

## 1783 | score=0.333 | number_theory

Let \( p \) be a prime number such that \( p \equiv 1 \pmod{4} \). Prove that there exist positive integers \( a \) and \( b \) such that \( a^2 + b^2 = p \).

Answer: `a^2 + b^2 = p`

## 1784 | score=0.333 | number_theory

Let $S$ be a set of positive integers such that for any $a, b \in S$ with $a < b$, there exists a unique $c \in S$ such that $a + c = b$. Furthermore, let $S$ contain exactly 2023 elements. Find the sum of the smallest and largest elements of $S$.

Answer: `2024`

## 1785 | score=0.444 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + 2017x^{n-1} + 2016x^{n-2} + \dots + 2x^2 + x + 1 \) has all its roots as integers.

Answer: `1`

## 1786 | score=0.333 | number_theory

Let f(x) be a polynomial with integer coefficients such that f(0) = 0 and f(1) = 1. If for all positive integers n, the value of f(n) is always an odd number, determine the smallest possible degree of f(x).

Answer: `1`

## 1787 | score=0.556 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a continuous function such that for all real numbers \( x \) and \( y \), the inequality \( |f(x+y) - f(x) - f(y)| \leq |y| \) holds. Show that there exists a real number \( a \) such that \( f(x) = ax \) for all \( x \in \mathbb{R} \).

Answer: `f(x) = ax`

## 1788 | score=0.444 | geometry

Let \( ABCD \) be a convex quadrilateral with \( AB = 8 \), \( BC = 15 \), \( CD = 20 \), and \( DA = 17 \). Diagonals \( AC \) and \( BD \) intersect at point \( E \). Given that the area of \( \triangle ABE \) is \( 60 \), find the area of \( \triangle CDE \).

Answer: `60`

## 1789 | score=0.333 | combinatorics

Consider a 4x4 chessboard. In how many distinct ways can you place 4 indistinguishable rooks on the board such that no two rooks attack each other? Note that two placements are considered the same if one can be obtained by rotating or reflecting the other.

Answer: `5`

## 1790 | score=0.667 | number_theory

In a sequence of positive integers, each term after the first is the sum of the two preceding terms, starting with $1$ and $2$. If the $15^{\text{th}}$ term is a multiple of $11$, how many terms between the $1^{st}$ and the $15^{th}$ (inclusive) are also multiples of $11$?

Answer: `1`

## 1791 | score=0.556 | geometry

Let \(ABC\) be an acute-angled triangle with \(AB < AC\). Let \(D\) be the foot of the perpendicular from \(A\) to \(BC\). Let \(E\) and \(F\) be points on \(AB\) and \(AC\) respectively, such that \(DE\) and \(DF\) are the angle bisectors of \(\angle ADC\) and \(\angle ADB\), respectively. Let \(G\) be the intersection of \(DE\) and \(DF\). If \(BG = CG = DG\), find the measure of \(\angle BAC\) in degrees.

Answer: `60`

## 1792 | score=0.556 | geometry

In the enchanted land of Geometria, a magical circle with radius 10 units is inscribed inside a square field. A wizard casts a spell, transforming the square into a regular hexagon while maintaining the circle's center within the new shape. If the area of the hexagon is greater than the original square by exactly 250 square units, what is the side length of the original square?

Answer: `20`

## 1793 | score=0.444 | algebra

Let $f(x) = x^4 - 20x^3 + 109x^2 - 140x + 50$. Find the number of distinct real solutions to the equation $f(f(x)) = 0$.

Answer: `4`

## 1794 | score=0.667 | geometry

Find all positive integers \( n \) such that the number of distinct prime factors of \( n \) is exactly 3 and \( n \) is a perfect square.

Answer: `900`

## 1795 | score=0.333 | number_theory

Find the smallest positive integer $n$ such that there exists a strictly increasing sequence of $n$ positive integers $a_1, a_2, ..., a_n$ satisfying:

1. $a_1 + a_2 + ... + a_n = 2023$, and
2. For all $1 \leq i < j \leq n$, $a_j$ divides $a_i + a_j$.

Answer: `3`

## 1796 | score=0.778 | number_theory

Find all pairs of positive integers $(m,n)$ such that $m^n + 1 = 2n^m$.

Answer: `(1, 1)`

## 1797 | score=0.444 | number_theory

Let $p$ be a prime number and $n$ a positive integer such that $p \mid n$. Consider the sequence $\{a_k\}_{k \geq 1}$ defined by $a_1 = n$, and for $k \geq 2$, $a_k$ is the smallest positive integer greater than $a_{k-1}$ that satisfies the following condition: if $p^j \mid n$ and $p^j \mid k$, then $p^{j-1} \mid a_k$. Determine the smallest $n$ for which the sequence $\{a_k\}$ becomes periodic with a period of at most $p^2$.

Answer: `p^2`

## 1798 | score=0.667 | geometry

In the complex plane, let \( z \) be a complex number satisfying the equation
\[ z^3 + \overline{z}^3 = 2 \]
where \( \overline{z} \) is the complex conjugate of \( z \). Find the sum of all possible values of \( z^2 + \overline{z}^2 \).

Answer: `2`

## 1799 | score=0.444 | geometry

Let $f(x)$ be a polynomial with integer coefficients such that $f(0) = f(1) = 1$ and $f(n)$ is a perfect square for all non-negative integers $n$. Find the smallest possible degree of $f(x)$.

Answer: `2`

## 1800 | score=0.444 | geometry

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) has exactly three distinct real roots, and determine the sum of the squares of these roots.

Answer: `-1`

## 1801 | score=0.333 | number_theory

Given a sequence of distinct positive integers \(a_1, a_2, ..., a_{100}\) such that \(a_{i} < a_{i+1}\) for all \(1 \leq i \leq 99\), and the sum of any 50 consecutive terms in this sequence is divisible by 50, find the smallest possible value of \(a_{100}\).

Answer: `100`

## 1802 | score=0.778 | algebra

Let \( P(x) \) be a polynomial of degree 3 such that \( P(1) = 1, P(2) = 2, P(3) = 3, \) and \( P(4) = 4. \) Determine the value of \( P(5). \)

Answer: `5`

## 1803 | score=0.667 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + ax + b \) (where \( a \) and \( b \) are integers) has exactly one real root, and this root is rational.

Answer: `1`

## 1804 | score=0.556 | algebra

Let \( P(x) \) be a polynomial of degree \( n \) with real coefficients such that \( P(x) = x \) has exactly one real root, \( r \). Suppose further that \( P(x) \) has the property that for any real number \( y \) not equal to \( r \), \( P(P(y)) = y \). Determine all possible values of \( n \).

Answer: `1`

## 1805 | score=0.444 | number_theory

Find all positive integers \( n \) such that the equation
\[ x^2 - nxy + y^2 = 1 \]
has exactly three distinct solutions in positive integers \((x, y)\).

Answer: `3`

## 1806 | score=0.778 | geometry

In a magical land, there exists a sequence of numbers that follows a unique pattern. The sequence starts with 1, and each subsequent number is the sum of the squares of the digits of the previous number. For example, the first few terms are 1, 1, 1, 1, 1, 1, ... until the first term that does not repeat, which is 16 (since 1^2 = 1 and 6^2 = 36, and 1 + 36 = 37). The sequence continues as follows: 1, 1, 1, 1, 1, 1, 16, 37, 58, 89, 145, 42, 20, 4, 16, ... Notice that the sequence enters a cycle after a certain point. Determine the length of the cycle that the sequence enters after it first reaches a number greater than 9.

Answer: `8`

## 1807 | score=0.556 | number_theory

Find all positive integers \( n \) such that the equation
\[ x^2 + y^2 + z^2 = nxyz \]
has a solution in positive integers \( x, y, z \).

Answer: `3`

## 1808 | score=0.333 | number_theory

A sequence of numbers \( a_1, a_2, a_3, \ldots \) is defined as follows: \( a_1 = 2 \), and for \( n \geq 2 \), \( a_n \) is the smallest positive integer such that \( a_n \) is not a factor of \( a_{n-1} \). Find the sum of the first 2023 terms of this sequence.

Answer: `5057`

## 1809 | score=0.556 | number_theory

Find all positive integers \( n \) such that \( n \) divides \( 3^{n} - 2^{n} \), and \( n \) is not a power of 3.

Answer: `1`

## 1810 | score=0.778 | number_theory

A sequence of numbers \(\{a_n\}\) is defined as follows: \(a_1 = 1\), and for \(n \geq 2\), \(a_n = a_{n-1}^2 - 2\). Let \(S\) be the sum of the first 2023 terms of this sequence. Find the remainder when \(S\) is divided by 1000.

Answer: `979`

## 1811 | score=0.778 | geometry

There is a circle with radius \( r \) and a point \( P \) outside the circle such that the line segment from \( P \) to the center of the circle is perpendicular to the tangent at the point of tangency. If \( PQ \) is the length of the tangent from \( P \) to the point of tangency and \( QR \) is the distance from the point of tangency to the point \( R \) where a second tangent from \( P \) intersects the circle again, find the value of \( \frac{PQ^2}{QR^2} \).

Answer: `1`

## 1812 | score=0.667 | geometry

In triangle \( ABC \), point \( D \) is on side \( BC \) such that \( BD : DC = 2 : 1 \). Point \( E \) is on side \( AC \) such that \( AE : EC = 1 : 2 \). The lines \( AD \) and \( BE \) intersect at point \( F \). If the area of triangle \( ABC \) is 180 square units, find the area of triangle \( BDF \).

Answer: `40`

## 1813 | score=0.556 | number_theory

Let \( p \) be a prime number greater than 3. Consider the sequence of integers defined by \( a_n = n^2 + pn + 1 \). Determine the smallest positive integer \( k \) such that for all \( n \geq k \), the sequence \( a_n \) contains at least one term that is divisible by \( p \).

Answer: `1`

## 1814 | score=0.667 | geometry

Let \( ABC \) be an equilateral triangle with side length 12. Points \( D, E, \) and \( F \) lie on sides \( BC, CA, \) and \( AB \), respectively, such that \( BD = CE = AF = x \). Let \( G \) be the intersection of \( AD, BE, \) and \( CF \). Given that \( AG = BG = CG \), find the value of \( x \).

Answer: `4`

## 1815 | score=0.778 | number_theory

Find all integers \( n \geq 2 \) such that the equation
\[ x_1^2 + x_2^2 + \cdots + x_n^2 = x_{n+1}^2 + x_{n+2}^2 \]
has integer solutions \( x_1, x_2, \ldots, x_{n+2} \) where none of \( x_1, x_2, \ldots, x_{n+2} \) is divisible by \( n \).

Answer: `2`

## 1816 | score=0.556 | number_theory

Let $S$ be the set of all positive integers $n$ for which there exist positive integers $a$, $b$, and $c$ such that the polynomial $P(x) = x^3 + ax^2 + bx + c$ has integer roots and $P(1) = n$. If $S$ contains exactly 50 elements, find the sum of these 50 elements.

Answer: `1275`

## 1817 | score=0.667 | geometry

In a finite field \( F \) with \( q \) elements, where \( q = p^n \) for some prime \( p \) and \( n \geq 1 \), consider a polynomial \( P(x) = a_0 + a_1 x + a_2 x^2 + \cdots + a_d x^d \) with coefficients \( a_i \in F \). Suppose that for every \( x \in F \), the polynomial \( P(x) \) is a perfect square in \( F \). Determine the maximum possible value of \( d \) and provide an example of such a polynomial for this maximum value.

Answer: `q-1`

## 1818 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that \( n \) is divisible by 20, and the sum of the digits of \( n \) is also a divisor of 20.

Answer: `20`

## 1819 | score=0.444 | combinatorics

In a town, there are four houses in a row. Each house is painted a different color: red, blue, green, or yellow. The blue house is immediately to the left of the green house. The yellow house is not next to the red house. The green house is not at the far end of the row. How many possible arrangements of the houses are there, and what are they?

Answer: `4`

## 1820 | score=0.556 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a continuous function such that \( f(x) + f(y) = f(x+y) \) for all \( x, y \in \mathbb{R} \). Suppose also that \( f \) is differentiable at \( x = 0 \) with \( f'(0) = k \) for some constant \( k \). Prove that \( f \) is differentiable everywhere and find \( f'(x) \) in terms of \( k \).

Answer: `k`

## 1821 | score=0.333 | other

在一个无限长的数列 \( a_1, a_2, a_3, \ldots \) 中，每个 \( a_i \) 是 \( 1, 2, 3, \ldots, 2023 \) 中的一个正整数，且对任意的 \( i \neq j \)，\( a_i \neq a_j \)。对于每一个正整数 \( k \) (1 ≤ \( k \) ≤ 2023)，定义 \( S_k \) 为数列中所有出现次数恰好为 \( k \) 的数的集合。给定条件 \( S_k \) 的非空子集 \( T_k \)，求所有可能的 \( T_k \) 的集合的大小。

Answer: `2^{2023} - 1`

## 1822 | score=0.778 | algebra

Let $f: \mathbb{R} \to \mathbb{R}$ be a differentiable function such that for all $x, y \in \mathbb{R}$, we have $f'(x+y) = f'(x)f'(y)$. If $f'(0) = 1$ and $f(0) = 0$, find the value of $f\left(\ln(2)\right)$.

Answer: `1`

## 1823 | score=0.444 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) can be expressed as the product of two non-constant polynomials with integer coefficients.

Answer: `3`

## 1824 | score=0.333 | combinatorics

Find the maximum number of subsets that can be included in a collection of subsets of a set with 10 distinct objects such that no subset is a proper subset of another. That is, if $A$ and $B$ are subsets in the collection, then $A \neq B$ and it's not the case that $A$ is a proper subset of $B$ or $B$ is a proper subset of $A$. Let $f(n)$ denote the maximum number of subsets that can be included in such a collection. Find $f(10)$.

Answer: `11`

## 1825 | score=0.556 | number_theory

Let $f(x)$ be a function defined on the positive integers such that $f(1) = 1$ and for all positive integers $n$, \[f(n) = n - f(f(n-1)).\] Find the value of $f(2023)$.

Answer: `1012`

## 1826 | score=0.667 | geometry

In a magical forest, there are 100 trees arranged in a straight line. Each tree is either a pine or an oak. A wizard casts a spell that doubles the number of pines and triples the number of oaks every day. If initially there were 30 pines and 70 oaks, how many days will it take until the number of oaks is more than twice the number of pines?

Answer: `1`

## 1827 | score=0.556 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + nx^{n-1} + (n-1)x^{n-2} + \cdots + 2x + 1 \) can be factored into the product of two non-constant polynomials with integer coefficients.

Answer: `2`

## 1828 | score=0.333 | geometry

In the coordinate plane, let \(P\) be the point \((3,4)\) and \(Q\) the point \((7,12)\). Let \(R\) be a point on the circle centered at the origin with radius 5. Determine the maximum value of \(|PR^2 - QR^2|\).

Answer: `168 + 40\sqrt{5}`

## 1829 | score=0.444 | combinatorics

Consider the set {1, 2, 3, ..., 20}. How many ways can we select 6 numbers from this set such that any two selected numbers differ by at least 3?

Answer: `5005`

## 1830 | score=0.778 | number_theory

Consider the sequence of numbers \(a_n\) defined as follows: \(a_1 = 1\), and for \(n \geq 2\), \(a_n\) is the smallest positive integer greater than \(a_{n-1}\) that is not relatively prime to \(a_{n-1}\). For instance, \(a_2 = 2\), \(a_3 = 4\), and so on. Find the 2023rd term of this sequence, \(a_{2023}\).

Answer: `4046`

## 1831 | score=0.444 | number_theory

Let \( P(x) \) be a polynomial of degree 5 with integer coefficients such that \( P(1) = 2024 \), \( P(2) = 4048 \), and \( P(3) = 6072 \). It is also known that \( P(x) \) has exactly one real root in the interval \( (1, 3) \). Find the number of distinct integer roots of \( P(x) \).

Answer: `3`

## 1832 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) can be factored into the product of two non-constant polynomials with integer coefficients.

Answer: `3`

## 1833 | score=0.444 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n - x^{n-1} - x^{n-2} - \ldots - x - 1 \) has at least one real root greater than 2.

Answer: `3`

## 1834 | score=0.444 | other

在一个五边形网格中，每个小五边形的面积为1平方单位。已知AB = BC = CD = DE = EF = 1单位，且∠ABC = ∠CDE = ∠DEF = 90°。求整个五边形区域的面积。

Answer: `2`

## 1835 | score=0.778 | number_theory

What is the largest integer \( n \) such that \( \frac{1}{n} \) can be expressed as a terminating decimal in base 3 with exactly 4 digits after the radix point, and \( n \) is also a prime number?

Answer: `3`

## 1836 | score=0.778 | geometry

In the convex quadrilateral \(ABCD\), the diagonals \(AC\) and \(BD\) intersect at point \(E\). Let \(M\) and \(N\) be the midpoints of sides \(AD\) and \(BC\) respectively. If the area of triangle \(AEN\) is 20 square units and the area of triangle \(BEM\) is 30 square units, find the area of quadrilateral \(ABCD\).

Answer: `100`

## 1837 | score=0.556 | geometry

A set S consists of 10 distinct integers. We define a pair of distinct integers from S as good if their product is a perfect square. What is the maximum number of good pairs that can exist in S?

Answer: `45`

## 1838 | score=0.444 | combinatorics

In the complex plane, consider the set of points defined by the equation \( z^4 + 1 = 0 \). Let \( S \) be the set of all points \( z \) that satisfy this equation. If \( P \) is a point chosen uniformly at random from \( S \), what is the probability that \( \left| \frac{1}{2}P + \frac{\sqrt{3}}{2}P^3 \right| \) is a real number? Express your answer as a fraction in lowest terms.

Answer: `0`

## 1839 | score=0.667 | geometry

In the complex plane, consider a circle centered at the origin with radius 1. A point P is chosen randomly on this circle. Let A and B be two fixed points on the circle such that the arc AB subtends a right angle at the center. What is the probability that the line segment joining P and A intersects the line segment AB inside the circle? Express your answer as a common fraction.

Answer: `\frac{1}{2}`

## 1840 | score=0.556 | number_theory

Let \( f(n) \) be the function defined for all positive integers \( n \) as follows: if \( n \) is even, \( f(n) = \frac{n}{2} \); if \( n \) is odd, \( f(n) = 3n + 1 \). Consider the sequence generated by repeatedly applying \( f \) to the number 1024, starting with 1024. Let \( k \) be the number of terms in this sequence up to and including the first occurrence of the number 1. Find the value of \( k \).

Answer: `11`

## 1841 | score=0.333 | number_theory

A positive integer $n$ is chosen at random from the set $\{1, 2, 3, \ldots, 1000\}$. What is the probability that the sum of the digits of $n$ equals the product of the digits of $n$? Express your answer as a reduced fraction.

Answer: `\frac{1}{100}`

## 1842 | score=0.556 | other

In a country, there are 100 cities connected by roads. Each city is connected to exactly 10 other cities, and there are no direct road connections between any two cities more than once. A traveler decides to visit as many cities as possible such that no two visited cities are directly connected by a road. What is the maximum number of cities the traveler can visit?

Answer: `10`

## 1843 | score=0.333 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) can be expressed as the product of two non-constant polynomials with integer coefficients.

Answer: `3`

## 1844 | score=0.667 | geometry

In the coordinate plane, let \( P \) be the point \((2020, 2021)\) and \( Q \) the point \((2021, 2022)\). A finite sequence of points in the plane \( Q_1, Q_2, \ldots, Q_n \) is called a *harmonious path* from \( P \) to \( Q \) if:
1. \( Q_1 = P \) and \( Q_n = Q \),
2. For \( i = 1, 2, \ldots, n-1 \), the midpoint of \( Q_i \) and \( Q_{i+1} \) lies on the parabola \( y = x^2 \), and
3. The points \( Q_1, Q_2, \ldots, Q_n \) are all distinct.
Determine the minimum number of points that such a harmonious path must contain.

Answer: `3`

## 1845 | score=0.778 | algebra

Let \( f(x) \) be a polynomial of degree 3 such that the coefficients of \( x^3 \) and \( x \) are both 1. Given that \( f(x) \) satisfies \( f(x) + f(-x) = 0 \) for all real \( x \), and that \( f(2) = 6 \), find the value of \( f(-1) \).

Answer: `-2`

## 1846 | score=0.667 | algebra

In the geometric sequence $\{a_n\}$ with common ratio $q$, let $S_n$ be the sum of the first $n$ terms. If $(a_1, \frac{3}{4}a_3, 2a_2)$ forms an arithmetic sequence, find the value of $q$.

Answer: `\frac{2 + \sqrt{10}}{3}`

## 1847 | score=0.333 | combinatorics

In the complex plane, let \(A\), \(B\), and \(C\) be the vertices of a regular hexagon with side length \(1\). Let \(D\), \(E\), and \(F\) be the midpoints of \(BC\), \(CA\), and \(AB\) respectively. A point \(P\) is chosen uniformly at random inside the hexagon \(ABCDEF\). Find the probability that the distance from \(P\) to \(A\) is less than the distance from \(P\) to both \(D\) and \(E\).

Answer: `\frac{1}{2}`

## 1848 | score=0.444 | geometry

In the Cartesian plane, let P be the set of points (x, y) that satisfy the equation \[x^2 + y^2 = 1.\] For any non-negative integer n, let A_n be the set of points in P that have at least one coordinate that is rational and whose distance to the origin is 1/n. Determine the number of points in the set A_n \cup A_{n+1} \cup A_{n+2} \cup A_{n+3}, where A_n, A_{n+1}, A_{n+2}, and A_{n+3} are the sets defined as above for n, n+1, n+2, and n+3 respectively.

Answer: `\infty`

## 1849 | score=0.333 | number_theory

Find the smallest positive integer $n$ such that there exist integers $a$, $b$, and $c$ with $a^2 + b^2 + c^2 = n$ and $ab + bc + ca = 10$.

Answer: `5`

## 1850 | score=0.333 | geometry

Let \( ABC \) be a triangle with \( AB = 13 \), \( BC = 14 \), and \( CA = 15 \). Points \( D \), \( E \), and \( F \) lie on segments \( BC \), \( CA \), and \( AB \) respectively, such that \( AD \), \( BE \), and \( CF \) are concurrent. If the lengths of \( BD \), \( CE \), and \( AF \) are in arithmetic progression with a common difference of \( d \), find the length of \( d \).

Answer: `3`

## 1851 | score=0.556 | geometry

In the Cartesian plane, a sequence of points \( P_1, P_2, P_3, \ldots \) is defined as follows: \( P_1 \) is the point \((1,1)\), and for each \( n \geq 1 \), \( P_{n+1} \) is the reflection of \( P_n \) over the line \( y = x \), followed by a rotation of \( 90^\circ \) counterclockwise about the origin. Find the coordinates of \( P_{2024} \) in simplest form.

Answer: `(-1, 1)`

## 1852 | score=0.333 | number_theory

Consider a sequence of integers \(a_1, a_2, a_3, \ldots, a_n\) where each term \(a_i\) is defined by the recursive relation:
\[a_{i+1} = a_i^2 - a_i + 1\]
for \(i = 1, 2, \ldots, n-1\). Given that \(a_1 = 2\), determine the smallest positive integer \(n\) such that \(a_n\) is a multiple of 1000.

Answer: `10`

## 1853 | score=0.778 | combinatorics

In a magical land, there are 6 unique colored coins: red, blue, green, yellow, black, and white. A wizard needs to create a spell using exactly 3 coins, but the spell can only be effective if the coins follow a specific pattern: no two adjacent coins in the selection can be the same color, and the sequence must start with a red coin. How many different effective spells can the wizard create?

Answer: `20`

## 1854 | score=0.667 | geometry

Let \( A \), \( B \), and \( C \) be the vertices of a triangle in the complex plane, with \( A = 0 \), \( B = 1 \), and \( C \) as an arbitrary complex number. Define \( D \) as the midpoint of \( BC \), and let \( E \) be the foot of the perpendicular from \( A \) to \( BC \). If the product of the distances from \( D \) to \( E \) and from \( E \) to \( A \) is equal to \( \frac{1}{2} \), find all possible values of \( |C| \).

Answer: `1`

## 1855 | score=0.444 | geometry

In a triangular array of numbers, the top number is 1. Each number below it is the sum of the two numbers directly above it. The base of the triangle consists of 2023 numbers, all initially set to 1. After constructing the entire triangle, you are allowed to swap any two numbers in the base row exactly once. What is the maximum possible sum of the numbers in the 2024th row, which is the row at the bottom of the triangle?

Answer: `2^{2023}`

## 1856 | score=0.556 | algebra

In the complex plane, let \( z \) be a complex number such that \( z^3 = 1 \) and \( z \neq 1 \). Define \( w = z + \frac{1}{z} \). If \( P(x) \) is a polynomial of degree 5 with real coefficients such that \( P(z) = 0 \) for all possible values of \( z \) satisfying the given conditions, find the number of distinct real roots of the polynomial \( P(x) - x \).

Answer: `1`

## 1857 | score=0.667 | algebra

In the realm of functional equations, consider a function \( f: \mathbb{R} \to \mathbb{R} \) satisfying the equation \( f(x + y) + f(x - y) = 2f(x) + 2f(y) \) for all real numbers \( x \) and \( y \). Prove that \( f(x) = ax^2 + bx + c \) for some constants \( a, b, c \in \mathbb{R} \).

Answer: `f(x) = ax^2 + bx + c`

## 1858 | score=0.667 | geometry

Find the smallest positive integer \( n \) such that the sum of the first \( n \) positive integers is a perfect square and the sum of the squares of the first \( n \) positive integers is also a perfect square.

Answer: `1`

## 1859 | score=0.444 | geometry

In the complex plane, let \( P \) be a point such that the distance from \( P \) to the origin is 10. Let \( Q \) be another point in the complex plane such that \( |Q - P| = 12 \) and \( |Q| = 14 \). Find the area of the triangle formed by the points \( P \), \( Q \), and the origin.

Answer: `24\sqrt{6}`

## 1860 | score=0.444 | geometry

Let \(ABC\) be an acute triangle with circumcenter \(O\), and let \(D\), \(E\), and \(F\) be the feet of the altitudes from \(A\), \(B\), and \(C\) respectively. The circle with diameter \(BC\) intersects line \(EF\) at points \(P\) and \(Q\). Given that the area of triangle \(ABC\) is \(60\) square units and \(BC = 10\) units, find the length of \(PQ\).

Answer: `10`

## 1861 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^n + x^{n-1} + \cdots + x + 1 \) can be factored into the product of two non-constant polynomials with integer coefficients.

Answer: `3`

## 1862 | score=0.778 | number_theory

In a game, Alice and Bob play with a sequence of integers \( a_1, a_2, \ldots, a_n \) where each \( a_i \) is a positive integer less than or equal to \( n \). The game proceeds as follows: Alice starts by choosing an index \( i \) and removes the element \( a_i \) from the sequence. Then Bob removes the element \( a_{a_i} \). This process continues with Alice removing the index of the element that Bob removed, and so on. The game ends when no more elements can be removed. What is the minimum possible value of \( n \) for which Alice can ensure that the game ends after exactly 5 moves, regardless of the initial sequence and Bob's choices?

Answer: `5`

## 1863 | score=0.667 | number_theory

Let \( f(n) \) be a function defined on the set of positive integers such that \( f(1) = 1 \) and for all positive integers \( n \), \( f(n+1) = f(n) + \frac{1}{f(n)} \). Prove that \( f(2023) > 45 \).

Answer: `f(2023) > 45`

## 1864 | score=0.333 | geometry

In a triangle \( \triangle ABC \), the lengths of sides \( AB \), \( BC \), and \( CA \) are distinct positive integers. It is given that \( AB \) and \( BC \) are the two shortest sides, and the length of \( CA \) is the sum of \( AB \) and \( BC \). Additionally, the angle bisector of \( \angle B \) intersects side \( CA \) at a point \( D \) such that the segments \( AD \) and \( DC \) are in the ratio \( 2:3 \). If the area of \( \triangle ABD \) is \( 24 \) square units, determine the length of side \( BC \).

Answer: `9`

## 1865 | score=0.667 | number_theory

Consider a sequence of positive integers \(a_1, a_2, a_3, \ldots, a_n\) where each term is the smallest integer greater than the previous term and not relatively prime to any of the previous terms. If the first term \(a_1 = 2\), find the smallest possible value of \(n\) such that \(a_n = 2024\).

Answer: `1012`

## 1866 | score=0.556 | number_theory

Let \( S \) be a set of positive integers such that for any two distinct elements \( a \) and \( b \) in \( S \), the greatest common divisor \( \gcd(a, b) \) is not a prime number. What is the maximum possible number of elements in \( S \) if \( S \) contains at most 10 distinct prime numbers?

Answer: `10`

## 1867 | score=0.444 | number_theory

Find all pairs of positive integers $(m, n)$ such that the polynomial $P(x) = x^3 + mx^2 + nx + m$ has three distinct real roots, all of which are integers. Determine the sum of all possible values of $m$.

Answer: `6`

## 1868 | score=0.667 | geometry

Find all pairs of integers (x, y) such that x² + y² = 3xy + 1. Prove that the sum of all possible values of x is a perfect square.

Answer: `0`

## 1869 | score=0.333 | number_theory

Find the number of ordered triples $(a, b, c)$ of positive integers such that $abc = 1000$ and $a \leq b \leq c$.

Answer: `10`

## 1870 | score=0.556 | combinatorics

Let \( S = \{1, 2, 3, \ldots, 20\} \). Define a function \( f: S \to S \) such that for every subset \( A \subseteq S \) with \( |A| = 5 \), there exists a permutation \( \sigma \in S_5 \) such that \( f(a_1), f(a_2), f(a_3), f(a_4), f(a_5) \) is a derangement of \( \sigma(1), \sigma(2), \sigma(3), \sigma(4), \sigma(5) \). Find the number of such functions \( f \).

Note: A derangement is a permutation where no element appears in its original position.

Answer: `1`

## 1871 | score=0.667 | number_theory

A sequence of positive integers $a_1, a_2, a_3, \ldots$ is defined by the following rule: $a_{n+1} = a_n^2 - a_n + 1$ for all $n \geq 1$. If $a_1 = 2$, find the value of $a_{10} \mod 1000$.

Answer: `443`

## 1872 | score=0.333 | geometry

In the coordinate plane, let \(P\) be the set of points with integer coordinates. A set of segments \(\mathcal{S}\) is a perfect matching if every point in \(P\) is an endpoint of exactly one segment in \(\mathcal{S}\), and no two segments in \(\mathcal{S}\) intersect except possibly at their endpoints. What is the minimum number of segments required to form a perfect matching in \(P\), given that the set of points \(P\) contains all points \((x, y)\) such that \(x\) and \(y\) are non-negative integers with \(x+y \leq 100\)?

Answer: `2575`

## 1873 | score=0.500 | other

In a country with $n \ge 2$ cities, each city is connected to every other city by either a highway or a direct flight (but not both). A traveler starts in one city and wants to visit each city exactly once, returning to the starting city. If the total number of such circuits is $24!$ (the factorial of 24), determine the smallest possible value of $n$.

Answer: `25`

## 1874 | score=0.333 | geometry

In the complex plane, let \( z_1, z_2, z_3 \) be the vertices of an equilateral triangle inscribed in the unit circle, with \( z_1 = 1 \) and \( z_3 = e^{i\pi/3} \). If \( w = z_2 + z_3 \), find the absolute value of the imaginary part of \( w \), denoted as \( |Im(w)| \).

Answer: `\sqrt{3}`

## 1875 | score=0.778 | number_theory

Determine all positive integers \( n \) such that there exists a set of \( n \) distinct positive integers \(\{a_1, a_2, \ldots, a_n\}\) where \(\sum_{i=1}^{n} \frac{1}{a_i} = 1\).

Answer: `n \geq 3`

## 1876 | score=0.444 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + (n-1)x + 1 \) can be factored into two non-constant polynomials with integer coefficients.

Answer: `1`

## 1877 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers that can be expressed as the sum of two or more consecutive positive integers. How many positive integers less than or equal to 1000 are not in \( S \)?

Answer: `10`

## 1878 | score=0.667 | number_theory

A function \( f \) is defined on the positive integers such that \( f(1) = 1 \) and for all positive integers \( n \), \( f(n + 1) = f(n) + \frac{1}{f(n)} \). Determine the integer closest to \( f(2023) \).

Answer: `64`

## 1879 | score=0.444 | number_theory

Find all prime numbers \( p \) and \( q \) such that \( p^2 + pq + q^2 = n^2 \) for some integer \( n \). Additionally, determine the number of distinct pairs \((p, q)\) that satisfy this equation.

Answer: `0`

## 1880 | score=0.778 | number_theory

Let $S$ be a set of integers such that for any $a, b \in S$, the expression $a^3 + b^3 + 1$ is divisible by $a + b + 1$. Find the number of distinct elements in $S$ if $S$ contains all integers from $1$ to $100$ inclusive.

Answer: `100`

## 1881 | score=0.333 | geometry

A convex quadrilateral \(ABCD\) has side lengths \(AB = 13\), \(BC = 14\), \(CD = 15\), and \(DA = 16\). The diagonals \(AC\) and \(BD\) intersect at point \(P\) such that the areas of triangles \(APB\), \(BPC\), \(CPD\), and \(DPA\) are equal. Find the length of diagonal \(AC\).

Answer: `17`

## 1882 | score=0.444 | other

在一个有限的正整数集合S中，元素个数为n。已知对于所有a,b∈S且a≠b，满足|a-b|也是集合S中的一个元素（除了当a+b>max(S)时，设|a-b|=a-b）。集合S的最大值记为m。现在，求解最大的m值，使得这样的集合S最少有3个不同的元素。

Answer: `3`

## 1883 | score=0.444 | number_theory

Let \( S \) be a set of 100 positive integers, all less than or equal to 1000. Define \( T \) as the set of all pairwise sums of distinct elements from \( S \). If \( T \) contains exactly 200 elements and all elements of \( T \) are distinct, what is the maximum possible value of the smallest element in \( T \)?

Answer: `3`

## 1884 | score=0.444 | number_theory

In a sequence of positive integers \( a_1, a_2, a_3, \ldots, a_{2023} \), each term after the first is the smallest integer greater than the previous term that is relatively prime to all previous terms. Given that \( a_{2023} = 2023 \), find the sum of all possible values of \( a_1 \).

Answer: `1`

## 1885 | score=0.778 | number_theory

Let \( f(x) \) be a function defined for all real numbers \( x \), such that \( f(x) \) satisfies the functional equation:
\[ f(x + y) + f(x - y) = 2f(x)f(y) \]
for all \( x, y \in \mathbb{R} \). Furthermore, it is given that \( f(0) = 1 \) and \( f(1) = a \), where \( a \) is a positive real number. Find all possible values of \( a \) such that \( f(x) \) is a periodic function with period \( T \), where \( T \) is the smallest positive real number for which \( f(x + T) = f(x) \) for all \( x \in \mathbb{R} \).

Answer: `1`

## 1886 | score=0.444 | geometry

In triangle \(ABC\), let \(D\) be the midpoint of \(BC\). The perpendicular bisector of \(BD\) intersects \(AC\) at point \(E\). If \(AB = 10\), \(BC = 14\), and \(CA = 16\), determine the length of segment \(AE\).

Answer: `8`

## 1887 | score=0.333 | algebra

在一个边长为1的正三角形区域内随机放置一个点P。点P的坐标(x, y)满足0 <= x <= 1且0 <= y <= 1。定义函数f(P)为从P到该正三角形顶点的距离平方的平均值。请问f(P)的最小可能值是多少？

Answer: `\frac{1}{3}`

## 1888 | score=0.778 | geometry

Find all integers \( n \) such that \( n^2 + 23n + 133 \) is a perfect square.

Answer: `-11, -12`

## 1889 | score=0.556 | algebra

In the complex plane, let \( P(z) \) be a polynomial of degree 4 with real coefficients, such that \( P(1) = 10, P(2) = 20, P(3) = 30, \) and \( P(0) = 0. \) Find the sum of all possible values of \( P(4). \)

Answer: `40`

## 1890 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the number of integers \( k \) satisfying \( 1 \leq k \leq n \) and \( k^3 \equiv 1 \pmod{n} \) is equal to the number of integers \( m \) satisfying \( 1 \leq m \leq n \) and \( m^2 \equiv 1 \pmod{n} \).

Answer: `4`

## 1891 | score=0.556 | number_theory

Find the smallest positive integer \( n \) such that the polynomial \( P(x) = x^4 + ax^3 + bx^2 + cx + d \) has exactly two distinct real roots, and these roots are both integers, and the coefficients \( a, b, c, d \) are all integers.

Answer: `1`

## 1892 | score=0.667 | number_theory

Find the number of ordered triples $(a, b, c)$ of positive integers such that $a \cdot b \cdot c = 1008$ and each of $a, b,$ and $c$ is a divisor of the next one in the sequence. For example, $(12, 84, 1008)$ is one such triple since $1008$ is divisible by $84$, and $84$ is divisible by $12$.

Answer: `270`

## 1893 | score=0.667 | number_theory

Find all positive integers \( n \) such that the polynomial \( x^n + y^n + z^n - 3xyz \) is divisible by \( (x + y + z) \) for all real numbers \( x, y, z \).

Answer: `3`

## 1894 | score=0.333 | number_theory

Find all integer solutions \((x, y)\) to the equation:
\[ x^3 + y^3 + 1 = 6xy. \]

Answer: `(0, -1), (-1, 0)`

## 1895 | score=0.444 | number_theory

Find all positive integers \( n \) such that \( n \) divides \( 2^n + 1 \) and \( n + 1 \) divides \( 2^n - 1 \). Prove that if such \( n \) exists, then \( n \) must be a multiple of 3.

Answer: `3`

## 1896 | score=0.444 | number_theory

Find the smallest positive integer \( n \) such that \( n! \) (n factorial) is divisible by the product of all primes less than \( n \).

Answer: `2`

## 1897 | score=0.667 | number_theory

Consider a sequence of positive integers \(a_1, a_2, a_3, \ldots, a_n\) such that \(a_1 = 1\) and \(a_{k+1} = a_k^2 - 2\) for \(k \geq 1\). Let \(S_n\) be the sum of the first \(n\) terms of this sequence. Find the smallest positive integer \(n\) such that \(S_n\) is divisible by 1000.

Answer: `2`

## 1898 | score=0.333 | number_theory

Let $a$, $b$, and $c$ be positive integers such that $a^2 + b^2 = c^3$. If $a$ and $b$ are consecutive integers and $c$ is a prime number, find the smallest possible value of $c$ for which this condition holds.

Answer: `13`

## 1899 | score=0.333 | number_theory

Find the number of positive integers \( n \) such that \( n \) divides \( 2020^n + 1 \) and \( n \) is a prime number less than 1000.

Answer: `2`

## 1900 | score=0.778 | number_theory

Let \( p \) be a prime number. Determine the number of solutions to the equation \( x^2 - px + p^2 - 1 = 0 \) modulo \( p^2 \) for any given prime \( p \).

Answer: `2`

## 1901 | score=0.333 | number_theory

In the enchanted forest, there are 12 magical trees, each with a unique number of golden leaves. The total number of golden leaves among all the trees is 132. The number of leaves on each tree is a positive integer, and no two trees have the same number of leaves. If the tree with the least number of leaves has exactly 6 leaves, what is the maximum possible number of leaves on the tree with the most leaves?

Answer: `11`

## 1902 | score=0.333 | number_theory

There exists a function \(f: \mathbb{Z} \to \mathbb{Z}\) such that for all integers \(x\) and \(y\), the equation \(f(xy) = f(x)f(y) + x + y\) holds. Moreover, it is given that \(f(2) = 2\). Find the value of \(f(3)\).

Answer: `4`

## 1903 | score=0.333 | number_theory

Consider a sequence of integers \(a_n\) defined by the recurrence relation \(a_0 = 2\), \(a_1 = 3\), and \(a_{n+2} = a_{n+1} + a_n\) for all \(n \geq 0\). Let \(p(n)\) denote the number of positive integers less than or equal to \(n\) that are relatively prime to \(a_n\). Find the smallest \(n\) for which \(p(n) = 2023\).

Answer: `2023`

## 1904 | score=0.667 | number_theory

Consider a sequence of positive integers \(a_1, a_2, \ldots, a_n\) where each \(a_i\) is distinct and satisfies \(a_i \leq 100\) for all \(i = 1, 2, \ldots, n\). Define a function \(f\) that maps each sequence to a positive integer by the formula:
\[ f(a_1, a_2, \ldots, a_n) = a_1 \cdot a_2 \cdots a_n + \sum_{i=1}^{n} a_i. \]
Determine the maximum value of \(f\) if \(n = 5\).

Answer: `9034502890`

## 1905 | score=0.444 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(0) = 0 \) and \( P(1) = 2024 \). Define a sequence \( \{a_n\} \) by \( a_n = P(n) \). Prove that there exists a positive integer \( k \) such that \( a_{2k} = 2a_k \).

Answer: `1`

## 1906 | score=0.333 | number_theory

A sequence of integers \(a_1, a_2, a_3, \ldots, a_n\) is defined recursively by \(a_1 = 1\) and \(a_{k+1} = a_k^2 - a_k + 1\) for \(k \geq 1\). Find the smallest positive integer \(n\) such that \(a_n\) is divisible by \(1000\).

Answer: `0`

## 1907 | score=0.556 | geometry

Let \( ABC \) be a triangle with circumradius \( R \) and inradius \( r \). Suppose the perpendicular bisectors of the sides \( AB \) and \( AC \) intersect the circumcircle of \( ABC \) at points \( P \) and \( Q \), respectively. If the area of triangle \( APQ \) is \( \frac{1}{3} \) of the area of triangle \( ABC \), find the ratio \( \frac{R}{r} \).

Answer: `2`

## 1908 | score=0.333 | number_theory

Consider the sequence of positive integers \(a_n\) defined by \(a_1 = 1\), \(a_2 = 3\), and for \(n \geq 3\), \(a_n = a_{n-1} + 2a_{n-2}\). Find the smallest \(n\) such that \(a_n\) has exactly 5 distinct prime factors.

Answer: `21`

## 1909 | score=0.333 | geometry

In the plane, there are \( n \) points, no three of which are collinear. A circle is drawn around each point that passes through it and one of the other two points. What is the maximum number of intersections of these circles that can be formed if \( n = 7 \)?

Answer: `1190`

## 1910 | score=0.333 | number_theory

In the kingdom of Mathoria, there exists a magical sequence of numbers, \(M_n\), defined as follows: \(M_1 = 1\), \(M_2 = 2\), and for \(n \geq 3\), \(M_n\) is the smallest positive integer greater than \(M_{n-1}\) that cannot be expressed as the sum of two distinct earlier terms in the sequence. For instance, \(M_3 = 4\) because it is the smallest integer greater than 2 that cannot be expressed as the sum of two distinct earlier terms (1 and 2). What is \(M_{10}\)?

Answer: `14`

## 1911 | score=0.667 | geometry

In the plane, points $A, B, C, D, E,$ and $F$ are chosen such that $AB = BC = CD = DE = EF = FA$ and $B, D,$ and $F$ are collinear. If $\angle ABC = \theta$ and $\angle ADE = 2\theta$, find the value of $\theta$ for which $\triangle ABC$ and $\triangle ADE$ have equal areas.

Answer: `60`

## 1912 | score=0.556 | number_theory

Let \( S \) be the set of all positive integers \( n \) for which the polynomial \( P(x) = x^3 - nx + n \) has three distinct integer roots. Find the sum of all elements in \( S \).

Answer: `6`

## 1913 | score=0.444 | number_theory

Find all positive integers \( n \) such that the polynomial \( P(x) = x^n + ax^{n-1} + bx^{n-2} + \ldots + k \) with integer coefficients has a root that is a rational number, and the sum of the absolute values of all coefficients of \( P(x) \) is less than \( 2n + 1 \).

Answer: `1, 2`

## 1914 | score=0.333 | geometry

A square $ABCD$ is inscribed in a circle of radius $r$. Points $E$ and $F$ lie on sides $AB$ and $BC$ respectively, such that $AE = 2BE$ and $CF = 3BF$. Find the ratio of the area of triangle $AEF$ to the area of the square $ABCD$.

Answer: `\frac{1}{12}`

## 1915 | score=0.333 | geometry

Let \( S \) be a set of \( n \) distinct positive integers. For any two distinct elements \( a, b \in S \), define \( f(a, b) \) as the number of ordered pairs \( (c, d) \) of elements from \( S \) such that \( a \leq c < d \leq b \) and \( c + d \) is a perfect square. If \( f(a, b) = 12 \) for some \( a, b \in S \), find the minimum possible value of \( n \) for which such a set \( S \) exists.

Answer: `13`

## 1916 | score=0.444 | number_theory

Find all triples of prime numbers \( p, q, \) and \( r \) such that \( p + q + r = pqr \).

Answer: `(2, 3, 5)`

## 1917 | score=0.556 | algebra

Let \( f(x) \) be a polynomial of degree \( n \) with real coefficients such that \( f(x) \) has \( n \) distinct real roots. Define \( g(x) = f'(x) \). Suppose that for some real number \( a \), the equation \( g(x) = a \) has exactly \( n - 1 \) real solutions. Prove that there exists a real number \( b \) such that the equation \( g(x) = b \) has exactly \( n - 1 \) real solutions and \( b \neq a \).

Answer: `b`

## 1918 | score=0.333 | geometry

Find all positive integers \( n \) such that \( n^4 + 200n^2 + 1 \) is a perfect square.

Answer: `70`

## 1919 | score=0.333 | number_theory

There exists a sequence of numbers $a_1, a_2, a_3, \ldots$ defined by the recursion:
\[a_1 = 1, \quad a_{n+1} = a_n + \frac{1}{a_n^2}\]
for all $n \ge 1$. Find the smallest positive integer $k$ such that $a_k > 100$. If $k$ does not exist, enter $0$.

Answer: `333334`

## 1920 | score=0.667 | geometry

In triangle \(ABC\), the altitude from \(A\) meets \(BC\) at \(D\). Let \(E\) be the point on \(AC\) such that \(DE\) is perpendicular to \(AC\). If \(AD = 8\), \(BD = 5\), and \(CD = 6\), find the length of \(DE\).

Answer: `8.8`

## 1921 | score=0.333 | logic_puzzle

In a peculiar town, there are three types of coins: gold, silver, and bronze. A gold coin is worth 5 silver coins, and a silver coin is worth 5 bronze coins. A traveler arrives with 1 gold coin, 2 silver coins, and 3 bronze coins. If he exchanges all his coins into bronze coins, he finds he has 40 more bronze coins than he initially had. How many bronze coins did he have originally?

Answer: `38`

## 1922 | score=0.667 | number_theory

Find the number of ordered triples \((a, b, c)\) of positive integers such that \(a \leq b \leq c \leq 100\), and the equation \(a^3 + b^3 + c^3 = 3abc + 300\) holds.

Answer: `1`

## 1923 | score=0.444 | geometry

A convex polygon with 2023 sides is given. Each vertex is colored either red or blue, and each side is colored either black or white. It is known that no two adjacent sides have the same color. Moreover, if two vertices are of the same color, then the side between them is black; otherwise, the side is white. Find the number of distinct colorings of the polygon, given that two colorings are considered distinct if there is at least one vertex or side that has a different color.

Answer: `2^{2023}`

## 1924 | score=0.444 | algebra

Let $f(x) = x^3 - 3x^2 + 2x$. Determine the number of distinct real solutions to the equation $f(f(x)) = 0$.

Answer: `9`

## 1925 | score=0.667 | number_theory

Let \( f: \mathbb{Z} \to \mathbb{Z} \) be a function defined by \( f(n) = n^2 + 2n + 3 \). For how many integers \( k \) is there an integer \( n \) such that \( f(n) = k \) and \( n \) is a prime number?

Answer: `\infty`

## 1926 | score=0.667 | number_theory

Let $S$ be the set of all positive integers that can be expressed in the form $n^4 + 4n^3 + 6n^2 + 4n + 1$ for some positive integer $n$. Prove that for any positive integer $k$, the number $k^5 - k$ can be expressed as the sum of $k$ distinct elements of $S$.

Answer: `k^5 - k`

## 1927 | score=0.333 | logic_puzzle

In a magical forest, there are three types of trees: Oak, Maple, and Birch. Each tree type has a unique way of growing new branches. Oak trees grow a branch for every month that passes since the last leaf falls, Maple trees grow a branch for every two months that pass without rain, and Birch trees grow a branch for every three months that pass without snow. If today is January 1st and it has been exactly 365 days since the last leaf fell on an Oak tree, 730 days without rain on a Maple tree, and 1095 days without snow on a Birch tree, how many new branches will each tree type grow by the end of the year?

Answer: `12`

## 1928 | score=0.444 | number_theory

In a magical land, there exists a unique species of flowers that bloom in cycles of $1, 2, 3, 4, 5, ...$ days. However, on day $n$, each flower transforms into a new flower with a bloom cycle that is the least common multiple (LCM) of $n$ and $n+1$. On day 1, there is a single flower. What is the number of flowers after 2023 days?

Answer: `1`

## 1929 | score=0.556 | other

在一个无限长的直线上，有n个点，每个点都有一个值ai。现在，你可以选择一个整数k（1<=k<=n），然后将第i个点和第i+k（或i-k）个点之间的距离变成0。换句话说，你可以将某两个相邻的点“合并”成一个点。求出一种操作方式，使得所有点最终相邻的点之间距离都为0（即所有点都在同一个点上），并且使得最终的合并次数最少。输出最小的合并次数。

Answer: `n-1`

## 1930 | score=0.333 | number_theory

What is the least positive integer that can be expressed as the sum of distinct powers of 3 such that the sum is also a prime number?

Answer: `3`

## 1931 | score=0.444 | geometry

In a unique game of infinite chess, two players take turns moving a single knight on an unbounded chessboard. The first player aims to reach a specific position, while the second player attempts to prevent this. If the first player can reach their target position, they win; otherwise, the game continues indefinitely. Assuming both players play optimally, determine the minimum number of moves required for the first player to guarantee victory when their target position is 5 squares horizontally and 3 squares vertically away from the starting position.

Answer: `3`

## 1932 | score=0.556 | other

在一个圆桌旁坐着 $n$ 个人，每个人面前都有一个盘子。每个人都会从自己面前的盘子中随机选取一个物品放入另一个盘子中。如果物品数量为偶数，则放入其中任何一个盘子；如果物品数量为奇数，则只能放入面前的盘子。问，当 $n=2023$ 时，恰好 $1012$ 个人的盘子中物品数量相同（包括物品数量为 $0$ 的情况）的概率是多少？

Answer: `0`

## 1933 | score=0.667 | geometry

In a sequence of positive integers \(a_1, a_2, a_3, \ldots, a_n\), each term is the sum of the squares of its digits. For example, \(a_1 = 23\), \(a_2 = 2^2 + 3^2 = 13\), and \(a_3 = 1^2 + 3^2 = 10\). Determine the smallest positive integer \(n\) such that \(a_n = 1\) and \(a_{n+1} = 1\), and explain why no smaller \(n\) satisfies these conditions.

Answer: `4`

## 1934 | score=0.333 | number_theory

Let \( S \) be a finite set of positive integers. Define the set \( T \) as follows: For every positive integer \( n \), if the number of distinct prime factors of \( n \) is even, then \( n \) is in \( T \). If the number of distinct prime factors of \( n \) is odd, then \( n \) is in \( T \) if and only if \( n \) is a product of exactly two distinct primes. Let \( A \) be the sum of all elements in \( S \) that are also in \( T \). Given that \( A = 120 \) and the number of elements in \( S \) is 10, determine the maximum possible number of elements in \( S \) that are prime numbers.

Answer: `5`

## 1935 | score=0.444 | number_theory

Let $S$ be a set of $n$ distinct positive integers. A subset $T$ of $S$ is called *reversible* if there exists a positive integer $k$ such that for every pair of distinct elements $x$ and $y$ in $T$, either $x$ divides $y$ or $y$ divides $x$ and $k$. How many reversible subsets can be formed from $S$?

Answer: `2^n`

## 1936 | score=0.444 | number_theory

What is the smallest positive integer \( n \) for which the equation \[ \left( x - \frac{1}{x} \right)^2 = n \] has at least three distinct real solutions for \( x \)?

Answer: `1`

## 1937 | score=0.444 | number_theory

Consider the sequence \( a_1, a_2, a_3, \ldots \) defined by \( a_1 = 1 \) and for \( n \geq 2 \),
\[
a_n = a_{n-1} + \frac{1}{a_1 a_2 \cdots a_{n-1}}.
\]
Find the smallest integer \( k \) such that \( a_k > 2023 \).

Answer: `2023`

## 1938 | score=0.333 | geometry

Given a convex quadrilateral $ABCD$ with diagonals $AC$ and $BD$ intersecting at point $E$, and lengths $AE = 4$, $EC = 6$, $BE = 3$, and $ED = 5$, find the maximum possible value of the area of $ABCD$.

Note: Use the Brahmagupta's formula for the area of a cyclic quadrilateral if necessary.

Answer: `40`

## 1939 | score=0.556 | combinatorics

A sequence of real numbers \(\{a_n\}\) is defined by the recurrence relation \(a_{n+1} = \frac{a_n + a_{n-1}}{2}\) for \(n \geq 2\), with initial conditions \(a_1 = 2\) and \(a_2 = 6\). Find the value of \(a_{2024}\).

Answer: `4`

## 1940 | score=0.333 | number_theory

Find all positive integers \( n \) such that the equation
\[
n^3 - n^2 - 5n + 3 = 2^k
\]
holds for some non-negative integer \( k \).

Answer: `2`

## 1941 | score=0.667 | number_theory

Find all positive integers \( n \) for which the equation
\[ x^2 + y^2 + z^2 + w^2 = nxy + nyw + nzw + nzx \]
has a non-trivial solution in the integers, i.e., a solution where not all of \( x, y, z, w \) are zero. Prove that your list of solutions is complete.

Answer: `1`

## 1942 | score=0.333 | number_theory

Find all positive integers \( n \) such that \( 3^n - 1 \) is divisible by \( 2^n + 1 \).

Answer: `1`

## 1943 | score=0.333 | geometry

Let $ABCDEF$ be a regular hexagon with side length $s$. Let $G$ be the midpoint of $AB$, $H$ the midpoint of $BC$, and $I$ the midpoint of $CD$. The lines $GH$ and $HI$ intersect at point $J$. Find the ratio of the area of triangle $GJI$ to the area of the hexagon $ABCDEF$.

Answer: `\frac{1}{12}`

## 1944 | score=0.444 | algebra

Consider a function \(f(x)\) defined for all positive real numbers \(x\) such that \(f(x) = x^3 + \frac{1}{x^3}\). If \(f(a) = f(b)\) for distinct positive real numbers \(a\) and \(b\), and \(a + b = 10\), find the value of \(ab\).

Answer: `25`

## 1945 | score=0.333 | number_theory

Let $A$ be an array of $n$ integers in the range $[-n, n]$, and let $B$ be a subset of $A$ containing exactly $m$ elements where $m \leq n$. Define the weighted sum $S$ of the elements in $B$ as $S = \sum_{i=1}^{m} a_i \cdot w_i$, where $a_i \in B$ and $w_i \in [1, 10]$. Find the number of ways to choose the subset $B$ and assign the weights $w_i$ such that the weighted sum $S$ is divisible by $n$.

Answer: `\binom{n}{m} \cdot 10^m`

## 1946 | score=0.556 | number_theory

Find the number of positive integers \( n \) such that the polynomial \( P(x) = x^4 + nx^2 + 1 \) can be expressed as a product of two non-constant polynomials with integer coefficients.

Answer: `1`

## 1947 | score=0.556 | geometry

Let \( P \) be a point inside triangle \( ABC \) such that \( PA = PB \) and \( \angle BPA = 120^\circ \). Let \( D \) be the midpoint of side \( AB \). Prove that \( PD \) is perpendicular to \( BC \).

Answer: `PD \perp BC`

## 1948 | score=0.556 | number_theory

A sequence of positive integers $a_1, a_2, a_3, \ldots$ is defined by $a_1 = 2023$ and for all $n \geq 2$, $a_n = a_{n-1}^2 - 2a_{n-1} + 2$. Let $S$ be the set of all positive integers that can be expressed as $a_m - a_k$ for some integers $m > k \geq 1$. Find the number of elements in $S$ that are less than $10^{12}$.

Answer: `1`

## 1949 | score=0.333 | geometry

A circle is inscribed in an isosceles triangle with sides 13, 13, and 10. A smaller circle is drawn tangent to the larger circle and also tangent to the two legs of the triangle. Find the radius of the smaller circle.

Answer: `\frac{5}{3}`

## 1950 | score=0.333 | number_theory

Let $f(n)$ be a function defined on the positive integers, where $f(1) = 1$ and for all $n \ge 2$, $f(n)$ is the smallest positive integer not already in the sequence $f(1), f(2), \ldots, f(n-1)$ that is coprime to $n$. Determine the value of $f(2023)$.

Answer: `2`

## 1951 | score=0.556 | number_theory

Find all integers \( n \) such that the equation
\[ x^3 - y^3 = n^2 \]
has exactly one solution in positive integers \( (x, y) \).

Answer: `0`

## 1952 | score=0.667 | geometry

In the plane, a point \( P \) is chosen at random inside a square with vertices at \((0,0)\), \((10,0)\), \((10,10)\), and \((0,10)\). A circle centered at \( P \) is drawn such that it passes through the point \( (10,10) \). What is the probability that this circle intersects the positive \( x \)-axis? Express your answer as a common fraction.

Answer: `\frac{1}{2}`

## 1953 | score=0.444 | number_theory

Let $P(x) = x^4 + ax^3 + bx^2 + cx + d$ be a polynomial with integer coefficients. Suppose that $P(1) = 2023$, $P(2) = 2024$, and $P(3) = 2025$. If $r$ is a root of $P(x)$, find the smallest possible positive integer value of $r^2$.

Answer: `1`

## 1954 | score=0.778 | number_theory

Find the smallest positive integer \( n \) such that the sum of the digits of \( n! \) is divisible by \( n \).

Answer: `1`

## 1955 | score=0.444 | geometry

Find all positive integers \( n \) such that \( n^4 + 4n^3 + 2n^2 + 4n + 1 \) is a perfect square.

Answer: `1`

## 1956 | score=0.625 | number_theory

Let \( f(x) \) be a polynomial with integer coefficients such that \( f(1) = 5 \) and \( f(2) = 11 \). If \( f(x) \) can be expressed in the form \( ax^3 + bx^2 + cx + d \), find the smallest possible value of \( |a + b + c + d| \).

Answer: `5`

## 1957 | score=0.444 | number_theory

Find the smallest positive integer \( n \) such that the number of ordered pairs of positive integers \( (x, y) \) satisfying the equation \( x^2 - y^2 = n \) is exactly 8.

Answer: `24`

## 1958 | score=0.333 | geometry

Let \( S \) be a set of 2023 points in the plane, no three of which are collinear. Each point \( P \) in \( S \) has an associated positive real number \( r_P \), which represents its "radius." Define the "distance" between two points \( P \) and \( Q \) in \( S \) to be \( r_P + r_Q \) if \( P \) and \( Q \) are not connected by an edge in a graph \( G \) that is formed by connecting every pair of points \( (P, Q) \) such that \( r_P + r_Q = d \) for some fixed distance \( d \). Determine the maximum possible number of edges in the graph \( G \) such that for any subset of points \( T \subseteq S \), the sum of the radii of the points in \( T \) is greater than the minimum distance between any two points in \( T \).

Answer: `2045253`

## 1959 | score=0.444 | number_theory

Find all positive integers \( n \) such that \( n^2 + n + 1 \) divides \( n! \).

Answer: `0`

## 1960 | score=0.556 | number_theory

Find all prime numbers \( p \) and positive integers \( n \) such that \( p^n + 1 \) divides \( n^p + 1 \).

Answer: `(2, 2)`

## 1961 | score=0.333 | number_theory

Find all positive integers \( n \) such that there exists a polynomial \( P(x) \) with integer coefficients satisfying the equation \( P(k) = k^n \) for all positive integers \( k \).

Answer: `1`

## 1962 | score=0.778 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a continuous function such that for every \( x \in \mathbb{R} \), the sequence \( \{ f(n x) \}_{n=1}^\infty \) is bounded. Prove that there exists a real number \( c \) such that \( f(x + c) = f(x) \) for all \( x \in \mathbb{R} \).

Answer: `c`

## 1963 | score=0.556 | number_theory

There exists a positive integer \( n \) such that \( 2^n + 3^n \) is divisible by \( n \). Find the largest possible value of \( n \) that satisfies this condition.

Answer: `5`

## 1964 | score=0.667 | algebra

Let $f : \mathbb{R} \to \mathbb{R}$ be a function satisfying $f(x+y) = f(x)f(y) - f(xy) + 1$ for all real numbers $x$ and $y$. If $f(1) = 2$, determine the value of $f(5)$.

Answer: `6`

## 1965 | score=0.333 | algebra

In the complex plane, let \( z \) be a root of the polynomial \( P(z) = z^5 - z^3 + z^2 - 1 \). Find the sum of all possible values of \( \text{Re}(z^2) \), where \( \text{Re} \) denotes the real part of the complex number.

Note: The roots are complex numbers and the real part of a complex number \( a + bi \) is \( a \).

Answer: `2`

## 1966 | score=0.667 | number_theory

Let \( S \) be a finite set of positive integers such that for any two distinct elements \( a \) and \( b \) in \( S \), the greatest common divisor of \( a \) and \( b \) is 1. Suppose that for any element \( n \) in \( S \), the product of the elements in \( S \) is divisible by \( n \). If the smallest element in \( S \) is 2 and the largest element is 10, what is the sum of all elements in \( S \)?

Answer: `17`

## 1967 | score=0.556 | number_theory

Find all triples \((a, b, c)\) of positive integers such that
\[ a + b + c = abc + 1 \]

Answer: `(1, 2, 2), (2, 1, 2), (2, 2, 1)`

## 1968 | score=0.556 | number_theory

Find all integers $x$ such that the polynomial $x^4 - 16x^3 + 89x^2 - 192x + 147$ can be factored into two quadratic polynomials with integer coefficients. Provide the sum of all such integers $x$.

Answer: `0`

## 1969 | score=0.444 | number_theory

Let $f(x) = x^5 + ax^4 + bx^3 + cx^2 + dx + e$ be a polynomial with integer coefficients and exactly five distinct integer roots. Given that the sum of the roots taken two at a time is 20, and the product of the roots taken two at a time is 100, find the value of $e$.

Answer: `-100`

## 1970 | score=0.667 | number_theory

Consider the sequence defined by \(a_1 = 1\) and \(a_{n+1} = a_n + \frac{1}{a_n}\) for all \(n \geq 1\). Find the smallest integer \(N\) such that \(a_N > 5\).

Answer: `13`

## 1971 | score=0.333 | number_theory

Let \( P(x) \) be a polynomial with integer coefficients such that \( P(1) = 2 \) and \( P(2) = 3 \). Suppose that there exists an integer \( k \) for which \( P(k) = k^2 + 1 \). Determine the smallest possible positive value of \( k \) that satisfies this condition.

Answer: `1`

## 1972 | score=0.333 | number_theory

Find the smallest positive integer \( n \) such that the product of the first \( n \) positive integers (i.e., \( n! \)) is divisible by \( 10^{12} \). Prove your answer.

Answer: `60`

## 1973 | score=0.444 | number_theory

Let $P(x)$ be a polynomial of degree $n$ with integer coefficients such that $P(0) = 1$ and for every positive integer $k$, $P(k)$ is divisible by $k$. Find the smallest possible value of $n$ such that there exists a polynomial $P(x)$ satisfying these conditions.

Answer: `2`

## 1974 | score=0.333 | number_theory

Let $P(x)$ be a polynomial with integer coefficients such that $P(10) = 1000$ and $P(100) = 100000$. Given that $P(x)$ has a degree of at most $5$, find the number of possible integer roots that $P(x)$ can have.

Answer: `5`

## 1975 | score=0.556 | algebra

Let \( f: \mathbb{R} \to \mathbb{R} \) be a function defined by
\[ f(x) = x^4 - 4x^3 + 6x^2 - 4x + 4. \]
Prove that there exists a unique real number \( c \) such that \( f(c) = c \). Moreover, determine the value of \( c \).

Answer: `1`

## 1976 | score=0.667 | geometry

Find the number of ordered pairs of positive integers \((a, b)\) that satisfy the equation \(a^2 + b^2 = 2024\). Then, prove that if \(a\) and \(b\) are the legs of a right triangle, the hypotenuse is an integer.

Answer: `0`

## 1977 | score=0.333 | geometry

In a triangular grid, each vertex is connected to its neighboring vertices. Starting from a vertex, a path is formed by moving to adjacent vertices, with the restriction that no vertex can be visited more than once. Given a triangular grid with 6 layers (forming a triangle with 1 vertex at the top, 2 vertices in the second row, and so on until 6 vertices in the bottom row), how many unique paths can be taken that start and end at the top vertex and traverse exactly 5 edges?

Answer: `2`

## 1978 | score=0.556 | number_theory

Find all positive integers \(n\) for which there exists a permutation \(\sigma\) of the set \(\{1, 2, \ldots, n\}\) such that for every integer \(k\) with \(1 \leq k \leq n\), the following condition holds:
\[
\sigma(1) + \sigma(2) + \cdots + \sigma(k) \equiv k \pmod{n}.
\]

Answer: `1`

## 1979 | score=0.667 | number_theory

Let $f(x)$ be a polynomial of degree $n$ with integer coefficients such that $f(0) = 1$ and $f(1) = 2$. Suppose further that $f(x)$ has exactly $k$ distinct integer roots. Determine the maximum possible value of $n$ for which it is possible to have $k=5$ roots of $f(x)$.

Answer: `5`

## 1980 | score=0.667 | combinatorics

In a peculiar town, every person either always tells the truth or always lies. On a particular day, each resident makes a statement about the number of truth-tellers in the town. If the number of truth-tellers is n, then the nth truth-teller claims there are n truth-tellers, and the nth liar claims there are n+1 truth-tellers. Given that there are more truth-tellers than liars, what is the smallest possible number of truth-tellers in the town?

Answer: `1`

## 1981 | score=0.667 | number_theory

Given a positive integer \( n \), let \( S(n) \) be the sum of its digits, and let \( P(n) \) be the product of its digits. Find all positive integers \( n \) such that \( n = S(n) \times P(n) \).

Answer: `1`

## 1982 | score=0.667 | number_theory

Find all prime numbers \( p \) such that the equation \( x^2 + xy + y^2 = p \) has integer solutions.

Answer: `3`

## 1983 | score=0.333 | geometry

What is the smallest positive integer $n$ such that there exists a set of $n$ distinct positive integers where the sum of any three distinct members of the set is a perfect square?

Answer: `5`

## 1984 | score=0.333 | algebra

Let \( f(x) = x^5 + ax^4 + bx^3 + cx^2 + dx + e \) be a polynomial with real coefficients such that the polynomial \( g(x) = f(x + 1) \) has five distinct real roots, all less than or equal to \(-1\). If the sum of the coefficients of \( f(x) \) is 0, find the maximum possible value of the constant term \( e \).

Answer: `1`

## 1985 | score=0.444 | number_theory

In a certain town, there are 100 houses numbered from 1 to 100. Each house has a unique number of pets, ranging from 0 to 9. The sum of the number of pets in all the houses is 450. If the number of pets in each house is a non-negative integer and no two adjacent houses (e.g., houses 3 and 4 or houses 10 and 11) can have the same number of pets, what is the maximum number of houses that can have exactly 5 pets?

Answer: `50`

## 1986 | score=0.333 | number_theory

Find all pairs of positive integers $(x, y)$ such that $x^y + y^x = x! + y!$.

Answer: `(1, 1)`

## 1987 | score=0.333 | combinatorics

What is the minimum number of colors needed to color the vertices of a regular icosahedron (a polyhedron with 20 triangular faces) such that no two adjacent vertices share the same color?

Answer: `4`

## 1988 | score=0.444 | geometry

In the complex plane, let $z_1, z_2, z_3, z_4$ be the vertices of a square with side length $s$, centered at the origin. If the product of all the vertices is given by $z_1z_2z_3z_4 = i$, find the area of the square.

Answer: `2`

## 1989 | score=0.444 | number_theory

Let \( f(x) \) be a polynomial with integer coefficients such that \( f(1) = 10 \) and \( f(2) = 20 \). Define the sequence \( a_n = f(n) \) for \( n \in \mathbb{N} \). Find the smallest positive integer \( k \) such that \( a_k \) is divisible by both 5 and 11.

Answer: `11`

## 1990 | score=0.667 | algebra

设 \(f(x)\) 是定义在 \((0, +\infty)\) 上的连续函数，且满足 \(f(x + 1) = 2f(x)\) 对所有 \(x > 0\) 成立。已知 \(f(1) = 1\) 且 \(f\) 在区间 \((0, 1]\) 内连续且严格递增。求证：对于任意正实数 \(n\)，有 \(f(n) > 2^{n-1}\)。

Answer: `f(n) > 2^{n-1}`

## 1991 | score=0.556 | number_theory

Find all integer solutions \((x, y)\) to the equation \(x^2 + y^2 + xy = x + y + 1\).

Answer: `(1, 1), (1, -1), (-1, 1)`

## 1992 | score=0.556 | number_theory

A polynomial \( P(x) \) with integer coefficients is such that when divided by \( x - a \) (where \( a \) is an integer), the remainder is \( a \). When \( P(x) \) is divided by \( x - b \) (where \( b \) is an integer), the remainder is \( b \). Given that \( P(10) = 1000 \), find the remainder when \( P(x) \) is divided by \( (x - 10)(x - 11) \).

Answer: `-989x + 10890`

## 1993 | score=0.333 | number_theory

Find all positive integers \( n \) such that the equation
\[ x^2 + y^2 + z^2 = 3^n \]
has exactly \( n \) distinct positive integer solutions \( (x, y, z) \), where \( x, y, z \) are positive integers and \( x \leq y \leq z \).

Answer: `3`

## 1994 | score=0.333 | number_theory

Find all pairs of positive integers \((a, b)\) such that the equation \(a^2 + b^2 = 3ab + 1\) holds.

Answer: `(1, 3), (3, 1), (3, 8), (8, 3)`

## 1995 | score=0.667 | geometry

Consider the function \( f: \mathbb{Z}^+ \to \mathbb{Z}^+ \) defined recursively by \( f(1) = 1 \) and for \( n > 1 \), \( f(n) = f(n-1) + \left\lfloor \sqrt{f(n-1)} \right\rfloor \). Determine the smallest positive integer \( k \) such that \( f(k) \) is a perfect square.

Answer: `4`

## 1996 | score=0.444 | number_theory

Find all integers \( n \) such that the sum of the digits of \( n^2 \) is equal to \( n \). Provide a proof for your answer.

Answer: `0, 1, 2, 3, 9`

## 1997 | score=0.667 | geometry

Let \( ABC \) be an acute triangle with circumcircle \( \Gamma \). Let \( P \) be a point inside \( \Gamma \) such that \( \angle PBA = \angle PCA \). Let \( Q \) be the second intersection of line \( AP \) with \( \Gamma \). If \( R \) is the midpoint of \( BC \), prove that \( QR \) is perpendicular to \( BP \).

Answer: `QR \perp BP`

## 1998 | score=0.667 | geometry

In the complex plane, consider three distinct points $A, B,$ and $C$ representing complex numbers $a, b,$ and $c$ respectively, such that $|a| = |b| = |c| = r > 0$ and $\arg(a) < \arg(b) < \arg(c)$. If the complex number $d$ is the centroid of triangle $ABC$, find the value of $|d|^2$ in terms of $r$ and the arguments of $a, b,$ and $c$. Use the fact that the centroid's argument lies between the smallest and largest arguments among $a, b,$ and $c$.

Answer: `\frac{r^2}{3}`

## 1999 | score=0.556 | other

In a certain kingdom, there are 100 cities, and each city is connected to exactly 3 other cities by roads. No road is shared by more than 2 cities. A traveling salesman wants to visit each city exactly once and return to his starting city. Can the salesman complete his tour, and if so, what is the minimum number of roads he needs to travel to visit all cities and return to the starting city?

Answer: `100`

## 2000 | score=0.444 | combinatorics

What is the number of ways to arrange the letters in the word COMBINATIONS such that no two vowels are adjacent?

Answer: `4233600`

## 2001 | score=0.444 | combinatorics

What is the minimum number of moves required to arrange the numbers \(1\) through \(8\) on a circular board so that no two adjacent numbers differ by more than \(1\)?

Answer: `0`

## 2002 | score=0.444 | geometry

In the coordinate plane, let  $A = (-2, 0)$ ,  $B = (2, 0)$ , and  $C$  be a point in the  $x$ -axis such that  $C$  lies between  $A$  and  $B$ . Let  $P$  be a point on the curve  $y = \sqrt{4 - x^2}$  (the top half of the circle centered at the origin with radius 2). Find the minimum possible value of  $PA^2 + PB^2 + PC^2$ .

Answer: `20`

## 2003 | score=0.444 | number_theory

Find all integer solutions \((x, y)\) to the equation
\[ x^3 - y^3 = 3xy + 2. \]

Answer: `(1, 0)`

## 2004 | score=0.778 | number_theory

Let \( f: \mathbb{N} \rightarrow \mathbb{N} \) be a function such that for all natural numbers \( n \) and \( k \), the following conditions hold:
1. \( f(n + k) = f(n) + f(k) - nk \)
2. \( f(n) \) is divisible by \( n \).

Determine all possible values of \( f(2023) \).

Answer: `2023`

## 2005 | score=0.333 | calculus

In a kingdom with an unlimited number of elks and a limited number of officers, there are three types of flowers: Red Roses, Blue Lilies, and White Tulips. Elks, officers, and flowers have a relationship such that a bouquet is considered "enchanted" if it contains exactly 10 flowers, with at least one of each type. However, there is a twist: Elks can only give flowers in the morning and officers can only give flowers in the evening. Given that there are two elks and three officers, determine the number of different enchanted bouquets that can be created, considering the time constraints.

Answer: `36`

## 2006 | score=0.444 | other

In the complex plane, consider the point \(P\) at \((1,0)\). A series of points \(P_1, P_2, P_3, \ldots\) are constructed such that each point \(P_{n+1}\) is the midpoint of the segment connecting \(P_n\) and the origin, but only if \(P_n\) is not already the origin. If the process is repeated 20 times, what is the distance from the final point \(P_{20}\) to the origin?

Answer: `\frac{1}{2^{19}}`

## 2007 | score=0.444 | algebra

Let \( f(x) \) be a polynomial of degree 4 such that the equation \( f(x) = 0 \) has exactly four distinct real roots. Suppose further that the polynomial \( f(x) \) satisfies the condition \( f(x) = f(4 - x) \) for all real numbers \( x \). Given that \( f(x) \) has a double root at \( x = 1 \) and another double root at \( x = 3 \), find the sum of all possible values of \( f(2) \).

Answer: `0`

## 2008 | score=0.333 | number_theory

There exists a sequence of positive integers \(a_1, a_2, a_3, \ldots\) defined by \(a_1 = 1\) and \(a_{n+1} = a_n^2 + a_n + 1\) for all \(n \geq 1\). Determine the remainder when \(a_{100}\) is divided by 1000.

Answer: `001`

## 2009 | score=0.444 | number_theory

In the complex plane, let $S$ be the set of points $z$ such that the imaginary part of $\left(\frac{1}{2020} + z\right)^{2020}$ is a non-negative integer. Find the number of distinct values the imaginary part of $\frac{1}{2020} + z$ can take for $z \in S$.

Answer: `2020`

## 2010 | score=0.556 | algebra

Let $f: \mathbb{R}^2 \rightarrow \mathbb{R}$ be a continuously differentiable function such that $f(x,y) = xy$ for all $(x,y) \in \mathbb{R}^2$ with $x^2 + y^2 \leq 1$. Define $g: \mathbb{R} \rightarrow \mathbb{R}$ by $g(t) = f(t, \sqrt{1-t^2})$ for all $t \in [-1,1]$. Suppose that $g'(t) = 0$ for all $t \in (-1,1)$. Show that there exists a constant $C > 0$ such that $|f(x,y)| \leq C(|x| + |y|)^2$ for all $(x,y) \in \mathbb{R}^2$.

Answer: `\frac{1}{2}`

## 2011 | score=0.667 | number_theory

Consider the sequence \( \{a_n\} \) defined by \( a_1 = 1 \) and \( a_{n+1} = a_n^2 - a_n + 1 \) for \( n \geq 1 \). Prove that for any positive integer \( k \), the number \( a_{2^k} - 1 \) is divisible by \( 2^{2k} \).

Answer: `2^{2k}`

## 2012 | score=0.333 | geometry

In triangle \(ABC\), \(AB = AC\), \(D\) is the midpoint of \(BC\), and \(E\) is a point on \(AB\) such that \(DE\) is perpendicular to \(AB\). If \(DE = 12\) and the area of triangle \(ABC\) is \(240\), find the length of \(AB\).

Answer: `26`

## 2013 | score=0.667 | number_theory

Find all integer solutions \((x, y)\) for the equation \(x^3 + y^3 = 9xy + 27\) and determine the maximum value of \(x + y\).

Answer: `3`

## 2014 | score=0.444 | geometry

In the land of Geometria, there exists a peculiar triangular region $ABC$ where the angles satisfy $\angle A = 2\angle B = 4\angle C$. The area of triangle $ABC$ is exactly 24 square units. What is the length of side $AB$?

Given that all vertices of the triangle lie on the unit circle centered at the origin in the complex plane, and the vertices are represented by the complex numbers $z_A$, $z_B$, and $z_C$ respectively, with $|z_A| = |z_B| = |z_C| = 1$ and the vertices are arranged such that $z_A \cdot z_B \cdot z_C = 1$, calculate the length of side $AB$.

Answer: `4`

## 2015 | score=0.556 | geometry

Consider a complete graph with \( n \) vertices where each edge is colored either red or blue. A *monochromatic triangle* is a set of three vertices where all three edges are the same color. Determine the minimum number of monochromatic triangles that must exist in such a graph for \( n \geq 6 \). Express your answer in terms of \( n \).

Answer: `1`

## 2016 | score=0.667 | number_theory

Let $f(x)$ be a polynomial of degree 4 with integer coefficients such that $f(1) = 17$, $f(2) = 34$, $f(3) = 51$, and $f(4) = 68$. Determine the coefficient of $x^3$ in $f(x)$.

Answer: `-10`

## 2017 | score=0.778 | number_theory

Find all positive integers $n$ such that the equation $x^2 - nx + n = 0$ has integer solutions for $x$, and the sum of these solutions is equal to the product of the solutions.

Answer: `4`

## 2018 | score=0.333 | number_theory

Let \( p \) be a prime number greater than 3, and consider the set \( S = \{1, 2, 3, \ldots, p-1\} \). Define a function \( f: S \to S \) such that \( f(k) = k^2 \mod p \). Determine the number of functions \( f \) that are bijective (one-to-one and onto) on the set \( S \).

Answer: `0`

## 2019 | score=0.444 | algebra

Let \( f(x) \) be a polynomial of degree 4 with real coefficients, where \( f(x) = x^4 + ax^3 + bx^2 + cx + d \). Given that \( f(x) \) has four real roots, one of which is \( x = 1 \), and the polynomial \( g(x) = f(x) - 4 \) has roots at \( x = 2, 3, \) and \( 4 \), determine the value of \( a + b + c + d \).

Answer: `-1`

## 2020 | score=0.444 | number_theory

Let \( S \) be the set of all positive integers that are multiples of 3 but not of 5. Define a sequence \( \{a_n\} \) such that \( a_n \) is the smallest element in \( S \) that can be expressed as the sum of \( n \) distinct elements from \( S \). Find \( a_{10} \).

Answer: `189`

## 2021 | score=0.333 | combinatorics

In a mystical forest, there are 1000 distinct trees, each bearing fruits that change color each year in a unique pattern. The fruits start as red, then turn yellow, and finally become blue, after which they repeat the cycle. At the beginning of the year, a forest guardian casts a spell such that every third tree has all its fruits red, every fourth tree has all its fruits yellow, and every fifth tree has all its fruits blue. This pattern continues for the entire year, with the condition that a tree's fruits change color to blue after the second change. What is the minimum number of years that must pass so that all trees have at least one fruit that is blue?

Answer: `60`

## 2022 | score=0.333 | geometry

In a triangle \(ABC\), the sides \(AB\), \(BC\), and \(CA\) are of lengths \(a\), \(b\), and \(c\) respectively. Points \(D\) and \(E\) are on \(BC\) and \(CA\) such that \(BD = DE = EC = \frac{b}{3}\). Let \(F\) be the intersection of \(AD\) and \(BE\). Find the ratio of the area of triangle \(ADF\) to the area of triangle \(BDF\), expressed in simplest form.

Answer: `2`

## 2023 | score=0.333 | geometry

In a finite set of positive integers \( S \), each element is less than or equal to 2023, and the sum of the squares of any three distinct elements in \( S \) is not divisible by 2023. What is the maximum number of elements that \( S \) can contain?

Answer: `1012`

## 2024 | score=0.444 | number_theory

Consider a sequence of integers \((a_n)_{n=1}^{\infty}\) defined by the recurrence relation \(a_1 = 1\), \(a_2 = 2\), and for \(n \geq 3\),
\[a_n = 2a_{n-1} + 3a_{n-2}.\]
Let \(S\) be the set of all positive integers that can be expressed as the sum of distinct terms of this sequence. Determine the largest integer \(k\) such that \(k \in S\) and \(k\) is not divisible by any prime less than \(10\).

Answer: `547`

## 2025 | score=0.778 | geometry

A sequence of positive integers \((a_n)\) is defined as follows: \(a_1 = 1\), and for \(n \geq 1\), \(a_{n+1}\) is the smallest positive integer such that the sum of the first \(n+1\) terms is a perfect square. Find the smallest \(k\) such that \(a_k\) is greater than 100.

Answer: `51`

## 2026 | score=0.556 | geometry

Consider a right triangle ABC with legs of length AB = 12 cm and BC = 16 cm. Point D lies on AC such that AD : DC = 3 : 4. Construct a square DEFG with DE on line segment BC and E on AB. Find the area of the square DEFG.

Answer: `\dfrac{2304}{49}`

## 2027 | score=0.556 | number_theory

Find the smallest positive integer n such that the sum of the cubes of the first n positive integers is divisible by the product of the first n positive integers.

Answer: `1`

## 2028 | score=0.333 | geometry

In triangle \(ABC\), point \(D\) is on side \(BC\) such that \(BD:DC = 2:1\). Point \(E\) is on side \(AC\) such that \(AE:EC = 3:1\). Lines \(AD\) and \(BE\) intersect at point \(P\). If the area of triangle \(ABC\) is 100 square units, determine the ratio of the area of triangle \(APB\) to the area of triangle \(PBD\).

Answer: `2`

## 2029 | score=0.333 | geometry

There exists a convex quadrilateral $ABCD$ with side lengths $AB = a$, $BC = b$, $CD = c$, and $DA = d$, where $a, b, c, d$ are positive integers. The quadrilateral is inscribed in a circle, meaning all its vertices lie on the circumference of a single circle. It is known that the area of quadrilateral $ABCD$ is equal to the product of its two diagonals, $AC \cdot BD$. Given that $a + b + c + d = 50$, find all possible values of the diagonal $AC$.

Answer: `15`

## 2030 | score=0.444 | number_theory

Let $a$, $b$, $c$ be positive integers such that $a^2 + b^2 + c^2 = 2023$ and $ab + bc + ca = 2023$. Find the value of $a + b + c$.

Answer: `77`

## 2031 | score=0.667 | number_theory

Let \( n \) be a positive integer. Consider the set \( S = \{1, 2, \dots, n\} \). Define a sequence \( a_1, a_2, \dots, a_n \) where \( a_k \) is the number of distinct subsets of \( S \) that contain exactly \( k \) elements. Determine the value of the expression:
\[ \sum_{k=1}^{n} \binom{n}{k} a_k \]

Answer: `\binom{2n}{n} - 1`

## 2032 | score=0.444 | number_theory

Find all positive integers \( n \) for which the equation
\[ \sum_{k=1}^n \frac{1}{k} = \frac{a}{b} \]
has \( n \) and \( a \) as coprime, \( b \) as positive, and \( a < b \), with the additional constraint that \( a^2 + b^2 = n^2 + 1 \).

Provide a detailed reasoning process to prove your answer.

Answer: `1`

## 2033 | score=0.333 | geometry

Find all positive integers \( n \) such that the sum of the squares of the first \( n \) positive integers is divisible by \( n \).

Answer: `1`

## 2034 | score=0.556 | geometry

A regular hexagon $ABCDEF$ is inscribed in a circle with radius $r$. The midpoints of sides $AB$ and $CD$ are $M$ and $N$ respectively. If $MN$ is parallel to $AD$ and $BC$, find the length of $MN$ in terms of $r$.

Answer: `\frac{3r}{2}`

## 2035 | score=0.667 | geometry

In the complex plane, consider the set of points $z$ such that the product of the distances from $z$ to the points $1$, $i$, and $-1$ is equal to the square of the distance from $z$ to the point $0$. Find the area enclosed by this set of points.

Answer: `\pi`

## 2036 | score=0.333 | geometry

In the complex plane, let $A$ be the point corresponding to the complex number $z_1 = \frac{1}{2} + \frac{\sqrt{3}}{2}i$, and $B$ be the point corresponding to $z_2 = -\frac{1}{2} + \frac{\sqrt{3}}{2}i$. Let $C$ be the midpoint of the line segment $AB$. A circle $\Gamma$ is drawn with center at $C$ and passes through $A$. Let $D$ be the intersection of $\Gamma$ and the real axis, and let $E$ be the intersection of $\Gamma$ and the imaginary axis. Find the value of $|z_1^2 + z_2^2 + z_3^2|$, where $z_3 = d + ei$, $d$ and $e$ are real numbers, and $D$ and $E$ correspond to points $d$ and $e$ on the real and imaginary axes, respectively.

Answer: `1`

## 2037 | score=0.667 | geometry

Find the smallest positive integer \( n \) such that \( n^3 - 3n^2 + 2n \) is a perfect square and \( n \) is a prime number.

Answer: `2`

## 2038 | score=0.556 | geometry

A set of points in the plane is called *symmetric* if it remains unchanged after any 180-degree rotation about its center. If a *symmetric* set contains at least one point on each coordinate axis and has exactly 100 points in total, what is the minimum possible number of points that lie on the line y=x? Assume all points have integer coordinates.

Answer: `2`

