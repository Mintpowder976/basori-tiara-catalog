#!/usr/bin/env python3
"""Merge the researched supplement into catalog.json and optionally fetch images."""

from __future__ import annotations

import argparse
import json
import mimetypes
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "catalog.json"
CHECKED_AT = "2026-10-01"


def item(
    item_id: str,
    name_ja: str,
    name_zh: str,
    category: str,
    campaign: str,
    year: int,
    manufacturer: str,
    price: int | None,
    image_url: str,
    source_url: str,
    *,
    variant: str = "马剃天爱星",
    sale_type: str = "single",
    total_variants: int | None = None,
    size: str | None = None,
    material: str | None = None,
    release_date: str | None = None,
    verification: str = "confirmed_text",
    source_type: str = "official",
    role: str = "product",
    tags: list[str] | None = None,
    notes: str | None = None,
    phase: str = "general_sale",
    seller: str | None = None,
) -> dict:
    suffix = Path(image_url.split("?", 1)[0]).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ".jpg"
    image_path = f"images/items/{item_id}{suffix}"
    return {
        "id": item_id,
        "name_ja": name_ja,
        "name_zh": name_zh,
        "category": category,
        "campaign": campaign,
        "campaign_year": year,
        "manufacturer": manufacturer,
        "variant": variant,
        "sale_format": {"type": sale_type, "total_variants": total_variants},
        "spec": {"size": size, "material": material},
        "release_date": release_date,
        "list_price_yen": price,
        "official_status": "official",
        "verification": verification,
        "images": [{"path": image_path, "role": role, "source_url": image_url}],
        "sales": [{"seller": seller or manufacturer, "phase": phase, "url": source_url}],
        "sources": [{"url": source_url, "type": source_type, "checked_at": CHECKED_AT}],
        "tags": tags or [],
        "notes": notes,
    }


POST_IMG = "https://d1bdgtbdniw5kz.cloudfront.net/img/goods/L/"
GAMERS_IMG = "https://tc-gamers.techorus-cdn.com/resize_image/resize_image.php?image="
ANIMATE_IMG = "https://tc-animate.techorus-cdn.com/resize_image/resize_image.php?image="
PR_IMG = "https://prcdn.freetls.fastly.net/release_image/16064/"

# Images for records which were already present but had no locally archived image.
EXISTING_IMAGES = {
    "tosyo-winter-stand-tiara": (POST_IMG + "CS9983402141.jpg", "https://www.shop.post.japanpost.jp/shop/g/gCS9983402141/"),
    "tosyo-winter-keychain-tiara": (POST_IMG + "CS9983402153.jpg", "https://www.shop.post.japanpost.jp/shop/g/gCS9983402153/"),
    "tosyo-winter-stamp-tiara": (POST_IMG + "CS9983402165.jpg", "https://www.shop.post.japanpost.jp/shop/g/gCS9983402165/"),
    "tosyo-winter-bookmarker-tiara": (POST_IMG + "CS9983402178.jpg", "https://www.shop.post.japanpost.jp/shop/g/gCS9983402178/"),
    "tosyo-coaster-tiara": (POST_IMG + "CS9983402129.jpg", "https://www.shop.post.japanpost.jp/shop/g/gCS9983402129/"),
    "tosyo-mug-tiara": (POST_IMG + "CS9983402126.jpg", "https://www.shop.post.japanpost.jp/shop/g/gCS9983402126/"),
    "thechara-valentine-stand-tiara": (GAMERS_IMG + "01271417_69784a5236669.jpg&width=1200&height=630", "https://www.gamers.co.jp/pn/pd/10870407/"),
    "thechara-valentine-keychain-tiara": (GAMERS_IMG + "01271415_697849e50c89a.jpg&width=1200&height=630", "https://www.gamers.co.jp/pn/pd/10870399/"),
    "thechara-valentine-microfiber-tiara": (GAMERS_IMG + "01271419_69784acc097af.jpg&width=1200&height=630", "https://www.gamers.co.jp/pn/pd/10870416/"),
    "thechara-valentine-tapestry-tiara": (GAMERS_IMG + "01271427_69784cc0c73a0.jpg&width=1200&height=630", "https://www.gamers.co.jp/pn/pd/10870426/"),
    "thechara-pale-stand-tiara": (GAMERS_IMG + "06181258_6a336cf3d1124.jpg&width=1200&height=630", "https://www.gamers.co.jp/pn/pd/10907454/"),
    "thechara-pale-keychain-tiara": (GAMERS_IMG + "06181251_6a336b4d4daa3.jpg&width=1200&height=630", "https://www.gamers.co.jp/pn/pd/10907447/"),
    "thechara-pale-microfiber-tiara": (GAMERS_IMG + "06181312_6a3370175c9d5.jpg&width=1200&height=630", "https://www.gamers.co.jp/pn/pd/10907464/"),
}


ITEMS: list[dict] = []


def add(*args, **kwargs) -> None:
    ITEMS.append(item(*args, **kwargs))


# Animate indexed products: kemomimi parka, CS.FRONT /09, Suzuki Haruka and Eterno Recit.
for row in [
    ("keyth-kemomimi-stand-tiara", "アクリルスタンド 馬剃天愛星 けもみみパーカー", "兽耳连帽衫亚克力立牌", "acrylic_stand", 1210, "4580883060064_1_1780052727.jpg", "3496857"),
    ("keyth-kemomimi-keychain-tiara", "アクリルキーホルダー 馬剃天愛星 けもみみパーカー", "兽耳连帽衫亚克力挂件", "acrylic_keychain", 990, "4580883060149_1_1780052717.jpg", "3496865"),
    ("keyth-kemomimi-block-tiara", "ダイカットアクリルブロック 馬剃天愛星 けもみみパーカー", "兽耳连帽衫异形亚克力砖", "acrylic_art", 990, "4571608539972_1_1780052721.jpg", "3496849"),
]:
    iid, ja, zh, cat, price, image, pid = row
    source = f"https://www.animate-onlineshop.jp/pn/pd/{pid}/"
    add(iid, ja, zh, cat, "けもみみパーカー", 2026, "Key-th / カーテン魂", price, ANIMATE_IMG + image + "&width=400&height=400&square=1", source, material="アクリル", source_type="seller", tags=["兽耳", "连帽衫"])

