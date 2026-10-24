## #39 手机摇杆：开场醒来的阻塞对话会收起战斗界面，原先这时松开摇杆的事件被丢掉，摇杆锁在最后的方向。
## 四条出身都走一遍：现代车间里上推摇杆（角色真的往上走）→ 醒来对话收起界面 → 松手 / 松手事件丢失 →
## 对话放完后摇杆回中、角色不再自己走，再拖一次能照常移动。
extends "res://tests/test_case.gd"

const DT := 1.0 / 60.0


func _prologue(o: String) -> Prologue:
	var lv := Prologue.new()
	lv.setup("shaolin", "jiemai")
	lv.origin = o
	lv.profile = Profile.new()
	tree.root.add_child(lv)
	lv.hud.mobile = true
	return lv


func _touch(hud: Hud, index: int, at: Vector2, pressed: bool) -> void:
	var e := InputEventScreenTouch.new()
	e.index = index
	e.position = at
	e.pressed = pressed
	hud._input(e)


func _drag(hud: Hud, index: int, at: Vector2) -> void:
	var e := InputEventScreenDrag.new()
	e.index = index
	e.position = at
	hud._input(e)


func _steps(lv: Prologue, n: int) -> void:
	for i in n:
		lv._physics_process(DT)


## 醒来对话放完，进到能走动的教学
func _finish_wake(lv: Prologue) -> void:
	lv.dialogue.hide()
	lv._on_dialogue_done()
	_steps(lv, 2)


func test_stick_released_while_hidden() -> void:
	for o in Story.ORIGINS:
		var lv := _prologue(o)
		var hud := lv.hud
		var c := Hud.STICK_CENTER
		_touch(hud, 7, c, true)
		_drag(hud, 7, c + Vector2(0, -Hud.STICK_R * 1.5))   # 拖到摇杆上沿之外
		var y0 := lv.me.pos.y
		_steps(lv, 20)
		check(lv.me.pos.y < y0 - 10.0, "%s：上推摇杆，角色往上走" % o)
		lv._wake()
		_steps(lv, 1)
		check(not hud.visible, "%s：醒来对话收起战斗界面" % o)
		_touch(hud, 7, c + Vector2(0, -Hud.STICK_R * 1.5), false)   # 收起期间松手
		_finish_wake(lv)
		check(hud.visible, "%s：对话放完界面回来" % o)
		check_eq(hud.touch_move, Vector2.ZERO, "%s：摇杆回中" % o)
		var p := lv.me.pos
		_steps(lv, 30)
		check(lv.me.pos.distance_to(p) < 1.0, "%s：没按摇杆时角色不自己走（走了 %.0f）" % [o, lv.me.pos.distance_to(p)])
		_touch(hud, 12, c, true)
		_drag(hud, 12, c + Vector2(Hud.STICK_R, 0))
		var x0 := lv.me.pos.x
		_steps(lv, 20)
		check(lv.me.pos.x > x0 + 10.0, "%s：再拖一次摇杆，角色照常往右走" % o)
		_touch(hud, 12, c + Vector2(Hud.STICK_R, 0), false)
		lv.free()


## 松手事件整个丢了（比如浏览器没送到）：界面一收起就清掉触点，回来后新的一指能接管摇杆
func test_stick_reset_when_release_lost() -> void:
	var lv := _prologue("langzhong")
	var hud := lv.hud
	var c := Hud.STICK_CENTER
	_touch(hud, 3, c, true)
	_drag(hud, 3, c + Vector2(0, -Hud.STICK_R))
	_touch(hud, 4, Vector2(Hud.MOBILE[0][0], Hud.MOBILE[0][1]), true)   # 另一指按着普攻
	lv._wake()
	_steps(lv, 1)
	_finish_wake(lv)
	check_eq(hud.touch_move, Vector2.ZERO, "摇杆回中")
	check(hud.touch_held.is_empty(), "按住的键也松开了")
	_touch(hud, 9, c, true)
	_drag(hud, 9, c + Vector2(-Hud.STICK_R, 0))
	check(hud.touch_move.x < -0.5, "新的一指接管摇杆")
	lv.free()
