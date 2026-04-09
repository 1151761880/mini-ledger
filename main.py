import json
import os
import base64
import io
from datetime import datetime
from uuid import uuid4

import flet as ft
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 设置中文字体
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

DATA_FILE = "ledger_data.json"
CUSTOM_CATEGORY_FILE = "custom_categories.json"
BUDGET_FILE = "budget_data.json"
TEMPLATE_FILE = "template_data.json"
TRASH_FILE = "trash_data.json"
BACKUP_DIR = "backups"
EXPORT_DIR = "exports"
TRANSPARENT_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+Xn3wAAAAASUVORK5CYII="
PIE_COLORS_HEX = ["#4FC3F7", "#EF5350", "#66BB6A", "#FFA726", "#AB47BC", "#26A69A", "#EC407A", "#FFCA28", "#26C6DA", "#D4E157"]

CATEGORY_OPTIONS = [
    "餐饮",
    "交通",
    "娱乐",
    "购物",
    "其他",
]

CATEGORY_ICON = {
    "餐饮": "🍔",
    "交通": "🚌",
    "娱乐": "🎮",
    "购物": "🛍️",
    "其他": "✨",
}

INCOME_CATEGORY_OPTIONS = [
    "工资",
    "补贴",
    "其他收入",
]
 

def _safe_load_json(path, default_value):
    if not os.path.exists(path):
        return default_value
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception:
        return default_value


def _safe_write_json(path, data):
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp_path, path)


def load_budget_data():
    data = _safe_load_json(BUDGET_FILE, {"monthly": 0.0, "by_category": {}})
    if not isinstance(data, dict):
        return {"monthly": 0.0, "by_category": {}}
    if "monthly" not in data:
        data["monthly"] = 0.0
    if "by_category" not in data or not isinstance(data["by_category"], dict):
        data["by_category"] = {}
    return data


def save_budget_data(data):
    _safe_write_json(BUDGET_FILE, data)


def load_template_data():
    data = _safe_load_json(TEMPLATE_FILE, [])
    if not isinstance(data, list):
        return []
    return data


def save_template_data(data):
    _safe_write_json(TEMPLATE_FILE, data)


def load_trash_data():
    data = _safe_load_json(TRASH_FILE, [])
    if not isinstance(data, list):
        return []
    return data


def save_trash_data(data):
    _safe_write_json(TRASH_FILE, data)

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            return data
    except Exception:
        return []

def save_data(data):
    _safe_write_json(DATA_FILE, data)