for row in [
    ("csfront-09-sticker-tiara", "ステッカー /09 馬剃天愛星", "CS.FRONT /09 贴纸", "sticker", 330, "4582689112701_1_1770289512.jpg", "3395390"),
    ("csfront-09-shaker-tiara", "シャカシャカキーホルダー /09 馬剃天愛星", "CS.FRONT /09 摇摇挂件", "acrylic_keychain", 1650, "4582689112619_1_1770289504.jpg", "3395381"),
    ("csfront-09-diorama-tiara", "アクリルジオラマ /09 馬剃天愛星", "CS.FRONT /09 亚克力场景", "acrylic_art", 1980, "4582689112527_1_1770289513.jpg", "3395372"),
    ("csfront-09-passcase-tiara", "レザーパスケース /09 馬剃天愛星", "CS.FRONT /09 皮革卡套", "accessory", 990, "4582689112848_1_1770289505.jpg", "3395400"),
]:
    iid, ja, zh, cat, price, image, pid = row
    source = f"https://www.animate-onlineshop.jp/pn/pd/{pid}/"
    add(iid, ja, zh, cat, "CS.FRONT", 2026, "CS.FRONT", price, ANIMATE_IMG + image + "&width=400&height=400&square=1", source, source_type="seller", tags=["09号", "单人"])

add("suzuki-haruka-stand-tiara", "鈴木ハルカ アクリルスタンド 馬剃天愛星", "铃木遥香绘亚克力立牌", "acrylic_stand", "鈴木ハルカ イラスト", 2026, "鈴木ハルカ", 1210, ANIMATE_IMG + "4571694210083_1_1762945511.jpg&width=400&height=400&square=1", "https://www.animate-onlineshop.jp/pn/pd/3306412/", material="アクリル", source_type="seller", tags=["铃木遥香", "单人"])

for row in [
    ("eternorecit-stand-keyholder-tiara", "アクリルスタンドキーホルダー 馬剃天愛星", "Eterno Recit 亚克力立牌挂件", "acrylic_stand", 990, "10141818_68ee15618ba36.jpg", "3277891"),
    ("eternorecit-keychain-tiara", "アクリルキーホルダー 馬剃天愛星", "Eterno Recit 亚克力挂件", "acrylic_keychain", 880, "4582636976783_1_1759982710.jpg", "3277899"),
    ("eternorecit-stickers", "フレークシールセット 全8種", "Eterno Recit 8款散装贴纸套装", "sticker", 770, "4582636976622_1_1759982706.jpg", "3277883"),
    ("eternorecit-trading-badge", "トレーディング缶バッジ 全8種", "Eterno Recit 随机徽章 天爱星款", "can_badge", 550, "4582636976516_1_1759982704.jpg", "3277872"),
]:
    iid, ja, zh, cat, price, image, pid = row
    source = f"https://www.animate-onlineshop.jp/pn/pd/{pid}/"
    random = "trading" in iid
    add(iid, ja, zh, cat, "Eterno Récit", 2025, "Eterno Récit", price, ANIMATE_IMG + image + "&width=400&height=400&square=1", source, variant="套装内含天爱星" if "stickers" in iid else "马剃天爱星", sale_type="random" if random else "set" if "stickers" in iid else "single", total_variants=8 if random else None, source_type="seller", role="lineup" if random or "stickers" in iid else "product", tags=["随机"] if random else ["套装"] if "stickers" in iid else ["单人"])

# Key-th group goods from the same kemomimi-parka lineup.
KEYTH = "https://www.curtain-damashii.com"
for row in [
    ("keyth-kemomimi-noren", "のれん けもみみパーカー", "兽耳连帽衫门帘", "fabric_goods", 3960, "noren_makeine03", "noren_makeine03_2.jpg", "single", None),
    ("keyth-kemomimi-tshirt", "Tシャツ けもみみパーカー", "兽耳连帽衫 T 恤", "apparel", 3300, "tshirt_makeine03", "tshirt_makeine03_1.jpg", "single", None),
    ("keyth-kemomimi-tote", "トートバッグ けもみみパーカー", "兽耳连帽衫托特包", "bag", 1980, "totebag_makeine03", "totebag_makeine03_1.jpg", "single", None),
    ("keyth-kemomimi-rubbermat", "ラバーマット けもみみパーカー", "兽耳连帽衫橡胶桌垫", "stationery", 3300, "rubbermat_makeine03", "rubbermat_makeine03_1.jpg", "single", None),
    ("keyth-kemomimi-badge", "トレーディング缶バッジ けもみみパーカー", "兽耳连帽衫随机徽章 天爱星款", "can_badge", 495, "badgebox_makeine03", "badgebox_makeine03_1.jpg", "random", 8),
]:
    iid, ja, zh, cat, price, slug, image, sale, variants = row
    source = f"{KEYTH}/item/{slug}/"
    add(iid, ja, zh, cat, "けもみみパーカー", 2026, "Key-th / カーテン魂", price, f"{KEYTH}/index_ag/wp/wp-content/uploads/{image}", source, variant="集合图内含天爱星" if sale == "single" else "马剃天爱星", sale_type=sale, total_variants=variants, role="lineup", tags=["兽耳", "群像"])

# TOSYO winter-uniform group products.
add("tosyo-winter-badge", "缶バッジコンプリートセット 冬制服", "冬制服徽章全套（含天爱星）", "can_badge", "冬制服", 2025, "TOSYO / 郵便局物販サービス", 7150, POST_IMG + "CS9983402166.jpg", "https://www.shop.post.japanpost.jp/shop/g/gCS9983402166/", variant="13枚套装内含天爱星", sale_type="set", total_variants=13, size="直径约56mm", material="ブリキ", role="lineup", tags=["冬制服", "套装"], notes="12款普通徽章各1枚，另附1枚随机闪粉特别版。")
add("tosyo-winter-b2-tapestry", "B2横タペストリー 冬制服", "冬制服 B2 横向挂毯", "tapestry", "冬制服", 2025, "TOSYO", 3300, "https://tosyo-goods.jp/cdn/shop/files/tbhtpmho0002_1.jpg?v=1763439332&width=1946", "https://tosyo-goods.jp/products/tbhtpmho0002", variant="集合图内含天爱星", sale_type="single", size="约W728×H515mm", material="Wスエード", role="lineup", tags=["冬制服", "群像"])

