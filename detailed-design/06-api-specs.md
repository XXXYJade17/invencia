# 06 —— API 请求/响应 JSON 规范
> 版本：v1.0
> 日期：2026-05-24
> 依赖：architecture.md 五、02-auth.md、03-characters.md、04-game-engine.md
---
## 一、通用规范
### 1.1 响应封装
成功响应：
```json
{
  "success": true,
  "data": { ... }
}
```
错误响应：
```json
{
  "success": false,
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "用户名或密码错误"
  }
}
```
### 1.2 认证方式
- 请求头：`Authorization: Bearer <token>`
- Token 续期：响应头 X-New-Token: `<new_token>`
### 1.3 错误码一览
| HTTP 状态码 | 错误码                      | 说明       |
| -------- | ------------------------ | -------- |
| 401      | AUTH_REQUIRED            | 未提供认证凭证  |
| 401      | AUTH_EXPIRED             | 凭证已过期    |
| 401      | AUTH_INVALID_CREDENTIALS | 用户名或密码错误 |
| 403      | FORBIDDEN                | 无权访问该资源  |
| 404      | NOT_FOUND                | 资源不存在    |
| 409      | CONFLICT                 | 用户名已存在   |
| 422      | VALIDATION_ERROR         | 参数校验失败   |
| 503 | AI_UNAVAILABLE | AI 服务不可用 |
---
## 二、认证 API
### 2.1 POST /api/auth/register
请求：
```json
{
  "username": "修仙萌新",
  "password": "mypassword123",
  "password_confirm": "mypassword123"
}
```
成功响应 (201)：
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": 1,
      "username": "修仙萌新"
    }
  }
}
```
### 2.2 POST /api/auth/login
请求：
```json
{
  "username": "修仙萌新",
  "password": "mypassword123"
}
```
成功响应 (200)：
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": 1,
      "username": "修仙萌新"
    }
  }
}
```
### 2.3 POST /api/auth/refresh
请求头：`Authorization: Bearer <token>`
成功响应 (200)：
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```
---
## 三、世界 API
### 3.1 GET /api/worlds
成功响应 (200)：
```json
{
  "success": true,
  "data": {
    "worlds": [
      {
        "id": 1,
        "name": "cultivation",
        "display_name": "玄天界",
        "description": "一个名为五域的修仙世界，包含苍玄、焚天、无尘、玄冥、混元五块大陆...",
        "cover_image": "/static/images/world_cultivation.jpg",
        "tags": ["修仙", "东方玄幻", "叙事RPG"],
        "sort_order": 1
      }
    ]
  }
}
```
---
## 四、角色 API
### 4.1 GET /api/characters
查询参数：?world_id=1（可选）
成功响应 (200)：
```json
{
  "success": true,
  "data": {
    "characters": [
      {
        "id": 1,
        "name": "云逸",
        "gender": "男",
        "world_id": 1,
        "is_dead": false,
        "created_at": "2026-05-24 10:30:00"
      }
    ]
  }
}
```
### 4.2 POST /api/characters
请求：
```json
{
  "name": "云逸",
  "gender": "男",
  "world_id": 1
}
```
成功响应 (201)：
```json
{
  "success": true,
  "data": {
    "character": {
      "id": 1,
      "name": "云逸",
      "gender": "男",
      "world_id": 1,
      "infomation": {
        "realm": "刚刚踏入炼气期一重，丹田深处一缕微弱真气如风中烛火...",
        "power": "比凡人强不了多少。全力一掌能劈断碗口粗的树干...",
        "origin": "东荒青云村一户猎户家的遗腹子...",
        "location": "东荒·青云村——一座蜷缩在青牛山脚的小村落...",
        "dao_heart": "尚是一片白纸。没杀过人，没救过人...",
        "causality": "目前唯一说得上因果的，是那张兽皮卷...",
        "relationships": "村里人对你还算客气，但也仅此而已...",
        "inventory": "一身打满补丁的粗布衣，一双草鞋左脚已经开了口子...",
      },
      "is_dead": false,
      "created_at": "2026-05-24 10:30:00",
      "updated_at": "2026-05-24 10:30:00"
    }
  }
}
```
### 4.3 GET /api/characters/{id}
成功响应 (200)：
```json
{
  "success": true,
  "data": {
    "character": {
      "id": 1,
      "name": "云逸",
      "gender": "男",
      "world_id": 1,
      "infomation": { ... },
      "is_dead": false,
      "created_at": "2026-05-24 10:30:00",
      "updated_at": "2026-05-24 12:15:00"
    }
  }
}
```
---
## 五、游戏 API
### 5.1 POST /api/game/{character_id}/act
请求：
```json
{
  "content": "我决定不绕道了，握紧猎刀，朝着妖兽的方向正面走过去。虽然害怕，但这是青云村的方向——我不想绕三天远路。"
}
```
成功响应 (200)：
```json
{
  "success": true,
  "data": {
    "narrative": "云逸握紧手中那把豁了口的猎刀，刀柄上老猎户缠的麻绳早已磨得发亮。夜风从山谷深处灌出来，带着一股浓烈的腥臊——那是妖兽的气味。他深吸一口气，迈出了第一步。落叶在脚下发出细碎的咔嚓声，每一步都像踩在自己的心跳上。走出三十步后，他终于看见了它——一头形似野猪却生着三只眼的妖兽，正低垂着脑袋在溪边饮水。那第三只眼半睁半闭，眼珠转动时，云逸的丹田深处那缕微弱的真气忽然像被什么东西挑动了一下，猛地窜了一窜。他连忙稳住呼吸，将那缕躁动的真气强压下去。妖兽似乎察觉到了什么，抬起头朝他的方向看了一眼。三只眼睛同时聚焦的那一刻，云逸觉得自己的心脏停了一拍。但那妖兽只是打了个响鼻，转身拖着笨重的身躯沿溪流走远了。云逸站在原地，直到那腥臊味完全散尽才敢大口喘气。他不知道是妖兽没把他放在眼里，还是怀里那张兽皮卷起了什么他不知道的作用。但他知道一件事：如果刚才那头妖兽扑过来，他现在已经是一具尸体了。他还太弱。弱到连一头最普通的妖兽都瞧不上他。这个念头比刚才的恐惧更让人难受。",
    "hooks": [
      "刚刚丹田里那股真气为什么突然躁动？是害怕，还是感受到了什么？就地打坐探查一下，还是先赶回村里再说？",
      "那头妖兽为什么放过了自己？它闻到了什么？怀里那张兽皮卷，要不要拿出来仔细看看？",
      "妖兽走远的方向是山谷深处。要不要跟上去看看——也许它的巢穴里有什么好东西？"
    ],
    "info_changes": {
      "dao_heart": "第一次正面面对妖兽，虽然对方根本懒得动手，但那种生死之间的窒息感让云逸第一次真正意识到了自己的弱小。不是自怨自艾，而是一种清醒的刺痛——他不想再做那个被妖兽无视的人了。"
    },
    "character": {
      "id": 1,
      "name": "云逸",
      "infomation": {
        "realm": "刚刚踏入炼气期一重...",
        "dao_heart": "第一次正面面对妖兽...（已更新）",
        "..." : "..."
      }
    }
  }
}
```
### 5.2 GET /api/game/{character_id}/messages
查询参数：?before_id=50&limit=20
成功响应 (200)：
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": 31,
        "role": "user",
        "content": "我决定不绕道了...",
        "metadata": null,
        "created_at": "2026-05-24 14:30:10"
      },
      {
        "id": 32,
        "role": "assistant",
        "content": "云逸握紧手中那把豁了口的猎刀...",
        "metadata": {
          "event_type": "normal",
          "result": null
        },
        "created_at": "2026-05-24 14:30:15"
      }
    ],
    "has_more": true
  }
}
```
---
*06-api-specs.md v1.0 完成。下一步：[07-frontend.md](./07-frontend.md)。*