def load_custom_categories():
    if not os.path.exists(CUSTOM_CATEGORY_FILE):
        return []
    try:
        with open(CUSTOM_CATEGORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            return data
    except Exception:
        return []

def save_custom_categories(data):
    _safe_write_json(CUSTOM_CATEGORY_FILE, data)

def main(page: ft.Page):
    page.title = "极简记账本"
    page.scroll = "auto"
    page.window_width = 760
    page.window_height = 800

    records = load_data()
    custom_categories = load_custom_categories()
    budget_data = load_budget_data()
    template_data = load_template_data()
    trash_records = load_trash_data()
    undo_stack = []
    backup_files = []
    all_categories = CATEGORY_OPTIONS + custom_categories

    # 过滤条件
    w_filter_type = ft.Dropdown(
        label="类型",
        width=120,
        options=[
            ft.dropdown.Option("全部"),
            ft.dropdown.Option("收入"),
            ft.dropdown.Option("支出"),
        ],
        value="全部",
    )
    w_filter_month = ft.Dropdown(
        label="月份",
        width=140,
        options=[
            ft.dropdown.Option("全部"),
        ],
        value="全部",
    )
    w_filter_category = ft.Dropdown(
        label="分类",
        width=140,
        options=[ft.dropdown.Option("全部")] + [ft.dropdown.Option(c) for c in all_categories + INCOME_CATEGORY_OPTIONS],
        value="全部",
    )

    def on_filter_type_change(e):
        update_filter_category_options()
        page.update()

    w_filter_type.on_change = on_filter_type_change

    def on_filter_query(e):
        update_display()

    def on_filter_reset(e):
        w_filter_type.value = "全部"
        w_filter_month.value = "全部"
        w_filter_category.value = "全部"
        update_filter_category_options()
        update_display()

    def get_month_options():
        months = sorted({r.get("date", "")[:7] for r in records if r.get("date")}, reverse=True)
        options = [ft.dropdown.Option("全部")] + [ft.dropdown.Option(m) for m in months]
        return options

    def update_filters_month_options():
        w_filter_month.options = get_month_options()
        if w_filter_month.value not in [o.key for o in w_filter_month.options]:
            w_filter_month.value = "全部"

    def update_filter_category_options():
        ft_val = w_filter_type.value
        if ft_val == "收入":
            cats = INCOME_CATEGORY_OPTIONS
        elif ft_val == "支出":
            cats = list(all_categories)
        else:
            cats = list(all_categories) + INCOME_CATEGORY_OPTIONS
        # 去重保持顺序
        seen = set()
        unique_cats = []
        for c in cats:
            if c not in seen:
                seen.add(c)
                unique_cats.append(c)
        w_filter_category.options = [ft.dropdown.Option("全部")] + [ft.dropdown.Option(c) for c in unique_cats]
        if w_filter_category.value not in ["全部"] + unique_cats:
            w_filter_category.value = "全部"

    # 输入区
    txt_amount = ft.TextField(label="支出金额", keyboard_type=ft.KeyboardType.NUMBER, width=160)
    dd_category = ft.Dropdown(label="分类", width=160, value=all_categories[0], options=[ft.dropdown.Option(c) for c in all_categories])
    txt_custom_category = ft.TextField(label="自定义分类", width=120)
    txt_note = ft.TextField(label="备注", width=260)
    txt_date = ft.TextField(label="日期", value=datetime.now().strftime("%Y-%m-%d"), width=160)

    # 收入输入区
    txt_income_amount = ft.TextField(label="收入金额", keyboard_type=ft.KeyboardType.NUMBER, width=160)
    dd_income_category = ft.Dropdown(label="收入分类", width=160, value=INCOME_CATEGORY_OPTIONS[0], options=[ft.dropdown.Option(c) for c in INCOME_CATEGORY_OPTIONS])
    txt_income_note = ft.TextField(label="收入备注", width=260)
    txt_income_date = ft.TextField(label="收入日期", value=datetime.now().strftime("%Y-%m-%d"), width=160)

    # 预算管理
    txt_budget_monthly = ft.TextField(label="月总预算", width=140, value=str(budget_data.get("monthly", 0.0)))
    dd_budget_category = ft.Dropdown(label="分类预算", width=140, value=all_categories[0], options=[ft.dropdown.Option(c) for c in all_categories])
    txt_budget_category_amount = ft.TextField(label="分类预算金额", width=140)
    txt_budget_status = ft.Text("预算状态：未设置", size=14)

    # 固定模板
    dd_template_type = ft.Dropdown(
        label="模板类型",
        width=120,
        value="expense",
        options=[ft.dropdown.Option("expense", "支出"), ft.dropdown.Option("income", "收入")],
    )
    txt_template_amount = ft.TextField(label="模板金额", width=120)
    txt_template_category = ft.TextField(label="模板分类", width=120)
    txt_template_note = ft.TextField(label="模板备注", width=180)
    txt_template_day = ft.TextField(label="每月执行日(1-28)", width=120, value="1")
    lv_templates = ft.ListView(height=140, spacing=6)

    # 回收站与撤销
    txt_undo_status = ft.Text("撤销状态：无", size=13)
    lv_trash = ft.ListView(height=120, spacing=6)

    # 导入导出
    txt_import_path = ft.TextField(label="导入文件路径(.json/.csv)", width=360, value="import_ledger.json")
    txt_export_status = ft.Text("导入导出：待操作", size=13)

    # 数据安全
    dd_backup_file = ft.Dropdown(label="备份文件", width=360, options=[])
    txt_backup_status = ft.Text("备份状态：待操作", size=13)

    # 图表区 (文本 + 饼状图)
    txt_chart = ft.Text("支出统计：\n无数据", size=16)
    txt_income_chart = ft.Text("收入统计：\n无数据", size=16)
    img_pie_expense = ft.Image(src=f"data:image/png;base64,{TRANSPARENT_PNG_BASE64}", width=220, height=220, visible=False)
    img_pie_income = ft.Image(src=f"data:image/png;base64,{TRANSPARENT_PNG_BASE64}", width=220, height=220, visible=False)
    legend_pie_expense = ft.Column(spacing=3)
    legend_pie_income = ft.Column(spacing=3)

    lv_records = ft.ListView(expand=True, spacing=8)

    def _show_msg(text):
        page.snack_bar = ft.SnackBar(ft.Text(text))
        page.snack_bar.open = True
        page.update()

    def _persist_all():
        save_data(records)
        save_custom_categories(custom_categories)
        save_budget_data(budget_data)
        save_template_data(template_data)
        save_trash_data(trash_records)

    def create_backup_snapshot(reason="manual"):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_payload = {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "reason": reason,
            "records": records,
            "custom_categories": custom_categories,
            "budget_data": budget_data,
            "template_data": template_data,
            "trash_records": trash_records,
        }
        backup_path = os.path.join(BACKUP_DIR, f"backup_{ts}_{reason}.json")
        _safe_write_json(backup_path, backup_payload)
        return backup_path

    def refresh_backup_options():
        nonlocal backup_files
        os.makedirs(BACKUP_DIR, exist_ok=True)
        files = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".json")]
        files.sort(reverse=True)
        backup_files = files
        dd_backup_file.options = [ft.dropdown.Option(f) for f in files]
        if files and dd_backup_file.value not in files:
            dd_backup_file.value = files[0]
        if not files:
            dd_backup_file.value = None

    def on_manual_backup(e):
        path = create_backup_snapshot("manual")
        refresh_backup_options()
        txt_backup_status.value = f"备份成功：{path}"
        _show_msg("手动备份完成")

    def on_restore_backup(e):
        nonlocal records, custom_categories, budget_data, template_data, trash_records
        if not dd_backup_file.value:
            _show_msg("请先选择备份文件")
            return
        path = os.path.join(BACKUP_DIR, dd_backup_file.value)
        data = _safe_load_json(path, {})
        if not isinstance(data, dict):
            _show_msg("备份文件格式错误")
            return
        create_backup_snapshot("before_restore")
        records = data.get("records", []) if isinstance(data.get("records", []), list) else []
        custom_categories = data.get("custom_categories", []) if isinstance(data.get("custom_categories", []), list) else []
        budget_data = data.get("budget_data", {"monthly": 0.0, "by_category": {}}) if isinstance(data.get("budget_data", {}), dict) else {"monthly": 0.0, "by_category": {}}
        template_data = data.get("template_data", []) if isinstance(data.get("template_data", []), list) else []
        trash_records = data.get("trash_records", []) if isinstance(data.get("trash_records", []), list) else []
        all_categories.clear()
        all_categories.extend(CATEGORY_OPTIONS + custom_categories)
        _persist_all()
        txt_budget_monthly.value = str(budget_data.get("monthly", 0.0))
        update_category_options()
        update_template_list()
        update_trash_list()
        txt_backup_status.value = f"已恢复：{dd_backup_file.value}"
        update_display()
        _show_msg("数据已从备份恢复")

    def update_budget_status():
        month = datetime.now().strftime("%Y-%m")
        month_records = [r for r in records if r.get("date", "").startswith(month)]
        month_expense = sum(float(r.get("amount", 0) or 0) for r in month_records if not _is_income(r))
        monthly_budget = float(budget_data.get("monthly", 0) or 0)
        if monthly_budget > 0:
            ratio = month_expense / monthly_budget * 100
            budget_text = f"预算状态：本月支出 ¥{month_expense:.2f} / 预算 ¥{monthly_budget:.2f} ({ratio:.1f}%)"
        else:
            budget_text = f"预算状态：本月支出 ¥{month_expense:.2f} / 未设置总预算"

        category_lines = []
        for cat, val in budget_data.get("by_category", {}).items():
            try:
                budget_amount = float(val or 0)
            except Exception:
                budget_amount = 0
            cat_expense = sum(float(r.get("amount", 0) or 0) for r in month_records if not _is_income(r) and r.get("category") == cat)
            if budget_amount > 0:
                category_lines.append(f"{cat}:{cat_expense:.0f}/{budget_amount:.0f}")
        if category_lines:
            budget_text += " | 分类:" + "、".join(category_lines)
        txt_budget_status.value = budget_text

    def on_save_monthly_budget(e):
        try:
            val = float((txt_budget_monthly.value or "0").strip())
            if val < 0:
                raise ValueError()
        except Exception:
            _show_msg("月总预算必须是大于等于0的数字")
            return
        budget_data["monthly"] = val
        save_budget_data(budget_data)
        update_budget_status()
        _show_msg("月总预算已保存")

    def on_save_category_budget(e):
        cat = dd_budget_category.value
        if not cat:
            _show_msg("请选择分类")
            return
        try:
            val = float((txt_budget_category_amount.value or "0").strip())
            if val < 0:
                raise ValueError()
        except Exception:
            _show_msg("分类预算必须是大于等于0的数字")
            return
        budget_data.setdefault("by_category", {})[cat] = val
        save_budget_data(budget_data)
        txt_budget_category_amount.value = ""
        update_budget_status()
        page.update()
        _show_msg("分类预算已保存")

    def _append_record_with_undo(new_record, action_type):
        create_backup_snapshot("before_add")
        records.append(new_record)
        undo_stack.append({"action": action_type, "record_id": new_record.get("id")})
        save_data(records)

    def update_template_list():
        lv_templates.controls.clear()
        for t in sorted(template_data, key=lambda x: x.get("created_at", ""), reverse=True):
            tid = t.get("id")
            t_type = "收入" if t.get("type") == "income" else "支出"
            t_text = f"{t_type} | 每月{t.get('day', 1)}日 | ¥{float(t.get('amount', 0) or 0):.2f} | {t.get('category', '')} | {t.get('note', '')}"
            lv_templates.controls.append(
                ft.Row([
                    ft.Text(t_text, size=12, width=430, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Switch(value=bool(t.get("enabled", True)), on_change=lambda e, tid=tid: toggle_template_enabled(tid, e.control.value)),
                    ft.IconButton(icon=ft.Icons.PLAY_ARROW, tooltip="立即执行", on_click=lambda e, tid=tid: run_single_template(tid)),
                    ft.IconButton(icon=ft.Icons.DELETE, tooltip="删除模板", on_click=lambda e, tid=tid: delete_template(tid)),
                ], spacing=4)
            )

    def add_template(e):
        t_type = dd_template_type.value or "expense"
        try:
            amount = float((txt_template_amount.value or "").strip())
            if amount <= 0:
                raise ValueError()
        except Exception:
            _show_msg("模板金额必须大于0")
            return
        category = (txt_template_category.value or "").strip()
        if not category:
            _show_msg("模板分类不能为空")
            return
        note = (txt_template_note.value or "").strip()
        try:
            day = int((txt_template_day.value or "1").strip())
            if day < 1 or day > 28:
                raise ValueError()
        except Exception:
            _show_msg("模板执行日必须在1-28")
            return

        template = {
            "id": str(uuid4()),
            "type": t_type,
            "amount": amount,
            "category": category,
            "note": note,
            "day": day,
            "enabled": True,
            "last_run_month": "",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        template_data.append(template)
        save_template_data(template_data)
        txt_template_amount.value = ""
        txt_template_category.value = ""
        txt_template_note.value = ""
        txt_template_day.value = "1"
        update_template_list()
        page.update()
        _show_msg("模板已新增")

    def toggle_template_enabled(tid, enabled):
        for t in template_data:
            if t.get("id") == tid:
                t["enabled"] = bool(enabled)
                break
        save_template_data(template_data)

    def delete_template(tid):
        nonlocal template_data
        template_data = [t for t in template_data if t.get("id") != tid]
        save_template_data(template_data)
        update_template_list()
        page.update()

    def _run_template_to_record(t, target_month):
        run_date = f"{target_month}-{int(t.get('day', 1)):02d}"
        new_record = {
            "id": str(uuid4()),
            "amount": float(t.get("amount", 0) or 0),
            "category": t.get("category", "其他"),
            "note": f"[模板]{t.get('note', '')}",
            "date": run_date,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "income" if t.get("type") == "income" else "expense",
        }
        _append_record_with_undo(new_record, "add")

    def run_single_template(tid):
        target_month = datetime.now().strftime("%Y-%m")
        for t in template_data:
            if t.get("id") == tid:
                _run_template_to_record(t, target_month)
                t["last_run_month"] = target_month
                save_template_data(template_data)
                update_display()
                _show_msg("模板已执行")
                return

    def run_templates_for_current_month(e=None, silent=False):
        target_month = datetime.now().strftime("%Y-%m")
        count = 0
        for t in template_data:
            if not t.get("enabled", True):
                continue
            if t.get("last_run_month") == target_month:
                continue
            _run_template_to_record(t, target_month)
            t["last_run_month"] = target_month
            count += 1
        save_template_data(template_data)
        if count > 0:
            update_display()
        if not silent:
            _show_msg(f"本月模板执行完成，共 {count} 条")

    def update_trash_list():
        lv_trash.controls.clear()
        for item in sorted(trash_records, key=lambda x: x.get("deleted_at", ""), reverse=True):
            rid = item.get("id")
            cat = item.get("category", "")
            date = item.get("date", "")
            amount = float(item.get("amount", 0) or 0)
            lv_trash.controls.append(
                ft.Row([
                    ft.Text(f"{date} | {cat} | ¥{amount:.2f}", size=12, width=360, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.IconButton(icon=ft.Icons.RESTORE_FROM_TRASH, tooltip="恢复", on_click=lambda e, rid=rid: restore_from_trash(rid)),
                    ft.IconButton(icon=ft.Icons.DELETE_FOREVER, tooltip="彻底删除", on_click=lambda e, rid=rid: purge_from_trash(rid)),
                ], spacing=4)
            )

    def restore_from_trash(rid):
        nonlocal trash_records
        target = None
        remain = []
        for item in trash_records:
            if item.get("id") == rid and target is None:
                target = item
            else:
                remain.append(item)
        if target is None:
            return
        trash_records = remain
        target.pop("deleted_at", None)
        records.append(target)
        save_trash_data(trash_records)
        save_data(records)
        update_trash_list()
        update_display()
        _show_msg("已从回收站恢复")

    def purge_from_trash(rid):
        nonlocal trash_records
        trash_records = [x for x in trash_records if x.get("id") != rid]
        save_trash_data(trash_records)
        update_trash_list()
        page.update()

    def clear_trash(e):
        nonlocal trash_records
        trash_records = []
        save_trash_data(trash_records)
        update_trash_list()
        page.update()
        _show_msg("回收站已清空")

    def undo_last_action(e):
        if not undo_stack:
            txt_undo_status.value = "撤销状态：无可撤销操作"
            page.update()
            return
        action = undo_stack.pop()
        if action.get("action") == "add":
            rid = action.get("record_id")
            nonlocal_records = [r for r in records if r.get("id") != rid]
            records.clear()
            records.extend(nonlocal_records)
            save_data(records)
            txt_undo_status.value = "撤销状态：已撤销最近新增记录"
        elif action.get("action") == "delete":
            rec = action.get("record")
            idx = int(action.get("index", len(records)))
            if rec:
                if idx < 0:
                    idx = 0
                if idx > len(records):
                    idx = len(records)
                records.insert(idx, rec)
                save_data(records)
                txt_undo_status.value = "撤销状态：已撤销最近删除记录"
        elif action.get("action") == "import":
            ids = set(action.get("record_ids", []))
            records[:] = [r for r in records if r.get("id") not in ids]
            save_data(records)
            txt_undo_status.value = "撤销状态：已撤销最近导入"
        update_display()

    def export_json(e):
        os.makedirs(EXPORT_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(EXPORT_DIR, f"ledger_export_{ts}.json")
        payload = {
            "records": records,
            "custom_categories": custom_categories,
            "budget_data": budget_data,
            "template_data": template_data,
            "trash_records": trash_records,
        }
        _safe_write_json(path, payload)
        txt_export_status.value = f"已导出 JSON：{path}"
        _show_msg("JSON 导出成功")

    def export_csv(e):
        os.makedirs(EXPORT_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(EXPORT_DIR, f"ledger_export_{ts}.csv")
        lines = ["id,type,date,category,amount,note,created_at"]
        for r in records:
            row = [
                str(r.get("id", "")).replace(",", " "),
                str(r.get("type", "")).replace(",", " "),
                str(r.get("date", "")).replace(",", " "),
                str(r.get("category", "")).replace(",", " "),
                str(r.get("amount", "")).replace(",", " "),
                str(r.get("note", "")).replace(",", " "),
                str(r.get("created_at", "")).replace(",", " "),
            ]
            lines.append(",".join(row))
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        txt_export_status.value = f"已导出 CSV：{path}"
        _show_msg("CSV 导出成功")

    def import_records(e):
        path = (txt_import_path.value or "").strip()
        if not path:
            _show_msg("请填写导入文件路径")
            return
        if not os.path.exists(path):
            _show_msg("导入文件不存在")
            return

        imported = []
        try:
            if path.lower().endswith(".json"):
                data = _safe_load_json(path, [])
                if isinstance(data, dict) and isinstance(data.get("records"), list):
                    data = data["records"]
                if not isinstance(data, list):
                    raise ValueError("JSON 必须是记录数组或含 records")
                for r in data:
                    if not isinstance(r, dict):
                        continue
                    nr = {
                        "id": str(r.get("id") or uuid4()),
                        "amount": float(r.get("amount", 0) or 0),
                        "category": str(r.get("category", "其他")),
                        "note": str(r.get("note", "")),
                        "date": str(r.get("date", datetime.now().strftime("%Y-%m-%d"))),
                        "created_at": str(r.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
                        "type": "income" if str(r.get("type", "expense")) == "income" else "expense",
                    }
                    imported.append(nr)
            elif path.lower().endswith(".csv"):
                with open(path, "r", encoding="utf-8") as f:
                    lines = [ln.strip() for ln in f.readlines() if ln.strip()]
                if not lines:
                    raise ValueError("CSV 为空")
                header = [x.strip() for x in lines[0].split(",")]
                for ln in lines[1:]:
                    cols = [x.strip() for x in ln.split(",")]
                    row = {header[i]: cols[i] if i < len(cols) else "" for i in range(len(header))}
                    nr = {
                        "id": str(row.get("id") or uuid4()),
                        "amount": float(row.get("amount", 0) or 0),
                        "category": str(row.get("category", "其他")),
                        "note": str(row.get("note", "")),
                        "date": str(row.get("date", datetime.now().strftime("%Y-%m-%d"))),
                        "created_at": str(row.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
                        "type": "income" if str(row.get("type", "expense")) == "income" else "expense",
                    }
                    imported.append(nr)
            else:
                _show_msg("仅支持 .json 或 .csv")
                return
        except Exception as ex:
            _show_msg(f"导入失败: {ex}")
            return

        if not imported:
            _show_msg("没有可导入记录")
            return

        create_backup_snapshot("before_import")
        existing_ids = {r.get("id") for r in records}
        append_records = [r for r in imported if r.get("id") not in existing_ids]
        records.extend(append_records)
        save_data(records)
        undo_stack.append({"action": "import", "record_ids": [r.get("id") for r in append_records]})
        txt_export_status.value = f"导入成功：新增 {len(append_records)} 条"
        update_display()
        _show_msg(f"导入完成：新增 {len(append_records)} 条")

    def _is_income(r):
        return r.get("type") == "income" or r.get("category") in INCOME_CATEGORY_OPTIONS

    def get_filtered_records():
        filtered = records
        # 月份筛选
        if w_filter_month.value != "全部":
            filtered = [r for r in filtered if r.get("date", "").startswith(w_filter_month.value)]
        # 类型筛选
        ft_val = w_filter_type.value
        if ft_val == "收入":
            filtered = [r for r in filtered if _is_income(r)]
        elif ft_val == "支出":
            filtered = [r for r in filtered if not _is_income(r)]
        # 分类筛选
        if w_filter_category.value != "全部":
            filtered = [r for r in filtered if r.get("category") == w_filter_category.value]
        return filtered

    def _get_latest_month():
        months = sorted({r.get("date", "")[:7] for r in records if r.get("date")}, reverse=True)
        return months[0] if months else None

    def update_chart():
        filtered = get_filtered_records()
        filtered = [r for r in filtered if not _is_income(r)]
        totals = {}
        for r in filtered:
            cat = r.get("category", "其他")
            amount = float(r.get("amount", 0) or 0)
            totals[cat] = totals.get(cat, 0) + amount

        if not totals:
            txt_chart.value = "支出统计：\n无数据"
            img_pie_expense.visible = False
            legend_pie_expense.controls = []
            return

        lines = ["支出统计（按分类）："]
        for cat, total in sorted(totals.items(), key=lambda x: -x[1]):
            lines.append(f"{cat}: ¥{total:.2f}")
        txt_chart.value = "\n".join(lines)

        # 饼状图 - 最新月份支出
        latest = _get_latest_month()
        if latest:
            pie_data = {}
            for r in records:
                if r.get("date", "").startswith(latest) and not _is_income(r):
                    cat = r.get("category", "其他")
                    pie_data[cat] = pie_data.get(cat, 0) + float(r.get("amount", 0) or 0)
            _build_pie_image(img_pie_expense, legend_pie_expense, pie_data, f"{latest} 支出")
        else:
            img_pie_expense.visible = False
            legend_pie_expense.controls = []

    def _build_pie_image(img_ctrl, legend_ctrl, data, title):
        if not data:
            img_ctrl.visible = False
            legend_ctrl.controls = []
            return
        labels = list(data.keys())
        values = list(data.values())
        total = sum(values)
        colors = [PIE_COLORS_HEX[i % len(PIE_COLORS_HEX)] for i in range(len(values))]
        fig, ax = plt.subplots(figsize=(2.5, 2.5), dpi=100)
        wedges, texts, autotexts = ax.pie(
            values, labels=None, autopct=lambda p: f"{p:.0f}%" if p > 5 else "",
            colors=colors, startangle=90,
            textprops={"fontsize": 8},
        )
        for t in autotexts:
            t.set_fontsize(7)
            t.set_color("white")
            t.set_fontweight("bold")
        # 图例
        legend_labels = [f"{l} {v:.0f}元" for l, v in zip(labels, values)]
        ax.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1, 0.5), fontsize=7, frameon=False)
        ax.set_title(title, fontsize=9, fontweight="bold")
        fig.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", transparent=True, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("utf-8")
        img_ctrl.src = f"data:image/png;base64,{b64}"
        img_ctrl.visible = True

        legend_rows = [ft.Text(f"{title} 颜色图例", size=12, weight="bold")]
        for i, (lab, val) in enumerate(zip(labels, values)):
            pct = (val / total * 100) if total else 0
            legend_rows.append(
                ft.Row([
                    ft.Container(width=12, height=12, bgcolor=colors[i], border_radius=2),
                    ft.Text(f"{lab}：¥{val:.2f}（{pct:.1f}%）", size=11),
                ], spacing=6)
            )
        legend_ctrl.controls = legend_rows

    def update_income_chart():
        filtered = get_filtered_income_records()
        totals = {}
        for r in filtered:
            cat = r.get("category", "其他收入")
            amount = float(r.get("amount", 0) or 0)
            totals[cat] = totals.get(cat, 0) + amount
        if not totals:
            txt_income_chart.value = "收入统计：\n无数据"
            img_pie_income.visible = False
            legend_pie_income.controls = []
            return
        lines = ["收入统计（按分类）："]
        for cat, total in sorted(totals.items(), key=lambda x: -x[1]):
            lines.append(f"{cat}: ¥{total:.2f}")
        txt_income_chart.value = "\n".join(lines)

        # 饼状图 - 最新月份收入
        latest = _get_latest_month()
        if latest:
            pie_data = {}
            for r in records:
                if r.get("date", "").startswith(latest) and _is_income(r):
                    cat = r.get("category", "其他收入")
                    pie_data[cat] = pie_data.get(cat, 0) + float(r.get("amount", 0) or 0)
            _build_pie_image(img_pie_income, legend_pie_income, pie_data, f"{latest} 收入")
        else:
            img_pie_income.visible = False
            legend_pie_income.controls = []

    def get_filtered_income_records():
        filtered = get_filtered_records()
        return [r for r in filtered if _is_income(r)]

    def update_list():
        lv_records.controls.clear()
        filtered = get_filtered_records()

        # 时间倒序
        try:
            filtered_sorted = sorted(filtered, key=lambda x: x.get("date", ""), reverse=True)
        except Exception:
            filtered_sorted = filtered

        # 分为收入和支出两组
        income_column = ft.Column([], spacing=4)
        expense_column = ft.Column([], spacing=4)

        def make_delete_btn(rid):
            def handle_delete(e):
                delete_record_by_id(e.control.data)
            return ft.IconButton(icon=ft.Icons.DELETE, tooltip="删除", data=rid, on_click=handle_delete, icon_size=18)

        for r in filtered_sorted:
            cat = r.get("category", "其他")
            note = r.get("note", "")
            date = r.get("date", "")
            amount = float(r.get("amount", 0) or 0)
            is_income = r.get("type") == "income" or cat in INCOME_CATEGORY_OPTIONS
            rid = r.get("id") or r.get("created_at")
            record_row = ft.Container(
                content=ft.Row([
                    ft.Text(CATEGORY_ICON.get(cat, "✨"), size=18, width=26),
                    ft.Text(f"{date}", width=76, size=13, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(cat, width=50, size=13, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(note if note else "", width=56, size=13, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(f"¥{amount:.2f}", color=ft.Colors.GREEN if is_income else ft.Colors.RED, width=68, size=13),
                    make_delete_btn(rid),
                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                padding=2
            )
            if is_income:
                income_column.controls.append(record_row)
            else:
                expense_column.controls.append(record_row)

        # 标题行
        lv_records.controls.append(
            ft.Row([
                ft.Container(ft.Text("收入记录", size=18, weight="bold"), expand=True),
                ft.Container(ft.Text("支出记录", size=18, weight="bold"), expand=True),
            ], spacing=8)
        )
        # 记录行
        lv_records.controls.append(
            ft.Row([
                ft.Container(income_column, expand=True),
                ft.Container(expense_column, expand=True),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.START)
        )

    def update_display():
        update_filters_month_options()
        update_filter_category_options()
        update_budget_status()
        update_template_list()
        update_trash_list()
        update_income_chart()
        update_chart()
        update_list()
        update_summary()
        update_category_manage_row()
        page.update()

    def update_summary():
        filtered = get_filtered_records()
        expense = [r for r in filtered if r.get("type") != "income" and r.get("category") not in INCOME_CATEGORY_OPTIONS]
        income = [r for r in filtered if r.get("type") == "income" or r.get("category") in INCOME_CATEGORY_OPTIONS]
        total_expense = sum(float(r.get("amount", 0) or 0) for r in expense)
        total_income = sum(float(r.get("amount", 0) or 0) for r in income)
        lbl_summary.value = f"总收入：¥{total_income:.2f}  总支出：¥{total_expense:.2f}  结余：¥{total_income - total_expense:.2f}"

    def add_expense(e):
        nonlocal records, custom_categories
        val = txt_amount.value.strip()
        cat = dd_category.value
        custom_cat = txt_custom_category.value.strip()
        note = txt_note.value.strip()
        date = txt_date.value.strip()

        if custom_cat:
            cat = custom_cat
            if custom_cat not in custom_categories and custom_cat not in CATEGORY_OPTIONS:
                custom_categories.append(custom_cat)
                save_custom_categories(custom_categories)
                update_category_options()

        try:
            amount = float(val)
        except Exception:
            page.snack_bar = ft.SnackBar(ft.Text("金额无效，请输入数字"))
            page.snack_bar.open = True
            page.update()
            return

        if amount <= 0:
            page.snack_bar = ft.SnackBar(ft.Text("金额必须大于 0"))
            page.snack_bar.open = True
            page.update()
            return

        # 简单日期校验
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except Exception:
            page.snack_bar = ft.SnackBar(ft.Text("日期格式不正确，请使用 yyyy-mm-dd"))
            page.snack_bar.open = True
            page.update()
            return

        new_record = {
            "id": str(uuid4()),
            "amount": amount,
            "category": cat,
            "note": note,
            "date": date,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "expense",
        }

        _append_record_with_undo(new_record, "add")

        txt_amount.value = ""
        txt_note.value = ""
        txt_custom_category.value = ""
        txt_date.value = datetime.now().strftime("%Y-%m-%d")

        update_display()

    def delete_record_by_id(rid):
        nonlocal records, trash_records
        for i, rec in enumerate(records):
            if rec.get("id") == rid or rec.get("created_at") == rid:
                create_backup_snapshot("before_delete")
                deleted = records.pop(i)
                deleted["deleted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                trash_records.append(deleted)
                undo_stack.append({"action": "delete", "record": {k: v for k, v in deleted.items() if k != "deleted_at"}, "index": i})
                save_data(records)
                save_trash_data(trash_records)
                update_trash_list()
                update_display()
                break

    def delete_custom_category(e, cat):
        nonlocal custom_categories
        if cat in custom_categories:
            custom_categories.remove(cat)
            save_custom_categories(custom_categories)
            update_category_options()
            update_display()

    def update_category_options():
        all_categories.clear()
        all_categories.extend(CATEGORY_OPTIONS + custom_categories)
        dd_category.options = [ft.dropdown.Option(c) for c in all_categories]
        dd_budget_category.options = [ft.dropdown.Option(c) for c in all_categories]
        update_filter_category_options()
        page.update()

    def update_category_manage_row():
        # 分类管理行，显示所有自定义分类和删除按钮
        category_manage_row.controls.clear()
        category_manage_row.controls.append(ft.Text("自定义分类管理："))
        for c in custom_categories:
            category_manage_row.controls.append(
                ft.Container(
                    ft.Row([
                        ft.Text(c),
                        ft.IconButton(ft.Icons.DELETE, tooltip="删除分类", on_click=lambda e, cat=c: delete_custom_category(e, cat)),
                    ]),
                    padding=4
                )
            )
        page.update()

    lbl_summary = ft.Text("总收入：¥0.00  总支出：¥0.00  结余：¥0.00", size=18, weight="bold")

    # 初始化分类管理行
    category_manage_row = ft.Row([], scroll="auto")

    # 收入相关函数，确保在 page.add 之前
    def add_income(e):
        nonlocal records
        val = txt_income_amount.value.strip()
        cat = dd_income_category.value
        note = txt_income_note.value.strip()
        date = txt_income_date.value.strip()
        try:
            amount = float(val)
        except Exception:
            page.snack_bar = ft.SnackBar(ft.Text("收入金额无效，请输入数字"))
            page.snack_bar.open = True
            page.update()
            return
        if amount <= 0:
            page.snack_bar = ft.SnackBar(ft.Text("收入金额必须大于 0"))
            page.snack_bar.open = True
            page.update()
            return
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except Exception:
            page.snack_bar = ft.SnackBar(ft.Text("日期格式不正确，请使用 yyyy-mm-dd"))
            page.snack_bar.open = True
            page.update()
            return
        new_record = {
            "id": str(uuid4()),
            "amount": amount,
            "category": cat,
            "note": note,
            "date": date,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "income"
        }
        _append_record_with_undo(new_record, "add")
        txt_income_amount.value = ""
        txt_income_note.value = ""
        txt_income_date.value = datetime.now().strftime("%Y-%m-%d")
        update_display()

    page.add(
        ft.Column(
            [
                ft.Text("极简记账本", size=28, weight="bold"),
                ft.Row([lbl_summary], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row(
                    [
                        txt_amount,
                        dd_category,
                        txt_custom_category,
                        txt_note,
                        txt_date,
                        ft.Button("记一笔支出", on_click=add_expense),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    scroll="auto",
                ),
                ft.Row(
                    [
                        txt_income_amount,
                        dd_income_category,
                        txt_income_note,
                        txt_income_date,
                        ft.Button("记一笔收入", on_click=add_income),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    scroll="auto",
                ),
                category_manage_row,
                ft.Divider(),
                ft.Text("预算管理", size=18, weight="bold"),
                ft.Row([
                    txt_budget_monthly,
                    ft.Button("保存月预算", on_click=on_save_monthly_budget),
                    dd_budget_category,
                    txt_budget_category_amount,
                    ft.Button("保存分类预算", on_click=on_save_category_budget),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER, scroll="auto"),
                txt_budget_status,
                ft.Divider(),
                ft.Text("固定模板", size=18, weight="bold"),
                ft.Row([
                    dd_template_type,
                    txt_template_amount,
                    txt_template_category,
                    txt_template_note,
                    txt_template_day,
                    ft.Button("新增模板", on_click=add_template),
                    ft.Button("执行本月模板", on_click=run_templates_for_current_month),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER, scroll="auto"),
                lv_templates,
                ft.Divider(),
                ft.Text("回收站与撤销", size=18, weight="bold"),
                ft.Row([
                    ft.Button("撤销上一步", on_click=undo_last_action),
                    ft.Button("清空回收站", on_click=clear_trash),
                    txt_undo_status,
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                lv_trash,
                ft.Divider(),
                ft.Text("导入导出", size=18, weight="bold"),
                ft.Row([
                    txt_import_path,
                    ft.Button("导入记录", on_click=import_records),
                    ft.Button("导出JSON", on_click=export_json),
                    ft.Button("导出CSV", on_click=export_csv),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER, scroll="auto"),
                txt_export_status,
                ft.Divider(),
                ft.Text("数据安全", size=18, weight="bold"),
                ft.Row([
                    dd_backup_file,
                    ft.Button("手动备份", on_click=on_manual_backup),
                    ft.Button("恢复所选备份", on_click=on_restore_backup),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER, scroll="auto"),
                txt_backup_status,
                ft.Divider(),
                ft.Row([
                    w_filter_type, w_filter_month, w_filter_category,
                    ft.Button("🔍 查询", on_click=on_filter_query),
                    ft.Button("重置", on_click=on_filter_reset),
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([
                    ft.Container(txt_income_chart, width=200),
                    img_pie_income,
                    legend_pie_income,
                ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
                ft.Row([
                    ft.Container(txt_chart, width=200),
                    img_pie_expense,
                    legend_pie_expense,
                ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
                ft.Text("流水记录", size=20, weight="bold"),
                lv_records,
            ],
            spacing=16,
            expand=True,
        )
    )

    refresh_backup_options()
    run_templates_for_current_month(silent=True)
    update_display()


if __name__ == "__main__":
    ft.run(main)