# Valentine's Day lineup: the four solo items already existed; these are its group/random goods.
VAL_SOURCE = "https://www.gamers.co.jp/contents/event_fair/detail.php?id=7160"
for row in [
    ("thechara-valentine-badge", "ホログラムカンバッジ（ブラインド）バレンタイン ver.", "情人节随机镭射徽章 天爱星款", "can_badge", 660, "01271413_69784997b48cb.jpg", "10870393", "random", 6, "马剃天爱星"),
    ("thechara-valentine-phone-stand", "アクリルスマホスタンド 生徒会 バレンタイン ver.", "情人节学生会亚克力手机架", "stationery", 1870, "01271415_69784a01b5f2d.jpg", "10870401", "single", None, "学生会集合图内含天爱星"),
    ("thechara-valentine-mini-art", "ミニアクリルアート バレンタイン ver.", "情人节迷你亚克力画", "acrylic_art", 2640, "01271417_69784a659b7d9.jpg", "10870408", "single", None, "集合图内含天爱星"),
    ("thechara-valentine-clock", "ミニアクリルクロック 生徒会 バレンタイン ver.", "情人节学生会迷你亚克力时钟", "stationery", 3850, "01271417_69784a833f973.jpg", "10870410", "single", None, "学生会集合图内含天爱星"),
    ("thechara-valentine-deskmat", "ラバーデスクマット バレンタイン ver.", "情人节橡胶桌垫", "stationery", 4400, "01271419_69784ad955c60.jpg", "10870417", "single", None, "集合图内含天爱星"),
    ("thechara-valentine-blanket", "超特大ブランケット 生徒会 バレンタイン ver.", "情人节学生会超大毛毯", "fabric_goods", 7700, "01271419_69784af2c9e54.jpg", "10870419", "single", None, "学生会集合图内含天爱星"),
    ("thechara-valentine-mug", "マグカップ バレンタイン ver.", "情人节马克杯", "tableware", 1980, "01271419_69784aff7bbbf.jpg", "10870420", "single", None, "集合图内含天爱星"),
    ("thechara-valentine-memorial-art", "メモリアルアート バレンタイン ver.", "情人节纪念画", "acrylic_art", 16500, "01271427_69784cd633c6a.jpg", "10870427", "single", None, "集合图内含天爱星"),
]:
    iid, ja, zh, cat, price, image, pid, sale, variants, variant = row
    add(iid, ja, zh, cat, "バレンタイン ver.", 2026, "コンテンツシード", price, GAMERS_IMG + image + "&width=1200&height=630", f"https://www.gamers.co.jp/pn/pd/{pid}/", variant=variant, sale_type=sale, total_variants=variants, source_type="seller", role="lineup", tags=["情人节", "学生会"])

# After-Kyomaf shrine-maiden-dance lineup.
SHRINE_SOURCE = "https://www.gamers.co.jp/contents/event_fair/detail.php?id=7943"
SHRINE_IMG = "https://www.gamers.co.jp/upload/save_image/"
for row in [
    ("thechara-shrine-tapestry-tiara", "特大タペストリー 馬剃天愛星 巫女舞 ver.", "巫女舞天爱星超大挂毯", "tapestry", 8800, "09101511_6aa24a1a96c51.jpg", "single", None, "马剃天爱星", "H1700×W600mm", "スエード"),
    ("thechara-shrine-memorial-art", "メモリアルアート 巫女舞 ver.", "巫女舞纪念画", "acrylic_art", 16500, "09101511_6aa24a2924392.jpg", "single", None, "集合图内含天爱星", "外寸约340×430mm／画面A4", "樹脂"),
    ("thechara-shrine-badge", "ホログラムカンバッジ（ブラインド）巫女舞 ver.", "巫女舞随机镭射徽章 天爱星款", "can_badge", 715, "09101512_6aa24a39a4cec.jpg", "random", 6, "马剃天爱星", None, None),
    ("thechara-shrine-woodstrap-tiara", "木札ストラップ 馬剃天愛星 巫女舞 ver.", "巫女舞天爱星木札挂件", "accessory", 770, "09101513_6aa24a75562c1.jpg", "single", None, "马剃天爱星", "约6.5×5.2cm", "木"),
    ("thechara-shrine-stand-tiara", "デカアクリルスタンド 馬剃天愛星 巫女舞 ver.", "巫女舞天爱星大亚克力立牌", "acrylic_stand", 2420, "09101514_6aa24abc6eda7.jpg", "single", None, "马剃天爱星", None, "アクリル"),
    ("thechara-shrine-mini-art", "ミニアクリルアート 生徒会 巫女舞 ver.", "巫女舞学生会迷你亚克力画", "acrylic_art", 3190, "09101514_6aa24adc9ee9a.jpg", "single", None, "学生会集合图内含天爱星", None, "アクリル"),
    ("thechara-shrine-microfiber-tiara", "マイクロファイバー 馬剃天愛星 巫女舞 ver.", "巫女舞天爱星超细纤维布", "fabric_goods", 825, "09101515_6aa24b16a2b22.jpg", "single", None, "马剃天爱星", None, "マイクロファイバー"),
    ("thechara-shrine-deskmat", "ラバーデスクマット 巫女舞 ver.", "巫女舞橡胶桌垫", "stationery", 4400, "09101516_6aa24b232a40e.jpg", "single", None, "集合图内含天爱星", None, "ラバー"),
]:
    iid, ja, zh, cat, price, image, sale, variants, variant, size, material = row
    add(iid, ja, zh, cat, "巫女舞 ver.", 2026, "コンテンツシード", price, SHRINE_IMG + image, SHRINE_SOURCE, variant=variant, sale_type=sale, total_variants=variants, size=size, material=material, role="lineup" if sale != "single" else "product", tags=["巫女舞", "学生会"])

