# Overview
`plr`(python-leetcode-runner) is a tool to fetch [LeetCode](https://leetcode.com) problems (using the problem title slug) and then to test your solutions.

Code logic has mostly been lifted from the [leetcode-runner project](https://github.com/fbjorn/leetcode-runner).
This includes,
- `fetcher.py`: To execute the GraphQL query on the public API and get the problem details.
- `models.py`: Pydantic models for the problem data obtained.
- `generator.py`: To generate the template for the python solution file that's created.
- `runner.py`: To run tests and validate the solution.

Here are some of the changes I've made,
- Add a new `test` subcommand instead of calling the class method in the solution file.
- Remove `colorama`, `termcolor` dependencies in favour of directly using `rich`.
- Supports testing with multiple solutions for a problem.
- Other small things like naming changes, removing the `PROBLEM` variable and directly fetching it from the docstring, extra error handling.

# Installation
Currently, you'll need to clone the git repository and install it with [poetry](https://python-poetry.org/).

```sh
poetry install
```

# Usage
In order to fetch the problem details, run

```sh
$ plr pull two-sum

1-two-sum.py has been created! Happy solving
```
This will fetch the [two sum problem](https://leetcode.com/problems/two-sum/) and write the problem details and python starter code into `1-two-sum.py` file where `1` is the problem ID.

After figuring out a solution, run
```sh
$ plr test two-sum
```

This will test the `Solution` class method with the examples from the problem automatically. You can provide extra test cases if required.

Multiple methods can be defined in the Solution class and each would be tested with the example test cases.

```sh
=== twoSum_1 ===

[ OK ]
nums = [2,7,11,15], target = 9
Expected: [0, 1]
Actual  : [0, 1]
------------------------------
[ OK ]
nums = [3,2,4], target = 6
Expected: [1, 2]
Actual  : [1, 2]
------------------------------
[ OK ]
nums = [3,3], target = 6
Expected: [0, 1]
Actual  : [0, 1]
------------------------------

Passed: 3/3

=== twoSum_2 ===

[ FAILED ]
nums = [2,7,11,15], target = 9
Expected: [0, 1]
Actual  : [1, 2, 3]
------------------------------
[ FAILED ]
nums = [3,2,4], target = 6
Expected: [1, 2]
Actual  : [1, 2, 3]
------------------------------
[ FAILED ]
nums = [3,3], target = 6
Expected: [0, 1]
Actual  : [1, 2, 3]
------------------------------

Passed: 0/3

```

# TODO
- Write tests
- Allow for custom tests (eg: for problem 26, remove duplicates from sorted array)
- Publish on PyPI
