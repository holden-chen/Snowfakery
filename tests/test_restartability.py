from unittest import mock
from io import StringIO

from snowfakery.data_generator import generate


class TestRestart:
    def test_nicknames_persist(self, generated_rows):
        yaml = """
            - object: foo
              nickname: Foo
              just_once: True
              fields:
                A: 25
            - object: bar
              fields:
                foo_reference:
                    reference: Foo
                A: ${{Foo.A}}
            - object: baz
              fields:
                bar_reference:
                    reference: bar
            """
        continuation_file = StringIO()
        generate(StringIO(yaml), generate_continuation_file=continuation_file)
        next_contination_file = StringIO()
        generate(
            StringIO(yaml),
            continuation_file=StringIO(continuation_file.getvalue()),
            generate_continuation_file=next_contination_file,
        )

        assert generated_rows.row_values(1, "foo_reference") == "foo(1)"
        assert generated_rows.row_values(2, "bar_reference") == "bar(1)"
        assert generated_rows.row_values(3, "foo_reference") == "foo(1)"
        assert generated_rows.row_values(4, "bar_reference") == "bar(2)"

    @mock.patch("snowfakery.output_streams.DebugOutputStream.write_row")
    def test_ids_go_up(self, write_row):
        yaml = """
            - object: foo
              count: 5
              nickname: Foo
            """
        continuation_file = StringIO()
        generate(StringIO(yaml), generate_continuation_file=continuation_file)
        generate(
            StringIO(yaml), continuation_file=StringIO(continuation_file.getvalue())
        )

        assert write_row.mock_calls[-1][1][1]["id"] == 10

    @mock.patch("snowfakery.output_streams.DebugOutputStream.write_row")
    def test_faker_dates_work(self, write_row):
        yaml = """
            - object: foo
              nickname: Blah
              just_once: True
              count: 50
              fields:
                a_date:
                    date_between:
                        start_date: -30d
                        end_date: +180d
            """
        continuation_file = StringIO()
        generate(StringIO(yaml), generate_continuation_file=continuation_file)
        assert "a_date" in continuation_file.getvalue()

    @mock.patch("snowfakery.output_streams.DebugOutputStream.write_row")
    def test_circular_references(self, write_row):
        yaml_data = """
            - object: parent
              nickname: TheParent
              fields:
                child:
                    - object: child
                      nickname: TheChild
                      fields:
                        parent:
                            reference:
                                TheParent
            """
        continuation_file = StringIO()
        generate(StringIO(yaml_data), generate_continuation_file=continuation_file)
        continuation_yaml = continuation_file.getvalue()
        generate(
            StringIO(yaml_data),
            continuation_file=StringIO(continuation_yaml),
        )