# PALE TONE 2026 additions.
add("thechara-pale-badge", "ホログラムカンバッジ（ブラインド）PALE TONE series TSUWABUKI FES ver.", "PALE TONE TSUWABUKI FES 随机镭射徽章 天爱星款", "can_badge", "PALE TONE TSUWABUKI FES", 2026, "コンテンツシード", 660, GAMERS_IMG + "06181247_6a336a4d08052.jpg&width=1200&height=630", "https://www.gamers.co.jp/pn/pd/10907440/", sale_type="random", total_variants=7, source_type="seller", role="lineup", tags=["PALE TONE", "随机"])
add("thechara-pale-tapestry-tiara", "特大タペストリー PALE TONE series 馬剃天愛星 TSUWABUKI FES ver.", "PALE TONE TSUWABUKI FES 天爱星超大挂毯", "tapestry", "PALE TONE TSUWABUKI FES", 2026, "コンテンツシード", 8800, GAMERS_IMG + "06181317_6a33714449f5b.jpg&width=1200&height=630", "https://www.gamers.co.jp/pn/pd/10907471/", size="H1700×W600mm", material="スエード", source_type="seller", tags=["PALE TONE", "单人"])

# Original (non-PALE-TONE) TSUWABUKI FES range indexed by AmiAmi.
for row in [
    ("thechara-fes-keychain-tiara", "SNS風アクリルキーホルダー 馬剃天愛星 TSUWABUKI FES ver.", "TSUWABUKI FES 天爱星 SNS 风亚克力挂件", "acrylic_keychain", 1375, "GOODS-04638182", "H90×W60mm", "アクリル・金属"),
    ("thechara-fes-holo-stand-tiara", "ホログラムデカアクリルスタンド 馬剃天愛星 TSUWABUKI FES ver.", "TSUWABUKI FES 天爱星镭射大亚克力立牌", "acrylic_stand", 2750, "GOODS-04638193", None, "アクリル"),
    ("thechara-fes-board-tiara", "超特大ダイカットアクリルボード 馬剃天愛星 TSUWABUKI FES ver.", "TSUWABUKI FES 天爱星超大异形亚克力板", "acrylic_art", 5500, "GOODS-04638200", None, "アクリル"),
    ("thechara-fes-microfiber-tiara", "マイクロファイバー 馬剃天愛星 TSUWABUKI FES ver.", "TSUWABUKI FES 天爱星超细纤维布", "fabric_goods", 770, "GOODS-04638207", "200×200mm", "マイクロファイバー"),
    ("thechara-fes-tapestry-tiara", "特大タペストリー 馬剃天愛星 TSUWABUKI FES ver.", "TSUWABUKI FES 天爱星超大挂毯", "tapestry", 7700, "GOODS-04638216", "H1700×W600mm", "スエード"),
]:
    iid, ja, zh, cat, price, code, size, material = row
    source = f"https://www.amiami.jp/top/detail/detail?gcode={code}"
    add(iid, ja, zh, cat, "TSUWABUKI FES", 2025, "コンテンツシード", price, f"https://img.amiami.jp/images/product/main/252/{code}.jpg", source, size=size, material=material, verification="seller_claim", source_type="seller", tags=["TSUWABUKI FES", "单人"])

# Earlier standard retail products found through character-index and maker catalogs.
add("contentseed-sns-keychain-tiara", "SNS風アクリルキーホルダー 馬剃天愛星", "SNS 风天爱星亚克力挂件", "acrylic_keychain", "コンテンツシード 2025", 2025, "コンテンツシード", 1320, "https://img.amiami.jp/images/product/main/251/GOODS-04595965.jpg", "https://www.amiami.jp/top/detail/detail?gcode=GOODS-04595965", size="约60×89mm", material="アクリル・金属", release_date="2025-04", source_type="seller", tags=["单人"])
add("contentseed-diorama-hibari-tiara", "アクリルジオラマ 放虎原ひばり＆馬剃天愛星", "放虎原羽、马剃天爱星亚克力场景", "acrylic_art", "コンテンツシード 2025", 2025, "コンテンツシード", 2750, "https://img.amiami.jp/images/product/main/251/GOODS-04595970.jpg", "https://www.amiami.jp/top/detail/detail?gcode=GOODS-04595970", variant="放虎原羽＆马剃天爱星", size="约H166×W142mm（组装时）", material="アクリル", release_date="2025-04", source_type="seller", tags=["学生会", "双人"])
add("hobbystock-trading-badge-vol3", "トレーディング缶バッジ vol.3", "随机徽章 vol.3 天爱星款", "can_badge", "トレーディング缶バッジ vol.3", 2025, "ホビーストック", 440, "https://img.amiami.jp/images/product/main/251/GOODS-04592880.jpg", "https://www.amiami.jp/top/detail/detail?gcode=GOODS-04592880", sale_type="random", total_variants=12, size="直径约57mm", material="紙・スチール", release_date="2025-04", source_type="seller", role="lineup", tags=["随机"])
add("ensky-snapmide-tiara", "負けヒロインが多すぎる！ スナップマイド", "Snapmide 随机卡片 天爱星款", "card", "スナップマイド", 2025, "エンスカイ", 275, "https://www.1999.co.jp/itbig113/11138260a.jpg", "https://www.1999.co.jp/11138260", variant="48款中含天爱星单人/双人图", sale_type="random", total_variants=48, size="约H87×W54mm", material="紙", release_date="2025-01", source_type="seller", role="lineup", tags=["随机", "拍立得风"])

