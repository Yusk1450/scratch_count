import zipfile
import json
import os
import csv

dir = 'sb'
outputfile = 'data.csv'

block_category_prefixes = [
	# 動き
	'motion',
	# 見た目
	'looks',
	# 音
	'sound',
	# イベント
	'event',
	# 制御
	'control',
	# 調べる
	'sensing',
	# 演算
	'operator',
	# 変数
	'data',
	# ブロック定義
	'procedures'
]

# 途中...
block_names = [
	# 動き
	[
		# 〜歩動かす
		'motion_movesteps',
		# 〜度回す（右）
		'motion_turnright',
		# 〜度回す（左）
		'motion_turnleft',
		# 〜へ行く
		'motion_goto',
		# 〜へ行く？
		'motion_goto_menu',
		# x座標を〜、y座標を〜にする
		'motion_gotoxy',
		'motion_glideto',
		'motion_glideto_menu',
		'motion_glidesecstoxy',
		# 〜度に向ける
		'motion_pointindirection',
		# 〜へ向ける
		'motion_pointtowards'
	]
]

# Internal Drop-Down Reporters
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

def parsingSb3(data):
	# 総ブロック数
	all_blocks_num = 0
	# 変数の数
	variables_num = 0
	# スプライトの数
	sprites_num = 0
	# 各カテゴリのブロック数
	categories_block_num = []
	for i in range(len(block_category_prefixes)):
		categories_block_num.append(0)

	# print(data)

	# スプライト
	for _, e in enumerate(data['targets']):
		
		# print(e['name'])

		if not e['isStage']:
			sprites_num += 1

		# 変数
		for _, (hash_key, variable) in enumerate(e['variables'].items()):
			variables_num += 1

		# リスト
		for _, (hash_key, list) in enumerate(e['lists'].items()):
			variables_num += 1

		# ブロック
		for _, (hash_key, block) in enumerate(e['blocks'].items()):

			# print(block)

			# 値のブロックが放置されている場合の対策
			if not ("opcode" in block):
				continue

			# ブロック名
			opcode = block['opcode']

			# ブロックに付随するドロップダウンメニューブロックを除外する
			if opcode in dropdown_blocks:
				continue

			all_blocks_num += 1
			# print(opcode)

			# プレフィックスのみを抜き出す
			if len(opcode.split('_')) > 1:
				opcode_prefix = opcode.split('_')[0]

			for i, prefix in enumerate(block_category_prefixes):
				if prefix == opcode_prefix:
					categories_block_num[i] += 1

	return [
		all_blocks_num,
		variables_num,
		sprites_num,
		categories_block_num
	]

files = os.listdir(dir)

result = [['ファイル名', '総ブロック数', '変数の数', 'スプライト数', '動き', '見た目', '音', 'イベント', '制御', '調べる', '演算', '変数', 'ブロック定義']]

for file in files:
	if not (file.startswith(".")):
		print(file)
		f = openSb3(dir+'/'+file)
		data = json.load(f)

		r = parsingSb3(data)
		print(r)

		row = []
		row.append(file)
		row.append(r[0])
		row.append(r[1])
		row.append(r[2])
		for i in range(len(r[3])):
			row.append(r[3][i])

		result.append(row)

with open(outputfile, mode="w") as csv_file:
	writer = csv.writer(csv_file)
	writer.writerows(result)
