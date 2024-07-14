"""
217. Contains Duplicate
Easy

Given an integer array nums, return true if any value appears at least twice in the array, and return false if every element is distinct.
 
Example 1:
Input: nums = [1,2,3,1]
Output: true
Example 2:
Input: nums = [1,2,3,4]
Output: false
Example 3:
Input: nums = [1,1,1,3,3,4,3,2,4,2]
Output: true

 
Constraints:

1 <= nums.length <= 105
-109 <= nums[i] <= 109


"""


class Solution:
    # O(nlogn)
    def containsDuplicate_sort(self, nums: list[int]) -> bool:
        temp = sorted(nums)
        for i in range(1, len(temp)):
            if temp[i - 1] == temp[i]:
                return True
        return False

    # O(n)
    def containsDuplicate_set(self, nums: list[int]) -> bool:
        uniq_elements = set()
        for n in nums:
            if n in uniq_elements:
                return True
            else:
                uniq_elements.add(n)
        return False