# CS.FRONT /01 randomized and group products containing Tiara.
for row in [
    ("csfront-01-acrylic-card", "アクリルカード /01 全9種", "CS.FRONT /01 随机亚克力卡 天爱星款", "card", 660, "000000007380_vTKRKP3.jpg", "000000007380", "random", 9, "约90×55mm", "アクリル・鉄"),
    ("csfront-01-acrylic-board", "アクリルボード -技- /01 集合", "CS.FRONT /01 集合亚克力板", "acrylic_art", 3850, "000000007381_0efgr5Z.jpg", "000000007381", "single", None, "210×148mm", "アクリル・鉄"),
    ("csfront-01-stand-keyholder", "まるっとスタンドキーホルダー /01 全9種", "CS.FRONT /01 随机竖牌挂件 天爱星款", "acrylic_keychain", 880, "000000007409_WgEA5e5.jpg", "000000007409", "random", 9, "约65×65mm", "アクリル・真鍮・鉄"),
    ("csfront-01-badge", "缶バッジ /01 全9種", "CS.FRONT /01 随机徽章 天爱星款", "can_badge", 440, "000000007411_YRNnj54.jpg", "000000007411", "random", 9, "直径约56mm", "ブリキ・PET・紙"),
]:
    iid, ja, zh, cat, price, image, product_id, sale, variants, size, material = row
    add(iid, ja, zh, cat, "CS.FRONT /01", 2026, "CS.FRONT", price, f"https://makeshop-multi-images.akamaized.net/csshop/itemimages/{image}", f"https://www.crysto.jp/view/item/{product_id}", variant="集合图内含天爱星" if sale == "single" else "马剃天爱星", sale_type=sale, total_variants=variants, size=size, material=material, release_date="2026-04", role="lineup", tags=["CS.FRONT", "随机" if sale == "random" else "群像"])

# Group products from the original TSUWABUKI FES range.
for row in [
    ("thechara-fes-badge", "カンバッジ（ブラインド）TSUWABUKI FES ver.", "TSUWABUKI FES 随机徽章 天爱星款", "can_badge", 550, "06031134_683e5f1fd50ee.jpg", "10805297", "random", 7, None),
    ("thechara-fes-clock-student-council", "ミニアクリルクロック 生徒会 TSUWABUKI FES ver.", "TSUWABUKI FES 学生会迷你亚克力时钟", "stationery", 3850, "06031139_683e607ca5f6d.jpg", "10805308", "single", None, "约H100×W140mm"),
    ("thechara-fes-deskmat-student-council", "ラバーデスクマット 生徒会 TSUWABUKI FES ver.", "TSUWABUKI FES 学生会橡胶桌垫", "stationery", 3850, "06031152_683e635b56268.jpg", "10805331", "single", None, "350×600mm"),
]:
    iid, ja, zh, cat, price, image, pid, sale, variants, size = row
    add(iid, ja, zh, cat, "TSUWABUKI FES", 2025, "コンテンツシード", price, GAMERS_IMG + image + "&width=1200&height=630", f"https://www.gamers.co.jp/pn/pd/{pid}/", variant="马剃天爱星" if sale == "random" else "学生会集合图内含天爱星", sale_type=sale, total_variants=variants, size=size, material="アクリル" if "art" in iid or "clock" in iid else "ラバー", source_type="seller", role="lineup", tags=["TSUWABUKI FES", "学生会"])

add("thechara-fes-mini-art-student-council", "ミニアクリルアート 生徒会 TSUWABUKI FES ver.", "TSUWABUKI FES 学生会迷你亚克力画", "acrylic_art", "TSUWABUKI FES", 2025, "コンテンツシード", 2530, "https://collabo-cafe.com/wp-content/uploads/14ab0291f8d1fbbcdf8fdc59affa4c0e.jpg", "https://www.1999.co.jp/11213023", variant="学生会集合图内含天爱星", size="约128×182mm", material="アクリル・ビス", source_type="seller", role="lineup", tags=["TSUWABUKI FES", "学生会"])
add("thechara-fes-tshirt-student-council", "Tシャツ 生徒会 TSUWABUKI FES ver.", "TSUWABUKI FES 学生会 T 恤", "apparel", "TSUWABUKI FES", 2025, "コンテンツシード", 4400, "https://collabo-cafe.com/wp-content/uploads/ffaeb23d4616dd1434ccf148392924a8.jpg", "https://www.1999.co.jp/11213046", variant="学生会集合图内含天爱星", size="XL：衣长约780・肩宽约530・袖长约240mm", material="綿", source_type="seller", role="lineup", tags=["TSUWABUKI FES", "学生会"])

# PALE TONE student-council/group products omitted by exact-character searches.
for row in [
    ("thechara-pale-mini-art-student-council", "ミニアクリルアート PALE TONE series 生徒会 TSUWABUKI FES ver.", "PALE TONE 学生会迷你亚克力画", "acrylic_art", 2640, "06181300_6a336d6315094.jpg", "10907456", "约128×182mm", "アクリル・ビス"),
    ("thechara-pale-deskmat", "ラバーデスクマット PALE TONE series TSUWABUKI FES ver.", "PALE TONE TSUWABUKI FES 橡胶桌垫", "stationery", 4400, "06181302_6a336de36cf50.jpg", "10907457", "600×350mm", "ラバー"),
    ("thechara-pale-memorial-art", "メモリアルアート PALE TONE series 生徒会 TSUWABUKI FES ver.", "PALE TONE 学生会纪念画", "acrylic_art", 16500, "https://prcdn.freetls.fastly.net/release_image/69812/838/69812-838-99c51f3d27ed2806d76b3fed34e43dc0-800x800.jpg", "10907473", "外寸约340×430mm／画面A4", "樹脂・PVC・紙"),
]:
    iid, ja, zh, cat, price, image, pid, size, material = row
    image_url = image if image.startswith("http") else GAMERS_IMG + image + "&width=1200&height=630"
    add(iid, ja, zh, cat, "PALE TONE TSUWABUKI FES", 2026, "コンテンツシード", price, image_url, f"https://www.gamers.co.jp/pn/pd/{pid}/", variant="学生会/集合图内含天爱星", size=size, material=material, release_date="2026-09", source_type="seller", role="lineup", tags=["PALE TONE", "学生会"])

