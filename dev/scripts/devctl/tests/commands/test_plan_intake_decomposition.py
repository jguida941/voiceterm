from dev.scripts.devctl.commands.development.plan_intake_decomposition import (
    decomposed_packet_rows,
)


def test_range_s1_to_s5_yields_five_distinct_non_placeholder_titles() -> None:
    rows = decomposed_packet_rows(
        "- MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S1..S5 - Extend system picture graph"
    )

    assert [row.row_id for row in rows] == [
        "MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S1",
        "MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S2",
        "MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S3",
        "MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S4",
        "MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S5",
    ]
    assert {row.title for row in rows} == {"Extend system picture graph"}
    assert not any(row.title.startswith("Materialize packet closure") for row in rows)


def test_range_title_must_not_contain_literal_range_substring() -> None:
    rows = decomposed_packet_rows(
        "- MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S1..S5 - Extend system picture graph"
    )

    assert rows
    assert not any("S1..S5" in row.title for row in rows)


def test_range_title_must_not_equal_full_literal_range_token() -> None:
    rows = decomposed_packet_rows(
        "- MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S1..S5 - Extend system picture graph"
    )

    assert rows
    assert not any(
        row.title == "MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S1..S5" for row in rows
    )


def test_range_token_stripped_before_prefix_and_suffix_evaluation() -> None:
    rows = decomposed_packet_rows(
        "For rev_pkt_4106 -> MP-NEW-P204-S1..S2 - Operator directive packet"
    )

    assert [row.row_id for row in rows] == ["MP-NEW-P204-S1", "MP-NEW-P204-S2"]
    assert {row.title for row in rows} == {"Operator directive packet"}


def test_source_line_index_tracked_across_all_expanded_ranges() -> None:
    rows = decomposed_packet_rows(
        "\n".join(
            [
                "Intro",
                "",
                "- MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S1..S3 - Extend graph",
            ]
        )
    )

    assert [row.source_line for row in rows] == [3, 3, 3]
