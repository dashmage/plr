# Overview
`plr`(python-leetcode-runner) is a tool to fetch [LeetCode](https://leetcode.com) problems (using the problem title slug) and then to test your solutions.

A lot of code logic has been lifted from the wonderful [leetcode-runner project](https://github.com/fbjorn/leetcode-runner).
- `fetcher.py`: To execute the GraphQL query on the public API and get the problem details.
- `models.py`: Pydantic models for the problem data obtained.
- `generator.py`: To generate the template for the python solution file that's created.

Some of my improvements include,
- A new `test` subcommand instead of calling the class method in the solution file.
- Supports testing with multiple solutions for a problem.
- Specify your own custom methods for more complex testing scenarios required for certain problems.
- Shorter name 😉

Note: This project is still a work in progress.

# Installation
[pipx](https://pipx.pypa.io/stable) makes it super easy to get started with using `plr` in an isolated environment.

```sh
pipx install git+https://github.com/dashmage/plr.git
```

You might need to add `~/.local/bin` to your PATH in case calling `plr` doesn't work.
```sh
echo "export PATH=$PATH:~/.local/bin" >> ~/.bashrc
source ~/.bashrc
```

Otherwise, you can also install the package with `pip` (preferably in a virtual environment).
```sh
python3 -m venv venv
source venv/bin/activate
pip install git+https://github.com/dashmage/plr.git#egg=plr
```

# Usage
From the LeetCode problem URL, obtain the title slug name. For the [two sum problem](https://leetcode.com/problems/two-sum/), that would be `two-sum`.

Now run,
```sh
$ plr pull two-sum

1-two-sum.py has been created! Happy solving
```
This fetches the problem description and python starter code and adds into the newly created `1-two-sum.py` python file. `1` is the problem ID for the two sum problem.

After coding up a solution and adding it to the `Solution` class, run the `plr test` command to validate it against the example test cases.
```sh
$ plr test two-sum
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

## Advanced Usage
Certain problems require more steps to be performed either while evaluating and returning the actual results from the solution method or while validating whether the results are as expected.

For these situations, you can optionally define two methods outside the `Solution` class, namely `evaluate` and `validate`.

The `evaluate` method comes in handy when you need to alter the results returned by the solution method. This can happen when the expected results also check the value of the input array which changes in-place.

Example: Problem #26, remove duplicates from sorted array. Here, we need to evaluate the number of unique elements and return that along with the input array as a tuple.
```python
def evaluate(method, kwargs):
    result = method(**kwargs)
    return result, kwargs["nums"][:result]
```

The `validate` method can be defined when you need to explicitly specify how to compare the actual and expected test case results. By default, this is checked simply by running `actual == expected`. But in some problems, say, where the order of elements in the expected array can be ignored, you cannot directly compare their values.

Example: Problem #347, top k frequent elements. In this problem, we're expected to return the top k frequent elements as a list in any order. So `Counters` can be used to ignore the sort order but still preserve duplicates during the comparison between the lists.
```python
def validate(actual, expected):
    from collections import Counter
    return Counter(actual) == Counter(expected)
```

Take a look at the [solved LeetCode problems provided in the repo](https://github.com/dashmage/plr/tree/main/tests/problems) some of which utilize these methods for testing.

# Development

Ensure you have `poetry` installed. Clone the repo, change into the created directory, run `poetry shell` and you're good to go.

Tests can be executed with `poetry run pytest -v`