PALE_EVENT_SOURCE = "https://prtimes.jp/main/html/rd/p/000000838.000069812.html"
PALE_BONUS_IMAGE = "https://prcdn.freetls.fastly.net/release_image/69812/838/69812-838-9fcfb15edd2c0b3aceb407036f7268fc-2000x1414.jpg"
add("thechara-pale-bromide-tiara", "ご購入者様特典 ブロマイド 馬剃天愛星 PALE TONE series", "PALE TONE 天爱星照片卡（购入特典）", "card", "PALE TONE TSUWABUKI FES", 2026, "コンテンツシード / 有楽町マルイ", None, PALE_BONUS_IMAGE, PALE_EVENT_SOURCE, sale_type="random", total_variants=9, role="lineup", tags=["PALE TONE", "购入特典", "非卖品"], notes="活动期间店铺每购买3,000日元随机赠送1枚；官方特典图确认共9款并含天爱星。", phase="purchase_bonus", seller="有楽町マルイ")
add("thechara-pale-lottery-figure-tiara", "抽選会 特大アクリルスタンド 馬剃天愛星 PALE TONE series", "PALE TONE 天爱星特大亚克力竖牌（抽奖奖品）", "acrylic_stand", "PALE TONE TSUWABUKI FES", 2026, "コンテンツシード / 有楽町マルイ", None, PALE_BONUS_IMAGE, PALE_EVENT_SOURCE, sale_type="random", total_variants=7, size="最大约H300mm", material="アクリル", role="lineup", tags=["PALE TONE", "抽奖", "非卖品"], notes="活动购买者可参加特大竖牌抽奖；官方图确认全7款并含天爱星。", phase="lottery_prize", seller="有楽町マルイ")

# Event-only prizes and purchase bonuses are separate records, not retail goods.
add("thechara-shrine-lottery-figure-tiara", "A賞 特大アクリルフィギュア 馬剃天愛星 巫女舞 ver.", "巫女舞天爱星特大亚克力竖像（抽奖奖品）", "acrylic_stand", "アフター京まふ", 2026, "ゲーマーズ / コンテンツシード", None, SHRINE_IMG + "09101514_6aa24abc6eda7.jpg", SHRINE_SOURCE, sale_type="random", total_variants=6, size="约30cm", material="アクリル", role="reference", tags=["巫女舞", "抽奖", "非卖品"], notes="每购买或预订内金3,000日元可参加一次抽奖；A赏图案可在库存范围内选择。", phase="lottery_prize", seller="ゲーマーズ")
add("thechara-valentine-lottery-figure-tiara", "A賞 特大アクリルフィギュア 馬剃天愛星 バレンタイン ver.", "情人节天爱星特大亚克力竖像（抽奖奖品）", "acrylic_stand", "バレンタイン ver.", 2026, "ゲーマーズ / コンテンツシード", None, GAMERS_IMG + "01271417_69784a5236669.jpg&width=1200&height=630", VAL_SOURCE, sale_type="random", total_variants=6, size="约30cm", material="アクリル", role="reference", tags=["情人节", "抽奖", "非卖品"], notes="店铺抽奖A赏；图片为同系列天爱星角色图参考。", phase="lottery_prize", seller="ゲーマーズ")
add("thechara-valentine-bromide-tiara", "購入特典 ブロマイド 馬剃天愛星 バレンタイン ver.", "情人节天爱星照片卡（购入特典）", "card", "バレンタイン ver.", 2026, "ゲーマーズ / コンテンツシード", None, GAMERS_IMG + "01271417_69784a5236669.jpg&width=1200&height=630", VAL_SOURCE, sale_type="random", total_variants=7, role="reference", tags=["情人节", "购入特典", "非卖品"], notes="每购买活动商品3,000日元随机赠送1枚；图片为同系列角色图参考。", phase="purchase_bonus", seller="ゲーマーズ")

# NEO GATE Animate-fair bonuses, both confirmed to have a Tiara design.
NEOGATE_SOURCE = "https://www.neogate.jp/makeine_goods/"
add("neogate-yumekawa-heart-card-tiara", "ハート型ミニカード 馬剃天愛星 ゆめかわver.", "梦幻可爱天爱星心形迷你卡（通贩预订特典）", "card", "ゆめかわフェア in アニメイト", 2026, "NEO GATE / アニメイト", None, "https://www.neogate.jp/wp-content/uploads/makeine_goods_campaign.webp", NEOGATE_SOURCE, sale_type="random", total_variants=5, release_date="2026-10-10", role="lineup", tags=["梦幻可爱", "预订特典", "非卖品"], notes="通贩事前预订期间，每满1,100日元随机赠送1枚。", phase="reservation_bonus", seller="アニメイト通販")
add("neogate-yumekawa-bookmark-tiara", "特製しおり 馬剃天愛星 ゆめかわver.", "梦幻可爱天爱星特制书签（店铺购入特典）", "card", "ゆめかわフェア in アニメイト", 2026, "NEO GATE / アニメイト", None, "https://www.neogate.jp/wp-content/uploads/makeine_goods_campaign2.webp", NEOGATE_SOURCE, sale_type="random", total_variants=5, release_date="2026-10-10", role="lineup", tags=["梦幻可爱", "购入特典", "非卖品"], notes="实体店活动期间，每满1,100日元随机赠送1枚。", phase="purchase_bonus", seller="アニメイト")

# Local-only town-walk merchandise, sold at the shop matching Tiara's stamp design.
add("toyohashi-townwalk-badge-kitchen-ninjin", "豊橋まちあるきスタンプ オリジナル缶バッジ キッチンにんじん（馬剃天愛星）", "丰桥街步印章 Kitchen Ninjin 天爱星原创徽章", "can_badge", "豊橋まちあるきスタンプ", 2025, "シャイニングヒロイン実行委員会", 400, "https://image.jimcdn.com/app/cms/image/transf/dimension%3D236x10000%3Aformat%3Djpg/path/s154f533fae7a44ca/image/i15ebdee472b79074/version/1757924601/image.jpg", "https://makeine-toyohashi.jimdofree.com/", size="店头限定原创规格", material="ブリキ等", role="product", tags=["丰桥", "地方限定", "街步"], notes="天爱星印章图案对应店铺为キッチンにんじん，徽章在对应店铺售卖。", phase="local_sale", seller="キッチンにんじん")

