# LeetCode-Problems-Crawler

Flexible Assignment of course « Web Information Processing and Application »

## Output format

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
