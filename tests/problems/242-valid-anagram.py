"""
242. Valid Anagram
Easy

Given two strings s and t, return true if t is an anagram of s, and false otherwise.
An Anagram is a word or phrase formed by rearranging the letters of a different word or phrase, typically using all the original letters exactly once.
 
Example 1:
Input: s = "anagram", t = "nagaram"
Output: true
Example 2:
Input: s = "rat", t = "car"
Output: false

 
Constraints:

1 <= s.length, t.length <= 5 * 104
s and t consist of lowercase English letters.

 
Follow up: What if the inputs contain Unicode characters? How would you adapt your solution to such a case?

"""

from collections import defaultdict


def get_letter_count(s: str) -> dict[str, int]:
    letter_count = defaultdict(int)
    for c in s:
        letter_count[c] += 1
    return letter_count


class Solution:
    def isAnagram(self, s: str, t: str) -> bool:
        if get_letter_count(s) == get_letter_count(t):
            return True
        return False