# Bookstore campaign rewards that do not appear in ordinary character-goods shops.
add("gagaga-summer-2026-scented-bookmark-tiara", "夏のガガガ文庫フェア2026 香り付き特製しおり 馬剃天愛星", "2026 夏日 GAGAGA 天爱星香味书签（咖啡牛奶味）", "card", "夏のガガ文庫フェア2026", 2026, "小学館 / ガガガ文庫", None, "https://pbs.twimg.com/media/HLedDB1asAAZORD.jpg?name=orig", "https://x.com/makeine0718/status/2070446988127256952", size="书签", material="紙・香料", release_date="2026-07-17", role="lineup", tags=["GAGAGA", "书店特典", "非卖品", "咖啡牛奶"], notes="原作官方账号确认：天爱星款为咖啡牛奶香，背面含作者新写文字。", phase="purchase_bonus", seller="活动对象书店")
add("melonbooks-novel-fes-2025-metal-poster-tiara", "メタルポスター 馬剃天愛星 第16回メロンブックスノベル祭り～2025 Summer～", "Melonbooks 第16回小说祭天爱星 A3 金属海报", "poster", "第16回メロンブックスノベル祭り", 2025, "メロンブックス", None, "https://www.suruga-ya.jp/database/pics_light/game/561915607.jpg", "https://www.suruga-ya.jp/product/detail/561915607", size="A3（420×297mm）", material="金属・印刷", release_date="2025-08-01", verification="seller_claim", source_type="secondary", tags=["Melonbooks", "积分兑换", "限定品"], notes="原活动页已下线；规格、日期与角色名由骏河屋和 Goods Republic 的独立目录交叉确认。", phase="point_reward", seller="メロンブックス")

# Nonhoi Park collaboration: Tiara appears in the 16-design chibi attraction range.
NONHOI_SOURCE = "https://prtimes.jp/main/html/rd/p/000008499.000016064.html"
for row in [
    ("amnibus-nonhoi-chibi-stand", "トレーディングちびキャラ 植物＆アトラクションver. アクリルスタンド", "丰桥动物园 Q 版植物与游乐设施随机立牌 天爱星款", "acrylic_stand", 880, "8499-03384b3555440a9ef95313855aa462e2-1350x1500.jpg", "最大约64×60mm", "アクリル", "random", 16),
    ("amnibus-nonhoi-chibi-keychain", "トレーディングちびキャラ 植物＆アトラクションver. アクリルキーホルダー", "丰桥动物园 Q 版植物与游乐设施随机挂件 天爱星款", "acrylic_keychain", 715, "8499-d256a6424d919730be15438b496dbb54-1350x1500.jpg", "最大约65×60mm", "アクリル", "random", 16),
    ("amnibus-nonhoi-chibi-badge", "トレーディングちびキャラ 植物＆アトラクションver. グリッター缶バッジ", "丰桥动物园 Q 版植物与游乐设施随机闪粉徽章 天爱星款", "can_badge", 605, "8499-a6c62dd54caeaea125f83afde42cce2c-1350x1500.jpg", "直径约56mm", "紙・ブリキ", "random", 16),
    ("amnibus-nonhoi-chibi-sticker", "トレーディングちびキャラ 植物＆アトラクションver. ダイカットステッカー", "丰桥动物园 Q 版植物与游乐设施随机异形贴纸 天爱星款", "sticker", 550, "8499-fa92cbae559cf87344f1dc1de57b301f-1350x1500.jpg", "最大约90×89mm", "紙・PP", "random", 16),
    ("amnibus-nonhoi-chibi-mug", "ちびキャラ アトラクションver. マグカップ", "丰桥动物园 Q 版游乐设施马克杯", "tableware", 1980, "8499-b88f22e3fbc32f789cc1fb3aa22cdf77-1350x1500.jpg", "直径约82×H95mm", "陶器", "single", None),
]:
    iid, ja, zh, cat, price, image, size, material, sale, variants = row
    image_url = PR_IMG + image.split("-", 1)[0] + "/16064-" + image
    variant = "集合图内含天爱星" if iid.endswith("mug") else "马剃天爱星"
    add(iid, ja, zh, cat, "のんほいパーク", 2025, "アルマビアンカ", price, image_url, NONHOI_SOURCE, variant=variant, sale_type=sale, total_variants=variants, size=size, material=material, role="lineup", tags=["丰桥动物园", "Q版"])

