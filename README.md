# LeetCode-Problems-Crawler

Flexible Assignment of course « Web Information Processing and Application »

## Install

This is a single-file Python script and its only non-standard requirement is `requests`, so install it with `pip`.

## Run

You need to log in to LeetCode before their GraphQL endpoint is accessible.

There are two ways to provide your login credentials to the script: Either give them in environment variables `LEETCODE_USERNAME` and `LEETCODE_PASSWORD`, or run the script directly and let it prompt you to enter them.

This script lists all LeetCode problems and try to fetch them and store them in a small SQLite3 database (located at `data/data.db`), then it retrieves the problems and re-format them into the required JSON format.

## Output format

This is the required format from the TAs.

```javascript
[
  {
    "questionId": "135",                      // id
    "titleSlug": "candy",                     // 题目url
    "title": "Candy",                         // 题目标题
    "content": "<p>There are <em>N</em> ...", // 题目描述
    "difficulty": "Hard",                     // 难度
    "likes": 623,                             // 赞数
    "dislikes": 131,                          // 踩数
    "topicTags": [                            // 类比标签
      "Greedy",
      ...
    ],
    "codeSnippets": [                         // 所有语言的代码模板
      {
        "lang": "Python",                     // 语言
        "code": "class Solution(object):...", // 代码模板
      },
      ...
    ],
    "totalAccepted": 112669,                  // 通过数量
    "totalSubmission": 381432,                // 提交数量
    "solution": {
      "id": "90",                             // 解答id
      "content": "[TOC]\n\n## Solution ..."   // 解答内容
      "averageRating": 4.931,                 // 平均评分
      "votes": 29                             // 票数
    }
  },
  ...
]
```
