## 完整流程走查（2026-10-24）找出的问题：选卡片的焦点、进山门的守卫、开场的道具与通用技、
## 任务栏 / 对话框 / 互动键 / 暂停菜单的显示，以及电脑镜头不让技能栏挡住地图下沿。
extends "res://tests/test_case.gd"

const DT := 1.0 / 60.0


func _main() -> Node:
	var m: Node = load("res://scripts/game/main.gd").new()
	tree.root.add_child(m)
	m.profile = Profile.new()
	return m


## 选出身、门派、通用技：卡片之间方向键 / 十字键能互相切换（原先卡片直接挂在 CanvasLayer 下，找不到邻居）
func test_select_cards_focus_neighbors() -> void:
	for page in ["_origin_select", "_sect_select", "_utility_select"]:
		var m := _main()   # 每页单独建：换页时旧页 queue_free，测试里不过帧还留在树上
		m.call(page)
		var cards: Array = m._layer.get_children().filter(func(c): return c is Button and c.get_child_count() >= 3)
		cards.sort_custom(func(a, b): return a.position.x < b.position.x)
		check(cards.size() >= 2, "%s 有多张卡片" % page)
		for i in range(1, cards.size()):
			check_eq(cards[i].find_valid_focus_neighbor(SIDE_LEFT), cards[i - 1], "%s：第 %d 张卡片按左键到前一张" % [page, i + 1])
			check_eq(cards[i - 1].find_valid_focus_neighbor(SIDE_RIGHT), cards[i], "%s：第 %d 张卡片按右键到后一张（不跳到确认键）" % [page, i])
		m.free()


## 进山门：开场对话放完之前喽啰不动手，放完才开打；任务栏一直按 4 个没击退算
func test_shanmen_guards_wait_for_intro() -> void:
	var lv := Shanmen.new()
	lv.setup("shaolin", "jiemai")
	lv.origin = "xiban"   # 戏班线出生点紧挨着喽啰，最容易被围
	lv.profile = Profile.new()
	tree.root.add_child(lv)
	var guards := lv.world.fighters.filter(func(f): return f.kind == "louluo")
	check_eq(guards.size(), 4, "四个喽啰")
	var hp := lv.me.hp
	for i in 60 * 4:
		lv._physics_process(DT)
	check(guards.all(func(f): return f.state == "wait"), "开场对话期间喽啰原地等着")
	check_eq(lv.me.hp, hp, "开场对话期间不掉血")
	check_eq(lv.hud.objectives[1], "击退守卫 0 / 4", "还没开打时任务栏是 0 / 4")
	lv.dialogue.hide()
	lv._on_dialogue_done()
	check(guards.all(func(f): return f.state != "wait"), "对话放完喽啰开始动")
	lv.free()


## 出身开场：现代车间那十秒里没有古代的引导人和道具，醒来才出现；通用技还没选，那一格不显示、按了也不放
func test_prologue_modern_and_utility() -> void:
	var lv := Prologue.new()
	lv.setup("shaolin", "jiemai")
	lv.origin = "xiban"
	lv.profile = Profile.new()
	tree.root.add_child(lv)
	check_eq(lv.world.fighters.filter(func(f): return not f.is_hero()).size(), 0, "现代车间里没有引导人和道具")
	check(lv.hud.hide_utility, "开场不显示通用技")
	lv._wake()
	check(lv.trainer != null and lv.prop != null, "醒来后引导人和道具都在")
	var b: Array = Hud.MOBILE[Hud.ACTIONS.find("utility")]
	check_eq(lv.hud._button_at(Vector2(b[0], b[1])), "", "手机上点通用技那一格没反应")
	lv.free()


## 互动键写要做的事；对话翻页提示跟设备走；暂停菜单「关」的开关看得见
func test_labels_and_switch() -> void:
	var lv := Shanmen.new()
	lv.setup("shaolin", "jiemai")
	lv.profile = Profile.new()
	tree.root.add_child(lv)
	lv.me.pos = Shanmen.TORCHES[0] + Vector2(20, 0)
	lv.interact_hint([[Shanmen.TORCHES[0], "熄灭火把"]])
	check_eq(lv.hud.talk_label, "熄灭火把", "手机互动键写「熄灭火把」")
	lv.interact_hint([[lv.me.pos, "拼装弩车（3 秒）"]])
	check_eq(lv.hud.talk_label, "拼装弩车", "括号里的说明不上键")
	lv.dialogue.mobile = true
	check_eq(lv.dialogue._continue_hint(), "点按继续", "手机对话只提示点按")
	lv.dialogue.mobile = false
	check(lv.dialogue._continue_hint().begins_with("E"), "电脑提示 E")
	var off: Texture2D = LevelBase._switch_off(Vector2(32, 16))
	var img := off.get_image()
	var lit := 0
	for x in 32:
		if img.get_pixel(x, 8).a > 0.5:
			lit += 1
	check(lit > 20, "「关」的开关有一条看得见的轨道（%d 像素）" % lit)
	lv.free()


## 电脑：镜头可以往地图下沿外多走一个技能栏高，站在最下面的出生点时人在技能栏上方
func test_desktop_camera_clears_skill_bar() -> void:
	var lv := Shanmen.new()
	lv.setup("shaolin", "jiemai")
	lv.profile = Profile.new()
	tree.root.add_child(lv)
	lv.hud.mobile = false
	lv._update_camera(DT)
	check_eq(lv.camera.limit_bottom, int(lv.map_size.y) + LevelBase.DESK_BAR_PAD, "电脑镜头下沿多留技能栏高")
	var cam_y := minf(lv.me.pos.y - 16.0, lv.map_size.y + LevelBase.DESK_BAR_PAD - 270.0)
	check(lv.me.pos.y - cam_y + 270.0 < 420.0, "出生点在技能栏（屏幕 y≥420）上方")
	lv.hud.mobile = true
	lv._update_camera(DT)
	check_eq(lv.camera.limit_bottom, int(lv.map_size.y), "手机不多留")
	lv.free()


## 中文断行：标点不落到行首
func test_wrap_cjk() -> void:
	for s in ["沈家卧房醒来，枕下压着一封血书。捐香火，直接见方丈。", "茶馆后台醒来，台下黑衣客扔上一锭裹着纸条的银子。扮香客混进寺。"]:
		for line in UiKit.wrap_cjk(s, 184).split("\n"):
			check(not "，。、；：！？".contains(line.left(1)), "行首是标点：%s" % line)
