"""Theme configuration primitives for the Operator Console."""

from .style_resolver import (
    resolved_border_width,
    resolved_radius,
    theme_bool,
    theme_choice,
    theme_int,
)
from .theme_components import (
    COMPONENT_CATEGORIES,
    COMPONENT_SPECS,
    ThemeChoiceSpec,
    default_component_settings,
)
from .theme_motion import (
    MOTION_CATEGORIES,
    MOTION_SPECS,
    ThemeMotionSpec,
    default_motion_settings,
)
from .theme_tokens import (
    TOKEN_CATEGORIES,
    TOKEN_SPECS,
    ThemeTokenSpec,
    default_theme_tokens,
)
