"""Local W101 builder for Navigator and the shared left-panel host."""
from __future__ import annotations

from calamus_application_components import (
    NavigatorComponents,
    NavigatorCompositionInput,
    SetOnceReference,
)
from calamus_left_panel import LeftPanelHost
from calamus_navigation_gateway import NavigationController
from calamus_navigation_view import NavigationViewAdapter
from calamus_navigator_panel import NavigatorPanelRuntime
from calamus_navigator_panel_view import build_navigator_panel_view


def build_navigator_components(
    inputs: NavigatorCompositionInput,
) -> NavigatorComponents:
    runtime_reference = SetOnceReference("navigator-panel-runtime")
    navigation_controller = NavigationController(
        NavigationViewAdapter(inputs.text_view)
    )
    left_panel_host = LeftPanelHost(
        inputs.workspace_paned,
        inputs.queue_wrap_reflow,
    )
    panel_view = build_navigator_panel_view(
        navigation_controller,
        lambda: runtime_reference.require().hide(),
    )
    panel_host = left_panel_host.register("navigator", panel_view.widget)
    panel_runtime = NavigatorPanelRuntime(
        panel_host,
        panel_view,
        inputs.navigator_menu_item,
        inputs.text_view.grab_focus,
    )
    runtime_reference.set(panel_runtime)
    return NavigatorComponents(
        navigation_controller=navigation_controller,
        left_panel_host=left_panel_host,
        panel_view=panel_view,
        panel_host=panel_host,
        panel_runtime=panel_runtime,
    )
