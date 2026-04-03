# Overview
`plr`(python-leetcode-runner) is a tool to fetch [LeetCode](https://leetcode.com) problems (using the problem title slug) and then to test your solutions.

`plr` handles the most common custom-judge cases directly from the docstring, so you usually do not need to add extra helper functions to the solution file.

# Installation
Use [uv](https://docs.astral.sh/uv) to install and manage `plr`.

```sh
uv tool install git+https://github.com/dashmage/plr.git
```

# Usage
From the LeetCode problem URL, obtain the title slug name. For the [two sum problem](https://leetcode.com/problems/two-sum/), that would be `two-sum`.

Now run,
```sh
$ plr pull two-sum
# Or even directly with: uv run plr pull two-sum

001-two-sum.py has been created! Happy solving
```
This fetches the problem description and python starter code and adds into the newly created `001-two-sum.py` python file. `001` is the zero-padded problem ID for the two sum problem.

After coding up a solution and adding it to the `Solution` class, run the `plr test` command with the path to the problem file to validate it against the example test cases.
```sh
$ plr test 001-two-sum.py
# Or: python -m plr test 001-two-sum.py
```

This will test the `Solution` class method(s) with the examples automatically parsed from the problem description in the docstring.


## Multiple Solutions
You can even provide multiple solution methods in the `Solution` class and each of them would be validated with the example test cases.

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

## Extra Test Cases
Extra test cases can easily be added by appending a new "Example" in the problem description. This additional test will be picked up by the test validator.

```
Example 5:
Input: nums = [1,2,3], k = 2
Output: [1,2]
```

## In-Place Array Problems
When the output includes a returned value and a mutated input array, `plr` treats that as an in-place prefix check automatically.

For example, in [Problem #26](https://leetcode.com/problems/remove-duplicates-from-sorted-array/), duplicates are to be removed from a sorted array. For testing solutions to this problem, we need to evaluate the number of unique elements and return that along with the input array as a tuple.

Here is what a sample input and output look like,
```
Input: nums = [1,1,2]
Output: 2, nums = [1,2,_]
Explanation: Your function should return k = 2, with the first two elements of nums being 1 and 2 respectively.
It does not matter what you leave beyond the returned k (hence they are underscores).
```

`plr` will call the solution, read the returned `k`, and compare `nums[:k]` against the non-underscore prefix from the expected output.

## Inferred Comparison Rules
For problems where equality is not a simple `actual == expected`, `plr` infers the right comparison mode directly from the problem text.

It currently detects:
- order-insensitive flat lists when the problem says the answer can be returned in any order
- order-insensitive nested lists for cases like `3Sum` and grouped anagrams
- order-insensitive in-place prefix checks for custom-judge problems such as `Remove Element`

For example, in [Problem #347](https://leetcode.com/problems/top-k-frequent-elements/), the answer can be returned in any order:
```
Input: nums = [1,1,1,2,2,3], k = 2
Output: [1,2]
```

For nested outputs such as `3Sum` or grouped anagrams:
```
Input: nums = [-1,0,1,2,-1,-4]
Output: [[-1,-1,2],[-1,0,1]]
```

For [Problem #27](https://leetcode.com/problems/remove-element/), where the first `k` mutated elements may be in any order:
```
Input: nums = [3,2,2,3], val = 3
Output: 2, nums = [2,2,_,_]
```

Take a look at the [solved LeetCode problems provided in the repo](https://github.com/dashmage/plr/tree/main/tests/problems) for concrete examples.

# Development

Install the project with the test extra into your local environment.
```sh
uv sync --extra test
```

For a live editable install in a virtualenv:
```sh
uv venv
source .venv/bin/activate
uv pip install -e .
```

This makes the local `plr` command use your current checkout, so code changes are reflected immediately.

Run the test suite with:
```sh
uv run --extra test pytest -q
```

Run type checking with `ty`:
```sh
ty check
```

For a one-off local CLI install without activating a venv:
```sh
uv tool install --force .
```
