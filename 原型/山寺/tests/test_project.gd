## 工程设置：分辨率、像素风渲染与输入映射没被编辑器改坏。
extends "res://tests/test_case.gd"

const ACTIONS := ["move_up", "move_down", "move_left", "move_right", "aim_up", "aim_down", "aim_left", "aim_right",
	"attack", "skill_1", "skill_2", "skill_3", "utility", "combo", "dodge", "cancel", "interact", "inventory", "pause", "potion"]


func test_display() -> void:
	check_eq(ProjectSettings.get_setting("display/window/size/viewport_width"), 960, "内部宽度")
	check_eq(ProjectSettings.get_setting("display/window/size/viewport_height"), 540, "内部高度")
	check_eq(ProjectSettings.get_setting("display/window/stretch/scale_mode"), "integer", "整数倍拉伸")
	check_eq(ProjectSettings.get_setting("rendering/textures/canvas_textures/default_texture_filter"), 0, "最近邻过滤")


func test_input_actions() -> void:
	for action in ACTIONS:
		check(InputMap.has_action(action), "缺少输入动作 " + action)
		if InputMap.has_action(action):
			check(not InputMap.action_get_events(action).is_empty(), action + " 没有绑定任何按键")


func test_every_action_has_gamepad() -> void:
	for action in ACTIONS:
		if not InputMap.has_action(action):
			continue
		var pad := InputMap.action_get_events(action).any(func(e): return e is InputEventJoypadButton or e is InputEventJoypadMotion)
		check(pad, action + " 没有手柄绑定")


func test_main_scene_loads() -> void:
	var path: String = ProjectSettings.get_setting("application/run/main_scene", "")
	check(path != "", "没有设置主场景")
	if path != "":
		check(load(path) is PackedScene, "主场景无法加载：" + path)


## #28 套到可卷动的地图：站到每个关键物 / 出生点 / 敌人位置上时（镜头在地图边缘会被夹住），
## 这个点在屏幕上都不落进手机触屏操作区；单屏的茶棚在手机上直接把操作区从可走区里挖掉
func test_mobile_layout_keeps_targets_clear() -> void:
	var levels := {
		"山门": [Shanmen.TORCHES + Shanmen.LOULUO + [Shanmen.START, Shanmen.ARENA_START, Shanmen.BOSS_WAIT]
			+ Shanmen.ENTRY.values().map(func(e): return e.at) + Shanmen.ENTRY.values().filter(func(e): return not e.npc.is_empty()).map(func(e): return e.npc[1])],
		"藏经阁": [Cangjingge.LOULUO + Cangjingge.PROPS.map(func(x): return x[1]) + [Cangjingge.START, Cangjingge.HALL_START, Cangjingge.DULAO_AT]],
		"大雄宝殿": [Daxiongbaodian.PILES.map(func(x): return x[1]) + Daxiongbaodian.SPOTS + [Daxiongbaodian.START, Daxiongbaodian.HALL_START,
			Daxiongbaodian.BALLISTA_AT, Daxiongbaodian.CHEST_AT, Daxiongbaodian.JINGANG_AT]],
	}
	for name in levels:
		for p: Vector2 in levels[name][0]:
			var s := LevelBase.screen_pos(p, p, Vector2(1920, 1080))
			check(not LevelBase.in_mobile_zone(s), "%s：%s 站上去时在屏幕 %s，落进手机操作区" % [name, p, s])
	# 出身开场都是单屏（镜头不动）：关键点直接用屏幕坐标查，手机上可走区挖掉操作区后它们还得走得到
	for o in Prologue.LAYOUTS:
		var lay: Dictionary = Prologue.LAYOUTS[o]
		var walk := LevelBase.mobile_bounds(Prologue.floor_of(o))
		for z: Rect2 in Hud.MOBILE_ZONES:
			check(not Geometry2D.is_point_in_polygon(z.get_center(), walk), "%s 开场手机可走区挖掉了操作区 %s" % [o, z])
		for p: Vector2 in [lay.start, lay.move, lay.prop[1], lay.trainer, lay.info, lay.exit]:
			check(not LevelBase.in_mobile_zone(p), "%s 开场：%s 落在手机操作区" % [o, p])
			check(Geometry2D.is_point_in_polygon(p, walk) or p == lay.exit, "%s 开场：%s 不在手机可走区里" % [o, p])


## #35 首页：有存档时「上次出身」与存档摘要不压在按钮上；出身卡片的介绍在卡片宽度内换行
func test_title_and_origin_text_fit() -> void:
	var m: Node = load("res://scripts/game/main.gd").new()
	tree.root.add_child(m)
	m.profile = Profile.new()
	m.profile.exists = true
	m.profile.origin = "langzhong"
	m._title()
	var panel: Control = m._layer.get_child(m._layer.get_child_count() - 1)
	var buttons := []
	var labels := []
	for c in panel.get_children():
		if c is Button:
			buttons.append(Rect2(c.position, c.custom_minimum_size))
		elif c is Label:
			labels.append(c)
	check_eq(buttons.size(), 2, "首页两个按钮")
	var saw_origin := false
	for l in labels:
		saw_origin = saw_origin or l.text.begins_with("上次出身")
		for b in buttons:
			check(not Rect2(l.position, l.size).intersects(b), "「%s」压在按钮上" % l.text)
	check(saw_origin, "有存档时显示上次出身")
	m._origin_select()
	var cards := 0
	for c in m._layer.get_children():
		if c is Button and c.get_child_count() >= 3:
			var desc: Label = c.get_child(c.get_child_count() - 2)
			cards += 1
			check(desc.size.x <= c.size.x - 24.0 + 0.5, "%s 的介绍宽 %d，超出卡片" % [desc.text.left(4), int(desc.size.x)])
			check(desc.get_line_count() > 1, "%s 的介绍没有换行" % desc.text.left(4))
			check(desc.get_line_count() * 20 <= desc.size.y, "%s 的介绍放不下" % desc.text.left(4))
	check_eq(cards, 4, "四张出身卡片")
	m.free()
