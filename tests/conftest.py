import warnings

from typing import Type, cast

try:
    from matplotlib import MatplotlibDeprecationWarning as _MDW  # optional attribute

    MatplotlibDeprecationWarning = cast(Type[Warning], _MDW)
except Exception:
    MatplotlibDeprecationWarning = UserWarning
warnings.filterwarnings("ignore", category=MatplotlibDeprecationWarning)
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=(
        r"The 'labels' parameter of boxplot\(\) renamed 'tick_labels' since Matplotlib 3.9; "
        r"old name will be dropped in 3.11."
    ),
)
