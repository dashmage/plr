"""
49. Group Anagrams
Medium

Given an array of strings strs, group the anagrams together. You can return the answer in any order.
An Anagram is a word or phrase formed by rearranging the letters of a different word or phrase, typically using all the original letters exactly once.
 
Example 1:
Input: strs = ["eat","tea","tan","ate","nat","bat"]
Output: [["bat"],["nat","tan"],["ate","eat","tea"]]
Example 2:
Input: strs = [""]
Output: [[""]]
Example 3:
Input: strs = ["a"]
Output: [["a"]]
 
Constraints:

1 <= strs.length <= 104
0 <= strs[i].length <= 100
strs[i] consists of lowercase English letters.


"""

from collections import defaultdict


class Solution:
    def groupAnagrams(self, strs: list[str]) -> list[list[str]]:
        # sorted letters mapped to all the words that can be formed from it
        anagram_map = defaultdict(list)
        for word in strs:
            sorted_word = "".join(sorted(word))
            anagram_map[sorted_word].append(word)
        return list(anagram_map.values())


def validate(actual, expected):
    actual = sorted([sorted(elem) for elem in actual], key=lambda x: len(x))
    return actual == expected
