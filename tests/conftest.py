import warnings

try:
    from matplotlib import MatplotlibDeprecationWarning
except ImportError:
    MatplotlibDeprecationWarning = UserWarning
warnings.filterwarnings("ignore", category=MatplotlibDeprecationWarning)
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=r"The 'labels' parameter of boxplot\(\) has been renamed 'tick_labels' since Matplotlib 3.9; support for the old name will be dropped in 3.11.",
)