# JR Central Oshitabi second wave: drawn and chibi ranges containing Tiara.
JR_SOURCE = "https://prtimes.jp/main/html/rd/p/000008501.000016064.html"
for row in [
    ("amnibus-jr2-trading-stand", "描き下ろし 駅員ver. 第2弾 トレーディングアクリルスタンド", "JR 东海第二弹新绘随机亚克力立牌 天爱星款", "acrylic_stand", 880, "8501-06af6e9e07dd87a67cb0fa1b8b69df77-1350x1500.jpg", "random", 16, "最大约70×48mm", "アクリル"),
    ("amnibus-jr2-acrylic-card", "描き下ろし 駅員ver. 第2弾 トレーディングアクリルカード", "JR 东海第二弹新绘随机亚克力卡 天爱星款", "card", 715, "8501-7c1cd79bf7a6a1df4c2ec57819d10247-1350x1500.jpg", "random", 9, "约70×55mm", "アクリル"),
    ("amnibus-jr2-glitter-badge", "描き下ろし 駅員ver. 第2弾 トレーディンググリッター缶バッジ", "JR 东海第二弹新绘随机闪粉徽章 天爱星款", "can_badge", 605, "8501-7f79795a179c3a20834e583429d5d58c-1350x1500.jpg", "random", 9, "直径约56mm", "紙・ブリキ"),
    ("amnibus-jr2-instant-card", "駅員ver. 第2弾 トレーディングインスタントカメラ風イラストカード", "JR 东海第二弹随机拍立得风卡片 天爱星款", "card", 275, "8501-52cbeb35cc7db10c05b7d54182ca3a89-1350x1500.jpg", "random", 16, "约80×50mm", "紙"),
    ("amnibus-jr2-deskmat-b", "描き下ろし 駅員ver. 第2弾 マルチデスクマット B", "JR 东海第二弹新绘多用途桌垫 B", "stationery", 3960, "8501-37c426da3e01d672e55fde3716073360-1350x1500.jpg", "single", None, "约60×35cm", "ポリエステル・ラバー"),
    ("amnibus-jr2-diorama-b", "描き下ろし 駅員ver. 第2弾 アクリルジオラマ B", "JR 东海第二弹新绘亚克力场景 B", "acrylic_art", 3850, "8501-ac4b6269fc06389c414ffa3e75a8975b-1350x1500.jpg", "single", None, "约23×18cm", "アクリル"),
    ("amnibus-jr2-postcards", "描き下ろし 駅員ver. 第2弾 ポストカード3枚セット", "JR 东海第二弹新绘明信片 3 枚套装", "card", 550, "8501-8738b20e6dd3a533983fa35680c4b42a-1350x1500.jpg", "set", 3, "约148×100mm", "紙"),
    ("amnibus-jr2-chibi-stand", "駅員ver. 第2弾 ちびキャラ トレーディングアクリルスタンド", "JR 东海第二弹 Q 版随机亚克力立牌 天爱星款", "acrylic_stand", 880, "8501-0541ee4cea7f2ae8bb627cdb66688c2f-1350x1500.jpg", "random", 6, "最大约68×54mm", "アクリル"),
    ("amnibus-jr2-chibi-keychain", "駅員ver. 第2弾 ちびキャラ トレーディングアクリルキーホルダー", "JR 东海第二弹 Q 版随机亚克力挂件 天爱星款", "acrylic_keychain", 715, "8501-09a10740ac8c9e12c927eff1583c5c8c-1350x1500.jpg", "random", 8, "最大约69×42mm", "アクリル"),
    ("amnibus-jr2-chibi-badge", "駅員ver. 第2弾 ちびキャラ トレーディンググリッター缶バッジ", "JR 东海第二弹 Q 版随机闪粉徽章 天爱星款", "can_badge", 605, "8501-4a73560eac3375ab76ca366d2f64beb1-1350x1500.jpg", "random", 6, "直径约56mm", "紙・ブリキ"),
    ("amnibus-jr2-chibi-mug", "駅員ver. 第2弾 ちびキャラ マグカップ", "JR 东海第二弹 Q 版马克杯", "tableware", 1980, "8501-921c77b1cffab4aeae894e2179ae3609-1350x1500.jpg", "single", None, "直径约82×H95mm", "陶器"),
    ("amnibus-jr2-chibi-stickers", "駅員ver. 第2弾 ちびキャラ フレークシール", "JR 东海第二弹 Q 版散装贴纸", "sticker", 1100, "8501-9cb6965d4594a61425e613cb40d9271f-1350x1500.jpg", "set", 16, None, "紙・PP"),
]:
    iid, ja, zh, cat, price, image, sale, variants, size, material = row
    image_url = PR_IMG + image.split("-", 1)[0] + "/16064-" + image
    add(iid, ja, zh, cat, "推し旅 駅員ver. 第2弾", 2026, "アルマビアンカ", price, image_url, JR_SOURCE, variant="全款式/集合图内含天爱星", sale_type=sale, total_variants=variants, size=size, material=material, role="lineup", tags=["JR东海", "推し旅"])

# Collectible cards are catalogued as variants originating from a randomized booster.
for iid, card_no, rarity, image, pid in [
    ("weiss-mki-w126-083", "MKI/W126-083", "U", "7015238_1.jpg", "10811518"),
    ("weiss-mki-w126-083s", "MKI/W126-083S", "SR", "7015158_1.jpg", "10811598"),
]:
    source = f"https://ws-tcg.com/cardlist/?cardno={card_no.replace('/', '%2F')}&l="
    add(iid, f"生徒会副会長 馬剃天愛星 {rarity}", f"Weiss Schwarz 学生会副会长 马剃天爱星（{rarity}）", "trading_card", "ヴァイスシュヴァルツ ブースターパック", 2025, "ブシロード", None, GAMERS_IMG + image + "&width=1200&height=630", source, variant=f"{card_no} / {rarity}", sale_type="random", release_date="2025-06-27", source_type="official", tags=["Weiss Schwarz", rarity], notes="收录于随机补充包；不把二手单卡行情记作官方定价。")


def merge_catalog() -> dict:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    existing = {entry["id"]: entry for entry in data["items"]}

    for item_id, (image_url, source_url) in EXISTING_IMAGES.items():
        current = existing[item_id]
        current["images"] = [{
            "path": f"images/items/{item_id}.jpg",
            "role": "product",
            "source_url": image_url,
        }]
        if not any(source.get("url") == source_url for source in current["sources"]):
            current["sources"].append({"url": source_url, "type": "official" if "post.japanpost" in source_url else "seller", "checked_at": CHECKED_AT})
        # These lines were announced with month-only delivery windows, not exact dates.
        if item_id.startswith("thechara-"):
            current["release_date"] = None

    for new_item in ITEMS:
        if new_item["id"] in existing:
            data["items"][data["items"].index(existing[new_item["id"]])] = new_item
        else:
            data["items"].append(new_item)
        existing[new_item["id"]] = new_item

    data["catalog"]["updated_at"] = CHECKED_AT
    data["catalog"]["status"] = "expanded_verified_catalog"
    CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def download_one(image: dict) -> tuple[str, str]:
    target = ROOT / image["path"]
    if target.exists() and target.stat().st_size > 1024:
        return image["path"], "exists"
    target.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; TiaraCatalog/1.0)"}
    if "neogate.jp" in image["source_url"]:
        headers["Referer"] = NEOGATE_SOURCE
    request = urllib.request.Request(image["source_url"], headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read()
        content_type = response.headers.get_content_type()
    if not content_type.startswith("image/") or len(payload) < 1024:
        raise ValueError(f"not an image ({content_type}, {len(payload)} bytes)")
    temporary = target.with_suffix(target.suffix + ".part")
    temporary.write_bytes(payload)
    temporary.replace(target)
    return image["path"], "downloaded"


def download_images(data: dict) -> int:
    images = {image["path"]: image for entry in data["items"] for image in entry["images"]}
    failures = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(download_one, image): image for image in images.values()}
        for future in as_completed(futures):
            image = futures[future]
            try:
                path, status = future.result()
                print(f"{status:10} {path}")
            except Exception as error:  # keep the rest of the archive moving
                failures += 1
                print(f"FAILED     {image['path']}: {error}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true", help="download all missing local images")
    args = parser.parse_args()
    data = merge_catalog()
    print(f"Merged catalog: {len(data['items'])} items")
    return 1 if args.download and download_images(data) else 0


if __name__ == "__main__":
    raise SystemExit(main())
