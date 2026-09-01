"""
recipes/review_compare.py

NOT a custom recipe -- a short, documented example of invoking Prodigy's own
BUILT-IN `review` recipe, plus notes on how it maps onto Kaspi's assessor
workflow.

This is the one place in this whole scaffold where we can state something
about Prodigy with real confidence rather than a hedge: `review` is
Prodigy's standard, long-documented mechanism for exactly the workflow
described at the start of the conversation this project came out of -- an
assessor looks at multiple annotators' answers on the same input and
picks/edits/merges one. See https://prodi.gy/docs/recipes#review.

TALKING POINT FOR THE MEETING: Kaspi's assessor role already does this
today (assessors compare markup from multiple annotators and pick/correct
one). That means this is a case where **we don't need to build anything** --
Prodigy's own `review` recipe already does it. No custom recipe file is
needed for this piece; this file exists only to document the invocation so
it's easy to point at in the meeting and in any future PyCharm run
configuration.

CANNOT BE RUN IN THIS ENVIRONMENT (no Prodigy license) -- same caveat as
recipes/audio_markup.py. The command below is the documented public
invocation shape; confirm exact flag names against your installed version
with `python -m prodigy review --help`.
"""

# Example invocation (run from the project root, once Prodigy is installed
# and the two source datasets already contain annotator answers from
# recipes/audio_markup.py):
#
#   python -m prodigy review \
#       kaspi_markup_reviewed \
#       kaspi_markup_annotator_a,kaspi_markup_annotator_b \
#       -v blocks
#
# Argument meaning (per Prodigy's public docs for `review`):
#   kaspi_markup_reviewed              -- new dataset the assessor's final
#                                          decisions are saved to
#   kaspi_markup_annotator_a,...       -- comma-separated list of existing
#                                          datasets to compare answers from
#                                          (one per annotator, or one per
#                                          annotation pass)
#   -v blocks                          -- CONFIRM WITH YOUR PRODIGY VERSION:
#                                          `-v/--view-id` lets you pick which
#                                          interface renders each compared
#                                          example; "blocks" is a reasonable
#                                          default if the underlying examples
#                                          used a "blocks" view (e.g. from
#                                          audio_markup.py), but the right
#                                          value depends on what view_id the
#                                          source datasets were annotated
#                                          with -- check
#                                          https://prodi.gy/docs/recipes#review
#                                          for the current flag list.
#
# `review` shows the assessor every differing answer side-by-side (or
# overlaid, depending on view) for the same input across the listed
# datasets, and lets them accept one, edit a merged version, or reject all.
# That is precisely Kaspi's existing "assessor sees multiple annotators'
# answers on the same input and picks/edits one" process -- so the honest
# answer to "how do we build the review/comparison feature" is "we don't;
# ask the team to run this command against their existing annotator
# datasets."

REVIEW_EXAMPLE_COMMAND = (
    "python -m prodigy review "
    "kaspi_markup_reviewed "
    "kaspi_markup_annotator_a,kaspi_markup_annotator_b "
    "-v blocks"
)


def print_example_command() -> None:
    """
    Convenience for a PyCharm run configuration or terminal: prints the
    example `review` command above rather than running it (this project
    does not shell out to `prodigy` itself, since it isn't installed here).
    """
    print(REVIEW_EXAMPLE_COMMAND)


if __name__ == "__main__":
    print_example_command()
