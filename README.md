# 马剃天爱星制品图鉴

这是一套以 `JSON + 独立图片` 保存的静态制品图鉴。公共商品资料与个人收藏记录分开存储，更新目录时不会覆盖用户的收藏状态。

## 本地运行

```bash
cd basori-tiara-catalog
python3 -m http.server 4173
```

然后访问 `http://localhost:4173/`。由于页面使用 `fetch()` 读取 JSON，不要直接双击 `index.html`。

## 数据存在哪里

| 内容 | 位置 | 说明 |
| --- | --- | --- |
| 制品目录 | `data/catalog.json` | 商品名称、分类、价格、发售方式、来源等公共资料 |
| 数据格式 | `data/catalog.schema.json` | `catalog.json` 的 JSON Schema 约束 |
| 商品原图 | `images/items/` | 详情页使用的本地图片，路径记录在 `images[].path` |
| 列表缩略图 | `images/thumbs/` | 列表页使用的 WebP 小图，路径记录在 `images[].thumbnail_path` |
| 个人收藏 | 浏览器 `localStorage` | 键名为 `basori-tiara-catalog-collection-v1`，保存“我有/想要”、数量、入手价和备注 |

个人收藏不会写回 `catalog.json`。它只存在于当前浏览器和当前站点地址下，可以通过页面上的“导出”按钮备份为 `basori-tiara-collection.json`。

## 存储示例

`data/catalog.json` 中的一件制品：

```json
{
  "id": "example-acrylic-stand-tiara",
  "name_ja": "馬剃天愛星 アクリルスタンド",
  "name_zh": "马剃天爱星亚克力立牌",
  "category": "acrylic_stand",
  "campaign": "示例联动",
  "campaign_year": 2026,
  "manufacturer": "示例厂商",
  "variant": "马剃天爱星",
  "sale_format": {
    "type": "single",
    "total_variants": null
  },
  "spec": {
    "size": "约 150 mm",
    "material": "亚克力"
  },
  "release_date": "2026-10-01",
  "list_price_yen": 1650,
  "official_status": "official",
  "verification": "confirmed_text",
  "images": [
    {
      "path": "images/items/example-acrylic-stand-tiara.jpg",
      "role": "product",
      "source_url": "https://example.com/product-image.jpg"
    }
  ],
  "sales": [
    {
      "seller": "示例商店",
      "phase": "general_sale",
      "url": "https://example.com/product"
    }
  ],
  "sources": [
    {
      "url": "https://example.com/product",
      "type": "official",
      "checked_at": "2026-10-01"
    }
  ],
  "tags": ["联动", "立牌"],
  "notes": null
}
```

浏览器中对应的个人收藏记录：

```json
{
  "version": 1,
  "items": {
    "example-acrylic-stand-tiara": {
      "status": "owned",
      "quantity": 1,
      "paid_price_yen": 1650,
      "acquired_from": "示例商店",
      "acquired_at": "2026-10-01",
      "note": "线下活动购入"
    }
  }
}
```

## 维护资料

- 一条 `item` 代表一件能被收藏者区分的天爱星制品或图案。
- 同一制品的先行销售、通贩和再贩写入同一条记录的 `sales`。
- 图片保存在 `images/items/`，JSON 只保存相对路径与原图来源。
- 缺失字段使用 `null`，不使用空字符串或“未知”。
- 商品 ID 一旦发布就不要修改，否则会断开用户已保存的收藏记录。

本次资料补充可以重复执行；脚本会按商品 ID 合并，不会重复追加：

```bash
python3 tools/enrich_catalog.py
python3 tools/enrich_catalog.py --download
```

第二条命令会把缺失的商品图归档到 `images/items/`。数据来源包括版权方或厂商页面、官方新闻稿、官方卡牌数据库，以及 Animate、Gamers、AmiAmi 等授权销售页；仅能从销售页确认的条目会标成 `seller_claim`。

新增或替换原图后，重新生成列表缩略图：

```bash
python3 tools/generate_thumbnails.py
```

## 校验

```bash
python3 tools/validate_catalog.py
```

`data/catalog.schema.json` 可供编辑器或后续的 JSON Schema 校验工具使用。
