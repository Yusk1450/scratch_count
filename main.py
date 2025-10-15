import zipfile
import json
import os
import csv
import statistics

dir = 'sb'
outputfile = 'data.csv'

block_category_prefixes = [
    'motion',   # 動き
    'looks',    # 見た目
    'sound',    # 音
    'event',    # イベント
    'control',  # 制御
    'sensing',  # 調べる
    'operator', # 演算
    'data',     # 変数
    'procedures' # ブロック定義
]

dropdown_blocks = [
    'motion_goto_menu',
    'motion_glideto_menu',
    'motion_pointtowards_menu',
    'looks_costume',
    'looks_backdrops',
    'sound_sounds_menu',
    'event_broadcast_menu',
    'control_create_clone_of_menu',
    'sensing_touchingobjectmenu',
    'sensing_distancetomenu',
    'sensing_keyoptions',
    'sensing_of_object_menu'
]

def openSb3(filename):
    zf = zipfile.ZipFile(filename, 'r')
    return zf.open('project.json')

def collect_script_blocks(blocks, start_id):
    visited = set()
    stack = [start_id]

    while stack:
        block_id = stack.pop()
        if block_id in visited or block_id not in blocks:
            continue
        visited.add(block_id)
        block = blocks[block_id]

        for _, val in block.get("inputs", {}).items():
            if isinstance(val, list) and len(val) > 1 and isinstance(val[1], str):
                if val[1] in blocks:
                    stack.append(val[1])

        next_id = block.get("next")
        if isinstance(next_id, str) and next_id in blocks:
            stack.append(next_id)

    return visited

def block_depth(blocks, block_id, current_depth=1):
    block = blocks[block_id]
    depth = current_depth

    for input_name, val in block.get("inputs", {}).items():
        if input_name in ("SUBSTACK", "SUBSTACK2"):
            if isinstance(val, list) and len(val) > 1:
                child = val[1]
                if isinstance(child, str) and child in blocks:
                    depth = max(depth, block_depth(blocks, child, current_depth + 1))

    next_id = block.get("next")
    if isinstance(next_id, str) and next_id in blocks:
        depth = max(depth, block_depth(blocks, next_id, current_depth))

    return depth

def is_event_block(block):
    opcode = block.get("opcode", "")
    if opcode.startswith("event_"):
        if opcode in ("event_broadcast", "event_broadcastandwait"):
            return False
        return True
    return False

def parsingSb3(data):
    all_blocks_num = 0
    variables_num = 0
    sprites_num = 0
    categories_block_num = [0] * len(block_category_prefixes)
    script_depths = []
    target_depths = {}

    for e in data['targets']:
        if not e['isStage']:
            sprites_num += 1

        for _, (hash_key, variable) in e['variables'].items():
            variables_num += 1

        for _, (hash_key, list) in enumerate(e['lists'].items()):
            variables_num += 1

        blocks = e['blocks']
        local_depths = []

        for block_id, block in blocks.items():
            if not ("opcode" in block):
                continue
            if block.get("topLevel") and is_event_block(block):

                # このスクリプトに含まれる全ブロックを収集
                script_blocks = collect_script_blocks(blocks, block_id)

                # イベントブロックしかない (=1つだけ) の場合はスキップ
                if len(script_blocks) <= 1:
                    continue

                # ネスト深さを計算
                depth = block_depth(blocks, block_id)
                script_depths.append(depth)
                local_depths.append(depth)

                # ブロック数カウント
                for b_id in script_blocks:
                    b = blocks[b_id]
                    op = b.get("opcode", "")
                    if op in dropdown_blocks:
                        continue
                    all_blocks_num += 1
                    if len(op.split('_')) > 1:
                        prefix = op.split('_')[0]
                        for i, cat in enumerate(block_category_prefixes):
                            if cat == prefix:
                                categories_block_num[i] += 1

        if local_depths:
            target_depths[e['name']] = max(local_depths)

    if script_depths:
        max_depth = max(script_depths)
        avg_depth = statistics.mean(script_depths)
        median_depth = statistics.median(script_depths)
        max_targets = [name for name, d in target_depths.items() if d == max_depth]
    else:
        max_depth = avg_depth = median_depth = 0
        max_targets = []

    return [all_blocks_num, variables_num, sprites_num, categories_block_num,
            max_depth, avg_depth, median_depth, max_targets]

# CSV 出力準備
result = [['ファイル名', '総ブロック数', '変数の数', 'スプライト数',
           '動き', '見た目', '音', 'イベント', '制御', '調べる', '演算', '変数', 'ブロック定義',
           '最大ネスト', '平均ネスト', '中央値']]

files = os.listdir(dir)
for file in files:
    if not (file.startswith(".")) and file.endswith(".sb3"):
        print("解析中:", file)
        f = openSb3(os.path.join(dir, file))
        data = json.load(f)
        r = parsingSb3(data)
        print(r)

        row = [file, r[0], r[1], r[2]]
        row.extend(r[3])
        # ネスト統計情報を個別の列として追加
        row.extend([r[4], f"{r[5]:.2f}", r[6]])

        result.append(row)

with open(outputfile, mode="w", newline="") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerows(result)
