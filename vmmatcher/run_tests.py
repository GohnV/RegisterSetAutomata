from test_functions import *

# Basic literal match
test(r"abc", "abc", True, "exact match")
test(r"abc", "ab", False, "partial missing char")
test(r"abc", "abcd", True, "prefix match")

# Anchors
test(r"^abc$", "abc", True, "exact anchored match")
test(r"^abc$", "abcc", False, "extra char at end")
test(r"^abc$", "xabc", False, "extra char at start")

# Dot wildcard
test(r"a.c", "abc", True, "dot matches one char")
test(r"a.c", "a c", True, "dot matches space")
test(r"a.c", "ac", False, "dot requires one char")

# Quantifiers *
test(r"ab*c", "ac", True, "* zero occurrences")
test(r"ab*c", "abc", True, "* one occurrence")
test(r"ab*c", "abbbc", True, "* multiple occurrences")

# Quantifiers +
test(r"ab+c", "ac", False, "+ requires at least one")
test(r"ab+c", "abc", True, "+ one occurrence")
test(r"ab+c", "abbbc", True, "+ multiple occurrences")

# Quantifiers ?
test(r"ab?c", "ac", True, "? zero occurrence")
test(r"ab?c", "abc", True, "? one occurrence")
test(r"ab?c", "abbc", False, "? too many")

# Bounded repetition
test(r"ab{3,5}c", "ac", False, "{3,5} no repetitions")
test(r"ab{3,5}c", "abc", False, "{3,5} 1 repetition")
test(r"ab{3,5}c", "abbc", False, "{3,5} 2 repetitions")
test(r"ab{3,5}c", "abbbc", True, "{3,5} 3 repetitions")
test(r"ab{3,5}c", "abbbbc", True, "{3,5} 4 repetitions")
test(r"ab{3,5}c", "abbbbbc", True, "{3,5} 5 repetitions")
test(r"ab{3,5}c", "abbbbbbc", False, "{3,5} 6 repetitions")
test(r"ab{3,5}c", "abbbbbbbc", False, "{3,5} 7 repetitions")

# Character classes
test(r"[abc]", "a", True, "char class single")
test(r"[abc]", "d", False, "char class negative")
test(r"[a-z]", "m", True, "range match")
test(r"[a-z]", "M", False, "range case sensitive")

# Negated classes
test(r"[^abc]", "d", True, "negated class match")
test(r"[^abc]", "a", False, "negated class fail")

# Escaping
test(r"\.", ".", True, "escaped dot")
test(r"\.", "a", False, "escaped dot mismatch")

# Digits / shorthand
test(r"\d+", "123", True, "digit match")
test(r"\d+", "abc", False, "digit fail")

# Word characters
test(r"\w+", "abc123_", True, "word chars")
test(r"\w+", "!!!", False, "non word chars")

# Whitespace
test(r"\s+", "   ", True, "spaces match")
test(r"\s+", "a", False, "no whitespace")

# Alternation
test(r"cat|dog", "cat", True, "alt first")
test(r"cat|dog", "dog", True, "alt second")
test(r"cat|dog", "cow", False, "alt fail")

# Grouping
test(r"(ab)+", "ab", True, "group once")
test(r"(ab)+", "abab", True, "group repeated")
test(r"^(ab)+$", "aba", False, "incomplete group")

# Complex combo
test(r"^\d{3}-\d{2}-\d{4}$", "123-45-6789", True, "ssn format valid")
test(r"^\d{3}-\d{2}-\d{4}$", "12-345-6789", False, "ssn format invalid")

# Greedy behavior (basic expectation)
test(r"a.*c", "abbbbbc", True, "greedy match")
test(r"a.*c", "ac", True, "greedy zero middle")
test(r"a.*c", "abbbb", False, "missing end char")

#BACK-REFERENCES

# With unicode
test(r"(.).*\1", "aa", True, "repeat easy")
test(r"(.).*\1", "ČčaařŘ", True, "repeat 2")
test(r"(.).*\1", "Čča🍔🎆ařŘ", True, "repeat 3")
test(r"([^🍔]).*\1", "Čča🍔🎆ařŘ", True, "repeat negative class")
test(r"([^🍔]).*\1", "Čča🍔🎆řŘ", False, "repeat negative class fail")

# Back-references: basic single char
test(r"(.)\1", "aa", True, "simple double char")
test(r"(.)\1", "ab", False, "different chars")

# Back-ref with wildcard
test(r"(.)\1\1", "aaa", True, "triple same char")
test(r"(.)\1\1", "aab", False, "last char differs")

# Back-ref anywhere in string
test(r"a(.)\1c", "abbc", True, "middle repeated char")
test(r"a(.)\1c", "abcc", False, "wrong repetition")

# Character class capture + back-ref
test(r"([abc])\1", "aa", True, "class back-ref match")
test(r"([abc])\1", "bb", True, "class back-ref match 2")
test(r"([abc])\1", "dd", False, "outside class")

# Mixed literals + back-ref
test(r"x(.)\1x", "xzzx", True, "wrapped repeat")
test(r"x(.)\1x", "xzax", False, "not repeated")

# Multiple back-references (same group)
test(r"(.)a\1", "bab", True, "same char around literal")
test(r"(.)a\1", "bac", False, "end mismatch")

# Anchored back-ref
test(r"^(.)\1$", "cc", True, "anchored double")
test(r"^(.)\1$", "ccc", False, "too long")

# Back-ref with quantifiers applied to group
test(r"(.)\1+", "aaaa", True, "one or more repeats")
test(r"(.)\1+", "ab", False, "no repetition")

# Back-ref inside longer pattern
test(r"(.)b\1b\1", "ababa", True, "alternating repeat")
test(r"(.)b\1b\1", "ababb", False, "breaks pattern")

# Back-ref with dot and anchors
test(r"^(.)..\1$", "abca", True, "same start and end")
test(r"^(.)..\1$", "abcd", False, "end mismatch")

# Character class + structure
test(r"^([xyz])\1$", "xx", True, "class anchored match")
test(r"^([xyz])\1$", "xy", False, "not repeated")

# Back-ref with optional noise between
test(r"(.)\1?c", "aac", True, "optional duplicate present")
test(r"(.)\1?c", "ac", True, "optional duplicate absent")
test(r"^(.)\1?c", "abc", False, "wrong structure")

# Edge: minimal usage
test(r"(.)\1", "", False, "empty string")
test(r"(.)\1", "a", False, "single char only")
