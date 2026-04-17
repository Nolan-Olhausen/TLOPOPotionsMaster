from .ui_coordination import (
    _append_game_log,
    _brew_automation_hotkey_sync,
    _clear_game_log,
    _raise_overlay_tags,
    _refresh_game_action_button_labels,
)
from .app_actions import (
    _active_pil_template,
    _automation_start_button_style,
    _get_objects_button_style,
    _on_automation_start_clicked,
    _on_escape,
    _on_root_delete_protocol,
    _refresh_automation_start_button,
    _refresh_logs_toggle_label,
)
from .game_log_embed import (
    _destroy_game_log_embed,
    _game_log_text_key_guard,
    _sync_game_log_text_body,
)
from .strategy_board import (
    _apply_brew_strategy_choice,
    _brew_board_memory_apply_automation_drop,
    _brew_reset_board_memory,
    _brew_strategy_wrap_two_lines,
    _destroy_game_strategy_embed,
    _draw_game_strategy_embed,
    _ingredient_for_board_line_color,
    _rebuild_brew_strategy_menu,
    _refresh_brew_strategy_dropdown,
)
