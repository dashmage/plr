"""
347. Top K Frequent Elements
Medium

Given an integer array nums and an integer k, return the k most frequent elements. You may return the answer in any order.
 
Example 1:
Input: nums = [1,1,1,2,2,3], k = 2
Output: [1,2]
Example 2:
Input: nums = [1], k = 1
Output: [1]
Example 3:
Input: nums = [4,1,-1,2,-1,2,3], k = 2
Output: [2,-1]
Example 4:
Input: nums = [1,2,2,3,3,3,3], k = 2
Output: [3,2]
 
Constraints:

1 <= nums.length <= 105
-104 <= nums[i] <= 104
k is in the range [1, the number of unique elements in the array].
It is guaranteed that the answer is unique.

 
Follow up: Your algorithm's time complexity must be better than O(n log n), where n is the array's size.

"""

from collections import defaultdict


class Solution:
    # sorting through count values in dict
    # O(nlogn)
    def topKFrequent(self, nums: list[int], k: int) -> list[int]:
        count = defaultdict(int)
        for n in nums:
            count[n] += 1

        return sorted(count, key=lambda x: count[x], reverse=True)[:k]

    # bucket sort with freq as index
    # thanks NeetCode, https://youtu.be/YPTqKIgVk-k?si=UqXaqjvCXi5xnCAy
    # O(n)
    def topKFrequent_efficient(self, nums: list[int], k: int) -> list[int]:
        count = defaultdict(int)
        for n in nums:
            count[n] += 1

        # stores the freq of element at each index
        # eg: index 3 will have a list of elements with count 3
        freq = [[] for _ in range(len(nums) + 1)]
        for n, c in count.items():
            freq[c].append(n)

        topk = []
        for i in range(len(freq) - 1, 0, -1):
            for n in freq[i]:
                topk.append(n)
                if len(topk) == k:  # guaranteed to execute
                    return topk


def validate(actual, expected):
    from collections import Counter

    return Counter(actual) == Counter(expected)
